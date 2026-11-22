#!/usr/bin/env python3
"""跨源合并：model_registry.json + 各源 CSV -> merged.csv（统一宽表）。

行 = 注册表里的模型（统一 slug），列 = config.imputation_pool 的
18 个指标 + Model/Creator。各源分数通过别名匹配；livebench 别名可为列表，
多个匹配时取分数最高者。缺失值留空，交由评分阶段的岭回归填补。

数据源：
- AA (scripts/aa_providers.csv)         -> FrontierCode 2.0 / Terminal-Bench v4.0 / AutomationBench / LCR / MLCR / Omniscience Accuracy / HLE Diamond / CritPt v2 Hard / Briefcase / 成本列
    （同一 Model Slug 有多 Provider 行时：分数各行一致，定价取官方行，
    见 _pick_aa_row；视觉变体是独立 slug，不会混入）
- LiveBench (scripts/.cache/livebench.csv) -> Coding / Long-Horizon / Browser / Data Analysis / Reasoning / Research / Design
- EQ-Bench  (scripts/.cache/eqbench.csv)   -> Elo

DeepSWE 于 2026-11 退役：上游停更、不在任何榜单权重内，抓取与合并均已
移除（docs/adr/0002-retire-deepswe.md）。
"""
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
import csv
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(BASE)
CACHE = os.path.join(BASE, ".cache")
REGISTRY = os.path.join(BASE, "model_registry.json")
AA_CSV = os.path.join(BASE, "aa_providers.csv")


def _read_csv(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _alias_index(rows, key_col):
    """{key_col 值 -> 行 dict}，支持一行多列。"""
    idx = {}
    for r in rows:
        k = (r.get(key_col) or "").strip()
        if k:
            idx[k] = r
    return idx


def load_registry():
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)["models"]


def _row_score(row):
    """行内数值列的均值（忽略 model/release 等非数值列），用于跨档位比较。"""
    vals = []
    for k, v in row.items():
        if k in ("model", "release"):
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    return sum(vals) / len(vals) if vals else None


def _release_key(value):
    """release 标识归一为纯数字用于排序（20261106 / 2026-11-06 / 2026_11_06 等价）。"""
    return re.sub(r"\D", "", value or "")


def _pick_best_row(idx, alias):
    """别名可为字符串或列表；返回**最新 release 里综合分最高**的行及其别名。

    优先级（见 ADR-0005）：
    1. release 新的行优先——源站每次 release 会重测/重命名，同一模型在
       不同 release 里可能叫法不同（旧口径带 `-max-effort` 后缀），混用
       会得到互相矛盾的分数；
    2. 同一 release 内多档（`-max` / `-xhigh`）取行内数值列均值最高者；
       源里只公布 `-high` 的就是该模型的最高档；
    3. 同分按别名顺序取先出现者（确定性）。

    旧实现直接返回别名列表里第一个命中的行，既不看 release 也不看分数，
    是 2026-11 维护时 claude-haiku-5.5 出现三行矛盾数据的直接原因。
    """
    if alias is None:
        return None, None
    alist = alias if isinstance(alias, list) else [alias]
    best = None            # (release, score, order, row, alias)
    for order, a in enumerate(alist):
        row = idx.get(a)
        if row is None:
            continue
        score = _row_score(row)
        if score is None:
            continue
        cand = (_release_key(row.get("release")), score, -order, row, a)
        if best is None or cand[:3] > best[:3]:
            best = cand
    if best is None:
        return None, None
    return best[3], best[4]


def _norm_token(s):
    """归一化单个 token：去空白/分隔符 + 小写，供官方行判定用。"""
    return re.sub(r"[\s.\-_]+", "", (s or "").lower())


