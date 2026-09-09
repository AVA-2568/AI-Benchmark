"""Unit tests for detect_new_models (new-model + alias-missing discovery)."""
import csv
import json
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import detect_new_models as dnm  # noqa: E402


def _write_registry(path, models):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"models": models}, f)


def _write_cache(cache_dir, fname, models):
    p = os.path.join(cache_dir, fname)
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "score"])
        for m in models:
            w.writerow([m, "1.0"])


def _write_aa(path, slugs):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model Slug", "LCR"])
        for s in slugs:
            w.writerow([s, "0.5"])


# ---- load_whitelists ----

def test_load_whitelists_split_by_source(tmp_path):
    reg = tmp_path / "reg.json"
    _write_registry(str(reg), [
        {"slug": "a", "aa": "a-1", "livebench": ["a-high", "a"],
         "deepswe": None, "swebench": None, "eqbench": "a"},
    ])
    wl = dnm.load_whitelists(str(reg))
    assert wl["livebench"] == {"a-high", "a"}
    assert wl["deepswe"] == set()


# ---- detect_new_models ----

def test_new_models_flags_only_uncovered(tmp_path):
    reg = tmp_path / "reg.json"
    _write_registry(str(reg), [
        {"slug": "gemini-3.7-flash", "aa": "gemini-3-7-flash",
         "livebench": "gemini-3.7-flash-high", "deepswe": "gemini-3.7-flash",
         "swebench": None, "eqbench": "gemini-3.7-flash"},
    ])
    cache = tmp_path / "cache"
    cache.mkdir(exist_ok=True)
    _write_cache(str(cache), "livebench.csv",
                 ["gemini-3.7-flash-high", "some-new-model-high"])
    _write_cache(str(cache), "deepswe.csv",
                 ["gemini-3.7-flash", "another-new-model"])

    got = dnm.detect_new_models(dnm.load_whitelists(str(reg)),
                                cache_dir=str(cache))
    assert got["livebench.csv"] == ["some-new-model-high"]
    assert got["deepswe.csv"] == ["another-new-model"]


def test_new_models_no_cross_source_confusion(tmp_path):
    """livebench 源里的名字只匹配 livebench 别名，不被 eqbench 别名误判覆盖。"""
    reg = tmp_path / "reg.json"
    _write_registry(str(reg), [
        {"slug": "x", "aa": None, "livebench": "x-high", "deepswe": None,
         "swebench": None, "eqbench": "x"},
    ])
    cache = tmp_path / "cache"
    cache.mkdir(exist_ok=True)
    _write_cache(str(cache), "livebench.csv", ["x"])
    _write_cache(str(cache), "deepswe.csv", [])

    got = dnm.detect_new_models(dnm.load_whitelists(str(reg)),
                                cache_dir=str(cache))
    assert got["livebench.csv"] == ["x"]


def test_new_models_case_insensitive(tmp_path):
    reg = tmp_path / "reg.json"
    _write_registry(str(reg), [
        {"slug": "x", "aa": None, "livebench": "X-High", "deepswe": None,
         "swebench": None, "eqbench": None},
    ])
    cache = tmp_path / "cache"
    cache.mkdir(exist_ok=True)
    _write_cache(str(cache), "livebench.csv", ["x-high"])
    _write_cache(str(cache), "deepswe.csv", [])

    got = dnm.detect_new_models(dnm.load_whitelists(str(reg)),
                                cache_dir=str(cache))
    assert got["livebench.csv"] == []


def test_new_models_missing_cache(tmp_path):
    reg = tmp_path / "reg.json"
    _write_registry(str(reg), [])
    got = dnm.detect_new_models(dnm.load_whitelists(str(reg)),
                                cache_dir=str(tmp_path / "nope"))
    assert got == {"livebench.csv": [], "deepswe.csv": []}


# ---- detect_missing_aliases ----

def test_missing_aliases_aa_detected(tmp_path):
    """registry aa=null 但 AA 源有连字符 slug → 报漏配。"""
    reg = [
        {"slug": "qwen3.8-max", "aa": None, "livebench": "qwen3.8-max",
         "deepswe": "qwen3.8-max", "swebench": None, "eqbench": None},
    ]
    aa = tmp_path / "aa.csv"
    _write_aa(str(aa), ["qwen3-8-max"])

    got = dnm.detect_missing_aliases(reg, cache_dir=str(tmp_path / "nope"),
                                     aa_csv=str(aa))
    assert got["aa"] == ["qwen3.8-max -> qwen3-8-max"]


def test_missing_aliases_no_false_positive(tmp_path):
    """字段已配（值在源里）→ 不报漏配；字段 null 但源里也没有 → 不报。"""
    reg = [
        {"slug": "a", "aa": "a-1", "livebench": None, "deepswe": None,
         "swebench": None, "eqbench": None},
        {"slug": "b", "aa": None, "livebench": None, "deepswe": None,
         "swebench": None, "eqbench": None},
    ]
    aa = tmp_path / "aa.csv"
    _write_aa(str(aa), ["a-1"])  # 只有 a，没有 b

    got = dnm.detect_missing_aliases(reg, cache_dir=str(tmp_path / "nope"),
                                     aa_csv=str(aa))
    assert got["aa"] == []  # a 已配、b 源里没有 → 都不报


