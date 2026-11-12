# AI 前沿模型排行 LLM Leaderboard：通用 / 写作 / 性价比三榜

<!--HERO_START-->
精选 75 个主流旗舰大模型，针对三大真实需求提供三张榜单：
- **干重活与写代码（通用榜）**：看编程、智能体、复杂逻辑与长上下文能力（当前 claude-fable-5.2 第一，81.1 分）；
- **写文章与专业案头（文本榜）**：看创意写作、文风质感、长文阅读与日常问答（当前 claude-fable-5.2 第一，87.5 分）；
- **算钱包与真实花销（性价比榜）**：看折算真实订阅套餐与 API 折扣后的到手单价（订阅折算后最低约 $0.001/M）。
<!--HERO_END-->

数据来自 LiveBench 2.0、Artificial Analysis、EQ-Bench 等独立公开评测的交叉聚合，不是某一家的一家之言；价格同时标注美元与人民币，每月随上游自动更新。

## 能力-成本曲线：预算多少，买哪个模型

怎么看图：在横轴定位你的预算，红色阶梯线上对应的模型就是这个预算里最聪明的选择（前沿高度即该预算能买到的最强综合能力）。

每个点代表一个模型：横轴是实际支付价（最优订阅套餐折算后的等效价，无订阅厂商按官方按量混合价；人民币、对数刻度），纵轴是通用榜综合分。

<!--FRONTIER_START-->
当前前沿自左向右依次是 gpt-6-luna、minimax-m3.1-flash、gpt-6.1-terra、gpt-6.1-sol、claude-opus-5.5、gpt-6-astra，终点是 claude-fable-5.2。

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

编程、智能体、日常混合使用看这张。权重：代码与 Agent 35%（Terminal-Bench v4.0 40%、LiveBench Long-Horizon 35%、LiveBench Coding 25%）、业务自动化与 Web 15%（AutomationBench 40%、LiveBench Browser 35%、LiveBench Data Analysis 25%）、指令遵循与长上下文 20%（LCR 55%、MLCR 45%）、终极科学与推理 20%（HLE 60%、CritPt v2 Hard 25%、LiveBench Reasoning 15%）、事实准确性 10%（Omniscience Index 100%）。

<!--SNAPSHOT_GENERAL_START-->
> 2026-11-12 数据（75 精选模型 -> 26 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.06 (>10%: 63.2%/38) ; LiveBench Long-Horizon MAE=8.32 (>10%: 71.0%/31) ; LiveBench Coding MAE=8.53 (>10%: 48.4%/31) ; AutomationBench MAE=0.11 (>10%: 73.7%/38) ; LiveBench Browser MAE=14.12 (>10%: 61.3%/31) ; LiveBench Data Analysis MAE=6.79 (>10%: 32.3%/31) ; LCR MAE=0.03 (>10%: 10.8%/37) ; MLCR MAE=0.08 (>10%: 78.8%/33) ; HLE MAE=0.04 (>10%: 36.1%/36) ; CritPt v2 Hard MAE=0.07 (>10%: 57.6%/33) ; LiveBench Reasoning MAE=3.06 (>10%: 3.2%/31) ; Omniscience Index MAE=17.50 (>10%: 97.0%/33)
<!--SNAPSHOT_GENERAL_END-->

<!--TOP15_GENERAL_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-fable-5.2 | Anthropic | 👁️ | 81.1 | - |
| 2 | gpt-6-astra | OpenAI | 👁️ | 76.6 | - |
| 3 | claude-opus-5.5 | Anthropic | 👁️ | 75.2 | - |
| 4 | gemini-4-carbon | Google | 👁️ | 74.2 | HLE(reg) |
| 5 | gpt-6.1-sol | OpenAI | 👁️ | 73.7 | - |
| 6 | claude-sonnet-5.5 | Anthropic | 👁️ | 72.3 | - |
| 7 | gpt-6.1-terra | OpenAI | 👁️ | 69.1 | - |
| 8 | gemini-4-argon | Google | 👁️ | 68.7 | - |
| 9 | kimi-k3.1-pro | Moonshot AI | 👁️ | 67.9 | - |
| 10 | muse-wonder-1.0 | Meta | 👁️ | 62.1 | - |
| 11 | claude-haiku-5.5 | Anthropic | 👁️ | 57.2 | - |
| 12 | deepseek-v4.1-flash | DeepSeek | 👁️ | 55.5 | - |
| 13 | grok-4.7 | xAI | 👁️ | 54.9 | - |
| 14 | mimo-v2.6-pro | Xiaomi | 👁️ | 52.1 | - |
| 15 | qwen3.8-max | Alibaba | 👁️ | 51.1 | - |
<!--TOP15_GENERAL_END-->

