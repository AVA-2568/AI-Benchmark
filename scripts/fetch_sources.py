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
    html = _get("https://livebench.ai/").decode("utf-8", errors="replace")
    rel = _livebench_release(html)
    rel_u = rel.replace("-", "_")
    table = _get(f"https://livebench.ai/table_{rel_u}.csv").decode("utf-8")
    cats = json.loads(_get(f"https://livebench.ai/categories_{rel_u}.json").decode("utf-8"))

    rows = list(csv.reader(table.splitlines()))
    header = rows[0]
    col_idx = {c: i for i, c in enumerate(header)}
    model_idx = col_idx.get("model", 0)

    # 判断是否为 LiveBench 2.0 结构（含 long_horizon / browser 等）
    is_v2 = "long_horizon" in col_idx or "Long-Horizon" in cats

    if is_v2:
        # LiveBench 2.0: 7 大宏观能力列
        v2_cols = {
            "Coding": ["coding"],
            "Long-Horizon": ["long_horizon"],
            "Browser": ["browser"],
            "Reasoning": ["reasoning"],
            "Data Analysis": ["data_analysis"],
            "Research": ["research"],
            "Design": ["design_layout"],
        }
        # 同时保留 1.0 兼容列（平滑下游解析与填补）
        out_header = ["model", "Coding", "Long-Horizon", "Browser", "Reasoning", "Data Analysis", "Research", "Design",
                      "Agentic Coding", "IF", "Language", "LiveBench StoryGen", "LiveBench Summarize", "LiveBench Simplify", "LiveBench Theory of Mind"]
        out_rows = []
        for r in rows[1:]:
            if not r or not r[0]:
                continue
            model = r[model_idx]
            row_dict = {}
            for col_name, tasks in v2_cols.items():
                vals = []
                for t in tasks:
                    if t in col_idx:
                        try:
                            vals.append(float(r[col_idx[t]]))
                        except (ValueError, IndexError):
                            pass
                row_dict[col_name] = round(sum(vals) / len(vals), 1) if vals else ""
            
            # 兼容列填充（2.0 中 Browser 与 Long-Horizon 对应智能体能力）
            row_dict["Agentic Coding"] = row_dict["Browser"]
            row_dict["IF"] = ""
            row_dict["Language"] = row_dict["Research"]
            row_dict["LiveBench StoryGen"] = row_dict["Design"]
            row_dict["LiveBench Summarize"] = row_dict["Research"]
            row_dict["LiveBench Simplify"] = ""
            row_dict["LiveBench Theory of Mind"] = row_dict["Reasoning"]

            row_out = [model] + [row_dict.get(c, "") for c in out_header[1:]]
            out_rows.append(row_out)
    else:
        # LiveBench 1.0 遗留结构
        out_header = ["model"] + list(LB_CATEGORIES.keys()) + list(LB_TASK_COLUMNS.keys())
        out_rows = []
        for r in rows[1:]:
            if not r or not r[0]:
                continue
            model = r[model_idx]
            scores = []
            for cat, tasks in LB_CATEGORIES.items():
                vals = []
                for t in tasks:
                    if t in col_idx:
                        try:
                            vals.append(float(r[col_idx[t]]))
                        except (ValueError, IndexError):
                            pass
                scores.append(round(sum(vals) / len(vals), 1) if vals else "")
            for col_name, task_key in LB_TASK_COLUMNS.items():
                val = ""
                if task_key in col_idx:
                    try:
                        val = round(float(r[col_idx[task_key]]), 1)
                    except (ValueError, IndexError):
                        pass
                scores.append(val)
            out_rows.append([model] + scores)

    path = _write_csv("livebench.csv", out_header, out_rows)
    print(f"livebench: {len(out_rows)} 模型, release={rel} (v2={is_v2}) -> {os.path.basename(path)}")
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