def test_missing_aliases_livebench_dotted_name(tmp_path):
    """livebench=null 且源名带点号 → 必须报漏配。

    回归：旧实现只试 slug.replace(".", "-")，glm-5.3 这类「源名带点」
    的模型整类漏报，真实分数被静默丢弃走填补。
    """
    reg = [
        {"slug": "glm-5.3", "aa": "glm-5-3", "livebench": None,
         "deepswe": "glm-5.3", "swebench": None, "eqbench": None},
    ]
    cache = tmp_path / "cache"
    cache.mkdir(exist_ok=True)
    _write_cache(str(cache), "livebench.csv", ["glm-5.3"])
    _write_cache(str(cache), "eqbench.csv", ["GLM-5.3"])

    got = dnm.detect_missing_aliases(reg, cache_dir=str(cache),
                                     aa_csv=str(tmp_path / "aa.csv"))
    assert got["livebench"] == ["glm-5.3 -> glm-5.3"]
    assert got["eqbench"] == ["glm-5.3 -> glm-5.3"]

# ---- derive_slug ----

def test_derive_slug_strips_effort_suffixes():
    assert dnm.derive_slug("Claude-Opus-5-Max-Effort") == "claude-opus-5"
    assert dnm.derive_slug("gemini-3.7-flash-high") == "gemini-3.7-flash"
    assert dnm.derive_slug("gpt-5.4-xhigh") == "gpt-5.4"


def test_derive_slug_ambiguous_max():
    """裸 -max 仅在前段非版本数字时剥离；qwen3.8-max 是型号名。"""
    assert dnm.derive_slug("ox-alpha-max") == "ox-alpha"
    assert dnm.derive_slug("gpt-5.6-luna-max") == "gpt-5.6-luna"
    assert dnm.derive_slug("qwen3.8-max") == "qwen3.8-max"


def test_derive_slug_dotted_version():
    """版本分隔符一律收敛为点号（registry slug 规范）。

    回归：LiveBench 用连字符写版本（claude-fable-5-1-max-effort），旧实现
    直接拿源名当 slug，产出 claude-fable-5-1 这种错名并带上 (reg) 填补分。
    """
    assert dnm.derive_slug("claude-fable-5-1-max-effort") == "claude-fable-5.1"
    assert dnm.derive_slug("claude-opus-4-7-xhigh-effort") == "claude-opus-4.7"
    assert dnm.derive_slug("qwen3-8-max") == "qwen3.8-max"
    assert dnm.derive_slug("grok-4-3") == "grok-4.3"


def test_derive_slug_keeps_non_version_dash():
    """非纯数字分量不参与点号化，避免 llama-3-70b 之类被改坏。"""
    assert dnm.derive_slug("llama-3-70b") == "llama-3-70b"
    assert dnm.derive_slug("nemotron-3-ultra-550b-a55b") == \
        "nemotron-3-ultra-550b-a55b"


def test_derive_slug_strips_release_date():
    """LiveBench 的发布日分量不是版本号，slug 里去掉。"""
    assert dnm.derive_slug("gpt-5.2-2025-12-11-high") == "gpt-5.2"
    assert dnm.derive_slug("claude-opus-4-5-20251101-thinking-64k") == \
        "claude-opus-4.5-thinking-64k"


# ---- auto_add_candidates ----

def _run_auto_add(tmp_path, registry_doc, lb, ds, aa_rows=(), eq=()):
    reg = tmp_path / "reg.json"
    with open(str(reg), "w", encoding="utf-8") as f:
        json.dump(registry_doc, f)
    cache = tmp_path / "cache"
    cache.mkdir(exist_ok=True)
    _write_cache(str(cache), "livebench.csv", lb)
    _write_cache(str(cache), "deepswe.csv", ds)
    if eq:
        _write_cache(str(cache), "eqbench.csv", eq)
    aa = tmp_path / "aa.csv"
    with open(str(aa), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Model Slug", "Creator", "LCR"])
        for slug, creator in aa_rows:
            w.writerow([slug, creator, "0.5"])
    added, deferred = dnm.auto_add_candidates(
        registry_path=str(reg), cache_dir=str(cache), aa_csv=str(aa),
        today="2026-08-25")
    return str(reg), added, deferred


def _load_models(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["models"]


def test_auto_add_two_source_confirmed(tmp_path):
    """livebench + deepswe 双源出现 -> 入池，别名/日期齐全。"""
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["new-model-a"], ds=["new-model-a"])
    assert deferred == []
    assert len(added) == 1
    e = added[0]
    assert e["slug"] == "new-model-a"
    assert e["livebench"] == "new-model-a"
    assert e["deepswe"] == "new-model-a"
    assert e["aa"] is None and e["swebench"] is None
    assert e["auto_added"] == "2026-08-25"
    assert len(_load_models(reg)) == 1


def test_auto_add_idempotent(tmp_path):
    reg, added, _ = _run_auto_add(
        tmp_path, {"models": []},
        lb=["new-model-a"], ds=["new-model-a"])
    assert len(added) == 1
    added2, deferred2 = dnm.auto_add_candidates(
        registry_path=reg,
        cache_dir=str(tmp_path / "cache"), aa_csv=str(tmp_path / "aa.csv"))
    assert added2 == [] and deferred2 == []
    assert len(_load_models(reg)) == 1  # 不重复入池


def test_auto_add_single_source_deferred(tmp_path):
    """仅 livebench 单源孤立 -> 不入池，注明原因，registry 不变。"""
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["solo-model"], ds=[])
    assert added == []
    assert len(deferred) == 1
    assert deferred[0]["reason"] == "insufficient_confirmation"
    assert deferred[0]["sources"] == {
        "livebench": True, "deepswe": False, "aa": False}
    assert _load_models(reg) == []


