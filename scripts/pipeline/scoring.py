"""Scoring: min-max norm, weighted total, cost, ranking + threshold."""
from __future__ import annotations

import fnmatch
from typing import Any, Dict, List, Optional, Tuple

from .config import board_weights, to_float
from .models import ScoredModel


def norm(v, lo, hi):
    """Min-max normalize v into 0-100 using [lo, hi]. Flat range -> 50.

    Clipped to [0, 100]: an out-of-anchor raw value (e.g. EQ-Bench Elo
    above the 2200 upper anchor) must not produce a >100 or <0 score.
    """
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100.0))


def fmt_val(val, is_imputed, is_low):
    s = str(round(val, 3))
    if is_low:
        return s + "**"
    if is_imputed:
        return s + "*"
    return s


def _cache_rate_for(cost, creator):
    """Real-world cache-hit-rate assumption for a model creator.

    Falls back to ``provider_cache_rates.default`` then the global
    ``cache_hit_rate``. AA does not publish per-model hit rates (hit
    rate depends on the user's prompt pattern), so this is a
    configurable usage assumption per creator.
    """
    rates = cost.get("provider_cache_rates") or {}
    if creator in rates:
        return float(rates[creator])
    if "default" in rates:
        return float(rates["default"])
    return float(cost.get("cache_hit_rate", 0.50))


def _match_pattern(name: Optional[str], patterns: Optional[Any]) -> bool:
    """Check if name matches any pattern in patterns (using fnmatch)."""
    if not name or not patterns:
        return False
    return any(fnmatch.fnmatch(name, str(pat).strip()) for pat in patterns)


def _resolve_scale(model: Optional[str], scale_map: Optional[Dict[str, Any]]) -> Optional[float]:
    """Resolve model_cost_scale: exact match first, then fnmatch pattern."""
    if not model or not scale_map:
        return 1.0
    if model in scale_map:
        return float(scale_map[model])
    for pat, scale in scale_map.items():
        if fnmatch.fnmatch(model, str(pat).strip()):
            return float(scale)
    return None


def _plan_for(plans, creator, model=None):
    """Best (lowest-effective-discount) matching subscription plan, else None.

    A plan matches when the row's Creator is in its ``creator_match``
    OR the model slug matches any pattern in its ``model_match`` (supports
    fnmatch wildcards). A plan is rejected if the model matches any pattern
    in ``exclude_match`` (one-vote veto). The lowest discount wins (cheapest
    effective price). Credit-value plans (e.g. GitHub Copilot) make API usage
    effectively cheaper than the list price. Plans with discount >= 1
    (credit-metered, no reliable token conversion) never change the
    cost math; when no real discount plan matches, the cheapest
    credit-metered one is still returned as the *nominal* plan so the
    leaderboard can show it exists (discount 1.0 = list price).

    ``model_cost_scale`` is applied *before* the comparison: the chosen
    plan must be the cheapest by what this model actually pays. Resolves
    by exact key first, then fnmatch pattern; if unmatched but matched via
    wildcard in ``model_match``, falls back safely to max(scale_map.values())
    to prevent underestimating costs. The returned plan carries the scaled
    discount, so callers must not rescale again.
    """
    best = None
    best_d = None
    nominal = None
    for p in plans or []:
        if model and _match_pattern(model, p.get("exclude_match")):
            continue
        matched = creator in (p.get("creator_match") or [])
        if not matched and model and p.get("model_match"):
            matched = _match_pattern(model, p["model_match"])
        if not matched:
            continue
        d = float(p.get("discount") or 1.0)
        if d >= 1.0:
            if nominal is None or float(p.get("monthly") or 0) < \
                    float(nominal.get("monthly") or 0):
                nominal = p
            continue
        scale_map = p.get("model_cost_scale") or {}
        if scale_map and model:
            scale = _resolve_scale(model, scale_map)
            if scale is None and p.get("model_match"):
                if model not in p["model_match"] and _match_pattern(model, p["model_match"]):
                    scale = max(float(v) for v in scale_map.values())
            d = min(d * (scale or 1.0), 1.0)
        if best is None or d < best_d:
            best, best_d = {**p, "discount": round(d, 6)}, d
    return best or nominal


