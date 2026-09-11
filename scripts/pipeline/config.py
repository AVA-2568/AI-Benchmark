"""Config loading and validation.

Replaces the old ``assert``-based checks with actionable
``ConfigError`` messages. Pure / import-safe.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List


class ConfigError(AssertionError, ValueError):
    """Raised when config.json violates a scoring invariant."""


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ConfigError(f"config.json not found at {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def board_weights(board: Dict[str, Any]):
    """Return (CATS, GLOBAL weight map) for one leaderboard config."""
    cats = [(c["name"], c["weight"],
              [(m["name"], m["sub_weight"]) for m in c["metrics"]])
            for c in board["categories"]]
    glob = {}
    for _, cw, subs in cats:
        for m, sw in subs:
            glob[m] = cw * sw
    return cats, glob


def cost_params(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve the cost block with sensible defaults.

    The $/1M estimate is a *per-token unit price*: it blends the
    provider's list prices (input / cached-input / output) with fixed
    share weights. Thinking effort is intentionally NOT part of this
    estimate — AA publishes a single list price per model, and
    thinking level changes how many tokens a task consumes, not the
    per-token price.
    """
    cost = cfg.get("cost", {})
    rates = cost.get("provider_cache_rates") or {}
    return {
        "input_share": cost.get("input_share", 0.70),
        "output_share": cost.get("output_share", 0.30),
        "cache_hit_rate": cost.get("cache_hit_rate", 0.50),
        "cache_write_ratio": cost.get("cache_write_ratio", 0.20),
        "provider_cache_rates": rates,
    }


def plan_params(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resolve the subscription-plan table.

    Two kinds of value basis:
    - ``credit_value``: official included API usage (e.g. GitHub
      Copilot — the monthly fee buys that many API dollars).
    - ``implied_value``: community-measured API-equivalent value of a
      subscription's *capped app/agent* usage (e.g. ChatGPT Plus /
      Claude Pro, measured by SemiAnalysis 2026-06 by running each
      tier to its weekly limit).

    ``discount`` = monthly / value, applied to the API unit price for
    models whose Creator is in ``creator_match``. Note: implied-value
    plans assume the plan is used to its cap — an upper-bound
    estimate, documented per plan.

    ``url`` is the official purchase link (display-only, never
    fetched by the build).

    ``multiplier`` = value / monthly — API-equivalent dollars bought
    per subscription dollar (70x on ChatGPT Pro 20x). Derived from
    implied/credit value instead of 1/discount because the 3-decimal
    discount inflates rounding (0.014 -> 71x vs the true 70x).
    """

    def _mult(p):
        val = to_float(p.get("implied_value")) or to_float(p.get("credit_value"))
        monthly = to_float(p.get("monthly"))
        if val and monthly:
            return round(val / monthly, 1)
        return None

    plans = cfg.get("plans") or []
    return [
        {
            "name": p.get("name", "?"),
            "creator_match": p.get("creator_match") or [],
            "model_match": p.get("model_match") or [],
            "exclude_match": p.get("exclude_match") or [],
            "monthly": to_float(p.get("monthly")),
            "credit_value": to_float(p.get("credit_value")),
            "implied_value": to_float(p.get("implied_value")),
            "discount": to_float(p.get("discount")),
            "multiplier": _mult(p),
            "tokens": p.get("tokens", ""),
            "source": p.get("source", ""),
            "note": p.get("note", ""),
            "url": p.get("url", ""),
            "model_cost_scale": p.get("model_cost_scale") or {},
        }
        for p in plans
    ]


def to_float(v):
    if v is None:
        return None
    if isinstance(v, str):
        v = v.strip()
        if v in ("", "None", "null"):
            return None
    try:
        return float(v)
    except Exception:
        return None


def imputation_params(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve imputation / cost-fallback parameters with defaults."""
    imp = cfg.get("imputation", {})
    fb = cfg.get("cost_fallback", {})
    return {
        "max_iters": imp.get("max_iters", 100),
        "relative_tolerance": imp.get("relative_tolerance", 0.005),
        "stable_rounds": imp.get("stable_rounds", 3),
        "damping": imp.get("damping", 0.5),
        "clip_quantile": imp.get("clip_quantile", 0.95),
        "cache_hit_multiplier": fb.get("cache_hit_multiplier", 0.1),
    }


