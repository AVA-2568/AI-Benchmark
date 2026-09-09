# 评分方法论

> 本文档是 [README](README.md) 中评分方法的完整展开，包含权重推导、数据源与模型池、归一化细节、特征标准化、缺失值填补算法、留一验证和 R² 拟合质量。

## 数据源与模型池

### 模型池：主流旗舰精选

榜单只收录**国际 + 国内主流厂商旗舰**模型（当前 50 个，随新模型自动入池增长），而非全量长尾。模型池定义在 [`scripts/model_registry.json`](scripts/model_registry.json)：

- **国际**：OpenAI（GPT-6/5.6/5.5/5.4/5.2）、Anthropic（Claude Fable 5 / Opus 5 / Opus 4.x / Sonnet）、Google（Gemini 3.x）、xAI（Grok 4.x/Build）、Meta（Muse Spark）、Thinking Machines（Inkling）
- **国内**：DeepSeek（V4）、Kimi（K3/K2.6/K2.7）、Qwen（3.8/3.7/3.6）、GLM（5.3/5.2）、MiniMax（M3）、Xiaomi（MiMo）、Tencent（Hy）

**为什么是精选而非全量**：AA 的 1000+ 模型里 90% 是重复变体（同一模型不同推理档）、长尾小厂、已弃用条目。精选池让覆盖率更高（核心指标覆盖 28–50/50，其中 LCR/HLE/Omniscience 全覆盖，DeepSWE 28/50 最低）、填补更少、分数更「实」。

### 数据源（6 个，全部公开可抓）

| 源 | 提供指标 | 维护方 | 抓取方式 |
|---|---|---|---|
| LiveBench | Coding / Agentic Coding / Instruction Following / Language | Abacus.AI + 学界 | `table_<release>.csv` + `categories_<release>.json` |
| DeepSWE | Pass@1（长程工程 agent） | Datacurve | `/artifacts/v1.1/leaderboard-live.json`（JSON API，每模型取最高 pass_rate 档） |
| EQ-Bench | Creative Writing Elo | 独立 | `creative_writing.js` 内嵌 CSV |
| Artificial Analysis (Intelligence Index v4.3) | Terminal-Bench v4.0 / AA-Briefcase / tau3-Banking / LCR / Omniscience Index / HLE / CritPt / SciCode | 独立评测机构 | RSC 流（三级解析链） |
| Frankfurter | USD→CNY 汇率（ECB 官方） | 开源 | v2 rates API（备源 open.er-api.com） |

### 人民币价格

性价比榜同时输出美元与人民币价格：`Total ¥/1M` / `Effective ¥/1M` = 对应美元价 × 实时 USD→CNY 汇率。汇率每次构建实时抓取（Frankfurter 主、open.er-api 备），写入 `scripts/.cache/fx.json`，不硬编码。

### 缓存命中率假设

混合价按 90% 缓存命中率折算（`config.json` 的 `provider_cache_rates` 全厂商统一 0.9）：输入部分按 10% 未命中价 + 90% 缓存命中价混合，再按输入/输出占比（0.85/0.15）加权。AA 不公布分模型命中率，命中率取决于用户提示词复用程度；90% 取编程场景高复用假设（GLM 官方额度参考即按 95% 档标定），属偏乐观口径。`Total $/1M` 标准价列沿用全局中性假设（`cache_hit_rate` 0.5），与 `Effective` 列口径分离。

### 订阅套餐与倍率

官方订阅套餐定义在 `config.json` 的 `plans` 表（每条含 `creator_match` / `monthly` / `implied_value` 或 `credit_value` / `discount` / `url`）。两种价值基准：

- **`credit_value`**：官方随附的 API 额度（如 GitHub Copilot——月费直接买到等额 API 美元）
- **`implied_value`**：社区实测的订阅额度上限 API 等价（如 SemiAnalysis 2026-06 对 ChatGPT/Claude 各档跑满上限的实测）

三个派生量：

