#!/usr/bin/env python3
"""一键构建：抓取 AA leaderboard -> 解析 -> 去重 -> 评分 -> 刷新 README。

抓取策略（与 parse_aa.py 的三级解析链配套）：
1. 主路径：带 ``RSC: 1`` 头请求同一 URL，拿 RSC 数据流（~2.4MB 纯数据）
2. 回退：抓整页 HTML（~5.4MB），parse_aa.py 走 __next_f.push / __NEXT_DATA__
3. 最后手段：沿用上次运行留下的缓存文件并打警告（CI 日志可见）

可在本地运行，也可由 GitHub Actions 调用。
"""
import argparse
import datetime
import csv
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)
sys.path.insert(0, BASE)

from pipeline.config import plan_params  # noqa: E402
from url_guard import assert_safe_url  # noqa: E402
from plot_frontier import render as render_frontier  # noqa: E402

RSC = os.path.join(BASE, "aa_providers.rsc")
HTML = os.path.join(BASE, "aa_providers.html")
URL = "https://artificialanalysis.ai/leaderboards/providers"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# RSC 流 2026-07 实测 ~2.4MB；小于该值大概率是错误页/挑战页
RSC_MIN_SIZE = 500_000
HTML_MIN_SIZE = 100_000
MANIFEST = os.path.join(REPO_ROOT, "results", "manifest.json")


class BuildError(RuntimeError):
    """Raised when a build cannot produce a trustworthy result."""


class StaleCacheError(BuildError):
    """Raised when only stale input is available without explicit opt-in."""


def _fetch(url, out_path, min_size, extra_headers=None):
    """curl 优先、urllib 回退的通用抓取。写临时文件成功后才覆盖目标，
    避免失败请求把上次的可用缓存冲掉。"""
    assert_safe_url(url)
    tmp = out_path + ".tmp"
    headers = {"User-Agent": UA}
    headers.update(extra_headers or {})
    try:
        cmd = ["curl", "-sL", "--max-time", "120", url, "-o", tmp]
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
        r = subprocess.run(cmd, check=False)
        if r.returncode == 0 and os.path.exists(tmp) \
                and os.path.getsize(tmp) > min_size:
            os.replace(tmp, out_path)
            print(f"fetched via curl -> {os.path.basename(out_path)}, "
                  f"size={os.path.getsize(out_path)}")
            return True
    except FileNotFoundError:
        pass
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        if len(data) > min_size:
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, out_path)
            print(f"fetched via urllib -> {os.path.basename(out_path)}, "
                  f"size={len(data)}")
            return True
    except Exception as e:
        print(f"urllib fetch failed: {e}")
    if os.path.exists(tmp):
        os.remove(tmp)
    return False


def fetch_data(allow_stale=False, offline=False):
    """获取 RSC/HTML；缓存只有显式允许时才能作为输入。"""
    if offline:
        if os.path.exists(RSC) or os.path.exists(HTML):
            print("offline mode: using existing cache")
            return True, True
        raise BuildError("offline mode requested but no input cache exists")
    if _fetch(URL, RSC, RSC_MIN_SIZE, {"RSC": "1"}):
        return True, False
    print("!! RSC fetch failed, falling back to full HTML")
    if _fetch(URL, HTML, HTML_MIN_SIZE):
        # HTML 是新鲜的，删掉过期 RSC，防止 parse_aa.py 优先吃到旧数据
        if os.path.exists(RSC):
            os.remove(RSC)
            print("removed stale aa_providers.rsc (fresh HTML takes over)")
        return True, False
    if allow_stale and (os.path.exists(RSC) or os.path.exists(HTML)):
        print("!! WARNING: both fetches failed, explicitly reusing STALE cache")
        return True, True
    if os.path.exists(RSC) or os.path.exists(HTML):
        raise StaleCacheError(
            "both fetches failed; stale cache exists but --allow-stale was not set"
        )
    return False, False


def run(script, *args):
    subprocess.run([sys.executable, os.path.join(BASE, script), *args],
                   cwd=BASE, check=True)


