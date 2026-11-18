"""ZERO VAST -- "Type" (9:16, 22 s, NO VOICEOVER)

The type is the only actor. Words punch in on the beat, one idea per shot, and the ground moves
underneath constantly -- never a still colour field, never the same surface twice in a row.

The grammar is `huashu-art-motion`'s **y5 动态文字**: one focus per shot, entrance on expo-out, exit
faster than the entrance, a hard accent exactly on the cut. The brief is `bang-motion`'s anti-PPT
file: sentence case, one weight, no pill on every line, no all-caps shouting, alternating entry
directions -- and one emphasised word per shot, the "marker" highlighter, never more.

Hierarchy is the whole trick in a type film: each beat has ONE hero line fitted edge-to-edge and a
small support line under it, so the page has a headline and a caption rather than two equal lines.

No voiceover. The cut sheet below is the script: 96 bpm, one bar = 2.5 s, every cut on a bar line,
so `audio/score.wav` puts a hit exactly where the picture changes.
"""
import math
import pathlib
import sys

import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE.parent / "_shared" / "eng"))

import filmkit as FK                                                     # noqa: E402
import transitions as TR                                                 # noqa: E402
import ty                                                                # noqa: E402
from filmkit import P, clamp, pop, hit, ramp                             # noqa: E402
from engine import Film, Item, ease_out_cubic                             # noqa: E402

SW, SH = 1080.0, 1920.0
INK = (18, 15, 20)
CREAM = (250, 244, 232)
VERM = (233, 94, 40)
SAND = (232, 215, 186)
NAVY = (18, 21, 30)
DUSK = (28, 21, 25)

BPM = 96.0
DUR = 22.0
CUTS = [0.0, 3.0, 5.5, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0]


def _ease(u):
    return ease_out_cubic(clamp(u))


def fit(text, max_w, cap, kind="ui"):
    """Largest size at which `text` fits `max_w`. Kinetic type has to touch the frame."""
    path = str(FK.DISPLAY if kind == "display" else FK.UI)
    lo, hi = 20.0, float(cap)
    for _ in range(24):
        mid = (lo + hi) / 2
        if ty.measure(text, path, mid) <= max_w:
            lo = mid
        else:
            hi = mid
    return lo