[完整排名 CSV](results/general_scored.csv)

## 文本榜 Top 15

适用于文学创作、长篇阅读、专业案头分析与日常问答。评测覆盖 5 个维度：创意文学 25%（EQ-Bench Creative Writing 60%、LiveBench Design 40%）、专业案头 25%（AA-Briefcase 40%、LiveBench Research 35%、LiveBench Data Analysis 25%）、指令约束 20%（LCR 55%、MLCR 45%）、事实与长文本 15%（Omniscience Index 60%、Omniscience Non-Halluc. 40%）、推理与科研判断 15%（LiveBench Reasoning 60%、CritPt v2 Hard 40%）。不包含代码生成与数理考试指标。图表纵轴为文本榜综合分，横轴为百万 token 成本，用于按预算选型。

<!--TEXT_FRONTIER_START-->
![文本榜能力-成本前沿：给定每 1M token 预算时的最优写作模型](results/text_frontier.svg)
<!--TEXT_FRONTIER_END-->

<!--SNAPSHOT_TEXT_START-->
> 2026-11-12 数据（75 精选模型 -> 26 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：EQ-Bench Creative Writing MAE=78.71 (>10%: 15.2%/46) ; LiveBench Design MAE=3.42 (>10%: 9.7%/31) ; AA-Briefcase MAE=136.60 (>10%: 44.7%/38) ; LiveBench Research MAE=6.42 (>10%: 22.6%/31) ; LiveBench Data Analysis MAE=6.79 (>10%: 32.3%/31) ; LCR MAE=0.03 (>10%: 10.8%/37) ; MLCR MAE=0.08 (>10%: 78.8%/33) ; Omniscience Index MAE=17.50 (>10%: 97.0%/33) ; Omniscience Non-Halluc. MAE=0.20 (>10%: 90.9%/33) ; LiveBench Reasoning MAE=3.06 (>10%: 3.2%/31) ; CritPt v2 Hard MAE=0.07 (>10%: 57.6%/33)
<!--SNAPSHOT_TEXT_END-->

<!--TOP15_TEXT_START-->
| # | Model | Creator | Vision | Score | Imputed |
|---|---|---|---|---|---|
| 1 | claude-fable-5.2 | Anthropic | 👁️ | 87.5 | EQ-Bench Creative Writing(reg) |
| 2 | gpt-6-astra | OpenAI | 👁️ | 86.0 | - |
| 3 | gemini-4-carbon | Google | 👁️ | 83.0 | EQ-Bench Creative Writing(reg) |
| 4 | kimi-k3.1-pro | Moonshot AI | 👁️ | 83.0 | - |
| 5 | claude-opus-5.5 | Anthropic | 👁️ | 82.9 | - |
| 6 | gpt-6.1-sol | OpenAI | 👁️ | 82.6 | EQ-Bench Creative Writing(reg) |
| 7 | claude-sonnet-5.5 | Anthropic | 👁️ | 82.3 | EQ-Bench Creative Writing(reg) |
| 8 | gpt-6.1-terra | OpenAI | 👁️ | 78.5 | EQ-Bench Creative Writing(reg) |
| 9 | muse-wonder-1.0 | Meta | 👁️ | 77.7 | - |
| 10 | grok-4.7 | xAI | 👁️ | 75.2 | - |
| 11 | claude-haiku-5.5 | Anthropic | 👁️ | 75.0 | EQ-Bench Creative Writing(reg) |
| 12 | gemini-4-argon | Google | 👁️ | 73.0 | - |
| 13 | qwen3.8-max | Alibaba | 👁️ | 68.9 | - |
| 14 | mistral-large-4 | Mistral | 👁️ | 67.8 | EQ-Bench Creative Writing(reg), LCR(reg) |
| 15 | step-5-preview | StepFun | 👁️ | 65.9 | EQ-Bench Creative Writing(reg) |
<!--TOP15_TEXT_END-->

