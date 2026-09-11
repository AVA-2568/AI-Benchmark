#!/usr/bin/env python3
"""套餐数据核验管道（verify_plans）。

config.json 里 35 个订阅套餐的月费/额度/折扣是性价比榜的地基，且口径
随官方调价漂移（本项目已两次因套餐数据过时返工）。本脚本把「数据是否
还成立」变成 CI 可执行的检查，人只在告警时介入维护。

三层检查：

- 一致性（离线，确定性）—— 硬伤即 FAIL：
    1. 必填字段：name/monthly/url 非空；discount ∈ (0, 1]；
       creator_match 与 model_match 至少一个非空。
    2. 算术自洽：discount 与 monthly/implied_value（或 monthly/credit_value）
       的偏差 ≤1% 通过，1%~5% 记 WARN（历史舍入），>5% FAIL。
    3. 家族单调性：同一产品线（按名称首词分组）月费升档时，额度
       （implied_value / credit_value / tokens）必须非降——专抓
       「改了 A 档忘了 B 档」。

- 时效（离线）—— WARN：
    source 中最早核验日期距今超过 --max-age（默认 21 天），或 source
    根本没写核验日期。

- 可达性（联网，best-effort）—— WARN：
    官方页 URL 可达性。多数定价页是 JS 渲染，内容匹配误报率高，
    故只查 HTTP 状态；抓不到仅 WARN，不影响退出码。

退出码：存在 FAIL 时 exit 1（CI 红灯 = 真问题）；WARN 只记录。
输出：results/plan_audit.json + stdout 摘要。

用法：
    python scripts/verify_plans.py --offline   # 仅离线层（pytest 亦走此路径）
    python scripts/verify_plans.py             # 全量（workflow 每周跑）
"""
import argparse
import datetime
import fnmatch
import json
import os
import re
import sys
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
try:
    from pipeline.scoring import _match_pattern, _resolve_scale, _plan_for
except ImportError:
    from scripts.pipeline.scoring import _match_pattern, _resolve_scale, _plan_for

REPO_ROOT = os.path.dirname(BASE)
CONFIG = os.path.join(REPO_ROOT, "config.json")
REGISTRY = os.path.join(REPO_ROOT, "scripts", "model_registry.json")
OUT = os.path.join(REPO_ROOT, "results", "plan_audit.json")

# 联网层参数
URL_TIMEOUT = 20
UA = {"User-Agent": "Mozilla/5.0 (plan-audit; repo AA-AI-Benchmark)"}

# 家族分组：name 首词（GitHub Copilot 取两词）。同产品线才做单调性比较。
_FAMILY_TWO_WORD = {"GitHub Copilot"}


def load_plans():
    with open(CONFIG, encoding="utf-8") as f:
        return json.load(f)["plans"]


# ---------- 可比量解析 ----------

_NUM_WAN_YI = re.compile(r"([\d.,]+)\s*[~\-至]\s*([\d.,]+)\s*(万|亿)|([\d.,]+)\s*(万|亿)")


def parse_tokens(val):
    """tokens 字段 → 绝对数量；无法解析（Credits 制等）返回 None。

    "3500万/月"->3.5e7；"≈2.1~4.2亿/月"->4.2e8（取上限）；"18亿+"->1.8e9。
    Credits/积分/美元口径官方未公布换算，解析不了就不比。
    """
    if not val:
        return None
    m = _NUM_WAN_YI.search(val)
    if not m:
        return None
    try:
        if m.group(1):  # 区间，取上限
            return float(m.group(2).replace(",", "")) * (1e4 if m.group(3) == "万" else 1e8)
        return float(m.group(4).replace(",", "")) * (1e4 if m.group(5) == "万" else 1e8)
    except ValueError:
        return None


def comparable_size(plan):
    """套餐的「额度量」：implied_value > credit_value > tokens 解析值。"""
    for key in ("implied_value", "credit_value"):
        v = plan.get(key)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                pass
    return parse_tokens(plan.get("tokens"))


