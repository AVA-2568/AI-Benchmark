#!/usr/bin/env python3
"""OpenRouter 模型元数据与 Modalities (Vision) 判定与核准工具。

功能：
1. 抓取 / 缓存 OpenRouter models API (https://openrouter.ai/api/v1/models)；
2. 解析 architecture.input_modalities 与 architecture.modality，确定是否支持视觉（Vision）；
3. 智能匹配 model_registry.json 中的模型条目；
4. 审查 (audit) 与同步 (sync) 注册表中模型的 vision 属性，杜绝人工误配与盲目全 True；
5. 为 detect_new_models 自动入池提供权威模态判定。
"""
import argparse
import json
import os
import re
import sys
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from url_guard import assert_safe_url  # noqa: E402

CACHE_DIR = os.path.join(BASE, ".cache")
DEFAULT_CACHE_FILE = os.path.join(CACHE_DIR, "openrouter_models.json")
DEFAULT_REGISTRY_FILE = os.path.join(BASE, "model_registry.json")
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# 机构/厂商名称与 OpenRouter id 命名空间的映射
CREATOR_NAMESPACE_MAP = {
    "anthropic": ["anthropic"],
    "openai": ["openai"],
    "google": ["google"],
    "xai": ["x-ai"],
    "x-ai": ["x-ai"],
    "meta": ["meta"],
    "deepseek": ["deepseek"],
    "moonshot": ["moonshotai"],
    "moonshotai": ["moonshotai"],
    "qwen": ["qwen", "alibaba"],
    "alibaba": ["qwen", "alibaba"],
    "zhipu": ["z-ai", "zhipuai", "thudm"],
    "zhipu ai": ["z-ai", "zhipuai", "thudm"],
    "z-ai": ["z-ai", "zhipuai", "thudm"],
    "minimax": ["minimax"],
    "xiaomi": ["xiaomi"],
    "tencent": ["tencent"],
    "thinking machines": ["thinkingmachines"],
    "thinkingmachines": ["thinkingmachines"],
    "ibm": ["ibm-granite"],
}


def _ensure_safe_subpath(target_path, base_dir=BASE):
    """确保目标路径在允许的基准目录下，防范路径穿越。"""
    real_base = os.path.realpath(base_dir)
    real_target = os.path.realpath(target_path)
    if not (real_target == real_base or real_target.startswith(real_base + os.sep)):
        raise ValueError(f"Blocked unsafe path traversal: {target_path}")
    return real_target


def fetch_openrouter_models(cache_path=DEFAULT_CACHE_FILE, timeout=30):
    """从 OpenRouter API 抓取模型列表并缓存至本地 JSON。"""
    safe_path = _ensure_safe_subpath(cache_path)
    assert_safe_url(OPENROUTER_MODELS_URL)

    req = urllib.request.Request(OPENROUTER_MODELS_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()

    data = json.loads(raw.decode("utf-8"))
    models = data.get("data", [])
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    tmp = safe_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)
    os.replace(tmp, safe_path)
    return models


def load_openrouter_models(cache_path=DEFAULT_CACHE_FILE):
    """从缓存读取 OpenRouter 模型列表；若不存在则返回空列表。"""
    safe_path = _ensure_safe_subpath(cache_path)
    if not os.path.exists(safe_path):
        return []
    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: failed to load {safe_path}: {e}", file=sys.stderr)
        return []


def is_vision_model(model_obj):
    """根据 OpenRouter 模型对象的 architecture 判断其是否支持视觉输入。

    判定规则：
    1. architecture.input_modalities 包含 'image'；
    2. 或 architecture.modality 包含 'image'。
    """
    if not isinstance(model_obj, dict):
        return False
    arch = model_obj.get("architecture") or {}
    in_mods = arch.get("input_modalities") or []
    if any(str(m).strip().lower() == "image" for m in in_mods):
        return True
    mod = str(arch.get("modality") or "").lower()
    if "image" in mod:
        return True
    return False


def _clean_slug(s):
    """清理后缀与干扰词，用于模糊匹配。"""
    if not s:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"-(thinking|adaptive|max|high|preview|effort|batch|xhigh|medium|low|customtools).*", "", s)
    return s


