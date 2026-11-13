# ADR-0009：重铸两榜为零共享的能力链，以头部区分度为准绳

- **状态**：已采纳（2026-11-13）
- **影响面**：`config.json`、`scripts/merge.py`、`scripts/pipeline/scoring.py`、`scripts/build.py`、`tests/fixtures/*`、`tests/test_score_helpers.py`、METHODOLOGY、README、AGENTS.md

## 背景

重铸前三个可量化的问题：

1. **两张榜其实是一张**：通用榜与文本榜共享 LCR / MLCR / Omniscience Index / LiveBench Reasoning / CritPt v2 Hard 等底层指标，排名 Spearman **0.928**、Top15 重合 **13/15**、榜首同一个模型。读者想看的「写代码强 vs 写文章强」分不出来。
2. **头部名次落在噪声里**：通用榜 Top5 首尾只差 **7.4 分**，而 12 个指标里有 7 个的归一化填补 MAE 超过 7.4 分（Omniscience Index 17.5、MLCR 16.6、LiveBench Browser 14.1）。第 2~5 名之间 1~2 分的差距不可信。
3. **权重与区分度错配**：HLE 占 12% 全局权重却只贡献 1.25 的加权标准差（头部 sd 7.2），LCR 占 11% 贡献 0.47（头部 sd 2.1）；反过来 Omniscience Index 与 MLCR 贡献了约 24.5% 的分差，却是 R² 0.192 / 0.215 的低可信指标——榜单把填补噪声当成了能力差距。

另外 `domain_groups`（7 域）与 `leaderboards.categories`（两榜各 5 域）是两套划分，存在三处不闭合（通用榜业务自动化域借用文本榜 professional_work 的 LiveBench Data Analysis、通用榜事实域 1 指标挂在 2 指标 factuality 域、文本榜推理域挂在含 HLE 的 3 指标 reasoning 域），回归特征会跨榜借用。

## 决策

1. **零共享的能力链**：通用榜（偏编程）= 工程能力链，3 域 9 指标；文本榜 = 内容生产能力链，4 域 9 指标。18 个池指标分属两榜，**不共享任何一个**。每榜都同时含 Artificial Analysis 与 LiveBench 2.0 的原始基准（文本榜另用 EQ-Bench 创意写作 Elo）。
2. **不使用单一榜单的结论**：不引用任何上游综合分（AA Intelligence Index / LiveBench 总榜），不拿一张榜的结论定义另一张，两榜各自独立评分。指标入池、替换与权重调整必须同时在两榜数据上验证，不能只看单榜的表现下结论。
3. **用同构难版替换头部饱和指标**（替换非叠加，池指标数保持 18）：

   | 退役 | 启用 | Top10 sd | 说明 |
   |---|---|---|---|
   | HLE | HLE Diamond | 7.2 → 16.1 | 博士级难题子集 |
   | Omniscience Index | Omniscience Accuracy | 9.1 → 13.8 | 与 Non-Halluc. r=-0.066，独立 |
   | 科学域主锚让位 | FrontierCode 2.0 | (TB v4.0 4.4) → 16.3 | 前沿代码难题，Top10 区分度最高 |

   Terminal-Bench v4.0 与 CritPt v2 Hard 保留，与新基准构成难度梯度，不叠加同构指标。
4. **权重按「头部分辨率 × 信噪比」配置**，不按语义重要性平均分配：MLCR 70 / LCR 30（Top10 sd 20.1 vs 2.1）、EQ-Bench 65 / LiveBench Design 35（实测 sd 28 vs 8）。通用榜代码与终端 Agent 45% / 长程自主与自动化 25% / 科学与硬推理 30%，文本榜创意写作 30% / 专业案头 30% / 长上下文 25% / 事实 15%。
5. **域定义唯一**：7 个 `domain_groups` 与两榜 `categories` 一一对应，每个域只服务一个榜，回归严格域内。`domain_hierarchies` 因新指标难度阶梯未实证而清空（「宁可无约束，不设错约束」）。
6. **短板可见**：输出 `Bottleneck`（最低域分）与 `Bottleneck Domain`。加权总分允许长板补偿短板，但真实 agent / 案头任务是串联的，短板决定成败。

## 后果

- 三榜仍 **26 行**，上榜门槛不变（每域最多缺 1，无例外）。
- 通用榜 **26/26 行全实测**（重铸前 24/26）；Top5 分差 7.4 → **9.2**，全榜标准差 15.5 → **20.1**。
- 文本榜 Top5 分差 4.7 → **7.9**，全榜标准差 13.8 → 14.7；两榜 Spearman 0.928 → **0.884**。
- 短板列暴露出头部模型普遍卡在「长程自主与自动化」域（75~77 分），这在单一综合分里完全看不见。
- `config.json` / `merge.py` / `scoring.py` / `build.py` / 测试 fixture 与 golden 快照 / 三份文档全部同步；`python -m pytest -q` 177 passed，`build.py --offline` BUILD OK。

## 已知限制

- **文本榜 15/26 行带填补**，集中在 EQ-Bench Creative Writing（实测覆盖 46/75、域内 R² 0.036）。`Imputed` 列逐行标注，`imputed_weight_discount` 仍为默认 1.0。下一步应按指标 R² 做差异化降权，避免低信噪填补值制造头部名次。
- **FrontierCode 2.0 与 LiveBench Long-Horizon r=0.944**，分属两个域仍有同源重复计权。保留理由是二者分别测难题代码上限与长程工程耐力，且长程域权重仅 25%。ADR-0008 否决的是「已有 LB Long-Horizon 再叠加 FrontierCode 2.0」，与本处分域共存不同。
- 两榜 Spearman 仍达 0.884：工程轴与内容轴在本季数据上 Pearson 0.946，模型底层能力高度相关，零共享只能拉到这个程度，不能制造出不存在的能力维度。
- 榜单不测可靠性（同任务重复成功率）、长程自主的步数上限与成本-成功率曲线。上游没有这类公开数据，不硬造，但读者应知道这是空白。

## 替代方案

- **只重排域名、沿用现有指标**：模拟显示通用榜 Top5 分差 7.4 → 7.1，几乎无改善。头部饱和是根因，已否决。
- **把 AA 的 5 个满覆盖新指标全部加入池**：彼此 r 0.87~0.96（Terminal-Bench Science ~ HLE Diamond 0.961），叠加等于重复计权，且 ADR-0008 已否决。改为替换，已否决叠加。
- **域分几何平均替代算术加权**：模拟显示 Top5 分差 9.9 → 9.7、全体 sd 20.6 → 20.9，收益极小。改为输出短板列表达短板，不动总分算法，已否决。
- **按榜分域重构 ImputationEngine**（允许同一指标在两榜属不同域）：能彻底消除跨域借特征，但改动面大。零共享方案天然让每个域只服务一榜，无需重构，已否决。
