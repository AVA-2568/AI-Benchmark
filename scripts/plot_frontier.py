#!/usr/bin/env python3
"""能力-成本 Pareto 前沿图：给定每 1M token 预算时的最优模型选择。

读 value_scored.csv 的行（通用榜名次序），横轴取实际支付价（最优订阅
套餐折算后的等效价，无订阅厂商即官方按量混合价）× 汇率折人民币，
纵轴取 Weighted Total。前沿 = 价格升序中能力递增的模型；阶梯线在
预算 x 处的高度即该预算能买到的最强模型。输出单面板 SVG（人民币
计价），标签用英文以兼容无中文字体的构建环境。
"""
import math

import matplotlib

matplotlib.use("Agg")
# 中文标签字体链：CI（ubuntu，装 fonts-noto-cjk）用 Noto，Windows 本地回退雅黑/黑体
matplotlib.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC", "Microsoft YaHei", "SimHei", "DejaVu Sans"]

import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.text as mtext  # noqa: E402


def pareto_frontier(points):
    """[(price, score, label, ...)] -> 价格升序中能力递增的最优点序列。

    剔除无价格/无分数的点；同价取先到者（分数必须严格更高才入前沿）。
    保留原元组的所有元素（兼容 vision 等附加字段）。
    """
    pts = sorted((p for p in points if p[0] and p[1] is not None),
                 key=lambda p: p[0])
    out = []
    best = float("-inf")
    for pt in pts:
        score = pt[1]
        if score > best:
            out.append(pt)
            best = score
    return out


def _label_frontier(ax, frontier):
    """为前沿点放置不重叠的模型名标注，必要时带引线。

    必须在轴刻度/范围设置与 tight_layout 之后调用。流程三段分离：
    用纯 Text 量出模型名的真实宽高（Annotation 的 bbox 会把引线
    patch 也算进去，不能用于布局）；在 display 像素空间按水平投影
    分簇、簇内按锚点高度贪心垂直排布并回退到画布内；最后按算好的
    位置一次性创建标注，被推离锚点较远的加细引线和白底框。
    """
    fig = ax.figure
    trans = ax.transData
    inv_trans = trans.inverted()
    dpi = fig.dpi

    FS = 8.5  # 字号 pt
    min_gap = 3.0 * dpi / 72  # 标签间最小垂直间隙（px）
    leader_thresh = 14.0 * dpi / 72  # 超此距离加引线
    init_dx = 8.0 * dpi / 72
    init_dy = 11.0 * dpi / 72

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax_bbox = ax.get_window_extent(renderer)

    # 1. 测量：纯 Text 的真实宽高（不受引线 patch 污染）
    meas = mtext.Text(0, 0, "", fontsize=FS)
    meas.set_figure(fig)
    sizes = []
    for pt in frontier:
        name = pt[2]
        meas.set_text(name)
        b = meas.get_window_extent(renderer)
        sizes.append((b.width, b.height))
    del meas

    n = len(frontier)
    anchors = [trans.transform((pt[0], pt[1])) for pt in frontier]
    ws = [w for w, _ in sizes]
    hs = [h for _, h in sizes]
    x0s = [anchors[k][0] + init_dx for k in range(n)]

    # 2a. 簇分组：x 升序，水平投影重叠的连成一簇
    order = sorted(range(n), key=lambda k: anchors[k][0])
    clusters, cur, cur_right = [], [order[0]], x0s[order[0]] + ws[order[0]]
    for k in order[1:]:
        if x0s[k] < cur_right:
            cur.append(k)
            cur_right = max(cur_right, x0s[k] + ws[k])
        else:
            clusters.append(cur)
            cur, cur_right = [k], x0s[k] + ws[k]
    clusters.append(cur)

    # 2b. 簇内贪心垂直排布：锚点 y 升序放置，冲突沿初始方向单调外推
    ys = [0.0] * n
    for cluster in clusters:
        placed = []  # (x0, x1, y0, y1)
        for k in sorted(cluster, key=lambda k: anchors[k][1]):
            sign = -1 if k % 2 == 0 else 1  # 初始方向：偶下奇上
            y = anchors[k][1] + sign * init_dy
            for _ in range(50):  # 保险上限；+0.5px 余量防浮点推不动
                hits = [b for b in placed
                        if x0s[k] < b[1] and b[0] < x0s[k] + ws[k]
                        and y - hs[k] / 2 < b[3] + min_gap
                        and y + hs[k] / 2 > b[2] - min_gap]
                if not hits:
                    break
                if sign < 0:
                    y = min(b[2] for b in hits) - min_gap - hs[k] / 2 - 0.5
                else:
                    y = max(b[3] for b in hits) + min_gap + hs[k] / 2 + 0.5
            ys[k] = y
            placed.append((x0s[k], x0s[k] + ws[k], y - hs[k] / 2, y + hs[k] / 2))

    # 2c. 边界回退 + 全对复核（纯数字盒；正常一轮收敛）
    def clamp(k):
        ys[k] = min(max(ys[k], ax_bbox.y0 + 2 + hs[k] / 2),
                    ax_bbox.y1 - 2 - hs[k] / 2)

    for k in range(n):
        clamp(k)
    boxes = [(x0s[k], x0s[k] + ws[k], ys[k] - hs[k] / 2, ys[k] + hs[k] / 2)
             for k in range(n)]
    for _ in range(60):
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)
                 if boxes[i][0] < boxes[j][1] and boxes[j][0] < boxes[i][1]
                 and boxes[i][2] < boxes[j][3] + min_gap
                 and boxes[j][2] < boxes[i][3] + min_gap]
        if not pairs:
            break
        for i, j in pairs:
            up, dn = (i, j) if boxes[i][2] >= boxes[j][2] else (j, i)
            overlap = min(boxes[i][3], boxes[j][3]) - max(boxes[i][2], boxes[j][2])
            for m, d in ((up, 1), (dn, -1)):
                ys[m] += d * (overlap / 2 + min_gap + 0.5)
                clamp(m)
                boxes[m] = (boxes[m][0], boxes[m][1],
                            ys[m] - hs[m] / 2, ys[m] + hs[m] / 2)

    # 3. 按算好的位置创建标注；一律垫白底框（阶梯竖线常从锚点右侧
    # 穿过，无白底时文字压线不可读），被推离锚点较远的另加引线
    texts = []
    for k, pt in enumerate(frontier):
        price, score, name = pt[0], pt[1], pt[2]
        tx, ty = inv_trans.transform((x0s[k], ys[k]))
        far = math.hypot(x0s[k] - anchors[k][0],
                         ys[k] - anchors[k][1]) > leader_thresh
        texts.append(ax.annotate(
            name, xy=(price, score), xytext=(tx, ty), fontsize=FS,
            ha="left", va="center", color="#222", zorder=5,
            arrowprops=dict(arrowstyle="-", color="#888", lw=0.6,
                            shrinkA=2, shrinkB=4) if far else None,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                      alpha=0.8)))
    return texts


