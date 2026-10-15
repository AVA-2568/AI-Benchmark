#!/usr/bin/env python3
"""抓取独立源 leaderboard → 标准化 CSV。

每个源一个函数，产出 ``scripts/.cache/<source>.csv``（第一列 ``model``，
其余为该源的分数列）。抓取失败时回退到已存在的缓存文件。

- LiveBench:  动态定位最新 release 的 table_*.csv + categories_*.json，聚合 7 分类
- DeepSWE:    JSON API，提取 model + Pass@1%（每模型取最高档）
- EQ-Bench:   creative_writing.js，提取 model + Elo

SWE-bench 已饱和停用（前沿厂商停止报告），不再抓取。

所有源均为公开网页/文件，无需登录，可被 GitHub Actions 调用。
"""
import csv
import json
import os
import re
import urllib.request

from url_guard import assert_safe_url

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, ".cache")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# LiveBench 分类 -> 任务列名映射（与 categories_*.json 一致）
LB_CATEGORIES = {
    "Coding": ["code_generation", "code_completion"],
    "Agentic Coding": ["javascript", "typescript", "python"],
    "IF": ["paraphrase", "simplify", "story_generation", "summarize"],
    "Language": ["connections", "plot_unscrambling", "typos"],
    "Reasoning": ["theory_of_mind", "zebra_puzzle", "spatial", "logic_with_navigation"],
    "Mathematics": ["AMPS_Hard", "integrals_with_game", "math_comp", "olympiad"],
    "Data Analysis": ["consecutive_events", "tablejoin", "tablereformat"],
}

# LiveBench 单项解耦任务列定义（针对文本榜专业能力）
LB_TASK_COLUMNS = {
    "LiveBench StoryGen": "story_generation",
    "LiveBench Summarize": "summarize",
    "LiveBench Simplify": "simplify",
    "LiveBench Theory of Mind": "theory_of_mind",
}


def _get(url):
    """GET 返回 bytes；失败抛异常。"""
    assert_safe_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def _save(name, text):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return path


def _write_csv(name, header, rows):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


# ---------- LiveBench ----------

def _livebench_release(html):
    """从首页 HTML 提取 main.<hash>.js，再从中解析最新 release 日期。

    兼容 LiveBench 2.0 (gen: "v2") 与 1.0 (gen: "v1") 发布结构。
    """
    m = re.search(r'src="\./static/js/main\.([a-f0-9]+)\.js"', html)
    if not m:
        raise RuntimeError("livebench main.js hash not found")
    js = _get(f"https://livebench.ai/static/js/main.{m.group(1)}.js").decode(
        "utf-8", errors="replace")

    # 1. 优先匹配 LiveBench 2.0 (v2) release
    idx = js.find('gen:"v2"')
    if idx != -1:
        pre = js[max(0, idx - 100):idx]
        m_var = re.findall(r'\.\.\.([a-zA-Z0-9_$]+)\.map', pre)
        if m_var:
            m_arr = re.search(r'(?:const|let|var|,)\s*' + re.escape(m_var[-1]) + r'\s*=\s*\[([^\]]+)\]', js)
            if m_arr:
                rels = re.findall(r'"(\d{4}-\d{2}-\d{2})"', m_arr.group(1))
                if rels:
                    return rels[-1]

    # 2. 回退匹配 1.0 (v1)
    m_v1 = re.search(r'pe=\[([^\]]+)\]', js) or re.search(r'\[([^\]]+)\]\.map\([^)]*gen:"v1"', js)
    if m_v1:
        rels = re.findall(r'"(\d{4}-\d{2}-\d{2})"', m_v1.group(1))
        if rels:
            return rels[-1]

    # 3. 全局搜索包含 release 格式日期的数组
    cand_lists = re.findall(r'\[("(?:202\d-\d{2}-\d{2})"(?:\s*,\s*"(?:202\d-\d{2}-\d{2})")*)\]', js)
    all_rels = []
    for cl in cand_lists:
        all_rels.extend(re.findall(r'"(\d{4}-\d{2}-\d{2})"', cl))
    if all_rels:
        return sorted(set(all_rels))[-1]

    raise RuntimeError("livebench release list not found")