def find_openrouter_match(registry_entry, or_models):
    """为 registry_entry 在 or_models 中寻找最佳匹配的 OpenRouter 模型对象。"""
    if not or_models:
        return None

    # 1. 如果显式配置了 openrouter 别名，优先精确命中
    explicit = (registry_entry.get("openrouter") or "").strip().lower()
    if explicit:
        for m in or_models:
            mid = m.get("id", "").lower()
            if mid == explicit or mid.split(":") == [explicit]:
                return m

    slug = registry_entry.get("slug", "").strip().lower()
    creator = (registry_entry.get("creator") or "").strip().lower()
    allowed_ns = CREATOR_NAMESPACE_MAP.get(creator, [])

    # 准备候选名称列表
    candidates = []
    if slug:
        candidates.append(slug)
        candidates.append(slug.replace(".", "-"))
        candidates.append(slug.replace("-", "."))
        if "-next" in slug:
            candidates.append(slug.replace("-next", ""))

    # 别名
    aliases = []
    for k in ["aa", "eqbench"]:
        v = registry_entry.get(k)
        if v and isinstance(v, str):
            aliases.append(v)
    lb = registry_entry.get("livebench")
    if isinstance(lb, list):
        aliases.extend(lb)
    elif lb and isinstance(lb, str):
        aliases.append(lb)

    for a in aliases:
        clean_a = _clean_slug(a)
        if clean_a:
            candidates.append(clean_a)
            candidates.append(clean_a.replace(".", "-"))
            candidates.append(clean_a.replace("-", "."))

    # 去重且保持顺序
    seen_c = set()
    uniq_candidates = []
    for c in candidates:
        c_low = c.strip().lower()
        if c_low and c_low not in seen_c:
            seen_c.add(c_low)
            uniq_candidates.append(c_low)

    # 策略 1: 命名空间精确匹配
    for m in or_models:
        mid = m.get("id", "").lower()
        parts = mid.split("/", 1)
        if len(parts) == 2:
            ns, short = parts
            short_clean = short.split(":")[0]  # 去除 :batch 等 tag
            if allowed_ns and ns in allowed_ns:
                for c in uniq_candidates:
                    if (short_clean == c
                            or short_clean.replace(".", "-") == c.replace(".", "-")
                            or short_clean.replace("-", ".") == c.replace("-", ".")):
                        return m

    # 策略 2: 全局 short_id 精确匹配
    for m in or_models:
        mid = m.get("id", "").lower()
        short_clean = mid.split("/")[-1].split(":")[0]
        for c in uniq_candidates:
            if (short_clean == c
                    or short_clean.replace(".", "-") == c.replace(".", "-")
                    or short_clean.replace("-", ".") == c.replace("-", ".")):
                return m

    # 策略 3: 前缀匹配（例如 gemini-3.1-pro 匹配 gemini-3.1-pro-preview）
    for m in or_models:
        mid = m.get("id", "").lower()
        parts = mid.split("/", 1)
        ns = parts[0] if len(parts) == 2 else ""
        short_clean = (parts[1] if len(parts) == 2 else parts[0]).split(":")[0]
        if not allowed_ns or ns in allowed_ns:
            for c in uniq_candidates:
                if (short_clean == f"{c}-preview"
                        or short_clean.startswith(f"{c}-")):
                    return m

    return None


def resolve_model_vision(registry_entry, or_models=None):
    """判定单个注册表条目的 vision 属性。

    返回三元组: (has_vision: bool, matched_openrouter_id: str or None, source: str)
    source 可为:
    - 'openrouter': 经 OpenRouter 架构模态权威确认
    - 'explicit': 注册表既有配置（未在 OpenRouter 查到时的保底）
    """
    if or_models:
        matched = find_openrouter_match(registry_entry, or_models)
        if matched:
            return is_vision_model(matched), matched.get("id"), "openrouter"

    # 启发式保底检测
    slug = (registry_entry.get("slug") or "").lower()
    for kw in ["-vl", "-vision", "multimodal", "-image"]:
        if kw in slug:
            return True, None, "heuristic"

    # 若 registry 本身已有配置，保留原值
    if "vision" in registry_entry:
        return bool(registry_entry["vision"]), None, "explicit"

    # 默认保底
    return False, None, "default"


