"""Unit tests for pipeline.scoring (norm / fmt_val / score_board).

``score_board`` is tested in isolation with a lightweight fake
engine (mimics the attributes the real ``ImputationEngine``
exposes) so the test does not depend on imputation numerics.
"""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from pipeline import fmt_val, norm, score_board  # noqa: E402


# ---- norm ----

def test_norm_midpoint():
    assert norm(50, 0, 100) == 50.0

def test_norm_bounds():
    assert norm(0, 0, 100) == 0.0
    assert norm(100, 0, 100) == 100.0

def test_norm_flat_range():
    assert norm(7, 3, 3) == 50.0


# ---- fmt_val ----

def test_fmt_val_plain():
    assert fmt_val(0.531, False, False) == "0.531"

def test_fmt_val_imputed():
    assert fmt_val(0.531, True, False) == "0.531*"

def test_fmt_val_low_beats_imputed():
    assert fmt_val(0.531, True, True) == "0.531**"


# ---- score_board (isolated fake engine) ----

class FakeEngine:
    """Minimal stand-in for ImputationEngine for score_board."""

    def __init__(self):
        self.pool = ["m1", "m2"]
        # (lo, hi, top50mean, p90, clip)
        self.stats = {
            "m1": (0.0, 100.0, 50.0, 95.0, 100.0),
            "m2": (0.0, 50.0, 25.0, 47.0, 50.0),
        }
        self.cur = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
        self.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
        self.imputation_quality = {
            "m1": {"n_train": 2},
            "m2": {"n_train": 2},
        }
        self.min_samples = 3


_BOARD = {
    "categories": [
        {"name": "c1", "weight": 0.5,
         "metrics": [{"name": "m1", "sub_weight": 1.0}]},
        {"name": "c2", "weight": 0.5,
         "metrics": [{"name": "m2", "sub_weight": 1.0}]},
    ]
}

_COST = {"input_share": 0.7, "output_share": 0.3, "cache_hit_rate": 0.5}

_ROWS = [
    {"Model": "A", "Price 1M Input": "1.0",
     "Price 1M Output": "2.0", "Cache Hit Price": "0.1"},
    {"Model": "B", "Price 1M Input": "1.0",
     "Price 1M Output": "2.0", "Cache Hit Price": "0.1"},
]


def test_score_board_sorts_and_ranks():
    out, headers = score_board(_ROWS, _BOARD, FakeEngine(),
                                 _COST, 0.1, 0.0)
    assert len(out) == 2
    # both models: m1 norm=80, m2 norm=80 -> total=80; tie -> Model order
    assert out[0]["Model"] == "A"
    assert out[0]["Rank"] == 1
    assert out[1]["Model"] == "B"
    assert out[1]["Rank"] == 2
    assert out[0]["Weighted Total"] == 80.0


def test_score_board_threshold_filter():
    out, _ = score_board(_ROWS, _BOARD, FakeEngine(), _COST, 0.1, 90.0)
    assert out == []  # totals are 80 < 90


def test_score_board_headers_and_norm_columns():
    _, headers = score_board(_ROWS, _BOARD, FakeEngine(), _COST, 0.1, 0.0)
    assert "Rank" in headers and "Model" in headers
    assert "Weighted Total" in headers
    assert "m1" in headers and "m1 (norm)" in headers


def test_score_board_imputed_marker():
    eng = FakeEngine()
    # force one cell to be imputed AND below min_samples -> "(low)" marker
    eng.raw = {"m1": [80.0, None], "m2": [40.0, 10.0]}
    eng.cur = {"m1": [80.0, 33.0], "m2": [40.0, 10.0]}
    eng.imputation_quality = {"m1": {"n_train": 1}, "m2": {"n_train": 2}}
    rows = [
        {"Model": "A", "Price 1M Input": "1.0",
         "Price 1M Output": "2.0", "Cache Hit Price": "0.1"},
        {"Model": "B", "Price 1M Input": "1.0",
         "Price 1M Output": "2.0", "Cache Hit Price": "0.1"},
    ]
    out, _ = score_board(rows, _BOARD, eng, _COST, 0.1, 0.0)
    b = next(r for r in out if r["Model"] == "B")
    # imputed AND below min_samples -> "(reg,low)" marker in Imputed column
    assert "m1(reg,low)" in b["Imputed"]


# ---- cost is unit-price only (thinking effort NOT a factor) ----

