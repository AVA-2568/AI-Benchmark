# AI 前沿模型排行 LLM Leaderboard：通用 / 写作 / 性价比三榜

50 个主流旗舰大模型，三个问题三张榜：写代码用哪个模型（通用榜，claude-fable-5.1 第一，70.5 分）、写文章用哪个（文本榜，gpt-6-astra 第一，77.7 分）、买哪个订阅最划算（性价比榜，订阅折算后单价最低约 $0.005/M）。数据来自 LiveBench、DeepSWE、EQ-Bench、Artificial Analysis 四个独立评测的交叉聚合，不是某一家的一家之言；价格同时给美元和人民币，每月随上游自动更新一次。

## 能力-成本曲线：预算多少，买哪个模型

每个点是一个模型：横轴是实际支付价（最优订阅套餐折算后的等效价，无订阅厂商即官方按量混合价；人民币、对数刻度），纵轴是通用榜综合分。红色阶梯线是最优选择前沿：在横轴上定位你的预算，前沿在该处的高度就是这笔预算能买到的最强模型。当前前沿自左向右依次是 gpt-5.4-nano、minimax-m3、glm-5.3-flash、gpt-5.6-terra、glm-5.3、gpt-5.6-sol、claude-opus-5、gpt-6-astra，终点是 claude-fable-5.1。

<!--FRONTIER_START-->
![能力-成本前沿：给定每 1M token 预算时的最优模型](results/value_frontier.svg)
<!--FRONTIER_END-->

## 这个榜单怎么做

大多数公开榜单要么只看一家的合成指数，要么把几百个长尾模型堆在一起凑数。这里的做法不同：

- 只要旗舰（50 个），不要长尾。国际六家加国内七家，每家只取主力版本。长尾的重复变体和已弃用条目堆着只会稀释参考价值。
- 四个独立源交叉聚合：LiveBench、DeepSWE、EQ-Bench、Artificial Analysis。单一来源有偏见，交叉验证更可信。
- 固定锚点打分：按指标理论范围换算 0-100 分，不做「样本第一 = 100」的名次分。加新模型不影响已有分数，分数反映真实差距。
- 美元与人民币双币价，汇率每次构建实时抓取。

## 通用榜 Top 15

编程、智能体、日常混合使用看这张。权重：代码与 Agent 35%（Terminal-Bench v4.0 45%、DeepSWE 35%、LiveBench Coding 20%）、业务自动化 15%、指令遵循与长上下文 20%、科学与推理 20%、事实准确性 10%。

<!--SNAPSHOT_GENERAL_START-->
> 2026-09-08 数据（50 精选模型 -> 50 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.07 (>10%: 84.6%/39) ; DeepSWE MAE=8.39 (>10%: 53.6%/28) ; LiveBench Coding MAE=3.02 (>10%: 4.2%/48) ; tau3-Banking MAE=0.05 (>10%: 56.5%/46) ; LiveBench Data Analysis MAE=4.80 (>10%: 18.8%/48) ; LiveBench Agentic Coding MAE=3.66 (>10%: 27.1%/48) ; LiveBench Instruction Following MAE=2.26 (>10%: 0.0%/48) ; LCR MAE=0.02 (>10%: 0.0%/50) ; HLE MAE=0.03 (>10%: 20.0%/50) ; SciCode MAE=0.02 (>10%: 2.4%/42) ; LiveBench Reasoning MAE=3.25 (>10%: 6.2%/48) ; Omniscience Index MAE=14.65 (>10%: 96.0%/50)
<!--SNAPSHOT_GENERAL_END-->

