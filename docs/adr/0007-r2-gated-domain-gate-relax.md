# ADR-0007：领域门槛对「回测可信」的域再放宽 1 个缺口

- **状态**：已采纳（2026-11-12）
- **影响面**：`config.json`（`domain_gate_relax`）、`scripts/pipeline/scoring.py`、`scripts/pipeline/__init__.py`、`scripts/pipeline/config.py`、`tests/test_scoring.py`、METHODOLOGY

## 背景

ADR-0006 定的门槛是「每个领域最多缺 1 个基准值」。它解决的是全局缺失率一刀切的问题，但留下了另一个死区：**某个域整体缺 2 个**时整行出局——哪怕这一行有 15/17 个实测值，缺的只是上游尚未公布的评测。

2026-11-12 的实例：Gemini 4 Carbon 同时出现在 LiveBench 与 AA，被自动入池，但通用榜 5 个域里「终极科学与推理」缺 HLE 与 SciCode 两个值——AA 只对它有 Omniscience / Terminal-Bench / AutomationBench / LCR 的数据，HLE、SciCode 尚未补测。结果它拿到文本榜 #2（82.4）却在通用榜完全消失，读者看到的是「同一个模型两张榜一有一无」。

两个缺口的可回测性并不差：池内 LOO 交叉预测的 R² 为 HLE 0.922、SciCode 0.873，属于全池最高的一档（对比 LiveBench Coding 0.514、LiveBench Data Analysis 0.243）。

## 决策

在 ADR-0006 的个数门槛之上，加一条**仅对高可回测指标生效**的例外：

```
若某域缺口数 == max_missing_per_domain + 1
   且 该域全部缺口指标的域内回归 R² ≥ domain_gate_relax.min_domain_r2
则放行；每行最多放宽 max_relaxed_domains 个域
```

实现：`pipeline.scoring._domain_ok(raw, i, board, max_missing, r2=..., relax_min_r2=..., max_relaxed_domains=...)`；R² 由 `ImputationEngine.r2_log()` 在评分前算出并传入（原实现是评分后才打印）。未配置 `domain_gate_relax` 时行为与 ADR-0006 完全一致。

默认参数：`min_domain_r2 = 0.85`、`max_relaxed_domains = 1`。

## 后果

- 池 75 模型 → **25 个上榜**（三榜均 25 行）。放宽**只**放行 Gemini 4 Carbon（通用 #3 / 文本 #2 / 性价比 #3），其余 7 个仅 12/17 实测的模型仍被原门槛拦下——它们的缺口落在「代码与 Agent」（LB 系 R² 0.514–0.790），够不到 0.85。
- 通用榜 23/25 行为全实测，2 行带 2 个域内回测值；文本榜维持 93% 权重为实测。
- 缺口不再由「个数」单维决定，而是「个数 × 该指标是否可被可信回测」。R² 低的域（代码与 Agent 的 LB 系、事实准确性的 Omniscience 0.192）等同于没有例外。
- 风险：R² 是在有真值的模型上算的，对新模型的外推质量无法直接验证。缓解手段是门槛只放宽 1 个缺口、每行只放宽 1 个域，且 `max_imputed_ratio`（0.6）仍在兜底。

## 替代方案

- **直接 `max_missing_per_domain = 2`**：会把 7 个只有 12/17 实测（LB 系全缺）的模型一并放入通用榜，其中 glm-5.3 直接进前 11。个数门槛失去意义，已否决。
- **保持原门槛、等上游补测**：代价是新模型首发窗口（数天到两周）内两张榜不一致，而这段时间恰是读者最关注的。已否决。
- **把 AA 的 Intelligence Index 或 GDPval-AA 直接塞进推理域凑第二个实测值**：跨域指标混入会破坏域内互锁语义（Intelligence Index 本身是综合分，AGENTS.md 明令禁止引入合成综合分），已否决。
