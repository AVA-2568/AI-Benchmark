# ADR-0002：DeepSWE 全链路退役

- **状态**：已采纳（2026-11-10）
- **影响面**：`scripts/fetch_sources.py`、`scripts/merge.py`、`scripts/detect_new_models.py`、`scripts/model_registry.json`、`scripts/openrouter_modalities.py`、文档与测试

## 背景

DeepSWE（Datacurve，Pass@1）曾被用于「代码与 Agent」域的 35% 子权重。此后发生三件事，使它变成了一条只花钱不产出的链路：

1. **上游停更**：`METHODOLOGY.md` 与 README 都已声明「替代已停更的 DeepSWE」，配置里「代码与 Agent」域改为 Terminal-Bench v4.0 40% / LiveBench Long-Horizon 35% / LiveBench Coding 25%，**DeepSWE 不在任何榜单权重内**。
2. **抓取仍在跑**：`fetch_sources.fetch_deepswe()` 每次构建仍然请求 `deepswe.datacurve.ai` 的 JSON API，失败会带崩整个 `fetch_sources`（`main()` 汇总失败即返回 1，`build.run` 的 `check=True` 直接终止构建）。
3. **合并结果是丢弃的**：`merge.py` 把 `deepswe.csv` 读成 `ds` 索引后**从未使用**，`merged.csv` 里根本没有 `Pass@1` 列；registry 的 73 条记录却都保留着 `deepswe` 字段（其中 28 条有真实别名），读者会误以为它还在参与评分。

## 决策

彻底退役，不留半条链路：

1. 删除 `fetch_deepswe()` 与 `FETCHERS["deepswe"]`。
2. 删除 `merge.py` 里未使用的 `ds` 索引与 docstring 中的 DeepSWE 行。
3. `detect_new_models.py` 的新模型扫描源收窄为 LiveBench 单源；入池确认门槛改为「**LiveBench 出现 + AA 精确匹配（Model Slug 或 Host API ID）**」，仍是双源，只是换掉退役源。删掉不再被调用的 `_pick_alias()`。
4. registry 的 73 条记录删除 `deepswe` 字段；`swebench` / `terminalbench` 属更早的遗留字段（值仍在，但无消费者），本次保留并在 `note` 中标注为历史遗留，不再声称其为有效数据源。
5. 文档（README / METHODOLOGY / AGENTS）删除 DeepSWE 的有效源身份，改写为「已退役 + 时间 + 替代者」。

## 后果

- 每次构建少一次对外请求，少一个可能拖垮构建的外部依赖。
- 新模型自动入池的信号源从 3 个降到 2 个。这是**有意收紧**：单源候选本来就只报告不入池，`results/new_model_candidates.json` 里 5 个 smaug 系候选（仅 LiveBench 出现）在改动前后行为一致。
- 覆盖的 `deepswe` 别名可在 git 历史中找回，不影响历史可追溯性。
- 相关文档的「数据源」条目数由虚标的 6 个修正为实际的 3 个评测源 + 汇率 + 模态元数据。

## 替代方案

- **保留抓取仅作检测信号**：省不了请求，且上游真停更后该信号会静默变空、无人察觉，比彻底删掉更危险。
- **保留字段只为兼容**：registry 不是对外 API，没有兼容包袱，保留只会持续误导读者。