def _is_official_aa_row(row, registry_creator):
    """AA 行是否为模型官方行：Provider 与 Creator 归一化后互含即官方。

    归一化去空白/分隔符/大小写后，官方行天然互含（"Thinking Machines"
    vs "thinking-machines"、"Z.AI" vs "zai"、"Alibaba" vs
    "alibaba_cloud"、"xAI" vs "SpaceXAI"/"xai"）。唯一特例是
    Moonshot AI（官方 Provider 叫 Kimi），走别名表。
    registry_creator 为空时退回 True（不过滤）。
    """
    if not registry_creator:
        return True
    creator = _norm_token(registry_creator)
    provs = [_norm_token(row.get("Provider Slug")),
             _norm_token(row.get("Provider"))]
    if any(p and (creator in p or p in creator) for p in provs):
        return True
    wants = {"moonshotai": ("kimi",)}.get(creator, ())
    return any(p and any(w in p or p in w for w in wants) for p in provs)


# ---------- AA 行选取 ----------
# AA 的 label 把 reasoning effort 档位写在括号里，且同一 Model Slug 下并列多档
# （non-reasoning / low / medium / high / xhigh / max）。括号里还会出现量化格式
# （FP8 / FP4 / NVFP4 / BF16）与部署标记（FAST / ULTRA / Vertex / AI Studio），
# 这些不代表档位，不参与排序。
AA_TIER_ORDER = {"non-reasoning": 0, "low": 1, "medium": 2,
                 "high": 3, "xhigh": 4, "max": 5}
_TIER_RE = re.compile(r"\(([^()]*)\)")

# AA 来源的池指标。用于判断「该档位行是否真的带评测分数」：小模型的
# non-reasoning 行常常只有定价与老基准，池指标全空，按档位盲选会取到空行。
# 必须与 build_merged 的 cols 中的 AA 项一致（tests/test_merge.py 有断言）。
AA_METRICS = (
    "FrontierCode 2.0", "Terminal-Bench v4.0", "AutomationBench", "LCR", "MLCR",
    "Omniscience Accuracy", "Omniscience Non-Halluc.", "HLE Diamond",
    "CritPt v2 Hard", "AA-Briefcase",
)


def _aa_tier(label):
    """label 中的 reasoning 档位序数；无档位词返回 -1（默认档 / 量化变体）。"""
    ranks = [AA_TIER_ORDER[t.strip().lower()]
             for t in _TIER_RE.findall(label or "")
             if t.strip().lower() in AA_TIER_ORDER]
    return max(ranks) if ranks else -1


def _aa_coverage(row):
    """该档位行在池内指标上的实测覆盖数（0 = 只有定价的空档）。"""
    return sum(1 for c in AA_METRICS if _num(row.get(c)) is not None)


def _pick_aa_row(rows, alias, creator):
    """AA 取行：覆盖度最高的一批里取最高 reasoning 档，同档内取官方行。

    背景（2026-11）：AA 把 reasoning effort 档位并列在同一 Model Slug 下，
    label 形如 `DeepSeek V4.1 Flash 1017 (non-reasoning | high | max)`，
    三档分数差距极大（FrontierCode 0.061 / 0.168 / 0.285）。旧实现取
    「第一个官方行」，结果完全取决于 AA 页面的行序——2026-11-22 恰好吃到
    non-reasoning 档，deepseek-v4.1-flash 的 AA 指标全线腰斩、排名 #12 → #21。

    判据顺序（缺一不可）：
    1. **覆盖度优先**：先取池内指标实测覆盖数最多的那批行。小模型的
       non-reasoning 行常常只挂着 LCR 一个池指标（如 gemma-4-31b：1/10），
       纯按档位选会选中它，其余 9 个指标全空、整行被打成填补值。
    2. **档位次之**：覆盖度相同时取最高 effort 档（与 LiveBench 口径一致，
       见 ADR-0004：同模型取最高档，不混档）。
    3. 同档内官方 provider 优先（定价取官方牌价，AA 各档 token 单价一致，
       仅 costPerTask 随档位变化）。
    """
    if alias is None:
        return None, None
    alist = alias if isinstance(alias, list) else [alias]
    for a in alist:
        cands = [r for r in rows if (r.get("Model Slug") or "").strip() == a]
        if not cands:
            continue
        best_cov = max(_aa_coverage(r) for r in cands)
        finalists = [(i, r) for i, r in enumerate(cands)
                     if _aa_coverage(r) == best_cov]
        # 末位 tie-break 保留旧语义：无官方行时回退末行（旧的定价回退规则），
        # 保证同一份 CSV 每次选出同一行。
        _, best = max(finalists,
                      key=lambda t: (_aa_tier(t[1].get("Model")),
                                     _is_official_aa_row(t[1], creator), t[0]))
        return best, a
    return None, None