def test_score_board_cost_independent_of_thinking_effort():
    """Total $/1M is a per-token unit price: it must depend only on the
    provider's list prices, never on reasoning flag or thinking level.
    Same price -> same $/1M, no matter the (max)/(high) suffix."""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0, 20.0], "m2": [40.0, 10.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "R (max)", "Reasoning Model": "True",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "R (high)", "Reasoning Model": "True",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "N", "Reasoning Model": "False",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
    ]
    out, headers = score_board(rows, _BOARD, eng, _COST, 0.1, 0.0)
    by_model = {r["Model"]: r for r in out}
    costs = {float(by_model[m]["Total $/1M"]) for m in by_model}
    assert len(costs) == 1, "same list price must yield identical $/1M"
    assert "Reasoning Cost ×" not in headers


# ---- real-world cost: per-creator cache rate + plan discount ----

_COST_EFF = {
    "input_share": 0.7, "output_share": 0.3, "cache_hit_rate": 0.5,
    "provider_cache_rates": {"OpenAI": 0.5, "Anthropic": 0.6,
                             "default": 0.1},
}

_PLANS = [
    {"name": "GitHub Copilot Pro+",
     "creator_match": ["OpenAI", "Anthropic", "Google"],
     "discount": 0.557, "monthly": 39, "credit_value": 70,
     "multiplier": 1.8, "url": "https://github.com/features/copilot/plans"},
    {"name": "GitHub Copilot Max",
     "creator_match": ["OpenAI", "Anthropic", "Google"],
     "discount": 0.50, "monthly": 100, "credit_value": 200,
     "multiplier": 2.0, "url": "https://github.com/features/copilot/plans"},
]


def test_effective_cost_applies_subscription_discount():
    """Effective $/1M = standard × cheapest matching plan discount."""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "GPT", "Creator": "OpenAI",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "DS", "Creator": "DeepSeek",
         "Price 1M Input": "0.5", "Price 1M Output": "1.0",
         "Cache Hit Price": "0.005"},
    ]
    out, _ = score_board(rows, _BOARD, eng, _COST_EFF, 0.1, 0.0,
                         plans=_PLANS)
    by_model = {r["Model"]: r for r in out}
    # OpenAI in Copilot catalog: Max (0.50) beats Pro+ (0.557)
    std = float(by_model["GPT"]["Total $/1M"])
    eff = float(by_model["GPT"]["Effective $/1M"])
    blended = float(by_model["GPT"]["Blended $/1M"])
    assert abs(eff - std * 0.50) < 1e-3  # both rounded to 3 decimals
    assert abs(eff - blended * 0.50) < 1e-3
    assert by_model["GPT"]["Plan"] == "GitHub Copilot Max"
    assert by_model["GPT"]["Plan Monthly"] == 100
    assert by_model["GPT"]["Plan Multiplier"] == 2.0
    assert by_model["GPT"]["Plan Discount"] == 0.50
    assert by_model["GPT"]["Plan URL"] == \
        "https://github.com/features/copilot/plans"
    # DeepSeek: no plan -> discount 1.0; cache rate falls to default 0.1
    assert by_model["DS"]["Plan"] == ""
    assert by_model["DS"]["Plan Multiplier"] is None
    assert float(by_model["DS"]["Cache Hit Rate"]) == 0.1
    # effective with hit-rate 0.1, no discount:
    # 0.7*0.9*0.5 + 0.7*0.1*0.005 + 0.3*1.0 = 0.615
    assert abs(float(by_model["DS"]["Effective $/1M"]) - 0.615) < 1e-3


def test_effective_cost_uses_creator_cache_rate():
    """Real-world cost uses per-creator cache rate, not the global 50%."""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "C", "Creator": "Anthropic",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "X", "Creator": "SomeLab",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
    ]
    out, _ = score_board(rows, _BOARD, eng, _COST_EFF, 0.1, 0.0)
    by_model = {r["Model"]: r for r in out}
    # Anthropic: 0.6 cache rate vs SomeLab default 0.1 -> Anthropic
    # pays less for the cached input share -> lower effective cost
    assert float(by_model["C"]["Effective $/1M"]) < \
        float(by_model["X"]["Effective $/1M"])
    assert float(by_model["C"]["Cache Hit Rate"]) == 0.6


