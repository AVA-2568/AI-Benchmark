# 简化大模型套餐维护与多模型聚合匹配设计规范

- **状态**：已批准 (Approved)
- **创建日期**：2026-09-11
- **目标**：降低项目套餐的维护成本，杜绝新模型自动入池后的套餐匹配断层，并使第三方聚合套餐所覆盖的模型实质可见、易于复核。

---

## 1. 现状与痛点分析

1. **死板的字符串全等匹配**：
   目前 `scripts/pipeline/scoring.py` 仅支持 `model in p["model_match"]` 全等判断。导致每当 `detect_new_models.py --apply` 自动发现并入池一个新变体（如 `deepseek-v4.1-flash`、`muse-spark-1.3`），该模型无法自动继承其所属系列的聚合套餐，直接回退到无折扣的原价或名义套餐。
2. **多平台同物异名干扰**：
   各聚合平台往往带有额外修饰后缀（如 OpenCode 的 `Muse Spark 1.3 Contributor`）。人工在 `config.json` 维护死板的完整字符串极其容易遗漏。
3. **覆盖不可见性**：
   缺乏直观的审计视图展示每个第三方聚合套餐在当前库内到底实质命中了哪些模型。

---

## 2. 系统架构设计

### 2.1 匹配引擎升级（`pipeline/scoring.py`）
- 在 `_plan_for` 决策中引入标准库 `fnmatch.fnmatch`；
- 模型匹配判定：
  $$\text{Matched} \iff (\text{Creator} \in \text{creator\_match}) \lor \exists \text{pat} \in \text{model\_match} : \text{fnmatch}(\text{Model}, \text{pat})$$
- 分模型倍率修正（`model_cost_scale`）：
  优先精准匹配 key，若无则尝试 pattern 匹配。

### 2.2 聚合套餐配置模式化（`config.json`）
- 将以下 5 个聚合类套餐的枚举全面升级为族系模式，并补齐已知上架的族系（包含 `muse-spark*`）：
  - `OpenCode Go`
  - `火山方舟 Coding Plan Pro / Lite`
  - `Command Code GOAT`
  - `R4 Coder Code Lite`
  - `Ollama Pro`
- 保持官方自营订阅（ChatGPT、Claude、Kimi、MiMo、GLM 等）按 `creator_match` 走，维持零维护成本。

### 2.3 审计透视表与防呆检查（`verify_plans.py`）
- 新增离线审计透视报告：输出每个第三方聚合套餐在当前有效模型库中的实质命中清单；
- 增加空命中拦截：若 `model_match` 在当前库内未命中任何有效模型，提示维护者检查 pattern 是否拼写有误。

---

## 3. 测试与验证标准

1. **单元测试回归**：
   - 更新并运行 `tests/test_scoring.py`，新增针对通配符 pattern 匹配的单元测试用例；
   - 保证 `pytest` 全部测试 100% 通过。
2. **离线数据审计**：
   - 运行 `python scripts/verify_plans.py --offline`，保证 48 套餐审计 0 FAIL、0 WARN，并输出覆盖透视表。
3. **端到端效果验证**：
   - `muse-spark-1.3` 与 `muse-spark-1.2` 成功匹配到 `OpenCode Go`（6× 倍率），套餐内单价降至 ~$0.14/1M；
   - `deepseek-v4.1-flash` 成功匹配到 `火山方舟 Coding Plan Pro`（10× 倍率），套餐内单价维持在 ~$0.021/1M（¥0.141/1M）。