- **折扣 `discount` = monthly ÷ value**：乘在无折扣混合价上得到套餐内等效价
- **倍率 `multiplier` = value ÷ monthly**：每 1 元月费换到的 API 等价额度（如 ChatGPT Pro 20x = 70×）。从 value/monthly 直接计算而非 1/discount，避免 3 位小数折扣反算的舍入误差（0.014 → 71×，实际 70×）
- **`Blended $/1M`**：无折扣的 per-creator 缓存混合价（`Effective $/1M` = Blended × discount 的基准），用于在任意套餐下重算等效价

**≈Token/月（套餐购买指南列）**：优先用官方公布的 token 池（`plans[].tokens`，如 MiniMax 6 亿/18 亿/71 亿）；其余按 `API 等价价值 ÷ 最强模型官方混合价（Blended $/1M）` 折算——即把额度全部用于该最强模型时的 token 量级，实际使用便宜模型可换到更多。

**三类套餐**（`plans` 表）：

1. **implied_value 型**：订阅额度上限的 API 等价（SemiAnalysis 实测 ChatGPT/Claude 等）
2. **token 池型**：官方公布月 token 额度 × 榜单该厂商最强模型混合价折成 implied_value（MiniMax / GLM / 混元 / MiMo，折算口径随构建快照人工更新）。GLM 直接采用官方「可用额度参考」周 token 区间（GLM-5.3、95% 缓存命中率档；区间下限=全高峰 1×抵扣、上限=全非高峰 0.5×抵扣），×52/12 折月后再乘混合价
3. **Credit/积分计量型**：千问 Token Plan、WorkBuddy 官方未公布可靠的 Credits→token 系数，使用 `discount = 1.0` 且无 `implied_value`，不折算 API 等价倍率；`_plan_for` 跳过这类套餐的成本折算，它们只出现在套餐购买指南。腾讯云需区分两条产品线：Hy Token Plan 仅含 Hy3，按 token 池折算；通用 Token Plan 的存量模型在同一档位内统一系数，新上架模型才可能按模型区分。OpenCode Go 虽称 Credits/额度制，但官方直接按模型分为 $60/$30/$15 三档，分别对应 6×/3×/1.5×；config 以 $60 档折扣为基准，通过 `model_cost_scale` 对 $30 档乘 2、$15 档乘 4。token 量尽量给估算：WorkBuddy 按官方实得积分 × 社区实测（1 积分 ≈ 4,100 token）；千问仅列官方积分额。

国内套餐人民币月费按固定口径 ÷7.2 折算为 USD（与构建时汇率独立，避免历史数据漂移）。

**倍率按用满额度上限估算**——轻量用户实际折扣更少；无订阅套餐的厂商（DeepSeek / Qwen / GLM 等）按 API 按量计费（倍率 1×）。`url` 为官方购买直链（展示用，构建不请求）。

**分模型成本修正 `model_cost_scale`**：积分/Credits 制套餐对不同模型的抵扣密度可能不同——套餐折扣以旗舰锚点折出，对积分系数不同的衍生模型会系统性偏差。典型案例：智谱 GLM Coding Plan 的积分以 GLM-5.3 标准版标定（In 690/Cached 170/Out 2400 积分每 M token），而 glm-5.3-flash 的积分系数恰为标准版 1/3（230/56/800），但 flash 的 API 牌价约为标准版 1/9~1/10，导致直接沿用标准版折扣时 flash 的 effective 价格系统性虚低约 3 倍。config 在 plan 上以 `model_cost_scale` 给出经官方积分系数核实的乘数（如 `{"glm-5.3-flash": 3.0}`）。**乘数在套餐选择之前应用**：`_plan_for` 按修正后的实付折扣比较、选出对「这个模型」实付最优的套餐并返回带修正折扣的副本——不存在「选择用名义、实付用修正」的分离（旧语义会让 kimi-k3 选中名义 6× 但 $15 档实付 1.5× 的 OpenCode Go，比固定 4.5× 的 Kimi 会员贵 3 倍）。其他厂商（OpenAI / Anthropic / xAI / Copilot）未公布分模型配额，属不可修黑盒，维持锚点折扣。

