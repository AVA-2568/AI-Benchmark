# 术语表（Glossary）

本仓库的口径词汇。写文档、改代码、看 issue 前先对齐这里；新增术语请顺带补一行。

## 模型与命名

| 术语 | 英文 / 代码位置 | 含义 |
|---|---|---|
| **统一 slug** | `slug`，`scripts/model_registry.json` | 模型的唯一标识，全小写、连字符分词、版本号用点号（`claude-fable-5.1`、`qwen3.8-max`）。榜单、CSV、README 里出现的模型名一律是 slug，不是任何源的原始名 |
| **registry** | `scripts/model_registry.json` | 模型池 + 各源别名映射的唯一权威来源。`merge.py` 以它为白名单：不在 registry 的模型不会进榜 |
| **精选池** | pool / `model_registry.models` | 当前收录的 73 个主流旗舰。榜单只覆盖池内模型；池外的长尾模型由「精选」原则排除 |
| **别名** | alias，字段 `aa` / `livebench` / `eqbench` / `openrouter` | 某模型在某个数据源里的原始名字。`livebench` 可以是列表（多档 effort 行） |
| **release** | `livebench.csv` 的 `release` 列 | LiveBench 每期评测的版本标识（如 `20261106`）。同一模型跨 release 出现时取**最新一期**（见 ADR-0005） |
| **多档 effort 行** | tier | 同一模型的多个思考档位行（`-max` / `-xhigh` / `-high` / 裸名）。仅在**同一 release 内**比较时取行内均值最高者；源里只公布 `-high` 就以 `-high` 为准（见 ADR-0004） |
| **双源确认** | `detect_new_models.auto_add_candidates` | 新模型自动入池的门槛：必须「LiveBench 出现 + AA 精确匹配（Model Slug 或 Host API ID）」。仅单源出现的候选只报告不入池 |
| **auto_added / auto_add_exclude** | registry 字段 | 自动入池条目带的日期标记；顶层 `auto_add_exclude` 是 fnmatch 通配的永久排除名单（如 `smaug-*`） |

## 评分

| 术语 | 英文 / 代码位置 | 含义 |
|---|---|---|
| **指标池** | `config.json` → `imputation_pool` | 参与评分与填补的 17 个指标。榜单权重只能引用池内指标 |
| **领域分组** | `domain_groups` | 把 17 个指标切成 8 个互不相交的域。填补**只允许域内交叉预测**，禁止跨域特征污染 |
| **固定锚点** | `metric_scales` | 每个指标的固定理论范围 `[lo, hi]`。归一化用 `(v-lo)/(hi-lo)*100`，越界裁剪到 0–100。不做「样本最高=100」的动态 min-max |
| **原始值 / 填补值** | raw / imputed | 源里真实存在的分数是原始值；由岭回归预测出来的是填补值。CSV 里填补值带 `*`，低置信度填补带 `**` |
| **低置信度填补** | `(low)` / `min_samples` | 某指标可用于训练的真实样本数小于阈值时，填补结果打 `(low)` 标记 |
| **填补降权** | `imputed_weight_discount` | 可选参数：把填补指标的权重打折后重新归一化，抑制填补误差对排名的干扰。默认 1.0（不降权） |
| **层级链** | `domain_hierarchies` | 域内的物理难度排序（如 Coding → Long-Horizon → Terminal-Bench），用于约束高层级指标的预测分不得脱离基础能力分 |
| **LOO 验证** | leave-one-out，`results/validation_*.json` | 每次构建对每个指标做留一交叉验证，产出 MAE 与 >10% 误差占比。注意当前实现略偏乐观（已填值进入特征） |
| **R²** | 构建日志 / METHODOLOGY「模型拟合质量」 | 全量训练集上每指标的拟合优度。越高说明该指标的缺失值越可预测，但**判断可信度应以 LOO MAE 为准** |
| **上榜门槛** | `max_missing_per_domain` | 每个领域最多缺 1 个基准值：3 基准域至少 2 个实测、单基准域必须实测。缺的那个值由域内回归回测；缺 2 个则整行不上榜（见 ADR-0006） |
| **综合分** | `Weighted Total` | 五维加权后的 0–100 分。权重定义在 `config.json` 的 `leaderboards.<board>` |
| **榜单排序口径** | `rank_by` | `score` = 按综合分排（通用榜/文本榜/性价比榜都用它）；`value` = 按分数÷等效价排（当前未用于任何榜单，避免便宜小模型霸榜） |

