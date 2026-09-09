#!/usr/bin/env python3
"""检测 registry 维护问题，并可选自动入池（--apply）。

merge.py 以 registry 为白名单，registry 维护不当会静默丢数据。本脚本补上
「发现」环节，做两类检测：

1. **新模型**（new_models）：源里出现、registry 完全没有收录的模型。
2. **别名漏配**（missing_aliases）：registry 已收录但某源字段为 null，而该
   源里存在「规范化 slug」对应的数据 —— 数据其实有，只是别名没配。

默认只读，候选写入 results/new_model_candidates.json 并打印告警；
``--apply`` 时把**确认充分**的新模型自动写入 registry（见下），发现候选
不视为失败（新模型上线是正常事件，不应阻塞榜单刷新）。

关于扫描范围：
- 新模型只扫 LiveBench + DeepSWE（前沿模型评测源，命名规范、几乎无长尾
  噪音）。EQ-Bench / SWE-bench / AA 含大量 open-weights 长尾与旧模型，
  不纳入新模型扫描。
- 别名漏配检测覆盖 aa / eqbench / deepswe / livebench 四个源：这里用
  registry 的 slug 做确定性反向匹配，不存在长尾噪音问题。

自动入池的确认门槛与可维护性：
- **双源确认**：候选需在 ≥2 个独立信号出现才自动入池（livebench /
  deepswe / aa 三者任二）。单源孤立条目（LiveBench 特评项、内部实验名等）
  只留在候选清单并标注原因，不入池——避免错误模型污染榜单。
- **确定性 slug/别名**：slug 由源名剥离 effort 后缀、再规范化版本分隔符
  派生（``claude-fable-5-1`` → ``claude-fable-5.1``）；各源别名只取源数据
  里真实存在的名字，不做模糊猜测。同一模型的点/连字符两种写法按规范化
  slug 归为一组，不会出现「一个模型两条目」或「别名落空」。
- **审计与回滚**：入池条目带 ``auto_added`` 日期标记；registry 顶层可选
  ``auto_add_exclude``（fnmatch 通配）永久排除指定模式；未入池候选连同
  原因写入候选 JSON，全程可追溯。
"""
import argparse
import csv
import datetime
import json
import os
import re
from fnmatch import fnmatch

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)
REGISTRY = os.path.join(BASE, "model_registry.json")
CACHE = os.path.join(BASE, ".cache")
RESULTS = os.path.join(REPO_ROOT, "results")
OUT = os.path.join(RESULTS, "new_model_candidates.json")

# AA 源文件在 scripts/ 下（parse_aa.py 产出），其余源在 .cache/
AA_CSV = os.path.join(BASE, "aa_providers.csv")

# 新模型扫描源：{缓存文件名: registry 中对应的别名字段}
NEW_MODEL_SOURCES = {
    "livebench.csv": "livebench",
    "deepswe.csv": "deepswe",
}


def _norm_candidates(slug):
    """slug 的规范化候选（小写 + 点/连字符互换 + 去实验版后缀）。

    registry 用点号（qwen3.8-max），AA 用连字符（qwen3-8-max）；
    DeepSWE/EQ-Bench 两者都有。互换覆盖所有情况。

    实验版后缀（-exp）是同物异名：LiveBench deepseek-v4-flash-vision-exp
    vs AA deepseek-v4-flash-vision，去后缀后才能命中同一模型。
    """
    s = slug.lower()
    base = s
    for suf in EXP_SUFFIXES:
        if base.endswith(suf) and len(base) > len(suf):
            base = base[:-len(suf)]
            break
    out = [s, s.replace(".", "-"), s.replace("-", ".")]
    if base != s:
        out += [base, base.replace(".", "-"), base.replace("-", ".")]
    return out


def load_registry(registry_path=REGISTRY):
    with open(registry_path, encoding="utf-8") as f:
        return json.load(f)["models"]


def load_whitelists(registry_path=REGISTRY):
    """按源字段分别收集别名 → {源字段: 小写别名集合}。

    各源命名风格不同（LiveBench 带 -high/-max 后缀、DeepSWE 无后缀、
    AA 用连字符），若混成一个集合，A 源的模型名可能被 B 源的别名
    误判为已覆盖，故按源分开匹配。
    """
    models = load_registry(registry_path)
    wl = {key: set() for key in NEW_MODEL_SOURCES.values()}
    for m in models:
        for key in wl:
            v = m.get(key)
            if v is None:
                continue
            for a in (v if isinstance(v, list) else [v]):
                wl[key].add(a.strip().lower())
    return wl


def _read_col(path, col):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r.get(col, "").strip() for r in csv.DictReader(f)
                if (r.get(col) or "").strip()]