### 套餐数据自动核验

套餐是性价比榜的地基，且口径随官方调价漂移。`scripts/verify_plans.py` 做三层检查，人只在告警时介入：

1. **一致性（离线，确定性）**：必填字段与 discount 取值域；`discount` 与 `monthly/implied_value`（或 `credit_value`）算术自洽（偏差 ≤1% 通过、1~5% WARN 历史舍入、>5% FAIL）；同产品线（按名称首词分组）月费升档时额度（implied_value/credit_value/tokens）必须非降。
2. **时效（离线）**：`source` 距最近一次核验超过 21 天、或从未写核验日期 → WARN。每次人工/模型复核后应把复核日期写回 `source`。
3. **可达性（联网，best-effort）**：官方购买页 URL 状态码；定价页多为 JS 渲染，只查可达性不做内容匹配。

FAIL（算术硬伤 / 档位额度反降 / 字段缺失）使脚本 exit 1。离线层同时固化为 `tests/test_plans_consistency.py`，随 pytest 在每次 push/PR 运行；联网全量由 `.github/workflows/plan-audit.yml` 每周一跑，产出 `results/plan_audit.json`，FAIL 时开 issue。语义级变化（官方调价、额度口径改动）无法纯靠脚本发现——审计 WARN 是「该复核了」的信号，不是「数据错误」的证明。

### 跨源模型名对齐

各源模型命名风格各异（如 LiveBench `claude-opus-4-7-xhigh-effort`、DeepSWE `claude-opus-4.7`、AA `claude-opus-4-7`）。`model_registry.json` 为每个统一 slug 维护各源别名，`merge.py` 按别名合并。**新增模型需同步维护别名映射**。

### 新模型自动发现与别名漏配检测

`merge.py` 以 `model_registry.json` 为白名单，registry 维护不当会静默丢数据。`detect_new_models.py` 在每次构建时做两类检测，结果写入 `results/new_model_candidates.json` 并打印告警：

1. **新模型**：源里出现、registry 完全没有收录的模型。只扫 LiveBench + DeepSWE 两个「前沿模型评测源」（命名规范、几乎无长尾噪音）；EQ-Bench / AA 因含大量 open-weights 长尾与旧模型不纳入新模型扫描。
2. **别名漏配**：registry 已收录但某源字段为 null，而该源里存在「规范化 slug」（点/连字符互换）对应的数据 —— 数据其实有，只是别名没配。这类检测覆盖 aa / eqbench / deepswe / livebench 四源，用 registry slug 做确定性反向匹配，无长尾噪音问题。

构建以 `detect_new_models.py --apply` 运行，对「新模型」做**自动入池**：

- **双源确认门槛**：候选需在 livebench / deepswe / aa 三个独立信号中至少出现两处才自动写入 registry；单源孤立条目（特评项、内部实验名等）只留在候选清单并标注 `insufficient_confirmation`，避免错误模型污染榜单。
- **确定性 slug/别名**：slug 由源名小写、剥离 effort 后缀、剥离 LiveBench 发布日分量（`gpt-5.2-2025-12-11-high` → `gpt-5.2`）、再把版本号分隔符收敛为点号派生（裸 `-max` 有歧义——`qwen3.8-max` 是型号名、`gpt-5.6-luna-max` 的 max 是档位——仅当前段非版本数字才剥离）。各源别名只取源数据里真实存在的名字，livebench 别名保留 effort 后缀原文。