def _check_aa_join(registry, matched_count):
    """AA 别名一条都匹配不上 => join key 断裂，直接失败。

    registry 里配了 aa 别名的模型是 AA 数据的唯一消费者；若全数落空，
    说明 aa_providers.csv 的 Model Slug 与 registry 口径脱节（上游挪路径、
    大小写/命名变更等）。此时评分列仍有值、覆盖率统计却是全 0，静默放行
    会让下游报「指标有效样本 < 2」——与本函数要暴露的真实原因无关。
    """
    configured = sum(1 for m in registry if m.get("aa"))
    if configured and matched_count == 0:
        raise RuntimeError(
            f"AA join 断裂：registry 里 {configured} 个模型配了 aa 别名，"
            "但 aa_providers.csv 里 0 行匹配。"
            "请检查 parse_aa 的 Model Slug 取值路径是否仍与上游一致。"
        )


def _check_eqbench_join(registry, matched_count):
    """EQ-Bench 别名一条都匹配不上 => 源侧改名或整表抓空，直接失败。

    与 ``_check_aa_join`` 同类的静默断链防护：eqbench 表照常解析、行数
    正常，但 model 列整体换写法（``claude-opus-5`` -> ``claude-opus-5-1``）
    时不会有任何报错，只会让「创意写作」域的可信覆盖悄悄归零，退化成
    对标兄弟指标的单变量填补。见 ADR-0011。
    """
    configured = sum(1 for m in registry if m.get("eqbench"))
    if configured and matched_count == 0:
        raise RuntimeError(
            f"EQ-Bench join 断裂：registry 里 {configured} 个模型配了 eqbench "
            "别名，但 eqbench.csv 里 0 行匹配。"
            "请检查 eqbench 源的 model 列命名是否已变更。"
        )


