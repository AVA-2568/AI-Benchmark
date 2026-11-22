"""Unit tests for build._plans_block (套餐购买指南渲染，纯函数无 IO)."""
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from build import _plans_block  # noqa: E402


def _row(model, creator, blended, total, rank):
    return {"Model": model, "Creator": creator,
            "Blended $/1M": blended, "Weighted Total": total, "Rank": rank}


def _plan(name, creators, discount, monthly, mult, url="", value=None,
          tokens=""):
    return {"name": name, "creator_match": creators, "discount": discount,
            "monthly": monthly, "multiplier": mult, "url": url,
            "implied_value": value, "credit_value": None, "tokens": tokens}


def test_sorts_by_plan_value_and_renders_links():
    # rows 按通用榜名次排序（fable-5 #1，gpt-sol #2）
    rows = [
        _row("fable-5", "Anthropic", "9.0", "77.9", 1),
        _row("gpt-sol", "OpenAI", "11.0", "73.2", 2),
    ]
    plans = [
        _plan("Claude Max 20x", ["Anthropic"], 0.025, 200, 40.0,
              "https://claude.com/pricing", value=8000),
        _plan("ChatGPT Pro 20x", ["OpenAI"], 0.014, 200, 70.0,
              "https://chatgpt.com/pricing", value=14000),
    ]
    md = _plans_block(plans, rows, fx_rate=7.0)
    lines = md.splitlines()
    # 套餐内 Value：ChatGPT = 73.2/(11×0.014)=475 > Claude = 77.9/(9×0.025)=346
    assert "ChatGPT" in lines[2]
    assert "Claude" in lines[3]
    assert "[Claude Max 20x](https://claude.com/pricing)" in md
    assert "¥1400" in md  # 200 × 7.0
    assert "40×" in md and "70×" in md
    assert "2.5%" in md and "1.4%" in md
    assert "fable-5 (#1)" in md and "gpt-sol (#2)" in md
    # token 推算：8000/9.0=889M -> ≈9亿；14000/11.0=1273M -> ≈13亿
    assert "≈9亿" in md
    assert "≈13亿" in md


def test_official_tokens_pool_shown_verbatim():
    # 官方公布的 token 池直接展示，不做推算
    rows = [_row("minimax-m3", "MiniMax", "0.01", "55.1", 35)]
    plans = [_plan("MiniMax Max Token Plan", ["MiniMax"], 0.019, 16.5, 53.0,
                   "https://platform.minimaxi.com/subscribe/token-plan",
                   tokens="18亿+")]
    md = _plans_block(plans, rows, fx_rate=7.0)
    assert "18亿+" in md
    assert "≈" not in md.splitlines()[2]  # 官方数字不带 ≈ 前缀


def test_tokens_dashes_without_value_basis():
    # 既无官方 token 池也无 implied/credit 价值 -> "-",
    rows = [_row("fable-5", "Anthropic", "9.0", "77.9", 1)]
    plans = [_plan("Claude Pro", ["Anthropic"], 0.05, 20, 20.0)]
    md = _plans_block(plans, rows, fx_rate=7.0)
    assert "| - |" in md


def test_best_model_is_first_matching_rank():
    # 多厂商套餐取通用榜名次最靠前的覆盖模型（rows 顺序即名次）
    rows = [
        _row("fable-5", "Anthropic", "9.0", "77.9", 1),
        _row("gpt-sol", "OpenAI", "11.0", "73.2", 2),
    ]
    plans = [_plan("Copilot Max", ["OpenAI", "Anthropic"], 0.5, 100, 2.0)]
    md = _plans_block(plans, rows, fx_rate=None)
    lines = md.splitlines()
    assert "fable-5 (#1)" in md
    # 无汇率时数据行 ¥/月 列为 "-"（表头列名含 ¥ 不受影响）
    assert all("¥" not in ln for ln in lines[2:])
    # 每行列数与表头一致
    assert all(ln.count("|") == lines[0].count("|") for ln in lines)


def test_skips_plan_without_covered_models_or_prices():
    rows = [_row("fable-5", "Anthropic", "", "77.9", 1)]
    plans = [
        _plan("NoMatch", ["xAI"], 0.19, 30, 5.3),
        _plan("NoPrice", ["Anthropic"], 0.5, 100, 2.0),
    ]
    md = _plans_block(plans, rows, fx_rate=7.0)
    assert "NoMatch" not in md
    assert "NoPrice" not in md


def test_urlless_plan_renders_plain_name():
    rows = [_row("fable-5", "Anthropic", "9.0", "77.9", 1)]
    plans = [_plan("Claude Max 20x", ["Anthropic"], 0.025, 200, 40.0)]
    md = _plans_block(plans, rows, fx_rate=7.0)
    assert "| Claude Max 20x |" in md  # 无链接时纯文本
    assert "](" not in md


def test_plans_block_applies_model_cost_scale():
    """_plans_block must apply model_cost_scale consistently with scoring._plan_for."""
    plans = [{
        "name": "GLM Max",
        "creator_match": ["Z.AI"],
        "monthly": 100.0,
        "discount": 0.1,
        "multiplier": 10.0,
        "model_cost_scale": {"glm-flash": 3.0},
        "url": "https://example.com",
    }]
    rows = [{
        "Model": "glm-flash",
        "Creator": "Z.AI",
        "Rank": "1",
        "Weighted Total": "60.0",
        "Blended $/1M": "1.0",
    }]
    md = _plans_block(plans, rows, fx_rate=7.0)
    # Effective discount = 0.1 * 3.0 = 0.3 -> eff price = 0.3, value = 60/0.3 = 200.0
    assert "| 30.0% |" in md
    assert "| 0.3 | 200.0 |" in md