<!--TOP15_GENERAL_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-fable-5.1 | Anthropic | 👁️ | 70.5 | DeepSWE(reg) |
| 2 | gpt-6-astra | OpenAI | 👁️ | 69.6 | - |
| 3 | claude-fable-5 | Anthropic | 👁️ | 67.1 | - |
| 4 | claude-opus-5 | Anthropic | 👁️ | 65.9 | - |
| 5 | gpt-5.6-sol | OpenAI | 👁️ | 63.9 | - |
| 6 | muse-spark-1.3 | Meta | 👁️ | 63.4 | DeepSWE(reg) |
| 7 | glm-5.3 | Z.AI | - | 61.2 | - |
| 8 | gemini-3.8-flash | Google | 👁️ | 60.1 | - |
| 9 | grok-4.6 | xAI | 👁️ | 59.6 | - |
| 10 | kimi-k3 | Moonshot AI | 👁️ | 59.1 | - |
| 11 | claude-opus-4.7 | Anthropic | 👁️ | 58.1 | Terminal-Bench v4.0(reg), DeepSWE(reg), SciCode(reg) |
| 12 | gpt-5.6-terra | OpenAI | 👁️ | 58.0 | - |
| 13 | gemini-3.7-flash | Google | 👁️ | 57.9 | - |
| 14 | gpt-5.5 | OpenAI | 👁️ | 57.9 | - |
| 15 | claude-opus-4.8 | Anthropic | 👁️ | 57.4 | - |
<!--TOP15_GENERAL_END-->

[完整排名 CSV](results/general_scored.csv)

## 文本榜 Top 15

适用于文学创作、长篇阅读、专业案头分析与日常问答。评测覆盖 5 个维度：创意文学 25%（StoryGen 55%、Language 45%）、专业案头 20%（AA-Briefcase 50%、Data Analysis 25%、Summarize 25%）、指令约束 20%、事实与长文本 20%、人际心智 15%。不包含代码生成与数理考试指标。图表纵轴为文本榜综合分，横轴为百万 token 成本，用于按预算选型。

<!--TEXT_FRONTIER_START-->
![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型](results/text_frontier.svg)
<!--TEXT_FRONTIER_END-->

<!--SNAPSHOT_TEXT_START-->
> 2026-09-08 数据（50 精选模型 -> 50 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：LiveBench StoryGen MAE=4.64 (>10%: 22.9%/48) ; LiveBench Language MAE=4.60 (>10%: 14.6%/48) ; AA-Briefcase MAE=213.41 (>10%: 61.9%/42) ; LiveBench Data Analysis MAE=4.80 (>10%: 18.8%/48) ; LiveBench Summarize MAE=7.58 (>10%: 43.8%/48) ; LiveBench Instruction Following MAE=2.26 (>10%: 0.0%/48) ; LiveBench Simplify MAE=2.25 (>10%: 0.0%/48) ; Omniscience Index MAE=14.65 (>10%: 96.0%/50) ; LCR MAE=0.02 (>10%: 0.0%/50) ; Omniscience Non-Halluc. MAE=0.20 (>10%: 88.0%/50) ; LiveBench Theory of Mind MAE=4.86 (>10%: 10.4%/48) ; CritPt MAE=0.05 (>10%: 84.0%/50)
<!--SNAPSHOT_TEXT_END-->

<!--TOP15_TEXT_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | gpt-6-astra | OpenAI | 👁️ | 77.7 | - |
| 2 | claude-fable-5.1 | Anthropic | 👁️ | 77.1 | - |
| 3 | claude-fable-5 | Anthropic | 👁️ | 76.8 | - |
| 4 | muse-spark-1.3 | Meta | 👁️ | 76.7 | - |
| 5 | grok-4.6 | xAI | 👁️ | 74.5 | - |
| 6 | gemini-3.8-flash | Google | 👁️ | 72.9 | - |
| 7 | kimi-k3 | Moonshot AI | 👁️ | 72.7 | - |
| 8 | gpt-5.6-sol | OpenAI | 👁️ | 72.4 | - |
| 9 | muse-spark-1.2 | Meta | 👁️ | 72.0 | - |
| 10 | gemini-3.7-flash | Google | 👁️ | 71.9 | - |
| 11 | claude-opus-5 | Anthropic | 👁️ | 71.5 | - |
| 12 | claude-opus-4.8 | Anthropic | 👁️ | 71.4 | - |
| 13 | glm-5.3 | Z.AI | - | 71.4 | - |
| 14 | grok-4.5 | xAI | 👁️ | 70.2 | - |
| 15 | qwen3.8-max | Alibaba | 👁️ | 69.9 | - |
<!--TOP15_TEXT_END-->

