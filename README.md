# AI 前沿模型排行 LLM Leaderboard：通用 / 写作 / 性价比三榜

精选 50 个主流旗舰大模型，针对三大真实需求提供三张榜单：
- **干重活与写代码（通用榜）**：看编程、智能体、复杂逻辑与长上下文能力（当前 claude-fable-5.1 第一，70.5 分）；
- **写文章与专业案头（文本榜）**：看创意写作、文风质感、长文阅读与日常问答（当前 gpt-6-astra 第一，77.7 分）；
- **算钱包与真实花销（性价比榜）**：看折算真实订阅套餐与 API 折扣后的到手单价（订阅折算后最低约 $0.005/M）。

数据来自 LiveBench 2.0、Artificial Analysis、EQ-Bench 等独立公开评测的交叉聚合，不是某一家的一家之言；价格同时标注美元与人民币，每月随上游自动更新。

## 能力-成本曲线：预算多少，买哪个模型

怎么看图：在横轴定位你的预算，红色阶梯线上对应的模型就是这个预算里最聪明的选择（前沿高度即该预算能买到的最强综合能力）。

每个点代表一个模型：横轴是实际支付价（最优订阅套餐折算后的等效价，无订阅厂商按官方按量混合价；人民币、对数刻度），纵轴是通用榜综合分。当前前沿自左向右依次是 gpt-5.4-nano、minimax-m3、glm-5.3-flash、gpt-5.6-terra、glm-5.3、gpt-5.6-sol、claude-opus-5、gpt-6-astra，终点是 claude-fable-5.1。

<!--FRONTIER_START-->
![能力-成本前沿：给定每 1M token 预算时的最优模型](results/value_frontier.svg)
<!--FRONTIER_END-->

## 这个榜单怎么做

大多数公开榜单要么只看一家的合成指数，要么把几百个长尾模型堆在一起凑数。这里的做法基于四条硬核事实：

- **只挑主力旗舰（50 个），不堆长尾**：覆盖国际主流与国内主力厂商，每家只收录当家版本，剔除重复变体与弃用条目，避免稀释参考价值。
- **多源独立交叉验证**：全面聚合 LiveBench 2.0、Artificial Analysis、EQ-Bench，用多方独立实测跑分抵消单源偏见。
- **算真实到手价（实付成本与 90% 缓存命中）**：结合各家实际订阅套餐折扣与 90% 缓存命中率折算等效单价，美元与人民币双币价由实时汇率驱动。
- **固定理论锚点打分**：按各项指标理论范围换算 0-100 分，不做「样本第一 = 100」的相对名次分。新增模型不影响已有分数，真实反映能力代差。

## 通用榜 Top 15

编程、智能体、日常混合使用看这张。权重：代码与 Agent 35%（Terminal-Bench v4.0 40%、LiveBench Long-Horizon 35%、LiveBench Coding 25%）、业务自动化与 Web 15%（tau3-Banking 40%、LiveBench Browser 35%、LiveBench Data Analysis 25%）、指令遵循与长上下文 20%（IFBench 50%、LCR 50%）、科学与推理 20%（HLE 60%、SciCode 25%、LiveBench Reasoning 15%）、事实准确性 10%（Omniscience Index 100%）。

<!--SNAPSHOT_GENERAL_START-->
> 2026-09-11 数据（60 精选模型 -> 60 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.05 (>10%: 75.0%/44) ; LiveBench Long-Horizon MAE=8.41 (>10%: 73.5%/34) ; LiveBench Coding MAE=7.63 (>10%: 29.4%/34) ; tau3-Banking MAE=0.08 (>10%: 69.4%/49) ; LiveBench Browser MAE=26.24 (>10%: 79.4%/34) ; LiveBench Data Analysis MAE=5.07 (>10%: 17.6%/34) ; IFBench MAE=0.07 (>10%: 42.3%/26) ; LCR MAE=0.02 (>10%: 5.6%/54) ; HLE MAE=0.03 (>10%: 18.5%/54) ; SciCode MAE=0.02 (>10%: 2.2%/46) ; LiveBench Reasoning MAE=2.60 (>10%: 5.9%/34) ; Omniscience Index MAE=15.39 (>10%: 96.3%/54)
<!--SNAPSHOT_GENERAL_END-->

