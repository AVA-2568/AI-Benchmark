"""Shared ridge-regression imputation + leave-one-out validation.

The imputation pool is partitioned into domain groups (1 major + 2 minors)
so that missing metrics are predicted strictly within their own domain features.
Imputation uses cross-feature ridge regression with z-score standardization
and damped updates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.preprocessing import StandardScaler

from .config import to_float


def compute_stats(rows, pool, clip_quantile=0.95):
    """Per-metric (lo, hi, top50mean, p90, clip) over observed values."""
    stats = {}
    for m in pool:
        vals = [to_float(r.get(m)) for r in rows]
        vals = [v for v in vals if v is not None]
        if len(vals) < 2:
            raise ValueError(f"{m} effective samples {len(vals)} < 2")
        lo, hi = min(vals), max(vals)
        sv = sorted(vals)
        p90 = sv[min(len(sv) - 1, int(0.90 * (len(sv) - 1)))]
        clip = sv[min(len(sv) - 1, int(clip_quantile * (len(sv) - 1)))]
        top50 = sv[len(sv) // 2:]
        top50mean = sum(top50) / len(top50)
        stats[m] = (lo, hi, top50mean, p90, clip)
    return stats


class ImputationEngine:
    """Holds the shared pool state and runs domain-scoped ridge imputation + LOO."""

    def __init__(self, rows, pool, cfg_params):
        self.rows = rows
        self.pool = pool
        self.n_pool = len(pool)
        self.alpha = cfg_params["ridge_alpha"]
        self.min_samples = cfg_params["imputation_min_samples"]
        self.standardize = cfg_params["standardize_features"]
        self.damping = cfg_params["damping"]
        self.domain_groups = cfg_params.get("domain_groups") or {}
        self.domain_hierarchies = cfg_params.get("domain_hierarchies") or {}
        self.metric_scales = cfg_params.get("metric_scales") or {}
        
        # 构建 metric -> domain metrics 映射
        self.metric_domains = {}
        for m in pool:
            assigned = None
            for d_name, d_metrics in self.domain_groups.items():
                if m in d_metrics:
                    assigned = [x for x in d_metrics if x in pool]
                    break
            self.metric_domains[m] = assigned or pool

        n = len(rows)
        self.raw = {m: [to_float(r.get(m)) for r in rows] for m in pool}
        self.stats = compute_stats(rows, pool, cfg_params["clip_quantile"])
        self.cur = {
            m: [(v if v is not None else self.stats[m][2]) for v in self.raw[m]]
            for m in pool
        }
        self.imputation_quality = {
            m: {"n_train": sum(1 for i in range(n) if self.raw[m][i] is not None)}
            for m in pool
        }
        
        # 分域 Scaler
        self.scalers = {}
        if self.standardize:
            for m in pool:
                d_metrics = self.metric_domains[m]
                x_raw_real = np.array([
                    [self.raw[mm][i] if self.raw[mm][i] is not None else self.stats[mm][2]
                     for i in range(n)]
                    for mm in d_metrics
                ], dtype=float)  # N_DOMAIN x n
                scaler = StandardScaler()
                scaler.fit(x_raw_real.T)
                self.scalers[m] = scaler
        else:
            self.scalers = {m: None for m in pool}

    def domain_feat_row(self, i, target_m):
        """Feature row for model i scoped to target_m's domain."""
        d_metrics = self.metric_domains[target_m]
        return [self.cur[mm][i] for mm in d_metrics]

    def to_X(self, arr_domain, target_m):
        """arr_domain: n x N_DOMAIN. Returns [1, std N_DOMAIN-1 excluding target]."""
        d_metrics = self.metric_domains[target_m]
        scaler = self.scalers[target_m]
        if scaler is not None:
            arr_domain = scaler.transform(arr_domain)
        target_idx = d_metrics.index(target_m)
        n_dim = len(d_metrics)
        keep = np.r_[:target_idx, target_idx + 1:n_dim]
        if len(keep) == 0:
            return np.ones((len(arr_domain), 1))
        return np.hstack([np.ones((len(arr_domain), 1)), arr_domain[:, keep]])

    def _apply_hierarchy_bounds(self, m, pred_val, i):
        """物理层级单调性与防刷分天花板约束。
        
        对于高层级前沿指标（如 L3 Terminal-Bench v4.0），其得分能力不应脱离基础层级（如 L1 LiveBench Coding）。
        依据固定锚点归一化空间映射，防止未公布高阶指标的模型被机械回归盲目抬高。
        """
        if not self.domain_hierarchies or not self.metric_scales:
            return pred_val
        
        # 寻找 m 所属的层级链
        target_chain = None
        for d_name, chain in self.domain_hierarchies.items():
            if m in chain:
                target_chain = chain
                break
        if not target_chain or m not in target_chain:
            return pred_val
        
        m_idx = target_chain.index(m)
        if m_idx == 0:
            return pred_val  # 最基础指标无需下层天花板
        
        # 查找下层基础指标当前值
        lo_m, hi_m = self.metric_scales.get(m, (0, 100))
        pred_nrm = (pred_val - lo_m) / ((hi_m - lo_m) or 1.0) * 100.0
        
        # 逐级检查基础指标约束（高层能力分通常 ≤ 基础能力分 * 1.05）
        max_allowed_nrm = 100.0
        for lower_m in target_chain[:m_idx]:
            if lower_m in self.cur:
                lo_l, hi_l = self.metric_scales.get(lower_m, (0, 100))
                l_val = self.cur[lower_m][i]
                l_nrm = (l_val - lo_l) / ((hi_l - lo_l) or 1.0) * 100.0
                # 高难指标不应大幅超越基础指标能力
                max_allowed_nrm = min(max_allowed_nrm, l_nrm * 1.05)
        
        if pred_nrm > max_allowed_nrm:
            # 压制回物理包络天花板
            clamped_val = lo_m + (max_allowed_nrm / 100.0) * (hi_m - lo_m)
            return clamped_val
        return pred_val

    def run(self, max_iters, rel_tol, stable_rounds):
        """Iterative domain-scoped imputation with hierarchy envelope constraints."""
        n = len(self.rows)
        prev = {m: list(self.cur[m]) for m in self.pool}
        stable_count = 0
        max_delta = 0.0
        converged_iter = None
        for it in range(max_iters):
            for m in self.pool:
                xtr, ytr = [], []
                for i in range(n):
                    if self.raw[m][i] is not None:
                        xtr.append(self.domain_feat_row(i, m))
                        ytr.append(self.raw[m][i])
                if len(xtr) < 3:
                    continue
                xtr_arr = np.array(xtr, dtype=float)
                ytr_arr = np.array(ytr, dtype=float)
                x1 = self.to_X(xtr_arr, m)
                a = x1.T @ x1 + self.alpha * np.eye(x1.shape[1])
                try:
                    beta = np.linalg.solve(a, x1.T @ ytr_arr)
                except np.linalg.LinAlgError:
                    beta = np.linalg.lstsq(x1, ytr_arr, rcond=None)[0]
                lo, hi, _, _, clip = self.stats[m]
                n_train = self.imputation_quality[m]["n_train"]
                for i in range(n):
                    if self.raw[m][i] is None and n_train >= self.min_samples:
                        xi = self.to_X(np.array([self.domain_feat_row(i, m)], dtype=float), m)[0]
                        pred = max(lo, min(clip, float(xi @ beta)))
                        # 物理层级单调性与防刷分天花板约束
                        pred = self._apply_hierarchy_bounds(m, pred, i)
                        self.cur[m][i] = (1 - self.damping) * self.cur[m][i] + self.damping * pred
            max_delta = 0.0
            for m in self.pool:
                lo, hi = self.stats[m][0], self.stats[m][1]
                rng = (hi - lo) or 1.0
                for i in range(n):
                    if self.raw[m][i] is None:
                        max_delta = max(
                            max_delta, abs(self.cur[m][i] - prev[m][i]) / rng)
            if max_delta < rel_tol:
                stable_count += 1
                if stable_count >= stable_rounds:
                    converged_iter = it - 1
                    break
            else:
                stable_count = 0
            prev = {m: list(self.cur[m]) for m in self.pool}
        return converged_iter, max_delta

    def loo_validation(self):
        """Leave-one-out validation within each metric's domain group."""
        n = len(self.rows)
        validation = {}
        for target_m in self.pool:
            has_true = [j for j in range(n) if self.raw[target_m][j] is not None]
            nn = len(has_true)
            if nn < 10:
                validation[target_m] = {"mae": None, "pct_over10": None, "n": nn}
                continue
            errors = []
            true_vals = []
            for skip_i in has_true:
                true_val = self.raw[target_m][skip_i]
                xtr, ytr = [], []
                for j in range(n):
                    if j != skip_i and self.raw[target_m][j] is not None:
                        xtr.append(self.domain_feat_row(j, target_m))
                        ytr.append(self.raw[target_m][j])
                if len(xtr) < 3:
                    continue
                xtr_arr = np.array(xtr, dtype=float)
                ytr_arr = np.array(ytr, dtype=float)
                x1 = self.to_X(xtr_arr, target_m)
                a = x1.T @ x1 + self.alpha * np.eye(x1.shape[1])
                try:
                    beta = np.linalg.solve(a, x1.T @ ytr_arr)
                except np.linalg.LinAlgError:
                    beta = np.linalg.lstsq(x1, ytr_arr, rcond=None)[0]
                xi = self.to_X(np.array([self.domain_feat_row(skip_i, target_m)], dtype=float), target_m)[0]
                pred = float(xi @ beta)
                lo, hi, _, _, clip = self.stats[target_m]
                pred = max(lo, min(clip, pred))
                errors.append(abs(pred - true_val))
                true_vals.append(true_val)
            if not errors:
                validation[target_m] = {"mae": None, "pct_over10": None, "n": nn}
                continue
            mae = sum(errors) / len(errors)
            over10 = sum(
                1 for i, e in enumerate(errors)
                if abs(true_vals[i]) > 0.001 and e / abs(true_vals[i]) > 0.10
            )
            validation[target_m] = {
                "mae": round(mae, 4),
                "pct_over10": round(over10 / len(errors) * 100, 1),
                "n": nn,
            }
        return validation

    def r2_log(self):
        """Training R2 per metric (domain-scoped cross-predict)."""
        n = len(self.rows)
        out = {}
        for m in self.pool:
            xtr, ytr = [], []
            for i in range(n):
                if self.raw[m][i] is not None:
                    xtr.append(self.domain_feat_row(i, m))
                    ytr.append(self.raw[m][i])
            if len(xtr) < 3:
                continue
            xtr_arr = np.array(xtr, dtype=float)
            ytr_arr = np.array(ytr, dtype=float)
            x1 = self.to_X(xtr_arr, m)
            beta = np.linalg.lstsq(x1, ytr_arr, rcond=None)[0]
            pred = x1 @ beta
            ybar = ytr_arr.mean()
            ss_tot = ((ytr_arr - ybar) ** 2).sum() or 1e-12
            ss_res = ((ytr_arr - pred) ** 2).sum()
            out[m] = max(0.0, 1 - ss_res / ss_tot)
        return out
