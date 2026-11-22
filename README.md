# AI 前沿模型排行 LLM Leaderboard：通用 / 写作 / 性价比三榜

<!--HERO_START-->
精选 80 个主流旗舰大模型，针对三大真实需求提供三张榜单：
- **干重活与写代码（通用榜）**：看编程、智能体、复杂逻辑与长上下文能力（当前 gpt-6.2-astra 第一，84.5 分）；
- **写文章与专业案头（文本榜）**：看创意写作、文风质感、长文阅读与日常问答（当前 gpt-6.2-astra 第一，82.5 分）；
- **算钱包与真实花销（性价比榜）**：看折算真实订阅套餐与 API 折扣后的到手单价（订阅折算后最低约 $0.001/M）。
<!--HERO_END-->

数据来自 LiveBench 2.0、Artificial Analysis、EQ-Bench 等独立公开评测的交叉聚合，不是某一家的一家之言；价格同时标注美元与人民币，每月随上游自动更新。

## 能力-成本曲线：预算多少，买哪个模型

怎么看图：在横轴定位你的预算，红色阶梯线上对应的模型就是这个预算里最聪明的选择（前沿高度即该预算能买到的最强综合能力）。

每个点代表一个模型：横轴是实际支付价（最优订阅套餐折算后的等效价，无订阅厂商按官方按量混合价；人民币、对数刻度），纵轴是通用榜综合分。

<!--FRONTIER_START-->
当前前沿自左向右依次是 gpt-6-luna、minimax-m3.1-flash、gpt-6.1-terra、gpt-6.2-sol，终点是 gpt-6.2-astra。

![能力-成本前沿：给定每 1M token 预算时的最优模型](results/value_frontier.svg)
<!--FRONTIER_END-->

## 这个榜单怎么做

大多数公开榜单要么只看一家的合成指数，要么把几百个长尾模型堆在一起凑数。这里的做法基于六条硬核事实：

- **只挑主力旗舰，不堆长尾**：覆盖国际主流与国内主力厂商，每家只收录当家版本，剔除重复变体与弃用条目，避免稀释参考价值（当前池规模见顶部，由构建自动渲染）。
- **两榜独立、零共享指标**：通用榜（偏编程）与文本榜各自从 Artificial Analysis + LiveBench 的原始基准独立构建，不共享任何评分指标；不引用任何上游综合分（AA Intelligence Index / LiveBench 总榜），也不拿一张榜的结论去定义另一张。两榜排名差异来自能力维度本身，不是权重微调。
- **多源独立交叉验证**：两张榜都同时含 Artificial Analysis 与 LiveBench 2.0 的实测基准（文本榜另用 EQ-Bench 创意写作 Elo），用多方独立实测抵消单源偏见。
- **证据门槛：每个领域最多缺 1 个基准值，无例外**：领域内缺 1 个只由同域其他基准回归回测，缺 2 个就不上榜——宁可行数少，也不让「一个实测 + 一堆猜测」混进排名。
- **算真实到手价（实付成本与 90% 缓存命中）**：结合各家实际订阅套餐折扣与 90% 缓存命中率折算等效单价，美元与人民币双币价由实时汇率驱动。
- **固定理论锚点打分**：按各项指标理论范围换算 0-100 分，不做「样本第一 = 100」的相对名次分。新增模型不影响已有分数，真实反映能力代差。

## 通用榜 Top 15

编程、智能体、复杂工作流看这张，**只测工程能力链**，与文本榜零共享指标。权重：代码与终端 Agent 45%（FrontierCode 2.0 40%、LiveBench Coding 30%、Terminal-Bench v4.0 30%）、长程自主与自动化 25%（LiveBench Long-Horizon 40%、AutomationBench 35%、LiveBench Browser 25%）、科学与硬推理 30%（HLE Diamond 40%、CritPt v2 Hard 35%、LiveBench Reasoning 25%）。`Bottleneck` 列给出该行最低的域分——加权总分允许长板补偿短板，但真实 agent 任务是串联的，短板才决定能不能把活干完。

