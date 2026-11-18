"""ZERO VAST -- "Deco" (9:16, 23 s, NO VOICEOVER)

A 1930s airbrushed night poster: sunburst, moon, a stepped skyline of lit windows, water that
mirrors it, gilt ornamental lettering. Painted by `claude-drawing-skill`'s artdeco engine -- no
outlines anywhere, every surface sprayed through a frisket -- which is why it does not look like any
of the other four ads in this set.

How it moves: the poster paints ITSELF for the first two and a half seconds (the engine's staged
plates are shown in order, so the sky fills, then the city, then the water, then the gold), and after
that the camera walks through the finished picture at six scales -- each cut going deeper into the
same artwork rather than to a new image. The picture is the set, not the background.

`huashu-art-motion`: one move per shot, a NEW scale at every cut, and the hold longer than the move.
`bang-motion`: no flat colour bars, no drop-shadowed title halos, and the type is the poster's own --
gold, tracked, and only where a 1930s poster would put it.

No voiceover: the track is the only sound, and every cut is a hit in it.
"""
import pathlib
import sys

import numpy as np
import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE.parent / "_shared" / "eng"))

import filmkit as FK                                                     # noqa: E402
import transitions as TR                                                 # noqa: E402
import ty                                                                # noqa: E402
from filmkit import P, clamp, pop, hit, ramp                             # noqa: E402
from engine import Film, Item, ease_out_cubic                             # noqa: E402

W, H = 1080.0, 1920.0
DUR = 23.0
GOLD = (230, 196, 121)
IVORY = (245, 236, 214)

# the painting stages, in the order the engine sprayed them, and when each one lands
STAGES = ["deco_sky", "deco_burst", "deco_far", "deco_near", "deco_water", "deco_jetty", "deco_lettering"]
STAGE_AT = [0.05, 0.40, 0.78, 1.30, 1.78, 2.05, 2.34]

SHOTS = [
    (0.00, 540, 960, 1.00),      # the poster, painting itself
    (2.62, 800, 905, 1.55),      # the skyline and the clock tower
    (5.82, 540, 300, 1.42),      # the gilt lettering, whole name in frame
    (8.62, 795, 700, 2.05),      # the clock and the crown: ten past ten
    (11.42, 540, 1410, 1.75),    # the waterline, and everything it mirrors
    (14.22, 540, 1595, 1.92),    # the address, as the poster prints it
    (17.02, 880, 1010, 1.34),    # the moon and the lit towers
    (19.42, 540, 960, 1.00),     # the whole poster again, and hold
]
CUTS = [s[0] for s in SHOTS[1:]]

CAPS = [
    (0.55, 2.40, "A city, drawn from nothing."),
    (2.90, 5.60, "Three kinds of work. One skyline."),
    (6.10, 8.40, "Hand-written. No framework."),
    (8.90, 11.20, "Every window lit on purpose."),
    (11.70, 14.00, "No page-builder payload. No lock-in."),
    (14.50, 16.80, "Built to perform, and handed over."),
    (17.30, 19.20, "Khammam, Telangana."),
]


class Poster(Item):
    """The painting, at whatever stage it has reached, as a world object the camera can walk into."""

    z = 0

    def __init__(self):
        super().__init__(-10, None, 0, sfx=False)
        self.img = {}

    def visible(self, t):
        return True

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-20, -20, W + 20, H + 20)

    def _get(self, name):
        if name not in self.img:
            from PIL import Image
            a = np.asarray(Image.open(HERE / "assets" / "plates" / f"{name}.jpg").convert("RGB"), np.uint8)
            self.img[name] = skia.Image.fromarray(
                np.ascontiguousarray(np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])),
                skia.kRGBA_8888_ColorType)
            # eight 1080x1920 plates is 66 MB of RGBA; keep only what the last few seconds need
            if len(self.img) > 2:
                for k in [k for k in self.img if k != name][:-1]:
                    self.img.pop(k, None)
        return self.img[name]

    def draw(self, c, res, t):
        k = 0
        for i, ts in enumerate(STAGE_AT):
            if t >= ts:
                k = i
        name = STAGES[k]
        img = self._get(name)
        c.drawImageRect(img, skia.Rect.MakeXYWH(0, 0, img.width(), img.height()),
                        skia.Rect.MakeXYWH(0, 0, W, H),
                        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear),
                        skia.Paint(AntiAlias=True))
        # between stages, a brief airborne bloom over the area just sprayed -- airbrush, not a wipe
        if k < len(STAGE_AT) - 1:
            u = clamp((t - STAGE_AT[k]) / 0.42)
            c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), P((206, 226, 238), 0.14 * (1 - u) ** 2))


