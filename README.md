# AI 前沿模型排行 LLM Leaderboard：通用 / 写作 / 性价比三榜

<!--HERO_START-->
精选 73 个主流旗舰大模型，针对三大真实需求提供三张榜单：
- **干重活与写代码（通用榜）**：看编程、智能体、复杂逻辑与长上下文能力（当前 claude-opus-5.5 第一，76.9 分）；
- **写文章与专业案头（文本榜）**：看创意写作、文风质感、长文阅读与日常问答（当前 claude-fable-5.1 第一，82.4 分）；
- **算钱包与真实花销（性价比榜）**：看折算真实订阅套餐与 API 折扣后的到手单价（订阅折算后最低约 $0.001/M）。
<!--HERO_END-->

数据来自 LiveBench 2.0、Artificial Analysis、EQ-Bench 等独立公开评测的交叉聚合，不是某一家的一家之言；价格同时标注美元与人民币，每月随上游自动更新。

## 能力-成本曲线：预算多少，买哪个模型

怎么看图：在横轴定位你的预算，红色阶梯线上对应的模型就是这个预算里最聪明的选择（前沿高度即该预算能买到的最强综合能力）。

每个点代表一个模型：横轴是实际支付价（最优订阅套餐折算后的等效价，无订阅厂商按官方按量混合价；人民币、对数刻度），纵轴是通用榜综合分。

<!--FRONTIER_START-->
当前前沿自左向右依次是 gpt-6-luna、minimax-m3.1-flash、gpt-6.1-terra、gpt-6.1-sol，终点是 claude-opus-5.5。

![能力-成本前沿：给定每 1M token 预算时的最优模型](results/value_frontier.svg)
<!--FRONTIER_END-->

## 这个榜单怎么做

大多数公开榜单要么只看一家的合成指数，要么把几百个长尾模型堆在一起凑数。这里的做法基于五条硬核事实：

- **只挑主力旗舰，不堆长尾**：覆盖国际主流与国内主力厂商，每家只收录当家版本，剔除重复变体与弃用条目，避免稀释参考价值（当前池规模见顶部，由构建自动渲染）。
- **多源独立交叉验证**：全面聚合 LiveBench 2.0、Artificial Analysis、EQ-Bench，用多方独立实测跑分抵消单源偏见。
- **证据门槛：每个领域最多缺 1 个基准值**：领域内缺 1 个用同域回归回测，缺 2 个就不上榜——宁可行数少，也不让「一个实测 + 一堆猜测」混进排名。
- **算真实到手价（实付成本与 90% 缓存命中）**：结合各家实际订阅套餐折扣与 90% 缓存命中率折算等效单价，美元与人民币双币价由实时汇率驱动。
- **固定理论锚点打分**：按各项指标理论范围换算 0-100 分，不做「样本第一 = 100」的相对名次分。新增模型不影响已有分数，真实反映能力代差。

## 通用榜 Top 15

编程、智能体、日常混合使用看这张。权重：代码与 Agent 35%（Terminal-Bench v4.0 40%、LiveBench Long-Horizon 35%、LiveBench Coding 25%）、业务自动化与 Web 15%（AutomationBench 40%、LiveBench Browser 35%、LiveBench Data Analysis 25%）、指令遵循与长上下文 20%（LCR 100%）、终极科学与推理 20%（HLE 60%、SciCode 25%、LiveBench Reasoning 15%）、事实准确性 10%（Omniscience Index 100%）。

<!--SNAPSHOT_GENERAL_START-->
> 2026-11-01 数据（73 精选模型 -> 24 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.07 (>10%: 67.6%/37) ; LiveBench Long-Horizon MAE=8.11 (>10%: 72.4%/29) ; LiveBench Coding MAE=8.34 (>10%: 44.8%/29) ; AutomationBench MAE=0.11 (>10%: 75.7%/37) ; LiveBench Browser MAE=15.53 (>10%: 72.4%/29) ; LiveBench Data Analysis MAE=6.95 (>10%: 37.9%/29) ; LCR MAE=0.03 (>10%: 8.3%/36) ; HLE MAE=0.02 (>10%: 13.9%/36) ; SciCode MAE=0.02 (>10%: 2.8%/36) ; LiveBench Reasoning MAE=2.61 (>10%: 3.4%/29) ; Omniscience Index MAE=16.44 (>10%: 87.5%/32)
<!--SNAPSHOT_GENERAL_END-->