<!--SNAPSHOT_GENERAL_START-->
> 2026-11-22 数据（80 精选模型 -> 26 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：FrontierCode 2.0 MAE=0.06 (>10%: 75.0%/32) ; LiveBench Coding MAE=8.18 (>10%: 44.4%/36) ; Terminal-Bench v4.0 MAE=0.08 (>10%: 69.4%/36) ; LiveBench Long-Horizon MAE=11.39 (>10%: 80.6%/36) ; AutomationBench MAE=0.10 (>10%: 63.9%/36) ; LiveBench Browser MAE=9.90 (>10%: 52.8%/36) ; HLE Diamond MAE=0.06 (>10%: 69.4%/36) ; CritPt v2 Hard MAE=0.06 (>10%: 53.1%/32) ; LiveBench Reasoning MAE=4.00 (>10%: 8.3%/36)
<!--SNAPSHOT_GENERAL_END-->

<!--TOP15_GENERAL_START-->
| # | Model | Creator | Vision | Score | Bottleneck | Imputed |
|---|---|---|---|---|---|---|
| 1 | gpt-6.2-astra | OpenAI | 👁️ | 84.5 | 78.2 | - |
| 2 | claude-opus-5.5 | Anthropic | 👁️ | 81.4 | 75.6 | - |
| 3 | gemini-4-carbon | Google | 👁️ | 79.6 | 75.9 | - |
| 4 | claude-fable-5.2 | Anthropic | 👁️ | 77.4 | 73.3 | - |
| 5 | gpt-6.2-sol | OpenAI | 👁️ | 76.6 | 72.2 | - |
| 6 | gemini-4-neon | Google | 👁️ | 70.1 | 58.3 | - |
| 7 | gemini-4-argon | Google | 👁️ | 66.2 | 62.2 | - |
| 8 | kimi-k3.1-pro | Moonshot AI | 👁️ | 61.3 | 60.1 | - |
| 9 | qwen4-max | Alibaba | 👁️ | 60.8 | 56.6 | - |
| 10 | muse-wonder-1.0 | Meta | 👁️ | 57.8 | 55.3 | - |
| 11 | gpt-6.1-terra | OpenAI | 👁️ | 56.7 | 44.1 | - |
| 12 | claude-sonnet-5.5 | Anthropic | 👁️ | 49.9 | 40.9 | - |
| 13 | claude-haiku-5.5 | Anthropic | 👁️ | 49.5 | 48.3 | - |
| 14 | gemini-4-hydrogen | Google | 👁️ | 48.9 | 32.9 | - |
| 15 | minimax-m3.1-flash | MiniMax | 👁️ | 48.9 | 45.0 | - |
<!--TOP15_GENERAL_END-->

[完整排名 CSV](results/general_scored.csv)

## 文本榜 Top 15

适用于文学创作、长篇阅读、专业案头分析与日常问答，**只测内容生产能力链**，与通用榜零共享指标，不含代码生成与数理考试。权重：创意写作与文档表现 30%（EQ-Bench Creative Writing 65%、LiveBench Design 35%）、专业案头与深度研究 30%（AA-Briefcase 40%、LiveBench Research 35%、LiveBench Data Analysis 25%）、长上下文检索与推理 25%（MLCR 70%、LCR 30%）、事实与抗幻觉 15%（Omniscience Accuracy 55%、Omniscience Non-Halluc. 45%）。图表纵轴为文本榜综合分，横轴为百万 token 成本，用于按预算选型。

<!--TEXT_FRONTIER_START-->
![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型](results/text_frontier.svg)
<!--TEXT_FRONTIER_END-->

<!--SNAPSHOT_TEXT_START-->
> 2026-11-22 数据（80 精选模型 -> 24 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：EQ-Bench Creative Writing MAE=77.31 (>10%: 13.0%/46) ; LiveBench Design MAE=3.13 (>10%: 11.1%/36) ; AA-Briefcase MAE=141.66 (>10%: 47.2%/36) ; LiveBench Research MAE=5.85 (>10%: 22.2%/36) ; LiveBench Data Analysis MAE=6.83 (>10%: 30.6%/36) ; MLCR MAE=0.06 (>10%: 76.9%/26) ; LCR MAE=0.04 (>10%: 17.9%/28) ; Omniscience Accuracy MAE=0.13 (>10%: 81.2%/32) ; Omniscience Non-Halluc. MAE=0.21 (>10%: 78.1%/32)
<!--SNAPSHOT_TEXT_END-->