def fetch_livebench():
    """抓取 LiveBench 官方数据：LiveBench 2.0 (最新前沿) + LiveBench 1.0 (历史经典补充)。

    - 2.0 最新前沿版 (2026-09-02): 涵盖 Claude 5.5 / GPT-6.1 / Gemini 4 等 44 个当季旗舰。
    - 1.0 最终版 (2026-06-25): 涵盖 GPT-5.4 / Claude 4.7 等历史主力模型。
    两者合并以 2.0 优先，1.0 补充未包含的历史模型，实现 100+ 模型、精选池 97% 的极高真值覆盖。
    """
    html = _get("https://livebench.ai/").decode("utf-8", errors="replace")
    rel = _livebench_release(html)
    rel_u = rel.replace("-", "_")

    # 1. 抓取 2.0 数据
    v2_csv_text = _get(f"https://livebench.ai/table_{rel_u}.csv").decode("utf-8")
    v2_rows = list(csv.DictReader(v2_csv_text.strip().splitlines()))

    merged_lb = {}
    for r in v2_rows:
        m = r.get("model")
        if not m:
            continue
        merged_lb[m] = {
            "model": m,
            "Coding": r.get("coding", ""),
            "Long-Horizon": r.get("long_horizon", ""),
            "Browser": r.get("browser", ""),
            "Reasoning": r.get("reasoning", ""),
            "Data Analysis": r.get("data_analysis", ""),
            "Research": r.get("research", ""),
            "Design": r.get("design_layout", ""),
        }

    # 2. 抓取 1.0 最终版作为历史补充
    try:
        v1_csv_text = _get("https://livebench.ai/table_2026_06_25.csv").decode("utf-8")
        v1_rows = list(csv.DictReader(v1_csv_text.strip().splitlines()))

        def _avg(row, cols):
            vals = []
            for c in cols:
                v = row.get(c)
                if v:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        pass
            return round(sum(vals) / len(vals), 1) if vals else ""

        for r in v1_rows:
            m = r.get("model")
            if not m or m in merged_lb:
                continue
            merged_lb[m] = {
                "model": m,
                "Coding": _avg(r, ["code_generation", "code_completion"]),
                "Long-Horizon": _avg(r, ["javascript", "typescript", "python"]),
                "Browser": _avg(r, ["javascript", "typescript"]),
                "Reasoning": _avg(r, ["zebra_puzzle", "spatial", "logic_with_navigation"]),
                "Data Analysis": _avg(r, ["consecutive_events", "tablejoin", "tablereformat"]),
                "Research": _avg(r, ["summarize", "connections"]),
                "Design": _avg(r, ["story_generation"]),
            }
    except Exception as e:
        print(f"  warning: failed to fetch livebench 1.0 supplementary table: {e}")

    out_header = ["model", "Coding", "Long-Horizon", "Browser", "Reasoning", "Data Analysis", "Research", "Design"]
    out_rows = []
    for m, d in sorted(merged_lb.items()):
        out_rows.append([d.get(c, "") for c in out_header])

    path = _write_csv("livebench.csv", out_header, out_rows)
    print(f"livebench: 合并 v2+v1 共 {len(out_rows)} 模型 (2.0 release={rel}) -> {os.path.basename(path)}")
    return path


# ---------- DeepSWE ----------

def fetch_deepswe():
    """DeepSWE 从 JSON API 抓完整 leaderboard。

    页面改版后 HTML 只渲染 top 17，完整数据在
    ``/artifacts/v1.1/leaderboard-live.json``（rows = (model, effort) 组合）。
    每个模型取 pass_rate 最高的档（与旧 HTML 按分数降序取首个一致）。
    model 名把版本号连字符转点号（claude-opus-4-8 -> claude-opus-4.8、
    kimi-k2-7-code -> kimi-k2.7-code）以对齐 registry slug。
    """
    data = json.loads(_get(
        "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json"
    ).decode("utf-8"))
    best = {}
    for r in data.get("rows") or []:
        model = r.get("model")
        pr = r.get("pass_rate")
        if not model or pr is None:
            continue
        pr = float(pr)
        if model not in best or pr > best[model]:
            best[model] = pr

    def _normalize(m):
        return re.sub(r"(\d+)-(\d+)", r"\1.\2", m)

    out = [[_normalize(m), round(pr * 100)] for m, pr in sorted(best.items())]
    path = _write_csv("deepswe.csv", ["model", "Pass@1"], out)
    print(f"deepswe: {len(out)} 模型 -> {os.path.basename(path)}")
    return path


