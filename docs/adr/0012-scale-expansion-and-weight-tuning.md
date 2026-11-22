# ADR-0012：克制微调触顶锚点与修复评分/成本边界

- **状态**：已采纳（2026-11-22）
- **影响面**：`config.json`、`scripts/pipeline/`、`scripts/build.py`、`scripts/plot_frontier.py`、`scripts/parse_aa.py`、`scripts/verify_plans.py`、`requirements.txt`、`tests/`、`README.md`、`AGENTS.md`

## 背景

2026-11 实测数据暴露出两类确定性问题：

1. **部分固定锚点已被击穿或贴顶（>97.5%）**：`AA-Briefcase`（原 `[400, 1700]`）已有 3 个模型突破 1700 被截断成 100 分（最高 1813.08）、1 个低于 400 被截成 0 分；`HLE Diamond`（原 `[0, 0.8]`）已被 `0.802` 击穿；`FrontierCode 2.0`（0.488/0.5，97.6%）与 `Omniscience Accuracy`（0.791/0.8，98.9%）已贴顶。
2. **工程边界缺陷**：
   - `_weighted_total` 实际做扁平重归一化，与 ADR-0011「短域缺测时该域权重不变」矛盾；
   - `_plans_block` 未应用 `model_cost_scale`，导致 GLM 套餐在指南表与主表差 3 倍；
   - `_creator_cache_price_mean` 用绝对缓存价均值回退，导致免费模型（`gemma-4-31b` 输入 `$0`）被赋予 `$0.1425` 缓存价；
   - 岭回归正则矩阵惩罚了截距项 `β₀`；
   - `pareto_frontier` 同价未按分数降序导致低分点混入；`build.py --offline` 误设 `stale=True` 跳过 README 刷新；`scikit-learn` 仅用于 1 处 `StandardScaler` 却引入重依赖。

## 决策

1. **克制微调已触顶/贴顶的 4 个锚点，不破坏各域分值量级与 `Bottleneck` 平衡**：
   - `AA-Briefcase`：`[400, 1700]` → `[350, 2000]`
   - `HLE Diamond`：`[0, 0.8]` → `[0, 0.9]`
   - `FrontierCode 2.0`：`[0, 0.5]` → `[0, 0.6]`
   - `Omniscience Accuracy`：`[0, 0.8]` → `[0, 0.9]`
2. **保持两榜 18 指标与全部权重不变**：不为了追求头部标准差而削弱榜单本身的语义定位（如保留 `Terminal-Bench v4.0` 30% 的终端 Agent 权重、`LiveBench Reasoning` 25% 的跨源制衡、文本榜创意写作域 30% 的核心占比）。
3. **全面修复工程缺陷**：`_weighted_total` 改为先域内归一化再按域权重加权；缓存回退改为厂商平均缓存折扣率并强制 `<= pin`；岭回归截距不惩罚；移除 `scikit-learn` 改用 4 行 numpy 标准化并删除零使用的 `pipeline/models.py`；`_plans_block` 复用 `model_cost_scale`；`--offline` 不再置 `stale=True`；`validate_config` 补全 `metric_scales` 与两榜零共享校验；`verify_plans` 接入 `url_guard`。
