"""README 头部结论（HERO 区块）必须由 build 渲染，不得手写。

背景：2026-11 维护时发现 README 头部的三榜第一名、分数、最低等效价、
精选池规模四项全部过期（手写句子 vs 自动生成的 SNAPSHOT 不同源）。
现在 HERO 区块纳入 build.py 的 marker 渲染，本测试锁住一致性：
渲染结果与 README 内容不一致即失败，提示重跑 build 或手改 README。
"""
import csv
import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SCRIPTS = os.path.join(_REPO, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import build  # noqa: E402


def _block(txt, name):
    start, end = f"<!--{name}_START-->", f"<!--{name}_END-->"
    assert start in txt and end in txt, f"README 缺少 {name} marker"
    return txt.split(start, 1)[1].split(end, 1)[0].strip()


def _write_board(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Rank", "Model", "Weighted Total", "Effective $/1M"])
        for r in rows:
            w.writerow(r)


def test_hero_block_matches_readme():
    """仓库里的 README 必须与当前渲染结果逐字一致。"""
    cfg = build._load_config()
    readme = os.path.join(_REPO, "README.md")
    with open(readme, encoding="utf-8") as f:
        txt = f.read()
    assert _block(txt, "HERO") == build.hero_block(cfg)


def test_hero_block_renders_from_results(tmp_path):
    """渲染逻辑本身：取各榜第一、性价比榜最低等效价、registry 规模。"""
    _write_board(tmp_path / "g.csv", [
        (1, "top-model", "88.8", "1.5"),
        (2, "second-model", "80.0", "1.0"),
    ])
    _write_board(tmp_path / "t.csv", [(1, "writer-model", "70.1", "2.0")])
    _write_board(tmp_path / "v.csv", [
        (1, "cheap-model", "60.0", "0.25"),
        (2, "cheaper-model", "55.0", "0.004"),
    ])
    boards = {
        "general": {"output_csv": "g.csv"},
        "text": {"output_csv": "t.csv"},
        "value": {"output_csv": "v.csv"},
    }
    md = build.hero_block({"leaderboards": boards}, results_dir=str(tmp_path))
    assert f"精选 {build.registry_size()} 个" in md
    assert "当前 top-model 第一，88.8 分" in md
    assert "当前 writer-model 第一，70.1 分" in md
    assert "最低约 $0.004/M" in md
    # 三个 bullet，最后一个用句号收尾
    assert md.count("\n- **") == 3
    assert md.rstrip().endswith("。")


def test_hero_block_tolerates_empty_board(tmp_path):
    """空榜不抛异常（新榜上线首日 / 全部被阈值过滤）。"""
    cfg = {"leaderboards": {"general": {"output_csv": "g.csv"}}}
    _write_board(tmp_path / "g.csv", [])
    md = build.hero_block(cfg, results_dir=str(tmp_path))
    assert "榜单为空" in md


def test_algorithm_version_is_source_derived():
    """algorithm_version 必须是 pipeline 源码摘要，而非写死常量。"""
    ver = build._algorithm_version()
    assert len(ver) == 12
    assert ver == build._algorithm_version()  # 确定性
    assert ver != "e5b76d2"


def test_frontier_line_matches_readme(tmp_path):
    """前沿序列描述与图同源：README 里的那句必须等于当前渲染结果。

    旧版这句是手写的，2026-11 维护时还停留在 gpt-5.4 时代的 8 个模型，
    而实际前沿只剩 5 个点、名字已换代。
    """
    from plot_frontier import render

    cfg = build._load_config()
    rows = build._read_csv_rows(os.path.join(
        _REPO, "results", cfg["leaderboards"]["value"]["output_csv"]))
    frontier = render(rows, str(tmp_path / "f.svg"), build._read_fx())
    with open(os.path.join(_REPO, "README.md"), encoding="utf-8") as f:
        txt = f.read()
    first_line = _block(txt, "FRONTIER").splitlines()[0]
    assert first_line == build._frontier_line(frontier)
