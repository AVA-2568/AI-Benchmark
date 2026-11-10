#!/usr/bin/env python3
"""解析 AA leaderboard 数据 → CSV。

三级解析链（按优先级降级）：
1. RSC 数据流（scripts/aa_providers.rsc，由 build.py 带 ``RSC: 1`` 头抓取，
   ~1.4MB-2.4MB 纯数据，无 HTML 壳，json.JSONDecoder().raw_decode 直接解析）
2. 整页 HTML 的 __next_f.push 序列化（scripts/aa_providers.html，App Router 流式注水）
3. 整页 HTML 的 __NEXT_DATA__ script 标签（Pages Router 遗留，2026-07 已确认
   AA 迁移后不再出现，保留仅作历史回退）

解析成功后过数据哨兵（行数 + 评分字段非空率），不达标直接失败，
避免半残数据静默污染下游评分。

执行逻辑封装在 ``main()`` 内，仅当以脚本方式运行
（``python parse_aa.py`` / ``build.py`` 子进程）时触发；
模块被 import 时不会自动执行，便于对纯解析/哨兵函数做单测。
"""
import re
import json
import csv
import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

OUT = os.path.dirname(os.path.abspath(__file__))
RSC_PATH = os.path.join(OUT, "aa_providers.rsc")
HTML_PATH = os.path.join(OUT, "aa_providers.html")


# ---------- 解析器 ----------

def _decode_rows_at(text, start):
    """从 text 的指定 '[' 处用标准库 raw_decode 解析出 rows 数组。"""
    i = text.find("[", start)
    if i == -1:
        return None
    try:
        rows, _ = json.JSONDecoder().raw_decode(text, i)
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows
    return None


def extract_via_rsc(path):
    """主路径：RSC 数据流。兼容 initialRows 与历史 rows 结构。"""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    best = None
    for marker in ('"initialRows":[', '"rows":['):
        start = text.find(marker)
        while start != -1:
            rows = _decode_rows_at(text, start + len(marker) - 1)
            if rows and "label" in rows[0] and (best is None or len(rows) > len(best)):
                best = rows
            start = text.find(marker, start + 1)
    return best


def extract_via_next_f_push(path):
    """回退 1：整页 HTML 的 __next_f.push 序列化（JS 字符串，需反转义）。"""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    pat = re.compile(
        r'self\.__next_f\.push\(\s*\[1,\s*"(.*?)"\s*\]\s*\)', re.S
    )
    chunks = pat.findall(html)
    if not chunks:
        return None
    combined = "".join(chunks).encode().decode("unicode_escape")
    for marker in ('"initialRows":[', '"rows":['):
        start = combined.find(marker)
        if start != -1:
            rows = _decode_rows_at(combined, start + len(marker) - 1)
            if rows:
                return rows
    return None


def extract_via_next_data(path):
    """回退 2：__NEXT_DATA__ script 标签（Pages Router 遗留）。"""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        html = f.read()
    m = re.search(
        r'<script\s+id="__NEXT_DATA__"[^>]*>\s*(.*?)\s*</script>',
        html, re.S | re.I,
    )
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None

    def find_rows(obj, depth=0):
        if depth > 12:
            return None
        if isinstance(obj, list) and len(obj) > 100:
            if isinstance(obj[0], dict) and "label" in obj[0]:
                return obj
        if isinstance(obj, dict):
            for v in obj.values():
                r = find_rows(v, depth + 1)
                if r is not None:
                    return r
        if isinstance(obj, list) and len(obj) < 100:
            for item in obj:
                r = find_rows(item, depth + 1)
                if r is not None:
                    return r
        return None

    return find_rows(data)


# ---------- 主解析（三级降级链） ----------
PARSERS = [
    ("RSC stream", lambda: extract_via_rsc(RSC_PATH)),
    ("__next_f.push", lambda: extract_via_next_f_push(HTML_PATH)),
    ("__NEXT_DATA__", lambda: extract_via_next_data(HTML_PATH)),
]

# 数据哨兵阈值（模块级常量，供单测断言）
MIN_ROWS = 400
SENTINEL_FIELDS = [
    "gdpvalNormalized", "terminalbenchHard", "terminalBench40", "scicode",
    "lcr", "omniscience", "ifbench", "hle", "briefcase",
    "omniscienceAccuracy", "omniscienceNonHallucination",
]
MEAN_RATE_MIN = 0.60   # 11 字段平均非空率下限（留波动余量）
FIELD_RATE_MIN = 0.05   # 单字段非空率下限（=0 说明该列已从页面消失）