<!--TOP15_GENERAL_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-opus-5.5 | Anthropic | 👁️ | 76.9 | - |
| 2 | claude-fable-5.1 | Anthropic | 👁️ | 75.2 | - |
| 3 | gpt-6-astra | OpenAI | 👁️ | 74.7 | - |
| 4 | gemini-4-argon | Google | 👁️ | 73.2 | - |
| 5 | gpt-6.1-sol | OpenAI | 👁️ | 72.6 | - |
| 6 | claude-sonnet-5.5 | Anthropic | 👁️ | 71.6 | - |
| 7 | gpt-6.1-terra | OpenAI | 👁️ | 69.5 | - |
| 8 | kimi-k3.1-pro | Moonshot AI | 👁️ | 68.7 | - |
| 9 | muse-wonder-1.0 | Meta | 👁️ | 65.2 | - |
| 10 | deepseek-v4.1-flash | DeepSeek | 👁️ | 59.3 | - |
| 11 | grok-4.7 | xAI | 👁️ | 58.9 | - |
| 12 | mimo-v2.6-pro | Xiaomi | 👁️ | 58.4 | - |
| 13 | claude-haiku-5.5 | Anthropic | 👁️ | 58.3 | - |
| 14 | qwen3.8-max | Alibaba | 👁️ | 55.5 | - |
| 15 | minimax-m3.1-flash | MiniMax | 👁️ | 55.2 | - |
<!--TOP15_GENERAL_END-->

[完整排名 CSV](results/general_scored.csv)

## 文本榜 Top 15

适用于文学创作、长篇阅读、专业案头分析与日常问答。评测覆盖 5 个维度：创意文学 25%（EQ-Bench Creative Writing 60%、LiveBench Design 40%）、专业案头 25%（AA-Briefcase 40%、LiveBench Research 35%、LiveBench Data Analysis 25%）、指令约束 20%（LCR 100%）、事实与长文本 15%（Omniscience Index 60%、Omniscience Non-Halluc. 40%）、人际心智 15%（LiveBench Reasoning 60%、CritPt 40%）。不包含代码生成与数理考试指标。图表纵轴为文本榜综合分，横轴为百万 token 成本，用于按预算选型。

<!--TEXT_FRONTIER_START-->
![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型](results/text_frontier.svg)
<!--TEXT_FRONTIER_END-->

<!--SNAPSHOT_TEXT_START-->
> 2026-11-01 数据（73 精选模型 -> 24 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：EQ-Bench Creative Writing MAE=80.93 (>10%: 15.2%/46) ; LiveBench Design MAE=3.48 (>10%: 10.3%/29) ; AA-Briefcase MAE=130.28 (>10%: 40.5%/37) ; LiveBench Research MAE=6.31 (>10%: 24.1%/29) ; LiveBench Data Analysis MAE=6.95 (>10%: 37.9%/29) ; LCR MAE=0.03 (>10%: 8.3%/36) ; Omniscience Index MAE=16.44 (>10%: 87.5%/32) ; Omniscience Non-Halluc. MAE=0.20 (>10%: 90.6%/32) ; LiveBench Reasoning MAE=2.61 (>10%: 3.4%/29) ; CritPt MAE=0.08 (>10%: 78.4%/37)
<!--SNAPSHOT_TEXT_END-->