<!--TOP15_TEXT_START-->
| # | Model | Creator | Vision | Score | Bottleneck | Imputed |
|---|---|---|---|---|---|---|
| 1 | gpt-6.2-astra | OpenAI | 👁️ | 82.5 | 65.2 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 2 | kimi-k3.1-pro | Moonshot AI | 👁️ | 82.0 | 61.8 | - |
| 3 | gpt-6.2-sol | OpenAI | 👁️ | 78.3 | 61.4 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 4 | claude-opus-5.5 | Anthropic | 👁️ | 78.1 | 64.3 | - |
| 5 | claude-fable-5.2 | Anthropic | 👁️ | 77.4 | 49.8 | EQ-Bench Creative Writing(reg), MLCR(reg) |
| 6 | gemini-4-neon | Google | 👁️ | 76.5 | 61.5 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 7 | gemini-4-carbon | Google | 👁️ | 75.3 | 49.3 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 8 | qwen4-max | Alibaba | 👁️ | 72.4 | 51.0 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 9 | grok-4.7 | xAI | 👁️ | 70.6 | 53.6 | - |
| 10 | claude-sonnet-5.5 | Anthropic | 👁️ | 68.3 | 47.8 | EQ-Bench Creative Writing(reg) |
| 11 | gemini-4-hydrogen | Google | 👁️ | 66.4 | 55.4 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 12 | claude-haiku-5.5 | Anthropic | 👁️ | 64.4 | 44.2 | EQ-Bench Creative Writing(reg) |
| 13 | gemini-4-argon | Google | 👁️ | 63.8 | 47.0 | MLCR(reg) |
| 14 | mimo-v2.6-pro | Xiaomi | 👁️ | 61.4 | 41.8 | EQ-Bench Creative Writing(reg) |
| 15 | glm-5.3-flash | Z.AI | 👁️ | 59.4 | 40.3 | EQ-Bench Creative Writing(reg) |
<!--TOP15_TEXT_END-->

[完整排名 CSV](results/text_scored.csv)

## 性价比榜 Top 15

回答「买哪个套餐最划算」。行序跟通用榜一致——按性价比排会让便宜小模型霸榜，没有决策价值。各列含义：API $/1M 是官方按量混合价（含缓存命中假设）；套餐内 $/1M 是该厂商最优订阅折算后的等效价；倍率是每 1 元月费换到的 API 等价额度，70× 即 $1 月费约换 $70 额度；Value = 综合分 ÷ 套餐内 $/1M。套餐名就是官方购买链接，没有订阅制的厂商按 API 按量计费（1×）。

<!--SNAPSHOT_VALUE_START-->
> 2026-11-22 数据（80 精选模型 -> 26 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：FrontierCode 2.0 MAE=0.06 (>10%: 75.0%/32) ; LiveBench Coding MAE=8.18 (>10%: 44.4%/36) ; Terminal-Bench v4.0 MAE=0.08 (>10%: 69.4%/36) ; LiveBench Long-Horizon MAE=11.39 (>10%: 80.6%/36) ; AutomationBench MAE=0.10 (>10%: 63.9%/36) ; LiveBench Browser MAE=9.90 (>10%: 52.8%/36) ; HLE Diamond MAE=0.06 (>10%: 69.4%/36) ; CritPt v2 Hard MAE=0.06 (>10%: 53.1%/32) ; LiveBench Reasoning MAE=4.00 (>10%: 8.3%/36)
<!--SNAPSHOT_VALUE_END-->

