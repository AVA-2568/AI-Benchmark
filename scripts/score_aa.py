import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
#!/usr/bin/env python3
"""Scoring CLI: rank merged models by custom weights (multi-leaderboard).

The algorithm now lives in ``pipeline`` (imported below) so it is
implemented exactly once. This module is the thin CLI wrapper:
load config -> read merged CSV -> load FX rate -> run the shared pipeline.

Pure helpers are re-exported for import-safety / unit tests.
"""
import json
import os
import sys

_BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_BASE)
SRC = os.path.join(_BASE, "merged.csv")
FX_PATH = os.path.join(_BASE, ".cache", "fx.json")
RESULTS_DIR = os.path.join(REPO_ROOT, "results")

# Re-export the public, import-safe helpers (single implementation
# in pipeline.config / pipeline.scoring).
from pipeline import (  # noqa: E402
    ConfigError,
    board_weights,
    fmt_val,
    load_config,
    norm,
    to_float,
    validate_config,
)

from pipeline import run_pipeline  # noqa: E402


def _load_fx():
    """读 .cache/fx.json 的 USD→CNY 汇率；缺失返回 None。"""
    if not os.path.exists(FX_PATH):
        return None
    try:
        with open(FX_PATH, encoding="utf-8") as f:
            return json.load(f).get("usd_cny")
    except (ValueError, OSError):
        return None


def main():
    if not os.path.exists(SRC):
        print(f"FATAL: {SRC} missing (run parse_aa.py + merge.py first)")
        sys.exit(1)
    config_path = os.path.join(REPO_ROOT, "config.json")
    try:
        cfg = load_config(config_path)
    except ConfigError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
    print("loaded config.json")

    validate_config(cfg)  # raises ConfigError on bad config

    fx_rate = _load_fx()
    if fx_rate:
        print(f"USD/CNY = {fx_rate}")
    else:
        print("!! fx.json missing, CNY 价格列将为空")

    import csv
    rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
    run_pipeline(rows, cfg, RESULTS_DIR, fx_rate=fx_rate)


if __name__ == "__main__":
    main()
