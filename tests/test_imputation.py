"""Unit tests for pipeline.imputation (synthetic data, no network).

Uses tiny synthetic rows with ``imputation_min_samples=3`` so the
iterative imputation path actually runs (the real config uses
``min_samples=50``, which only triggers on near-full data sets).
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from pipeline import ImputationEngine, compute_stats  # noqa: E402


POOL = ["m1", "m2", "m3"]

# 6 rows; each metric observed in >=3 rows so imputation can run.
# D.m1, C.m2, E.m3 are missing and should be imputed.
_ROWS = [
    {"Model": "A", "m1": "1", "m2": "10", "m3": "100"},
    {"Model": "B", "m1": "2", "m2": "20", "m3": "200"},
    {"Model": "C", "m1": "3", "m2": None, "m3": "300"},
    {"Model": "D", "m1": None, "m2": "40", "m3": "400"},
    {"Model": "E", "m1": "5", "m2": "50", "m3": None},
    {"Model": "F", "m1": "6", "m2": "60", "m3": "600"},
]


def _params(clip=0.95):
    return {
        "ridge_alpha": 0.1,
        "imputation_min_samples": 3,
        "standardize_features": True,
        "clip_quantile": clip,
        "damping": 0.5,
    }


def test_compute_stats_shape_and_clip():
    vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    rows = [{"Model": str(i), "x": str(v)} for i, v in enumerate(vals)]
    stats = compute_stats(rows, ["x"], clip_quantile=0.95)
    lo, hi, top50, p90, clip = stats["x"]
    assert (lo, hi) == (1, 10)
    # top50mean = mean of upper half (sv[len//2:] = [6..10]) = 8.0
    assert top50 == 8.0
    # clip at 0.95 quantile of 10 values: idx=min(9, int(0.95*9))=8 -> sorted[8]=9
    assert clip == 9


def test_compute_stats_rejects_sparse():
    rows = [{"Model": "A", "x": "1"}]  # only 1 observed
    try:
        compute_stats(rows, ["x"])
        assert False, "expected ValueError for <2 observed"
    except ValueError:
        pass


def test_engine_fills_missing_and_keeps_observed():
    eng = ImputationEngine(_ROWS, POOL, _params())
    it, _ = eng.run(100, 0.005, 3)
    assert it is not None  # converged

    # observed cells are untouched
    assert eng.cur["m1"][0] == 1.0      # A.m1
    assert eng.cur["m2"][1] == 20.0     # B.m2
    # missing cells are filled (not None) and clipped into [lo, clip]
    lo_m1 = eng.stats["m1"][0]
    clip_m1 = eng.stats["m1"][4]
    assert eng.cur["m1"][3] is not None   # D.m1 imputed
    assert lo_m1 <= eng.cur["m1"][3] <= clip_m1
    assert eng.cur["m2"][2] is not None   # C.m2 imputed
    assert eng.cur["m3"][4] is not None   # E.m3 imputed


def test_engine_respects_min_samples_gate():
    # raise gate so no imputation happens; missing stays at top50mean
    eng = ImputationEngine(_ROWS, POOL, _params())
    eng.min_samples = 999
    eng.run(100, 0.005, 3)
    # D.m1 still missing -> cur uses top50mean fallback (not None)
    assert eng.cur["m1"][3] is not None
    # but it equals the pool top50mean (no real prediction)
    assert eng.cur["m1"][3] == eng.stats["m1"][2]


def test_short_domain_is_not_imputable():
    """域内只有 2 个指标时，排除目标列后只剩 1 列特征，预测值退化为
    兄弟指标的仿射变换——因此不做填补。见 ADR-0011。"""
    params = _params()
    params["domain_groups"] = {"triple": ["m1", "m2", "m3"],
                              "pair": ["m4", "m5"]}
    pool = ["m1", "m2", "m3", "m4", "m5"]
    rows = [{"Model": r["Model"], "m1": r["m1"], "m2": r["m2"],
             "m3": r["m3"], "m4": r["m2"], "m5": r["m3"]} for r in _ROWS]
    eng = ImputationEngine(rows, pool, params)
    assert eng.metric_domains["m1"] == ["m1", "m2", "m3"]
    assert eng.imputable["m1"] is True
    assert eng.metric_domains["m4"] == ["m4", "m5"]
    assert eng.imputable["m4"] is False
    assert eng.imputable["m5"] is False


def test_short_domain_leaves_missing_at_fallback():
    """短域缺值保持 top50mean，不被写入伪造的预测值。"""
    params = _params()
    params["domain_groups"] = {"pair": ["m1", "m2"], "triple": ["m3"]}
    eng = ImputationEngine(_ROWS, POOL, params)
    eng.run(100, 0.005, 3)
    # D.m1 缺值：不填补 -> 仍是初始化用的 top50mean
    assert eng.cur["m1"][3] == eng.stats["m1"][2]
    # C.m2 同域（m1,m2）-> 也不填补
    assert eng.cur["m2"][2] == eng.stats["m2"][2]


def test_three_metric_domain_still_imputes():
    params = _params()
    params["domain_groups"] = {"triple": ["m1", "m2", "m3"]}
    eng = ImputationEngine(_ROWS, POOL, params)
    assert all(eng.imputable[m] for m in POOL)
    eng.run(100, 0.005, 3)
    assert eng.cur["m1"][3] is not None      # D.m1 已填补
    assert eng.cur["m1"][3] <= eng.stats["m1"][4]   # 且在 clip 内


def test_loo_validation_structure():
    # 12 rows; each metric missing in exactly one row -> 11 observed
    # (LOO requires >=10 observed to emit a non-None mae).
    rows = []
    for i in range(12):
        r = {"Model": f"M{i}"}
        for j, m in enumerate(POOL):
            r[m] = None if i == j else str((i + 1) * 10 + j)
        rows.append(r)
    eng = ImputationEngine(rows, POOL, _params())
    eng.run(100, 0.005, 3)
    val = eng.loo_validation()
    assert set(val.keys()) == set(POOL)
    for m in POOL:
        assert set(val[m].keys()) == {"mae", "pct_over10", "n"}
        # each metric observed in 11 rows
        assert val[m]["n"] == 11
        assert val[m]["mae"] is not None
        assert 0.0 <= val[m]["pct_over10"] <= 100.0