def _cost_terms(r, cost, cache_multiplier, cache_price_fallback, plans):
    """Compute standard vs real-world cost for one row.

    Returns (standard_total, effective_total, blended_total, cache_rate,
    plan, pin, pout, pcache_eff):
    - standard: unit-price baseline (global cache_hit_rate, real cache
      price when known, else input × cache_multiplier).
    - blended: per-creator cache-hit-rate mix at list prices, before
      any subscription discount (base for recomputing the price under
      an arbitrary plan).
    - effective: blended × subscription-plan discount.

    Cache input is priced as a blend of first-write and reuse reads:
    ``cache_write_ratio`` of cached input pays the Cache Write Price
    (write cost is amortized over reuses), the rest pays the Cache Hit
    Price. Providers without a published write price are treated as
    bundling write into the miss price (cache input = hit price only).
    """
    pin = to_float(r.get("Price 1M Input"))
    pout = to_float(r.get("Price 1M Output"))
    pcache = to_float(r.get("Cache Hit Price"))
    pwrite = to_float(r.get("Cache Write Price"))
    creator = (r.get("Creator") or "").strip()
    if None in (pin, pout):
        return None, None, None, None, None, pin, pout, None

    pcache_eff = pcache
    if pcache_eff is None and (cache_price_fallback or {}).get(creator):
        pcache_eff = cache_price_fallback[creator]
    if pcache_eff is None and pin is not None:
        pcache_eff = pin * cache_multiplier
    # blend write + read for cached input; no write price -> hit only
    write_ratio = float(cost.get("cache_write_ratio", 0.20))
    if pwrite is not None and write_ratio > 0:
        pcache_eff = (write_ratio * pwrite
                      + (1 - write_ratio) * pcache_eff)

    in_share = cost["input_share"]
    out_share = cost["output_share"]
    glob_hit = float(cost["cache_hit_rate"])
    eff_hit = _cache_rate_for(cost, creator)
    plan = _plan_for(plans, creator, r.get("Model"))
    discount = float(plan["discount"]) if plan else 1.0
    # model_cost_scale 已在 _plan_for 内于比较前应用（选中的 plan 即为
    # 本模型实付最优），discount 就是分模型标定后的实付折扣，此处不再
    # 重复相乘。

    standard = (in_share * (1 - glob_hit) * pin
                + in_share * glob_hit * pcache_eff
                + out_share * pout)
    blended = (in_share * (1 - eff_hit) * pin
               + in_share * eff_hit * pcache_eff
               + out_share * pout)
    effective = blended * discount
    return (round(standard, 3), round(effective, 3), round(blended, 3),
            eff_hit, plan, pin, pout, pcache_eff)


def _weighted_total(glob, nrm, imputed_set, discount):
    """加权总分；填补指标的权重按 discount 打折后重新归一化。

    discount >= 1 时退化为普通加权和（不降权）。填补不可信时 discount<1，
    填补指标对总分贡献降低、其余真实指标权重相对上升，总分仍落在
    0-100 可比较（权重重归一化，总和恒为 1）。
    """
    if discount >= 1.0:
        return sum(glob[m] * nrm[m] for m in nrm)
    w = {m: glob[m] * (discount if m in imputed_set else 1.0) for m in nrm}
    ws = sum(w.values())
    return sum(w[m] * nrm[m] for m in nrm) / ws if ws else 0.0


