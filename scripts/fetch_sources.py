#!/usr/bin/env python3
"""抓取 4 个独立源 leaderboard → 标准化 CSV。

每个源一个函数，产出 ``scripts/.cache/<source>.csv``（第一列 ``model``，
其余为该源的分数列）。抓取失败时回退到已存在的缓存文件。

- LiveBench:  动态定位最新 release 的 table_*.csv + categories_*.json，聚合 7 分类
- DeepSWE:    静态 HTML，提取 model[effort] + Pass@1%
- SWE-bench:  静态 HTML，提取 model + % Resolved
- EQ-Bench:   creative_writing.js，提取 model + Elo

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

    main.js 里有 ``const pe=["2024-06-24",...,"2026-06-25"]``，
    最新 release = 列表最后一个；URL 里 ``-`` 替换为 ``_``。
    """
    m = re.search(r'src="\./static/js/main\.([a-f0-9]+)\.js"', html)
    if not m:
        raise RuntimeError("livebench main.js hash not found")
    js = _get(f"https://livebench.ai/static/js/main.{m.group(1)}.js").decode(
        "utf-8", errors="replace")
    m2 = re.search(r'pe=\[([^\]]+)\]', js)
    if not m2:
        raise RuntimeError("livebench release list not found")
    rels = re.findall(r'"(\d{4}-\d{2}-\d{2})"', m2.group(1))
    if not rels:
        raise RuntimeError("livebench release list empty")
    return rels[-1]


def fetch_livebench():
    html = _get("https://livebench.ai/").decode("utf-8", errors="replace")
    rel = _livebench_release(html)
    rel_u = rel.replace("-", "_")
    # cache-busting 版本号从 main.js 里读取，缺失时用 0（文件仍可下载）
    table = _get(
        f"https://livebench.ai/table_{rel_u}.csv?v=1786579081").decode("utf-8")
    cats = json.loads(_get(
        f"https://livebench.ai/categories_{rel_u}.json?v=1786579081").decode("utf-8"))

    rows = list(csv.reader(table.splitlines()))
    header = rows[0]
    col_idx = {c: i for i, c in enumerate(header)}
    model_idx = col_idx.get("model", 0)

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
    print(f"livebench: {len(out_rows)} 模型, release={rel} -> {os.path.basename(path)}")
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


# ---------- SWE-bench ----------

def fetch_swebench():
    html = _get("https://www.swebench.com/").decode("utf-8", errors="replace")
    # 数据是内嵌 JSON 数组，每个对象含 name(含 effort)/per_instance_details。
    # % Resolved = per_instance_details 中 resolved=true 的比例。
    i = html.find('"model_display"')
    if i == -1:
        raise RuntimeError("swebench JSON not found")
    start = html.rfind('[{', 0, i)
    if start == -1:
        start = html.rfind('[', 0, i)
    try:
        arr, _ = json.JSONDecoder().raw_decode(html, start)
    except json.JSONDecodeError:
        raise RuntimeError("swebench JSON decode failed")
    rows = []
    for obj in arr:
        name = obj.get("name")
        details = obj.get("per_instance_details") or {}
        if not name or not details:
            continue
        n = len(details)
        ok = sum(1 for d in details.values() if d.get("resolved"))
        rows.append([name, round(ok / n * 100, 1) if n else ""])
    path = _write_csv("swebench.csv", ["model", "Resolved"], rows)
    print(f"swebench: {len(rows)} 模型 -> {os.path.basename(path)}")
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


# ---------- BrowseComp ----------

def fetch_browsecomp():
    """BrowseComp 网页自主浏览与搜索智能体评测。"""
    path = os.path.join(CACHE, "browsecomp.csv")
    try:
        html = _get("https://benchlm.ai/benchmarks/browsecomp").decode("utf-8", errors="replace")
        matches = re.findall(r'\"model\":\"(.*?)\",\"slug\":(\"[^\"]+\"|null).*?\"score\":([0-9.]+)', html)
        rows = []
        for m_name, slug_raw, score in matches:
            slug = json.loads(slug_raw) if slug_raw != "null" else ""
            rows.append([m_name, slug or "", score])
        if rows:
            return _write_csv("browsecomp.csv", ["model", "slug", "BrowseComp"], rows)
    except Exception as e:
        print(f"  browsecomp remote fetch error: {e}, fallback cache")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
        print(f"browsecomp: {n} 模型 -> {os.path.basename(path)}")
        return path
    return _write_csv("browsecomp.csv", ["model", "slug", "BrowseComp"], [])


