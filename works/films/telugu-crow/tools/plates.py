#!/usr/bin/env python3
"""Paint the film's sets the way a picture-book illustrator would -- with the drawing skill's engine.

The film used to draw its world with flat vector fills in Skia. This module paints each stage
instead, using `claude-drawing-skill`'s grainy-picture-book engine (numpy gouache: dry, chalky
brushes, paper tooth showing through, no ink outlines), and writes them as plates the renderer
blits under the animated cut-outs.

    python3 tools/plates.py --out assets/plates

Plates are painted in design pixels (1080 x 1920 frame) but cover a rect larger than any camera
move inside that stage, so a pan never runs off the paint.
"""
import argparse
import pathlib
import sys
import time

sys.path.insert(0, "/tmp/sk/claude-drawing-skill/lib")

import numpy as np                                                        # noqa: E402
from PIL import Image                                                     # noqa: E402
from grainbook import PAINTS, GrainBook, Region, _resample, _smooth, hexc   # noqa: E402

# ---------------------------------------------------------------- world geometry (design pixels)
PLATE = (-150, -700, 1380, 3160)        # x0, y0, w, h -- covers every framing of every stage
PX0, PY0, PW, PH = PLATE
HORIZON = 1180
SW, SH = 1080, 1920

PAL = dict(
    hill_far="#8fae8a", hill_near="#6a9140", ground_top="#eaaa38", ground_lo="#d2a56c",
    crack="#8c5a37", ink="#241812", pot="#bc5a2c", pot_dark="#922814", pot_light="#e0714f",
    stone="#8f8a86", stone_dark="#5f5b58", water="#4c8db0", white="#fff8ea",
    dune="#c98f52", sky_high="#7cb9ee", sky_mid="#bcdcf2", sky_low="#fbf0d6",
)
PAINTS.update(PAL)             # so the palette names resolve inside the skill's engine


# ---------------------------------------------------------------- helpers: design coords -> plate px
def px(x):
    return float(x) - PX0


def py(y):
    return float(y) - PY0


def poly(g, pts):
    """region from design-space polygon points"""
    return g.poly([(px(x), py(y)) for x, y in pts], smooth=True)


def ridge(g, y, amp, period, seed, slope=0.0):
    xs, ys = g.wavy(px(-120), px(SW + 160), py(y), amp, period, seed=seed, slope=slope)
    return g.below(xs, ys)


def blobr(g, x, y, rx, ry, rough=0.06, seed=None):
    return g.blob(px(x), py(y), rx, ry, rough=rough, seed=seed)


def stroke(g, pts, w0, w1, colour, angle=-25, **kw):
    """a brush stroke of our own: resample a design-space path, dilate it, lay paint in it.

    The skill's `tube` caps at one width per path; a crow's wing, a pot's rim and a crack all need
    a stroke that thins out, so this builds the mask directly and hands it to the dry brush.
    """
    P = _smooth(np.array([(px(x), py(y)) for x, y in pts], np.float32))
    P = _resample(P, 2.0)
    H, W = g.H, g.W
    m = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    for i in range(len(P)):
        x, y = P[i]
        t = i / max(1, len(P) - 1)
        r = w0 + (w1 - w0) * (t ** 0.85)
        y0, y1 = int(max(0, y - r - 2)), int(min(H, y + r + 3))
        x0, x1 = int(max(0, x - r - 2)), int(min(W, x + r + 3))
        if y1 <= y0 or x1 <= x0:
            continue
        sy, sx = yy[y0:y1, x0:x1], xx[y0:y1, x0:x1]
        d = np.sqrt((sy - y) ** 2 + (sx - x) ** 2)
        m[y0:y1, x0:x1] = np.maximum(m[y0:y1, x0:x1], np.clip(r - d + 0.5, 0, 1))
    g.fill(Region(0, 0, m), colour, angle=angle, streak=0.45, dry=0.28, edge=0.7, **kw)
    return Region(0, 0, m)