def score_board(rows, board, engine, cost, cache_multiplier, score_threshold,
                plans=None, cache_price_fallback=None, scales=None,
                fx_rate=None, imputed_weight_discount=1.0):
    """Score one leaderboard. Returns (scored_rows, headers).

    ``engine`` provides stats / cur / raw / imputation_quality and
    the shared pool. No algorithm is duplicated here.

    ``scales`` maps metric -> (src_lo, src_hi) 固定锚点：原始值落在此
    区间即映射到 0-100。未提供时回退到动态 min-max（stats 的 lo/hi）。

    ``rank_by`` (board config, default "score"): "score" ranks by
    Weighted Total, "value" ranks by Weighted Total / Effective $/1M
    and drops rows without an effective cost.
    """
    cats, glob = board_weights(board)
    metrics = list(glob.keys())
    rank_by = board.get("rank_by", "score")
    stats = engine.stats
    cur = engine.cur
    raw = engine.raw
    imp_q = engine.imputation_quality
    min_samples = engine.min_samples
    if scales is None:
        scales = {m: (stats[m][0], stats[m][1]) for m in metrics}

    out = []
    for i, r in enumerate(rows):
        eff = {}
        imputed = []
        for m in metrics:
            if raw[m][i] is not None:
                eff[m] = raw[m][i]
            else:
                n_train = imp_q[m]["n_train"]
                eff[m] = cur[m][i]
                if n_train < min_samples:
                    imputed.append(m + "(low)")
                else:
                    imputed.append(m)
        nrm = {m: norm(eff[m], scales[m][0], scales[m][1]) for m in metrics}
        imputed_set = {m.split("(low)")[0] for m in imputed}
        total = _weighted_total(glob, nrm, imputed_set,
                                imputed_weight_discount)
        feature_bonuses = board.get("feature_bonuses") or {}
        v_raw = r.get("Vision")
        has_vision = v_raw is True or (isinstance(v_raw, str) and v_raw.strip().lower() in ("true", "1", "yes"))
        if has_vision and "vision" in feature_bonuses:
            total = min(100.0, total + float(feature_bonuses["vision"]))

        std_cost, eff_cost, blended, cache_rate, plan, pin, pout, \
            pcache_eff = _cost_terms(r, cost, cache_multiplier,
                                     cache_price_fallback, plans)
        value_score = (round(total / eff_cost, 2)
                       if eff_cost else None)
        # 人民币价格（汇率实时抓取；缺失时不输出）
        std_cny = round(std_cost * fx_rate, 3) if (std_cost and fx_rate) else None
        eff_cny = round(eff_cost * fx_rate, 3) if (eff_cost and fx_rate) else None
        plan_monthly = plan.get("monthly") if plan else None
        plan_mult = plan.get("multiplier") if plan else None
        plan_discount = plan.get("discount") if plan else None
        plan_url = (plan.get("url") or "") if plan else ""

        low_set = {m.split("(low)")[0] for m in imputed if m.endswith("(low)")}

        out.append({
            "Model": r.get("Model"),
            "Creator": r.get("Creator"),
            "Vision": "Yes" if has_vision else "No",
            "Reasoning": r.get("Reasoning Model"),
            "Orig Intelligence Index": to_float(r.get("Intelligence Index")),
            **{m: fmt_val(eff[m], m in imputed_set, m in low_set)
               for m in metrics},
            **{m + " (norm)": round(nrm[m], 1) for m in metrics},
            "Weighted Total": round(total, 1),
            "Price 1M In": pin,
            "Price 1M Out": pout,
            "Cache Hit": pcache_eff,
            "Total $/1M": std_cost,
            "Blended $/1M": blended,
            "Effective $/1M": eff_cost,
            "Total ¥/1M": std_cny,
            "Effective ¥/1M": eff_cny,
            "Value Score": value_score,
            "Cache Hit Rate": cache_rate,
            "Plan": plan.get("name", "") if plan else "",
            "Plan Monthly": plan_monthly,
            "Plan Multiplier": plan_mult,
            "Plan Discount": plan_discount,
            "Plan URL": plan_url,
            "AA Cost/Task": to_float(r.get("Cost Per Task")),
            "Imputed": ", ".join(
                f"{m}(reg)" if not m.endswith("(low)")
                else f"{m[:-5]}(reg,low)"
                for m in imputed
            ) if imputed else "",
        })

    if rank_by == "value":
        out = [r for r in out if r.get("Value Score") is not None]
        out.sort(key=lambda x: (-x["Value Score"],
                                x.get("Model") or "",
                                x.get("Creator") or ""))
    else:
        out.sort(key=lambda x: (
            -(x["Weighted Total"] if x["Weighted Total"] is not None else -1),
            x.get("Model") or "",
            x.get("Creator") or "",
        ))

    out = [r for r in out
           if r["Weighted Total"] is not None
           and r["Weighted Total"] >= score_threshold]

    for idx, row in enumerate(out, 1):
        row["Rank"] = idx

    headers = ["Rank", "Model", "Vision", "Weighted Total", "Total $/1M",
               "Blended $/1M", "Effective $/1M", "Total ¥/1M",
               "Effective ¥/1M", "Value Score", "Cache Hit Rate",
               "Plan", "Plan Monthly", "Plan Multiplier",
               "Plan Discount", "Plan URL", "AA Cost/Task", "Creator",
               "Reasoning", "Orig Intelligence Index"]
    for _, _, subs in cats:
        for m, _ in subs:
            headers.append(m)
            headers.append(m + " (norm)")
    headers += ["Price 1M In", "Price 1M Out", "Cache Hit", "Imputed"]

    return out, headers