<!--TOP15_VALUE_START-->
| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gpt-6.2-astra | OpenAI | 👁️ | 84.5 | 6.986 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.1 | 0.667 | 844.54 |
| 2 | claude-opus-5.5 | Anthropic | 👁️ | 81.4 | 3.493 | [Claude Ultra](https://claude.com/pricing) | $200 | 33× | 0.106 | 0.707 | 768.26 |
| 3 | gemini-4-carbon | Google | 👁️ | 79.6 | 3.493 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.203 | 1.354 | 392.12 |
| 4 | claude-fable-5.2 | Anthropic | 👁️ | 77.4 | 6.833 | API 按量 | - | 1× | 6.833 | 45.58 | 11.33 |
| 5 | gpt-6.2-sol | OpenAI | 👁️ | 76.6 | 1.746 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.025 | 0.167 | 3062.9 |
| 6 | gemini-4-neon | Google | 👁️ | 70.1 | 2.62 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.152 | 1.014 | 461.28 |
| 7 | gemini-4-argon | Google | 👁️ | 66.2 | 3.493 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.203 | 1.354 | 326.09 |
| 8 | kimi-k3.1-pro | Moonshot AI | 👁️ | 61.3 | 1.823 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | 10.4× | 0.176 | 1.174 | 348.5 |
| 9 | qwen4-max | Alibaba | 👁️ | 60.8 | 0.86 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | 积分 | 0.86 | 5.737 | 70.74 |
| 10 | muse-wonder-1.0 | Meta | 👁️ | 57.8 | 3.493 | API 按量 | - | 1× | 3.493 | 23.3 | 16.55 |
| 11 | gpt-6.1-terra | OpenAI | 👁️ | 56.7 | 0.873 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.012 | 0.08 | 4725.13 |
| 12 | claude-sonnet-5.5 | Anthropic | 👁️ | 49.9 | 1.746 | [Claude Ultra](https://claude.com/pricing) | $200 | 33× | 0.053 | 0.354 | 940.89 |
| 13 | claude-haiku-5.5 | Anthropic | 👁️ | 49.5 | 0.091 | API 按量 | - | 1× | 0.091 | 0.607 | 543.8 |
| 14 | gemini-4-hydrogen | Google | 👁️ | 48.9 | 1.31 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.076 | 0.507 | 643.36 |
| 15 | minimax-m3.1-flash | MiniMax | 👁️ | 48.9 | 0.114 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | 66.3× | 0.002 | 0.013 | 24456.21 |
<!--TOP15_VALUE_END-->

[完整排名 CSV](results/value_scored.csv)

Imputed 列：`-` 表示全部真实值，`指标(reg)` 是岭回归填补，`指标(reg,low)` 是低可信填补。`Bottleneck` 是最低域分，完整 CSV 另有 `Bottleneck Domain` 指出短板落在哪个域。性价比榜完整 CSV 里还有 `Blended $/1M`（无折扣混合价）和 `Plan Monthly / Multiplier / Discount / URL` 等套餐明细列。

## 套餐购买指南

按订阅维度直接对比「买哪家最值」。每个套餐取它覆盖的厂商里通用榜最强的模型，按「套餐内 Value = 最强模型分 ÷ 该套餐下等效价」从高到低排。这个排法同时反映两件事：套餐能用到多强的模型、折算后到底多便宜，不是单纯比谁额度大。

各列口径：

- 倍率 = 每 1 元月费换到的 API 等价额度；折扣 = 套餐内单价 ÷ 官方单价
- ≈Token/月：官方公布了 token 池的直接引用（MiniMax、GLM、混元、MiMo、StepFun）；没公布的按「API 等价价值 ÷ 最强模型官方混合价」估算，即额度全部用于该模型时的量，实际用便宜模型能换到更多

数据来源与时点：ChatGPT / Claude 倍率来自 SemiAnalysis 2026-06 实测——Claude 三档已按 2026-10 官方「50% 临时提额结束、改永久 +25% 基线」公告比例等比下调 implied_value（2026-11-12 重算，非新实测），ChatGPT 档位名已对齐官方现名 Pro 100 / Pro 200；MiMo、GLM、Kimi 于 2026-11-12 按官方页复核（MiMo 额度改用官方 Credits 口径）；Mistral Pro 与 StepFun Step Plan 四档为 2026-11-12 新增（前者官方直给 $25.5/月 API 额度，后者按官方 $1 ≈ 7M Credits 换算，均不取限时促销、以月付常规价为准）；Google AI 四档与 Meta Muse 两档同为 2026-11-12 新增，官方未公布 token 口径，按同价位实测下限锚定（见下文「纳入标准」一段）；Copilot 是 GitHub 官方额度；Grok 为 agentplans.fyi 2026-06 估算；国内各家与聚合/Coding Plan 类（火山方舟、Ollama Pro、Command Code、R4 Coder、OpenCode Go、Windsurf、Cursor 等）按 2026-11 官方常规长期标价（不计限时活动）核验。倍率一律按用满额度上限计算，轻度用户实际拿不到这么多。国内套餐月费按固定 ÷7.2 口径折成美元入库，展示的 ¥/月 再乘当期汇率，因此与官网页挂牌价存在约 5~8% 偏差（以官方页为准）。

积分制套餐没有倍率。千问 Token Plan、Poe 和 WorkBuddy 官方都没公布 Credits 换 token 的系数，社区两套口径相差 5 到 10 倍，给数字等于编数，所以只列官方积分额度；WorkBuddy 的 token 量按社区实测「1 积分 ≈ 4,100 token」折了个大概，仅供参考。

纳入标准是「订阅里能不能用上这个模型」，不要求套餐给 API 额度；但**额度必须有实测或官方硬口径才能折算，没有就如实标 API 按量**。

Google 这一档有社区实测：官方承认 Gemini app 额度「按 API 定价扣减」，社区用单日 45 次调用 4.83M token、对上 API 账单 $2.99、恰好消耗掉 Ultra 5x 的 5 小时额度 6%，反推出 $50/5h，周额度 = 5h × 4；据此 Pro 周 $15、Ultra 5x 周 $200、Ultra 20x 周 $800，折月得 $65 / $860 / $3,440。所以 Google 四档能算：$4.99 的 AI Plus 就能用 Gemini 4 Argon，$19.99 的 AI Pro 起能用 Gemini 4 Carbon。

Meta 反而算不了：官方公布了 Power 500M / Maximum 3B「Muse tokens/周」，但明确不解释 Muse tokens 与 API token 的换算（agent 一步任务算多少 token 官方不给），任何折算都是编数。所以 muse-wonder 仍按 API 原价计。

现在剩 7 个模型按 API 原价计费：muse-wonder、muse-spark-open、Gemma 4 31B 属没有可折算口径或为开源权重；Nemotron（NVIDIA）与 Inkling（Thinking Machines）没有面向消费者的订阅；Claude Fable 与 Haiku 被有意排除——前者不在任何 Claude 订阅内，后者是 API 专用轻量档，套几十倍杠杆会算出虚高 Value。DeepSeek 没有自有订阅制，由火山方舟 Coding Plan 等第三方聚合池提供折扣（详见 FAQ）。

<!--PLANS_GUIDE_START-->
| # | 套餐 | 月费 | ¥/月 | 倍率 | 折扣 | ≈Token/月 | 最强模型（通用榜） | 模型分 | 套餐内 $/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | ¥110 | 66.3× | 1.5% | 18亿+ | minimax-m3.1-flash (#15) | 48.9 | 0.002 | 28407.1 |
| 2 | [MiniMax Ultra Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $65.1 | ¥434 | 66.3× | 1.5% | 71亿+ | minimax-m3.1-flash (#15) | 48.9 | 0.002 | 28407.1 |
| 3 | [MiniMax Plus Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $6.8 | ¥45 | 53.7× | 1.9% | 6亿+ | minimax-m3.1-flash (#15) | 48.9 | 0.002 | 23061.7 |
| 4 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | ¥999 | 34.4× | 2.9% | ≈29.3~58.6亿/月 | glm-5.3-flash (#18) | 43.2 | 0.003 | 13420.3 |
| 5 | [GLM Coding Plan Pro](https://bigmodel.cn/glm-coding) | $74.7 | ¥498 | 29.6× | 3.4% | ≈12.6~25.1亿/月 | glm-5.3-flash (#18) | 43.2 | 0.004 | 11446.7 |
| 6 | [GLM Coding Plan Lite](https://bigmodel.cn/glm-coding) | $16.4 | ¥109 | 22.4× | 4.5% | ≈2.1~4.2亿/月 | glm-5.3-flash (#18) | 43.2 | 0.005 | 8648.6 |
| 7 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | ¥1334 | 70× | 1.4% | ≈20亿 | gpt-6.2-astra (#1) | 84.5 | 0.1 | 845.8 |
| 8 | [Claude Ultra](https://claude.com/pricing) | $200 | ¥1334 | 33× | 3.0% | ≈19亿 | claude-opus-5.5 (#2) | 81.4 | 0.106 | 769.1 |
| 9 | [Ollama Pro](https://ollama.com) | $20 | ¥133 | 3× | 33.3% | $60/月 API 用量 | deepseek-v4.1-flash (#21) | 34.5 | 0.07 | 492.9 |
| 10 | [ChatGPT Pro 100](https://chatgpt.com/pricing) | $100 | ¥667 | 35× | 2.9% | ≈5亿 | gpt-6.2-astra (#1) | 84.5 | 0.2 | 422.9 |
| 11 | [ChatGPT Plus](https://chatgpt.com/pricing) | $20 | ¥133 | 35× | 2.9% | ≈1亿 | gpt-6.2-astra (#1) | 84.5 | 0.2 | 422.9 |
| 12 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | ¥1334 | 17.2× | 5.8% | ≈10亿 | gemini-4-carbon (#3) | 79.6 | 0.203 | 392.2 |
| 13 | [Claude Max](https://claude.com/pricing) | $100 | ¥667 | 16.6× | 6.0% | ≈5亿 | claude-opus-5.5 (#2) | 81.4 | 0.21 | 387.1 |
| 14 | [Claude Pro](https://claude.com/pricing) | $20 | ¥133 | 16.5× | 6.1% | ≈0.9亿 | claude-opus-5.5 (#2) | 81.4 | 0.212 | 384.6 |
| 15 | [MiMo Token Plan Max](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $100 | ¥667 | 1.3× | 79.0% | 820亿 Credits/月 | mimo-v2.6-pro (#16) | 48.4 | 0.134 | 360.4 |
| 16 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | ¥648 | 10.4× | 9.6% | 周240M uncached in/out | kimi-k3.1-pro (#8) | 61.3 | 0.176 | 349.2 |
| 17 | [MiMo Token Plan Pro](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $50 | ¥334 | 1.2× | 82.6% | 380亿 Credits/月 | mimo-v2.6-pro (#16) | 48.4 | 0.14 | 344.5 |
| 18 | [火山方舟 Coding Plan Pro](https://www.volcengine.com) | $27.78 | ¥185 | 10× | 10.0% | 每月最高 90,000 次请求 | kimi-k3.1-pro (#8) | 61.3 | 0.182 | 336.6 |
| 19 | [火山方舟 Coding Plan Lite](https://www.volcengine.com) | $5.56 | ¥37 | 10× | 10.0% | 每月最高 18,000 次请求 | kimi-k3.1-pro (#8) | 61.3 | 0.182 | 336.3 |
| 20 | [MiMo Token Plan Standard](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $16 | ¥107 | 1.1× | 91.4% | 110亿 Credits/月 | mimo-v2.6-pro (#16) | 48.4 | 0.155 | 311.4 |
| 21 | [MiMo Token Plan Lite](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $6 | ¥40 | 1.1× | 94.0% | 41亿 Credits/月 | mimo-v2.6-pro (#16) | 48.4 | 0.16 | 302.9 |
| 22 | [Command Code GOAT](https://commandcode.ai) | $10 | ¥67 | 7× | 14.3% | $70/月 API 用量 | kimi-k3.1-pro (#8) | 61.3 | 0.261 | 235.3 |
| 23 | [R4 Coder Code Lite](https://r4.codes) | $10 | ¥67 | 6× | 16.7% | $60/月 API 用量 | kimi-k3.1-pro (#8) | 61.3 | 0.304 | 201.7 |
| 24 | [OpenCode Go](https://opencode.ai/go) | $10 | ¥67 | 6× | 16.7% | $60/月（$60 档模型） | kimi-k3.1-pro (#8) | 61.3 | 0.304 | 201.4 |
| 25 | [Google AI Ultra 5x](https://gemini.google/subscriptions/) | $99.99 | ¥667 | 8.6× | 11.6% | ≈2亿 | gemini-4-carbon (#3) | 79.6 | 0.406 | 195.9 |
| 26 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | ¥2001 | 5.3× | 18.8% | ≈11亿 | grok-4.7 (#17) | 47.2 | 0.272 | 173.4 |
| 27 | [SuperGrok](https://x.ai/pricing) | $30 | ¥200 | 5.3× | 18.8% | ≈1亿 | grok-4.7 (#17) | 47.2 | 0.272 | 173.4 |
| 28 | [Kimi Moderato](https://www.kimi.com/membership/pricing) | $13.75 | ¥92 | 4.9× | 20.5% | 周16M uncached in/out | kimi-k3.1-pro (#8) | 61.3 | 0.373 | 164.3 |
| 29 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | ¥184 | 4.5× | 22.0% | ≈0.7亿 | kimi-k3.1-pro (#8) | 61.3 | 0.401 | 152.8 |
| 30 | [Mistral Pro](https://mistral.ai/pricing) | $14.99 | ¥100 | 1.7× | 58.8% | ≈0.6亿 | mistral-large-4 (#20) | 38.3 | 0.252 | 152.2 |
| 31 | [Google AI Plus](https://gemini.google/subscriptions/) | $4.99 | ¥33 | 6.5× | 15.3% | ≈9M | gemini-4-argon (#7) | 66.2 | 0.536 | 123.5 |
| 32 | [Kimi Andante](https://www.kimi.com/membership/pricing) | $6.8 | ¥45 | 2.5× | 40.5% | 周4M uncached in/out | kimi-k3.1-pro (#8) | 61.3 | 0.738 | 83.0 |
| 33 | [Google AI Pro](https://gemini.google/subscriptions/) | $19.99 | ¥133 | 3.3× | 30.8% | ≈0.2亿 | gemini-4-carbon (#3) | 79.6 | 1.074 | 74.1 |
| 34 | [Factory Droid Pro](https://factory.ai) | $20 | ¥133 | 2.4× | 41.7% | 2000万标准token | gpt-6.2-astra (#1) | 84.5 | 2.913 | 29.0 |
| 35 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | ¥667 | 2× | 50.0% | ≈0.3亿 | gpt-6.2-astra (#1) | 84.5 | 3.493 | 24.2 |
| 36 | [Trae Pro](https://www.trae.ai) | $10 | ¥67 | 2× | 50.0% | $20 基础用量 | gpt-6.2-astra (#1) | 84.5 | 3.493 | 24.2 |
| 37 | [Cursor Ultra](https://cursor.com/pricing) | $200 | ¥1334 | 2× | 50.0% | $400 API 用量 | gpt-6.2-astra (#1) | 84.5 | 3.493 | 24.2 |
| 38 | [GitHub Copilot Pro+](https://github.com/features/copilot/plans) | $39 | ¥260 | 1.8× | 55.7% | ≈0.1亿 | gpt-6.2-astra (#1) | 84.5 | 3.891 | 21.7 |
| 39 | [Windsurf Pro](https://codeium.com/windsurf) | $15 | ¥100 | 1.7× | 60.0% | 500 prompt credits/月 | gpt-6.2-astra (#1) | 84.5 | 4.192 | 20.2 |
| 40 | [GitHub Copilot Pro](https://github.com/features/copilot/plans) | $10 | ¥67 | 1.5× | 66.7% | ≈2M | gpt-6.2-astra (#1) | 84.5 | 4.66 | 18.1 |
| 41 | [Cursor Pro+](https://cursor.com/pricing) | $60 | ¥400 | 1.2× | 85.7% | $70 API 用量 | gpt-6.2-astra (#1) | 84.5 | 5.988 | 14.1 |
| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，不参与倍率排序）——* | | | | | | | | | |
| 42 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | ¥36 | - | - | 2,500 Credits/7天 | qwen4-max (#9) | 60.8 | 0.86 | 70.7 |
| 43 | [WorkBuddy 标准版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $13.8 | ¥92 | - | - | ≈1600万/月 | kimi-k3.1-pro (#8) | 61.3 | 1.823 | 33.6 |
| 44 | [Qwen Token Plan Standard](https://platform.qianwenai.com/pricing/token-plan) | $19.3 | ¥129 | - | - | 10,000 Credits/7天 | qwen4-max (#9) | 60.8 | 0.86 | 70.7 |
| 45 | [Poe Premium](https://poe.com) | $19.99 | ¥133 | - | - | 660,000 计算积分/月 | gpt-6.2-astra (#1) | 84.5 | 6.986 | 12.1 |
| 46 | [Cursor Pro](https://cursor.com/pricing) | $20 | ¥133 | - | - | $20 API 用量 | gpt-6.2-astra (#1) | 84.5 | 6.986 | 12.1 |
| 47 | [WorkBuddy 高级版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $27.6 | ¥184 | - | - | ≈3700万/月 | kimi-k3.1-pro (#8) | 61.3 | 1.823 | 33.6 |
| 48 | [Qwen Token Plan Pro](https://platform.qianwenai.com/pricing/token-plan) | $69.3 | ¥462 | - | - | 40,000 Credits/7天 | qwen4-max (#9) | 60.8 | 0.86 | 70.7 |
| 49 | [WorkBuddy 旗舰版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $138.8 | ¥926 | - | - | ≈2亿/月 | kimi-k3.1-pro (#8) | 61.3 | 1.823 | 33.6 |
<!--PLANS_GUIDE_END-->

---

## 数据源

| 源 | 测什么 | 维护方 | 抗污染 |
|---|---|---|---|
| [LiveBench](https://livebench.ai) | 编码 / 长程工程 / 浏览器 Agent / 推理 / 数据分析 / 研究 / 设计 | Abacus.AI + 学界 | ✅ 半年刷新 |
| [LiveBench 2.0 Long-Horizon](https://livebench.ai) | 长程复杂工程 agent（替代已停更的 DeepSWE） | LiveBench 官方 | ✅ 实测无污染 |
| [EQ-Bench](https://eqbench.com) | 创意写作 | 独立（LLM-judge） | ⚠️ 主观维度 |
| [Artificial Analysis](https://artificialanalysis.ai) | 前沿代码难题 (FrontierCode 2.0) / 真实终端操作 (Terminal-Bench v4.0) / 企业业务自动化 (AutomationBench) / 博士级科学 (HLE Diamond) / 科研批判 (CritPt v2 Hard) / 专业案头 (Briefcase) / 长上下文与事实抗伪 (LCR / MLCR / Omniscience) | 独立评测机构 | ✅ 第三方统一跑分 |
| [Frankfurter](https://frankfurter.dev) | USD→CNY 汇率（ECB 官方） | 开源 | — |

## 权重与打分

固定锚点打分：每项指标按理论范围换算到 0-100 分，再按权重加权。两榜各自独立从 Artificial Analysis + LiveBench 的原始基准构建，不共享评分指标，不引用任何单一上游榜单的综合结论。

- 通用榜（偏编程，3 域）：代码与终端 Agent 45%、长程自主与自动化 25%、科学与硬推理 30%
- 文本榜（内容生产，4 域）：创意写作与文档表现 30%、专业案头与深度研究 30%、长上下文检索与推理 25%、事实与抗幻觉 15%
- 性价比榜：与通用榜同权重同名次，展示官方 API 价与最优订阅折算价（含倍率和购买链接），Value = 综合分 ÷ 套餐内 $/1M；配套的套餐购买指南按套餐内性价比排序

[完整方法论](METHODOLOGY.md)

## FAQ

**我是小白或普通用户，写文章、查资料该怎么选？**

直接看文本榜。目前综合表现最好的是 claude-fable-5.2 与 gpt-6-astra；预算敏感或日常写材料，国产的 kimi-k3.1、glm-5.3-flash 以及 gemini-flash 系列在保持高分的同时更具成本优势。

**写代码、干复杂任务选 Claude 还是 GPT？**

通用榜上 claude-fable-5.2（85.4）领先 gpt-6-astra（80.1，#4）5.3 分，是断层第一，但 fable 系列被排除在 Claude 订阅之外，只能按 API 按量 $6.83/M 计。订阅能覆盖的最强档是 claude-opus-5.5（81.4，#2）与 gpt-6-astra（80.1，#4）：Claude Ultra（$200/月）折算后约 $0.106/M，ChatGPT Pro 200（$200/月）约 $0.13/M，Claude 侧反而更便宜。头部几名的 `Bottleneck` 普遍落在「长程自主与自动化」域，说明分差主要来自长程任务耐力而不是单点跑分。要极致能力直接买 fable 的 API，日常工程执行选 Claude 订阅，要 GPT 生态选 ChatGPT。

**国产模型（DeepSeek、Kimi、GLM、Qwen）现在什么水平？**

通用榜前十只剩一个国产：kimi-k3.1-pro 第 9（61.3）；glm-5.3-flash 第 19（43.2），glm-5.3 本轮未达上榜门槛（缺值超限）。国产的最大优势仍在官方套餐折扣：GLM Coding Plan Max 折后约 $0.003/M，是国际旗舰的百分之一量级。

**套餐“倍率”是什么意思？我怎么拿到这个折扣？**

倍率是“每花 1 元月费能换到的官方 API 等价额度”。例如 ChatGPT Pro 200 倍率 70×，等于用满额度相当于 1.4 折；GLM Coding Plan Max 倍率 34.4× 相当于 2.9 折。注意这是按用满额度上限测算，轻度偶尔使用的用户实际折扣会更低。

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