# ---------------------------------------------------------------- the sky, shared by every stage
def sky(g, hi, mid, lo, seed=3):
    g.bands(g.full(), [hi, hi, mid], [py(-700), py(700), py(HORIZON - 150)], angle=-5, wave=26,
            period=1100, dry=0.28, edge=2.2, soft=2.6, streak=0.35)
    g.bands(g.below(*g.wavy(px(-120), px(SW + 160), py(HORIZON - 210), 18, 900, seed=seed + 7)),
            [lo, "apricot"], [py(HORIZON - 90)], angle=-4, wave=16, dry=0.45, alpha=0.75,
            edge=3.0, soft=3.0)
    # the heat sits low: one broad warm wash above the horizon, painted as a band so it reads as
    # air rather than as a cloud of dirt
    g.bands(g.below(*g.wavy(px(-120), px(SW + 160), py(HORIZON - 260), 22, 800, seed=seed + 1)),
            ["cream", "apricot"], [py(HORIZON - 120)], angle=-4, wave=14, dry=0.5, alpha=0.45,
            edge=3.2, soft=3.2, streak=0.25)


def sun(g, x, y, r, colour="window", halo=True):
    if halo:
        g.glow(g.ellipse(px(x), py(y), r * 2.6, r * 2.6), "lamp", strength=0.5)
    g.fill(g.ellipse(px(x), py(y), r, r), colour, angle=-30, streak=0.5, dry=0.2, edge=1.2)
    sc = g.ellipse(px(x - r * 0.25), py(y - r * 0.3), r * 0.55, r * 0.5)
    g.scumble(sc, "cream", angle=-30, cover=0.55)
    # a few rays, drawn not filled
    for a in (-2.5, -2.1, -1.75, -1.4, -1.05, -0.7):
        g.crayon([(px(x + np.cos(a) * r * 1.35), py(y + np.sin(a) * r * 1.35)),
                  (px(x + np.cos(a) * r * 1.75), py(y + np.sin(a) * r * 1.75))],
                 3.4, "orange_light", taper=(0.3, 0.5), wobble=0.6, alpha=0.8)


def cloud(g, x, y, w, seed=None):
    for i, (dx, dy, k) in enumerate(((0, 0, 1.0), (-0.42 * w, 0.12 * w, 0.62), (0.46 * w, 0.10 * w, 0.55),
                                     (-0.16 * w, -0.24 * w, 0.62), (0.2 * w, -0.2 * w, 0.56))):
        g.fill(blobr(g, x + dx, y + dy, w * 0.5 * k, w * 0.30 * k, rough=0.10, seed=(seed or 0) + i),
               "white", angle=-8, streak=0.3, dry=0.25, edge=2.2, alpha=0.85)
    g.scumble(blobr(g, x, y + w * 0.10, w * 0.42, w * 0.14, seed=(seed or 0) + 9), "ice", cover=0.35)


def hills(g, dry=0.4, seed=11, horizon=HORIZON):
    far = ridge(g, horizon - 210, 46, 1100, seed)
    g.fill(far, "sage", angle=-6, streak=0.42, dry=0.3, edge=3.0, mottle=0.22)
    g.fill(ridge(g, horizon - 150, 34, 760, seed + 3), "olive", angle=-6, streak=0.4,
           dry=0.45, edge=2.6, alpha=0.7)
    g.scumble(far, "olive", angle=-6, cover=0.24)
    near = ridge(g, horizon - 74, 40, 620, seed + 1, slope=0.01)
    g.fill(near, "moss", angle=-5, streak=0.45, dry=0.26, edge=3.0, mottle=0.26)
    g.fill(ridge(g, horizon - 34, 26, 480, seed + 4), "green", angle=-5, streak=0.4,
           dry=0.45, edge=2.4, alpha=0.6)
    g.scumble(near, "green", angle=-5, cover=0.26)
    # a sunlit rim along each crest -- that is where drought reads, not in a haze band
    for rg, col in ((far, "cream"), (near, "mustard")):
        xs = np.linspace(px(-100), px(SW + 140), 60)
        ys = np.array([rg.box[0] + 3 for _ in xs])
        g.crayon(list(zip(xs, ys)), 3.2, col, taper=(0.2, 0.2), wobble=0.8, alpha=0.55)