# ------------------------------------------------------------------ the moving ground
class Surface(Item):
    """Five grounds, one per act: different colour, different motion, no repeats.

    Each one is soft-edged light rather than geometry -- flat coloured bars across a frame are the
    cheapest thing a type film can do, so the bands here are wide gradients at 3-6% contrast.
    """

    z = 0

    def __init__(self):
        super().__init__(-10, None, 0, sfx=False)

    def draw(self, c, res, t):
        if t < 3.0:
            # 1. ink; two slow diagonal washes of warm light and a bloom off-centre
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((17, 14, 19)))
            for i in range(2):
                y0 = SH * (0.1 + 0.55 * i) + math.sin(t * 0.35 + i) * 90
                g = skia.GradientShader.MakeLinear(
                    [skia.Point(0, y0 - 320), skia.Point(SW, y0 + 320)],
                    [skia.ColorSetARGB(0, 60, 36, 30), skia.ColorSetARGB(52, 96 + 30 * i, 52, 40),
                     skia.ColorSetARGB(0, 60, 36, 30)], [0.0, 0.5, 1.0])
                c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
            g = skia.GradientShader.MakeRadial(
                skia.Point(SW * 0.78, SH * 0.26), SH * 0.34,
                [skia.ColorSetARGB(120, 233, 94, 40), skia.ColorSetARGB(0, 233, 94, 40)], [0.0, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
        elif t < 5.5:
            # 2. sand: a dot grid breathing -- the first light ground
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P(SAND))
            step = 58
            for i in range(int(SW / step) + 2):
                for j in range(int(SH / step) + 2):
                    r = 1.8 + 2.6 * (0.5 + 0.5 * math.sin(t * 0.9 + i * 0.55 + j * 0.42))
                    c.drawCircle(i * step, j * step, r, P((58, 40, 36), 0.13))
            self._shade(c, t, (120, 70, 40), 0.18)
        elif t < 8.0:
            # 3. pale cream: one enormous soft shadow crossing, and slow drifting dust
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((247, 238, 220)))
            x = SW * (0.3 + 0.5 * math.sin((t - 5.5) * 0.6))
            g = skia.GradientShader.MakeRadial(
                skia.Point(x, SH * 0.42), SH * 0.62,
                [skia.ColorSetARGB(78, 120, 88, 66), skia.ColorSetARGB(0, 120, 88, 66)], [0.0, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
            for i in range(26):
                px = (i * 213.0 + t * 22) % SW
                py = (i * 371.0 - t * 14) % SH
                c.drawCircle(px, py, 1.6 + (i % 3), P((90, 62, 44), 0.10))
        elif t < 10.0:
            # 4. pale blue-grey, horizontal light bands drifting: same value as the cream, different colour
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((214, 222, 226)))
            for i in range(5):
                y = (i * SH / 4 + t * 26) % (SH + 300) - 150
                c.drawRect(skia.Rect.MakeXYWH(0, y, SW, 110), P((236, 242, 244), 0.55))
            self._shade(c, t, (60, 90, 110), 0.22)
        elif t < 12.0:
            # 5. navy, slow blobs of light behind the words
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P(NAVY))
            for i in range(5):
                x = SW * (0.22 + 0.16 * i) + math.sin(t * 0.55 + i) * 70
                y = SH * (0.24 + 0.15 * i) + math.cos(t * 0.45 + i * 1.7) * 80
                r = 240 + 70 * math.sin(t * 0.6 + i)
                g = skia.GradientShader.MakeRadial(
                    skia.Point(x, y), r,
                    [skia.ColorSetARGB(66, 70 + 18 * i, 84 + 12 * i, 120 + 6 * i),
                     skia.ColorSetARGB(0, 18, 21, 30)], [0.0, 1.0])
                c.drawCircle(x, y, r, skia.Paint(Shader=g))
        elif t < 14.0:
            # 6. ink, a bar of light travelling the frame
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((15, 13, 18)))
            x = ((t - 12.0) * 290) % (SW * 1.5) - SW * 0.25
            g = skia.GradientShader.MakeLinear(
                [skia.Point(x - 320, SH * 0.08), skia.Point(x + 260, SH * 0.92)],
                [skia.ColorSetARGB(0, 255, 205, 160), skia.ColorSetARGB(58, 255, 196, 150),
                 skia.ColorSetARGB(0, 255, 205, 160)], [0.0, 0.5, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
        elif t < 16.0:
            # 7. ink again -- but the motion is a slow rotating fan of light, nothing like the bar
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((16, 14, 17)))
            c.save()
            c.translate(SW * 0.5, SH * 0.46)
            c.rotate((t - 14.0) * 14.0)
            for i in range(6):
                c.rotate(60.0)
                g = skia.GradientShader.MakeLinear(
                    [skia.Point(0, 0), skia.Point(0, -SH * 0.8)],
                    [skia.ColorSetARGB(20, 255, 214, 176), skia.ColorSetARGB(0, 255, 214, 176)], [0.0, 1.0])
                path = skia.Path()
                path.moveTo(0, 0)
                path.lineTo(-SW * 0.10, -SH * 0.85)
                path.lineTo(SW * 0.10, -SH * 0.85)
                path.close()
                c.drawPath(path, skia.Paint(Shader=g))
            c.restore()
        elif t < 18.0:
            # 8. deep plum with light rising in vertical streaks
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((30, 20, 30)))
            for i in range(6):
                x = SW * (0.06 + 0.11 * i)
                ph = ((t - 16.0) * 0.5 + i * 0.13) % 1.0
                g = skia.GradientShader.MakeLinear(
                    [skia.Point(x, SH * (0.95 - ph * 0.8)), skia.Point(x, SH * 1.05)],
                    [skia.ColorSetARGB(0, 255, 190, 150), skia.ColorSetARGB(46, 255, 186, 146)], [0.0, 1.0])
                c.drawRect(skia.Rect.MakeXYWH(x - 34, 0, 68, SH), skia.Paint(Shader=g))
            g = skia.GradientShader.MakeRadial(
                skia.Point(SW * 0.5, SH * 1.02), SH * 0.5,
                [skia.ColorSetARGB(90, 200, 96, 60), skia.ColorSetARGB(0, 200, 96, 60)], [0.0, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
        else:
            # 9. the sign-off: a dusk, so the last frame is not another dark card
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P(DUSK))
            g = skia.GradientShader.MakeLinear(
                [skia.Point(0, SH * 0.42), skia.Point(0, SH)],
                [skia.ColorSetARGB(0, 180, 90, 50), skia.ColorSetARGB(150, 140, 66, 44),
                 skia.ColorSetARGB(210, 60, 34, 30)], [0.0, 0.62, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
            c.drawCircle(SW * 0.24, SH * 0.245, 104, P((255, 246, 230), 0.95))
            c.drawCircle(SW * 0.24, SH * 0.245, 168, P(VERM, 0.10))
            for i in range(22):
                x = (i * 149.0 + t * 8) % SW
                y = SH * 0.55 + (i * 67 % 300)
                c.drawCircle(x, y, 1.4 + (i % 3) * 0.9, P(CREAM, 0.10 + 0.06 * ((i * 7) % 3)))

    @staticmethod
    def _shade(c, t, rgb, a):
        """A soft corner shadow: keeps a light ground from looking like a flat fill."""
        g = skia.GradientShader.MakeRadial(
            skia.Point(SW * 0.12, SH * 0.94), SH * 0.85,
            [skia.ColorSetARGB(int(255 * a), *rgb), skia.ColorSetARGB(0, *rgb)], [0.0, 1.0])
        c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))


class Grain(Item):
    """Fine static, resampled every frame so it reads as film stock rather than dirt."""

    z = 71

    def __init__(self, a=0.05):
        super().__init__(-5, None, 71, sfx=False)
        self.a = a

    def draw(self, c, res, t):
        n = int(t * 30)
        for i in range(150):
            x = (i * 769.0 + n * 91) % SW
            y = (i * 431.0 + n * 137) % SH
            c.drawRect(skia.Rect.MakeXYWH(x, y, 2.0, 2.0), P((255, 250, 240), self.a))


# ------------------------------------------------------------------ the words
# rows are (role, text, marker_word); role decides the size, which is what gives hierarchy:
#   hero    fills the measure -- the line you would put on a billboard
#   display the same, in the serif face, for the two moments that need a voice change
#   sub     a caption, fixed and small, and deliberately NOT fitted to the frame
# acts are (t0, t1, rows, y_centre, align, colour, drift)
ACTS = [
    (0.12, 2.84, [("sub", "Your site is", -1),
                  ("hero", "the handshake", 1)], 950, "left", CREAM, 56, 1.0),
    (3.02, 5.34, [("sub", "Most sites are", -1),
                  ("hero", "somebody else's", 1),
                  ("hero", "template", -1)], 1018, "left", INK, -46, 1.30),
    (5.52, 7.84, [("hero", "No builder.", -1),
                  ("hero", "No framework.", 1),
                  ("sub", "Just the three languages the browser already speaks", -1)],
     946, "right", INK, 44, 1.45),
    (8.02, 9.84, [("sub", "Hand-written, top to bottom", -1),
                  ("hero", "HTML. CSS. JS.", -1)], 1024, "center", INK, 34, 1.22),
    (10.02, 11.84, [("display", "Budgeted", -1),
                    ("sub", "LCP  ·  CLS  ·  INP set before the first line", -1)],
     934, "center", CREAM, 26, 1.22),
    (12.02, 13.84, [("hero", "Accessible", -1),
                    ("hero", "by default", 1),
                    ("sub", "WCAG 2.2 AA, not bolted on afterwards", -1)], 1012, "left", CREAM, -30, 1.16),
    (14.02, 15.84, [("display", "Yours", -1),
                    ("display", "outright.", 0)], 968, "left", CREAM, 34, 1.0),
    (16.02, 17.84, [("hero", "No lock-in.", -1),
                    ("hero", "No seat licences.", 2),
                    ("sub", "The repository, the deploy steps, a walkthrough", -1)],
     1012, "center", CREAM, 26, 1.24),
]
END = (18.02, 21.62)


class Words(FK.ScreenCard):
    z = 40

    def __init__(self, film):
        super().__init__(film, None, self.z)

    def draw(self, c, res, t):
        for (t0, t1, rows, yc, align, rgb, drift, ceil_of) in ACTS:
            if not (t0 - 0.02 <= t <= t1 + 0.34):
                continue
            # the act, like its lines, is already mostly there on the frame after the cut
            a = (0.93 + 0.07 * ramp(t, t0, 0.16)) * (1 - ramp(t, t1, 0.15))
            if a <= 0.01:
                continue
            maxw = SW - (135 if align == "center" else 128)
            # one size per role, the smallest that fits ALL of that role's lines: a type block with
            # three different headline sizes is the single most common amateur tell
            sz = []
            for role, text, _mk in rows:
                if role == "hero":
                    sz.append(fit(text, maxw, 330))
                elif role == "display":
                    sz.append(fit(text, maxw, 360, "display"))
                else:
                    sz.append(min(52.0, fit(text, maxw, 52)))
            # A block is one size. The smallest-fitting line sets it, and the other lines may grow
            # only a fifth above that -- otherwise a two-word line balloons to twice its neighbour
            # and the block stops reading as one thought (the classic type-film failure).
            for role, ceil in (("hero", ceil_of), ("display", min(ceil_of, 1.20))):
                idx = [i for i, r in enumerate(rows) if r[0] == role]
                if idx:
                    small = min(sz[i] for i in idx)
                    for i in idx:
                        sz[i] = min(sz[i], small * ceil)
            gap = [min(28.0, sz[i] * 0.16) for i in range(len(rows))]
            total = sum(sz) + sum(gap)
            y = yc - total / 2
            self.screen(c, t)
            for li, (role, text, mk) in enumerate(rows):
                # A beat-synced cut is an ARRIVAL, not a fade: the words are already half-lit on the
                # first frame after the cut and settle in 0.2 s. Ramping from zero leaves the frame
                # empty for five frames after every hit, which on a music bed reads as a glitch.
                lu = ramp(t, t0 + li * 0.07, 0.18)
                la = a * (0.88 + 0.12 * lu)
                if la <= 0.01:
                    continue
                face = str(FK.DISPLAY if role == "display" else FK.UI)
                ln = ty.layout(text, face, sz[li])
                k = (1.0 + 0.115 * (1 - _ease(lu))) * (1.0 + 0.045 * hit(t, t0 + li * 0.085, 0.24))
                base = y + sz[li] * 0.78
                ax = {"left": 92.0, "center": SW / 2, "right": SW - 92.0}[align]
                c.save()
                c.translate(ax, base + (1 - _ease(lu)) * drift)
                c.scale(k, k)
                nw = max(1, len(ln.words))

                def a_word(wi, _n=nw, _u=lu):
                    return 0.60 + 0.40 * clamp((_u * (_n + 1.5) - wi) / 1.0)

                # One emphasis per line, and never the same trick twice on one line:
                # a highlighter bar needs words either side of it, so single-word lines get the
                # colour accent instead -- a bar across a whole word just reads as a chip.
                acc = None
                msz = 0.62 * sz[li]        # the bar belongs to the line, not to the point size
                if 0 <= mk < nw and nw > 1:
                    wd = ln.word_at(mk)
                    mku = clamp((lu - 0.24) / 0.42)
                    if wd is not None and mku > 0:
                        x0 = {"left": 0.0, "center": -ln.width / 2, "right": -ln.width}[align]
                        bx = x0 + wd.x - sz[li] * 0.04
                        c.drawRect(skia.Rect.MakeXYWH(bx, -msz * 0.30, (wd.w + sz[li] * 0.08) * mku, msz * 0.34),
                                   P(VERM, 0.58 * a))
                elif 0 <= mk < nw and nw > 1:
                    acc = 0 if rgb == CREAM else 1
                ty.draw(c, ln, 0, 0, rgb=rgb, a=la, align=align, a_word=a_word,
                        rgb_word=(lambda wi, col, _a=acc, _t0=t0 + li * 0.14:
                                  (VERM if _a == 0 else (150, 44, 16)) if wi == mk and ramp(t, _t0 + 0.18, 0.3) > 0.5
                                  else col) if acc is not None else None)
                c.restore()
                y += sz[li] + gap[li]
            c.restore()


class EndCard(FK.ScreenCard):
    """The address, held long enough to be read and short enough not to sit."""

    z = 42

    def __init__(self, film):
        super().__init__(film, None, self.z)

    def draw(self, c, res, t):
        t0, t1 = END
        if not (t0 - 0.02 <= t <= t1):
            return
        a = ramp(t, t0, 0.5)
        self.screen(c, t)
        sz = fit("ZERO VAST", SW - 190, 200, "display")
        ty.draw(c, ty.layout("ZERO VAST", str(FK.DISPLAY), sz), SW / 2, 1120, rgb=CREAM, a=a, align="center")
        rule = clamp((t - t0 - 0.28) / 0.5)
        c.drawRect(skia.Rect.MakeXYWH(SW / 2 - 170 * rule, 1162, 340 * rule, 3.0), P(VERM, a))
        ty.draw(c, ty.layout("Websites built to perform", str(FK.UI), 64), SW / 2, 1258,
                rgb=(255, 208, 168), a=ramp(t, t0 + 0.25, 0.4), align="center")
        ty.draw(c, ty.layout("zero-vast.vercel.app", str(FK.UI), 76), SW / 2, 1378,
                rgb=CREAM, a=ramp(t, t0 + 0.55, 0.45), align="center")
        ty.draw(c, ty.layout("Khammam, Telangana   ·   one point of contact", str(FK.UI), 34), SW / 2, 1448,
                rgb=(232, 218, 202), a=ramp(t, t0 + 0.75, 0.4), align="center")
        c.restore()


class Cuts(Item):
    z = 70

    def __init__(self):
        super().__init__(-5, None, 70, sfx=False)
        self.tr = [(CUTS[2], TR.CardSwing(dur=0.42, rgb=(232, 215, 186))),
                   (CUTS[3], TR.Whip(dur=0.22, direction=-1)),
                   (CUTS[4], TR.PushThrough(dur=0.38)),
                   (CUTS[6], TR.Curtain(dur=0.28, direction=1, rgb=(233, 94, 40), bands=6)),
                   (CUTS[8], TR.Leak(dur=0.65, colour=(255, 186, 120), x=0.6, y=0.34))]

    def draw(self, c, res, t):
        for t_cut, tr in self.tr:
            if abs(t - t_cut) < 0.45:
                tr.draw(c, t, t_cut)


def build_film(doc):
    """Timed from the cut sheet above, not from a recorded take: no timing.json is read."""
    film = Film(DUR, fps=30, look=dict(board="studio.png", bg=(16, 14, 18), grade=(1.0, 1.0, 1.0),
                                       grain=0.0, glow=0.0, vignette=0.10, curve=0.02, dim=(20, 16, 20)))
    film.fade_in, film.fade_out = 0.28, 0.8
    film.items.remove(film.board)
    film.add(Surface())

    # One framing for every shot: kinetic type must not swim. The cuts come from the picture.
    film.cam(0.0, 540, 960, 1.0)
    film.cam(DUR, 540, 960, 1.0)

    film.add(Words(film))
    film.add(EndCard(film))
    film.add(Cuts())
    film.add(FK.Embers(film, None, n=14, colour=(255, 226, 190), a=0.10, seed=3))
    film.add(Grain())
    film.add(FK.Vignette(film, None, strength=0.42, warm=(12, 9, 12)))

    # every cut is a hit; heavy and light alternate so the ear stops predicting them
    for i, cu in enumerate(CUTS[1:]):
        film.cue("impact" if i % 2 == 0 else "stamp", cu, 0.5)
    film.cue("whoosh", CUTS[3], 0.30)
    film.cue("shimmer", CUTS[7] + 0.25, 0.40)
    film.cue("impact", END[0], 0.55)
    return film
