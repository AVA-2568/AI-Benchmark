# ADR-0011：短域不做填补（指标数 < 3 的域）

- **状态**：已采纳（2026-11-22）
- **影响面**：`config.json`（`imputation.min_domain_metrics`）、
  `scripts/pipeline/imputation.py`、`scripts/pipeline/scoring.py`、
  `scripts/pipeline/config.py`、`scripts/merge.py`、
  `scripts/model_registry.json`、`tests/`、METHODOLOGY、AGENTS.md

## 背景

填补是**严格域内**的岭回归：目标指标的预测特征只取同域其余指标。因此
排除目标列后，特征维度 = 域内指标数 − 1。

通用榜与性价比榜的 3 个域都是 3 指标（`code_agent` /
`long_horizon_automation` / `hard_reasoning`），特征维度 2，尚可回归。
**文本榜 4 个域里有 3 个只有 2 指标**，合计承担 **70% 权重**：

| 域 | 权重 | 指标 | 两指标实测相关性 |
|---|---|---|---|
| 创意写作与文档表现 | 0.30 | EQ-Bench、LiveBench Design | r = 0.570（n=9） |
| 长上下文检索与推理 | 0.25 | MLCR、LCR | r = 0.600（n=304） |
| 事实与抗幻觉 | 0.15 | Omniscience Accuracy、Omniscience Non-Halluc. | **r = −0.130**（n=354） |
| 专业案头与深度研究 | 0.30 | AA-Briefcase、Research、Data Analysis | 三指标，正常 |

后果不是「填补不准」，而是**填补值就是兄弟指标的仿射变换**：

- 文本榜 17 个填补行的 EQ-Bench 全部落在 `EQ ≈ −140 + 27.2 × Design`
  直线上（±5 Elo 内 11/17，其余为 min/`clip_quantile` 截断所致）。
- 「创意写作」域的域得分与该直线代理值的偏差只有 **0.03–0.46 分**
  （满分 100）。该域对 2/3 的行**只有一个自由度**，却仍按 0.65 子权重
  参与评分，并把 `2135.0*` 这种值当成一次测量展示出来。

`factuality` 域更能说明「能跑通」不等于可信：两指标相关性 −0.13，
单特征回归比直接取域均值还差。它现在 0 填补纯属运气——不是因为设计正确。

### 为什么降权救不了

`imputed_weight_discount` 按指标打折后域内重归一化。但被降权的那一项
自己就是同域另一项的函数，重归一化恰好把权重还了回去：

| 设置 | 与现状的 Spearman ρ | 最大位次变动 |
|---|---|---|
| 0.5 | 0.998 | 1 |
| 0.3 | 0.995 | 2 |

同理，整域删除 EQ-Bench 也只有 ρ = 0.977。**调参在这个结构下是空操作。**

### 真正被放大的是「实测 / 填补不对称」

有实测的 9 行会拿到一次真正独立的写作读数，而它常常与 Design 冲突：

| 模型 | 实测 EQ(norm) | 若走填补 | 域分差 |
|---|---|---|---|
| deepseek-v4.1-flash | 17.5 | 78.8 | **−39.8** |
| kimi-k3.1-pro | 96.6 | 58.0 | **+25.1** |
| muse-wonder-1.0 | 75.9 | 48.5 | +17.8 |
| inkling | 26.1 | 0.0 | +17.0 |

一条模型**有没有被上游收录**，能让它在 30% 权重的域里上下浮动 40 分。
这是系统性偏置，不是噪声。

## 决策

`config.json` 新增 `imputation.min_domain_metrics: 3`。域内指标数低于该值
时：

1. **不填补**。`ImputationEngine.imputable[m] = False`，`run()` 跳过该
   指标，`cur` 保持初始化值。
2. **缺值不参与评分**。`score_board` 把它记为 `unavailable`，不进入
   `nrm`，CSV 单元格留空（与 `merged.csv`「空 = 上游未测」同义）。
3. **权重按剩余项重归一化**。`_weighted_total` 恒按有效权重和归一化；
   域得分也按域内剩余子权重归一化——否则 `0.35 × Design` 会被当成 35 分，
   使缺指标的域被系统性误判为短板（`Bottleneck`）。

