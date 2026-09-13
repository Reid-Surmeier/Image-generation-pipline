"""Render the IE7 new-tab animation deterministically.

Base: the 1600x240 tab-region crop of muse-runs/ie7-toolbar-flat-f variation-1 (native res).
Second tab, stub and seam are drawn as anti-aliased geometry (4x supersample) with the
source's outline colour/width; only the page icon and label glyphs come from Muse.

Timeline (24 fps, 6 s): hold; stub pressed 100 ms; stub grows into the tab over 350 ms
(ease-out) while the new stub slides out behind it; "Connecting..." held; one-frame swap
to "Blank Page"; hold.  The grow is the Chrome-1.0-era idiom, not IE7's hard cut.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
import os
MODE = os.environ.get("MODE", "grow")  # grow | slide
GROW_MS = int(os.environ.get("GROW_MS", "400"))
OUT = ROOT / "edit-work" / ("anim-frames" if MODE == "grow" else f"anim-frames-{MODE}")
OUT.mkdir(exist_ok=True)
FPS, DUR = 24, 6.0
B = 4  # pixel block size of the source outlines (4 px, stepped slants)
OUTLINE = (130, 132, 136)
OUTLINE_W = 4
STUB_FILL = (247, 239, 244)
STUB_PRESSED = (228, 218, 226)
PER = 35  # stripe period
TAB_DX = 504  # second tab = first tab shifted right (top-left 334 -> 838)

src = Image.open(ROOT / "references" / "tab-region.png").convert("RGB")
a = np.array(src)
H, W, _ = a.shape


def poly_mask(pts, size=(W, H)):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return np.array(m) > 0


# base: source with the old stub erased by stripe-aligned background (tab1 untouched)
tab1_m = poly_mask([(279, 198), (331, 69), (831, 69), (831, 96), (795, 198)])
stub_erase = poly_mask([(776, 200), (813, 84), (955, 84), (921, 200)]) & ~tab1_m
base = a.copy()
base[stub_erase] = np.roll(a, -10 * PER, axis=1)[stub_erase]

# geometry (region coords).  6-vertex parametrisation shared by stub and tab so they lerp.
# order: top-left, top-right, right-vertical-bottom, bottom-right, bottom-left, left-vertical-bottom
# measured: tab1's right edge runs (827,74) -> (788,199), no vertical segment; the stub's left
# edge sits on that same line, so tab2's left edge and the stub share one divider.
EDGE_TOP, EDGE_BOT = (827, 74), (789, 196)
# measured stub: top outline rows 96-99, right slant 948@96 -> 910@196, bottom outline = bar border rows 196-199
STUB0 = [(820, 96), (948, 96), (948, 96), (910, 196), (788, 196), (820, 96)]
TAB2 = [(827, 73), (1321, 73), (1321, 73), (1283, 196), (789, 196), (827, 73)]
STUB_SHAPE = [(0, 0), (128, 0), (128, 0), (90, 100), (-32, 100), (0, 0)]  # relative to top-left at y=96
stub_interior = ndi.binary_erosion(poly_mask([(round(x), round(y)) for x, y in STUB0]), iterations=5)
# whiten tab1's own stepped right-edge pixels (left side of the line); the divider is redrawn on the grid
edge_band = poly_mask([(817, 77), (831, 77), (792, 200), (778, 200)])
base[edge_band] = 255


def lerp_pts(p, q, t):
    return [(p[i][0] + (q[i][0] - p[i][0]) * t, p[i][1] + (q[i][1] - p[i][1]) * t) for i in range(len(p))]


def draw_shape(layer, pts, fill, bottom_line=True):
    """Filled polygon with a one-block outline on the block grid: stepped edges like the source.
    Tabs are open at the bottom (the source tab has no bottom line and covers the bar border);
    the stub's bottom line is the bar border itself."""
    d = ImageDraw.Draw(layer)
    P = [(round(x / B), round(y / B)) for x, y in pts]
    fillP = P if bottom_line else [P[0], P[1], P[2], (P[3][0], P[3][1] + 1), (P[4][0], P[4][1] + 1), P[5]]
    d.polygon(fillP, fill=fill + (255,))
    d.line([P[1], P[0]], fill=OUTLINE + (255,), width=1)  # top
    slant(d, P[2], P[3]); slant(d, P[5], P[4])  # right, left
    if bottom_line:
        d.line([P[4], P[3]], fill=OUTLINE + (255,), width=1)


def slant(d, p, q):
    """One-block-wide stepped slant whose runs overlap by a block at each step, like the source outline."""
    d.line([p, q], fill=OUTLINE + (255,), width=1)
    d.line([(p[0], p[1] + 1), (q[0], q[1] + 1)], fill=OUTLINE + (255,), width=1)


def draw_divider(layer):
    d = ImageDraw.Draw(layer)
    slant(d, (round(EDGE_TOP[0] / B), round(EDGE_TOP[1] / B)), (round(EDGE_BOT[0] / B), round(EDGE_BOT[1] / B)))


def composite_rgba(rgb, layer):
    big = layer.resize((W, H), Image.NEAREST)
    out = Image.alpha_composite(Image.fromarray(rgb).convert("RGBA"), big).convert("RGB")
    return np.array(out)


# content layers (white bg) from Muse glyphs, positioned like the first tab's flag + label
dark = a.max(2) < 110
ys, xs = np.where(dark[:, 452:786]); WL_top, WL_base = int(ys.min()), int(ys.max())
flag = (a.max(2).astype(int) - a.min(2)) > 80
ys, xs = np.where(flag[:, 300:440]); FL = (300 + int(xs.min()), int(ys.min()), 300 + int(xs.max()), int(ys.max()))


