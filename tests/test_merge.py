"""Unit tests for scripts/merge.py AA official-price row picking.

AA 是按 (Model Slug x Provider) 的宽表：同一模型 N 行，分数一致、
定价是各 Provider 自报的分销价。合并必须取官方行（Provider 与
Creator 一致，如 DeepSeek 行），而非按 CSV 行序取末行（如 Makora
分销价 0.09/0.195）。
"""
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from merge import (  # noqa: E402
    _check_aa_join,
    _check_eqbench_join,
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


# ---- AA join 哨兵：别名全落空 = 上游 slug 口径变了 ----

def test_aa_join_broken_raises():
    registry = [{"slug": "a", "aa": "gpt-6"}, {"slug": "b", "aa": "claude-opus-5"}]
    with pytest.raises(RuntimeError, match="AA join 断裂"):
        _check_aa_join(registry, 0)


def test_aa_join_passes_when_any_matched():
    registry = [{"slug": "a", "aa": "gpt-6"}, {"slug": "b", "aa": "absent"}]
    _check_aa_join(registry, 1)  # 不抛异常即通过


def test_aa_join_skips_when_no_alias_configured():
    _check_aa_join([{"slug": "a"}, {"slug": "b", "aa": None}], 0)


def test_eqbench_join_broken_raises():
    """eqbench 源整体改名时，「创意写作」覆盖会静默归零，退化成对标
    LiveBench Design 的单变量填补（ADR-0011）。必须当场失败。"""
    registry = [{"slug": "a", "eqbench": "claude-opus-5"},
                {"slug": "b", "eqbench": "gpt-6-astra"}]
    with pytest.raises(RuntimeError, match="EQ-Bench join 断裂"):
        _check_eqbench_join(registry, 0)


def test_eqbench_join_passes_when_any_matched():
    registry = [{"slug": "a", "eqbench": "claude-opus-5"},
                {"slug": "b", "eqbench": "absent"}]
    _check_eqbench_join(registry, 1)  # 不抛异常即通过


def test_eqbench_join_skips_when_no_alias_configured():
    _check_eqbench_join([{"slug": "a"}, {"slug": "b", "eqbench": None}], 0)


# ---- AA 同 slug 多档：覆盖度优先，同覆盖度取最高 effort 档 ----
#
# 回归：AA 把 non-reasoning / high / max 并列在同一 Model Slug 下，旧实现取
# 「第一个官方行」完全取决于页面行序，2026-11-22 吃到 non-reasoning 档，
# deepseek-v4.1-flash 的 AA 指标全线腰斩（FrontierCode 0.285 → 0.061），
# 排名 #12 → #21。

def _aa_row(label, fc, lcr=None, provider="DeepSeek", slug="m"):
    row = {"Model": label, "Model Slug": slug, "Provider": provider,
           "FrontierCode 2.0": fc}
    if lcr is not None:
        row["LCR"] = lcr
    return row


def test_picks_highest_effort_tier():
    rows = [
        _aa_row("M (non-reasoning)", "0.06"),
        _aa_row("M (high)", "0.17"),
        _aa_row("M (max)", "0.28"),
    ]
    row, _ = _pick_aa_row(rows, "m", "DeepSeek")
    assert row["Model"] == "M (max)"
    assert row["FrontierCode 2.0"] == "0.28"


def test_tier_selection_ignores_quantization_suffix():
    """FP8 / NVFP4 / FAST 是量化或部署标记，不是档位，不能压过 max。"""
    rows = [
        _aa_row("M (max)", "0.28"),
        _aa_row("M (max) (FP8) (FAST)", "0.28", provider="Other"),
        _aa_row("M (NVFP4)", "0.10", provider="Other"),
    ]
    row, _ = _pick_aa_row(rows, "m", "DeepSeek")
    assert row["Model"] == "M (max)"


def test_coverage_beats_tier():
    """non-reasoning 档只挂着 LCR 一个指标时不能被选中（会整行掉数据）。

    回归：gemma-4-31b 的 non-reasoning 行只有 LCR，纯按档位选会让 9 个
    池指标变空。
    """
    rows = [
        _aa_row("M (non-reasoning)", "", lcr="0.5"),
        _aa_row("M", "0.10", lcr="0.5", provider="Other"),
    ]
    row, _ = _pick_aa_row(rows, "m", "Google")
    assert row["Model"] == "M"


def test_empty_tier_rows_lose_to_scored_ones():
    """全空档位行（只有定价）不能入选。"""
    rows = [
        _aa_row("M (max)", "", provider="Other"),
        _aa_row("M", "0.10", provider="Other"),
    ]
    row, _ = _pick_aa_row(rows, "m", "Google")
    assert row["Model"] == "M"


def test_official_provider_wins_within_same_coverage_and_tier():
    rows = [
        _aa_row("M (max)", "0.28", provider="SomeReseller"),
        _aa_row("M (max)", "0.28", provider="DeepSeek"),
    ]
    row, _ = _pick_aa_row(rows, "m", "DeepSeek")
    assert row["Provider"] == "DeepSeek"


def test_aa_metrics_subset_of_pool():
    """AA_METRICS 必须都在 build_merged 的池指标里，否则覆盖度判据会失效。"""
    from merge import AA_METRICS, build_merged  # noqa: F401
    import inspect
    src = inspect.getsource(build_merged)
    for m in AA_METRICS:
        assert f'"{m}"' in src, f"{m} 不在 build_merged 的 cols 里"


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