<!--TOP15_TEXT_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-fable-5.1 | Anthropic | 👁️ | 82.4 | - |
| 2 | gpt-6-astra | OpenAI | 👁️ | 82.4 | - |
| 3 | claude-opus-5.5 | Anthropic | 👁️ | 82.3 | - |
| 4 | kimi-k3.1-pro | Moonshot AI | 👁️ | 81.7 | - |
| 5 | gpt-6.1-sol | OpenAI | 👁️ | 80.0 | EQ-Bench Creative Writing(reg) |
| 6 | claude-sonnet-5.5 | Anthropic | 👁️ | 79.7 | EQ-Bench Creative Writing(reg) |
| 7 | muse-wonder-1.0 | Meta | 👁️ | 78.9 | - |
| 8 | gpt-6.1-terra | OpenAI | 👁️ | 77.1 | EQ-Bench Creative Writing(reg) |
| 9 | grok-4.7 | xAI | 👁️ | 77.1 | - |
| 10 | gemini-4-argon | Google | 👁️ | 75.4 | - |
| 11 | claude-haiku-5.5 | Anthropic | 👁️ | 74.2 | EQ-Bench Creative Writing(reg) |
| 12 | qwen3.8-max | Alibaba | 👁️ | 71.4 | - |
| 13 | mimo-v2.6-pro | Xiaomi | 👁️ | 69.7 | EQ-Bench Creative Writing(reg) |
| 14 | step-5-preview | StepFun | 👁️ | 69.4 | EQ-Bench Creative Writing(reg) |
| 15 | glm-5.3-flash | Z.AI | 👁️ | 67.8 | EQ-Bench Creative Writing(reg) |
<!--TOP15_TEXT_END-->

[完整排名 CSV](results/text_scored.csv)

## 性价比榜 Top 15

回答「买哪个套餐最划算」。行序跟通用榜一致——按性价比排会让便宜小模型霸榜，没有决策价值。各列含义：API $/1M 是官方按量混合价（含缓存命中假设）；套餐内 $/1M 是该厂商最优订阅折算后的等效价；倍率是每 1 元月费换到的 API 等价额度，70× 即 $1 月费约换 $70 额度；Value = 综合分 ÷ 套餐内 $/1M。套餐名就是官方购买链接，没有订阅制的厂商按 API 按量计费（1×）。

<!--SNAPSHOT_VALUE_START-->
> 2026-11-01 数据（73 精选模型 -> 24 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.07 (>10%: 67.6%/37) ; LiveBench Long-Horizon MAE=8.11 (>10%: 72.4%/29) ; LiveBench Coding MAE=8.34 (>10%: 44.8%/29) ; AutomationBench MAE=0.11 (>10%: 75.7%/37) ; LiveBench Browser MAE=15.53 (>10%: 72.4%/29) ; LiveBench Data Analysis MAE=6.95 (>10%: 37.9%/29) ; LCR MAE=0.03 (>10%: 8.3%/36) ; HLE MAE=0.02 (>10%: 13.9%/36) ; SciCode MAE=0.02 (>10%: 2.8%/36) ; LiveBench Reasoning MAE=2.61 (>10%: 3.4%/29) ; Omniscience Index MAE=16.44 (>10%: 87.5%/32)
<!--SNAPSHOT_VALUE_END-->