## 价格与套餐

| 术语 | 英文 / 代码位置 | 含义 |
|---|---|---|
| **标准价** | `Total $/1M` | 全局中性缓存命中假设（`cache_hit_rate` 0.5）下的每百万 token 混合价 |
| **混合价** | `Blended $/1M` | 按 per-creator 缓存命中率（默认 0.9）折算、**未含订阅折扣**的价。是换算任意套餐等效价的基准 |
| **等效价** | `Effective $/1M` | `Blended × 套餐折扣`，即真实到手单价。无可用套餐时等于混合价（API 按量） |
| **折扣 / 倍率** | `discount` / `multiplier` | 折扣 = `monthly ÷ value`；倍率 = `value ÷ monthly`。两者独立计算，不用 `1/discount` 反算，避免舍入误差 |
| **价值基准** | `implied_value` / `credit_value` | 订阅额度上限的 API 等价：前者是社区实测的上限（ChatGPT/Claude），后者是官方随附额度（Copilot）。积分制套餐两者皆无，`discount = 1.0` |
| **分模型修正** | `model_cost_scale` | 积分/Credits 套餐对不同模型的抵扣密度不同，用它按官方积分系数修正。**修正发生在套餐比较之前**，选中的套餐已带修正折扣 |
| **套餐匹配** | `model_match` / `exclude_match` / `creator_match` | 白名单 + 一票否决黑名单 + 厂商匹配。定义了 `model_match` 的套餐必须命中它，不允许被 `creator_match` 旁路 |
| **能力-成本前沿** | frontier，`results/*_frontier.svg` | 价格升序中综合分严格递增的 Pareto 点序列。预算 x 处阶梯线的高度 = 该预算能买到的最强模型 |
| **人民币价格** | `Total ¥/1M` / `Effective ¥/1M` | 美元价 × 实时 USD→CNY（Frankfurter 主、open.er-api 备）。汇率缓存写入 `scripts/.cache/fx.json` |

## 构建产物与状态

| 术语 | 英文 / 代码位置 | 含义 |
|---|---|---|
| **marker 区块** | `<!--NAME_START-->` … `<!--NAME_END-->` | README 里唯一允许自动替换的区域。当前有 `HERO` / `SNAPSHOT_*` / `TOP15_*` / `PLANS_GUIDE` / `FRONTIER` / `TEXT_FRONTIER`。标记缺失即构建失败 |
| **HERO** | `build.hero_block()` | README 头部三榜结论（第一名/分数/最低等效价/池规模），由 scored CSV + registry 渲染，**禁止手写** |
| **stale** | `results/manifest.json` | 输入可能过期（抓取失败后复用缓存）。`stale=true` 时**不刷新 README** |
| **offline** | `results/manifest.json` | 本次未联网、仅复算缓存。与 `stale` 正交：离线复算不代表数据过期 |
| **算法版本** | `algorithm_version` | `scripts/pipeline/*.py` 源码摘要前 12 位。用来核对某份 CSV 与当前算法是否同源 |
| **manifest** | `results/manifest.json` | 每次构建的凭证：运行时间、数据时点、输入/配置哈希、算法版本、模型数、stale、offline |
| **候选清单** | `results/new_model_candidates.json` | 新模型发现与别名漏配的只读报告。发现候选不算构建失败，但 `missing_aliases` 应人工清零——漏配会导致真值被静默丢弃、改用填补值 |
| **审计** | `results/plan_audit.json`，`scripts/verify_plans.py` | 套餐数据的算术自洽 + 档位单调 + 核验时效（21 天）+ URL 可达性。FAIL 开 issue，WARN 只记录 |
| **核验日期** | `plans[].source` | 上次人工/模型复核该套餐的日期。超过 21 天产生 WARN，复核后要写回 |
