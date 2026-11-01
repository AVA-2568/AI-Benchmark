"""AA-AI-Benchmark scoring pipeline (shared, implemented once).

Public API:
- ``load_config``, ``validate_config``, ``board_weights``, ``to_float``
- ``ImputationEngine`` (stats + iterative imputation + LOO + R2)
- ``score_board``
- ``run_pipeline(rows, cfg, results_dir)`` — full orchestration

Both ``scripts/score_aa.py`` (CLI) imports from here; the algorithm
lives only in this package.
"""
from __future__ import annotations

import datetime
import os

from .config import (
    ConfigError,
    board_weights,
    cost_params,
    imputation_params,
    load_config,
    plan_params,
    to_float,
    validate_config,
)
from .imputation import ImputationEngine, compute_stats
from .io_utils import (
    read_rows,
    write_scored_csv,
    write_validation,
)
from .models import (
    CategorySpec,
    ImputationResult,
    LeaderboardConfig,
    MetricSpec,
    ScoredModel,
)
from .scoring import fmt_val, norm, score_board

__all__ = [
    "ConfigError",
    "ImputationEngine",
    "compute_stats",
    "board_weights",
    "to_float",
    "validate_config",
    "load_config",
    "imputation_params",
    "read_rows",
    "write_scored_csv",
    "write_validation",
    "norm",
    "fmt_val",
    "score_board",
    "run_pipeline",
    "MetricSpec",
    "CategorySpec",
    "LeaderboardConfig",
    "ImputationResult",
    "ScoredModel",
]


def _creator_cache_price_mean(rows):
    """Mean Cache Hit Price per Creator (rows with a real value only).

    Used as a fallback cache price for rows whose provider does not
    publish a cache-hit price, instead of a blind global guess.
    """
    sums: dict = {}
    counts: dict = {}
    for r in rows:
        creator = (r.get("Creator") or "").strip()
        p = to_float(r.get("Cache Hit Price"))
        if creator and p is not None:
            sums[creator] = sums.get(creator, 0.0) + p
            counts[creator] = counts.get(creator, 0) + 1
    return {c: round(sums[c] / counts[c], 4)
            for c in sums if counts[c] > 0}


def run_pipeline(rows, cfg, results_dir, fx_rate=None):
    """Full scoring run: impute -> validate -> score both boards.

    Prints the same diagnostics as the legacy script and writes one
    CSV + one validation JSON per leaderboard. Returns the validation
    dict (pool metric -> {mae, pct_over10, n}).
    """
    pool = cfg["imputation_pool"]
    boards = cfg["leaderboards"]
    cost = cost_params(cfg)
    plans = plan_params(cfg)
    score_threshold = cfg["score_threshold"]
    ip = imputation_params(cfg)
    cache_multiplier = ip["cache_hit_multiplier"]
    scales = cfg.get("metric_scales")

    # per-creator mean cache price for rows missing a real Cache Hit
    # Price (better than a blind input × multiplier guess)
    cache_price_fallback = _creator_cache_price_mean(rows)

    params = {
        "ridge_alpha": cfg["ridge_alpha"],
        "imputation_min_samples": cfg["imputation_min_samples"],
        "standardize_features": cfg.get("standardize_features", True),
        "clip_quantile": ip["clip_quantile"],
        "damping": ip["damping"],
        "domain_groups": cfg.get("domain_groups"),
        "domain_hierarchies": cfg.get("domain_hierarchies"),
        "metric_scales": scales,
    }
    engine = ImputationEngine(rows, pool, params)

    for bkey, board in boards.items():
        _, glob = board_weights(board)
        print(f"[{bkey}] global weights:",
              {m: round(w, 3) for m, w in glob.items()})

    print(f"loaded rows: {len(rows)}")

    converged_iter, max_delta = engine.run(
        ip["max_iters"], ip["relative_tolerance"], ip["stable_rounds"])
    if converged_iter is None:
        print(f"  !! WARNING: not converged after {ip['max_iters']} iters, "
              f"max_delta={max_delta:.4f}")

    validation = engine.loo_validation()
    for bkey, board in boards.items():
        _, glob = board_weights(board)
        board_val = {m: validation[m] for m in glob if m in validation}
        val_path = os.path.join(results_dir, board["validation_json"])
        write_validation(bkey, board_val, val_path)
        print(f"Saved validation [{bkey}] -> {val_path}")

    for bkey, board in boards.items():
        out, headers = score_board(
            rows, board, engine, cost, cache_multiplier, score_threshold,
            plans=plans, cache_price_fallback=cache_price_fallback,
            scales=scales, fx_rate=fx_rate,
            imputed_weight_discount=cfg.get("imputed_weight_discount", 1.0),
            max_imputed_ratio=board.get("max_imputed_ratio", cfg.get("max_imputed_ratio")))
        out_csv = os.path.join(results_dir, board["output_csv"])
        write_scored_csv(out, headers, out_csv)
        print(f"[{bkey}] >={score_threshold} score: {len(out)} rows")
        print(f"Saved [{bkey}] -> {out_csv}")

    r2 = engine.r2_log()
    print(f"\nData snapshot: {datetime.date.today().isoformat()}")
    print(f"Training R2 (no II, {len(pool) - 1}->1 cross-predict "
          f"over shared pool):")
    for m in pool:
        if m in r2:
            print(f"  {m:25} R2={r2[m]:.3f}")

    print("\nDONE")
    return validation
