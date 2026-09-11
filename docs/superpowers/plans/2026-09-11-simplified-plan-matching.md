# 简化大模型套餐维护与匹配实施计划 (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 升级套餐匹配引擎支持带语义通配与排除机制的匹配，引入安全 Scale 兜底，补齐 Muse Spark 等模型支持，并在审计层实现双向透视表，从而彻底降低后续套餐维护与新模型入池成本。

**Architecture:** 
- 在 `scripts/pipeline/scoring.py` 中改造 `_plan_for`，使用标准库 `fnmatch` 赋予 `model_match` 模式匹配能力，加入 `exclude_match` 黑名单与 `model_cost_scale` 保守默认防线。
- 在 `config.json` 中将第三方聚合套餐的离散枚举重构为语义族系 pattern，补齐 `muse-spark-1.[23]*` 及遗漏的 scale 配置。
- 在 `scripts/verify_plans.py` 中增加单 Pattern 死规则拦截与正反双向透视输出。

**Tech Stack:** Python 3.10+, `fnmatch`, `pytest`, `verify_plans`

## Global Constraints
- 禁止引入额外第三方依赖，全部采用 Python 标准库（`fnmatch`, `json`, `re` 等）。
- 任何通过通配符命中、但未在 `model_cost_scale` 显式标定 scale 的模型，必须默认按该套餐内的最大 scale 惩罚结算，严禁虚假低估成本。
- 排除名单 `exclude_match` 具备一票否决权。
- 保持官方自营订阅的 `creator_match` 模式不受影响。
- 每次任务变更必须通过 `python -m pytest -q` 与 `python scripts/verify_plans.py --offline` 双重验证。

---

### Task 1: 核心匹配引擎改造（`_plan_for` 支持 fnmatch、exclude 与安全 scale 兜底）

**Files:**
- Modify: `scripts/pipeline/scoring.py:46-90`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `plans` (list of plan dicts), `creator` (str), `model` (str or None)
- Produces: `_plan_for(plans, creator, model) -> Optional[dict]` (带通配符、排除名单与安全 scale 副本)

- [ ] **Step 1: 在 `tests/test_scoring.py` 中编写通配符与防过度匹配的失败测试**

```python
def test_plan_for_wildcard_and_exclude():
    plans = [
        {
            "name": "Proxy Plan",
            "monthly": 10.0,
            "discount": 0.167,
            "model_match": ["deepseek-v4*", "qwen3.*-max", "muse-spark-1.[23]*"],
            "exclude_match": ["*-27b*", "muse-spark-1.1"],
            "model_cost_scale": {"*-pro": 4.0, "deepseek-v4-flash": 2.0}
        }
    ]
    # 1. 命中通配符且 scale 显式命中
    p1 = _plan_for(plans, "DeepSeek", "deepseek-v4-flash")
    assert p1 is not None and abs(p1["discount"] - 0.167 * 2.0) < 1e-4

    # 2. 命中通配符但 scale 未显式指定 -> 触发最大 scale 4.0 兜底
    p2 = _plan_for(plans, "DeepSeek", "deepseek-v4.1-flash")
    assert p2 is not None and abs(p2["discount"] - 0.167 * 4.0) < 1e-4

    # 3. 命中 exclude 黑名单 -> 一票否决
    p3 = _plan_for(plans, "Meta", "muse-spark-1.1")
    assert p3 is None

    # 4. 正常命中白名单通配
    p4 = _plan_for(plans, "Meta", "muse-spark-1.3")
    assert p4 is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_scoring.py::test_plan_for_wildcard_and_exclude -v`
Expected: FAIL (AttributeError 或断言失败)

- [ ] **Step 3: 在 `scripts/pipeline/scoring.py` 中实现通配、排除与安全 scale**

修改 `_plan_for` 逻辑：
```python
import fnmatch

def _match_pattern(name, patterns):
    if not name or not patterns:
        return False
    return any(fnmatch.fnmatch(name, pat.strip()) for pat in patterns)

def _resolve_scale(model, scale_map):
    if not model or not scale_map:
        return 1.0
    if model in scale_map:
        return float(scale_map[model])
    for pat, scale in scale_map.items():
        if fnmatch.fnmatch(model, pat.strip()):
            return float(scale)
    return None
```
在 `_plan_for` 循环体内增加：
```python
        if model and _match_pattern(model, p.get("exclude_match")):
            continue
        matched = creator in (p.get("creator_match") or [])
        if not matched and model and p.get("model_match"):
            matched = _match_pattern(model, p["model_match"])
        if not matched:
            continue
        # ...
        scale_map = p.get("model_cost_scale") or {}
        if scale_map and model:
            scale = _resolve_scale(model, scale_map)
            if scale is None and p.get("model_match") and _match_pattern(model, p["model_match"]):
                scale = max(float(v) for v in scale_map.values())
            d = min(d * (scale or 1.0), 1.0)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_scoring.py::test_plan_for_wildcard_and_exclude -v`
Expected: PASS

- [ ] **Step 5: 提交 commit**

```bash
git add scripts/pipeline/scoring.py tests/test_scoring.py
git commit -m "feat: _plan_for 支持 fnmatch 通配、exclude_match 与安全 scale 兜底"
```

---

### Task 2: 配置校验层（`scripts/pipeline/config.py` 与 `scripts/verify_plans.py`）放行与增强