def glyph_crop(img, x0, y0, x1, y1, thr=110):
    m = np.array(img.crop((x0, y0, x1, y1)).convert("RGB")); d = m.max(2) < thr; ys, xs = np.where(d)
    return img.crop((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))


def icon_crop(img, x0, y0, x1, y1):
    m = np.array(img.crop((x0, y0, x1, y1)).convert("RGB")).astype(int); d = m.max(2) < 225; ys, xs = np.where(d)
    return img.crop((x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1))


con = Image.open(ROOT / "edit-work" / "connecting-01.output.png").convert("RGB")
bl = Image.open(ROOT / "edit-work" / "blank-01.output.png").convert("RGB")
gC = glyph_crop(con, 2050, 290, 2140, 450); gW = glyph_crop(src, 452, 90, 503, 170)
S = gW.size[1] / gC.size[1]


def content_layer(words, muse):
    im = Image.new("RGB", (W, H), (255, 255, 255))
    ic = icon_crop(con, 1830, 285, 2000, 450); h = FL[3] - FL[1] + 1  # one icon for both states
    ic = ic.resize((round(ic.size[0] * h / ic.size[1]), h), Image.LANCZOS)
    im.paste(ic, (FL[0] + TAB_DX + 8, FL[1]))
    x = 452 + TAB_DX
    for (wx0, wx1) in words:
        g = glyph_crop(muse, wx0, 290, wx1, 450)
        gs = g.resize((max(1, round(g.size[0] * S)), max(1, round(g.size[1] * S))), Image.LANCZOS)
        gm = np.array(gs.convert("RGB")).max(2) < 110; rows = gm.sum(1)
        b = max(i for i, v in enumerate(rows) if v >= 0.3 * rows.max())
        im.paste(gs, (x, WL_base - b)); x += gs.size[0] + 22
    return np.array(im).astype(np.float32)


CONNECTING = content_layer([(2050, 2790)], con)
BLANK = content_layer([(2020, 2330), (2500, 2790)], bl)


def ease_out(t):
    return 1 - (1 - t) ** 3


def render(t):
    """Region image at time t (seconds)."""
    T_PRESS, T_GROW0, T_SWAP0 = 1.5, 1.6, 2.9  # seconds
    T_GROW1 = T_GROW0 + GROW_MS / 1000
    if t < T_PRESS:
        return a  # exact source frame
    if t < T_GROW0:  # pressed: tint the source stub's face in place, no geometry redrawn
        out = a.copy(); out[stub_interior] = STUB_PRESSED
        return out
    layer = Image.new("RGBA", (W // B, H // B), (0, 0, 0, 0))
    s = ease_out(min(1.0, (t - T_GROW0) / (T_GROW1 - T_GROW0)))
    if MODE == "slide":
        # full-size tab translates out from behind the first tab; the stub rides on its right edge
        shift = -(TAB2[1][0] - TAB2[0][0]) * (1 - s)
        pts = [(x + shift, y) for x, y in TAB2]
        fill = (255, 255, 255)
    else:
        pts = lerp_pts(STUB0, TAB2, s)
        fill = tuple(round(STUB_FILL[i] + (255 - STUB_FILL[i]) * s) for i in range(3))
    right_top_x = pts[1][0]
    stub2 = [(right_top_x - 7 + dx, 96 + dy) for dx, dy in STUB_SHAPE]
    draw_shape(layer, stub2, STUB_FILL)  # behind
    draw_shape(layer, pts, fill, bottom_line=(MODE != "slide" and s < 0.5))
    draw_divider(layer)  # tab1's edge stays on top: one shared divider, no wedge
    rgb = composite_rgba(base, layer)
    # contents, clipped to the growing interior, fading in over the second half of the grow
    alpha = 0.0 if s < 0.5 else min(1.0, (s - 0.5) / 0.5)
    content = BLANK if t >= T_SWAP0 else CONNECTING  # hard swap, as IE7 did
    if alpha > 0:
        interior = ndi.binary_erosion(poly_mask([(round(x), round(y)) for x, y in pts]), iterations=6)
        m = (interior.astype(np.float32) * alpha)[..., None]
        rgb = (rgb.astype(np.float32) * (1 - m) + content * m).round().astype(np.uint8)
    if MODE == "slide":
        rgb[tab1_m] = a[tab1_m]  # first tab stays in front while the new tab emerges
    return rgb


if __name__ == "__main__":
    full = Image.open("/home/reidsurmeier/muse-runs/ie7-toolbar-flat-f/final/variation-1.png").convert("RGB")
    n = int(FPS * DUR)
    for i in range(n):
        reg = Image.fromarray(render(i / FPS))
        f = full.copy(); f.paste(reg, (1330, 180))
        c = f.crop((1345, 0, 4480, 560)); sc = 1680 / c.size[0]
        c = c.resize((1680, round(560 * sc)), Image.LANCZOS)
        canvas = Image.new("RGB", (1680, 720), (255, 255, 255)); canvas.paste(c, (0, (720 - c.size[1]) // 2))
        canvas.save(OUT / f"f{i:04d}.png")
        if i in (0, 38, 40, 42, 44, 46, 60, 66, 143):
            reg.save(OUT / f"region-{i:04d}.png")
    print("frames", n)
