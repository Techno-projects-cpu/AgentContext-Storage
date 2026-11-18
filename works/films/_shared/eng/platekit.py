"""Paint the two English ads' sets with the drawing skill's gouache engine (v2: value plan first).

Same medium as the crow film -- `grainbook` gypsum gouache: dry chalky brushes, paper tooth, no ink
outlines -- but these are ADVERTS, so each plate is built as three clear values (dark / mid / light)
with one warm light source, and everything else is a flat shape. No glow ellipses: a light pool is
painted as concentric low-alpha washes, which is what gouache actually does.

    python3 tools/plates.py --which zerovast --out assets/plates
    python3 tools/plates.py --which vignan   --out assets/plates
"""
import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, "/tmp/sk/claude-drawing-skill/lib")

import numpy as np                                                        # noqa: E402
from PIL import Image                                                     # noqa: E402
from grainbook import PAINTS, GrainBook                                   # noqa: E402

PLATE = (-260, -900, 1600, 3500)       # x0, y0, w, h in design px
PX0, PY0, PW, PH = PLATE
SW, SH = 1080, 1920
HORIZON = 1180

PAINTS.update(dict(
    # ZeroVast: dusk over Telangana, and ink
    dusk_hi="#6b7ea8", dusk_mid="#c98a6a", dusk_lo="#eeb277", dusk_hot="#f8cf9a",
    city="#3f3a4e", city_far="#6d6480", earth="#8a593b", earth_lo="#5f3b26",
    ink_navy="#161b2e", vermilion="#d9552a", ochre="#d99f3c", brass="#bd9748",
    # Vignan: a study at night
    night_hi="#1e2541", night_mid="#2e3557", night_lo="#463f66",
    lamp="#e8bd7d", lamp_warm="#f6dcb4", desk="#9a6b3b", desk_lo="#6e4926", desk_hi="#bd8c52",
    page="#f7f0e0", page_shade="#ddd0b6", bolt="#2c8f66", bolt_hi="#54bb89", grape="#5b3f9c",
))


def px(x):
    return float(x) - PX0


def py(y):
    return float(y) - PY0


# ---------------------------------------------------------------- the brush vocabulary
def wash(g, region, colour, dry=0.14, a=1.0, streak=0.12, angle=-3):
    """a broad area of paint: solid, barely broken, no streaks fighting the value"""
    g.fill(region, colour, angle=angle, streak=streak, dry=dry, edge=2.4, soft=0.5, alpha=a)


def solid(g, region, colour, a=1.0):
    g.fill(region, colour, angle=0, streak=0.18, dry=0.06, edge=1.4, soft=0.35, alpha=a)


def bands(g, region, colours, ys, a=1.0, dry=0.16):
    g.bands(region, colours, ys, angle=-3, wave=18, period=1500, dry=dry, edge=2.4, soft=0.6,
            streak=0.13, alpha=a)


def line(g, pts, w, colour, alpha=1.0, wob=0.8):
    g.crayon([(px(x), py(y)) for x, y in pts], w, colour, taper=(0.25, 0.2), wobble=wob, alpha=alpha)


def poly(g, pts):
    return g.poly([(px(x), py(y)) for x, y in pts])


def box(g, x0, y0, x1, y1):
    return g.rect(px(x0), py(y0), px(x1), py(y1))


def ridge(g, y, amp, period, seed, x0=-320, x1=1400):
    xs, ys = g.wavy(px(x0), px(x1), py(y), amp, period, seed=seed)
    return g.below(xs, ys)


def pool(g, x, y, rx, ry, colour, steps=6, a0=0.22):
    """a lamp pool: concentric washes, each a little smaller and softer -- gouache, not a gradient"""
    for i in range(steps):
        f = 1.0 - i / (steps + 1.0)
        g.fill(g.ellipse(px(x), py(y), rx * f, ry * f), colour, angle=-4, streak=0.2, dry=0.5,
               edge=6.0, soft=3.0, alpha=a0 * (0.55 + 0.45 * f))