def audit_registry(registry_path=DEFAULT_REGISTRY_FILE, or_models=None):
    """对比模型注册表与 OpenRouter 的 Modalities，输出审查审计报告。"""
    safe_reg_path = _ensure_safe_subpath(registry_path)
    if or_models is None:
        or_models = load_openrouter_models()

    with open(safe_reg_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    models = doc.get("models", [])

    matched_list = []
    mismatched_list = []
    unmatched_list = []

    for m in models:
        cur_v = bool(m.get("vision", False))
        matched = find_openrouter_match(m, or_models)
        if matched:
            or_v = is_vision_model(matched)
            matched_list.append((m, matched, or_v))
            if cur_v != or_v:
                mismatched_list.append((m, matched, cur_v, or_v))
        else:
            unmatched_list.append(m)

    return {
        "total": len(models),
        "matched_count": len(matched_list),
        "mismatched_count": len(mismatched_list),
        "unmatched_count": len(unmatched_list),
        "mismatched": mismatched_list,
        "unmatched": unmatched_list,
        "matched": matched_list,
    }


def sync_registry_vision(registry_path=DEFAULT_REGISTRY_FILE, or_models=None, update_file=False):
    """将 OpenRouter 确认的真实 Modalities 同步到 model_registry.json 中。

    对存在差异的模型进行修复，返回修改的模型清单。
    """
    safe_reg_path = _ensure_safe_subpath(registry_path)
    if or_models is None:
        or_models = load_openrouter_models()

    with open(safe_reg_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    models = doc.get("models", [])

    changes = []
    for m in models:
        matched = find_openrouter_match(m, or_models)
        if matched:
            or_v = is_vision_model(matched)
            cur_v = bool(m.get("vision", False))
            if cur_v != or_v:
                old_val = m.get("vision")
                m["vision"] = or_v
                changes.append({
                    "slug": m["slug"],
                    "old_vision": old_val,
                    "new_vision": or_v,
                    "openrouter_id": matched.get("id"),
                    "modality": (matched.get("architecture") or {}).get("modality"),
                    "input_modalities": (matched.get("architecture") or {}).get("input_modalities"),
                })

    if changes and update_file:
        tmp = safe_reg_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, safe_reg_path)

    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch latest models from OpenRouter API")
    parser.add_argument("--check", action="store_true", help="Audit model_registry.json against OpenRouter")
    parser.add_argument("--sync", action="store_true", help="Sync confirmed modalities into model_registry.json")
    args = parser.parse_args()

    if args.fetch:
        print("Fetching latest OpenRouter models...")
        models = fetch_openrouter_models()
        print(f"Fetched and cached {len(models)} models.")
    else:
        models = load_openrouter_models()
        if not models:
            print("No cached OpenRouter models found. Fetching now...")
            models = fetch_openrouter_models()

    report = audit_registry(or_models=models)
    print(f"Total Registry Models: {report['total']}")
    print(f"Matched with OpenRouter: {report['matched_count']}")
    print(f"Unmatched: {report['unmatched_count']}")
    print(f"Mismatched Vision: {report['mismatched_count']}")

    if report["mismatched"]:
        print("\n--- Mismatches Found ---")
        for m, matched, cur_v, or_v in report["mismatched"]:
            arch = matched.get("architecture") or {}
            print(f"[{m['slug']}] Registry: {cur_v} -> OpenRouter: {or_v} "
                  f"(id: {matched['id']}, in_mods: {arch.get('input_modalities')})")

    if report["unmatched"]:
        print("\n--- Unmatched Models ---")
        for m in report["unmatched"]:
            print(f"[{m['slug']}] Creator: {m.get('creator')}, Current Vision: {m.get('vision')}")

    if args.sync:
        changes = sync_registry_vision(update_file=True, or_models=models)
        print(f"\nSuccessfully synced {len(changes)} model(s) in model_registry.json.")
        for c in changes:
            print(f"  - {c['slug']}: vision {c['old_vision']} -> {c['new_vision']} ({c['openrouter_id']})")
    elif args.check and report["mismatched_count"] > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
