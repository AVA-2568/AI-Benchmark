# 性价比榜单套餐维护与模型映射表 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 维护性价比榜单，清理泛滥式品牌匹配，建立「套餐-模型精准映射表（白名单）」，杜绝未收录模型（如 Gemini 4 Argon、Gemma、Claude Haiku/Fable、GPT Nano/Codex）误享倍率优惠，并全面核实刷新最新套餐状态。

**Architecture:** 
1. 将所有聚合类 IDE 与跨厂商套餐（GitHub Copilot、Cursor、Windsurf、Trae、Factory Droid、Poe）的宽泛 `creator_match` 彻底重构为严格的 `model_match` 白名单及 `exclude_match` 黑名单；
2. 为第一方官方订阅（ChatGPT、Claude、Hy）增加专用/API端模型（`*-nano`、`*-codex`、`claude-haiku*`、`claude-fable*`）排除规则，防止极廉价或非订阅模型产生虚高畸形倍率；
3. 在 `scripts/pipeline/scoring.py` 与 `scripts/build.py` 抽象统一的 `_plan_matches`，保证评分与购买指南双端一致；
4. 升级 `scripts/verify_plans.py` 生成完整的正反向「套餐-模型映射表」并提供强类型一致性检验与 CI 保护。

**Tech Stack:** Python 3.10+, pytest, JSON, fnmatch, CSV.

**Spec:** `METHODOLOGY.md`（订阅套餐与倍率章节）、`config.json`（plans 规范）、`scripts/model_registry.json`（64 模型清单）。

## Global Constraints

- 任何套餐的实际命中模型必须具有官方支持依据，严禁未收录模型（如 Gemini 4 Argon、Gemma 4 31B 等）享受套餐折扣。
- 修改评分与匹配算法必须保证 `_plans_block`（套餐购买指南）与 `_plan_for`（性价比榜单计算）使用完全一致的匹配规则。
- 遵循项目现有不变量：离线复算 `python scripts/build.py --offline` 必须成功，`python scripts/verify_plans.py --offline` 必须 0 FAIL / 0 WARN，`python -m pytest -q` 必须全数通过。
- 不保留过时兼容逻辑，最简实现优先。

## Review Focus

1. **白名单漏网输入**：如果一个套餐同时设置了 `creator_match` 和 `model_match`，非白名单内的同厂商模型必须被判定为不匹配，不可被 `creator_match` 旁路。
2. **通配符黑名单一票否决**：`exclude_match` 规则（如 `*-nano`、`*-codex`、`claude-haiku*`）必须在任何白名单或厂商匹配前执行一票否决。
3. **极小单价模型防爆**：`claude-haiku-5.5`（API 牌价 $0.08/1M）不能误套用 Claude Max 20x 的 40× 杠杆导致 Value 破万畸变。
4. **套餐购买指南一致性**：`_plans_block` 挑选的最强模型必须是该套餐真正支持的模型，不得选出如 GitHub Copilot 匹配 Gemini 4 Argon 的荒谬结果。
5. **未覆盖模型正确定价**：未收录于任何折扣套餐的模型（如 `gemini-4-argon`、`gemma-4-31b`、`muse-spark-1.1`、`inkling`、`mistral-large-4`）在性价比榜中必须显示为 `API 按量`、`倍率 1×`、`Effective $/1M = Blended $/1M`。

---

### Task 1: 核心匹配函数重构与双端对齐

**Files:**
- Modify: `scripts/pipeline/scoring.py`
- Modify: `scripts/build.py`
- Modify: `scripts/parse_aa.py`
- Test: `tests/test_scoring.py`
- Test: `tests/test_plans_block.py`

**Interfaces:**
- Consumes: `plans` list from `config.json`, model metadata (`Creator`, `Model`).
- Produces: `_plan_matches(plan: Dict[str, Any], creator: Optional[str], model: Optional[str]) -> bool`

- [ ] **Step 1: 编写测试用例验证 _plan_matches 与 _plan_for 的白名单约束**
在 `tests/test_scoring.py` 中添加测试：
```python
def test_plan_matches_strict_whitelist():
    from pipeline.scoring import _plan_matches
    # 既有 creator 又有 model_match 时，不在 model_match 的同厂商模型必须为 False
    plan = {
        "name": "Test IDE",
        "creator_match": ["Google"],
        "model_match": ["gemini-3.*-flash"],
        "exclude_match": ["*-lite"],
    }
    assert _plan_matches(plan, "Google", "gemini-3.8-flash") is True
    assert _plan_matches(plan, "Google", "gemini-4-argon") is False
    assert _plan_matches(plan, "Google", "gemini-3.5-flash-lite") is False
    assert _plan_matches(plan, "Anthropic", "claude-sonnet-5.5") is False
```

- [ ] **Step 2: 运行测试并确认失败**
运行: `python -m pytest tests/test_scoring.py -k test_plan_matches_strict_whitelist`
预期: FAIL（`_plan_matches` 尚未定义或逻辑未就绪）

