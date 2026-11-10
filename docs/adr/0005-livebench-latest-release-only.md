# ADR-0005：LiveBench 只取最新 release，并按 release 去重

- **状态**：已采纳（2026-11-10）
- **影响面**：`scripts/fetch_sources.py`、`scripts/merge.py`、`scripts/model_registry.json`（别名）、METHODOLOGY

## 背景

用户在核对 `claude-haiku-5.5` 时发现：AA 上只有一条 Haiku 5.5（reasoning effort: max），而我们库里有三行，Coding 分别是 77.6 / 91.4 / 76.4。核查上游后确认：

1. LiveBench 最新 release（`data/20261106/table.csv`）只有 33 行，**一行一个模型、没有任何 effort 后缀**；`claude-haiku-5.5` 单行 = `47.9 / 82.4 / 77.6 / 69.5 / 53.1 / 84.3 / 79.3`，与 AA 页面的 7 个 suite 数字**逐项一致**（AA 的 suite 即 LiveBench 2.0）。
2. 我们多出来的 `-max-effort` / `-xhigh-effort` 行来自 LiveBench **1.0 补充口径**。该口径的 `table_2026_06_25.csv` 现已全路径 404，且 404 页返回 **HTTP 200 + HTML**，旧实现把它当 CSV 解析，一行读不到也不报错，属静默失败。
3. 旧 `fetch_livebench()` 把 1.0 / 2.0 两代命名合进一张表且不记录来源版本，于是同一模型出现多行、分数互相矛盾；`merge` 再按别名顺序任选其一（见 ADR-0004）。

## 决策

1. **只抓最新 release**（`LB_RELEASES_KEEP = 1`），不再抓 1.0 补充。
2. 每行写 `release` 列（如 `20261106`），供 merge 判断新鲜度。
3. `merge._pick_best_row()` 的优先级改为：**release 新 > 同 release 内分数高 > 别名顺序**。release 标识归一为纯数字再比较（`20261106` / `2026-11-06` 等价）。
4. 抓取前校验表头：首行必须以 `model` 开头，否则抛错——让「200 + HTML 错误页」显式失败，而不是静默变成零行。

## 后果

- `claude-haiku-5.5` 只剩一行，数值与 AA 页面一致（Coding 77.6，不再是 91.4）。
- LiveBench 覆盖从 70/73 降到 29/73（最新 release 只测 33 个模型）。这个损失不可回避——旧覆盖有一半是 1.0 时代的不同测试集，本来就不该与新数据混算。
- 覆盖下降触发榜单重排，进而需要新的上榜门槛，见 ADR-0006。
- registry 里的 `livebench` 别名列表仍然有用（历史写法 + 大小写差异），但不再是「多档选择」的主要机制。

## 替代方案

- **继续保留 1.0 补充以维持覆盖率**：数据源已 404，且 1.0 的子项映射（如 Design ← story_generation）与 2.0 不同量表，混算本身就是错误口径。否决。
- **抓多个 2.0 历史 release 取并集**：能回到 56 个模型，但用户明确要求「使用最新的测评结果」，且跨 release 混用同样存在重测不同步的风险。否决（机制保留：`LB_RELEASES_KEEP` 可调）。