def ground(g, dry=0.8, seed=3, horizon=HORIZON):
    g.fill(g.below(*g.wavy(px(-120), px(SW + 160), py(horizon), 20, 900, seed=seed)),
           "olive", angle=-3, streak=0.45, dry=0.3, edge=2.4, mottle=0.18, alpha=0.85)
    g.bands(g.below(*g.wavy(px(-120), px(SW + 160), py(horizon + 30), 20, 900, seed=seed + 9)),
            ["mustard", "apricot"], [py(horizon + 150)], angle=-3, wave=18, dry=0.5,
            edge=2.6, alpha=0.8, streak=0.4)
    g.bands(g.below(*g.wavy(px(-120), px(SW + 160), py(horizon + 240), 18, 1200, seed=seed + 1)),
            ["apricot", "kraft", "dune", "brown_light"],
            [py(horizon + 300), py(horizon + 640), py(horizon + 1020)],
            angle=-2, wave=22, dry=0.45, edge=2.0, streak=0.5, alpha=0.9)
    # green scrub clinging to the verge: the drought is a dry field, not a desert
    r0 = np.random.default_rng(seed + 17)
    for _ in range(16):
        x, y = r0.uniform(-40, SW + 40), horizon + r0.uniform(-30, 420)
        w = r0.uniform(60, 190) * (1 + 0.5 * (1 - (y - horizon) / 420))
        g.fill(g.blob(px(x), py(y), w * 0.5, w * 0.16, rough=0.22, seed=abs(int(x)) + 7),
               "olive" if r0.random() < 0.6 else "moss", angle=-8, dry=0.55, edge=2.4, alpha=0.75)
    g.mottle(g.below(*g.wavy(px(-120), px(SW + 160), py(horizon + 60), 20, 800, seed=seed + 2)),
             "orange_light", scale=120, cover=0.16, alpha=0.28, angle=-2, streak=0.3)
    # the lip where ground meets sky
    g.crayon([(px(-120), py(horizon)), (px(SW + 160), py(horizon))], 3.0, "cream",
             taper=(0.1, 0.1), wobble=0.4, alpha=0.5)
    if dry < 0.5:
        return
    # cracked mud: long cracks that branch, drawn with the crayon so they wobble like the real thing
    r = np.random.default_rng(seed + 5)
    for _ in range(11):
        x, y = r.uniform(-40, SW + 40), horizon + r.uniform(60, 900)
        pts = [(x, y)]
        for _ in range(4):
            x += r.uniform(-70, 70)
            y += r.uniform(18, 54)
            pts.append((x, y))
        g.crayon([(px(a), py(b)) for a, b in pts], 2.2, "crack", taper=(0.4, 0.12), wobble=1.0, alpha=0.30)
        if r.random() < 0.6:
            g.crayon([(px(pts[1][0]), py(pts[1][1])),
                      (px(pts[1][0] + r.uniform(-90, 90)), py(pts[1][1] + r.uniform(20, 60)))],
                     1.5, "crack", taper=(0.3, 0.08), wobble=0.9, alpha=0.22)
    # pebbles, tufts and dust
    for _ in range(90):
        x, y = r.uniform(-40, SW + 40), horizon + r.uniform(40, 700)
        g.fill(g.ellipse(px(x), py(y), r.uniform(2.5, 5.0), r.uniform(2.0, 3.6)),
               "brown_light" if r.random() < 0.5 else "kraft", angle=0, dry=0.2, edge=0.6, alpha=0.8)
    for _ in range(26):
        x, y = r.uniform(-40, SW + 40), horizon + r.uniform(60, 640)
        for k in range(3):
            g.crayon([(px(x + k * 4 - 4), py(y)), (px(x + k * 7 - 6 + r.uniform(-6, 6)), py(y - r.uniform(16, 40)))],
                     1.6, "olive", taper=(0.1, 0.6), wobble=1.4, alpha=0.7)


def thirsty_tree(g, x, y, h, seed=21):
    g.shadow(g.ellipse(px(x + 18), py(y + 4), h * 0.24, h * 0.05), "shadow", depth=0.55, angle=0)
    g.crayon([(px(x), py(y)), (px(x - 10), py(y - h * 0.45)), (px(x + 6), py(y - h))],
             9.0, "wood_dark", taper=(1.0, 0.25), wobble=1.0)
    r = np.random.default_rng(seed)
    for i in range(7):
        t = 0.42 + 0.075 * i
        bx = x + 6 * (t - 0.5) * 2
        by = y - h * t
        ang = -2.3 + 0.35 * i + r.uniform(-0.2, 0.2)
        ln = h * r.uniform(0.14, 0.26)
        g.crayon([(px(bx), py(by)), (px(bx + np.cos(ang) * ln), py(by + np.sin(ang) * ln))],
                 3.4, "wood_dark", taper=(0.8, 0.1), wobble=1.2)
    for i in range(14):
        bx = x + r.uniform(-h * 0.16, h * 0.16)
        by = y - h * r.uniform(0.62, 1.0)
        g.fill(blobr(g, bx, by, r.uniform(9, 15), r.uniform(5, 8), rough=0.2, seed=seed + i),
               "olive" if i % 3 else "mustard", angle=-30, dry=0.5, edge=1.4, alpha=0.9)


