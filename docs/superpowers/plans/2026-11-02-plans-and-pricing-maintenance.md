# 2026-11-02 套餐价格、折扣倍率与模型映射全面维护 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全面维护项目套餐体系，根据 73 个模型池的最新状态校准各套餐提供的模型清单（`model_match` / `exclude_match`）、实际折扣倍率与分模型扣费修正（`model_cost_scale`），完成套餐核验时效刷新并保证端到端构建与审计全绿通过。

**Architecture:**
1. **聚合套餐白名单与通配符升级**：更新 OpenCode Go、Command Code GOAT、WorkBuddy 等聚合套餐中的通配符（如将 `mimo-v2.5*` 扩展为 `mimo-v2*`），使其精确命中新版旗舰与小版本模型；
2. **分模型 Scale 精度校准**：完善 OpenCode Go 中对 `kimi-k3*`、`deepseek-v4-flash-vision`、`qwen3.8-flash*`、`mimo-v2*` 等新模型的抵扣系数映射，防止因通配未命中导致错误回退到最高 4.0x 惩罚系数；
3. **未收录模型防御机制核验**：确保 NVIDIA Nemotron 系列、StepFun step-5-preview、Meta muse-spark-open、Anthropic Haiku/Fable 等未开放或专有模型坚决不被不当套餐套利，严格维持 API 按量；
4. **套餐时效全面刷新与算术核验**：刷新所有套餐在 `config.json` 中的 `source` 巡检时间戳至 2026-11-02，保持所有套餐算术偏差 <1% 且档位单调递增；
5. **端到端复算与基准回归**：运行 `verify_plans.py`、`pytest`、`build.py --offline`，同步更新榜单结果、审计报告及方法论文档。

**Tech Stack:** Python 3.10+, pytest, JSON, fnmatch, CSV.

**Spec:** `METHODOLOGY.md`（订阅套餐与倍率、白名单与排除机制）、`config.json`（plans 规范）、`scripts/model_registry.json`（73 模全量池）。

---

### Task 1: 备份关键配置与建立测试用例

**Files:**
- Create: `config.json.bak`
- Modify: `tests/test_plans_consistency.py`
- Modify: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `config.json`, `scripts/verify_plans.py`, `scripts/pipeline/scoring.py`
- Produces: Regression tests covering newly added models, scale mappings, and consistency rules.

- [ ] **Step 1: 备份原 `config.json`**
  执行安全备份，以备发生异常时快速回滚：
  `python -c "import shutil; shutil.copyfile("config.json", "config.json.bak")"`

- [ ] **Step 2: 在 `tests/test_plans_consistency.py` 中增加对新模型映射和 Scale 的严格断言**
  验证 `mimo-v2.6-pro`、`kimi-k3.1-pro`、`deepseek-v4-flash-vision` 在对应套餐中的行为，验证未收录模型保持 API 按量。

- [ ] **Step 3: 运行现有测试确认 baseline**
  `python -m pytest tests/test_plans_consistency.py -q`

---

### Task 2: 精准校准 `config.json` 套餐模型映射与 Scale 系数

**Files:**
- Modify: `config.json`

**Interfaces:**
- Updates: `plans` 表项中的 `model_match`, `model_cost_scale`, `source`, `verified_date`

- [ ] **Step 1: 升级 OpenCode Go 模型匹配与 Scale 映射**
  - 将 `mimo-v2.5*` 升级为 `mimo-v2*`
  - 在 `model_cost_scale` 中增加：
    - `"mimo-v2*": 4.0`
    - `"kimi-k3*": 4.0`
    - `"deepseek-v4-flash-vision*": 4.0`
    - `"qwen3.8-flash*": 2.0`
    - `"*-flash*": 2.0`
  - 清理无用 scale 键。

- [ ] **Step 2: 升级 Command Code GOAT 模型匹配**
  - 将 `mimo-v2.5*` 升级为 `mimo-v2*`

- [ ] **Step 3: 检查并刷新所有 48 个套餐的时效记录**
  - 更新所有套餐的 `source` 字段，追加 `2026-11-02 巡检一致；模型映射与倍率核验完毕`，消除超过 21 天的时效告警隐患。

- [ ] **Step 4: 运行 `verify_plans.py` 离线审计**
  运行：`python scripts/verify_plans.py --offline`
  要求：0 FAIL, 0 WARN，正向与反向透视符合预期。

---

### Task 3: 刷新榜单与文档，完成端到端全量验证

**Files:**
- Modify: `results/value_scored.csv`
- Modify: `results/plan_audit.json`
- Modify: `results/manifest.json`
- Modify: `README.md`
- Modify: `METHODOLOGY.md`

**Interfaces:**
- Consumes: updated `config.json`, `pipeline/scoring.py`
- Produces: fully validated value scores, updated leaderboard markdown, updated documentation.

- [ ] **Step 1: 运行全量离线端到端构建**
  `python scripts/build.py --offline`

- [ ] **Step 2: 运行全量 pytest 测试套件**
  `python -m pytest -q`

- [ ] **Step 3: 核对 Value 榜单前列与关键模型实付价**
  检查 `results/value_scored.csv`，确保 `mimo-v2.6-pro`、`kimi-k3.1-pro`、`deepseek-v4-flash-vision`、`gemini-3.8-flash` 等各旗舰与轻量模型的 Effective $/1M 准确自洽。

- [ ] **Step 4: 检查并同步 METHODOLOGY.md**
  核对方法论中的套餐描述，确保最新映射规则被清晰记录。
