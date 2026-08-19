#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成产品锁定件：meansights 标记 + 字标 ｜ HR AI Learning Agent（全部转成矢量轮廓）。

为什么要这个脚本，而不是用 CSS 拼一行文字：
页面上原来是「字标 SVG（Geist 轮廓）+ 系统字体写的描述词」，两种字体并排——
字形、字重、字距都不是一家的，放大看很明显。这里让描述词也走 Geist、也转成轮廓，
出来的整块跟主版严格同源，而且不依赖使用者机器上装没装字体。

刻意不改 ~/Desktop/铭曦 logo/_源文件/build_logo.py：
那是公司品牌的权威源，它重跑时会清空 01–06 编号目录。产品专用的衍生件放在产品仓库里，
公司资产和产品资产分开，谁也不会覆盖谁。

遵守 brand/使用说明.md 的两条硬规矩：
  ①渐变版只在浅底 24px 以上用 → 这里一律用主版纯色，不上渐变
  ②青绿全局只出现一处 → 青绿只留给标记的第四根光柱，描述词一律走石墨灰

用法（依赖 fontTools，见 .venv-brand）：
    .venv-brand/bin/python scripts/build_product_lockup.py
"""
import os
import sys

from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.expanduser("~/Desktop/铭曦 logo/_源文件/Geist.ttf")
OUT_DIR = os.path.join(ROOT, "frontend", "brand")

# ── 品牌常量（与 build_logo.py 保持一致，改这里等于改品牌，别随手动）──
INK = "#1E2226"
TEAL = "#0FB2B8"
WORD = "meansights"
SPLIT = 4                 # "mean" 用主字重，"sights" 用细字重
W_MAIN, W_LIGHT = 550, 300
TRACKING = 0.016          # 字标字距 +16‰

BARS = [(8, 28, 28), (21, 40, 16), (34, 28, 28)]   # x, y, 高
GLOW = (47, 4, 52)
BAR_W, RX, BASELINE = 8, 1.4, 56.0
EM_IN_MARK_UNITS = 64 * 28 / 46          # 字标字号换算成标记网格单位 ≈ 38.96
GAP_IN_MARK_UNITS = 64 * 12 / 46 + 9     # 光柱右缘 → 字标起笔 ≈ 25.70

# ── 描述词（产品层，不属于公司品牌）──
DESC = "HR AI Learning Agent"
DESC_WEIGHT = 400         # 比字标主字重(550)轻，读起来是副信息不是并列品牌
DESC_TRACKING = 0.022     # 含大写，字距比字标略松才透气
DESC_OPACITY = "0.46"     # 石墨灰的浅色版；不引入新颜色，也不碰青绿
# 分隔竖线。⚠️ 宽度按标记网格单位算：导航栏把 58.311 单位压到 28px，缩放比 0.48，
# 所以 1 单位只有 0.48px——不足一个 CSS 像素，会被反锯齿糊掉甚至消失。2.08 单位才等于 1px。
DIV_OPACITY = "0.22"
DIV_WIDTH = 2.1           # ≈1px @ 导航栏尺寸
DIV_HEIGHT_RATIO = 0.86   # 相对描述词大写高度，别顶满

_cache = {}


def inst(weight):
    if weight not in _cache:
        f = TTFont(FONT_PATH)
        _cache[weight] = instancer.instantiateVariableFont(
            f, {"wght": weight}, inplace=False)
    return _cache[weight]


def _ntos(v):
    s = f"{float(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0", "-") else s


def fmt(v):
    s = f"{float(v):.3f}".rstrip("0").rstrip(".")
    return s or "0"


def build_text(text, em, weights, tracking):
    """把一串字转成轮廓。返回 (每段 path, 总宽, bbox)。相邻同字重合并成一个 path。"""
    upem = inst(weights[0])["head"].unitsPerEm
    scale = em / upem
    track = tracking * em
    x, runs, cur, cur_w, bbox = 0.0, [], [], weights[0], None

    for i, ch in enumerate(text):
        w = weights[i]
        font = inst(w)
        gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
        if ord(ch) not in cmap:               # 空格等直接推进笔位
            x += em * 0.28 + track
            continue
        gname = cmap[ord(ch)]
        tf = Transform(scale, 0, 0, -scale, x, 0)
        if w != cur_w:
            runs.append((" ".join(cur), cur_w))
            cur, cur_w = [], w
        pen = SVGPathPen(gs, ntos=_ntos)
        gs[gname].draw(TransformPen(pen, tf))
        if pen.getCommands():
            cur.append(pen.getCommands())
        bp = BoundsPen(gs)
        gs[gname].draw(TransformPen(bp, tf))
        if bp.bounds:
            bbox = bp.bounds if bbox is None else (
                min(bbox[0], bp.bounds[0]), min(bbox[1], bp.bounds[1]),
                max(bbox[2], bp.bounds[2]), max(bbox[3], bp.bounds[3]))
        x += hmtx[gname][0] * scale + track

    runs.append((" ".join(cur), cur_w))
    return runs, x - track, bbox


def mark_body(gid):
    out = []
    for x, y, h in BARS:
        out.append(f'  <rect x="{x}" y="{y}" width="{BAR_W}" height="{h}" '
                   f'rx="{RX}" fill="{INK}"/>')
    gx, gy, gh = GLOW
    out.append(f'  <rect x="{gx}" y="{gy}" width="{BAR_W}" height="{gh}" '
               f'rx="{RX}" fill="url(#{gid})"/>')
    return "\n".join(out) + "\n"


def build(desc_ratio: float, out_name: str, desc_opacity: str = DESC_OPACITY,
          div_w: float = DIV_WIDTH, div_op: str = DIV_OPACITY,
          div_ratio: float = DIV_HEIGHT_RATIO):
    """desc_ratio: 描述词字号相对字标的比例。1.0 = 完全同字号。
    desc_opacity: 石墨灰的浓度。太淡会读不出来，太浓会跟品牌名争主次。"""
    em = EM_IN_MARK_UNITS
    wm_runs, wm_w, wm_bb = build_text(
        WORD, em, [W_MAIN] * SPLIT + [W_LIGHT] * (len(WORD) - SPLIT), TRACKING)
    wm_x = 55.0 + GAP_IN_MARK_UNITS          # 光柱右缘 = 55

    d_em = em * desc_ratio
    d_runs, d_w, d_bb = build_text(
        DESC, d_em, [DESC_WEIGHT] * len(DESC), DESC_TRACKING)

    gap = GAP_IN_MARK_UNITS * 0.62           # 字标 → 竖线 → 描述词，两侧各留这么多
    div_x = wm_x + wm_w + gap
    d_x = div_x + gap

    # 竖线高度贴着描述词的大写高度，两端各收一点，别顶满
    cap_h = -d_bb[1]                          # bbox 在翻转坐标系里，yMin 是升部（负）
    div_h = cap_h * div_ratio
    div_top = BASELINE - cap_h * 0.5 - div_h * 0.5   # 相对大写高度居中，不吊在基线上

    top = min(4.0, BASELINE + wm_bb[1], BASELINE + d_bb[1])
    bottom = max(BASELINE, BASELINE + wm_bb[3], BASELINE + d_bb[3])
    left, right = 8.0, d_x + d_w
    W, H = right - left, bottom - top

    gid = "pGlow"
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" '
         f'viewBox="{fmt(left)} {fmt(top)} {fmt(W)} {fmt(H)}" '
         f'width="{fmt(W)}" height="{fmt(H)}" role="img" '
         f'aria-label="meansights — {DESC}">\n'
         f'  <title>meansights — {DESC}</title>\n'
         f'  <defs>\n'
         f'    <linearGradient id="{gid}" x1="0" y1="1" x2="0" y2="0">\n'
         f'      <stop offset="0" stop-color="{TEAL}" stop-opacity="1"/>\n'
         f'      <stop offset="0.5" stop-color="{TEAL}" stop-opacity="0.88"/>\n'
         f'      <stop offset="1" stop-color="{TEAL}" stop-opacity="0"/>\n'
         f'    </linearGradient>\n  </defs>\n')
    s += mark_body(gid)
    s += f'  <g transform="translate({fmt(wm_x)} {fmt(BASELINE)})">\n'
    for d, _w in wm_runs:
        if d:
            s += f'    <path d="{d}" fill="{INK}"/>\n'
    s += "  </g>\n"
    s += (f'  <rect x="{fmt(div_x)}" y="{fmt(div_top)}" width="{fmt(div_w)}" '
          f'height="{fmt(div_h)}" rx="{fmt(div_w/2)}" '
          f'fill="{INK}" fill-opacity="{div_op}"/>\n')
    s += f'  <g transform="translate({fmt(d_x)} {fmt(BASELINE)})">\n'
    for d, _w in d_runs:
        if d:
            s += (f'    <path d="{d}" fill="{INK}" '
                  f'fill-opacity="{desc_opacity}"/>\n')
    s += "  </g>\n</svg>\n"

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, out_name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(s)
    return path, W, H, d_em


if __name__ == "__main__":
    if not os.path.exists(FONT_PATH):
        sys.exit(f"找不到字体：{FONT_PATH}\n（品牌源文件夹被移动过？）")
    if "--divider" in sys.argv:   # 调竖线时用
        for w_, op_, tag in ((1.0, "0.18", "a-现状"), (2.1, "0.22", "b-1px"),
                             (3.0, "0.26", "c-1.4px"), (2.1, "0.40", "d-1px深")):
            p, W, H, em = build(0.84, f"_div-{tag}.svg", "0.58", w_, op_)
            print(f"✓ {tag}: 宽 {w_} 单位 = {w_*28/58.311:.2f}px · 浓度 {op_}")
        sys.exit(0)
    p, W, H, em = build(0.84, "lockup-product.svg", "0.58")
    print(f"✓ lockup-product.svg  {W:.0f}×{H:.0f} 单位 · 字号 84% · "
          f"描述词浓度 0.58 · 竖线 {DIV_WIDTH} 单位 · {os.path.getsize(p)/1024:.0f} KB")
