# ADR-0008：以「LiveBench 本季模型的 AA 覆盖率」为准绳换基准

- **状态**：已采纳（2026-11-12）
- **影响面**：`config.json`、`scripts/merge.py`、`scripts/parse_aa.py`、`tests/fixtures/*`、`tests/test_parse.py`、METHODOLOGY、README

## 背景

选基准此前一直按「语义贴题」＋「全池覆盖」两条标准，但全池 75 个模型里有一半是历史条目，上游已不再测它们。真正决定榜单形态的是 **LiveBench 本季 release 的 34 个模型**——它们同时是唯一一批「AA 与 LiveBench 双源都在跟踪」的前沿模型。以它们为分母重算覆盖率，结论与全池视角不同：

| 基准 | 34 个 LB 模型的 AA 覆盖 | 说明 |
|---|---|---|
| Terminal-Bench v4.0 / AutomationBench / AA-Briefcase / Omniscience Index | 27/27 | 满覆盖，保留 |
| CritPt v2 Hard / HLE Diamond / Terminal-Bench Science / FrontierCode 2.0 | 27/27 | 2026-11 新上，此前从未拉取 |
| LCR | 25/27 | 覆盖够，但 sd 仅 0.05（全挤在 0.69–0.88） |
| SciCode | 24/27 | 覆盖最低的在用指标 |
| IFBench / tau3 / TB v2.1 / GPQA / ITBench | 1–8/27 | 覆盖不足，不可用 |

两个硬信号：

1. **SciCode 被 AA 标注 `underReview`**：「An independent audit has flagged possible errors in the dataset of this evaluation.」而它当时承担推理域 25% 子权重。
2. **AA 新增了 15 个评分字段**（frontiercode-2-0、hle-diamond、critpt-v2-hard、mlcr-aa、terminal-bench-science、gdp-pdf、aa-analyst-agent、mka、vials-aa 等），`parse_aa.py` 的固定列清单把它们全部静默丢弃——不是「没有更好的指标」，是「有，但我们从来没拉」。

## 决策

1. **推理域 SciCode → CritPt v2 Hard**（子权重仍 25%）。CritPt v2 Hard 覆盖 27/27、sd 0.209（SciCode 为 24/27、sd 0.06），与 HLE r=0.875，不与主指标重复。
2. **长上下文域 LCR 100% → LCR 55% + MLCR 45%**。MLCR 覆盖 26/27、sd 0.11，与 LCR 仅 r=0.44——是互补而非重复，补上非英文长文维度，同时把该域从单指标变成双指标（单指标域必须实测，双指标域可缺 1）。
3. **文本榜第 5 域改名「推理与科研判断」，CritPt → CritPt v2 Hard**。原域名「人际心智与人文社科」与内容无关（两个指标都不是人文/心智），且池内没有 Theory-of-Mind 基准。
4. **解析器补齐**：新增 `NEW_SCORE_FIELDS`（15 个），并加 `unmapped_score_fields()` —— 每次解析点名任何未登记的评分字段，避免再出现「AA 上新基准、我们永远拉不到」。

## 后果

- 三榜 25 → **26 行**（新增 1 个此前因缺长上下文实测而落榜的模型）。
- 通用榜：claude-fable-5.2 81.1 / gpt-6-astra 76.6 / claude-opus-5.5 75.2 / gemini-4-carbon 74.2（#4）。carbon 的缺口从「HLE + SciCode」缩到只剩 HLE，不再依赖 ADR-0007 的放宽条款。
- 文本榜：claude-fable-5.2 87.5 / gpt-6-astra 86.0 / gemini-4-carbon 83.0（#3）。
- LCR 的 R² 从 0.000 升到 0.245、MLCR 0.221（互为依据）；SciCode 的 R² 0.873 随之下架，CritPt v2 为 0.820。
- 池仍是 17 个指标、7 个域（`humanities_mind` 空域删除），`domain_hierarchies` 的 `instruction` 链随之取消（LCR 与 MLCR 不是难度阶梯，设链会错误压制）。

## 替代方案

- **保留 SciCode、只降权重**：数据集被审计标疑，降权仍会把可能错误的数据计入 5% 全局分，已否决。
- **用 HLE Diamond 替 HLE**：与 HLE r=0.907，同构念升级。覆盖 27/27、sd 0.208 确实更好，但会切断 HLE 的历史时间序列，且与 CritPt v2 Hard（r=0.936）叠加即重复计权。列为下一季的升级项。
- **用 FrontierCode 2.0 替 LiveBench Coding**：与 LB Long-Horizon r=0.945，进榜等于重复计权，已否决。
- **把 15 个新基准全部入池**：AA Analyst Agent / MKA / VIALS / AA-3D / Code2Video / HealthBench 在 LB 本季模型上覆盖 10–21/27，域内会变成「缺 2」，大面积落榜。只取满覆盖的 5 个。