def render(rows, out_path, fx_rate=None, ylabel="通用榜综合分", fmt="svg"):
    """渲染单面板（人民币）前沿图到 out_path。

    rows 为 *_scored.csv 的行（各榜同构）；fx_rate（USD→CNY）必需；
    ylabel 为纵轴名称（如「通用榜综合分」「文本榜综合分」）；fmt 为
    输出格式（默认 svg 供 README 内嵌；本地校对可传 png）。
    画幅与字号按 GitHub README ~780px 的显示宽度校准：字号相对放大、
    x 轴用手动刻度直标 ¥ 数值（不出现 10^n 或 USD 字样）。
    轴范围按数据自适应：x 下界给最便宜点留呼吸空间、上界保证延长线
    有去处；y 下界 floor(min/5)*5，上界 ceil(max/5)*5+2（顶部余量给
    最高点的标签）。
    """
    if not fx_rate:
        raise ValueError("fx_rate is required: the chart is priced in CNY")
    points = []
    for r in rows:
        try:
            price = float(r.get("Effective $/1M") or 0) * fx_rate
            score = float(r.get("Weighted Total") or 0)
        except ValueError:
            continue
        v_raw = r.get("Vision")
        has_v = (v_raw is True or str(v_raw).strip().lower() in ("yes", "true", "1"))
        if price > 0 and score > 0:
            points.append((price, score, r.get("Model") or "?", has_v))
    frontier = pareto_frontier(points)
    if not frontier:
        raise ValueError("no plottable models: empty frontier")

    fig, ax = plt.subplots(figsize=(8.4, 5.2))

    # x 范围随数据自适应：下界给最便宜点留呼吸空间；上界由「最后一个
    # ¥ 刻度 ×1.25」兜底，保证末位刻度不贴边被裁（¥50 案例），并让
    # 延长线有去处（预算再高也是前沿最后一个模型）
    min_p = min(pt[0] for pt in points)
    max_p = max(pt[0] for pt in points)
    x_lo = max(min_p * 0.68, 0.012)
    all_ticks = [0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100]
    x_hi_raw = max(max_p * 1.3, 30.0)
    ticks = [t for t in all_ticks if x_lo <= t <= x_hi_raw]
    x_hi = max(ticks[-1] * 1.25, max_p * 1.15)
    ticks = [t for t in all_ticks if x_lo <= t <= x_hi]
    all_scores = [pt[1] for pt in points]
    y_lo = math.floor(min(all_scores) / 5) * 5
    y_hi = math.ceil(max(all_scores) / 5) * 5 + 2

    # 非前沿点：按是否具备 Vision 区分形状（实心圆点 vs 纯文本三角）
    v_pts = [pt for pt in points if pt[3]]
    t_pts = [pt for pt in points if not pt[3]]
    if v_pts:
        ax.scatter([pt[0] for pt in v_pts], [pt[1] for pt in v_pts],
                   s=22, color="#b9bfc8", marker="o", alpha=0.45, linewidths=0, zorder=1,
                   label="支持视觉 all (vision)")
    if t_pts:
        ax.scatter([pt[0] for pt in t_pts], [pt[1] for pt in t_pts],
                   s=22, color="#9ea6b3", marker="^", alpha=0.55, linewidths=0, zorder=1,
                   label="纯文本 all (text-only)")

    # 前沿阶梯：线下淡填充标记「被支配区」，延长到 x 上界（预算再高
    # 也是最后一个模型）；线上加深红点 + 白描边提升质感
    fx_p = [pt[0] for pt in frontier]
    scores = [pt[1] for pt in frontier]
    step_x = fx_p + [x_hi]
    step_y = scores + [scores[-1]]
    ax.fill_between(step_x, step_y, y_lo, step="post",
                    color="#d62728", alpha=0.045, linewidths=0, zorder=1.5)
    ax.step(step_x, step_y, where="post", color="#d62728",
            linewidth=2.4, zorder=2, label="最优选择前沿 best choice")

    # 前沿点散点：按视觉能力区分圆点与三角
    f_v = [pt for pt in frontier if len(pt) > 3 and pt[3]]
    f_t = [pt for pt in frontier if len(pt) > 3 and not pt[3]]
    if f_v:
        ax.scatter([pt[0] for pt in f_v], [pt[1] for pt in f_v], s=65, color="#d62728",
                   marker="o", edgecolor="white", linewidth=0.9, zorder=3)
    if f_t:
        ax.scatter([pt[0] for pt in f_t], [pt[1] for pt in f_t], s=75, color="#d62728",
                   marker="^", edgecolor="white", linewidth=0.9, zorder=3)
    if not f_v and not f_t:
        ax.scatter(fx_p, scores, s=60, color="#d62728",
                   edgecolor="white", linewidth=0.9, zorder=3)

    ax.set_xscale("log")
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"¥{t:g}" for t in ticks], fontsize=10.5)
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.set_yticks(range(math.ceil(min(all_scores) / 5) * 5,
                        math.ceil(max(all_scores) / 5) * 5 + 1, 5))
    ax.set_xlabel("实际等效价 / 1M tokens（¥，对数刻度）", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, which="major", alpha=0.25)
    # 对数轴的 minor 网格帮助读 2~5 之间的档位；仅 x 轴（y 为线性）
    ax.xaxis.grid(True, which="minor", alpha=0.12, linewidth=0.5)
    ax.tick_params(axis="y", labelsize=10.5)
    ax.legend(fontsize=10, loc="lower right", frameon=False)
    # 左上角轻引导：不占图例位，浅灰斜体随数据而不喧宾
    ax.annotate("← 越靠左上，每 1 元换到的能力越高",
                xy=(0.015, 0.975), xycoords="axes fraction",
                fontsize=9, style="italic", color="#8a9099",
                ha="left", va="top", zorder=4)
    # 标注布局依赖最终坐标变换，必须在所有轴设置与 tight_layout 之后
    fig.tight_layout()
    _label_frontier(ax, frontier)
    fig.savefig(out_path, format=fmt)
    plt.close(fig)
    return [(pt[0], pt[1], pt[2]) for pt in frontier]
