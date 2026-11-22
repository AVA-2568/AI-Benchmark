"""Unit tests for plot_frontier.pareto_frontier (纯函数) 与 render 冒烟。"""
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from plot_frontier import pareto_frontier, render  # noqa: E402


def test_frontier_keeps_increasing_scores_at_rising_prices():
    pts = [(1.0, 50.0, "cheap-weak"), (0.5, 40.0, "cheaper"),
           (2.0, 60.0, "mid"), (3.0, 55.0, "dominated"), (10.0, 70.0, "top")]
    out = pareto_frontier(pts)
    # 价格升序：0.5/40 -> 1.0/50 -> 2.0/60 -> 10.0/70；3.0/55 被 2.0/60 支配
    assert [lbl for _, _, lbl in out] == ["cheaper", "cheap-weak", "mid", "top"]
    scores = [s for _, s, _ in out]
    assert scores == sorted(scores)


def test_frontier_skips_invalid_points():
    pts = [(None, 50.0, "no-price"), (1.0, None, "no-score"),
           (1.0, 30.0, "ok")]
    out = pareto_frontier(pts)
    assert [lbl for _, _, lbl in out] == ["ok"]


def test_frontier_empty_on_all_invalid():
    assert pareto_frontier([(0, 10, "zero"), (None, None, "?")]) == []


def test_render_smoke(tmp_path):
    rows = [
        {"Model": "a", "Effective $/1M": "0.1", "Weighted Total": "40"},
        {"Model": "b", "Effective $/1M": "1.0", "Weighted Total": "60"},
        {"Model": "c", "Effective $/1M": "5.0", "Weighted Total": "73"},
        {"Model": "d", "Effective $/1M": "", "Weighted Total": "70"},
    ]
    out = tmp_path / "f.svg"
    frontier = render(rows, str(out), fx_rate=7.0)
    assert out.exists() and out.stat().st_size > 0
    assert [lbl for _, _, lbl in frontier] == ["a", "b", "c"]


def test_render_text_board_ylabel_and_adaptive_ylim(tmp_path):
    # 文本榜分数整体低于通用榜：y 轴须自适应下探，ylabel 透传
    rows = [
        {"Model": "a", "Effective $/1M": "0.1", "Weighted Total": "43.9"},
        {"Model": "b", "Effective $/1M": "1.0", "Weighted Total": "55"},
        {"Model": "c", "Effective $/1M": "5.0", "Weighted Total": "77.1"},
    ]
    out = tmp_path / "text.svg"
    frontier = render(rows, str(out), fx_rate=7.0, ylabel="文本榜综合分")
    assert out.exists() and out.stat().st_size > 0
    assert [lbl for _, _, lbl in frontier] == ["a", "b", "c"]
    svg = out.read_text(encoding="utf-8")
    assert "文本榜综合分" in svg


def test_render_requires_fx_rate():
    with pytest.raises(ValueError, match="fx_rate"):
        render([{"Model": "a", "Effective $/1M": "1", "Weighted Total": "5"}],
               "unused.svg", fx_rate=None)


def test_render_raises_on_empty():
    with pytest.raises(ValueError):
        render([], "unused.svg", fx_rate=7.0)


def test_pareto_same_price_picks_highest_score_only():
    """Same-price lower-score model appearing first must not enter the Pareto frontier."""
    pts = [(1.0, 50.0, "weak"), (1.0, 80.0, "strong"), (2.0, 90.0, "top")]
    front = pareto_frontier(pts)
    assert [p[2] for p in front] == ["strong", "top"]