[完整排名 CSV](results/text_scored.csv)

## 性价比榜 Top 15

回答「买哪个套餐最划算」。行序跟通用榜一致——按性价比排会让便宜小模型霸榜，没有决策价值。各列含义：API $/1M 是官方按量混合价（含缓存命中假设）；套餐内 $/1M 是该厂商最优订阅折算后的等效价；倍率是每 1 元月费换到的 API 等价额度，70× 即 $1 月费约换 $70 额度；Value = 综合分 ÷ 套餐内 $/1M。套餐名就是官方购买链接，没有订阅制的厂商按 API 按量计费（1×）。

<!--SNAPSHOT_VALUE_START-->
> 2026-09-08 数据（50 精选模型 -> 50 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.07 (>10%: 84.6%/39) ; DeepSWE MAE=8.39 (>10%: 53.6%/28) ; LiveBench Coding MAE=3.02 (>10%: 4.2%/48) ; tau3-Banking MAE=0.05 (>10%: 56.5%/46) ; LiveBench Data Analysis MAE=4.80 (>10%: 18.8%/48) ; LiveBench Agentic Coding MAE=3.66 (>10%: 27.1%/48) ; LiveBench Instruction Following MAE=2.26 (>10%: 0.0%/48) ; LCR MAE=0.02 (>10%: 0.0%/50) ; HLE MAE=0.03 (>10%: 20.0%/50) ; SciCode MAE=0.02 (>10%: 2.4%/42) ; LiveBench Reasoning MAE=3.25 (>10%: 6.2%/48) ; Omniscience Index MAE=14.65 (>10%: 96.0%/50)
<!--SNAPSHOT_VALUE_END-->

<!--TOP15_VALUE_START-->
| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | claude-fable-5.1 | Anthropic | 👁️ | 70.5 | 8.541 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.214 | 1.436 | 329.44 |
| 2 | gpt-6-astra | OpenAI | 👁️ | 69.6 | 9.115 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.13 | 0.872 | 535.73 |
| 3 | claude-fable-5 | Anthropic | 👁️ | 67.1 | 8.651 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.216 | 1.449 | 310.65 |
| 4 | claude-opus-5 | Anthropic | 👁️ | 65.9 | 4.558 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.114 | 0.765 | 578.5 |
| 5 | gpt-5.6-sol | OpenAI | 👁️ | 63.9 | 3.646 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.052 | 0.349 | 1228.82 |
| 6 | muse-spark-1.3 | Meta | 👁️ | 63.4 | 0.858 | API 按量 | - | 1× | 0.858 | 5.756 | 73.94 |
| 7 | glm-5.3 | Z.AI | - | 61.2 | 1.329 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | 34.4× | 0.039 | 0.262 | 1568.3 |
| 8 | gemini-3.8-flash | Google | 👁️ | 60.1 | 0.684 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | 2× | 0.342 | 2.294 | 175.87 |
| 9 | grok-4.6 | xAI | 👁️ | 59.6 | 1.452 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | 5.3× | 0.272 | 1.825 | 219.26 |
| 10 | kimi-k3 | Moonshot AI | 👁️ | 59.1 | 2.734 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | 4.5× | 0.602 | 4.038 | 98.21 |
| 11 | claude-opus-4.7 | Anthropic | 👁️ | 58.1 | 4.558 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.114 | 0.765 | 509.64 |
| 12 | gpt-5.6-terra | OpenAI | 👁️ | 58.0 | 2.923 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.042 | 0.282 | 1382.03 |
| 13 | gemini-3.7-flash | Google | 👁️ | 57.9 | 0.684 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | 2× | 0.342 | 2.294 | 169.37 |
| 14 | gpt-5.5 | OpenAI | 👁️ | 57.9 | 5.308 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.076 | 0.51 | 761.43 |
| 15 | claude-opus-4.8 | Anthropic | 👁️ | 57.4 | 4.558 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.114 | 0.765 | 503.91 |
<!--TOP15_VALUE_END-->