def speckle_stars(g, seed, n=30, x0=-200, x1=1300, y0=-860, y1=1400, col="cream", a=(0.18, 0.55)):
    rr = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rr.uniform(x0, x1), rr.uniform(y0, y1)
        solid(g, g.ellipse(px(x), py(y), rr.uniform(1.4, 2.8), rr.uniform(1.4, 2.6)), col, rr.uniform(*a))


def finish(book, out, name, quality=93):
    img = book.composite()
    out.mkdir(parents=True, exist_ok=True)
    img.save(out / f"{name}.jpg", quality=quality)
    meta_p = out / "plates.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    meta[name] = dict(x=PX0, y=PY0, w=PW, h=PH)
    meta_p.write_text(json.dumps(meta, indent=1))
    print(f"  {name:10s} {img.size}")


def paper_tile(out, size=760, seed=91):
    g = GrainBook(size, size, seed=seed, keep_stages=False)
    g.paper("cream", angle=-80)
    Image.fromarray((np.clip(g.C, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out / "paper.jpg", quality=90)
    print(f"  paper      {size}x{size}")


# ================================================================ ZERO VAST
def zv_dusk(g):
    """Khammam at dusk: three value steps (sky, hills, plain) and a sun sitting on the ridge."""
    SUN = (744, HORIZON - 150)
    bands(g, g.full(), ["ink_navy", "dusk_hi", "dusk_hi", "dusk_mid", "dusk_lo"],
          [py(-900), py(-620), py(-120), py(430), py(HORIZON - 120)])
    # one big soft cloud bank catching the last light, low over the hills
    for k, (cx, cy, cw, ch, col) in enumerate(((560, 760, 900, 60, "dusk_mid"), (620, 830, 760, 46, "dusk_hot"),
                                               (300, 700, 560, 40, "dusk_mid"))):
        g.fill(g.blob(px(cx), py(cy), cw * 0.5, ch, rough=0.22, seed=200 + k), col,
               angle=-4, streak=0.35, dry=0.4, edge=6.0, alpha=0.30)
    # thin, warm cloud underliners -- three only, so the sky stays a sky
    for (cx, cy, cw, ch) in ((200, 150, 520, 22), (820, 330, 560, 18), (330, 620, 700, 16)):
        g.fill(g.blob(px(cx), py(cy), cw * 0.5, ch, rough=0.2, seed=int(cx)),
               "dusk_mid", angle=-5, streak=0.4, dry=0.45, edge=4.0, alpha=0.28)
        g.fill(g.blob(px(cx + cw * 0.1), py(cy + 12), cw * 0.34, ch * 0.7, rough=0.2, seed=int(cx) + 5),
               "dusk_hot", angle=-5, streak=0.4, dry=0.45, edge=4.0, alpha=0.30)
    pool(g, SUN[0], SUN[1], 300, 260, "dusk_hot", steps=5, a0=0.16)
    # two hills, far then near, each a flat value with a lit crest
    far = ridge(g, HORIZON - 230, 50, 780, 41)
    wash(g, far, "city_far", dry=0.2, a=0.85)
    near = ridge(g, HORIZON - 120, 44, 560, 44)
    wash(g, near, "city", dry=0.2)
    for rg, col, al in ((far, "dusk_hot", 0.35), (near, "dusk_lo", 0.4)):
        xs = np.linspace(px(-300), px(1380), 90)
        g.crayon(list(zip(xs, np.full_like(xs, rg.box[0] + 2.0))), 2.8, col,
                 taper=(0.2, 0.2), wobble=0.7, alpha=al)
    # the sun, half sunk behind the near ridge
    solid(g, g.ellipse(px(SUN[0]), py(SUN[1]), 58, 58), "cream")
    solid(g, g.ellipse(px(SUN[0] - 14), py(SUN[1] - 12), 24, 22), "white", 0.8)
    # the plain: three steps into shadow, scrub, and a thin track
    bands(g, ridge(g, HORIZON + 4, 10, 700, 51), ["earth", "earth_lo"],
          [py(HORIZON + 260), py(HORIZON + 1400)], dry=0.2)
    for i in range(26):
        rr = np.random.default_rng(100 + i)
        x, y = rr.uniform(-200, 1280), HORIZON + rr.uniform(40, 620)
        w = rr.uniform(50, 150) * (1 + 0.5 * (y - HORIZON) / 620)
        g.fill(g.blob(px(x), py(y), w * 0.5, w * 0.12, rough=0.26, seed=i + 7),
               "earth_lo" if i % 3 else "city", angle=-6, dry=0.4, edge=3.0, alpha=0.45)
    # a village on the near ridge: one tower, three roofs, one window lit
    line(g, [(180, HORIZON - 40), (196, HORIZON - 150)], 5.0, "city")
    line(g, [(220, HORIZON - 40), (206, HORIZON - 150)], 5.0, "city")
    solid(g, g.ellipse(px(200), py(HORIZON - 166), 38, 30), "city")
    solid(g, poly(g, [(164, HORIZON - 166), (200, HORIZON - 196), (236, HORIZON - 166)]), "city")
    for (hx, hw, hh) in ((940, 130, 64), (1052, 96, 46), (742, 84, 38)):
        solid(g, box(g, hx, HORIZON - hh, hx + hw, HORIZON + 6), "city")
        solid(g, poly(g, [(hx - 10, HORIZON - hh), (hx + hw / 2, HORIZON - hh - 28),
                          (hx + hw + 10, HORIZON - hh)]), "city_far")
        solid(g, box(g, hx + hw * 0.3, HORIZON - hh * 0.6, hx + hw * 0.46, HORIZON - hh * 0.32), "dusk_hot", 0.8)
    # the track: two soft edges, converging
    g.fill(poly(g, [(600, HORIZON + 10), (640, HORIZON + 10), (880, HORIZON + 1400), (300, HORIZON + 1400)]),
           "dusk_hot", angle=-4, streak=0.4, dry=0.7, edge=8.0, alpha=0.16)
    line(g, [(618, HORIZON + 14), (556, HORIZON + 700), (470, HORIZON + 1400)], 2.4, "dusk_hot", 0.22, 1.4)
    line(g, [(626, HORIZON + 14), (704, HORIZON + 700), (800, HORIZON + 1400)], 2.4, "dusk_hot", 0.22, 1.4)
    speckle_stars(g, 5, n=24, x0=-200, x1=1300, y0=-860, y1=200, a=(0.12, 0.4))


def zv_desk(g):
    """The desk at midnight: navy wall, a cork pinboard, warm wood, one lamp, a mug, a stack of paper."""
    wash(g, g.full(), "ink_navy")
    bands(g, g.full(), ["ink_navy", "night_hi"], [py(600), py(1200)], a=0.9)
    # pinboard, left of frame, with pinned printouts
    solid(g, box(g, -70, 640, 470, 1140), "desk_lo")
    line(g, [(-70, 640), (470, 640), (470, 1140), (-70, 1140), (-70, 640)], 3.0, "earth_lo", 0.8)
    rr = np.random.default_rng(23)
    for i in range(5):
        cx, cy = 10 + i * 92 + rr.uniform(-6, 6), 700 + rr.uniform(0, 200)
        bw, bh = rr.uniform(96, 130), rr.uniform(110, 170)
        solid(g, box(g, cx, cy, cx + bw, cy + bh), "page", 0.94)
        line(g, [(cx + 8, cy + 20), (cx + bw - 12, cy + 20)], 2.0, "page_shade", 0.9)
        line(g, [(cx + 8, cy + 34), (cx + bw - 30, cy + 34)], 2.0, "page_shade", 0.9)
        solid(g, g.ellipse(px(cx + bw / 2), py(cy + 6), 5, 5), "vermilion")
    # desk surface with a lit band where the lamp falls
    wash(g, ridge(g, HORIZON, 8, 900, 71), "desk")
    bands(g, ridge(g, HORIZON + 240, 10, 1200, 72), ["desk", "desk_lo"], [py(HORIZON + 1500)])
    pool(g, 760, 1330, 470, 210, "lamp", steps=5, a0=0.16)
    rr2 = np.random.default_rng(29)
    for i in range(30):
        y0 = HORIZON + rr2.uniform(6, 900)
        x0 = rr2.uniform(-260, 1340)
        line(g, [(x0, y0), (x0 + rr2.uniform(-24, 24), y0 + rr2.uniform(150, 440))], 1.8,
             "desk_lo" if i % 3 else "desk_hi", 0.22, 1.2)
    # the lamp: a shade, a stalk, a base -- a silhouette in front of its own pool
    solid(g, poly(g, [(700, 1000), (830, 1000), (860, 1120), (668, 1120)]), "ink_navy")
    line(g, [(764, 1120), (764, 1290)], 7.0, "ink_navy")
    solid(g, g.ellipse(px(764), py(1300), 62, 20), "ink_navy")
    line(g, [(690, 1120), (838, 1120)], 4.0, "lamp", 0.5)
    # a mug and a stack of paper: two shapes that say "someone works here"
    solid(g, box(g, 250, 1240, 356, 1340), "page")
    solid(g, g.ellipse(px(303), py(1240), 53, 16), "page_shade")
    for i in range(4):
        solid(g, box(g, 900, 1290 - i * 22, 1140, 1312 - i * 22), "page" if i % 2 else "page_shade")
    speckle_stars(g, 31, n=14, x0=0, x1=1000, y0=300, y1=1100, col="lamp", a=(0.06, 0.16))


def zv_glass(g):
    """A dark room lit only by a phone: a wall, a table, a chair back. No stars -- this is indoors."""
    bands(g, g.full(), ["ink_navy", "ink_navy", "night_hi"], [py(-900), py(700), py(2000)])
    # the wall behind, a shade lighter than the dark, with one soft wash of the screen's glow
    wash(g, g.full(), "night_hi", a=0.30)
    pool(g, 540, 900, 470, 560, "night_mid", steps=6, a0=0.26)
    pool(g, 540, 860, 260, 340, "dusk_hi", steps=4, a0=0.13)
    # a table edge and its front face: the whole bottom third is furniture, not void
    wash(g, g.rect(px(-260), py(1520), px(1340), py(2400)), "night_hi", dry=0.2)
    wash(g, g.rect(px(-260), py(1560), px(1340), py(2400)), "ink_navy", a=0.6, dry=0.2)
    line(g, [(-260, 1520), (300, 1514), (800, 1522), (1340, 1516)], 4.0, "dusk_hi", 0.45, 0.5)
    line(g, [(-260, 1560), (300, 1554), (800, 1562), (1340, 1556)], 2.0, "night_mid", 0.5, 0.5)
    # the tabletop catches a little of the light
    pool(g, 540, 1560, 420, 90, "dusk_hi", steps=3, a0=0.10)
    # a chair back, low left, and a mug, low right: two dark shapes that say "a room"
    solid(g, box(g, -60, 1660, 240, 2060), "night_hi", 0.55)
    solid(g, box(g, 980, 1470, 1046, 1536), "night_mid", 0.6)
    solid(g, g.ellipse(px(1013), py(1470), 33, 12), "night_hi", 0.8)
    # a curtain edge on the right, just catching the phone light
    line(g, [(1290, -200), (1262, 800), (1296, 1520)], 26.0, "night_mid", 0.5, 1.0)


def zv_end(g):
    """The sign-off plate: near-black navy, one warm pool up top, a dusk line to land the mark on."""
    bands(g, g.full(), ["ink_navy", "ink_navy", "night_hi"], [py(-900), py(700), py(2400)])
    pool(g, 540, 900, 520, 460, "night_mid", steps=5, a0=0.24)
    pool(g, 540, 1500, 460, 240, "dusk_mid", steps=4, a0=0.10)
    wash(g, ridge(g, 2080, 18, 1100, 111), "ink_navy", dry=0.3)
    line(g, [(-260, 2080), (520, 2072), (1340, 2084)], 2.8, "dusk_hot", 0.32, 0.6)
    speckle_stars(g, 113, n=30, x0=-200, x1=1300, y0=-820, y1=1200, a=(0.14, 0.42))


# ================================================================ VIGNAN
def vg_study(g):
    """A student's desk at night: three values -- night wall, moonlit window, lamplit desk."""
    bands(g, g.full(), ["night_hi", "night_mid", "night_lo"], [py(-900), py(240), py(1240)])
    # the window, off-frame right: a sky panel, a moon, three rooftops, a frame
    solid(g, box(g, 560, 90, 1400, 780), "night_hi")
    solid(g, box(g, 560, 90, 1400, 480), "night_mid", 0.55)
    pool(g, 880, 300, 150, 150, "cream", steps=4, a0=0.18)
    solid(g, g.ellipse(px(880), py(300), 58, 58), "page")
    solid(g, g.ellipse(px(864), py(286), 40, 40), "night_mid", 0.55)
    speckle_stars(g, 31, n=22, x0=590, x1=1380, y0=120, y1=740, a=(0.3, 0.75))
    for (hx, hw, hh) in ((580, 190, 150), (760, 150, 110), (900, 230, 190), (1120, 170, 130)):
        solid(g, box(g, hx, 780 - hh, hx + hw, 780), "ink_navy", 0.9)
        if hx == 900:
            solid(g, box(g, hx + 60, 780 - hh * 0.55, hx + 100, 780 - hh * 0.25), "lamp", 0.85)
    for xx in (560, 960, 1400):
        line(g, [(xx, 90), (xx, 780)], 10.0, "desk_lo", 0.95, 0.2)
    line(g, [(560, 430), (1400, 430)], 10.0, "desk_lo", 0.95, 0.2)
    # the desk
    wash(g, ridge(g, 1290, 8, 900, 91), "desk")
    bands(g, ridge(g, 1500, 10, 1100, 92), ["desk", "desk_lo"], [py(2400)])
    pool(g, 420, 1560, 420, 180, "lamp", steps=5, a0=0.18)
    rr = np.random.default_rng(37)
    for i in range(26):
        y0 = 1330 + rr.uniform(0, 900)
        x0 = rr.uniform(-260, 1340)
        line(g, [(x0, y0), (x0 + rr.uniform(-20, 20), y0 + rr.uniform(140, 420))], 1.8,
             "desk_lo" if i % 3 else "desk_hi", 0.22, 1.1)
    # the lamp, in front of its own pool
    solid(g, poly(g, [(96, 1080), (226, 1080), (256, 1210), (66, 1210)]), "night_hi")
    line(g, [(160, 1210), (160, 1360)], 6.0, "night_hi")
    solid(g, g.ellipse(px(160), py(1368), 56, 18), "night_hi")
    line(g, [(86, 1210), (236, 1210)], 4.0, "lamp", 0.55)
    # books: a stack, spines stepped, warm colours
    bx, by = 760, 1330
    for i, (col, hh) in enumerate((("bolt", 46), ("grape", 42), ("vermilion", 50), ("desk_lo", 38))):
        solid(g, box(g, bx + i * 4, by - i * hh, bx + 250 - i * 6, by - i * hh + hh - 6), col, 0.95)
        line(g, [(bx + i * 4, by - i * hh), (bx + 250 - i * 6, by - i * hh)], 2.0, "page", 0.35)
    # the open notebook, low left
    solid(g, poly(g, [(20, 1560), (450, 1500), (500, 1980), (70, 2050)]), "page")
    for i in range(6):
        y0 = 1596 + i * 60
        line(g, [(80, y0), (420, y0 - 26)], 2.4, "page_shade", 0.9)
    line(g, [(240, 1560), (280, 2000)], 3.0, "page_shade", 0.8)
    line(g, [(110, 1700), (208, 1690)], 4.0, "bolt", 0.85, 0.5)


def vg_pages(g):
    """Close on the book itself: two cream leaves under the lamp, ruled, one line highlighted."""
    wash(g, g.full(), "desk_lo")
    bands(g, g.full(), ["desk_lo", "desk"], [py(400), py(2400)], a=0.8)
    pool(g, 540, 1000, 700, 480, "lamp", steps=5, a0=0.18)
    solid(g, poly(g, [(-280, 1080), (540, 960), (540, 1900), (-300, 2160)]), "page")
    solid(g, poly(g, [(540, 960), (1360, 1080), (1400, 2160), (540, 1900)]), "page", 0.99)
    # the gutter: a soft dark seam, then the pages' own edge shading
    for i in range(4):
        g.fill(poly(g, [(520 + i * 6, 962), (566 + i * 6, 964), (566 + i * 6, 1898), (520 + i * 6, 1896)]),
               "desk_lo", angle=-2, dry=0.6, edge=6.0, alpha=0.18)
    line(g, [(540, 962), (540, 1898)], 3.0, "page_shade", 0.9)
    rr = np.random.default_rng(43)
    for side, (x0, x1) in enumerate(((40, 470), (610, 1290))):
        for i in range(15):
            y0 = 1100 + i * 52 + (0 if side == 0 else 34)
            xa = x0 + rr.uniform(0, 26)
            xb = x1 - rr.uniform(0, 80)
            line(g, [(xa, y0), (xb, y0 + (0 if side == 0 else 10))], 3.2 if i % 5 else 5.0,
                 "page_shade" if i % 5 else "desk_lo", 0.8, 0.5)
    # a diagram on the right leaf: a circle, an arrow, a highlighted phrase
    solid(g, g.ellipse(px(830), py(1290), 52, 52), "page_shade")
    line(g, [(830, 1238), (966, 1206)], 3.4, "grape", 0.9, 0.4)
    line(g, [(700, 1520), (940, 1512)], 8.0, "bolt", 0.55, 0.4)
    line(g, [(710, 1450), (1010, 1440)], 7.0, "bolt_hi", 0.35, 0.4)


def vg_map(g):
    """The roadmap sheet: cream paper on the desk, one green route through the product, notes in the margin."""
    wash(g, g.full(), "night_mid")
    bands(g, g.full(), ["night_mid", "night_hi"], [py(300), py(2400)], a=0.9)
    # the sheet, tilted, with a cast shadow under its lower edge
    g.fill(poly(g, [(30, 220), (1050, 190), (1070, 1650), (20, 1690)]), "desk_lo",
           angle=-2, streak=0.2, dry=0.5, edge=5.0, alpha=0.45)
    solid(g, poly(g, [(20, 200), (1040, 172), (1060, 1620), (10, 1662)]), "page")
    line(g, [(20, 200), (1040, 172), (1060, 1620), (10, 1662), (20, 200)], 2.6, "page_shade", 0.7, 0.4)
    # the route
    stops = [(160, 1400), (300, 1160), (250, 860), (470, 690), (700, 550), (900, 700), (830, 1000)]
    line(g, stops, 9.0, "bolt", 0.95, 1.6)
    for i, (x, y) in enumerate(stops):
        solid(g, g.ellipse(px(x), py(y), 32, 32), "page")
        solid(g, g.ellipse(px(x), py(y), 20, 20), "bolt" if i in (0, len(stops) - 1) else "desk_lo")
    # margin notes and a highlighted block, so the sheet reads as a working plan
    rr = np.random.default_rng(53)
    for i in range(8):
        y0 = 300 + i * 44
        line(g, [(660 + rr.uniform(0, 20), y0), (990 - rr.uniform(0, 40), y0 + 6)], 2.6, "page_shade", 0.8, 0.5)
    solid(g, box(g, 640, 700, 1000, 790), "bolt_hi", 0.35)
    line(g, [(650, 720), (860, 716)], 6.0, "bolt", 0.5, 0.4)


def vg_room(g):
    """Pulled back: the shelf, the table, two chairs, and the rug -- where the studying actually happens."""
    bands(g, g.full(), ["night_hi", "night_mid", "night_lo"], [py(-900), py(200), py(1300)])
    # a shelf of books, top left
    solid(g, box(g, -260, 640, 620, 668), "desk_lo")
    rr = np.random.default_rng(59)
    x = -230
    cols = ["bolt", "grape", "vermilion", "desk", "earth_lo", "night_hi"]
    while x < 590:
        w = rr.uniform(34, 60); h = rr.uniform(130, 220)
        solid(g, box(g, x, 640 - h, x + w, 636), cols[int(rr.integers(0, len(cols)))], 0.95)
        x += w + rr.uniform(2, 9)
    # the floor / desk plane
    wash(g, ridge(g, 1300, 10, 900, 97), "desk")
    bands(g, ridge(g, 1520, 12, 1100, 98), ["desk", "desk_lo"], [py(2400)])
    pool(g, 540, 1180, 560, 300, "lamp", steps=5, a0=0.16)
    # the rug
    solid(g, g.ellipse(px(560), py(1980), 700, 280), "earth_lo", 0.32)
    # two chairs: simple silhouettes, one turned
    for (cx, cy, w, h, rot) in ((210, 1500, 240, 460, -3), (880, 1470, 220, 430, 4)):
        solid(g, poly(g, [(cx - w / 2 - 18, cy + rot * 6), (cx + w / 2, cy), (cx + w / 2 + 6, cy - h),
                          (cx - w / 2 - 12, cy - h - 10)]), "night_hi")
        solid(g, box(g, cx - w / 2, cy + rot * 6, cx + w / 2, cy + 46), "night_hi")
        line(g, [(cx - w / 2 + 18, cy + 46), (cx - w / 2 + 26, cy + 210)], 9.0, "night_hi")
        line(g, [(cx + w / 2 - 18, cy + 46), (cx + w / 2 - 26, cy + 210)], 9.0, "night_hi")
    # a table between them, two open books and a mug
    solid(g, box(g, 330, 1560, 760, 1602), "desk_hi")
    for lx in (368, 700):
        line(g, [(lx, 1602), (lx + 12, 1760)], 12.0, "desk_lo")
    solid(g, poly(g, [(380, 1530), (540, 1518), (556, 1560), (392, 1572)]), "page")
    solid(g, poly(g, [(548, 1518), (730, 1532), (724, 1570), (556, 1560)]), "page")
    line(g, [(540, 1518), (540, 1562)], 3.0, "page_shade", 0.9)
    solid(g, box(g, 600, 1470, 650, 1524), "vermilion", 0.95)


def vg_end(g):
    """The sign-off: night navy, one warm pool, a desk edge -- cream type has somewhere to land."""
    bands(g, g.full(), ["night_hi", "night_hi", "night_mid"], [py(-900), py(300), py(2100)])
    pool(g, 540, 940, 560, 460, "night_lo", steps=5, a0=0.30)
    pool(g, 540, 1600, 520, 260, "lamp", steps=4, a0=0.10)
    wash(g, ridge(g, 2020, 16, 1100, 99), "night_hi", dry=0.3)
    line(g, [(-260, 2020), (540, 2014), (1340, 2022)], 2.6, "lamp", 0.30, 0.6)
    speckle_stars(g, 67, n=34, x0=-200, x1=1300, y0=-800, y1=1300, a=(0.14, 0.5))


PLATES = {
    "zerovast": {"zv_dusk": zv_dusk, "zv_desk": zv_desk, "zv_glass": zv_glass, "zv_end": zv_end},
    "vignan": {"vg_study": vg_study, "vg_pages": vg_pages, "vg_map": vg_map, "vg_room": vg_room, "vg_end": vg_end},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=sorted(PLATES), required=True)
    ap.add_argument("--out", default="assets/plates")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    want = [s for s in a.only.split(",") if s]
    for name, fn in PLATES[a.which].items():
        if want and name not in want:
            continue
        t0 = time.time()
        g = GrainBook(PW, PH, seed=sum(map(ord, name)) % 9999, keep_stages=False)
        g.finish(grain=0.8, speckle=0.35, soft=0.18)
        g.paper("cream", angle=-80)
        fn(g)
        finish(g, out, name)
        print(f"  {name:10s} {time.time() - t0:5.1f}s")
    if not want:
        paper_tile(out)


if __name__ == "__main__":
    main()