def detect_new_models(whitelists, cache_dir=CACHE):
    """返回 {源文件名: [未被覆盖的模型名]}（去重、排序）。"""
    out = {}
    for fname, key in NEW_MODEL_SOURCES.items():
        path = os.path.join(cache_dir, fname)
        if not os.path.exists(path):
            out[fname] = []
            continue
        missing = sorted({
            m for m in _read_col(path, "model")
            if m.lower() not in whitelists[key]
        })
        out[fname] = missing
    return out


def detect_missing_aliases(registry=None, cache_dir=CACHE, aa_csv=AA_CSV):
    """检测 registry 字段为 null、但源里有规范化 slug 数据的模型。

    返回 {源字段: ["slug -> 源内候选名", ...]}。
    """
    if registry is None:
        registry = load_registry()

    def _names(path, col):
        if not os.path.exists(path):
            return set()
        return {n.lower() for n in _read_col(path, col)}

    src = {
        "aa": _names(aa_csv, "Model Slug"),
        "eqbench": _names(os.path.join(cache_dir, "eqbench.csv"), "model"),
        "deepswe": _names(os.path.join(cache_dir, "deepswe.csv"), "model"),
        "livebench": _names(os.path.join(cache_dir, "livebench.csv"), "model"),
    }

    out = {k: [] for k in src}
    for m in registry:
        slug = m["slug"]
        # 精确匹配源：aa / eqbench / deepswe（规范化 slug 命中）
        for field in ("aa", "eqbench", "deepswe"):
            if m.get(field) is None:
                for c in _norm_candidates(slug):
                    if c in src[field]:
                        out[field].append(f"{slug} -> {c}")
                        break
        # livebench：effort 后缀不固定，用前缀匹配（保守，只提示）。
        # 候选须与其它源一致地覆盖点/连字符两种写法——只用 replace(".", "-")
        # 会让「源名带点号」的模型（glm-5.3）整类漏报。
        if m.get("livebench") is None:
            hit = None
            for c in _norm_candidates(slug):
                hit = next((x for x in sorted(src["livebench"])
                            if x.startswith(c)), None)
                if hit:
                    break
            if hit:
                out["livebench"].append(f"{slug} -> {hit}")
    return out


def write_candidates(result, out_path=OUT):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    os.replace(tmp, out_path)
    return out_path


# ---------- 自动入池（--apply） ----------

def _safe_path(path):
    """入口路径规范化：解析为绝对路径，含 .. 分量直接拒绝（目录穿越防护，
    与 url_guard.assert_safe_url 同一防御思路的路径版）。"""
    p = os.path.normpath(os.path.abspath(path))
    if ".." in p.split(os.sep):
        raise ValueError(f"path traversal rejected: {path}")
    return p


# slug 派生时剥离的确定性 effort 后缀（LiveBench 命名习惯，无歧义）
STRIP_SUFFIXES = (
    "-high-effort", "-xhigh-effort", "-max-effort",
    "-medium-effort", "-low-effort",
    "-thinking-auto-high", "-thinking-auto-medium", "-thinking-auto-low",
    "-xhigh", "-high", "-medium", "-low",
)

# 实验版后缀（同模型在别源不带，如 LiveBench deepseek-v4-flash-vision-exp
# vs AA deepseek-v4-flash-vision）：AA/DeepSWE 别名匹配时归一化掉。
EXP_SUFFIXES = ("-exp",)

# AA Creator 名 -> registry 惯用名
CREATOR_FIXUPS = {"Z AI": "Z.AI", "Kimi": "Moonshot AI", "SpaceXAI": "xAI"}

# 无 AA 数据时的 creator 前缀推断（长前缀优先，匹配不上则 Unknown）
PREFIX_CREATORS = {
    "deepseek": "DeepSeek", "kimi": "Moonshot AI", "moonshot": "Moonshot AI",
    "qwen": "Alibaba", "minimax": "MiniMax", "mimo": "Xiaomi",
    "claude": "Anthropic", "gemini": "Google", "glm": "Z.AI",
    "gpt": "OpenAI", "grok": "xAI", "llama": "Meta",
    "longcat": "LongCat", "ernie": "Baidu", "hunyuan": "Tencent",
}


# 版本号分隔符：源间不统一（LiveBench 写 claude-fable-5-1，DeepSWE/registry
# 写 claude-fable-5.1）。只取最左侧一对「数字-数字」，避免把日期后缀
# （...-20251101）或多级版本号一起吃掉。
_VERSION_DASH = re.compile(r"(?<=\d)-(?=\d+(?:[-.]|$))")