def test_effective_cost_falls_back_to_creator_mean_cache_price():
    """Missing Cache Hit Price falls back to the per-creator mean."""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "A", "Creator": "OpenAI",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "B", "Creator": "OpenAI",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": ""},
    ]
    fb = {"OpenAI": 0.5}
    out, _ = score_board(rows, _BOARD, eng, _COST_EFF, 0.1, 0.0,
                         cache_price_fallback=fb)
    by_model = {r["Model"]: r for r in out}
    assert float(by_model["A"]["Effective $/1M"]) == \
        float(by_model["B"]["Effective $/1M"])


def test_effective_cost_blends_cache_write_price():
    """Providers with a Cache Write Price pay write_ratio × write +
    (1-write_ratio) × hit for cached input; without one, hit only."""
    cost = dict(_COST_EFF)
    cost["cache_write_ratio"] = 0.2
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "W", "Creator": "Anthropic",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5", "Cache Write Price": "6.25"},
        {"Model": "H", "Creator": "Anthropic",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5", "Cache Write Price": ""},
    ]
    out, _ = score_board(rows, _BOARD, eng, cost, 0.1, 0.0)
    by_model = {r["Model"]: r for r in out}
    # W: blend = 0.2×6.25 + 0.8×0.5 = 1.65; H: hit only = 0.5
    assert abs(float(by_model["W"]["Cache Hit"]) - 1.65) < 1e-6
    assert abs(float(by_model["H"]["Cache Hit"]) - 0.5) < 1e-6
    # higher cache input price -> W costs more than H
    assert float(by_model["W"]["Effective $/1M"]) > \
        float(by_model["H"]["Effective $/1M"])


def test_value_board_ranks_by_score_per_dollar():
    """rank_by='value' sorts by Weighted Total / Effective $/1M and
    drops rows without a price."""
    board = dict(_BOARD)
    board["rank_by"] = "value"
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0, 20.0, 20.0],
               "m2": [40.0, 10.0, 10.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "Cheap", "Creator": "OpenAI",
         "Price 1M Input": "0.5", "Price 1M Output": "1.0",
         "Cache Hit Price": "0.05"},
        {"Model": "Pricey", "Creator": "OpenAI",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
        {"Model": "NoPrice", "Creator": "OpenAI",
         "Price 1M Input": "", "Price 1M Output": ""},
    ]
    out, headers = score_board(rows, board, eng, _COST_EFF, 0.1, 0.0,
                               plans=_PLANS)
    assert [r["Model"] for r in out] == ["Cheap", "Pricey"]
    assert out[0]["Value Score"] > out[1]["Value Score"]
    assert "Value Score" in headers and "Effective $/1M" in headers


def test_plan_for_skips_credit_metered_plans():
    """discount >= 1 的 Credit/积分计量套餐（Qwen Token Plan / WorkBuddy）
    不参与成本折算：有折扣套餐时折扣优先；仅有积分制时返回最便宜的
    名义套餐（折扣 1.0 = 官方价），保证榜单能显示套餐存在。"""
    from pipeline.scoring import _plan_for
    plans = [
        {"name": "Qwen Token Plan Lite", "creator_match": ["Alibaba"],
         "discount": 1.0, "monthly": 5.4},
        {"name": "Qwen Token Plan Standard", "creator_match": ["Alibaba"],
         "discount": 1.0, "monthly": 19.3},
        {"name": "Hy Token Plan Lite", "creator_match": ["Tencent"],
         "discount": 0.81, "monthly": 3.9},
        {"name": "WorkBuddy Pro", "creator_match": ["Tencent"],
         "discount": 1.0, "monthly": 27.6},
    ]
    # Alibaba 仅有积分制 -> 最便宜的名义套餐
    nominal = _plan_for(plans, "Alibaba")
    assert nominal["name"] == "Qwen Token Plan Lite"
    assert float(nominal["discount"]) == 1.0
    # Tencent 有折扣套餐 -> 折扣优先，积分制不干扰
    best = _plan_for(plans, "Tencent")
    assert best["name"] == "Hy Token Plan Lite"
    assert _plan_for(plans, "DeepSeek") is None