> **版本分隔符必须收敛为点号。** 各源对版本号的写法不一致：DeepSWE / registry 用点（`claude-fable-5.1`、`qwen3.8-max`），LiveBench 与 AA 用连字符（`claude-fable-5-1-max-effort`、`qwen3-8-max`）。早期实现直接拿源名当 slug，LiveBench 的连字符写法被原样写成 `claude-fable-5-1`（2026-09-02 修复），既与 `claude-fable-5.1` 的正名不符、又让读者误以为是 `claude-fable-5` 的变体。现在候选先按规范化 slug 归组（点/连字符两种写法合并成一个条目），再取各源内真实存在的名字作别名。点号化只作用于「纯数字分量之间」的最左侧一对，`llama-3-70b`、`nemotron-3-ultra-550b-a55b` 这类不会被改坏。
- **creator 推断**：AA 命中时取其 Creator（经 `Z AI→Z.AI` 等修正表归一），未命中时按 slug 前缀推断主流厂商，均不中则 `Unknown`。
- **审计与回滚**：入池条目带 `auto_added` 日期标记，可随时 `grep auto_added scripts/model_registry.json` 定位；registry 顶层可选 `auto_add_exclude`（fnmatch 通配）永久排除误报名称；未入池候选连同原因一并写入候选 JSON。
- **发现候选不视为构建失败**：新模型上线是正常事件，不应阻塞榜单刷新。

> **漏配必须人工清零。** `--apply` 只自动入池「新模型」，**不会**自动补写已有条目的缺失别名——`missing_aliases` 是只读报告。漏配的后果是静默的：该源的真实分数被丢弃，指标落进岭回归填补，README 里显示成 `指标(reg)`，看上去像"这个模型没测过"而已。典型案例 glm-5.3（2026-09-01 修复）：registry 漏配 livebench/eqbench 两个字段，导致 EQ-Bench Elo 用填补值 1857 代替真值 2062.4，Text 榜被压到 #13 而非真实的 #6。因此每次构建后应确认 `results/new_model_candidates.json` 的 `missing_aliases` 四个源均为空数组。

## 指标选取与权重

本仓库维护**三个榜单**（通用榜 / 文本榜 / 性价比榜），共用同一次抓取、合并与缺失值填补，仅评分权重不同。性价比榜与通用榜同权重、同名次（`rank_by: "score"`，按综合分排序，避免便宜小模型霸榜），每行展示官方 API 混合价、最优订阅套餐的月费 / 倍率 / 套餐内等效价与购买链接；`Value = 综合分 ÷ 套餐内 $/1M` 仅作参考列。配套的「套餐购买指南」按套餐维度汇总：每个套餐取其覆盖厂商在通用榜上的最强模型，`套餐内 Value = 最强模型综合分 ÷ (Blended $/1M × 折扣)`，按该值降序——同时反映套餐可用的模型上限与折算价格（详见「订阅套餐与倍率」一节）。

### 通用榜 General（五维黄金标尺）

面向**真实编程 / 智能体 / 复杂工作流**，全面对齐 OpenAI（GPT-6 / 5.x）与 Anthropic（Claude Fable / Opus）两家官方旗舰发布主表使用的核心共识基准，选取 13 个指标归入 5 大领域，按「一主两辅（一大两小）」铁三角架构严密互锁：