# ---------- EQ-Bench 4 ----------

def fetch_eqbench4():
    """EQ-Bench 4 多轮人设立体对话与情商评测。"""
    path = os.path.join(CACHE, "eqbench4.csv")
    try:
        html = _get("https://benchlm.ai/benchmarks/eqbench4").decode("utf-8", errors="replace")
        matches = re.findall(r'\"model\":\"(.*?)\",\"slug\":(\"[^\"]+\"|null).*?\"score\":([0-9.]+)', html)
        rows = []
        for m_name, slug_raw, score in matches:
            slug = json.loads(slug_raw) if slug_raw != "null" else ""
            rows.append([m_name, slug or "", score])
        if rows:
            return _write_csv("eqbench4.csv", ["model", "slug", "EQ-Bench 4"], rows)
    except Exception as e:
        print(f"  eqbench4 remote fetch error: {e}, fallback cache")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
        print(f"eqbench4: {n} 模型 -> {os.path.basename(path)}")
        return path
    return _write_csv("eqbench4.csv", ["model", "slug", "EQ-Bench 4"], [])


# ---------- AA Briefcase ----------

def fetch_aabriefcase():
    """Artificial Analysis Briefcase 专业白领知识工作评测。"""
    path = os.path.join(CACHE, "aabriefcase.csv")
    try:
        html = _get("https://benchlm.ai/benchmarks/aabriefcaseelo").decode("utf-8", errors="replace")
        matches = re.findall(r'\"model\":\"(.*?)\",\"slug\":(\"[^\"]+\"|null).*?\"score\":([0-9.]+)', html)
        rows = []
        for m_name, slug_raw, score in matches:
            slug = json.loads(slug_raw) if slug_raw != "null" else ""
            rows.append([m_name, slug or "", score])
        if rows:
            return _write_csv("aabriefcase.csv", ["model", "slug", "AA Briefcase"], rows)
    except Exception as e:
        print(f"  aabriefcase remote fetch error: {e}, fallback cache")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
        print(f"aabriefcase: {n} 模型 -> {os.path.basename(path)}")
        return path
    return _write_csv("aabriefcase.csv", ["model", "slug", "AA Briefcase"], [])


# ---------- DeepSearchQA ----------

def fetch_deepsearchqa():
    """DeepSearchQA 长程深度信息检索与开放式问答评测。"""
    path = os.path.join(CACHE, "deepsearchqa.csv")
    try:
        html = _get("https://benchlm.ai/benchmarks/deepsearchqa").decode("utf-8", errors="replace")
        matches = re.findall(r'\"model\":\"(.*?)\",\"slug\":(\"[^\"]+\"|null).*?\"score\":([0-9.]+)', html)
        rows = []
        for m_name, slug_raw, score in matches:
            slug = json.loads(slug_raw) if slug_raw != "null" else ""
            rows.append([m_name, slug or "", score])
        if rows:
            return _write_csv("deepsearchqa.csv", ["model", "slug", "DeepSearchQA"], rows)
    except Exception as e:
        print(f"  deepsearchqa remote fetch error: {e}, fallback cache")
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.DictReader(f))
        print(f"deepsearchqa: {n} 模型 -> {os.path.basename(path)}")
        return path
    return _write_csv("deepsearchqa.csv", ["model", "slug", "DeepSearchQA"], [])


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
    "swebench": fetch_swebench,
    "eqbench": fetch_eqbench,
    "browsecomp": fetch_browsecomp,
    "eqbench4": fetch_eqbench4,
    "aabriefcase": fetch_aabriefcase,
    "deepsearchqa": fetch_deepsearchqa,
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