# 哨兵字段在新旧 AA 数据流中的路径映射
SENTINEL_MAPPING = {
    "gdpvalNormalized": [("model", "scores", "gdpval-aa-normalized"), ("model", "gdpvalNormalized")],
    "terminalbenchHard": [("model", "scores", "terminalbench-hard"), ("model", "terminalbenchHard")],
    "terminalBench40": [("model", "scores", "terminalbench-4-0"), ("model", "terminalBench40")],
    "scicode": [("model", "scores", "scicode"), ("model", "scicode")],
    "lcr": [("model", "scores", "artificial-analysis-long-context-reasoning"), ("model", "lcr")],
    "omniscience": [("model", "omniscience"), ("model", "scores", "omniscience")],
    "ifbench": [("model", "scores", "ifbench"), ("model", "ifbench")],
    "hle": [("model", "scores", "humanitys-last-exam"), ("model", "hle")],
    "briefcase": [("model", "scores", "aa-briefcase"), ("model", "briefcase", "elo"), ("model", "briefcase")],
    "omniscienceAccuracy": [("model", "scores", "omniscience-accuracy"), ("model", "omniscienceAccuracy")],
    "omniscienceNonHallucination": [("model", "scores", "omniscience-non-hallucination"), ("model", "omniscienceNonHallucination")],
}


# ---------- 字段映射（模块级，供单测） ----------
KNOWN_PERF = {
    "medianOutputTokensPerSecond", "percentile05OutputTokensPerSec",
    "percentile05OutputTokensPerSecond", "quartile25OutputTokensPerSecond",
    "quartile75OutputTokensPerSecond", "percentile95OutputTokensPerSecond",
    "medianTimeToFirstTokenSeconds", "percentile05TimeToFirstTokenSeconds",
    "quartile25TimeToFirstTokenSeconds", "quartile75TimeToFirstTokenSeconds",
    "percentile95TimeToFirstTokenSeconds", "medianTimeToFirstAnswerTokenSeconds",
    "medianEndToEndResponseTimeSeconds", "medianReasoningTimeSeconds",
}


def _resolve_path(row, path):
    cur = row
    for p in path:
        if not isinstance(cur, dict):
            return None
        if isinstance(p, (tuple, list)):
            cur = next((cur.get(k) for k in p if cur.get(k) is not None), None)
        else:
            cur = cur.get(p)
    return cur


def get(row, spec):
    """按 spec 路径提取值。
    spec 格式为 (ColName, path1, path2, ...) 或 (ColName, elem1, elem2...)。
    当路径定义为嵌套 tuple/list 时，支持按先后顺序做候选回退。
    """
    paths = spec[1:]
    if not paths:
        return None
    if isinstance(paths[0], (tuple, list)):
        for p in paths:
            val = _resolve_path(row, p)
            if val is not None:
                return val
        return None
    return _resolve_path(row, paths)


def field_rates(rows):
    """计算每个哨兵字段的非空率。

    返回 {field: rate}。兼容新结构 (model.scores[kebab-case]) 与旧结构 (model[camelCase])。
    """
    n = len(rows)
    if n == 0:
        return {f: 0.0 for f in SENTINEL_FIELDS}
    rates = {}
    for f_ in SENTINEL_FIELDS:
        candidates = SENTINEL_MAPPING.get(f_, [("model", f_)])
        n_ok = sum(1 for r in rows if get(r, (f_, *candidates)) is not None)
        rates[f_] = n_ok / n
    return rates


def run_sentinel(rows):
    """数据哨兵：行数 + 字段非空率。不达标抛 AssertionError。"""
    assert len(rows) > MIN_ROWS, (
        f"行数哨兵触发：{len(rows)}（预期 >{MIN_ROWS}），页面结构可能已变化"
    )
    for key in ("label", "model"):
        missing = sum(1 for r in rows if key not in r)
        assert missing == 0, f"{missing} 行缺少字段 '{key}'"

    rates = field_rates(rows)
    mean_rate = sum(rates.values()) / len(rates)

    print(f"rows: {len(rows)}")
    print("字段非空率（全池）: " + ", ".join(
        f"{k}={v:.0%}" for k, v in rates.items()))
    print(f"均值={mean_rate:.0%}")

    bad = [k for k, v in rates.items() if v < FIELD_RATE_MIN]
    assert not bad, f"字段哨兵触发：{bad} 非空率 <{FIELD_RATE_MIN:.0%}，该列可能已从页面消失"
    assert mean_rate >= MEAN_RATE_MIN, (
        f"均值哨兵触发：评分字段平均非空率 {mean_rate:.0%} < {MEAN_RATE_MIN:.0%}"
    )
    return rates