def test_auto_add_creator_from_aa_with_fixup(tmp_path):
    """AA 命中时取其 Creator，并应用 AA->registry 名称修正表。"""
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["some-model"], ds=["some-model"],
        aa_rows=[("some-model", "Z AI")])
    assert deferred == []
    assert added[0]["creator"] == "Z.AI"
    assert added[0]["aa"] == "some-model"


def test_auto_add_creator_prefix_fallback(tmp_path):
    """无 AA 数据时按 slug 前缀推断 creator，匹配不上则 Unknown。"""
    reg, added, _ = _run_auto_add(
        tmp_path, {"models": []},
        lb=["kimi-k4"], ds=["kimi-k4"])
    assert added[0]["creator"] == "Moonshot AI"

    reg, added, _ = _run_auto_add(
        tmp_path, {"models": []},
        lb=["mystery-9b"], ds=["mystery-9b"])
    assert added[0]["creator"] == "Unknown"


def test_auto_add_exclude_pattern(tmp_path):
    """命中 auto_add_exclude 通配模式的候选永不入池。"""
    reg, added, deferred = _run_auto_add(
        tmp_path,
        {"models": [], "auto_add_exclude": ["smaug-*"]},
        lb=["smaug-agentic"], ds=["smaug-agentic"])
    assert added == []
    assert deferred[0]["reason"] == "excluded_by_pattern:smaug-*"
    assert _load_models(reg) == []


def test_auto_add_livebench_alias_keeps_suffix(tmp_path):
    """slug 剥离 effort 后缀，但 livebench 别名保留源内原名以对齐数据。"""
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["ox-alpha-max"], ds=["ox-alpha"])
    assert deferred == []
    assert added[0]["slug"] == "ox-alpha"
    assert added[0]["livebench"] == "ox-alpha-max"
    assert added[0]["deepswe"] == "ox-alpha"


def test_auto_add_dotted_version_from_dashed_source(tmp_path):
    """源名用连字符写版本 → slug 用点号，且别名回填源内真实名字。

    回归：claude-fable-5-1 曾被当作 slug 直接入池（错名 + 与 claude-fable-5
    混淆），正确结果是 slug=claude-fable-5.1、livebench 别名仍为源内原名。
    """
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["claude-fable-5-1-max-effort"], ds=[],
        aa_rows=[("claude-fable-5-1", "Anthropic")])
    assert deferred == []
    assert len(added) == 1
    e = added[0]
    assert e["slug"] == "claude-fable-5.1"
    assert e["livebench"] == "claude-fable-5-1-max-effort"
    assert e["aa"] == "claude-fable-5-1"
    assert e["creator"] == "Anthropic"
    assert e["deepswe"] is None


def test_auto_add_groups_dash_and_dot_variants(tmp_path):
    """同一模型的连字符/点号两种写法归为一组，不产生两个条目。"""
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["glm-5-4-max-effort"], ds=["glm-5.4"],
        aa_rows=[("glm-5-4", "Z AI")])
    assert deferred == []
    assert len(added) == 1
    e = added[0]
    assert e["slug"] == "glm-5.4"
    assert e["livebench"] == "glm-5-4-max-effort"
    assert e["deepswe"] == "glm-5.4"  # 优先取与 slug 一致的写法
    assert e["aa"] == "glm-5-4"
    assert e["eqbench"] is None


def test_auto_add_exp_suffix_same_model(tmp_path):
    """-exp 实验版后缀是同物异名：LiveBench 带、AA 不带也应双源确认入池。

    回归：deepseek-v4-flash-vision-exp（LiveBench）vs
    deepseek-v4-flash-vision（AA），旧逻辑 aa_alias=None 判单源 defer。
    """
    reg, added, deferred = _run_auto_add(
        tmp_path, {"models": []},
        lb=["deepseek-v4-flash-vision-exp"], ds=[],
        aa_rows=[("deepseek-v4-flash-vision", "DeepSeek")])
    assert deferred == []
    assert len(added) == 1
    e = added[0]
    assert e["slug"] == "deepseek-v4-flash-vision-exp"
    assert e["livebench"] == "deepseek-v4-flash-vision-exp"
    assert e["aa"] == "deepseek-v4-flash-vision"
    assert e["creator"] == "DeepSeek"