# ---------- EQ-Bench ----------

def fetch_eqbench():
    js = _get("https://eqbench.com/creative_writing.js").decode(
        "utf-8", errors="replace")
    # 数据是 JS 里的一段 CSV 字符串：
    # model_name,elo_score,creative_writing_score,avg_length,...
    # *claude-opus-5,2102.5,17.07,6003,...
    m = re.search(r'model_name,elo_score,creative_writing_score'
                  r'[^\n]*\n(.+?)(?:\n\s*\n|\n\s*["\']|\Z)', js, re.S)
    if not m:
        raise RuntimeError("eqbench CSV not found")
    rows = []
    for line in m.group(1).strip().splitlines():
        parts = line.split(",")
        if len(parts) < 2:
            continue
        model = parts[0].lstrip("*").strip()
        elo = parts[1].strip()
        if model and elo:
            rows.append([model, elo])
    # 去重（保留第一个）
    seen, dedup = set(), []
    for r in rows:
        if r[0] not in seen:
            seen.add(r[0])
            dedup.append(r)
    path = _write_csv("eqbench.csv", ["model", "Elo"], dedup)
    print(f"eqbench: {len(dedup)} 模型 -> {os.path.basename(path)}")
    return path


# ---------- 汇率 ----------

def fetch_fx():
    """抓取 USD→CNY 汇率，写 .cache/fx.json。

    主源 Frankfurter（ECB 官方参考汇率，无 key、无限流），
    备源 open.er-api.com。返回 {usd_cny, date}。
    """
    usd_cny, date = None, None
    # 主源：Frankfurter
    try:
        data = json.loads(_get(
            "https://api.frankfurter.dev/v2/rates?base=USD&quotes=CNY"
        ).decode("utf-8"))
        row = data[0]
        usd_cny = float(row["rate"])
        date = row["date"]
    except Exception as e:
        print(f"  frankfurter failed: {e}, fallback open.er-api")
    # 备源：open.er-api.com
    if usd_cny is None:
        data = json.loads(_get(
            "https://open.er-api.com/v6/latest/USD").decode("utf-8"))
        usd_cny = float(data["rates"]["CNY"])
        date = (data.get("time_last_update_utc") or "")[:10]
    fx = {"usd_cny": round(usd_cny, 4), "date": date}
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, "fx.json"), "w", encoding="utf-8") as f:
        json.dump(fx, f)
    print(f"fx: 1 USD = {fx['usd_cny']} CNY ({date})")
    return fx


# ---------- OpenRouter (Modalities / Vision) ----------

def fetch_openrouter():
    """抓取 OpenRouter models 架构与模态元数据，写 .cache/openrouter_models.json。"""
    raw = _get("https://openrouter.ai/api/v1/models")
    data = json.loads(raw.decode("utf-8"))
    models = data.get("data", [])
    path = _save("openrouter_models.json",
                 json.dumps(models, ensure_ascii=False, indent=2))
    print(f"openrouter: cached {len(models)} models ({path})")
    return models


FETCHERS = {
    "livebench": fetch_livebench,
    "deepswe": fetch_deepswe,
    "eqbench": fetch_eqbench,
    "fx": fetch_fx,
    "openrouter": fetch_openrouter,
}


def main():
    import sys
    only = sys.argv[1:] if len(sys.argv) > 1 else list(FETCHERS)
    failed = []
    for name in only:
        if name not in FETCHERS:
            print(f"unknown source: {name}")
            continue
        try:
            FETCHERS[name]()
        except Exception as e:
            print(f"!! {name} fetch failed: {e}")
            failed.append(name)
    if failed:
        print(f"FAILED sources: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
