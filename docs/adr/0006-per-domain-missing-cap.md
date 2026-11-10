# ADR-0006：上榜门槛按「领域内缺失的基准值个数」判定

- **状态**：已采纳（2026-11-10）
- **影响面**：`config.json`、`scripts/pipeline/scoring.py`、`tests/test_scoring.py`、METHODOLOGY、README

## 背景

榜单的每个领域由 2–3 个基准值构成，且这些基准值来自不同数据源：

| 领域 | 基准值 | 来源 |
|---|---|---|
| 代码与 Agent | Terminal-Bench v4.0 / LiveBench Long-Horizon / LiveBench Coding | AA + LiveBench |
| 业务自动化与 Web | AutomationBench / LiveBench Browser / LiveBench Data Analysis | AA + LiveBench |
| 指令遵循与长上下文 | LCR | AA |
| 终极科学与推理 | HLE / SciCode / LiveBench Reasoning | AA + LiveBench |
| 事实准确性 | Omniscience Index | AA |
| 创意文学（文本榜） | EQ-Bench Creative Writing / LiveBench Design | EQ-Bench + LiveBench |

2026-11 LiveBench 收窄到最新 release（33 个模型）后，LB 系覆盖从 70/73 掉到 29/73。原来的 `max_imputed_ratio = 0.45` 是一刀切的全局缺失率，会把「只缺一个领域里两个值」和「整体缺一半指标」当成同一类问题，结果把 `glm-5.3`、`minimax-m3`、`deepseek-v4-pro` 这类主力挤出榜单——它们只是缺了 LiveBench 那一路。

## 决策

按**领域内缺失的基准值个数**设门槛，而不是按数据源个数或全局缺失率：

```
每个领域：need = max(1, 领域基准数 - max_missing_per_domain)
```

`max_missing_per_domain = 1`（`config.json`），因此：

- 3 基准域：至少 2 个实测 → 缺 1 个可回测，缺 2 个整行不上榜；
- 2 基准域：至少 1 个实测 → 缺 1 个可回测，两个全缺则不上榜；
- 单基准域：必须实测（没有「缺一个」的余地）。

实现位置：`pipeline.scoring._domain_ok()`，按各榜自己的 `categories` 判定；`max_imputed_ratio` 降级为指标层面的二次保护（0.45 → 0.6）。

## 后果

- 73 个池模型 → **24 个上榜**，通用/文本/性价比三榜均 24 行。
- 榜内数据几乎全是实测：**通用榜 100% 实测**，文本榜按权重 93% 实测（其余为 `EQ-Bench ↔ LiveBench Design` 互测）。
- 榜首与主力模型保留（claude-opus-5.5 / claude-fable-5.1 / gpt-6-astra 等），出局的是证据不足的长尾与只存在于旧口径的模型。
- 代价：榜面从 35 行缩到 24 行。这是有意的——榜单的价值在「测得准」，不在「排得多」。
- 门槛是逐榜判定的，同一模型可能在文本榜上榜、通用榜落榜（例如只有 EQ + 部分 LB 的写作向模型）。

## 替代方案

- **按数据源个数（≥2 源）判定**：源是聚合概念，一个源覆盖多个领域；某模型缺整个 LB 但仍有两个源时会带着 40% 的填补值上榜，恰恰是本次要避免的。已否决。
- **保留全局缺失率 0.45**：一刀切，无法区分「缺一个域的两个值」与「缺半个池」，已否决。
- **不做门槛、全靠填补**：会出现「一个实测值 + 十个回归值」的排名，破坏榜单可信度，已否决。