def test_plan_for_model_level_match():
    """OpenCode Go 仅按显式模型清单匹配，避免把同厂商其他模型
    错套到 $60 档折扣。"""
    from pipeline.scoring import _plan_for
    plans = [
        {"name": "OpenCode Go", "model_match": ["hy3", "deepseek-v4-flash",
                                                   "deepseek-v4-pro"],
         "discount": 0.167, "monthly": 10},
        {"name": "腾讯通用 Token Plan Standard", "creator_match": ["DeepSeek"],
         "discount": 0.5, "monthly": 13.8},
    ]
    # 显式 model_match 命中
    assert _plan_for(plans, "DeepSeek", "deepseek-v4-flash")["name"] == \
        "OpenCode Go"
    assert _plan_for(plans, "Tencent", "hy3")["name"] == "OpenCode Go"
    # 同厂商但不在清单中的模型不会误匹配 OpenCode
    assert _plan_for(plans, "Z.AI", "glm-5.3") is None
    assert _plan_for(plans, "DeepSeek", "deepseek-v4-pro")["name"] == \
        "OpenCode Go"


def test_plan_for_compares_scaled_discount():
    """套餐选择必须按 model_cost_scale 修正后的实付折扣比较。

    回归：kimi-k3 在 OpenCode Go 名义 6×（0.167）但 $15 档实付 1.5×
    （0.668），劣于 Kimi 会员的固定 4.5×（0.22）。按名义折扣比较会
    选中实付贵 3 倍的 OpenCode Go。
    """
    from pipeline.scoring import _plan_for
    plans = [
        {"name": "OpenCode Go", "model_match": ["kimi-k3", "kimi-k2.6"],
         "discount": 0.167, "monthly": 10,
         "model_cost_scale": {"kimi-k3": 4.0}},
        {"name": "Kimi 会员 Allegretto", "creator_match": ["Moonshot AI"],
         "discount": 0.22, "monthly": 27.6},
    ]
    chosen = _plan_for(plans, "Moonshot AI", "kimi-k3")
    assert chosen["name"] == "Kimi 会员 Allegretto"
    # $60 档模型（无 scale）名义折扣仍直接参与比较
    assert _plan_for(plans, "Moonshot AI", "kimi-k2.6")["name"] == \
        "OpenCode Go"


def test_effective_cost_model_cost_scale():
    """model_cost_scale：积分制套餐对特定模型的抵扣密度差异按 config
    乘数修正有效折扣（如 glm-5.3-flash 系数为标准版 1/3 → ×3.0），
    只影响 cost 侧展示，不影响 plan 选择和其他模型。"""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    plans = [
        {"name": "GLM Coding Plan Max", "creator_match": ["Z.AI"],
         "discount": 0.029, "monthly": 149.7,
         "model_cost_scale": {"glm-5.3-flash": 3.0},
         "url": "https://bigmodel.cn/glm-coding"},
    ]
    rows = [
        {"Model": "glm-5.3-flash", "Creator": "Z.AI",
         "Price 1M Input": "0.8", "Price 1M Output": "2.8",
         "Cache Hit Price": "0.23"},
        {"Model": "glm-5.3", "Creator": "Z.AI",
         "Price 1M Input": "8", "Price 1M Output": "28",
         "Cache Hit Price": "2"},
    ]
    out, _ = score_board(rows, _BOARD, eng, _COST_EFF, 0.1, 0.0, plans=plans)
    by_model = {r["Model"]: r for r in out}
    # flash: discount 0.029 × 3.0 = 0.087
    assert by_model["glm-5.3-flash"]["Plan Discount"] == 0.087
    # standard: no scale entry -> discount unchanged
    assert by_model["glm-5.3"]["Plan Discount"] == 0.029
    # both matched the same plan (scale doesn't affect plan selection)
    assert by_model["glm-5.3-flash"]["Plan"] == "GLM Coding Plan Max"
    assert by_model["glm-5.3"]["Plan"] == "GLM Coding Plan Max"


def test_model_cost_scale_capped_at_one():
    """model_cost_scale 乘后折扣封顶 1.0（不倒贴）。"""
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 20.0], "m2": [40.0, 10.0]}
    eng.cur = dict(eng.raw)
    plans = [
        {"name": "CheapPlan", "creator_match": ["TestLab"],
         "discount": 0.4, "monthly": 10,
         "model_cost_scale": {"model-x": 3.0}},
    ]
    rows = [
        {"Model": "model-x", "Creator": "TestLab",
         "Price 1M Input": "1", "Price 1M Output": "2",
         "Cache Hit Price": "0.1"},
    ]
    out, _ = score_board(rows, _BOARD, eng, _COST_EFF, 0.1, 0.0, plans=plans)
    # 0.4 × 3.0 = 1.2 -> capped at 1.0
    assert out[0]["Plan Discount"] == 1.0


