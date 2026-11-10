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

from merge import (  # noqa: E402
    _is_official_aa_row,
    _pick_aa_row,
    _pick_best_row,
    _row_score,
)


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


# ---- _pick_best_row：最新 release 优先，同 release 内取最高档 ----

def _lb(name, coding, release=""):
    row = {"model": name, "Coding": coding, "Reasoning": coding}
    if release:
        row["release"] = release
    return row


def test_pick_max_takes_highest_effort_alias():
    """别名列表里排第一的是低档时，必须选分更高的高档行。

    回归：旧实现 `for a in alist: return idx[a]` 取首个命中，18 个多别名
    模型里 9 个因此吃了低档行（如 gpt-5.6-terra 用了裸名而非 -max）。
    """
    idx = {"gpt-5.6-terra": _lb("gpt-5.6-terra", "60"),
           "gpt-5.6-terra-max": _lb("gpt-5.6-terra-max", "72")}
    row, used = _pick_best_row(idx, ["gpt-5.6-terra", "gpt-5.6-terra-max"])
    assert used == "gpt-5.6-terra-max"
    assert row["Coding"] == "72"


def test_pick_max_only_high_is_fine():
    """源里只公布了 -high 的模型，就取 -high（不要求必须存在更高档）。"""
    idx = {"x-high": _lb("x-high", "55")}
    row, used = _pick_best_row(idx, ["x", "x-high"])
    assert used == "x-high"
    assert row["Coding"] == "55"


def test_pick_max_tie_keeps_first_alias():
    """同分时按别名顺序取先出现者，保证结果确定。"""
    idx = {"a": _lb("a", "50"), "b": _lb("b", "50")}
    _, used = _pick_best_row(idx, ["a", "b"])
    assert used == "a"


def test_pick_max_single_alias_and_missing():
    idx = {"m": _lb("m", "50")}
    assert _pick_best_row(idx, "m")[1] == "m"
    assert _pick_best_row(idx, None) == (None, None)
    assert _pick_best_row(idx, ["absent", "m"])[1] == "m"
    assert _pick_best_row({}, ["m"]) == (None, None)


def test_pick_max_skips_rows_without_numbers():
    idx = {"empty": {"model": "empty"}, "ok": _lb("ok", "40")}
    _, used = _pick_best_row(idx, ["empty", "ok"])
    assert used == "ok"


def test_row_score_ignores_non_numeric():
    assert _row_score({"model": "x", "A": "1", "B": "3", "note": "-"}) == 2.0
    assert _row_score({"model": "x"}) is None


def test_pick_best_row_prefers_newest_release():
    """新 release 的行优先，即使分数更低。

    回归：claude-haiku-5.5 曾同时存在旧口径的 -max-effort 行与新 release
    的裸名行，按分数取高会选中旧口径（Coding 91.4 vs 现网 77.6）。
    """
    idx = {"claude-haiku-5-5-max-effort": _lb("claude-haiku-5-5-max-effort",
                                              "91.4", "2026_06_25"),
           "claude-haiku-5.5": _lb("claude-haiku-5.5", "77.6", "20261106")}
    row, used = _pick_best_row(
        idx, ["claude-haiku-5-5-max-effort", "claude-haiku-5.5"])
    assert used == "claude-haiku-5.5"
    assert row["Coding"] == "77.6"


def test_pick_best_row_newest_release_then_highest_tier():
    """同一新 release 内仍取最高档（多档只在同 release 内比较）。"""
    idx = {"m": _lb("m", "60", "20261014"),
           "m-max": _lb("m-max", "72", "20261106"),
           "m-high": _lb("m-high", "65", "20261106")}
    _, used = _pick_best_row(idx, ["m-max", "m-high", "m"])
    assert used == "m-max"


def test_pick_best_row_missing_release_is_oldest():
    """没有 release 列的旧缓存行为等同最旧，不压过带版本的现行数据。"""
    idx = {"legacy": _lb("legacy", "99"), "cur": _lb("cur", "50", "20261106")}
    assert _pick_best_row(idx, ["legacy", "cur"])[1] == "cur"