class Bed(Item):
    """The dark room the poster is pinned in."""

    z = -20

    def __init__(self):
        super().__init__(-50, None, -20, sfx=False)

    def visible(self, t):
        return True

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        c.drawRect(skia.Rect.MakeXYWH(-3000, -3000, 12000, 12000), P((7, 8, 12)))
        g = skia.GradientShader.MakeRadial(
            skia.Point(540, 900), 2200,
            [skia.ColorSetARGB(34, 60, 90, 110), skia.ColorSetARGB(0, 7, 8, 12)], [0.0, 1.0])
        c.drawRect(skia.Rect.MakeXYWH(-3000, -3000, 12000, 12000), skia.Paint(Shader=g))


class Caps(FK.ScreenCard):
    """The poster's own caption voice: tracked gold caps, on a rule, low in the frame."""

    z = 40

    def __init__(self, film):
        super().__init__(film, None, self.z)

    def draw(self, c, res, t):
        for (t0, t1, line) in CAPS:
            if not (t0 <= t <= t1 + 0.3):
                continue
            a = ramp(t, t0, 0.3) * (1 - ramp(t, t1, 0.2))
            if a <= 0.01:
                continue
            self.screen(c, t)
            ln = ty.layout(line.upper(), str(FK.LABEL), 34)
            wpx = ln.width
            y = 1712.0
            # a soft shadow sells the letters as sprayed onto the plinth
            for dy, aa in ((3, 0.35), (2, 0.30)):
                ty.draw(c, ln, W / 2, y + dy, rgb=(4, 8, 16), a=a * aa, align="center")
            ty.draw(c, ln, W / 2, y, rgb=IVORY, a=a, align="center")
            # gold rules either side, growing from the centre -- the deco way to underline a line
            gw = clamp((t - t0) / 0.45) * 132
            for sgn in (-1, 1):
                x0 = W / 2 + sgn * (wpx / 2 + 26)
                c.drawRect(skia.Rect.MakeXYWH(min(x0, x0 + sgn * gw), y - 9, gw, 1.6), P(GOLD, a * 0.85))
            c.restore()


class Cuts(Item):
    z = 70

    def __init__(self):
        super().__init__(-5, None, 70, sfx=False)
        self.tr = [(CUTS[2], TR.Leak(dur=0.55, colour=(255, 220, 150), x=0.5, y=0.2)),
                   (CUTS[4], TR.Whip(dur=0.22, direction=-1)),
                   (CUTS[5], TR.PushThrough(dur=0.34, rgb=(8, 14, 26))),
                   (CUTS[6], TR.CardSwing(dur=0.34, rgb=(240, 228, 200)))]

    def draw(self, c, res, t):
        for t_cut, tr in self.tr:
            if abs(t - t_cut) < 0.45:
                tr.draw(c, t, t_cut)


class Grain(Item):
    z = 71

    def draw(self, c, res, t):
        n = int(t * 30)
        for i in range(120):
            x = (i * 769.0 + n * 91) % W
            y = (i * 431.0 + n * 137) % H
            c.drawRect(skia.Rect.MakeXYWH(x, y, 2.0, 2.0), P((255, 250, 240), 0.035))


def build_film(doc):
    """Timed from the shot list above, not from a recorded take: no timing.json is read."""
    film = Film(DUR, fps=30, look=dict(board="studio.png", bg=(7, 8, 12), grade=(1.02, 1.0, 0.96),
                                       grain=0.0, glow=0.0, vignette=0.10, curve=0.02, dim=(8, 10, 14)))
    film.fade_in, film.fade_out = 0.4, 1.2
    film.items.remove(film.board)
    film.add(Bed())
    film.add(Poster())

    film.cam(0.0, 540, 960, 1.0)
    cf = FK.CutFilm(film)
    film = cf
    for (t, cx, cy, z) in SHOTS:
        cf.shot(t, cx, cy, z)

    film.add(Caps(film))
    film.add(Cuts())
    film.add(Grain())
    film.add(FK.Vignette(film, None, strength=0.34, warm=(6, 8, 14)))

    for i, c in enumerate(CUTS):
        film.cue("impact" if i % 2 == 0 else "stamp", c, 0.45)
    film.cue("shimmer", 2.44, 0.35)
    film.cue("shimmer", 14.3, 0.3)
    film.cue("impact", 19.42, 0.5)
    return film