def family_of(name):
    words = name.split()
    if not words:
        return name
    if " ".join(words[:2]) in _FAMILY_TWO_WORD:
        return " ".join(words[:2])
    return words[0]


# ---------- 检查层 ----------

def load_registry_models():
    """从 scripts/model_registry.json 读取模型列表。"""
    if not os.path.exists(REGISTRY):
        return []
    with open(REGISTRY, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("models", [])


def _extract_slugs(registry_models):
    """从 registry_models（dict 列表或 str 列表）提取 slug 字符串集合/列表。"""
    slugs = []
    for m in registry_models or []:
        if isinstance(m, dict):
            s = m.get("slug")
            if s:
                slugs.append(str(s).strip())
        elif isinstance(m, str):
            s = m.strip()
            if s:
                slugs.append(s)
    return slugs


def check_dead_patterns(plans, registry_models=None):
    """单 Pattern 死规则检测：检查 model_match 是否命中 registry 中至少一个模型。

    若某个 pattern 无法命中任何模型的 slug，记为 DEAD_PATTERN 错误。
    """
    if registry_models is None:
        registry_models = load_registry_models()
    slugs = _extract_slugs(registry_models)

    errs = []
    for p in plans:
        name = p.get("name") or "?"
        patterns = p.get("model_match") or []
        for pat in patterns:
            pat_str = str(pat).strip()
            if not pat_str:
                continue
            matched = any(fnmatch.fnmatch(slug, pat_str) for slug in slugs)
            if not matched:
                errs.append(f"{name}: DEAD_PATTERN model_match pattern '{pat_str}' 未匹配到任何 registry 模型")
    return errs


def check_fields(plan):
    """必填字段与取值域。返回 errors。"""
    errs = []
    name = plan.get("name") or "?"
    if not plan.get("name"):
        errs.append("缺 name")
    if plan.get("monthly") is None:
        errs.append("缺 monthly")
    if not plan.get("url"):
        errs.append("缺 url")
    d = plan.get("discount")
    if d is None or not (0 < float(d) <= 1.0):
        errs.append(f"discount={d} 越界 (0,1]")
    if not (plan.get("creator_match") or plan.get("model_match")):
        errs.append("creator_match 与 model_match 均为空，该套餐永远不会被匹配")
    exclude = plan.get("exclude_match")
    if exclude is not None and not isinstance(exclude, list):
        errs.append("exclude_match 必须为列表")
    if errs:
        errs = [f"{name}: {e}" for e in errs]
    return errs


def check_arithmetic(plan):
    """discount 与 monthly/额度 的自洽性。返回 (errors, warnings)。"""
    errs, warns = [], []
    name = plan.get("name") or "?"
    monthly, discount = plan.get("monthly"), plan.get("discount")
    if monthly is None or discount in (None, 0):
        return errs, warns
    try:
        monthly, discount = float(monthly), float(discount)
    except (TypeError, ValueError):
        return errs, [f"{name}: monthly/discount 非数值"]

    denom = None
    kind = None
    if plan.get("implied_value"):
        denom, kind = float(plan["implied_value"]), "implied_value"
    elif plan.get("credit_value"):
        denom, kind = float(plan["credit_value"]), "credit_value"
    if denom is None or denom <= 0:
        return errs, warns  # discount=1.0 的展示项无额度口径，跳过

    implied_discount = monthly / denom
    dev = abs(implied_discount - discount) / discount
    if dev > 0.05:
        errs.append(
            f"{name}: discount={discount} 与 {kind} 折算 {implied_discount:.4f}"
            f"（{monthly}/{denom}）偏差 {dev:.1%}，>5%")
    elif dev > 0.01:
        warns.append(
            f"{name}: discount={discount} 与 {kind} 折算 {implied_discount:.4f}"
            f" 偏差 {dev:.1%}（历史舍入，建议对齐）")
    return errs, warns


def check_family_monotonic(plans):
    """同产品线月费升档时额度必须非降。返回 errors。"""
    errs = []
    families = {}
    for p in plans:
        families.setdefault(family_of(p.get("name") or ""), []).append(p)
    for fam, group in sorted(families.items()):
        if len(group) < 2:
            continue
        rows = []
        for p in group:
            size = comparable_size(p)
            if size is None:
                rows = None
                break
            rows.append((float(p["monthly"]), size, p["name"]))
        if rows is None:
            continue  # 组内有 Credits 制等不可比项，放弃该组
        rows.sort()
        for (m1, s1, n1), (m2, s2, n2) in zip(rows, rows[1:]):
            if s2 < s1:
                errs.append(
                    f"[{fam}] 月费升档额度反降：{n1} ${m1}/月额度 {s1:.3g} -> "
                    f"{n2} ${m2}/月额度 {s2:.3g}")
    return errs


_DATE_RE = re.compile(r"20\d{2}-\d{2}-\d{2}")


def check_freshness(plan, max_age_days, today):
    """距上次核验的天数超限 / 无核验日期。返回 warnings。

    source 可能叠多次核验记录（原口径日期 + 复核日期），语义取「最近
    一次核验距今多久」，故取 max 而非 min——否则追加新日期永远超龄。
    """
    warns = []
    name = plan.get("name") or "?"
    src = plan.get("source") or ""
    dates = _DATE_RE.findall(src)
    if not dates:
        warns.append(f"{name}: source 无核验日期")
        return warns
    latest = max(dates)
    try:
        age = (today - datetime.date.fromisoformat(latest)).days
    except ValueError:
        warns.append(f"{name}: source 日期 {latest} 无法解析")
        return warns
    if age > max_age_days:
        warns.append(f"{name}: 最近核验日期 {latest} 距今 {age} 天（>{max_age_days}），待复核")
    return warns


def check_url(plan):
    """官方页可达性（best-effort）。返回 (status, warnings)。"""
    url = plan.get("url")
    if not url:
        return None, []
    req = urllib.request.Request(url, headers=UA, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=URL_TIMEOUT) as resp:
            return resp.status, []
    except urllib.error.HTTPError as e:
        return e.code, [f"{plan.get('name')}: 官方页 HTTP {e.code}（{url}）"]
    except Exception as e:  # DNS/超时/SSL —— 页面问题≠数据问题，WARN 即可
        return None, [f"{plan.get('name')}: 官方页不可达（{type(e).__name__}: {e}）"]


# ---------- 双向透视矩阵 ----------

def resolve_plan_model_scale(plan, model_slug):
    """计算某个模型在特定套餐下的生效 scale 与有效 discount。

    返回 (scale, eff_discount, is_fallback)。
    """
    base_discount = float(plan.get("discount") or 1.0)
    scale_map = plan.get("model_cost_scale") or {}
    model_match = plan.get("model_match") or []

    scale = _resolve_scale(model_slug, scale_map) if scale_map else 1.0
    fallback = False
    if scale is None and model_match:
        if model_slug not in model_match and _match_pattern(model_slug, model_match) and scale_map:
            scale = max(float(v) for v in scale_map.values())
            fallback = True
        else:
            scale = 1.0
    elif scale is None:
        scale = 1.0
    eff_discount = round(min(base_discount * scale, 1.0), 6)
    return scale, eff_discount, fallback


def build_coverage_matrix(plans, registry_models=None):
    """构建双向透视矩阵数据：正向（聚合套餐->命中模型）与反向（模型->最优套餐）。"""
    if registry_models is None:
        registry_models = load_registry_models()

    model_list = []
    for m in registry_models or []:
        if isinstance(m, dict):
            slug = (m.get("slug") or "").strip()
            creator = (m.get("creator") or "").strip()
        else:
            slug = str(m).strip()
            creator = ""
        if slug:
            model_list.append({"slug": slug, "creator": creator})

    # 1. 正向透视：带有 model_match 的聚合类套餐
    forward = []
    for p in plans or []:
        if not p.get("model_match"):
            continue
        p_name = p.get("name") or "?"
        p_monthly = p.get("monthly")
        p_discount = float(p.get("discount") or 1.0)
        ex_match = p.get("exclude_match") or []
        m_match = p.get("model_match") or []
        c_match = p.get("creator_match") or []

        hits = []
        for m in model_list:
            slug, creator = m["slug"], m["creator"]
            if _match_pattern(slug, ex_match):
                continue
            matched = (creator in c_match) or _match_pattern(slug, m_match)
            if not matched:
                continue
            scale, eff_discount, fallback = resolve_plan_model_scale(p, slug)
            hits.append({
                "slug": slug,
                "creator": creator,
                "scale": scale,
                "effective_discount": eff_discount,
                "multiplier": round(1.0 / eff_discount, 2) if eff_discount > 0 else 1.0,
                "fallback": fallback,
            })
        forward.append({
            "name": p_name,
            "monthly": p_monthly,
            "discount": p_discount,
            "hit_count": len(hits),
            "hits": hits,
        })

    # 2. 反向透视：全模型最优套餐匹配概览与未覆盖模型高亮
    covered = []
    uncovered = []
    for m in model_list:
        slug, creator = m["slug"], m["creator"]
        best = _plan_for(plans, creator, slug)
        d = float(best.get("discount") or 1.0) if best else 1.0
        if best is None or d >= 1.0:
            status = "API 按量" if best is None else f"名义原价 ({best.get('name')})"
            uncovered.append({
                "slug": slug,
                "creator": creator,
                "status": status,
                "plan_name": best.get("name") if best else None,
                "discount": 1.0,
                "multiplier": 1.0,
            })
        else:
            covered.append({
                "slug": slug,
                "creator": creator,
                "plan_name": best.get("name"),
                "monthly": best.get("monthly"),
                "discount": d,
                "multiplier": round(1.0 / d, 2) if d > 0 else 1.0,
            })

    total = len(model_list)
    return {
        "summary": {
            "total_models": total,
            "covered_count": len(covered),
            "uncovered_count": len(uncovered),
            "coverage_rate": round(len(covered) / total, 4) if total > 0 else 0.0,
        },
        "forward": forward,
        "reverse": {
            "uncovered": uncovered,
            "covered": covered,
        },
    }


def print_coverage_matrix(matrix_data):
    """在控制台直观打印正向透视表与反向透视表。"""
    if not matrix_data:
        return
    print("\n" + "=" * 80)
    print("【正向透视：聚合类套餐命中模型与生效 Scale 审计】")
    print("=" * 80)
    for p in matrix_data.get("forward", []):
        name = p["name"]
        monthly = f"${p['monthly']:.1f}/月" if p.get("monthly") is not None else "免月费"
        disc_pct = f"{p['discount'] * 100:.1f}%"
        base_mult = f"{1.0 / p['discount']:.1f}×" if p['discount'] > 0 else "-"
        print(f"\n* {name} ({monthly}, 基准折扣 {disc_pct} / {base_mult} 杠杆) -> 实际命中 {p['hit_count']} 个模型:")
        for h in p["hits"]:
            fb_flag = " [FALLBACK MAX]" if h.get("fallback") else ""
            print(f"    - {h['slug']:<30} ({h['creator']:<18}) scale={h['scale']:<4.1f} 生效折扣: {h['effective_discount'] * 100:>5.1f}% ({h['multiplier']:>4.1f}×){fb_flag}")

    print("\n" + "=" * 80)
    print("【反向透视：全部模型最优套餐匹配概览与未覆盖专栏】")
    print("=" * 80)
    rev = matrix_data.get("reverse", {})
    summary = matrix_data.get("summary", {})
    tot = summary.get("total_models", 0)
    cov_cnt = summary.get("covered_count", 0)
    uncov_cnt = summary.get("uncovered_count", 0)
    cov_rate = summary.get("coverage_rate", 0.0) * 100
    print(f"模型总数: {tot} | 折扣覆盖: {cov_cnt} ({cov_rate:.1f}%) | 未覆盖/名义原价: {uncov_cnt} ({100 - cov_rate:.1f}%)\n")

    print("-" * 80)
    print(">>> [重点高亮] 未覆盖 / 名义原价模型 (Uncovered / Full Price Models)")
    print("-" * 80)
    uncovered = rev.get("uncovered", [])
    if not uncovered:
        print("  (全部模型均已享受有效折扣覆盖)")
    else:
        for u in uncovered:
            print(f"  * {u['slug']:<30} ({u['creator']:<18}) -> 状态: {u['status']} (折扣: 100.0%, 1.0×)")

    print("\n" + "-" * 80)
    print(">>> [最优匹配] 折扣覆盖模型明细 (Covered Models)")
    print("-" * 80)
    for c in rev.get("covered", []):
        print(f"  * {c['slug']:<30} ({c['creator']:<18}) -> {c['plan_name']:<25} | 折扣: {c['discount'] * 100:>5.1f}% ({c['multiplier']:>4.1f}×)")
    print("=" * 80 + "\n")


# ---------- 汇总 ----------

def audit(plans, max_age_days, today, online, registry_models=None):
    """跑全部检查层，返回审计 dict。"""
    if registry_models is None:
        registry_models = load_registry_models()
    entries = []
    fail = 0
    warn = 0
    for p in plans:
        dead_errs = check_dead_patterns([p], registry_models=registry_models)
        errors = check_fields(p) + check_arithmetic(p)[0] + dead_errs
        warnings = check_arithmetic(p)[1] + check_freshness(p, max_age_days, today)
        url_status = None
        if online:
            url_status, url_warns = check_url(p)
            warnings += url_warns
        status = "fail" if errors else ("warn" if warnings else "pass")
        fail += bool(errors)
        warn += bool(warnings) and not errors
        entries.append({
            "name": p.get("name"),
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "url_status": url_status,
        })
    family_errors = check_family_monotonic(plans)
    for e in family_errors:
        fail += 1
        entries.append({"name": "(family)", "status": "fail",
                        "errors": [e], "warnings": [], "url_status": None})
    coverage_data = build_coverage_matrix(plans, registry_models=registry_models)
    return {
        "run_date": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "max_age_days": max_age_days,
        "online": online,
        "summary": {"plans": len(plans), "pass": len(plans) + len(family_errors) - fail - warn,
                    "warn": warn, "fail": fail},
        "coverage": coverage_data,
        "entries": entries,
    }


def print_report(audit_result):
    s = audit_result["summary"]
    print(f"plan audit: {s['plans']} 套餐 -> pass {s['pass']} / warn {s['warn']} / fail {s['fail']}")
    for e in audit_result["entries"]:
        if e["status"] == "pass":
            continue
        tag = "FAIL" if e["status"] == "fail" else "WARN"
        print(f"  [{tag}] {e['name']}")
        for line in e["errors"] + e["warnings"]:
            print(f"        {line}")
    if "coverage" in audit_result:
        print_coverage_matrix(audit_result["coverage"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true",
                    help="跳过联网层（pytest / 无网环境）")
    ap.add_argument("--max-age", type=int, default=21,
                    help="source 核验日期容忍天数（默认 21）")
    ap.add_argument("--out", default=OUT, help="审计 JSON 输出路径")
    args = ap.parse_args(argv)

    plans = load_plans()
    result = audit(plans, args.max_age, datetime.date.today(),
                   online=not args.offline)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    os.replace(tmp, args.out)
    print_report(result)
    return 1 if result["summary"]["fail"] else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    raise SystemExit(main())
