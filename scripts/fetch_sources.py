#!/usr/bin/env python3
"""抓取独立源 leaderboard → 标准化 CSV。

每个源一个函数，产出 ``scripts/.cache/<source>.csv``（第一列 ``model``，
其余为该源的分数列）。抓取失败时回退到已存在的缓存文件。

- LiveBench:  动态定位最新 release 的 table.csv，聚合 7 分类（2.0 优先 + 1.0 历史补充）
- EQ-Bench:   creative_writing.js，提取 model + Elo

SWE-bench 已饱和停用（前沿厂商停止报告），不再抓取。
DeepSWE 上游停更且已退出所有榜单权重（2026-11 退役），不再抓取——
见 docs/adr/0002-retire-deepswe.md。

所有源均为公开网页/文件，无需登录，可被 GitHub Actions 调用。
"""
import csv
import json
import os
import re
import sys
import urllib.request

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

from url_guard import assert_safe_url

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, ".cache")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")


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
    """从首页 HTML 提取 main.<hash>.js，解析最新 release 标识。

    优先匹配 LiveBench 2.0 (v2) release（形如 "20261025" 或 "2026-10-25"）。
    """
    return _livebench_releases(html)[-1]


def _livebench_releases(html):
    """main.js 里声明的全部 2.0 release 标识，升序返回（旧 -> 新）。"""
    m = re.search(r'src="\./static/js/main\.([a-f0-9]+)\.js"', html)
    if not m:
        raise RuntimeError("livebench main.js hash not found")
    js = _get(f"https://livebench.ai/static/js/main.{m.group(1)}.js").decode(
        "utf-8", errors="replace")

    # 1. 优先匹配 LiveBench 2.0 (v2) release（包含 8 位数字如 20261025）
    v2_candidates = re.findall(r'"(202\d{5})"', js)
    if v2_candidates:
        return sorted(set(v2_candidates))

    # 2. 匹配带短横线的日期
    v2_dates = re.findall(r'"(202\d-\d{2}-\d{2})"', js)
    if v2_dates:
        return sorted(set(v2_dates))

    raise RuntimeError("livebench release list not found")


# 只取最新 release：2026-11 起上游每个 release 只含当季子集（30~55 个模型），
# 且已取消 v1 补充口径。缺失的模型不进抓取结果——是否上榜由 registry 的
# 双源确认规则决定，缺的指标走分域回归填补。
LB_RELEASES_KEEP = 1

LB_COLUMNS = [
    ("Long-Horizon", ("long_agentic", "long_horizon")),
    ("Reasoning", ("reasoning",)),
    ("Coding", ("coding",)),
    ("Browser", ("browser",)),
    ("Data Analysis", ("data_analysis",)),
    ("Research", ("research",)),
    ("Design", ("design", "design_layout")),
]


def _parse_lb_table(text, release):
    """解析 data/<release>/table.csv -> {model: row}。

    源站对不存在的路径返回 200 + HTML（GitHub Pages 404 页），因此必须
    校验表头，否则错误页会被静默当成"零行数据"吃掉。
    """
    first = text.lstrip().splitlines()[0] if text.strip() else ""
    if not first.lower().startswith("model"):
        raise RuntimeError(
            f"livebench {release} table.csv is not CSV (head={first[:40]!r})")
    rows = {}
    for r in csv.DictReader(text.splitlines()):
        name = (r.get("model") or "").strip()
        if not name:
            continue
        row = {"model": name, "release": release}
        for label, keys in LB_COLUMNS:
            for k in keys:
                if r.get(k) not in (None, ""):
                    row[label] = r[k]
                    break
        rows[name] = row
    if not rows:
        raise RuntimeError(f"livebench {release} table.csv has no model rows")
    return rows


def fetch_livebench():
    """抓 LiveBench 2.0 **最新 release**（``LB_RELEASES_KEEP`` 默认 1）。

    背景（2026-11 修正）：LiveBench 1.0 补充口径已下线（所有
    table_2026_06_25.csv 均 404），旧实现把 1.0 与 2.0 两代命名合进
    一张表又不记录来源版本，导致同一模型出现多行、分数互相矛盾
    （如 claude-haiku-5.5 三行、Coding 77.6/91.4 并存）。

    现在的口径：
    - 只抓 2.0 最新 release；该表一行一个模型、无 effort 后缀。
    - 每行带 ``release`` 列，merge 在别名冲突时优先最新（见 ADR-0005）。
    - 最新 release 未覆盖的模型不会出现在本表里；它是否仍上榜由 registry
      的双源确认规则决定，缺失的指标走分域回归填补。
    """
    html = _get("https://livebench.ai/").decode("utf-8", errors="replace")
    releases = _livebench_releases(html)[-LB_RELEASES_KEEP:]

    merged_lb = {}
    fetched = []
    for rel in releases:  # 升序，后抓到的覆盖先抓到的 => 最新实测胜出
        url = f"https://livebench.ai/data/{rel}/table.csv"
        try:
            text = _get(url).decode("utf-8")
        except Exception as e:
            print(f"  warning: livebench release {rel} fetch failed: {e}")
            continue
        rows = _parse_lb_table(text, rel)
        merged_lb.update(rows)
        fetched.append((rel, len(rows)))

    if not merged_lb:
        raise RuntimeError("livebench: no release could be fetched")

    out_header = ["model", "release"] + [c for c, _ in LB_COLUMNS]
    out_rows = []
    for m, d in sorted(merged_lb.items()):
        out_rows.append([d.get(c, "") for c in out_header])

    path = _write_csv("livebench.csv", out_header, out_rows)
    detail = ", ".join(f"{r}:{n}" for r, n in fetched)
    print(f"livebench: {len(out_rows)} 模型 <- release {detail} "
          f"(各模型取最新一次实测) -> {os.path.basename(path)}")
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
