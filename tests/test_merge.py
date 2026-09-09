"""Unit tests for scripts/merge.py AA official-price row picking.

AA 是按 (Model Slug x Provider) 的宽表：同一模型 N 行，分数一致、
定价是各 Provider 自报的分销价。合并必须取官方行（Provider 与
Creator 一致，如 DeepSeek 行），而非按 CSV 行序取末行（如 Makora
分销价 0.09/0.195）。
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from merge import _is_official_aa_row, _pick_aa_row  # noqa: E402


def _row(provider, slug, price_in, price_out, model_slug="m"):
    return {"Provider": provider, "Provider Slug": slug,
            "Model Slug": model_slug,
            "Price 1M Input": price_in, "Price 1M Output": price_out}


def test_picks_official_row_over_distributor():
    rows = [
        _row("CoreWeave", "coreweave", "0.14", "0.28"),
        _row("DeepSeek", "deepseek", "0.44", "1.32"),
        _row("Makora", "makora", "0.09", "0.195"),
    ]
    row, used = _pick_aa_row(rows, "m", "DeepSeek")
    assert row["Provider"] == "DeepSeek"
    assert row["Price 1M Input"] == "0.44"
    assert used == "m"


def test_falls_back_to_last_row_without_official():
    rows = [
        _row("SiliconFlow", "siliconflow", "0.132", "0.528"),
        _row("GMI", "gmi", "0.126", "0.522"),
    ]
    row, _ = _pick_aa_row(rows, "m", "Tencent")
    assert row["Provider"] == "GMI"  # 无官方行时保持旧语义（末行）


def test_official_match_is_normalized():
    # Z.AI vs zai、Thinking Machines vs thinking-machines、xAI vs SpaceXAI
    assert _is_official_aa_row(_row("Zai", "zai", "1", "2"), "Z.AI")
    assert _is_official_aa_row(
        _row("Thinking Machines", "thinking-machines", "1", "2"),
        "Thinking Machines")
    assert _is_official_aa_row(_row("SpaceXAI", "xai", "1", "2"), "xAI")
    # Moonshot AI 特例：官方 Provider 叫 Kimi
    assert _is_official_aa_row(_row("Kimi", "kimi", "1", "2"), "Moonshot AI")
    # 分销商不是官方
    assert not _is_official_aa_row(
        _row("Makora", "makora", "1", "2"), "DeepSeek")


def test_alias_list_tries_in_order():
    rows = [_row("DeepSeek", "deepseek", "0.44", "1.32",
                 model_slug="deepseek-v4-flash")]
    row, used = _pick_aa_row(
        rows, ["deepseek-v4-flash-0731", "deepseek-v4-flash"], "DeepSeek")
    assert used == "deepseek-v4-flash"
    assert row["Provider"] == "DeepSeek"


def test_no_match_returns_none():
    row, used = _pick_aa_row(
        [_row("DeepSeek", "deepseek", "0.44", "1.32", model_slug="other")],
        "m", "DeepSeek")
    assert (row, used) == (None, None)