# LiveBench 常把发布日拼进名字（claude-opus-4-5-20251101、gpt-5.2-2025-12-11），
# registry slug 一律去掉（见 gpt-5.2 / claude-opus-4.5 现有条目）。
_DATE_COMPACT = re.compile(r"-\d{8}")
_DATE_ISO = re.compile(r"-\d{4}-\d{2}-\d{2}")


def derive_slug(name):
    """源模型名 -> registry slug：小写 + 剥离 effort 后缀 + 版本点号规范化。

    裸 ``-max`` 有歧义（qwen3.8-max 的 max 是型号名，gpt-5.6-luna-max 的
    max 是档位），仅当前面不是版本数字时才剥离。

    版本号一律收敛为点号（slug 规范见 registry note）：``claude-fable-5-1``
    -> ``claude-fable-5.1``，``qwen3-8-max`` -> ``qwen3.8-max``。非纯数字
    分量不参与（``llama-3-70b`` 保持原样），发布日分量先剥离。
    """
    s = name.strip().lower()
    changed = True
    while changed:
        changed = False
        for suf in STRIP_SUFFIXES:
            if s.endswith(suf) and len(s) > len(suf):
                s = s[:-len(suf)]
                changed = True
                break
    if s.endswith("-max") and not re.search(r"\d+(\.\d+)?-max$", s):
        s = s[:-len("-max")]
    s = _DATE_ISO.sub("", s)
    s = _DATE_COMPACT.sub("", s)
    return _VERSION_DASH.sub(".", s, count=1)


def _prefix_creator(slug):
    best = None
    for pre in PREFIX_CREATORS:
        if slug.startswith(pre) and (best is None or len(pre) > len(best)):
            best = pre
    return PREFIX_CREATORS[best] if best else None


def _load_source_names(cache_dir=CACHE, aa_csv=AA_CSV):
    """各源模型名集合；AA 额外保留整行以提取 Creator。"""
    def _set(path):
        if not os.path.exists(path):
            return set()
        return {n.lower() for n in _read_col(path, "model")}

    aa_idx = {}
    if os.path.exists(aa_csv):
        with open(aa_csv, encoding="utf-8-sig", newline="") as f:
            aa_idx = {(r.get("Model Slug") or "").strip(): r
                      for r in csv.DictReader(f)
                      if (r.get("Model Slug") or "").strip()}
    return {
        "livebench": _set(os.path.join(cache_dir, "livebench.csv")),
        "deepswe": _set(os.path.join(cache_dir, "deepswe.csv")),
        "eqbench": _set(os.path.join(cache_dir, "eqbench.csv")),
        "aa": aa_idx,
    }


def _pick_alias(names, slug):
    """同组内选别名：优先与 slug 完全一致的写法，否则取字典序首个。

    ``names`` 已排序，结果确定。
    """
    if not names:
        return None
    return next((n for n in names if n.lower() == slug), names[0])


def _group_by_slug(cands):
    """候选名按规范化 slug 归组：{slug: {"livebench": [...], "deepswe": [...]}}。

    同一模型在不同源的分隔符可能不同（LiveBench ``claude-fable-5-1-max-effort``
    vs DeepSWE ``claude-fable-5.1``），按 slug 归组才不会拆成两个条目，也
    不会因「slug 写了点号、源里是连字符」而把别名落空。
    """
    groups = {}
    for fname, key in NEW_MODEL_SOURCES.items():
        for name in cands.get(fname, []):
            g = groups.setdefault(derive_slug(name),
                                  {k: [] for k in NEW_MODEL_SOURCES.values()})
            g[key].append(name)
    for g in groups.values():
        for key in g:
            g[key] = sorted(set(g[key]))
    return groups