def build_merged():
    registry = load_registry()

    # ---- 各源索引 ----
    aa_rows = _read_csv(AA_CSV)
    lb = _alias_index(_read_csv(os.path.join(CACHE, "livebench.csv")), "model")
    eq = _alias_index(_read_csv(os.path.join(CACHE, "eqbench.csv")), "model")

    # 官方发布技术报告核定的权威指标补充（声明式配置，便于自动化及模型维护）
    evals_path = os.path.join(os.path.dirname(__file__), "official_evals.json")
    official_evals = {}
    if os.path.exists(evals_path):
        with open(evals_path, "r", encoding="utf-8") as ef:
            official_evals = json.load(ef).get("models", {})

    # 指标名（与 config.json imputation_pool 一致）
    cols = [
        "FrontierCode 2.0", "LiveBench Coding", "Terminal-Bench v4.0",
        "LiveBench Long-Horizon", "AutomationBench", "LiveBench Browser",
        "HLE Diamond", "CritPt v2 Hard", "LiveBench Reasoning",
        "EQ-Bench Creative Writing", "LiveBench Design",
        "AA-Briefcase", "LiveBench Research", "LiveBench Data Analysis",
        "MLCR", "LCR", "Omniscience Accuracy", "Omniscience Non-Halluc.",
    ]

    out_rows = []
    aa_matched = 0
    eq_matched = 0
    for m in registry:
        slug = m["slug"]
        row = {"Model": slug, "Creator": m["creator"], "Vision": m.get("vision", False)}

        # LiveBench 2.0
        lb_row, lb_name = _pick_best_row(lb, m.get("livebench"))
        if lb_row:
            row["LiveBench Coding"] = _num(lb_row.get("Coding"))
            row["LiveBench Long-Horizon"] = _num(lb_row.get("Long-Horizon"))
            row["LiveBench Browser"] = _num(lb_row.get("Browser"))
            row["LiveBench Data Analysis"] = _num(lb_row.get("Data Analysis"))
            row["LiveBench Reasoning"] = _num(lb_row.get("Reasoning"))
            row["LiveBench Research"] = _num(lb_row.get("Research"))
            row["LiveBench Design"] = _num(lb_row.get("Design"))

        # EQ-Bench
        eq_row, _ = _pick_best_row(eq, m.get("eqbench"))
        if eq_row:
            eq_matched += 1
            row["EQ-Bench Creative Writing"] = _num(eq_row.get("Elo"))

        # AA（分数各 Provider 行一致；定价取官方行，见 _pick_aa_row）
        aa_row, _ = _pick_aa_row(aa_rows, m.get("aa"), m.get("creator"))
        if aa_row:
            aa_matched += 1
            row["FrontierCode 2.0"] = _num(aa_row.get("FrontierCode 2.0"))
            row["Terminal-Bench v4.0"] = _num(aa_row.get("Terminal-Bench v4.0"))
            row["AutomationBench"] = _num(aa_row.get("AutomationBench"))
            row["LCR"] = _num(aa_row.get("LCR"))
            row["MLCR"] = _num(aa_row.get("MLCR"))
            row["Omniscience Accuracy"] = _num(aa_row.get("Omniscience Accuracy"))
            row["Omniscience Non-Halluc."] = _num(aa_row.get("Omniscience Non-Halluc."))
            row["HLE Diamond"] = _num(aa_row.get("HLE Diamond"))
            row["CritPt v2 Hard"] = _num(aa_row.get("CritPt v2 Hard"))
            if aa_row.get("AA-Briefcase"):
                row["AA-Briefcase"] = _num(aa_row.get("AA-Briefcase"))
            # 成本列（性价比榜用）
            row["Price 1M Input"] = _num(aa_row.get("Price 1M Input"))
            row["Price 1M Output"] = _num(aa_row.get("Price 1M Output"))
            row["Cache Hit Price"] = _num(aa_row.get("Cache Hit Price"))
            row["Cache Write Price"] = _num(aa_row.get("Cache Write Price"))
            row["Cost Per Task"] = _num(aa_row.get("Cost Per Task"))

        # 官方技术报告公布的指标覆盖
        if slug in official_evals:
            for b_name, b_val in official_evals[slug].items():
                if b_name.startswith("_") or b_name == "source":
                    continue
                if row.get(b_name) is None:
                    row[b_name] = _num(b_val)

        out_rows.append(row)

    _check_aa_join(registry, aa_matched)
    _check_eqbench_join(registry, eq_matched)

    # 写 merged.csv（列序：Model, Creator, 指标, 成本列）
    price_cols = ["Price 1M Input", "Price 1M Output", "Cache Hit Price",
                  "Cache Write Price", "Cost Per Task"]
    header = ["Model", "Creator", "Vision"] + cols + price_cols
    os.makedirs(os.path.join(REPO_ROOT, "results"), exist_ok=True)
    out_path = os.path.join(BASE, "merged.csv")
    tmp = out_path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for r in out_rows:
            # 空值写空串，避免 "None"
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    os.replace(tmp, out_path)

    # 覆盖率统计
    n = len(out_rows)
    print(f"merged: {n} 模型 -> {os.path.basename(out_path)}")
    for c in cols:
        cover = sum(1 for r in out_rows if r.get(c) not in (None, ""))
        print(f"  {c:35} 覆盖 {cover}/{n}")
    return out_path


def main():
    try:
        build_merged()
    except FileNotFoundError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