- [ ] **Step 3: 在 scripts/pipeline/scoring.py 中实现 _plan_matches 并重构 _plan_for**
在 `scripts/pipeline/scoring.py` 实现：
```python
def _plan_matches(plan: Dict[str, Any], creator: Optional[str], model: Optional[str]) -> bool:
    """判断套餐是否支持给定的 creator 和 model。

    规则：
    1. 若 model 命中 exclude_match，一票否决返回 False；
    2. 若定义了 model_match，必须命中 model_match：
       - 若同时定义了 creator_match，要求 creator 亦在 creator_match 中；
       - 若未命中 model_match，坚决返回 False（禁止被 creator_match 旁路）；
    3. 若未定义 model_match，则只要 creator 在 creator_match 中即返回 True。
    """
    if model and _match_pattern(model, plan.get("exclude_match")):
        return False
    mm = plan.get("model_match")
    cm = plan.get("creator_match")
    if mm:
        if not model or not _match_pattern(model, mm):
            return False
        if cm and creator not in cm:
            return False
        return True
    return bool(creator and cm and creator in cm)
```
并让 `_plan_for` 内部直接调用 `_plan_matches(p, creator, model)`。

- [ ] **Step 4: 在 scripts/build.py 中重构 _plans_block 采用统一匹配逻辑**
将 `_plans_block` 中原先粗糙的集合匹配：
```python
best = next((r for r in rows if _plan_matches(p, r.get("Creator"), r.get("Model"))), None)
```
并在 `scripts/parse_aa.py` 顶部添加标准流 utf-8 重构，防止 Windows 环境 GBK 崩溃。

- [ ] **Step 5: 运行相关单元测试确认通过**
运行: `python -m pytest tests/test_scoring.py tests/test_plans_block.py -q`
预期: PASS

---

### Task 2: 清理宽泛匹配、建立精确映射表并刷新 config.json 套餐

**Files:**
- Modify: `config.json`
- Test: `tests/test_plans_consistency.py`

**Interfaces:**
- Consumes: 48 subscription plans in `config.json`.
- Produces: 精确带有 `model_match` / `exclude_match` 的 48 个套餐定义，时效更新为 2026-10-21。

- [ ] **Step 1: 编写映射表校验测试**
在 `tests/test_plans_consistency.py` 中添加断言：
- 所有多模型聚合 IDE（GitHub Copilot, Cursor, Windsurf, Trae, Factory Droid, Poe）必须没有宽泛 `creator_match`，全部具备明确的 `model_match`；
- `gemini-4-argon` 和 `gemma-4-31b` 绝不能被任何 GitHub Copilot 或 Cursor 套餐命中；
- `claude-haiku-5.5` 绝不能被 Claude Max 或 Claude Pro 套餐命中；
- `gpt-5.4-nano` 绝不能被 ChatGPT 套餐命中。

- [ ] **Step 2: 运行测试确认当前失败**
运行: `python -m pytest tests/test_plans_consistency.py -k test_plans_strict_mappings`
预期: FAIL

- [ ] **Step 3: 更新 config.json 中全部 48 个套餐**
1. GitHub Copilot (Max, Pro+, Pro):
   - 移除 `creator_match`；
   - `model_match`: `["claude-sonnet*", "gemini-3.*-flash", "gemini-3.1-pro", "gpt-5.4*", "gpt-5.5*", "gpt-5.6*", "gpt-6*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-lite", "*-codex"]`
2. Cursor (Ultra, Pro+, Pro):
   - 移除 `creator_match`；
   - `model_match`: `["claude-sonnet*", "claude-opus*", "gpt-5.4*", "gpt-5.5*", "gpt-5.6*", "gpt-6*", "gemini-3.1-pro", "gemini-3.*-flash", "grok-4.*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-lite", "*-codex", "claude-haiku*"]`
3. Windsurf Pro:
   - 移除 `creator_match`；
   - `model_match`: `["claude-sonnet*", "gpt-5.4*", "gpt-5.5*", "gpt-5.6*", "gpt-6*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-codex", "claude-opus*"]`
4. Trae Pro:
   - 移除 `creator_match`；
   - `model_match`: `["claude-sonnet*", "gpt-5.4*", "gpt-5.5*", "gpt-5.6*", "gpt-6*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-codex"]`
5. Factory Droid Pro:
   - 移除 `creator_match`；
   - `model_match`: `["claude-sonnet*", "claude-opus*", "gpt-5.4*", "gpt-5.5*", "gpt-5.6*", "gpt-6*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-codex", "claude-haiku*"]`
6. Poe Premium:
   - 移除 `creator_match`；
   - `model_match`: `["claude*", "gpt*", "gemini*", "grok*", "deepseek*"]`
   - `exclude_match`: `["*-nano", "*-mini", "*-codex", "gemma*"]`