[完整排名 CSV](results/text_scored.csv)

## 性价比榜 Top 15

回答「买哪个套餐最划算」。行序跟通用榜一致——按性价比排会让便宜小模型霸榜，没有决策价值。各列含义：API $/1M 是官方按量混合价（含缓存命中假设）；套餐内 $/1M 是该厂商最优订阅折算后的等效价；倍率是每 1 元月费换到的 API 等价额度，70× 即 $1 月费约换 $70 额度；Value = 综合分 ÷ 套餐内 $/1M。套餐名就是官方购买链接，没有订阅制的厂商按 API 按量计费（1×）。

<!--SNAPSHOT_VALUE_START-->
> 2026-11-12 数据（75 精选模型 -> 26 行；日期为上游抓取实际时点，stale 构建不刷新）。
> 填补验证：Terminal-Bench v4.0 MAE=0.06 (>10%: 63.2%/38) ; LiveBench Long-Horizon MAE=8.32 (>10%: 71.0%/31) ; LiveBench Coding MAE=8.53 (>10%: 48.4%/31) ; AutomationBench MAE=0.11 (>10%: 73.7%/38) ; LiveBench Browser MAE=14.12 (>10%: 61.3%/31) ; LiveBench Data Analysis MAE=6.79 (>10%: 32.3%/31) ; LCR MAE=0.03 (>10%: 10.8%/37) ; MLCR MAE=0.08 (>10%: 78.8%/33) ; HLE MAE=0.04 (>10%: 36.1%/36) ; CritPt v2 Hard MAE=0.07 (>10%: 57.6%/33) ; LiveBench Reasoning MAE=3.06 (>10%: 3.2%/31) ; Omniscience Index MAE=17.50 (>10%: 97.0%/33)
<!--SNAPSHOT_VALUE_END-->