| 领域分类 (权重) | 核心主基准 (Major) | 关键辅助基准 (Minors) | 子权重分配 | 官方来源与域内互锁逻辑 |
|---|---|---|---|---|
| **代码与 Agent** (35%) | **Terminal-Bench v4.0** | | 45% | AA 官方统一测试 harness 评测真实终端操作与命令行 Agent，杜绝多平台 scaffold 干扰。v4.0 在 AA v4.3 中取代 v2.1：v2.1 已饱和（精选池 24/39 模型挤在 ≥0.78），v4.0 区分度显著更高（标准差 0.165 vs 0.117），两者 r=0.709 |
| | | **DeepSWE v1.1** | 35% | 官方主表 Software Engineering（真实 GitHub Issue 修复） |
| | | **LiveBench Coding** | 20% | 独立防污染算法与严谨代码生成 |
| **业务自动化与 Web** (15%) | **tau3-Banking** | | 50% | AA 官方银行与金融真实业务智能体交互测试（Agentic Tool Use & Banking Workflows） |
| | | **LiveBench Data Analysis** | 30% | 复杂多表关联、数据转换与事件时间线分析 |
| | | **LiveBench Agentic** | 20% | 多步工具与智能体指令合成 |
| **指令遵循与长上下文** (20%) | **LiveBench IF** | | 55% | 严格多约束与负向规则遵循（指哪打哪） |
| | | **LCR** | 45% | 1M 超长文本跨文档检索可靠性 |
| **终极科学与推理** (20%) | **HLE (Humanity's Last Exam)** | | 60% | 博士级多学科前沿终极考场（彻底淘汰已饱和的 GPQA） |
| | | **SciCode** | 25% | 真实科研级科学计算与算法推理 |
| | | **LiveBench Reasoning** | 15% | 防污染复杂多步逻辑推理 |
| **事实准确性** (10%) | **Omniscience Index** | | 100% | 防幻觉与未知边界拒答基准 |

全局权重之和 = 1.00。

### 多模态（Vision）特性呈现与前沿标识

在日常代码排错（看终端截图、看 UI 设计稿）、文档阅读与日常选型中，模型**“具备图片识别能力”**还是**“纯文本模型”**具有质的体验差异。

- **不跑学术视觉跑分、不人为干预总分**：MMMU 等多模态学术跑分存在题库老化与偏题问题，且人为在综合分上加常数会破坏基准分数的纯粹性。因此**总分 100% 忠实于客观硬核基准加权求和**；
- **权威模态核准（基于 OpenRouter 官方元数据）**：所有模型的 Vision 特性均自动拉通 OpenRouter API 官方架构元数据（`architecture.input_modalities` 与 `architecture.modality`）进行 100% 机器可复核校验，杜绝人工误配与盲目全 True；新模型入池自动执行模态解析；
- **全链路决策呈现（选型维度）**：
  - **表格标识**：CSV 与 Top 15 表格增设 `Vision` 显式列（`👁️` / `-`）；
  - **双帕累托前沿图**：散点图清晰区分**实心圆点（支持视觉）**与**三角形点（纯文本）**，帮助用户在同一预算/能力档位下快速直观地做出多模态选型决策。

### 文本榜 Text

适用于小说创作、专业案头分析、长文阅读理解与日常对话，不包含代码生成与数理考试指标。全面剔除更新迟缓的第三方抓取源，回归 100% 官方受控的高覆盖体系（覆盖率均达 92%~100%）：

| 领域分类 (权重) | 核心主基准 (Major) | 关键辅助基准 (Minors) | 子权重分配 | 来源与评估重点 |
|---|---|---|---|---|
| **创意文学与小说创作** (25%) | **LiveBench StoryGen** | | 55% | 故事生成与长篇叙事创作 (LiveBench) |
| | | **LiveBench Language** | 45% | 字词组织、语感拼句与文字修辞 (LiveBench) |
| **专业案头与深度研究** (20%) | **AA-Briefcase** | | 50% | 真实多周知识工作项目（数千源文件、多关联任务）的 rubric + 两两对比评分 (AA)。2026-09 同步自 AA v4.3：取代 GDPval-AA——两者 r=0.973 高度冗余，Briefcase 覆盖 100%（GDPval 92%）且为私有 held-out 测试集，抗污染 |
| | | **LiveBench Data Analysis** | 25% | 商业数据表合并、转换与定量信息提取 (LiveBench) |
| | | **LiveBench Summarize** | 25% | 长文核心要点提炼与摘要 (LiveBench) |
| **严格指令与格式约束** (20%) | **LiveBench IF** | | 60% | 多重格式规则与负向约束遵循 (LiveBench) |
| | | **LiveBench Simplify** | 40% | 文本通俗化表达与精准改写约束 (LiveBench) |
| **事实抗伪与超长文本** (20%) | **Omniscience Index** | | 50% | 事实性与未知边界防幻觉拒答得分 (AA) |
| | | **LCR** | 30% | 1M 超长文本跨文档精确检索 (AA) |
| | | **Omniscience Non-Halluc.** | 20% | AA 官方抗幻觉率 (1 - Hallucination Rate) (AA) |
| **人际心智与人文社科** (15%) | **LiveBench Theory of Mind** | | 60% | 心智理论测试，评估社交认知与意图推断 (LiveBench) |
| | | **CritPt** | 40% | Critical Point 前沿物理学与复杂系统深度推理 (AA) |

全局权重之和 = 1.00。

> 各榜权重与领域分组均可在 [`config.json`](config.json) 中自定义，无需修改源码。

## 数据预处理

### 跨源合并

`merge.py` 读 `model_registry.json` + 各源 CSV，把 5 个源的分数合并成统一宽表（行 = 统一 slug，列 = 10 个指标 + Model/Creator）。LiveBench 别名可为列表（如 `deepseek-v4-pro` 的正式版 `-0813` 与预览版），多个匹配时取分数最高者。缺失值留空，交由评分阶段的岭回归填补。

**AA 定价取官方行**：AA 是按（Model Slug × Provider）的宽表，同一模型有 N 个 Provider 行（如 `deepseek-v4-flash` 15 行）。各行评测分数完全一致，但定价是各 Provider 自报的分销价——排行榜展示的必须是模型官方牌价（`Provider` 与 `Creator` 归一化互含，如 DeepSeek 行 0.44/1.32），而非 CSV 末行的分销价（Makora 0.09/0.195）。无官方行的模型（如 hy3 纯第三方分销）回退末行。视觉变体是独立 Model Slug（如 `deepseek-v4-flash-vision`），不会混入对应文本模型的行。

### 数据哨兵（AA）

AA 解析沿用三级降级链（RSC 流 → `__next_f.push` → `__NEXT_DATA__`）+ 数据哨兵（行数 + 评分字段非空率），不达标即失败退出，避免半残数据静默污染排名。

## 归一化方法（固定锚点缩放）

```
归一化得分 = (原始值 - 锚点下限) / (锚点上限 - 锚点下限) × 100
```

- 锚点是**固定的理论范围**（不是样本动态 min/max），定义在 `config.json` 的 `metric_scales`
- 结果范围 0–100，代表「原始值在理论范围中的位置」，即**真实能力分**而非**名次分**
- 保留绝对难度信息：DeepSWE 最高 74%（基准难）就是 74 分，Terminal-Bench v4.0 最高 0.591（基准难）就是 59 分，两者不再被同等拍成 100
- 加新模型不影响已有模型的分数（锚点固定，不随样本漂移）
- **越界裁剪**：原始值超出锚点范围时裁剪到 0–100（如 EQ-Bench Elo 超过 2200 上限不再产生 >100 的异常分）

各指标锚点：

| 指标 | 锚点 [lo, hi] | 说明 |
|---|---|---|
| LiveBench 各分类（含 Data Analysis）/ DeepSWE | [0, 100] | 已是 0–100 百分比 |
| LCR / HLE / tau3-Banking / Omniscience Non-Halluc. / CritPt / SciCode / Terminal-Bench v4.0 | [0, 1] | 0–1 比例，×100 隐含 |
| Omniscience Index | [-50, 50] | 净得分实际可达范围（全对/全错几乎不可能，0=中性） |
| EQ-Bench Creative Writing | [1400, 2200] | Elo 实际分布约 1438~2105，下限收紧到 1400 避免分数被压到 45 分以上 |
| AA-Briefcase | [400, 1700] | Elo 实际分布约 459~1662（AA v4.3 重锚后），与 EQ-Bench 同为 Elo 制固定锚点 |

> 与旧版 min-max 的区别：min-max 用「样本最高=100、最低=0」动态锚点，把名次差当能力差（离群值敏感、样本小不稳定、二次归一化抹掉难度）；固定锚点保留绝对难度与稳定性。Omniscience Index 用 [-50,50] 而非官方 [-100,100]：后者把实际样本（约 -19~43）压缩到 40-72 的窄区间、且让负分模型虚高到 40 分，[-50,50] 更贴合实际可达范围，负分模型正确压到 <50 分。

## 特征标准化（岭回归输入）

> 适用对象：**只用于缺失值填补阶段的岭回归输入 X**，不影响归一化（固定锚点 0-100）和最终加权求和。

跨源指标量纲差异大（EQ-Bench Elo 200–2100 vs 其他 0–100），`X^TX` 病态 → β 估计不稳。做法：

1. **fit 一次**：用全量 raw 真实值构造 (n × 10) 矩阵 → `StandardScaler.fit`
2. **最多 100 轮迭代 + LOO + R² 都用同一个 scaler** —— 不重 fit，避免随填补值漂移
3. **每次 transform 10 列**（含 target），删 target 列 + 加 bias 列 → 9 维标准化特征
4. **α=0.1**（z-score 空间统一）

`config.json` 加 `standardize_features` 开关（默认 `true`），设 `false` 退回原始 X + α=1.0。

## 缺失值填补与防刷分单调性约束

### 分域填补池（Domain Groups）

填补在 9 个互不相交的领域分组上进行，**严格禁止跨领域特征污染**（如禁止用文学写作分预测终端代码能力）。各领域池成员在 `config.json` `domain_groups` 中声明；`validate_config` 强制每个池指标恰属一域（重叠声明或漏声明都会构建失败，避免静默退化）。

| 域 | 成员 | 说明 |
|---|---|---|
| `code_agent` | Terminal-Bench v4.0 / DeepSWE / LiveBench Coding | 通用榜代码与 Agent |
| `automation_web` | tau3-Banking / LiveBench Agentic Coding | 通用榜业务自动化 |
| `instruction` | LiveBench IF / LiveBench Simplify / LCR | 两榜共用：指令遵循语义 |
| `reasoning` | HLE / SciCode / LiveBench Reasoning | 通用榜科学与推理 |
| `factuality` | Omniscience Index / Omniscience Non-Halluc. | 两榜共用：事实抗伪。Omniscience 当前全覆盖（50/50），该域回归实际只服务 Non-Halluc 缺失行；Omniscience LOO-MAE 偏高（≈14.7）仅作诚实披露，不影响任何行分数 |
| `creative_literature` | LiveBench StoryGen / LiveBench Language | 文本榜创意文学 |
| `professional_work` | AA-Briefcase / LiveBench Data Analysis / LiveBench Summarize | 文本榜专业案头 |
| `humanities_mind` | LiveBench Theory of Mind / CritPt | 文本榜人际心智（无层级链，见下） |
| `eqbench_solo` | EQ-Bench Creative Writing | 单指标域：EQ 不参与任一榜权重，缺失填均值并标 `(reg,low)`，比跨语义伪回归更诚实 |

### 填补算法：分域多变量岭回归 + 物理层级单调性约束

对每个目标指标 `T`，仅提取同一领域内部的其他已知指标进行预测：

1. **初始化**：缺失值用该领域内的基准均值填充；
2. **每轮分域迭代**：提取领域内真实值样本训练独立标准化 Scaler 与岭回归 → 预测缺失值 → 裁剪到 P95；
3. **物理层级单调性与防刷分天花板约束（Hierarchy Envelope）**：
   - 现实中，高阶前沿指标（如 `Terminal-Bench v4.0` 终端交互、`HLE` 博士考场）的难度必然高于基础指标（如 `LiveBench Coding`、`LiveBench Reasoning`）；
   - 算法内置领域层级链（`domain_hierarchies`），强制执行单调性约束：**高层级预测分严格不得脱离底层基础能力分**（防止未公布高难指标的普通模型被盲目抬高虚高分）；
   - 无实证难度排序的域不设链（`factuality`、`humanities_mind`、`eqbench_solo`、`instruction` 内 Simplify）：宁可无约束，不设错约束。反例：`humanities_mind` 曾设 `CritPt→Theory of Mind` 链，方向与数据相反（ToM 均值 78 是基础项、CritPt 均值 0.15 是高难项），导致无 ToM 真值的模型被压到 4~5 分，已删除；
4. **阻尼更新**：`cur = 0.5 * cur + 0.5 * pred`，迭代直至收敛（量程容差 0.5%）。

### 最小样本门槛

若某指标有效训练样本 < `imputation_min_samples`（当前 4），不回归填补，缺失值保留下层基础能力锚定均值，Imputed 列标注 `(reg,low)`。

### 填补降权（可配置）

填补值可信度低于真实值（留一验证 MAE 越大越不可靠）。`score_board` 支持对填补指标的权重打折：填补指标的权重 × `imputed_weight_discount`，其余真实指标权重不变，再**重新归一化**到总权重 1，保证总分仍落在 0–100 可比。

- `imputed_weight_discount = 1.0`（默认）= 不降权，与旧版一致。
- `discount < 1` 时，填补指标对总分贡献降低、真实指标权重相对上升——用于抑制填补误差对排名的干扰。
- 参数在 `config.json` 顶层 `imputed_weight_discount` 配置，缺失时默认 1.0。

## 留一验证

每次评分运行后，自动对每个指标做留一交叉验证（假装修饰一个真实值，用其余样本训练岭回归预测，报告 MAE 与 >10% 误差比例）。结果按榜单拆分写入 `results/validation_general.json` / `results/validation_text.json`。

**乐观偏差（须知）**：当前 LOO 在迭代填补写满 `cur` 之后运行，其他指标的已填补值会进入特征，故 MAE 略偏乐观（低估真实填补误差）。解读时按上界参考。

## 模型拟合质量（R²）

用全量训练集拟合后，计算每个指标的训练集 R²（z-score 空间）。R² 越高，该指标的缺失值预测越可信。当前（2026-09 快照）各指标 R² 约 0.00–0.87，其中 LiveBench Simplify（0.87）、LiveBench IF（0.86）、HLE（0.86）最可预测，EQ-Bench（0.00，单指标域、无交叉特征）、LiveBench Summarize（0.01）、LCR/Omniscience 系（0.05–0.08）最低；AA-Briefcase 为 0.31——填补可信度请以留一验证 MAE 为准。

## 能力-成本前沿图

`results/value_frontier.svg`（通用榜，纵轴 = 通用榜综合分）与 `results/text_frontier.svg`（文本榜，纵轴 = 文本榜综合分）随每次构建重新生成，算法在 `scripts/plot_frontier.py`：

- **横轴**：实际等效价（`Effective $/1M`，最优订阅套餐折算后的等效价，无订阅厂商即官方按量混合价）× 当次汇率折人民币，对数刻度；**纵轴**：对应榜单的 Weighted Total。
- **前沿定义**：价格升序中综合分严格递增的点序列（Pareto 最优）；红色阶梯线在预算 x 处的高度即该预算能买到的最强模型。
- **y 轴自适应**：下界 floor(min/5)×5、上界 ceil(max/5)×5+2，刻度间隔 5。
- **标注布局**：标签水平放点右侧，按水平投影分簇、簇内按锚点高度贪心垂直排布（重叠沿初始方向单调外推）、画布边界回退；离锚点较远的标签带细引线和白底框。布局用纯文本包围盒在 display 像素空间计算，与字体后端无关。

## 注意事项

1. **非绝对排名**：分数是相对排名，不代表能力绝对值
2. **填补值可信度**：留一验证 MAE 越低的指标填补越可靠；`(reg,low)` 填补仅供参考
3. **权重可自定义**：权重设计反映「编程 + 智能体 + 日常对话」的平衡，可通过 `config.json` 调整
4. **模型池需维护**：主流旗舰模型池与别名映射在 `model_registry.json`，新增模型需同步
5. **特征独立性**：填补仅用评分指标交叉预测，不含任何合成综合分，避免循环论证