<!--TOP15_GENERAL_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-fable-5.1 | Anthropic | 👁️ | 74.9 | IFBench(reg) |
| 2 | gpt-6-astra | OpenAI | 👁️ | 73.3 | IFBench(reg) |
| 3 | claude-opus-5 | Anthropic | 👁️ | 68.0 | IFBench(reg) |
| 4 | claude-fable-5 | Anthropic | 👁️ | 67.5 | - |
| 5 | claude-opus-5.5 | Anthropic | 👁️ | 67.0 | Terminal-Bench v4.0(reg), tau3-Banking(reg), IFBench(reg), LCR(reg), HLE(reg), SciCode(reg), Omniscience Index(reg) |
| 6 | gpt-6.1-sol | OpenAI | 👁️ | 66.2 | Terminal-Bench v4.0(reg), tau3-Banking(reg), IFBench(reg), LCR(reg), HLE(reg), SciCode(reg), Omniscience Index(reg) |
| 7 | claude-sonnet-5.5 | Anthropic | 👁️ | 65.4 | Terminal-Bench v4.0(reg), tau3-Banking(reg), IFBench(reg), LCR(reg), HLE(reg), SciCode(reg), Omniscience Index(reg) |
| 8 | gpt-6-sol | OpenAI | 👁️ | 64.6 | Terminal-Bench v4.0(reg), tau3-Banking(reg), IFBench(reg), LCR(reg), HLE(reg), SciCode(reg), Omniscience Index(reg) |
| 9 | gpt-5.6-sol | OpenAI | 👁️ | 64.1 | - |
| 10 | muse-spark-1.3 | Meta | 👁️ | 62.2 | IFBench(reg) |
| 11 | gpt-5.6-terra | OpenAI | 👁️ | 59.3 | - |
| 12 | grok-4.6 | xAI | 👁️ | 58.8 | IFBench(reg) |
| 13 | claude-opus-4.8 | Anthropic | 👁️ | 58.4 | - |
| 14 | gpt-5.5 | OpenAI | 👁️ | 56.9 | - |
| 15 | gpt-5.4 | OpenAI | 👁️ | 56.8 | Terminal-Bench v4.0(reg), LiveBench Long-Horizon(reg), LiveBench Coding(reg), LiveBench Browser(reg), LiveBench Data Analysis(reg), SciCode(reg), LiveBench Reasoning(reg) |
<!--TOP15_GENERAL_END-->

[完整排名 CSV](results/general_scored.csv)

## 文本榜 Top 15

适用于文学创作、长篇阅读、专业案头分析与日常问答。评测覆盖 5 个维度：创意文学 25%（EQ-Bench Creative Writing 60%、LiveBench Design 40%）、专业案头 25%（AA-Briefcase 40%、LiveBench Research 35%、LiveBench Data Analysis 25%）、指令约束 20%（IFBench 50%、LCR 50%）、事实与长文本 15%（Omniscience Index 60%、Omniscience Non-Halluc. 40%）、人际心智 15%（LiveBench Reasoning 60%、CritPt 40%）。不包含代码生成与数理考试指标。图表纵轴为文本榜综合分，横轴为百万 token 成本，用于按预算选型。

<!--TEXT_FRONTIER_START-->
![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型](results/text_frontier.svg)
<!--TEXT_FRONTIER_END-->