<!--TOP15_VALUE_START-->
| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | claude-opus-5.5 | Anthropic | 👁️ | 76.9 | 3.493 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.087 | 0.579 | 884.22 |
| 2 | claude-fable-5.1 | Anthropic | 👁️ | 75.2 | 8.541 | API 按量 | - | 1× | 8.541 | 56.856 | 8.8 |
| 3 | gpt-6-astra | OpenAI | 👁️ | 74.7 | 9.115 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.13 | 0.865 | 574.99 |
| 4 | gemini-4-argon | Google | 👁️ | 73.2 | 3.493 | API 按量 | - | 1× | 3.493 | 23.252 | 20.95 |
| 5 | gpt-6.1-sol | OpenAI | 👁️ | 72.6 | 1.746 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.025 | 0.166 | 2903.99 |
| 6 | claude-sonnet-5.5 | Anthropic | 👁️ | 71.6 | 1.746 | [Claude Max 20x](https://claude.com/pricing) | $200 | 40× | 0.044 | 0.293 | 1627.93 |
| 7 | gpt-6.1-terra | OpenAI | 👁️ | 69.5 | 0.873 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | 70× | 0.012 | 0.08 | 5792.21 |
| 8 | kimi-k3.1-pro | Moonshot AI | 👁️ | 68.7 | 1.823 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | 10.4× | 0.176 | 1.172 | 390.6 |
| 9 | muse-wonder-1.0 | Meta | 👁️ | 65.2 | 3.493 | API 按量 | - | 1× | 3.493 | 23.252 | 18.66 |
| 10 | deepseek-v4.1-flash | DeepSeek | 👁️ | 59.3 | 0.21 | [火山方舟 Coding Plan Pro](https://www.volcengine.com) | $27.78 | 10× | 0.021 | 0.14 | 2824.94 |
| 11 | grok-4.7 | xAI | 👁️ | 58.9 | 1.452 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | 5.3× | 0.272 | 1.811 | 216.7 |
| 12 | mimo-v2.6-pro | Xiaomi | 👁️ | 58.4 | 0.17 | [Command Code GOAT](https://commandcode.ai) | $10 | 7× | 0.024 | 0.16 | 2435.11 |
| 13 | claude-haiku-5.5 | Anthropic | 👁️ | 58.3 | 0.091 | API 按量 | - | 1× | 0.091 | 0.606 | 640.99 |
| 14 | qwen3.8-max | Alibaba | 👁️ | 55.5 | 1.261 | [Command Code GOAT](https://commandcode.ai) | $10 | 7× | 0.18 | 1.198 | 308.18 |
| 15 | minimax-m3.1-flash | MiniMax | 👁️ | 55.2 | 0.114 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | 66.3× | 0.002 | 0.013 | 27619.05 |
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

两个例外。Gemini 官方订阅不含 API 额度，不进表，部分编程模型（如 Gemini Flash / Pro）由 GitHub Copilot 与 Cursor 白名单精准覆盖（Gemini 4 Argon 等未入选模型按 API 原价计费）；DeepSeek 没有自有订阅制，由火山方舟 Coding Plan 等第三方聚合池提供折扣（详见 FAQ）。

<!--PLANS_GUIDE_START-->
| # | 套餐 | 月费 | ¥/月 | 倍率 | 折扣 | ≈Token/月 | 最强模型（通用榜） | 模型分 | 套餐内 $/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | ¥110 | 66.3× | 1.5% | 18亿+ | minimax-m3.1-flash (#15) | 55.2 | 0.002 | 32066.9 |
| 2 | [MiniMax Ultra Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $65.1 | ¥433 | 66.3× | 1.5% | 71亿+ | minimax-m3.1-flash (#15) | 55.2 | 0.002 | 32066.9 |
| 3 | [MiniMax Plus Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $6.8 | ¥45 | 53.7× | 1.9% | 6亿+ | minimax-m3.1-flash (#15) | 55.2 | 0.002 | 26032.8 |
| 4 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | ¥997 | 34.4× | 2.9% | ≈29.3~58.6亿/月 | glm-5.3-flash (#17) | 53.7 | 0.003 | 16682.2 |
| 5 | [GLM Coding Plan Pro](https://bigmodel.cn/glm-coding) | $74.7 | ¥497 | 29.6× | 3.4% | ≈12.6~25.1亿/月 | glm-5.3-flash (#17) | 53.7 | 0.004 | 14228.9 |
| 6 | [GLM Coding Plan Lite](https://bigmodel.cn/glm-coding) | $16.4 | ¥109 | 22.4× | 4.5% | ≈2.1~4.2亿/月 | glm-5.3-flash (#17) | 53.7 | 0.005 | 10750.8 |
| 7 | [Claude Max 20x](https://claude.com/pricing) | $200 | ¥1331 | 40× | 2.5% | ≈23亿 | claude-opus-5.5 (#1) | 76.9 | 0.087 | 880.6 |
| 8 | [Ollama Pro](https://ollama.com) | $20 | ¥133 | 3× | 33.3% | $60/月 API 用量 | deepseek-v4.1-flash (#10) | 59.3 | 0.07 | 847.2 |
| 9 | [ChatGPT Pro 20x](https://chatgpt.com/pricing) | $200 | ¥1331 | 70× | 1.4% | ≈15亿 | gpt-6-astra (#3) | 74.7 | 0.13 | 573.1 |
| 10 | [Claude Max 5x](https://claude.com/pricing) | $100 | ¥666 | 20× | 5.0% | ≈6亿 | claude-opus-5.5 (#1) | 76.9 | 0.175 | 440.3 |
| 11 | [Claude Pro](https://claude.com/pricing) | $20 | ¥133 | 20× | 5.0% | ≈1亿 | claude-opus-5.5 (#1) | 76.9 | 0.175 | 440.3 |
| 12 | [MiMo Token Plan Max](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $100 | ¥666 | 1.3× | 79.0% | ≈4.5亿/月 | mimo-v2.6-pro (#12) | 58.4 | 0.134 | 434.8 |
| 13 | [MiMo Token Plan Pro](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $50 | ¥333 | 1.2× | 82.6% | ≈2.1亿/月 | mimo-v2.6-pro (#12) | 58.4 | 0.14 | 415.7 |
| 14 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | ¥646 | 10.4× | 9.6% | 周240M uncached in/out | kimi-k3.1-pro (#8) | 68.7 | 0.176 | 391.3 |
| 15 | [火山方舟 Coding Plan Pro](https://www.volcengine.com) | $27.78 | ¥185 | 10× | 10.0% | 每月最高 90,000 次请求 | kimi-k3.1-pro (#8) | 68.7 | 0.182 | 377.2 |
| 16 | [火山方舟 Coding Plan Lite](https://www.volcengine.com) | $5.56 | ¥37 | 10× | 10.0% | 每月最高 18,000 次请求 | kimi-k3.1-pro (#8) | 68.7 | 0.182 | 376.9 |
| 17 | [MiMo Token Plan Standard](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $16 | ¥107 | 1.1× | 91.4% | ≈6200万/月 | mimo-v2.6-pro (#12) | 58.4 | 0.155 | 375.7 |
| 18 | [MiMo Token Plan Lite](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $6 | ¥40 | 1.1× | 94.0% | ≈2300万/月 | mimo-v2.6-pro (#12) | 58.4 | 0.16 | 365.5 |
| 19 | [ChatGPT Pro 5x](https://chatgpt.com/pricing) | $100 | ¥666 | 35× | 2.9% | ≈4亿 | gpt-6-astra (#3) | 74.7 | 0.261 | 286.5 |
| 20 | [ChatGPT Plus](https://chatgpt.com/pricing) | $20 | ¥133 | 35× | 2.9% | ≈0.8亿 | gpt-6-astra (#3) | 74.7 | 0.261 | 286.5 |
| 21 | [Command Code GOAT](https://commandcode.ai) | $10 | ¥67 | 7× | 14.3% | $70/月 API 用量 | kimi-k3.1-pro (#8) | 68.7 | 0.261 | 263.7 |
| 22 | [R4 Coder Code Lite](https://r4.codes) | $10 | ¥67 | 6× | 16.7% | $60/月 API 用量 | kimi-k3.1-pro (#8) | 68.7 | 0.304 | 226.1 |
| 23 | [OpenCode Go](https://opencode.ai/go) | $10 | ¥67 | 6× | 16.7% | $60/月（$60 档模型） | kimi-k3.1-pro (#8) | 68.7 | 0.304 | 225.7 |
| 24 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | ¥1997 | 5.3× | 18.8% | ≈11亿 | grok-4.7 (#11) | 58.9 | 0.272 | 216.3 |
| 25 | [SuperGrok](https://x.ai/pricing) | $30 | ¥200 | 5.3× | 18.8% | ≈1亿 | grok-4.7 (#11) | 58.9 | 0.272 | 216.3 |
| 26 | [Kimi Moderato](https://www.kimi.com/membership/pricing) | $13.75 | ¥92 | 4.9× | 20.5% | 周16M uncached in/out | kimi-k3.1-pro (#8) | 68.7 | 0.373 | 184.2 |
| 27 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | ¥184 | 4.5× | 22.0% | ≈0.7亿 | kimi-k3.1-pro (#8) | 68.7 | 0.401 | 171.3 |
| 28 | [Kimi Andante](https://www.kimi.com/membership/pricing) | $6.8 | ¥45 | 2.5× | 40.5% | 周4M uncached in/out | kimi-k3.1-pro (#8) | 68.7 | 0.738 | 93.0 |
| 29 | [Factory Droid Pro](https://factory.ai) | $20 | ¥133 | 2.4× | 41.7% | 2000万标准token | claude-opus-5.5 (#1) | 76.9 | 1.457 | 52.8 |
| 30 | [Cursor Ultra](https://cursor.com/pricing) | $200 | ¥1331 | 2× | 50.0% | $400 API 用量 | claude-opus-5.5 (#1) | 76.9 | 1.746 | 44.0 |
| 31 | [Cursor Pro+](https://cursor.com/pricing) | $60 | ¥399 | 1.2× | 85.7% | $70 API 用量 | claude-opus-5.5 (#1) | 76.9 | 2.994 | 25.7 |
| 32 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | ¥666 | 2× | 50.0% | ≈0.2亿 | gpt-6-astra (#3) | 74.7 | 4.558 | 16.4 |
| 33 | [Trae Pro](https://www.trae.ai) | $10 | ¥67 | 2× | 50.0% | $20 基础用量 | gpt-6-astra (#3) | 74.7 | 4.558 | 16.4 |
| 34 | [GitHub Copilot Pro+](https://github.com/features/copilot/plans) | $39 | ¥260 | 1.8× | 55.7% | ≈8M | gpt-6-astra (#3) | 74.7 | 5.077 | 14.7 |
| 35 | [Windsurf Pro](https://codeium.com/windsurf) | $15 | ¥100 | 1.7× | 60.0% | 500 prompt credits/月 | gpt-6-astra (#3) | 74.7 | 5.469 | 13.7 |
| 36 | [GitHub Copilot Pro](https://github.com/features/copilot/plans) | $10 | ¥67 | 1.5× | 66.7% | ≈2M | gpt-6-astra (#3) | 74.7 | 6.08 | 12.3 |
| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，不参与倍率排序）——* | | | | | | | | | |
| 37 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | ¥36 | - | - | 2,500 Credits/7天 | qwen3.8-max (#14) | 55.5 | 1.261 | 44.0 |
| 38 | [WorkBuddy 标准版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $13.8 | ¥92 | - | - | ≈1600万/月 | kimi-k3.1-pro (#8) | 68.7 | 1.823 | 37.7 |
| 39 | [Qwen Token Plan Standard](https://platform.qianwenai.com/pricing/token-plan) | $19.3 | ¥128 | - | - | 10,000 Credits/7天 | qwen3.8-max (#14) | 55.5 | 1.261 | 44.0 |
| 40 | [Poe Premium](https://poe.com) | $19.99 | ¥133 | - | - | 660,000 计算积分/月 | claude-opus-5.5 (#1) | 76.9 | 3.493 | 22.0 |
| 41 | [Cursor Pro](https://cursor.com/pricing) | $20 | ¥133 | - | - | $20 API 用量 | claude-opus-5.5 (#1) | 76.9 | 3.493 | 22.0 |
| 42 | [WorkBuddy 高级版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $27.6 | ¥184 | - | - | ≈3700万/月 | kimi-k3.1-pro (#8) | 68.7 | 1.823 | 37.7 |
| 43 | [Qwen Token Plan Pro](https://platform.qianwenai.com/pricing/token-plan) | $69.3 | ¥461 | - | - | 40,000 Credits/7天 | qwen3.8-max (#14) | 55.5 | 1.261 | 44.0 |
| 44 | [WorkBuddy 旗舰版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $138.8 | ¥924 | - | - | ≈2亿/月 | kimi-k3.1-pro (#8) | 68.7 | 1.823 | 37.7 |
<!--PLANS_GUIDE_END-->

---

## 数据源

| 源 | 测什么 | 维护方 | 抗污染 |
|---|---|---|---|
| [LiveBench](https://livebench.ai) | 编码 / 长程工程 / 浏览器 Agent / 推理 / 数据分析 / 研究 / 设计 | Abacus.AI + 学界 | ✅ 半年刷新 |
| [LiveBench 2.0 Long-Horizon](https://livebench.ai) | 长程复杂工程 agent（替代已停更的 DeepSWE） | LiveBench 官方 | ✅ 实测无污染 |
| [EQ-Bench](https://eqbench.com) | 创意写作 | 独立（LLM-judge） | ⚠️ 主观维度 |
| [Artificial Analysis](https://artificialanalysis.ai) | 真实终端操作 (Terminal-Bench v4.0) / 企业业务自动化 (AutomationBench) / 专业案头 (Briefcase) / 超长文本与事实抗伪 | 独立评测机构 | ✅ 第三方统一跑分 |
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

几百个开源小模型或旧代模型在日常复杂任务中已被淘汰或表现断层。榜单坚持精选各家主力旗舰，帮助用户直奔有效选项，不做长尾无意义堆量。

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
