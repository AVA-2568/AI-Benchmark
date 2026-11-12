# AA-AI-Benchmark Agent Guide

## 目标
按多源公开基准数据（LiveBench 2.0 / EQ-Bench / Artificial Analysis，外加 Frankfurter 汇率与 OpenRouter 模态元数据）生成 General / Text / Value 三个榜单。DeepSWE 已于 2026-11 退役，不再抓取或计权（`docs/adr/0002-retire-deepswe.md`）。

## 唯一入口
```bash
python scripts/build.py
```

离线复算现有缓存：
```bash
python scripts/build.py --offline
```

## 测试
```bash
python -m pytest -q
```

## 数据流
fetch(多源) -> detect(新模型发现，`--apply` 自动入池) -> merge(跨源合并) -> imputation -> validation -> scoring -> README

## 核心不变量
- leaderboard 权重总和必须为 1。
- 每个评分指标必须存在于 imputation_pool，且其固定锚点必须在 metric_scales 中。
- 基准集合的选取准绳是「**本季 LiveBench 模型的 AA 覆盖率**」（ADR-0008），不是全池覆盖率：池里一半历史条目早已不被上游跟踪，按全池选指标会把真正的前沿模型挡在域外。AA 新增评分字段必须登记到 `parse_aa.NEW_SCORE_FIELDS`，未登记会被 `unmapped_score_fields()` 在解析时点名告警。
- SciCode 于 2026-11 下架（AA 标注 `underReview`，数据集被独立审计发现疑似错误），科学推理位由 CritPt v2 Hard 承担；长上下文域补 MLCR（与 LCR r=0.44，互补）。
- 上榜门槛：每个领域最多缺 1 个基准值（`max_missing_per_domain=1`；3 基准域至少 2 个实测，单基准域必须实测），缺的那个值由域内回归回测，缺 2 个则整行不上榜。唯一例外（ADR-0007）：该域两个缺口指标的域内 R² 均 ≥ `domain_gate_relax.min_domain_r2`（0.85）时放行，且每行最多放宽 1 个域——放行依据是「可高置信回测」，不是「多缺一个没事」。
- 原始值与填补值必须区分。
- 填补仅用评分指标交叉预测，不得引入任何合成综合分。
- README 只能替换标记区块；标记缺失时构建失败。头部结论（`HERO`）同样由 `build.hero_block()` 从 scored CSV + registry 渲染，**禁止手写**，`tests/test_readme_hero.py` 会校验一致性。
- 抓取失败时默认失败；`--allow-stale` 仅用于显式诊断，且不刷新 README。
- 每次构建生成 `results/manifest.json`，记录输入哈希、配置哈希、`stale`（输入可能过期）与 `offline`（本次未联网复算）两个独立状态，`algorithm_version` 由 `pipeline/*.py` 源码摘要派生，禁止写死。
- 模型池与别名映射在 `scripts/model_registry.json`，新增模型需同步维护。
- `detect_new_models.py` 默认只读，输出 `results/new_model_candidates.json` 候选清单（新模型 + 别名漏配两类）；build 以 `--apply` 运行：双源确认（LiveBench 出现 + AA 精确匹配）的新模型自动入池，条目带 `auto_added` 日期标记；单源孤立候选只报告不入池；registry 顶层可选 `auto_add_exclude`（fnmatch 通配）永久排除误报名称；发现候选不视为构建失败。

## 修改规则
- 修改算法必须同步更新 METHODOLOGY.md。
- 修改结果字段必须同步更新测试和 README。
- 不得在实验脚本复制评分逻辑。
- 修改后先运行 `python -m pytest -q`，再用 `python scripts/build.py --offline` 做端到端验证。