<!--TOP15_VALUE_START-->
| # | Model | Creator | Vision | Score | API $/1M | 套餐 | 月费 | 倍率 | 套餐内 $/1M | 套餐内 ¥/1M | Value |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | claude-fable-5.2 | Anthropic | 👁️ | 81.1 | 6.833 | API 按量 | - | 1× | 6.833 | 45.544 | 11.86 |
| 2 | gpt-6-astra | OpenAI | 👁️ | 76.6 | 9.115 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.13 | 0.866 | 589.01 |
| 3 | claude-opus-5.5 | Anthropic | 👁️ | 75.2 | 3.493 | [Claude Ultra](https://claude.com/pricing) | $200 | 33× | 0.106 | 0.707 | 709.55 |
| 4 | gemini-4-carbon | Google | 👁️ | 74.2 | 3.493 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.203 | 1.353 | 365.57 |
| 5 | gpt-6.1-sol | OpenAI | 👁️ | 73.7 | 1.746 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.025 | 0.167 | 2946.61 |
| 6 | claude-sonnet-5.5 | Anthropic | 👁️ | 72.3 | 1.746 | [Claude Ultra](https://claude.com/pricing) | $200 | 33× | 0.053 | 0.353 | 1364.66 |
| 7 | gpt-6.1-terra | OpenAI | 👁️ | 69.1 | 0.873 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | 70× | 0.012 | 0.08 | 5755.16 |
| 8 | gemini-4-argon | Google | 👁️ | 68.7 | 3.493 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | 17.2× | 0.203 | 1.353 | 338.45 |
| 9 | kimi-k3.1-pro | Moonshot AI | 👁️ | 67.9 | 1.823 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | 10.4× | 0.176 | 1.173 | 385.97 |
| 10 | muse-wonder-1.0 | Meta | 👁️ | 62.1 | 3.493 | API 按量 | - | 1× | 3.493 | 23.282 | 17.77 |
| 11 | claude-haiku-5.5 | Anthropic | 👁️ | 57.2 | 0.091 | API 按量 | - | 1× | 0.091 | 0.607 | 628.13 |
| 12 | deepseek-v4.1-flash | DeepSeek | 👁️ | 55.5 | 0.21 | [火山方舟 Coding Plan Pro](https://www.volcengine.com) | $27.78 | 10× | 0.021 | 0.14 | 2640.53 |
| 13 | grok-4.7 | xAI | 👁️ | 54.9 | 1.452 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | 5.3× | 0.272 | 1.813 | 201.71 |
| 14 | mimo-v2.6-pro | Xiaomi | 👁️ | 52.1 | 0.17 | [Command Code GOAT](https://commandcode.ai) | $10 | 7× | 0.024 | 0.16 | 2168.9 |
| 15 | qwen3.8-max | Alibaba | 👁️ | 51.1 | 1.261 | [Command Code GOAT](https://commandcode.ai) | $10 | 7× | 0.18 | 1.2 | 283.78 |
<!--TOP15_VALUE_END-->

[完整排名 CSV](results/value_scored.csv)

Imputed 列：`-` 表示全部真实值，`指标(reg)` 是岭回归填补，`指标(reg,low)` 是低可信填补。性价比榜完整 CSV 里还有 `Blended $/1M`（无折扣混合价）和 `Plan Monthly / Multiplier / Discount / URL` 等套餐明细列。

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
| 1 | [MiniMax Max Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $16.5 | ¥110 | 66.3× | 1.5% | 18亿+ | minimax-m3.1-flash (#16) | 50.4 | 0.002 | 29278.5 |
| 2 | [MiniMax Ultra Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $65.1 | ¥434 | 66.3× | 1.5% | 71亿+ | minimax-m3.1-flash (#16) | 50.4 | 0.002 | 29278.5 |
| 3 | [MiniMax Plus Token Plan](https://platform.minimaxi.com/subscribe/token-plan) | $6.8 | ¥45 | 53.7× | 1.9% | 6亿+ | minimax-m3.1-flash (#16) | 50.4 | 0.002 | 23769.1 |
| 4 | [GLM Coding Plan Max](https://bigmodel.cn/glm-coding) | $149.7 | ¥998 | 34.4× | 2.9% | ≈29.3~58.6亿/月 | glm-5.3-flash (#20) | 47.6 | 0.003 | 14787.2 |
| 5 | [GLM Coding Plan Pro](https://bigmodel.cn/glm-coding) | $74.7 | ¥498 | 29.6× | 3.4% | ≈12.6~25.1亿/月 | glm-5.3-flash (#20) | 47.6 | 0.004 | 12612.6 |
| 6 | [GLM Coding Plan Lite](https://bigmodel.cn/glm-coding) | $16.4 | ¥109 | 22.4× | 4.5% | ≈2.1~4.2亿/月 | glm-5.3-flash (#20) | 47.6 | 0.005 | 9529.5 |
| 7 | [Step Plan Max](https://platform.stepfun.com/step-plan) | $97.08 | ¥647 | 58.9× | 1.7% | 40000M Credits/月 | step-5-preview (#17) | 49.5 | 0.01 | 5135.4 |
| 8 | [Step Plan Pro](https://platform.stepfun.com/step-plan) | $27.6 | ¥184 | 41.4× | 2.4% | 8000M Credits/月 | step-5-preview (#17) | 49.5 | 0.014 | 3607.5 |
| 9 | [Step Plan Plus](https://platform.stepfun.com/step-plan) | $13.75 | ¥92 | 16.6× | 6.0% | 1600M Credits/月 | step-5-preview (#17) | 49.5 | 0.034 | 1450.2 |
| 10 | [Ollama Pro](https://ollama.com) | $20 | ¥133 | 3× | 33.3% | $60/月 API 用量 | deepseek-v4.1-flash (#12) | 55.5 | 0.07 | 792.9 |
| 11 | [Step Plan Mini](https://platform.stepfun.com/step-plan) | $6.8 | ¥45 | 8.4× | 11.9% | 400M Credits/月 | step-5-preview (#17) | 49.5 | 0.067 | 733.6 |
| 12 | [Claude Ultra](https://claude.com/pricing) | $200 | ¥1333 | 33× | 3.0% | ≈19亿 | claude-opus-5.5 (#3) | 75.2 | 0.106 | 710.5 |
| 13 | [ChatGPT Pro 200](https://chatgpt.com/pricing) | $200 | ¥1333 | 70× | 1.4% | ≈15亿 | gpt-6-astra (#2) | 76.6 | 0.13 | 587.7 |
| 14 | [MiMo Token Plan Max](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $100 | ¥667 | 1.3× | 79.0% | 820亿 Credits/月 | mimo-v2.6-pro (#14) | 52.1 | 0.134 | 387.9 |
| 15 | [Kimi Allegro](https://www.kimi.com/membership/pricing) | $97.08 | ¥647 | 10.4× | 9.6% | 周240M uncached in/out | kimi-k3.1-pro (#9) | 67.9 | 0.176 | 386.8 |
| 16 | [火山方舟 Coding Plan Pro](https://www.volcengine.com) | $27.78 | ¥185 | 10× | 10.0% | 每月最高 90,000 次请求 | kimi-k3.1-pro (#9) | 67.9 | 0.182 | 372.8 |
| 17 | [火山方舟 Coding Plan Lite](https://www.volcengine.com) | $5.56 | ¥37 | 10× | 10.0% | 每月最高 18,000 次请求 | kimi-k3.1-pro (#9) | 67.9 | 0.182 | 372.5 |
| 18 | [MiMo Token Plan Pro](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $50 | ¥333 | 1.2× | 82.6% | 380亿 Credits/月 | mimo-v2.6-pro (#14) | 52.1 | 0.14 | 370.9 |
| 19 | [Google AI Ultra 20x](https://gemini.google/subscriptions/) | $199.99 | ¥1333 | 17.2× | 5.8% | ≈10亿 | gemini-4-carbon (#4) | 74.2 | 0.203 | 365.6 |
| 20 | [Claude Max](https://claude.com/pricing) | $100 | ¥667 | 16.6× | 6.0% | ≈5亿 | claude-opus-5.5 (#3) | 75.2 | 0.21 | 357.6 |
| 21 | [Claude Pro](https://claude.com/pricing) | $20 | ¥133 | 16.5× | 6.1% | ≈0.9亿 | claude-opus-5.5 (#3) | 75.2 | 0.212 | 355.3 |
| 22 | [MiMo Token Plan Standard](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $16 | ¥107 | 1.1× | 91.4% | 110亿 Credits/月 | mimo-v2.6-pro (#14) | 52.1 | 0.155 | 335.2 |
| 23 | [MiMo Token Plan Lite](https://mimo.mi.com/docs/zh-CN/price/token-plan) | $6 | ¥40 | 1.1× | 94.0% | 41亿 Credits/月 | mimo-v2.6-pro (#14) | 52.1 | 0.16 | 326.0 |
| 24 | [ChatGPT Pro 100](https://chatgpt.com/pricing) | $100 | ¥667 | 35× | 2.9% | ≈4亿 | gpt-6-astra (#2) | 76.6 | 0.261 | 293.8 |
| 25 | [ChatGPT Plus](https://chatgpt.com/pricing) | $20 | ¥133 | 35× | 2.9% | ≈0.8亿 | gpt-6-astra (#2) | 76.6 | 0.261 | 293.8 |
| 26 | [Command Code GOAT](https://commandcode.ai) | $10 | ¥67 | 7× | 14.3% | $70/月 API 用量 | kimi-k3.1-pro (#9) | 67.9 | 0.261 | 260.6 |
| 27 | [R4 Coder Code Lite](https://r4.codes) | $10 | ¥67 | 6× | 16.7% | $60/月 API 用量 | kimi-k3.1-pro (#9) | 67.9 | 0.304 | 223.4 |
| 28 | [OpenCode Go](https://opencode.ai/go) | $10 | ¥67 | 6× | 16.7% | $60/月（$60 档模型） | kimi-k3.1-pro (#9) | 67.9 | 0.304 | 223.0 |
| 29 | [SuperGrok Heavy](https://x.ai/pricing) | $300 | ¥2000 | 5.3× | 18.8% | ≈11亿 | grok-4.7 (#13) | 54.9 | 0.272 | 201.7 |
| 30 | [SuperGrok](https://x.ai/pricing) | $30 | ¥200 | 5.3× | 18.8% | ≈1亿 | grok-4.7 (#13) | 54.9 | 0.272 | 201.7 |
| 31 | [Mistral Pro](https://mistral.ai/pricing) | $14.99 | ¥100 | 1.7× | 58.8% | ≈0.6亿 | mistral-large-4 (#21) | 47.2 | 0.252 | 187.6 |
| 32 | [Google AI Ultra 5x](https://gemini.google/subscriptions/) | $99.99 | ¥666 | 8.6× | 11.6% | ≈2亿 | gemini-4-carbon (#4) | 74.2 | 0.406 | 182.7 |
| 33 | [Kimi Moderato](https://www.kimi.com/membership/pricing) | $13.75 | ¥92 | 4.9× | 20.5% | 周16M uncached in/out | kimi-k3.1-pro (#9) | 67.9 | 0.373 | 182.0 |
| 34 | [Kimi 会员 Allegretto](https://www.kimi.com/membership/pricing) | $27.6 | ¥184 | 4.5× | 22.0% | ≈0.7亿 | kimi-k3.1-pro (#9) | 67.9 | 0.401 | 169.3 |
| 35 | [Google AI Plus](https://gemini.google/subscriptions/) | $4.99 | ¥33 | 6.5× | 15.3% | ≈9M | gemini-4-argon (#8) | 68.7 | 0.536 | 128.1 |
| 36 | [Kimi Andante](https://www.kimi.com/membership/pricing) | $6.8 | ¥45 | 2.5× | 40.5% | 周4M uncached in/out | kimi-k3.1-pro (#9) | 67.9 | 0.738 | 92.0 |
| 37 | [Google AI Pro](https://gemini.google/subscriptions/) | $19.99 | ¥133 | 3.3× | 30.8% | ≈0.2亿 | gemini-4-carbon (#4) | 74.2 | 1.074 | 69.1 |
| 38 | [Factory Droid Pro](https://factory.ai) | $20 | ¥133 | 2.4× | 41.7% | 2000万标准token | gpt-6-astra (#2) | 76.6 | 3.801 | 20.2 |
| 39 | [GitHub Copilot Max](https://github.com/features/copilot/plans) | $100 | ¥667 | 2× | 50.0% | ≈0.2亿 | gpt-6-astra (#2) | 76.6 | 4.558 | 16.8 |
| 40 | [Trae Pro](https://www.trae.ai) | $10 | ¥67 | 2× | 50.0% | $20 基础用量 | gpt-6-astra (#2) | 76.6 | 4.558 | 16.8 |
| 41 | [Cursor Ultra](https://cursor.com/pricing) | $200 | ¥1333 | 2× | 50.0% | $400 API 用量 | gpt-6-astra (#2) | 76.6 | 4.558 | 16.8 |
| 42 | [GitHub Copilot Pro+](https://github.com/features/copilot/plans) | $39 | ¥260 | 1.8× | 55.7% | ≈8M | gpt-6-astra (#2) | 76.6 | 5.077 | 15.1 |
| 43 | [Windsurf Pro](https://codeium.com/windsurf) | $15 | ¥100 | 1.7× | 60.0% | 500 prompt credits/月 | gpt-6-astra (#2) | 76.6 | 5.469 | 14.0 |
| 44 | [GitHub Copilot Pro](https://github.com/features/copilot/plans) | $10 | ¥67 | 1.5× | 66.7% | ≈2M | gpt-6-astra (#2) | 76.6 | 6.08 | 12.6 |
| 45 | [Cursor Pro+](https://cursor.com/pricing) | $60 | ¥400 | 1.2× | 85.7% | $70 API 用量 | gpt-6-astra (#2) | 76.6 | 7.812 | 9.8 |
| | *—— 以下为积分/任务制套餐（官方未公布 Credits→token 换算，不参与倍率排序）——* | | | | | | | | | |
| 46 | [Qwen Token Plan Lite](https://platform.qianwenai.com/pricing/token-plan) | $5.4 | ¥36 | - | - | 2,500 Credits/7天 | qwen3.8-max (#15) | 51.1 | 1.261 | 40.5 |
| 47 | [WorkBuddy 标准版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $13.8 | ¥92 | - | - | ≈1600万/月 | kimi-k3.1-pro (#9) | 67.9 | 1.823 | 37.2 |
| 48 | [Qwen Token Plan Standard](https://platform.qianwenai.com/pricing/token-plan) | $19.3 | ¥129 | - | - | 10,000 Credits/7天 | qwen3.8-max (#15) | 51.1 | 1.261 | 40.5 |
| 49 | [Poe Premium](https://poe.com) | $19.99 | ¥133 | - | - | 660,000 计算积分/月 | gpt-6-astra (#2) | 76.6 | 9.115 | 8.4 |
| 50 | [Cursor Pro](https://cursor.com/pricing) | $20 | ¥133 | - | - | $20 API 用量 | gpt-6-astra (#2) | 76.6 | 9.115 | 8.4 |
| 51 | [WorkBuddy 高级版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $27.6 | ¥184 | - | - | ≈3700万/月 | kimi-k3.1-pro (#9) | 67.9 | 1.823 | 37.2 |
| 52 | [Qwen Token Plan Pro](https://platform.qianwenai.com/pricing/token-plan) | $69.3 | ¥462 | - | - | 40,000 Credits/7天 | qwen3.8-max (#15) | 51.1 | 1.261 | 40.5 |
| 53 | [WorkBuddy 旗舰版](https://www.workbuddy.cn/docs/workbuddy/Pricing) | $138.8 | ¥925 | - | - | ≈2亿/月 | kimi-k3.1-pro (#9) | 67.9 | 1.823 | 37.2 |
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
- 文本榜：创意文学 25%、专业案头 25%、指令约束 20%、事实与长文本 15%、推理与科研判断 15%
- 性价比榜：与通用榜同权重同名次，展示官方 API 价与最优订阅折算价（含倍率和购买链接），Value = 综合分 ÷ 套餐内 $/1M；配套的套餐购买指南按套餐内性价比排序

[完整方法论](METHODOLOGY.md)

## FAQ

**我是小白或普通用户，写文章、查资料该怎么选？**

直接看文本榜。目前综合表现最好的是 claude-fable-5.2 与 gpt-6-astra；预算敏感或日常写材料，国产的 kimi-k3.1、glm-5.3-flash 以及 gemini-flash 系列在保持高分的同时更具成本优势。

**写代码、干复杂任务选 Claude 还是 GPT？**

通用榜上 claude-fable-5.2（81.1）领先 gpt-6-astra（76.6）4.5 分，是断层第一，但 fable 系列被排除在 Claude 订阅之外，只能按 API 按量 $6.83/M 计。订阅能覆盖的最强档是 claude-opus-5.5（75.2）与 gpt-6-astra（76.6）：Claude Ultra（$200/月）折算后约 $0.106/M，ChatGPT Pro 200（$200/月）约 $0.13/M，Claude 侧反而更便宜。要极致能力直接买 fable 的 API，日常工程执行选 Claude 订阅，要 GPT 生态选 ChatGPT。

**国产模型（DeepSeek、Kimi、GLM、Qwen）现在什么水平？**

通用榜前十只剩一个国产：kimi-k3.1-pro 第 9（67.9）；glm-5.3-flash 第 20（47.6），glm-5.3 本轮未达上榜门槛（缺值超限）。国产的最大优势仍在官方套餐折扣：GLM Coding Plan Max 折后约 $0.003/M，是国际旗舰的百分之一量级。

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