def shrub(g, x, y, w, h, colour="moss", seed=5):
    for i in range(5):
        g.fill(blobr(g, x + (i - 2) * w * 0.19, y - h * 0.34 + (i % 2) * h * 0.1,
                     w * 0.24, h * 0.30, rough=0.16, seed=seed + i),
               colour, angle=-40, dry=0.4, edge=1.8, alpha=0.95)
    g.scumble(blobr(g, x - w * 0.1, y - h * 0.52, w * 0.3, h * 0.16, seed=seed + 9), "sage", cover=0.3)


# ---------------------------------------------------------------- the pot, painted
def pot(g, x, y, w, h, water=0.34, stones=28):
    """the clay pot as a painted solid: a tapered body with a raised rim, a water window and stones"""
    x0, x1 = x - w / 2, x + w / 2
    top, bot = y, y + h
    body = [(x0, top + 14), (x1, top + 14), (x1 - w * 0.10, bot - h * 0.02), (x0 + w * 0.10, bot - h * 0.02)]
    g.shadow(g.ellipse(px(x), py(bot + 6), w * 0.62, h * 0.045), "shadow", depth=0.7, angle=0)
    R = poly(g, body)
    g.fill(R, "pot", angle=-72, streak=0.5, dry=0.34, edge=2.2, mottle=0.22)
    # the shaded left flank and the lit right one, laid as their own dry passes
    g.fill(poly(g, [(x0, top + 20), (x0 + w * 0.16, top + 26), (x0 + w * 0.22, bot - 20), (x0 + w * 0.08, bot - 20)]),
           "pot_dark", angle=-80, streak=0.5, dry=0.5, edge=2.0, alpha=0.65)
    g.scumble(poly(g, [(x1 - w * 0.22, top + 30), (x1 - w * 0.05, top + 22),
                       (x1 - w * 0.12, bot - 40), (x1 - w * 0.3, bot - 60)]),
              "pot_light", angle=-75, cover=0.58)
    # two incised bands, plus the rim ring
    for yy, wd in ((top + h * 0.30, 4.0), (top + h * 0.62, 3.4)):
        g.crayon([(px(x0 + w * 0.13), py(yy)), (px(x1 - w * 0.11), py(yy - 6))], wd, "pot_dark",
                 taper=(0.3, 0.3), wobble=0.6, alpha=0.5)
    g.fill(g.ellipse(px(x), py(top + 8), w * 0.53, h * 0.055), "pot_dark", angle=-20, dry=0.3, edge=1.6)
    g.fill(g.ellipse(px(x), py(top + 2), w * 0.53, h * 0.05), "brown", angle=-20, dry=0.3, edge=1.6)
    # the mouth's dark inside
    g.fill(g.ellipse(px(x), py(top + 6), w * 0.47, h * 0.038), "coffee", angle=-20, dry=0.2, edge=1.4)
    # water in the window: a cool painted pool with ripple lines
    wl = bot - h * 0.045 - (h * 0.52) * water
    pool = poly(g, [(x0 + w * 0.15, wl), (x1 - w * 0.13, wl), (x1 - w * 0.16, bot - 22), (x0 + w * 0.18, bot - 22)])
    g.fill(pool, "water", angle=-10, streak=0.5, dry=0.3, edge=1.6, mottle=0.3)
    g.fill(poly(g, [(x0 + w * 0.16, wl + 10), (x1 - w * 0.14, wl + 10), (x1 - w * 0.15, wl + 24),
                    (x0 + w * 0.17, wl + 24)]), "ice", angle=-8, dry=0.4, edge=1.4, alpha=0.55)
    for i in range(3):
        yy = wl + 26 + i * 26
        g.crayon([(px(x - w * 0.2), py(yy)), (px(x + w * 0.16), py(yy - 3))], 2.0, "ice",
                 taper=(0.3, 0.3), wobble=1.0, alpha=0.45)
    # stones lying in the bottom
    r = np.random.default_rng(41)
    for i in range(stones):
        sx = x + r.uniform(-w * 0.34, w * 0.34)
        sy = bot - 26 - abs(sx - x) * 0.08 - r.uniform(0, 22)
        rr = r.uniform(9, 16)
        g.fill(blobr(g, sx, sy, rr, rr * 0.8, rough=0.14, seed=60 + i), "stone", angle=-25,
               dry=0.35, edge=1.2, alpha=0.95)
        g.scumble(blobr(g, sx + rr * 0.2, sy - rr * 0.25, rr * 0.5, rr * 0.34, seed=90 + i), "ice", cover=0.5)