<!--SNAPSHOT_TEXT_START-->
> 2026-09-11 数据（60 精选模型 -> 60 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：EQ-Bench Creative Writing MAE=87.90 (>10%: 11.4%/35) ; LiveBench Design MAE=3.51 (>10%: 11.8%/34) ; AA-Briefcase MAE=135.82 (>10%: 40.4%/47) ; LiveBench Research MAE=8.82 (>10%: 50.0%/34) ; LiveBench Data Analysis MAE=5.07 (>10%: 17.6%/34) ; IFBench MAE=0.07 (>10%: 42.3%/26) ; LCR MAE=0.02 (>10%: 5.6%/54) ; Omniscience Index MAE=15.39 (>10%: 96.3%/54) ; Omniscience Non-Halluc. MAE=0.19 (>10%: 88.9%/54) ; LiveBench Reasoning MAE=2.60 (>10%: 5.9%/34) ; CritPt MAE=0.07 (>10%: 87.0%/54)
<!--SNAPSHOT_TEXT_END-->

<!--TOP15_TEXT_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | gpt-6-astra | OpenAI | 👁️ | 80.9 | IFBench(reg) |
| 2 | claude-fable-5.1 | Anthropic | 👁️ | 80.1 | IFBench(reg) |
| 3 | claude-opus-5 | Anthropic | 👁️ | 79.0 | IFBench(reg) |
| 4 | kimi-k3 | Moonshot AI | 👁️ | 75.2 | IFBench(reg) |
| 5 | claude-fable-5 | Anthropic | 👁️ | 74.8 | - |
| 6 | claude-opus-5.5 | Anthropic | 👁️ | 74.4 | EQ-Bench Creative Writing(reg), AA-Briefcase(reg), IFBench(reg), LCR(reg), Omniscience Index(reg), Omniscience Non-Halluc.(reg), CritPt(reg) |
| 7 | grok-4.6 | xAI | 👁️ | 74.1 | EQ-Bench Creative Writing(reg), IFBench(reg) |
| 8 | glm-5.3 | Z.AI | - | 73.5 | IFBench(reg) |
| 9 | muse-spark-1.3 | Meta | 👁️ | 72.9 | IFBench(reg) |
| 10 | gpt-6.1-sol | OpenAI | 👁️ | 72.3 | EQ-Bench Creative Writing(reg), AA-Briefcase(reg), IFBench(reg), LCR(reg), Omniscience Index(reg), Omniscience Non-Halluc.(reg), CritPt(reg) |
| 11 | gpt-5.6-sol | OpenAI | 👁️ | 69.5 | - |
| 12 | gpt-6-sol | OpenAI | 👁️ | 69.2 | EQ-Bench Creative Writing(reg), AA-Briefcase(reg), IFBench(reg), LCR(reg), Omniscience Index(reg), Omniscience Non-Halluc.(reg), CritPt(reg) |
| 13 | claude-sonnet-5.5 | Anthropic | 👁️ | 68.7 | EQ-Bench Creative Writing(reg), AA-Briefcase(reg), IFBench(reg), LCR(reg), Omniscience Index(reg), Omniscience Non-Halluc.(reg), CritPt(reg) |
| 14 | grok-4.7 | xAI | 👁️ | 68.6 | EQ-Bench Creative Writing(reg), AA-Briefcase(reg), IFBench(reg), LCR(reg), Omniscience Index(reg), Omniscience Non-Halluc.(reg), CritPt(reg) |
| 15 | claude-sonnet-5 | Anthropic | 👁️ | 68.5 | IFBench(reg) |
<!--TOP15_TEXT_END-->

[完整排名 CSV](results/text_scored.csv)

## 性价比榜 Top 15

回答「买哪个套餐最划算」。行序跟通用榜一致——按性价比排会让便宜小模型霸榜，没有决策价值。各列含义：API $/1M 是官方按量混合价（含缓存命中假设）；套餐内 $/1M 是该厂商最优订阅折算后的等效价；倍率是每 1 元月费换到的 API 等价额度，70× 即 $1 月费约换 $70 额度；Value = 综合分 ÷ 套餐内 $/1M。套餐名就是官方购买链接，没有订阅制的厂商按 API 按量计费（1×）。

