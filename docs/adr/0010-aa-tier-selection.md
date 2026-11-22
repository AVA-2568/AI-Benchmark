# ADR-0010：AA 同 slug 多 reasoning 档的取行规则

- **状态**：已采纳（2026-11-22）
- **影响面**：`scripts/merge.py`、`tests/test_merge.py`、METHODOLOGY、AGENTS.md

## 背景

2026-11 起 Artificial Analysis 把同一模型的 reasoning effort 档位并列在**同一个 Model Slug** 下，靠 `label` 括号区分：`DeepSeek V4.1 Flash 1017 (non-reasoning)` / `(high)` / `(max)`。三档分数差距极大：

| label | FrontierCode 2.0 | Terminal-Bench v4.0 | CritPt v2 Hard | AutomationBench |
|---|---|---|---|---|
| (non-reasoning) | 0.061 | 0.091 | 0.010 | 0.488 |
| (high) | 0.168 | 0.288 | 0.275 | 0.685 |
| (max) | 0.285 | 0.338 | 0.250 | 0.666 |

`merge._pick_aa_row` 的旧实现是「遍历同 slug 的行，返回第一个官方 provider 行」，完全依赖 CSV 行序。AA 的 provider 页按分数排序，档位并列后行序随上游数据漂移：

- 2026-11-13 命中 `(max)` → `deepseek-v4.1-flash` Weighted Total **53.3**、排名 #12
- 2026-11-22 命中 `(non-reasoning)` → Weighted Total **34.5**、排名 #21

一次没有任何真实能力变化的重排，让榜单跌了 9 名、18.8 分。AA 目前 **101 个 slug 里有 46 个是多档**（claude-sonnet-5-5 五档、gpt-6-1-terra 六档），这是系统性风险而非个例。

## 决策

取行判据按以下优先级，缺一不可：

1. **覆盖度优先**：先取池内指标实测覆盖数最多的那批行。小模型的 `non-reasoning` 档常常只挂着 LCR 一个池指标（`gemma-4-31b`：1/10），纯按档位选会让其余 9 个指标变空、整行被打成填补值。
2. **档位次之**：覆盖度相同时取最高 effort 档（`non-reasoning < low < medium < high < xhigh < max`），与 LiveBench 取最高档的口径一致（ADR-0004）。
3. **官方 provider 优先**：同档内取官方行，定价用官方牌价（AA 各档 token 单价一致，仅 `costPerTask` 随档位变化，已实测确认）。
4. **末位 tie-break**：完全并列时取末行，保留 ADR-0005 之前的定价回退语义，保证同一份 CSV 每次选出同一行。

标签里的量化格式（FP8 / FP4 / NVFP4 / BF16）与部署标记（FAST / ULTRA / Vertex / AI Studio）不是档位，不参与排序。

## 明确否决的方案

- **逐指标取各档最大值**：会让同一模型的不同指标来自不同 effort 档，构成「拼接出来的模型」，违反 ADR-0005「同模型不混档」的原则。
- **按 label 档位硬选最高档**：会吃到只有定价、池指标全空的档位行（`gemma-4-31b` 等小模型），导致整行掉榜。
- **依赖行序**（旧行为）：结果不可复现，正是本次事故的成因。

## 影响

- `deepseek-v4.1-flash` 恢复 53.3 分 / #10，与 11-13 完全一致；`minimax-m3.1-flash` 48.9 分不变。
- AA 池指标覆盖 32~36/80，与修复前持平（不因取最高档而掉数据）。
- 新增 6 个回归测试，锁死「同档最高档」「量化后缀不参与排序」「覆盖度压过档位」「全空档位不入选」「同档官方优先」「AA_METRICS 必须是池指标子集」。