def _count(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_config():
    with open(os.path.join(REPO_ROOT, "config.json"), encoding="utf-8") as f:
        return json.load(f)


def _fmt_usd(v):
    return f"${float(v):g}"


def _board_blocks(bkey, board, n_models, today):
    """生成单个榜单的 (snapshot_md, top15_md)。"""
    scored = os.path.join(REPO_ROOT, "results", board["output_csv"])
    val_json = os.path.join(REPO_ROOT, "results", board["validation_json"])
    n_out = _count(scored)

    with open(scored, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    top = rows[:15]
    if bkey == "value":
        # 性价比榜：跟随通用榜名次，展示官方订阅套餐折算成本与购买链接
        lines = [
            "| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for r in top:
            name = (r.get("Plan") or "").strip()
            url = (r.get("Plan URL") or "").strip()
            if name and url:
                plan_cell = f"[{name}]({url})"
            elif name:
                plan_cell = name
            else:
                plan_cell = "API 按量"
            monthly = r.get("Plan Monthly")
            mult = r.get("Plan Multiplier")
            disc = r.get("Plan Discount")
            if not name:
                mult_cell = "1×"
            elif disc and float(disc) >= 1.0:
                mult_cell = "积分"  # 积分/任务制：官方未公布 token 换算
            elif mult:
                mult_cell = f"{float(mult):g}×"
            else:
                mult_cell = "-"
            v_val = r.get("Vision")
            has_v = (v_val is True or str(v_val).strip().lower() in ("yes", "true", "1"))
            v_cell = "👁️" if has_v else "-"
            lines.append(
                "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |"
                .format(
                    r["Rank"], r["Model"], r["Creator"], v_cell,
                    r.get("Weighted Total") or "",
                    r.get("Blended $/1M") or "",
                    plan_cell,
                    _fmt_usd(monthly) if monthly else "-",
                    mult_cell,
                    r.get("Effective $/1M") or "",
                    r.get("Effective ¥/1M") or "",
                    r.get("Value Score") or "",
                ))
    else:
        lines = [
            "| # | Model | Creator | Vision | Score | Imputed |",
            "|---|---|---|---|---|---|",
        ]
        for r in top:
            imp = (r["Imputed"] or "").strip()
            v_val = r.get("Vision")
            has_v = (v_val is True or str(v_val).strip().lower() in ("yes", "true", "1"))
            v_cell = "👁️" if has_v else "-"
            lines.append("| {} | {} | {} | {} | {} | {} |".format(
                r["Rank"], r["Model"], r["Creator"], v_cell,
                r.get("Weighted Total") or "",
                imp or "-",
            ))
    top15_md = "\n".join(lines)

    snapshot_parts = [
        f"> {today} 抓取（{n_models} 精选模型 -> {n_out} 行）。"
    ]
    if os.path.exists(val_json):
        with open(val_json, encoding="utf-8") as f:
            val = json.load(f)
        val_lines = []
        for m, v in val.items():
            if v.get("mae") is not None:
                val_lines.append(
                    f"{m} MAE={v['mae']:.2f}"
                    f" (>10%: {v['pct_over10']}%/{v['n']})"
                )
        if val_lines:
            snapshot_parts.append(f"> 填补验证：{' ; '.join(val_lines)}")

    return "\n".join(snapshot_parts), top15_md, n_out


def _read_fx():
    """读 .cache/fx.json 的 USD→CNY 汇率（缺失/非法时返回 None）。"""
    path = os.path.join(BASE, ".cache", "fx.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return float(json.load(f).get("usd_cny") or 0) or None
    except (OSError, ValueError):
        return None


def _fmt_tokens_m(m_tokens):
    """百万 token 数 → 中文量级短表述（123 -> ≈1.2亿，2460 -> ≈25亿）。"""
    if m_tokens >= 100:
        return f"≈{m_tokens / 100:.0f}亿"
    if m_tokens >= 10:
        return f"≈{m_tokens / 100:.1f}亿"
    return f"≈{m_tokens:.0f}M"


def _plans_block(plans, rows, fx_rate):
    """生成套餐购买指南 markdown。

    rows 为 value_scored.csv 的行（按通用榜名次排序）：每个套餐取其
    creator_match 覆盖范围内通用榜最强的模型，套餐内等效价 = 该模型
    Blended $/1M × 套餐折扣，套餐内 Value = 模型分 ÷ 等效价，按 Value
    降序——同时反映套餐能用到的最强模型与折算价格。套餐名为官方购买
    直链。

    ≈Token/月：官方公布的 token 池（MiniMax）优先；否则按
    API 等价价值 ÷ 最强模型官方混合价（Blended $/1M）折算——即把
    额度全部用于该模型时的 token 量级。
    """
    entries = []
    credit_entries = []
    for p in plans:
        creators = {c.strip() for c in p.get("creator_match") or []}
        models = {m.strip() for m in p.get("model_match") or []}
        best = next((r for r in rows
                     if (r.get("Creator") or "").strip() in creators
                     or (r.get("Model") or "").strip() in models), None)
        if best is None:
            continue
        try:
            blended = float(best.get("Blended $/1M") or 0)
            discount = float(p.get("discount") or 0)
            score = float(best.get("Weighted Total") or 0)
        except ValueError:
            continue
        if not (blended > 0 and 0 < discount <= 1 and score > 0):
            continue
        eff = blended * discount
        monthly = p.get("monthly")
        mult = p.get("multiplier")
        tokens_cell = (p.get("tokens") or "").strip()
        if not tokens_cell:
            value_usd = p.get("implied_value") or p.get("credit_value")
            tokens_cell = (_fmt_tokens_m(value_usd / blended)
                           if value_usd else "-")
        # discount >= 1 的积分制套餐不折算倍率，倍率/折扣列显示 "-"
        if discount >= 1.0:
            mult_cell, disc_cell = "-", "-"
        else:
            mult_cell = f"{float(mult):g}×" if mult else "-"
            disc_cell = f"{round(discount * 100, 1)}%"
        monthly_cny = round(monthly * fx_rate) if (monthly and fx_rate) else None
        name = p.get("name", "?")
        url = (p.get("url") or "").strip()
        name_cell = f"[{name}]({url})" if url else name
        entry = {
            "credit": discount >= 1.0,
            "monthly": monthly or 0,
            "value": score / eff,
            "line": "{} | {} | {} | {} | {} | {} | {} (#{}) | {} | {} | {}".format(
                name_cell,
                _fmt_usd(monthly) if monthly else "-",
                f"¥{monthly_cny}" if monthly_cny else "-",
                mult_cell,
                disc_cell,
                tokens_cell,
                best.get("Model"), best.get("Rank"),
                best.get("Weighted Total"),
                round(eff, 3),
                round(score / eff, 1),
            ),
        }
        (credit_entries if entry["credit"] else entries).append(entry)
    # 可折算套餐按套餐内 Value 降序；积分/任务制单独分组列于表尾
    # （官方未公布 token 换算，按月费升序），避免淹没在混合排序里
    entries.sort(key=lambda e: -e["value"])
    credit_entries.sort(key=lambda e: (e["monthly"], e["line"]))
    lines = [
        "| # | 套餐 | 月费 | ¥/月 | 倍率 | 折扣 | ≈Token/月 | 最强模型（通用榜） | 模型分 | 套餐内 $/1M | Value |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for i, e in enumerate(entries, 1):
        lines.append(f"| {i} | {e['line']} |")
    if credit_entries:
        lines.append(
            "| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，"
            "不参与倍率排序）——* | | | | | | | | | |")
        for i, e in enumerate(credit_entries, len(entries) + 1):
            lines.append(f"| {i} | {e['line']} |")
    return "\n".join(lines)


def update_readme():
    """用最新 scored CSV 刷新 README：每榜单一组 SNAPSHOT/TOP15 区块 +
    套餐购买指南 PLANS_GUIDE 区块。"""
    merged_csv = os.path.join(BASE, "merged.csv")
    today = datetime.date.today().isoformat()
    n_models = _count(merged_csv)
    cfg = _load_config()

    readme = os.path.join(REPO_ROOT, "README.md")
    txt = open(readme, encoding="utf-8").read()

    counts = {}
    for bkey, board in cfg["leaderboards"].items():
        snapshot_md, top15_md, n_out = _board_blocks(
            bkey, board, n_models, today)
        tag = bkey.upper()
        snapshot_name = f"SNAPSHOT_{tag}"
        top15_name = f"TOP15_{tag}"
        if not _has_markers(txt, snapshot_name) or not _has_markers(txt, top15_name):
            raise BuildError(f"README marker missing for {bkey}")
        txt = _replace_block(txt, snapshot_name, snapshot_md)
        txt = _replace_block(txt, top15_name, top15_md)
        counts[bkey] = n_out

    # 套餐购买指南：以 value_scored.csv（通用榜名次）为数据源
    if not _has_markers(txt, "PLANS_GUIDE"):
        raise BuildError("README marker missing for plans guide")
    value_csv = os.path.join(
        REPO_ROOT, "results", cfg["leaderboards"]["value"]["output_csv"])
    with open(value_csv, encoding="utf-8-sig", newline="") as f:
        value_rows = list(csv.DictReader(f))
    plans_md = _plans_block(plan_params(cfg), value_rows, _read_fx())
    txt = _replace_block(txt, "PLANS_GUIDE", plans_md)

    # 能力-成本前沿图（人民币单面板），随构建重生成
    if not _has_markers(txt, "FRONTIER"):
        raise BuildError("README marker missing for frontier chart")
    fx = _read_fx()
    svg = os.path.join(REPO_ROOT, "results", "value_frontier.svg")
    frontier = render_frontier(value_rows, svg, fx)
    print(f"frontier chart: {len(frontier)} models on the best-choice edge")
    txt = _replace_block(
        txt, "FRONTIER",
        "![能力-成本前沿：给定每 1M token 预算时的最优模型]"
        "(results/value_frontier.svg)")

    # 文本榜同款前沿图：纵轴换文本榜综合分
    if not _has_markers(txt, "TEXT_FRONTIER"):
        raise BuildError("README marker missing for text frontier chart")
    text_csv = os.path.join(
        REPO_ROOT, "results", cfg["leaderboards"]["text"]["output_csv"])
    with open(text_csv, encoding="utf-8-sig", newline="") as f:
        text_rows = list(csv.DictReader(f))
    text_svg = os.path.join(REPO_ROOT, "results", "text_frontier.svg")
    text_frontier = render_frontier(
        text_rows, text_svg, fx, ylabel="文本榜综合分")
    print(f"text frontier chart: {len(text_frontier)} models on the edge")
    txt = _replace_block(
        txt, "TEXT_FRONTIER",
        "![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型]"
        "(results/text_frontier.svg)")

    # Atomic write: stage to .tmp, then os.replace, so a crash mid-write
    # never leaves the repo with a half-written README.
    tmp = readme + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(txt)
    os.replace(tmp, readme)
    print("README updated: models=%d out=%s" % (n_models, counts))


def _has_markers(txt, name):
    start = f"<!--{name}_START-->"
    end = f"<!--{name}_END-->"
    s, e = txt.find(start), txt.find(end)
    return s != -1 and e != -1 and e >= s


def _replace_block(txt, name, content):
    """Replace a README marker block; return original text if absent."""
    start = f"<!--{name}_START-->"
    end = f"<!--{name}_END-->"
    s, e = txt.find(start), txt.find(end)
    if s == -1 or e == -1 or e < s:
        print(f"ERROR: marker {name} not found in README", file=sys.stderr)
        return txt
    return txt[:s + len(start)] + "\n" + content + "\n" + txt[e:]


def _read_last_parser():
    """Read the parser name recorded by parse_aa.py (best-effort)."""
    path = os.path.join(BASE, ".last_parser")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read().strip() or None


def _write_manifest(stale, parser=None):
    config_path = os.path.join(REPO_ROOT, "config.json")
    merged_csv = os.path.join(BASE, "merged.csv")
    manifest = {
        "run_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_url": URL,
        "parser": parser,
        "input_sha256": _sha256(merged_csv) if os.path.exists(merged_csv) else None,
        "config_sha256": _sha256(config_path),
        "algorithm_version": "e5b76d2",
        "models": _count(merged_csv),
        "stale": stale,
    }
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    tmp = MANIFEST + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, MANIFEST)
    print(f"manifest updated -> {MANIFEST}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="use existing input cache without network")
    parser.add_argument("--allow-stale", action="store_true",
                        help="allow stale cache when both fetches fail")
    args = parser.parse_args(argv)
    try:
        ok, stale = fetch_data(allow_stale=args.allow_stale, offline=args.offline)
        if not ok:
            raise BuildError("fetch failed")
        run("parse_aa.py")
        if args.offline:
            print("offline mode: skipping independent-source fetch (using cache)")
        else:
            run("fetch_sources.py")
        # 新模型发现先于合并：--apply 入池后 merge 即可带上新模型行
        run("detect_new_models.py", "--apply")
        run("merge.py")
        run("score_aa.py")
        if stale:
            print("stale input: skipping README update")
        else:
            update_readme()
        _write_manifest(stale=stale, parser=_read_last_parser())
    except (BuildError, subprocess.CalledProcessError) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        return 1
    print("BUILD OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