def build_cols(rows):
    """构造输出列定义（含动态发现的额外性能指标）。"""
    extra_perf = sorted({
        k for r in rows
        for k in (r.get("performance") or {})
        if k not in KNOWN_PERF
    })
    cols = [
        ("Model", "label"),
        ("Host API ID", "hostApiId"),
        ("Provider", "host", "name"),
        ("Provider Slug", "host", "slug"),
        ("Model Slug", "model", "slug"),
        ("Creator", "model", "creator", "name"),
        ("Open Weights", "model", "isOpenWeights"),
        ("Deprecated", "model", "deprecated"),
        ("Reasoning Model", "model", "reasoningModel"),
        ("Intelligence Index", "model", "intelligenceIndex"),
        ("Intelligence Index Est.", "model", "intelligenceIndexIsEstimated"),
        ("Omniscience Index", ("model", "omniscience"), ("model", "scores", "omniscience")),
        ("Omniscience Accuracy", ("model", "scores", "omniscience-accuracy"), ("model", "omniscienceAccuracy")),
        ("Omniscience Non-Halluc.", ("model", "scores", "omniscience-non-hallucination"), ("model", "omniscienceNonHallucination")),
        ("GDPval-AA", ("model", "scores", "gdpval-aa-normalized"), ("model", "gdpvalNormalized")),
        ("AA-Briefcase", ("model", "scores", "aa-briefcase"), ("model", "briefcase", "elo"), ("model", "briefcase")),
        ("Terminal-Bench Hard", ("model", "scores", "terminalbench-hard"), ("model", "terminalbenchHard")),
        ("Terminal-Bench v2.1", ("model", "scores", "terminalbench-2-1"), ("model", ("terminalBench21", "terminalbenchV21"))),
        ("Terminal-Bench v4.0", ("model", "scores", "terminalbench-4-0"), ("model", "terminalBench40")),
        ("tau2-Bench Telecom", ("model", "scores", "tau2-bench"), ("model", "tau2")),
        ("tau3-Banking", ("model", "scores", "tau3-banking"), ("model", "tauBanking")),
        ("LCR", ("model", "scores", "artificial-analysis-long-context-reasoning"), ("model", "lcr")),
        ("HLE", ("model", "scores", "humanitys-last-exam"), ("model", "hle")),
        ("GPQA Diamond", ("model", "scores", "gpqa-diamond"), ("model", "gpqa")),
        ("SciCode", ("model", "scores", "scicode"), ("model", "scicode")),
        ("LiveCodeBench", ("model", "scores", "livecodebench"), ("model", "livecodebench")),
        ("AIME 2025", ("model", "scores", "aime-2025"), ("model", "aime25")),
        ("IFBench", ("model", "scores", "ifbench"), ("model", "ifbench")),
        ("CritPt", ("model", "scores", "critpt"), ("model", "critpt")),
        ("APEX Agents", ("model", "scores", "apex-agents-aa"), ("model", "apexAgents")),
        ("ITBench SRE", ("model", "scores", "itbench-aa"), ("model", "itbenchSre")),
        ("Harvey LAB", ("model", "scores", "harvey-lab-aa"), ("model", "harveyLab")),
        ("AutomationBench", ("model", "scores", "automationbench-aa"), ("model", "automationBench")),
        ("MMMU-Pro", ("model", "scores", "mmmu-pro"), ("model", "mmmuPro")),
        ("Context Window", "features", "contextWindowTokens"),
        ("Function Calling", "features", "functionCalling"),
        ("JSON Mode", "features", "jsonMode"),
        ("OpenAI Compatible", "features", "openaiCompatible"),
        ("Price 1M Input", "pricing", "price1mInputTokens"),
        ("Price 1M Output", "pricing", "price1mOutputTokens"),
        ("Cache Hit Price", "pricing", "cacheHitPrice"),
        ("Cache Write Price", "pricing", "cacheWritePrice"),
        ("Cost Per Task", "pricing", "costPerTask"),
        ("Price Class", "pricing", "priceClass"),
        ("Median tok/s", "performance", "medianOutputTokensPerSecond"),
        ("P05 tok/s", ("performance", "percentile05OutputTokensPerSecond"), ("performance", "percentile05OutputTokensPerSec")),
    ]
    for k in extra_perf:
        cols.append((k, "performance", k))
    cols.append(("Footnotes", "footnotes"))
    return cols, extra_perf


def parse_rows():
    """跑三级解析链，返回 (rows, parser_used)。"""
    for name, fn in PARSERS:
        rows = fn()
        if rows:
            return rows, name
        print(f"⚠ {name} 未命中，尝试下一级")
    return None, None


def main():
    rows, parser_used = parse_rows()
    if not rows:
        print("FATAL: 全部解析方式失败（RSC / __next_f.push / __NEXT_DATA__）")
        sys.exit(1)
    # 记录本次使用的解析器，供 build.py 写入 manifest。
    with open(os.path.join(OUT, ".last_parser"), "w", encoding="utf-8") as fh:
        fh.write(parser_used or "")

    run_sentinel(rows)

    cols, extra_perf = build_cols(rows)
    csv_path = os.path.join(OUT, "aa_providers.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow([c[0] for c in cols])
        for r in rows:
            w.writerow([get(r, spec) for spec in cols])

    print(f"CSV -> {csv_path}  ({len(cols)} 列)")
    if extra_perf:
        print(f"🔔 发现新性能指标: {', '.join(extra_perf)}")
    else:
        print("无新增性能指标")


if __name__ == "__main__":
    main()