不填补的域仍然照常参与评分：域得分由实测指标承担，该域权重不变。上榜
门槛（`max_missing_per_domain: 1`，ADR-0006）不变，因此行数不减。

## 明确否决的方案

- **继续用 `imputed_weight_discount` 降权**：见上表，ρ ≥ 0.995，等于没改，
  而且伪造的数值仍会出现在表里。
- **彻底禁止 2 指标域的缺失**（要求两指标全实测）：文本榜会从 26 行
  塌到 9 行，`eqbench` 上游长期滞后于 AA，等于让榜单跟随最慢的数据源。
- **给短域硬凑第三个指标**：`factuality` 看似可加未纳入的
  `Omniscience Index`，但它是 Accuracy / Non-Halluc. 的复合量（线性还原
  MAE 17.6，无法拟合），不是独立信号；`creative_writing` 与
  `long_context` 在现有三个源里都没有第三个候选（LiveBench 2.0 仅 7 类、
  无写作项；AA 的 37 个评分列亦无写作项）。凑数会让「3 指标域」变成
  形式合规。
- **按区分度重排文本榜权重**：`创意写作` 拿 30% 权重只贡献 14% 的 Top10
  区分度，`长上下文` 25% 权重贡献 37%，确实倒挂；但重排会实质改变榜单
  名次，属产品决策，需按 ADR-0009 在两榜同时验证，不在本 ADR 范围内。

## 影响

以上数字为 2026-11-22 构建（commit `5d8b654`，26 行）实测：

- 文本榜排名基本稳定：与修改前 **ρ = 0.9891**，最大位次变动 3 位
  （`muse-wonder-1.0` #12→#9、`gpt-6.1-terra` #9→#12）。
- **文本榜填补归零**：`Imputed` 列 26 行全空，全表没有任何 `*` 单元格。
  EQ-Bench 17 行留空、LCR 6 行留空，其余指标本就全实测。
- 分数修正集中在低端：原先正被伪造的低填补值惩罚
  `muse-spark-open` **+10.1**（46.1→56.2）、`nemotron-super-vl-3.5`
  **+7.7**（42.5→50.2）、`gemma-4-31b` +2.1、`minimax-m3.1-flash` +1.8。
- 高端小幅回落（它们的 EQ 填补值原本高于实测均值）：
  `mistral-large-4` −2.5、`qwen4-max` −1.9、`gpt-6.2-astra` −1.8、
  `gpt-6.1-terra` −1.3。
- 通用榜、性价比榜逐行不变（无短域）。
- 头部压缩未解决：#9/#10 分差 0.2、Top1–Top10 极差 13.7（通用榜 16.5），
  Top10 相邻分差 `[4.2, 0.1, 0.2, 2.1, 0.9, 0.7, 2.9, 2.4, 0.2]`——
  这是权重议题（创意写作域 sd 4.02 却占 0.30 权重），不在本 ADR 范围内。
- 新增 `_check_eqbench_join` 哨兵：registry 配了 eqbench 别名却 0 行匹配时
  直接失败，防止源侧改名让「创意写作」覆盖静默归零、退化成单变量填补
  （与 `_check_aa_join` 同类，见 ADR-0010 背景）。
- registry 里 7 个指向源中不存在模型的 `eqbench` 别名（`gpt-5.4-nano`、
  `gpt-5.2-codex`、`gemini-3.5-flash`、`grok-4.6`、`grok-4.3`、
  `kimi-k2.7-code`、`qwen3.7-max`）置为 `null`，与「null = 该源未评测」
  的既有约定一致。
- 新增 12 个回归测试（测试总数 190 → 202）：短域不可填补 / 短域缺值保持回退值 /
  3 指标域仍填补 / 不可用指标留空且不参与加权 / 域内 Bottleneck 重归一化 /
  `_weighted_total` 重归一化与零权重 / `min_domain_metrics` 下限校验与默认值 /
  EQ-Bench join 哨兵三种情形。