**Files:**
- Modify: `scripts/pipeline/config.py:190-210`
- Modify: `scripts/verify_plans.py:108-140`
- Test: `tests/test_plans_consistency.py`

**Interfaces:**
- Consumes: plan schema definition
- Produces: 支持 `exclude_match` 字段，单 pattern 死规则拦截

- [ ] **Step 1: 在 `tests/test_plans_consistency.py` 中编写 dead pattern 检查测试**

```python
def test_verify_plans_catches_dead_patterns():
    bad_plan = {
        "name": "Bad Plan",
        "monthly": 10,
        "discount": 0.5,
        "url": "https://example.com",
        "model_match": ["non_existent_model_12345*"]
    }
    errs = vp.check_dead_patterns([bad_plan], [{"slug": "deepseek-v4-pro"}])
    assert any("DEAD_PATTERN" in e for e in errs)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/test_plans_consistency.py::test_verify_plans_catches_dead_patterns -v`
Expected: FAIL (AttributeError: 'module' object has no attribute 'check_dead_patterns')

- [ ] **Step 3: 在 `verify_plans.py` 与 `pipeline/config.py` 实现检查与放行**

在 `verify_plans.py` 中新增 `check_dead_patterns`：
```python
def check_dead_patterns(plans, registry_models):
    errs = []
    slugs = [m.get("slug") for m in registry_models if m.get("slug")]
    for p in plans:
        for pat in p.get("model_match") or []:
            if not any(fnmatch.fnmatch(s, pat.strip()) for s in slugs):
                errs.append(f"{p.get('name')}: pattern '{pat}' 在当前模型库中未命中任何模型 (DEAD_PATTERN)")
    return errs
```
在 `pipeline/config.py` 的校验循环中放行合法字段。

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/test_plans_consistency.py::test_verify_plans_catches_dead_patterns -v`
Expected: PASS

- [ ] **Step 5: 提交 commit**

```bash
git add scripts/pipeline/config.py scripts/verify_plans.py tests/test_plans_consistency.py
git commit -m "feat: 校验层支持 exclude_match 并引入单 pattern 死规则检测"
```

---

### Task 3: 重构 `config.json` 第三方聚合套餐并补齐 Muse Spark

**Files:**
- Modify: `config.json`

**Interfaces:**
- Consumes: 48 个套餐定义
- Produces: 语法合规、语义精准、包含 `exclude_match` 的标准化套餐配置

- [ ] **Step 1: 精准更新 `config.json` 中聚合套餐的 `model_match`、`exclude_match` 与 `model_cost_scale`**

更新 `OpenCode Go`：
- 补齐 `muse-spark-1.[23]*`，加入 `exclude_match: ["*-27b*", "*-7b*", "muse-spark-1.1"]`；
- 补齐 `qwen3.7-max: 2.0`、`glm-5.3*: 4.0`、`grok-4.6: 4.0`、`gpt-5.6-luna: 4.0`；
更新 `火山方舟 Coding Plan (Lite/Pro)`：
- `model_match: ["deepseek-v4*", "glm-5*", "kimi-k*"]`，精准覆盖全部在库衍生型号；
更新 `Ollama Pro`：
- `model_match: ["deepseek-v4*", "qwen3.*-27b"]`，精准面向开源权重；
更新 `R4 Coder Code Lite` 与 `Command Code GOAT`。

- [ ] **Step 2: 运行离线一致性审计**

Run: `python scripts/verify_plans.py --offline`
Expected: `plan audit: 48 套餐 -> pass 48 / warn 0 / fail 0`

- [ ] **Step 3: 运行完整测试套件**

Run: `python -m pytest -q`
Expected: 100% PASS

- [ ] **Step 4: 提交 commit**

```bash
git add config.json
git commit -m "feat(config): 聚合套餐升级为语义族系 pattern，补齐 Muse Spark 1.3/1.2"
```

---

### Task 4: `verify_plans.py` 增加双向透视表输出与端到端榜单重生成

**Files:**
- Modify: `scripts/verify_plans.py`
- Output: `README.md`, `results/*`

**Interfaces:**
- Consumes: `plans`, `model_registry.json`, `value_scored.csv`
- Produces: 双向透视控制台输出、刷新的排行榜

- [ ] **Step 1: 在 `verify_plans.py` 增加 `print_coverage_matrix`**

- 正向：遍历聚合套餐，打印其实质生效的模型及有效 scale；
- 反向：打印当前 52 个模型匹配的最优套餐；若为 API 按量或名义原价，归入 `[Uncovered / Full Price]` 专栏清晰呈现。

- [ ] **Step 2: 运行端到端构建与前沿图重绘**

Run: `python scripts/build.py`
Expected:
- `muse-spark-1.3` 与 `1.2` 成功获得 OpenCode Go 的 6× 杠杆，有效单价自 5.75 元降至约 0.96 元；
- `deepseek-v4.1-flash` 稳定获得火山方舟 10× 杠杆，有效单价维持在 0.141 元；
- README 与前沿图原子化更新成功。

- [ ] **Step 3: 运行全量测试验证零回归**

Run: `python -m pytest -q && python scripts/verify_plans.py --offline`
Expected: ALL PASS

- [ ] **Step 4: 同步推送合并至 main 分支**

```bash
git add -A
git commit -m "feat: 落地套餐双向透视审计，重算全榜数据与 README"
git push origin main
```
