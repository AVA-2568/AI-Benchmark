# ADR-0004：LiveBench 多档 effort 别名取最高档

- **状态**：已采纳（2026-11-10）
- **影响面**：`scripts/merge.py`（`_pick_max` / `_row_score`）、`tests/test_merge.py`、`METHODOLOGY.md`、`results/*_scored.csv`

## 背景

LiveBench 对同一模型常同时公布多档思考档位的行：`claude-opus-4-7-xhigh-effort`、`gpt-5.6-terra-max`、`gemini-3.8-flash-high`、以及裸名。`model_registry.json` 用别名列表记录这些写法，`note` 明确写着「livebench=… (可列表，**多个时取最高分**)」，`merge._pick_max` 的 docstring 也写着「返回匹配到的最高分」。

但实现是：

```python
for a in alist:
    if a in idx:
        return idx[a], a      # 命中即返回 -> 取的是列表里第一个
```

即**按别名顺序取首个命中**，与两处文档约定都不符。实测 73 个模型里 18 个是多别名，其中 **9 个正在使用低档行**：

| 模型 | 实际取到 | 本应取到 |
|---|---|---|
| gpt-5.6-terra | `gpt-5.6-terra` | `gpt-5.6-terra-max` |
| inkling | `inkling` | `inkling-xhigh` |
| gemini-3.8-flash | `gemini-3.8-flash` | `gemini-3.8-flash-high` |
| muse-spark-1.3 | `muse-spark-1.3` | `muse-spark-1.3-xhigh` |
| gpt-6-luna | `gpt-6-luna` | `gpt-6-luna-max` |
| grok-4.7 | `grok-4.7` | `grok-4.7-xhigh` |
| mistral-large-4 | `mistral-large-4` | `mistral-large-4-high` |
| muse-wonder-1.0 | `muse-wonder-1.0` | `muse-wonder-1.0-max` |
| claude-haiku-5.5 | `claude-haiku-5-5-max-effort` | `claude-haiku-5.5`（方向相反） |

后果是这些模型的 LiveBench 项被系统性低估，直接压低综合分与名次。

## 决策

按注册表约定实现「取最高档」：`_pick_max` 比较各别名行的**行内数值列均值**（`_row_score`，忽略 `model` 与空值/非数值），取最高者；同分按别名顺序取先出现者以保证确定性；无任何数值列的候选行跳过。

对「某模型只在源里公布了 `-high`」的情况不做特殊处理：清单里有几档就取其中最高的，只有 `-high` 就以 `-high` 为准。是否**真的**存在更高思考档位不由本函数判断，靠 registry 维护别名列表来体现。

## 后果

只改口径、不改权重，实测影响：

- 通用榜 16 个名次变动，文本榜 18 个；榜首不变（`claude-opus-5.5`，77.7 / 82.3）。
- 变动最大：`mistral-large-4` 27→16（+10.4 分）、`claude-haiku-5.5` 文本榜 18→12（+7.0 分）。
- 覆盖行数不变（同一行只是换成高档别名行），填补比例不变。
- `merged.csv` 与全部 scored CSV、validation、README 生成块随构建一并刷新。

## 后续修正（2026-11-10，见 ADR-0005）

本条 ADR 最初把 `claude-haiku-5.5` 的三行解释为「另一个变体」。**该判断是错的**。核对上游后确认：LiveBench 最新 release 只有一行（裸名），多出来的 `-max-effort` / `-xhigh-effort` 来自已下线的 LiveBench 1.0 补充口径——是我们的抓取把两代命名合表造成的重复，而不是三个真实档位。

因此取分口径细化为：**先比 release（新者优先），同 release 内再比分数**。本 ADR 的「同 release 内取最高档」仍然有效，只是不再是第一优先级；`_pick_max` 相应改名为 `_pick_best_row`。

## 替代方案

- **保持现状、只改文档措辞为「取首个命中」**：等于承认榜单长期使用低档行，与「每个模型取各源最高推理档」的建榜原则冲突，已否。
- **逐指标取跨别名最大值（按列拼一行）**：会混合不同档位的行，产生现实中不存在的「缝合模型」，已否。