[完整排名 CSV](results/value_scored.csv)

Imputed 列：`-` 表示全部真实值，`指标(reg)` 是岭回归填补，`指标(reg,low)` 是低可信填补。性价比榜完整 CSV 里还有 `Blended $/1M`（无折扣混合价）和 `Plan Monthly / Multiplier / Discount / URL` 等套餐明细列。

## 套餐购买指南

按订阅维度直接对比「买哪家最值」。每个套餐取它覆盖的厂商里通用榜最强的模型，按「套餐内 Value = 最强模型分 ÷ 该套餐下等效价」从高到低排。这个排法同时反映两件事：套餐能用到多强的模型、折算后到底多便宜，不是单纯比谁额度大。

各列口径：

- 倍率 = 每 1 元月费换到的 API 等价额度；折扣 = 套餐内单价 ÷ 官方单价
- ≈Token/月：官方公布了 token 池的直接引用（MiniMax、GLM、混元、MiMo）；没公布的按「API 等价价值 ÷ 最强模型官方混合价」估算，即额度全部用于该模型时的量，实际用便宜模型能换到更多

数据来源与时点：ChatGPT / Claude 倍率来自 SemiAnalysis 2026-06 实测，Copilot 是 GitHub 官方额度，Grok 为 agentplans.fyi 2026-06 估算，Kimi 为社区实测，国内各家为 2026-08 官方页面实查，聚合与 IDE 类（OpenCode Go、Factory、Trae、Cursor）为 awesome-coding-plan 2026-08 第三方实测。倍率一律按用满额度上限计算，轻度用户实际拿不到这么多。国内套餐标价为人民币，¥/月 按实时汇率折算。

积分制套餐没有倍率。千问 Token Plan 和 WorkBuddy 官方都没公布 Credits 换 token 的系数，社区两套口径相差 5 到 10 倍，给数字等于编数，所以只列官方积分额度；WorkBuddy 的 token 量按社区实测「1 积分 ≈ 4,100 token」折了个大概，仅供参考。

两个例外。Gemini 官方订阅不含 API 额度，不进表，编程需求可以由 GitHub Copilot 覆盖；DeepSeek 没有自有订阅制，由腾讯云 Hy Token Plan Standard 聚合池提供第三方折扣（详见 FAQ）。

