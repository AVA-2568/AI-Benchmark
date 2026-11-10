# ADR-0003：manifest 的算法版本与构建状态语义

- **状态**：已采纳（2026-11-10）
- **影响面**：`scripts/build.py`（`_algorithm_version` / `_write_manifest`）、`results/manifest.json`、`tests/test_readme_hero.py`、`tests/test_score_helpers.py`

## 背景

`results/manifest.json` 是「这份榜单出自哪次构建、哪份输入、哪版算法」的唯一凭证。实际有两个问题：

1. **`algorithm_version` 是硬编码字符串** `"e5b76d2"`，既不是 tag 也不对应任何 commit（维护时 HEAD 已是 `d412d11`）。也就是说这一栏**从来没有说过实话**，读者无法据此判断算法是否变过。
2. **只有 `stale` 一个状态位**，而 `--offline` 复算缓存也会把它设成 `true`。于是仓库里长期躺着一个 `stale: true` 的 manifest：到底是「抓取失败降级」还是「离线复算」，无从区分。

## 决策

1. `algorithm_version` 改为**派生值**：对 `scripts/pipeline/*.py`（真正承载评分算法的包）按文件名排序取 sha256，取前 12 位。算法不动则值不动，改算法必然变。不依赖 git（tarball / CI 浅克隆下也可用）。
2. manifest 增加独立字段 `offline`：`offline=true` 表示本次未联网、只复算缓存；`stale=true` 才表示输入可能过期。两者正交，README 刷新只受 `stale` 控制。
3. 测试锁定：`_algorithm_version()` 必须是 12 位且确定，且不再等于旧常量 `e5b76d2`；`main(["--offline"])` 必须把 `offline=True` 传给 `_write_manifest`。

## 后果

- manifest 从「看起来有版本」变成「真的能对版本」：改评分代码 -> 版本号必然变化，可用来核对某份 CSV 是否与当前代码同源。
- 注意：`pipeline/*.py` 的任何改动（含注释）都会改变版本号。用「源码摘要」而非「语义版本」就是为了避免维护者忘记手写 bump——宁可多变更，不可漏变更。
- `stale` 与 `offline` 语义分离后，CI 日志和 manifest 能分别回答「数据新旧」和「是否联网」两个问题。

## 替代方案

- **从 git 取 `rev-parse --short HEAD`**：能反映提交，但把版本绑在提交而非算法上——只改 README 也会改版本号，而且 tarball 场景不可用。
- **人工维护语义版本号**：本项目只有一名维护者、无发布节奏，必然忘记 bump。