def auto_add_candidates(registry_path=REGISTRY, cache_dir=CACHE,
                        aa_csv=AA_CSV, today=None):
    """把双源确认的新模型候选写入 registry，返回 (added, deferred)。

    added 为新入池条目列表；deferred 为 [{name, slug, reason}] —— 未达
    确认门槛 / 命中排除模式 / slug 已存在而跳过的候选。registry 写入为
    原子替换，无新增时不写文件。
    """
    registry_path = _safe_path(registry_path)
    aa_csv = _safe_path(aa_csv)
    with open(registry_path, encoding="utf-8") as f:
        doc = json.load(f)
    models = doc["models"]
    exclude = doc.get("auto_add_exclude", [])
    slugs = {m["slug"].lower() for m in models}

    cands = detect_new_models(load_whitelists(registry_path), cache_dir)
    groups = _group_by_slug(cands)
    src = _load_source_names(cache_dir, aa_csv)

    today = today or datetime.date.today().isoformat()
    added, deferred = [], []
    for slug in sorted(groups):
        group = groups[slug]
        lb_names, ds_names = group["livebench"], group["deepswe"]
        names = sorted(set(lb_names) | set(ds_names))
        rec = {"name": names[0], "slug": slug}
        pat = next((p for p in exclude
                    if fnmatch(slug, p)
                    or any(fnmatch(n, p) for n in names)), None)
        if pat:
            deferred.append({**rec, "reason": f"excluded_by_pattern:{pat}"})
            continue
        if slug.lower() in slugs:
            deferred.append({**rec, "reason": "slug_exists"})
            continue

        in_lb = bool(lb_names)
        ds_alias = (_pick_alias(ds_names, slug)
                    or next((c for c in _norm_candidates(slug)
                             if c in src["deepswe"]), None))
        aa_alias = next((c for c in _norm_candidates(slug)
                         if c in src["aa"]), None)
        eq_alias = next((c for c in _norm_candidates(slug)
                         if c in src["eqbench"]), None)

        confirmed = sum([in_lb, ds_alias is not None, aa_alias is not None])
        if confirmed < 2:
            deferred.append({
                **rec,
                "reason": "insufficient_confirmation",
                "sources": {"livebench": in_lb,
                            "deepswe": ds_alias is not None,
                            "aa": aa_alias is not None},
            })
            continue

        creator = None
        if aa_alias:
            raw = (src["aa"][aa_alias].get("Creator") or "").strip()
            creator = CREATOR_FIXUPS.get(raw) or (raw or None)
        entry = {
            "slug": slug,
            "creator": creator or _prefix_creator(slug) or "Unknown",
            "aa": aa_alias,
            # 保留源内真实名字（含 effort 后缀），否则 merge 按别名查不到数据
            "livebench": (lb_names[0] if len(lb_names) == 1
                          else (lb_names or None)),
            "deepswe": ds_alias,
            "swebench": None,
            "eqbench": eq_alias,
            "vision": False,
            "auto_added": today,
        }
        try:
            from openrouter_modalities import resolve_model_vision, load_openrouter_models
            or_models = load_openrouter_models()
            has_vision, or_id, _ = resolve_model_vision(entry, or_models)
            entry["vision"] = has_vision
            if or_id:
                entry["openrouter"] = or_id
        except Exception:
            pass

        models.append(entry)
        slugs.add(slug.lower())
        added.append(entry)

    if added:
        tmp = registry_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, registry_path)
    # 同一模型在两源名字不同（如 ox-alpha / ox-alpha-max）会产生两条候选，
    # 其一入池后另一条的 deferred 记录只是噪音，按 slug 过滤掉
    added_slugs = {e["slug"].lower() for e in added}
    deferred = [d for d in deferred if d["slug"].lower() not in added_slugs]
    return added, deferred


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="把双源确认的新模型候选自动写入 registry")
    args = ap.parse_args(argv)

    added, deferred = [], []
    if args.apply:
        try:
            added, deferred = auto_add_candidates()
        except (OSError, ValueError) as exc:
            print(f"!! 自动入池失败（registry 保持原样）: {exc}")

    registry = load_registry()
    new_models = detect_new_models(load_whitelists())
    missing = detect_missing_aliases(registry)
    result = {"new_models": new_models, "missing_aliases": missing}
    if deferred:
        result["deferred"] = deferred
    write_candidates(result)

    if added:
        print(f"自动入池 {len(added)} 个新模型：")
        for e in added:
            alias = ", ".join(f"{k}={e[k]}" for k in
                              ("aa", "livebench", "deepswe", "eqbench")
                              if e[k])
            print(f"    [{e['slug']}] creator={e['creator']}; {alias}")
    for d in deferred:
        print(f"    [未入池 {d['name']}] {d['reason']}")

    n_new = sum(len(v) for v in new_models.values())
    n_missing = sum(len(v) for v in missing.values())

    if n_new:
        print(f"!! 发现 {n_new} 个新模型候选（registry 未收录），"
              f"请评估是否补录：")
        for src, names in new_models.items():
            for n in names:
                print(f"    [新模型 {src}] {n}")
    if n_missing:
        print(f"!! 发现 {n_missing} 个「别名漏配」（源里有数据但 registry 字段"
              f"为 null），请补别名：")
        for src, items in missing.items():
            for it in items:
                print(f"    [漏配 {src}] {it}")
    if not n_new and not n_missing and not deferred:
        print("无候选（新模型与别名漏配均未发现）")
    # 候选出现不视为失败：返回 0 避免阻塞榜单刷新
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