def test_value_board_follows_general_ranking():
    """rank_by='score'（value 榜默认）：按综合分排序（跟随通用榜名次），
    无价格行保留（Value Score 为 None 而不是被丢弃）。"""
    board = dict(_BOARD)
    board["rank_by"] = "score"
    eng = FakeEngine()
    eng.raw = {"m1": [80.0, 90.0, 20.0], "m2": [40.0, 30.0, 10.0]}
    eng.cur = dict(eng.raw)
    rows = [
        {"Model": "Cheap", "Creator": "OpenAI",
         "Price 1M Input": "0.5", "Price 1M Output": "1.0",
         "Cache Hit Price": "0.05"},
        {"Model": "TopNoPrice", "Creator": "DeepSeek",
         "Price 1M Input": "", "Price 1M Output": ""},
        {"Model": "Pricey", "Creator": "OpenAI",
         "Price 1M Input": "5.0", "Price 1M Output": "25.0",
         "Cache Hit Price": "0.5"},
    ]
    out, headers = score_board(rows, board, eng, _COST_EFF, 0.1, 0.0,
                               plans=_PLANS)
    # totals: Cheap=80, TopNoPrice=75, Pricey=20 -> score order
    assert [r["Model"] for r in out] == ["Cheap", "TopNoPrice", "Pricey"]
    assert out[1]["Value Score"] is None
    assert out[1]["Plan"] == ""
    for col in ("Blended $/1M", "Plan Monthly", "Plan Multiplier",
                "Plan Discount", "Plan URL"):
        assert col in headers
    # cheapest plan wins for OpenAI rows
    assert out[0]["Plan"] == "GitHub Copilot Max"


def test_score_board_feature_bonuses():
    """feature_bonuses adds to Weighted Total if vision is True, up to 100 max."""
    board = dict(_BOARD)
    board["feature_bonuses"] = {"vision": 3.0}
    eng = FakeEngine()
    rows = [
        {"Model": "WithVision", "Vision": True, "Price 1M Input": "1.0",
         "Price 1M Output": "2.0"},
        {"Model": "TextOnly", "Vision": False, "Price 1M Input": "1.0",
         "Price 1M Output": "2.0"},
    ]
    out, headers = score_board(rows, board, eng, _COST, 0.1, 0.0)
    assert "Vision" in headers
    wv = next(r for r in out if r["Model"] == "WithVision")
    to = next(r for r in out if r["Model"] == "TextOnly")
    assert wv["Vision"] == "Yes"
    assert to["Vision"] == "No"
    # Base score is 80.0, WithVision gets +3.0 -> 83.0; TextOnly base is 20.0
    assert wv["Weighted Total"] == 83.0
    assert to["Weighted Total"] == 20.0


def test_plan_for_wildcard_and_exclude():
    from pipeline.scoring import _plan_for

    plans = [
        {
            "name": "Proxy Plan",
            "monthly": 10.0,
            "discount": 0.167,
            "model_match": ["deepseek-v4*", "qwen3.*-max", "muse-spark-1.[23]*"],
            "exclude_match": ["*-27b*", "muse-spark-1.1"],
            "model_cost_scale": {"*-pro": 4.0, "deepseek-v4-flash": 2.0},
        }
    ]
    # 1. 命中通配符且 scale 显式命中
    p1 = _plan_for(plans, "DeepSeek", "deepseek-v4-flash")
    assert p1 is not None and abs(p1["discount"] - 0.167 * 2.0) < 1e-4

    # 2. 命中通配符但 scale 未显式指定 -> 触发最大 scale 4.0 兜底
    p2 = _plan_for(plans, "DeepSeek", "deepseek-v4.1-flash")
    assert p2 is not None and abs(p2["discount"] - 0.167 * 4.0) < 1e-4

    # 3. 命中 exclude 黑名单 -> 一票否决
    p3 = _plan_for(plans, "Meta", "muse-spark-1.1")
    assert p3 is None

    # 4. 正常命中白名单通配
    p4 = _plan_for(plans, "Meta", "muse-spark-1.3")
    assert p4 is not None

    # 5. 通配命中 qwen3.*-max，未显式指定 scale -> 同样触发 4.0 兜底
    p5 = _plan_for(plans, "Alibaba", "qwen3.7-max")
    assert p5 is not None and abs(p5["discount"] - 0.167 * 4.0) < 1e-4

    # 6. 通配命中 qwen3.*-max 但命中了 exclude_match "*-27b*" -> 一票否决
    p6 = _plan_for(plans, "Alibaba", "qwen3.5-27b-max")
    assert p6 is None