7. ChatGPT (Plus, Pro 5x, Pro 20x):
   - 保留 `creator_match: ["OpenAI"]`，增加 `exclude_match: ["*-nano", "*-codex"]`
8. Claude (Pro, Max 5x, Max 20x):
   - 保留 `creator_match: ["Anthropic"]`，增加 `exclude_match: ["claude-haiku*", "claude-fable*"]`
9. Hy Token Plan (Lite, Standard, Pro, Max):
   - 增加 `model_match: ["hy*"]`
10. WorkBuddy (标准版, 高级版, 旗舰版):
   - 增加 `model_match: ["hy*", "glm*", "minimax*", "kimi*", "deepseek*"]`
11. 刷新所有 48 个套餐的 source 与 note 复核日期为最新 `2026-10-21`，记录最新官方套餐状态核验信息。

- [ ] **Step 4: 运行一致性测试验证通过**
运行: `python -m pytest tests/test_plans_consistency.py -q`
预期: PASS

---

### Task 3: 升级 verify_plans.py，输出完整映射表透视与审计报告

**Files:**
- Modify: `scripts/verify_plans.py`
- Modify: `tests/test_plans_consistency.py`

**Interfaces:**
- Produces: 升级的 `build_coverage_matrix` 与 `print_coverage_matrix`，并在 `results/plan_audit.json` 中保留完整的映射表矩阵。

- [ ] **Step 1: 扩展 build_coverage_matrix 透视矩阵**
更新 `scripts/verify_plans.py` 中的 `build_coverage_matrix`：
- 正向透视不仅能包含 `model_match` 的套餐，还能支持显示全部套餐对 64 个模型的实际命中映射；
- 统计并高亮当前真正属于「未覆盖 / 官方 API 原价（1.0×）」的模型清单（Gemini 4 Argon, Gemma 4 31B, Gemini 3.5 Flash Lite, Claude Haiku 5.5, Claude Fable, GPT Nano/Codex, Muse Spark 1.1, Inkling, Mistral Large 4）；
- 生成正向映射表字典 `plan_to_models` 与反向映射字典 `model_to_plan`。

- [ ] **Step 2: 运行 scripts/verify_plans.py --offline 并查看输出**
运行: `python scripts/verify_plans.py --offline`
预期: 48 套餐 pass 48 / warn 0 / fail 0，完整打印出清晰正向与反向映射表。

- [ ] **Step 3: 运行 pytest tests/test_plans_consistency.py 验证通过**
运行: `python -m pytest tests/test_plans_consistency.py -q`
预期: PASS

---

### Task 4: 端到端榜单重新计算与文档同步

**Files:**
- Modify: `METHODOLOGY.md`
- Modify: `README.md`
- Generate: `results/value_scored.csv`
- Generate: `results/plan_audit.json`
- Generate: `results/manifest.json`

- [ ] **Step 1: 运行离线全量构建**
运行: `$env:PYTHONIOENCODING="utf-8"; python scripts/build.py --offline`
预期: BUILD OK，生成更新的 `value_scored.csv`、`general_scored.csv`、`text_scored.csv`。

- [ ] **Step 2: 验证 value_scored.csv 关键行**
检查 `gemini-4-argon`、`claude-haiku-5.5`、`gpt-5.4-nano`、`gemma-4-31b`：
- `gemini-4-argon`：Plan 为空，倍率 1×，有效价等于混合价 $1.746，不再被 GitHub Copilot 误扣；
- `claude-haiku-5.5`：Plan 为空，倍率 1×，有效价等于混合价 $0.08，Value 分数归于正常 732.5，不再产生 29,277 虚高分；
- `gpt-5.4-nano`：Plan 为空，倍率 1×，正常按量计费；
- `claude-sonnet-5.5`：正常命中 Claude Max 20x（40×）；
- `gemini-3.8-flash`：正常命中 GitHub Copilot Max（2×）。

- [ ] **Step 3: 更新 METHODOLOGY.md 与 README.md**
- 在 `METHODOLOGY.md` 详细补充「套餐-模型精准映射表（白名单）机制」说明：解释为什么聚合 IDE（Copilot / Cursor / Windsurf / Trae 等）必须用白名单限制范围，以及为什么 API 端专用模型和超廉价模型不被消费级订阅覆盖。
- 在 `README.md` 中更新套餐购买指南说明与 FAQ，确保文档与新生成数据一致。

---

### Task 5: 全量回归与交付前自检

- [ ] **Step 1: 运行全量测试**
运行: `python -m pytest -q`
预期: 145+ passed，0 失败。

- [ ] **Step 2: 运行套餐审计脚本**
运行: `python scripts/verify_plans.py --offline`
预期: 0 FAIL, 0 WARN.

- [ ] **Step 3: 运行端到端构建自检**
运行: `$env:PYTHONIOENCODING="utf-8"; python scripts/build.py --offline`
预期: BUILD OK.

- [ ] **Step 4: 检查 git 状态**
运行: `git status` 确认没有未预期的修改和临时文件。