<!--PLANS_GUIDE_START-->
| # | 套餐 | 月费 | ¥/月 | 倍率 | 折扣 | ≈Token/月 | 最强模型（通用榜） | 模型分 | 套餐内 $/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | ¥111 | 66.3× | 1.5% | 18亿+ | minimax-m3 (#42) | 44.4 | 0.004 | 11714.7 |
| 2 | [MiniMax Ultra Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $65.1 | ¥437 | 66.3× | 1.5% | 71亿+ | minimax-m3 (#42) | 44.4 | 0.004 | 11714.7 |
| 3 | [MiniMax Plus Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $6.8 | ¥46 | 53.7× | 1.9% | 6亿+ | minimax-m3 (#42) | 44.4 | 0.005 | 9510.3 |
| 4 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | ¥1004 | 34.4× | 2.9% | ≈29.3~58.6亿/月 | glm-5.3 (#7) | 61.2 | 0.039 | 1587.9 |
| 5 | [GLM Coding Plan Pro](https://bigmodel.cn/glm-coding) | $74.7 | ¥501 | 29.6× | 3.4% | ≈12.6~25.1亿/月 | glm-5.3 (#7) | 61.2 | 0.045 | 1354.4 |
| 6 | [GLM Coding Plan Lite](https://bigmodel.cn/glm-coding) | $16.4 | ¥110 | 22.4× | 4.5% | ≈2.1~4.2亿/月 | glm-5.3 (#7) | 61.2 | 0.06 | 1023.3 |
| 7 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | ¥1342 | 70× | 1.4% | ≈15亿 | gpt-6-astra (#2) | 69.6 | 0.13 | 534.0 |
| 8 | [Hy Token Plan Max](https://cloud.tencent.com/act/pro/tokenplan) | $65 | ¥436 | 1.4× | 73.5% | 6.5亿/月 | hy3 (#45) | 43.3 | 0.084 | 516.8 |
| 9 | [Hy Token Plan Pro](https://cloud.tencent.com/act/pro/tokenplan) | $33.06 | ¥222 | 1.3× | 76.0% | 3.2亿/月 | hy3 (#45) | 43.3 | 0.087 | 499.8 |
| 10 | [Hy Token Plan Standard](https://cloud.tencent.com/act/pro/tokenplan) | $10.83 | ¥73 | 1.3× | 79.0% | 1亿/月 | hy3 (#45) | 43.3 | 0.09 | 480.8 |
| 11 | [Hy Token Plan Lite](https://cloud.tencent.com/act/pro/tokenplan) | $3.9 | ¥26 | 1.2× | 81.0% | 3500万/月 | hy3 (#45) | 43.3 | 0.092 | 468.9 |
| 12 | [MiMo Token Plan Max](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $100 | ¥671 | 1.3× | 79.0% | ≈4.5亿/月 | mimo-v2.5-pro (#41) | 44.6 | 0.134 | 332.1 |
| 13 | [Claude Max 20x](https://claude.com/pricing) | $200 | ¥1342 | 40× | 2.5% | ≈9亿 | claude-fable-5.1 (#1) | 70.5 | 0.214 | 330.2 |
| 14 | [MiMo Token Plan Lite](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $6 | ¥40 | 1.1× | 94.0% | ≈2300万/月 | mimo-v2.5-pro (#41) | 44.6 | 0.16 | 279.1 |
| 15 | [ChatGPT Pro 5x](https://chatgpt.com/pricing) | $100 | ¥671 | 35× | 2.9% | ≈4亿 | gpt-6-astra (#2) | 69.6 | 0.261 | 267.0 |
| 16 | [ChatGPT Plus](https://chatgpt.com/pricing) | $20 | ¥134 | 35× | 2.9% | ≈0.8亿 | gpt-6-astra (#2) | 69.6 | 0.261 | 267.0 |
| 17 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | ¥2012 | 5.3× | 18.8% | ≈11亿 | grok-4.6 (#9) | 59.6 | 0.272 | 218.9 |
| 18 | [SuperGrok](https://x.ai/pricing) | $30 | ¥201 | 5.3× | 18.8% | ≈1亿 | grok-4.6 (#9) | 59.6 | 0.272 | 218.9 |
| 19 | [Claude Max 5x](https://claude.com/pricing) | $100 | ¥671 | 20× | 5.0% | ≈2亿 | claude-fable-5.1 (#1) | 70.5 | 0.427 | 165.1 |
| 20 | [Claude Pro](https://claude.com/pricing) | $20 | ¥134 | 20× | 5.0% | ≈0.5亿 | claude-fable-5.1 (#1) | 70.5 | 0.427 | 165.1 |
| 21 | [OpenCode Go](https://opencode.ai/go) | $10 | ¥67 | 6× | 16.7% | $60/月（$60 档模型） | kimi-k3 (#10) | 59.1 | 0.457 | 129.4 |
| 22 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | ¥185 | 4.5× | 22.0% | ≈0.5亿 | kimi-k3 (#10) | 59.1 | 0.601 | 98.3 |
| 23 | [Kimi Andante](https://www.kimi.com/membership/pricing) | $6.8 | ¥46 | 2.5× | 40.5% | 周4M uncached in/out | kimi-k3 (#10) | 59.1 | 1.107 | 53.4 |
| 24 | [Factory Droid Pro](https://factory.ai) | $20 | ¥134 | 2.4× | 41.7% | 2000万标准token | claude-fable-5.1 (#1) | 70.5 | 3.562 | 19.8 |
| 25 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | ¥671 | 2× | 50.0% | ≈0.2亿 | claude-fable-5.1 (#1) | 70.5 | 4.271 | 16.5 |
| 26 | [Trae Pro](https://www.trae.ai) | $10 | ¥67 | 2× | 50.0% | $20 基础用量 | claude-fable-5.1 (#1) | 70.5 | 4.271 | 16.5 |
| 27 | [GitHub Copilot Pro+](https://github.com/features/copilot/plans) | $39 | ¥262 | 1.8× | 55.7% | ≈8M | claude-fable-5.1 (#1) | 70.5 | 4.757 | 14.8 |
| 28 | [GitHub Copilot Pro](https://github.com/features/copilot/plans) | $10 | ¥67 | 1.5× | 66.7% | ≈2M | claude-fable-5.1 (#1) | 70.5 | 5.697 | 12.4 |
| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，不参与倍率排序）——* | | | | | | | | | |
| 29 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | ¥36 | - | - | 2,500 Credits/7天 | qwen3.8-max (#17) | 55.4 | 1.261 | 43.9 |
| 30 | [WorkBuddy 标准版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $13.8 | ¥93 | - | - | ≈1600万/月 | hy3 (#45) | 43.3 | 0.114 | 379.8 |
| 31 | [Qwen Token Plan Standard](https://platform.qianwenai.com/pricing/token-plan) | $19.3 | ¥129 | - | - | 10,000 Credits/7天 | qwen3.8-max (#17) | 55.4 | 1.261 | 43.9 |
| 32 | [Cursor Pro](https://cursor.com/pricing) | $20 | ¥134 | - | - | $20 API 用量 | claude-fable-5.1 (#1) | 70.5 | 8.541 | 8.3 |
| 33 | [WorkBuddy 高级版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $27.6 | ¥185 | - | - | ≈3700万/月 | hy3 (#45) | 43.3 | 0.114 | 379.8 |
| 34 | [Qwen Token Plan Pro](https://platform.qianwenai.com/pricing/token-plan) | $69.3 | ¥465 | - | - | 40,000 Credits/7天 | qwen3.8-max (#17) | 55.4 | 1.261 | 43.9 |
| 35 | [WorkBuddy 旗舰版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $138.8 | ¥931 | - | - | ≈2亿/月 | hy3 (#45) | 43.3 | 0.114 | 379.8 |
<!--PLANS_GUIDE_END-->

---

## 数据源

| 源 | 测什么 | 维护方 | 抗污染 |
|---|---|---|---|
| [LiveBench](https://livebench.ai) | 编码 / Agentic Coding / 指令遵循 / 语言 | Abacus.AI + 学界 | ✅ 半年刷新 |
| [DeepSWE](https://deepswe.datacurve.ai) | 长程软件工程 agent | Datacurve | ✅ 原创任务 |
| [EQ-Bench](https://eqbench.com) | 创意写作 | 独立（LLM-judge） | ⚠️ 主观维度 |
| [Artificial Analysis](https://artificialanalysis.ai) | 长上下文 / 事实性 / 知识 | 独立评测机构 | ✅ 第三方统一跑分 |
| [Frankfurter](https://frankfurter.dev) | USD→CNY 汇率（ECB 官方） | 开源 | — |

## 权重与打分

固定锚点打分：每项指标按理论范围换算到 0-100 分，再按权重加权。

- 通用榜：代码与 Agent 35%、业务自动化 15%、指令遵循与长上下文 20%、科学与推理 20%、事实准确性 10%
- 文本榜：创意文学 25%、专业案头 20%、指令约束 20%、事实与长文本 20%、人际心智 15%
- 性价比榜：与通用榜同权重同名次，展示官方 API 价与最优订阅折算价（含倍率和购买链接），Value = 综合分 ÷ 套餐内 $/1M；配套的套餐购买指南按套餐内性价比排序

[完整方法论](METHODOLOGY.md)

## FAQ

**为什么只收旗舰、不收长尾？**

几百个模型里九成是重复变体、长尾小厂和已弃用条目，真正有人用的就这几十个。榜单定位是精选，不是堆量。

**分数为什么不像别家那么高，连 90 都见不到？**

不做 min-max 名次分。DeepSWE 最好的模型也只有 74%，那就写 74，不硬抬成 100。分数是能力，不是名次。

**为什么不用 SWE-bench？**

SWE-bench Verified 已经饱和，前沿厂商陆续停止报告（OpenAI 因污染问题退出），它的榜单停在旧模型上。真实工程能力由 DeepSWE 和 LiveBench Agentic Coding 覆盖。

**汇率哪来的？**

每次构建实时抓取 Frankfurter（ECB 官方参考价），失败时回退 open.er-api.com，不硬编码。注意有两套口径：榜单 `¥/1M` 列用构建时实时汇率；国产套餐 `¥/月` 标价按固定 ÷7.2 折美元（避免历史套餐数据随汇率漂移），两者相差约 7% 属正常。

**想低价用 Claude 或 GPT 写代码，有什么路子？**

两条路：官方高倍率订阅，或国产低折池。Claude Max 20x 用满额度上限约等于 API 打 2.5 折，ChatGPT Pro 对 GPT-5.6 系约 1.4 折；GLM Coding Plan 三档折算折扣在 2.9%~4.5%，OpenCode Go 每月 $10 对部分国产模型给到 $60 月度额度。差别在用谁的模型：前者始终是榜单最前排，后者目前最强 glm-5.3 排第 7。要分数还是要单价，看预算对哪个更敏感。

**写代码选 Claude 还是 GPT？**

通用榜上 claude-fable-5.1（70.5）第一，gpt-6-astra（69.6）第二，差距不到 1 分，同一档。往下 claude-fable-5（67.1）和 claude-opus-5（65.9）占三四名，gpt-5.6-sol（63.9）第五。实际选型更多看价格：Claude Max 20x 折后约 $0.21/M，ChatGPT Pro 20x 对 GPT 系折后约 $0.13/M，差距比分数差距大。

**国产模型现在排第几？**

通用榜前十里有两个国产：glm-5.3 第 7（61.2）、kimi-k3 第 10（59.1）。glm-5.3-flash 第 16（55.5）、qwen3.8-max 第 17（55.4）紧随其后。国产的优势在订阅价：GLM Coding Plan Max 折后约 $0.039/M，是 Claude Max 的两折不到，预算有限时优先看性价比榜。

**DeepSeek 为什么没有推荐套餐？**

DeepSeek 官方只卖 API 按量计费，没有订阅制。榜单给它挂的是腾讯云 Hy Token Plan Standard 聚合池：¥78/月共享 1 亿 token，能跑 DeepSeek-V4 等多家模型，折算约 79% 折扣。这是兜底选项，不如厂商自营订阅划算。

**Kimi 的会员档位怎么选？**

四档月付：Andante ¥49、Moderato ¥99、Allegretto ¥199、Allegro ¥699，年付约合八折，都含 Kimi Code 调用。轻度使用 Andante 够用；当编程主力一般要上到 Allegretto。官方已公告新会员体系将把 Kimi 与 Kimi Code 权益拆分，购买前留意公告。

## 复现

```bash
pip install -r requirements.txt
python scripts/build.py            # 完整构建（抓取 + 合并 + 评分 + README）
python scripts/build.py --offline  # 离线复算缓存
python -m pytest -q                # 测试
```

GitHub Actions 每月 1 号自动更新。

## License

评分脚本与整理结果：MIT。原始数据版权归各基准维护方。