<!--SNAPSHOT_VALUE_START-->
> 2026-09-11 数据（60 精选模型 -> 60 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.05 (>10%: 75.0%/44) ; LiveBench Long-Horizon MAE=8.41 (>10%: 73.5%/34) ; LiveBench Coding MAE=7.63 (>10%: 29.4%/34) ; tau3-Banking MAE=0.08 (>10%: 69.4%/49) ; LiveBench Browser MAE=26.24 (>10%: 79.4%/34) ; LiveBench Data Analysis MAE=5.07 (>10%: 17.6%/34) ; IFBench MAE=0.07 (>10%: 42.3%/26) ; LCR MAE=0.02 (>10%: 5.6%/54) ; HLE MAE=0.03 (>10%: 18.5%/54) ; SciCode MAE=0.02 (>10%: 2.2%/46) ; LiveBench Reasoning MAE=2.60 (>10%: 5.9%/34) ; Omniscience Index MAE=15.39 (>10%: 96.3%/54)
<!--SNAPSHOT_VALUE_END-->

<!--TOP15_VALUE_START-->
| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | claude-fable-5.1 | Anthropic | 👁️ | 74.9 | 8.541 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.214 | 1.435 | 349.78 |
| 2 | gpt-6-astra | OpenAI | 👁️ | 73.3 | 9.115 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.13 | 0.872 | 563.62 |
| 3 | claude-opus-5 | Anthropic | 👁️ | 68.0 | 4.558 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.114 | 0.764 | 596.8 |
| 4 | claude-fable-5 | Anthropic | 👁️ | 67.5 | 9.115 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.228 | 1.529 | 296.06 |
| 5 | claude-opus-5.5 | Anthropic | 👁️ | 67.0 |  | API 按量 | - | 1× |  |  |  |
| 6 | gpt-6.1-sol | OpenAI | 👁️ | 66.2 |  | API 按量 | - | 1× |  |  |  |
| 7 | claude-sonnet-5.5 | Anthropic | 👁️ | 65.4 |  | API 按量 | - | 1× |  |  |  |
| 8 | gpt-6-sol | OpenAI | 👁️ | 64.6 |  | API 按量 | - | 1× |  |  |  |
| 9 | gpt-5.6-sol | OpenAI | 👁️ | 64.1 | 3.646 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.052 | 0.349 | 1231.79 |
| 10 | muse-spark-1.3 | Meta | 👁️ | 62.2 | 0.858 | [OpenCode Go](https://opencode.ai/go) | $10 | 6× | 0.143 | 0.959 | 434.88 |
| 11 | gpt-5.6-terra | OpenAI | 👁️ | 59.3 | 2.123 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.03 | 0.201 | 1975.35 |
| 12 | grok-4.6 | xAI | 👁️ | 58.8 | 1.452 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | 5.3× | 0.272 | 1.824 | 216.24 |
| 13 | claude-opus-4.8 | Anthropic | 👁️ | 58.4 | 4.558 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.114 | 0.764 | 512.2 |
| 14 | gpt-5.5 | OpenAI | 👁️ | 56.9 | 5.308 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.076 | 0.51 | 748.98 |
| 15 | gpt-5.4 | OpenAI | 👁️ | 56.8 | 2.654 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.038 | 0.255 | 1493.5 |
<!--TOP15_VALUE_END-->

[完整排名 CSV](results/value_scored.csv)

Imputed 列：`-` 表示全部真实值，`指标(reg)` 是岭回归填补，`指标(reg,low)` 是低可信填补。性价比榜完整 CSV 里还有 `Blended $/1M`（无折扣混合价）和 `Plan Monthly / Multiplier / Discount / URL` 等套餐明细列。

## 套餐购买指南

按订阅维度直接对比「买哪家最值」。每个套餐取它覆盖的厂商里通用榜最强的模型，按「套餐内 Value = 最强模型分 ÷ 该套餐下等效价」从高到低排。这个排法同时反映两件事：套餐能用到多强的模型、折算后到底多便宜，不是单纯比谁额度大。

各列口径：

- 倍率 = 每 1 元月费换到的 API 等价额度；折扣 = 套餐内单价 ÷ 官方单价
- ≈Token/月：官方公布了 token 池的直接引用（MiniMax、GLM、混元、MiMo）；没公布的按「API 等价价值 ÷ 最强模型官方混合价」估算，即额度全部用于该模型时的量，实际用便宜模型能换到更多

数据来源与时点：ChatGPT / Claude 倍率来自 SemiAnalysis 2026-06 实测，Copilot 是 GitHub 官方额度，Grok 为 agentplans.fyi 2026-06 估算，Kimi/MiMo 为 2026-09 官方页面实查，国内各家与聚合/Coding Plan 类（火山方舟、Ollama Pro、Command Code、R4 Coder、OpenCode Go、Windsurf、Cursor 等）按 2026-09 官方常规长期标价（不计限时活动）核验。倍率一律按用满额度上限计算，轻度用户实际拿不到这么多。国内套餐标价为人民币，¥/月 按实时汇率折算。

积分制套餐没有倍率。千问 Token Plan、Poe 和 WorkBuddy 官方都没公布 Credits 换 token 的系数，社区两套口径相差 5 到 10 倍，给数字等于编数，所以只列官方积分额度；WorkBuddy 的 token 量按社区实测「1 积分 ≈ 4,100 token」折了个大概，仅供参考。

两个例外。Gemini 官方订阅不含 API 额度，不进表，编程需求可以由 GitHub Copilot 覆盖；DeepSeek 没有自有订阅制，由火山方舟 Coding Plan 等第三方聚合池提供折扣（详见 FAQ）。

<!--PLANS_GUIDE_START-->
| # | 套餐 | 月费 | ¥/月 | 倍率 | 折扣 | ≈Token/月 | 最强模型（通用榜） | 模型分 | 套餐内 $/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | ¥1004 | 34.4× | 2.9% | ≈29.3~58.6亿/月 | glm-5.3-flash (#21) | 55.8 | 0.003 | 17816.1 |
| 2 | [GLM Coding Plan Pro](https://bigmodel.cn/glm-coding) | $74.7 | ¥501 | 29.6× | 3.4% | ≈12.6~25.1亿/月 | glm-5.3-flash (#21) | 55.8 | 0.004 | 15196.1 |
| 3 | [GLM Coding Plan Lite](https://bigmodel.cn/glm-coding) | $16.4 | ¥110 | 22.4× | 4.5% | ≈2.1~4.2亿/月 | glm-5.3-flash (#21) | 55.8 | 0.005 | 11481.5 |
| 4 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | ¥111 | 66.3× | 1.5% | 18亿+ | minimax-m3 (#51) | 42.8 | 0.004 | 11292.6 |
| 5 | [MiniMax Ultra Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $65.1 | ¥436 | 66.3× | 1.5% | 71亿+ | minimax-m3 (#51) | 42.8 | 0.004 | 11292.6 |
| 6 | [MiniMax Plus Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $6.8 | ¥46 | 53.7× | 1.9% | 6亿+ | minimax-m3 (#51) | 42.8 | 0.005 | 9167.6 |
| 7 | [OpenCode Go](https://opencode.ai/go) | $10 | ¥67 | 6× | 16.7% | $60/月（$60 档模型） | hy3 (#55) | 41.0 | 0.019 | 2153.6 |
| 8 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | ¥651 | 10.4× | 9.6% | 周240M uncached in/out | kimi-k2.6 (#31) | 53.3 | 0.077 | 689.3 |
| 9 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | ¥1341 | 70× | 1.4% | ≈15亿 | gpt-6-astra (#2) | 73.3 | 0.13 | 562.4 |
| 10 | [Hy Token Plan Max](https://cloud.tencent.com/act/pro/tokenplan) | $65 | ¥436 | 1.4× | 73.5% | 6.5亿/月 | hy3 (#55) | 41.0 | 0.084 | 489.3 |
| 11 | [Hy Token Plan Pro](https://cloud.tencent.com/act/pro/tokenplan) | $33.06 | ¥222 | 1.3× | 76.0% | 3.2亿/月 | hy3 (#55) | 41.0 | 0.087 | 473.2 |
| 12 | [Hy Token Plan Standard](https://cloud.tencent.com/act/pro/tokenplan) | $10.83 | ¥73 | 1.3× | 79.0% | 1亿/月 | hy3 (#55) | 41.0 | 0.09 | 455.3 |
| 13 | [Hy Token Plan Lite](https://cloud.tencent.com/act/pro/tokenplan) | $3.9 | ¥26 | 1.2× | 81.0% | 3500万/月 | hy3 (#55) | 41.0 | 0.092 | 444.0 |
| 14 | [Claude Max 20x](https://claude.com/pricing) | $200 | ¥1341 | 40× | 2.5% | ≈9亿 | claude-fable-5.1 (#1) | 74.9 | 0.214 | 350.8 |
| 15 | [Kimi Moderato](https://www.kimi.com/membership/pricing) | $13.75 | ¥92 | 4.9× | 20.5% | 周16M uncached in/out | kimi-k2.6 (#31) | 53.3 | 0.164 | 324.4 |
| 16 | [MiMo Token Plan Max](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $100 | ¥670 | 1.3× | 79.0% | ≈4.5亿/月 | mimo-v2.5-pro (#52) | 42.6 | 0.134 | 317.2 |
| 17 | [MiMo Token Plan Pro](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $50 | ¥335 | 1.2× | 82.6% | ≈2.1亿/月 | mimo-v2.5-pro (#52) | 42.6 | 0.14 | 303.2 |
| 18 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | ¥185 | 4.5× | 22.0% | ≈2亿 | kimi-k2.6 (#31) | 53.3 | 0.177 | 301.7 |
| 19 | [ChatGPT Pro 5x](https://chatgpt.com/pricing) | $100 | ¥670 | 35× | 2.9% | ≈4亿 | gpt-6-astra (#2) | 73.3 | 0.261 | 281.2 |
| 20 | [ChatGPT Plus](https://chatgpt.com/pricing) | $20 | ¥134 | 35× | 2.9% | ≈0.8亿 | gpt-6-astra (#2) | 73.3 | 0.261 | 281.2 |
| 21 | [MiMo Token Plan Standard](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $16 | ¥107 | 1.1× | 91.4% | ≈6200万/月 | mimo-v2.5-pro (#52) | 42.6 | 0.155 | 274.1 |
| 22 | [MiMo Token Plan Lite](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $6 | ¥40 | 1.1× | 94.0% | ≈2300万/月 | mimo-v2.5-pro (#52) | 42.6 | 0.16 | 266.6 |
| 23 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | ¥2011 | 5.3× | 18.8% | ≈11亿 | grok-4.6 (#12) | 58.8 | 0.272 | 216.0 |
| 24 | [SuperGrok](https://x.ai/pricing) | $30 | ¥201 | 5.3× | 18.8% | ≈1亿 | grok-4.6 (#12) | 58.8 | 0.272 | 216.0 |
| 25 | [Claude Max 5x](https://claude.com/pricing) | $100 | ¥670 | 20× | 5.0% | ≈2亿 | claude-fable-5.1 (#1) | 74.9 | 0.427 | 175.4 |
| 26 | [Claude Pro](https://claude.com/pricing) | $20 | ¥134 | 20× | 5.0% | ≈0.5亿 | claude-fable-5.1 (#1) | 74.9 | 0.427 | 175.4 |
| 27 | [Kimi Andante](https://www.kimi.com/membership/pricing) | $6.8 | ¥46 | 2.5× | 40.5% | 周4M uncached in/out | kimi-k2.6 (#31) | 53.3 | 0.325 | 163.9 |
| 28 | [Factory Droid Pro](https://factory.ai) | $20 | ¥134 | 2.4× | 41.7% | 2000万标准token | claude-fable-5.1 (#1) | 74.9 | 3.562 | 21.0 |
| 29 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | ¥670 | 2× | 50.0% | ≈0.2亿 | claude-fable-5.1 (#1) | 74.9 | 4.271 | 17.5 |
| 30 | [Trae Pro](https://www.trae.ai) | $10 | ¥67 | 2× | 50.0% | $20 基础用量 | claude-fable-5.1 (#1) | 74.9 | 4.271 | 17.5 |
| 31 | [Cursor Ultra](https://cursor.com/pricing) | $200 | ¥1341 | 2× | 50.0% | $400 API 用量 | claude-fable-5.1 (#1) | 74.9 | 4.271 | 17.5 |
| 32 | [GitHub Copilot Pro+](https://github.com/features/copilot/plans) | $39 | ¥261 | 1.8× | 55.7% | ≈8M | claude-fable-5.1 (#1) | 74.9 | 4.757 | 15.7 |
| 33 | [Windsurf Pro](https://codeium.com/windsurf) | $15 | ¥101 | 1.7× | 60.0% | 500 prompt credits/月 | claude-fable-5.1 (#1) | 74.9 | 5.125 | 14.6 |
| 34 | [GitHub Copilot Pro](https://github.com/features/copilot/plans) | $10 | ¥67 | 1.5× | 66.7% | ≈2M | claude-fable-5.1 (#1) | 74.9 | 5.697 | 13.1 |
| 35 | [Cursor Pro+](https://cursor.com/pricing) | $60 | ¥402 | 1.2× | 85.7% | $70 API 用量 | claude-fable-5.1 (#1) | 74.9 | 7.32 | 10.2 |
| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，不参与倍率排序）——* | | | | | | | | | |
| 36 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | ¥36 | - | - | 2,500 Credits/7天 | qwen3.8-flash-next (#28) | 53.9 | 0.095 | 567.4 |
| 37 | [WorkBuddy 标准版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $13.8 | ¥93 | - | - | ≈1600万/月 | hy3 (#55) | 41.0 | 0.114 | 359.6 |
| 38 | [Qwen Token Plan Standard](https://platform.qianwenai.com/pricing/token-plan) | $19.3 | ¥129 | - | - | 10,000 Credits/7天 | qwen3.8-flash-next (#28) | 53.9 | 0.095 | 567.4 |
| 39 | [Poe Premium](https://poe.com) | $19.99 | ¥134 | - | - | 660,000 计算积分/月 | claude-fable-5.1 (#1) | 74.9 | 8.541 | 8.8 |
| 40 | [Cursor Pro](https://cursor.com/pricing) | $20 | ¥134 | - | - | $20 API 用量 | claude-fable-5.1 (#1) | 74.9 | 8.541 | 8.8 |
| 41 | [WorkBuddy 高级版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $27.6 | ¥185 | - | - | ≈3700万/月 | hy3 (#55) | 41.0 | 0.114 | 359.6 |
| 42 | [Qwen Token Plan Pro](https://platform.qianwenai.com/pricing/token-plan) | $69.3 | ¥465 | - | - | 40,000 Credits/7天 | qwen3.8-flash-next (#28) | 53.9 | 0.095 | 567.4 |
| 43 | [WorkBuddy 旗舰版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $138.8 | ¥931 | - | - | ≈2亿/月 | hy3 (#55) | 41.0 | 0.114 | 359.6 |
<!--PLANS_GUIDE_END-->

---

## 数据源

| 源 | 测什么 | 维护方 | 抗污染 |
|---|---|---|---|
| [LiveBench](https://livebench.ai) | 编码 / Agentic Coding / 指令遵循 / 语言 | Abacus.AI + 学界 | ✅ 半年刷新 |
| [LiveBench 2.0 Long-Horizon](https://livebench.ai) | 长程复杂工程 agent（替代已停更的 DeepSWE） | LiveBench 官方 | ✅ 实测无污染 |
| [EQ-Bench](https://eqbench.com) | 创意写作 | 独立（LLM-judge） | ⚠️ 主观维度 |
| [Artificial Analysis](https://artificialanalysis.ai) | 真实终端操作 (Terminal-Bench v4.0) / 金融业务与 Agent 工具 (tau3-Banking) / 专业案头 (Briefcase) / 超长文本与事实抗伪 | 独立评测机构 | ✅ 第三方统一跑分 |
| [Frankfurter](https://frankfurter.dev) | USD→CNY 汇率（ECB 官方） | 开源 | — |

## 权重与打分

固定锚点打分：每项指标按理论范围换算到 0-100 分，再按权重加权。

- 通用榜：代码与 Agent 35%、业务自动化 15%、指令遵循与长上下文 20%、科学与推理 20%、事实准确性 10%
- 文本榜：创意文学 25%、专业案头 25%、指令约束 20%、事实与长文本 15%、人际心智 15%
- 性价比榜：与通用榜同权重同名次，展示官方 API 价与最优订阅折算价（含倍率和购买链接），Value = 综合分 ÷ 套餐内 $/1M；配套的套餐购买指南按套餐内性价比排序

[完整方法论](METHODOLOGY.md)

## FAQ

**我是小白或普通用户，写文章、查资料该怎么选？**

直接看文本榜。目前综合表现最好的是 gpt-6-astra 与 claude-fable 系列；预算敏感或日常写材料，国产的 kimi-k3、glm-5.3 以及 gemini-flash 系列在保持高分的同时更具成本优势。

**写代码、干复杂任务选 Claude 还是 GPT？**

通用榜上 claude-fable-5.1（70.5）与 gpt-6-astra（69.6）同属第一梯队，差距小于 1 分。关键看实付花销：ChatGPT Pro 20x 搭配 GPT 系折算后约 $0.13/M，Claude Max 20x 搭配 Claude 系约 $0.21/M。如果追求极致工程执行力选 Claude，追求性价比与速度选 GPT。

**国产模型（DeepSeek、Kimi、GLM、Qwen）现在什么水平？**

通用榜前十有两个国产：glm-5.3 第 7（61.2）、kimi-k3 第 10（59.1）。国产的最大优势在官方套餐折扣：例如 GLM Coding Plan Max 折后约 $0.028/M，单价仅为国际旗舰的十分之一左右。

**套餐“倍率”是什么意思？我怎么拿到这个折扣？**

倍率是“每花 1 元月费能换到的官方 API 等价额度”。例如 ChatGPT Pro 20x 倍率 70×，等于用满额度相当于 1.4 折；GLM Coding Plan Max 倍率 34.4× 相当于 2.9 折。注意这是按用满额度上限测算，轻度偶尔使用的用户实际折扣会更低。

**为什么很多免费小模型或旧模型不在榜单里？**

几百个开源小模型或旧代模型在日常复杂任务中已被淘汰或表现断层。榜单坚持精选各家主力旗舰（50 个），帮助用户直奔有效选项，不做长尾无意义堆量。

**DeepSeek 怎么用最划算？**

DeepSeek 官方只提供 API 按量计费，没有自有订阅会员制。如果习惯用第三方 IDE 或聚合客户端，可通过聚合类 Coding Plan（如火山方舟等）获取多模型阶梯折扣；直接调用官方 API 则享有本身极低的官方混合价。

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