def validate_config(cfg: Dict[str, Any]) -> bool:
    """Fail fast on bad config with actionable validation errors."""
    try:
        cost = cfg["cost"]
        pool = cfg["imputation_pool"]
        boards = cfg["leaderboards"]
    except KeyError as exc:
        raise ConfigError(f"missing config field: {exc.args[0]}") from exc
    imp = cfg.get("imputation", {})
    fb = cfg.get("cost_fallback", {})
    if not isinstance(pool, list) or len(pool) != len(set(pool)):
        raise ConfigError("imputation_pool must be a list of unique metric names")
    if not 0 <= cfg.get("score_threshold", -1) <= 100:
        raise ConfigError("score_threshold must be in [0, 100]")
    if cfg.get("ridge_alpha", 0) <= 0:
        raise ConfigError("ridge_alpha must be > 0")
    if cfg.get("imputation_min_samples", 0) < 3:
        raise ConfigError("imputation_min_samples must be >= 3")
    if not 0 < imp.get("max_iters", 0):
        raise ConfigError("imputation.max_iters must be > 0")
    if not 0 < imp.get("relative_tolerance", 0):
        raise ConfigError("imputation.relative_tolerance must be > 0")
    if not 1 <= imp.get("stable_rounds", 0):
        raise ConfigError("imputation.stable_rounds must be >= 1")
    if not 0 < imp.get("damping", 0) <= 1:
        raise ConfigError("imputation.damping must be in (0, 1]")
    if not 0 < imp.get("clip_quantile", 0) <= 1:
        raise ConfigError("imputation.clip_quantile must be in (0, 1]")
    if not 0 < fb.get("cache_hit_multiplier", 0) <= 1:
        raise ConfigError("cost_fallback.cache_hit_multiplier must be in (0, 1]")
    if (not 0 <= cost.get("input_share", -1) <= 1
            or not 0 <= cost.get("output_share", -1) <= 1):
        raise ConfigError("cost shares must be in [0, 1]")
    if abs(cost["input_share"] + cost["output_share"] - 1.0) >= 1e-6:
        raise ConfigError(
            "cost.input_share + cost.output_share must equal 1, "
            f"got {cost['input_share'] + cost['output_share']}"
        )
    if not 0 <= cost.get("cache_hit_rate", -1) <= 1:
        raise ConfigError(
            f"cost.cache_hit_rate must be in [0, 1], "
            f"got {cost.get('cache_hit_rate')}"
        )
    if not 0 <= cost.get("cache_write_ratio", -1) <= 1:
        raise ConfigError(
            f"cost.cache_write_ratio must be in [0, 1], "
            f"got {cost.get('cache_write_ratio')}"
        )
    for creator, rate in (cost.get("provider_cache_rates") or {}).items():
        if not 0 <= float(rate) <= 1:
            raise ConfigError(
                f"cost.provider_cache_rates['{creator}'] must be in [0, 1], "
                f"got {rate}"
            )
    for i, p in enumerate(cfg.get("plans") or []):
        name = p.get("name", f"plans[{i}]")
        if not p.get("creator_match") and not p.get("model_match"):
            raise ConfigError(
                f"plan '{name}' needs a non-empty creator_match or model_match"
            )
        d = p.get("discount")
        if d is None or not 0 < float(d) <= 1:
            raise ConfigError(f"plan '{name}' discount must be in (0, 1]")
        url = p.get("url")
        if url and not str(url).startswith(("http://", "https://")):
            raise ConfigError(
                f"plan '{name}' url must start with http:// or https://"
            )
        if "exclude_match" in p and not isinstance(p["exclude_match"], list):
            raise ConfigError(
                f"plan '{name}' exclude_match must be a list"
            )
    for bkey, board in boards.items():
        if board.get("rank_by") not in (None, "score", "value"):
            raise ConfigError(
                f"[{bkey}] rank_by must be 'score' or 'value', "
                f"got {board.get('rank_by')}"
            )
        cats, glob = board_weights(board)
        if abs(sum(glob.values()) - 1.0) >= 1e-9:
            raise ConfigError(
                f"[{bkey}] global weights sum={sum(glob.values())}, must be 1.0"
            )
        for name, _, subs in cats:
            s = sum(sw for _, sw in subs)
            if abs(s - 1.0) >= 1e-6:
                raise ConfigError(
                    f"[{bkey}] category {name} sub_weight sum={s}, "
                    "must be 1.0"
                )
        for m in glob:
            if m not in pool:
                raise ConfigError(
                    f"[{bkey}] metric '{m}' not in imputation_pool — "
                    "add it to the pool"
                )
    # 域分组完整性：pool 中每个指标必须恰好归属一个域（首个命中生效）。
    # 重叠声明会被静默忽略（后者退化），缺失声明则回退全池污染——两者
    # 都是静默漂移，必须 fail fast。
    groups = cfg.get("domain_groups") or {}
    for m in pool:
        hits = [g for g, ms in groups.items() if m in ms]
        if not hits:
            raise ConfigError(
                f"metric '{m}' in imputation_pool but in no domain_group — "
                "it would fall back to the full pool"
            )
        if len(hits) > 1:
            raise ConfigError(
                f"metric '{m}' in multiple domain_groups {hits} — "
                "only the first takes effect, remove the overlap"
            )
    # 层级链必须引用已声明的域内指标，缺组即缺约束
    for g, chain in (cfg.get("domain_hierarchies") or {}).items():
        if g not in groups:
            raise ConfigError(
                f"domain_hierarchies group '{g}' not in domain_groups"
            )
        for m in chain:
            if m not in pool:
                raise ConfigError(
                    f"domain_hierarchies['{g}'] metric '{m}' "
                    "not in imputation_pool"
                )
    return True