# ---------------------------------------------------------------- one plate per stage
def paint(kind, out, seed=3):
    t0 = time.time()
    g = GrainBook(PW, PH, seed=seed)
    g.finish = None
    g.paper("cream", angle=-84)

    if kind == "field":
        sky(g, "sky_high", "sky_mid", "sky_low", seed)
        sun(g, 848, 268, 116)
        cloud(g, 250, 330, 220, seed=31)
        cloud(g, 690, 470, 150, seed=37)
        hills(g, seed=11)
        ground(g, dry=0.85, seed=3)
        thirsty_tree(g, 150, 1250, 470, seed=21)
        thirsty_tree(g, 1010, 1300, 300, seed=27)
        shrub(g, 60, 1420, 220, 180, "moss", seed=5)
        shrub(g, 1060, 1620, 200, 150, "olive", seed=8)

    elif kind == "pot":
        sky(g, "sky_high", "sky_mid", "sky_low", seed)
        sun(g, 862, 300, 96)
        cloud(g, 300, 400, 170, seed=33)
        hills(g, seed=13)
        ground(g, dry=0.7, seed=4)
        shrub(g, 40, 1500, 190, 150, "moss", seed=6)
        thirsty_tree(g, 1015, 1290, 260, seed=29)

    elif kind == "quiz":
        sky(g, "sky_mid", "sky_low", "cream", seed)
        sun(g, 872, 300, 78)
        hills(g, dry=0.2, seed=17)
        ground(g, dry=0.5, seed=6)
        shrub(g, 60, 1460, 180, 140, "sage", seed=9)
        shrub(g, 1040, 1540, 160, 130, "moss", seed=11)

    elif kind == "end":
        # the close: the same field at golden hour, wide and calm, room for the moral
        g.bands(g.full(), ["apricot", "apricot", "mustard", "cream"],
                [py(-700), py(380), py(800), py(HORIZON + 60)],
                angle=-4, wave=30, period=1200, dry=0.30, edge=2.0, soft=2.6)
        sun(g, 540, 720, 150, "window")
        cloud(g, 250, 380, 210, seed=53)
        cloud(g, 800, 300, 180, seed=59)
        far = ridge(g, HORIZON - 150, 30, 1000, 21)
        g.fill(far, "sage", angle=-6, streak=0.4, dry=0.35, edge=2.4)
        near = ridge(g, HORIZON - 60, 26, 700, 22, slope=0.01)
        g.fill(near, "olive", angle=-5, streak=0.45, dry=0.3, edge=2.4)
        ground(g, dry=0.35, seed=7)
        thirsty_tree(g, 130, 1270, 420, seed=31)
        shrub(g, 1000, 1400, 210, 170, "moss", seed=13)

    g.keep_stages = False
    img = Image.fromarray((np.clip(g.C, 0, 1) * 255 + 0.5).astype(np.uint8))
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / f"{kind}.jpg", quality=93, subsampling=0)
    import json
    meta_p = out / "plates.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    meta[kind] = dict(x=PX0, y=PY0, w=PW, h=PH)
    meta_p.write_text(json.dumps(meta, indent=1))
    print(f"{kind:6s} {img.size}  {time.time() - t0:5.1f}s")


def paper_tile(out, size=720):
    """the print stock the whole frame is pressed onto"""
    g = GrainBook(size, size, seed=91)
    g.paper("cream", angle=-80)
    img = Image.fromarray((np.clip(g.C, 0, 1) * 255 + 0.5).astype(np.uint8))
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / "paper.jpg", quality=90)
    print(f"paper  {img.size}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/plates")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    for kind in ("field", "pot", "quiz", "end"):
        paint(kind, out)
    paper_tile(out)


if __name__ == "__main__":
    main()
