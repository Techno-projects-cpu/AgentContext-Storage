"""ZERO VAST -- "Websites built to perform." (English, 9:16, ~35 s)

Same medium as the crow film, an advert's grammar: painted gouache plates (a Khammam dusk, a working
desk at midnight, a phone in a dark room), flat cut-out props that land on the beat, an ambient layer
that keeps the page breathing, and kinetic type.

Every claim on screen comes from zero-vast.vercel.app: hand-written HTML/CSS/JS, no page-builder
bloat or framework tax, Core Web Vitals budgets set before the build, WCAG 2.2 AA built in, the
repository + deploy steps + walkthrough handed over. Nothing here is invented.
"""
import math
import pathlib
import sys

import numpy as np
import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE.parent / "_shared" / "eng"))

import ambient as AMB                                                     # noqa: E402
import filmkit as FK                                                      # noqa: E402
import ty                                                                 # noqa: E402
from filmkit import (BigType, Captions, Embers, Label, Prop, ScreenCard, Stage, Vignette, Wash,   # noqa: E402
                     Halftone, P, LN, plaque, rich_type, type_line, type_fit, pop, hit, ramp, clamp)
from engine import Film, Item, ease_out_cubic                                         # noqa: E402

SW, SH = 1080.0, 1920.0
HORIZON = 1180.0

INK = (24, 20, 26)
CREAM = (250, 244, 232)
VERM = (224, 90, 43)
OCHRE = (224, 160, 58)
NAVY = (27, 33, 56)
GLASS = (207, 230, 239)

LOOK = dict(board="studio.png", bg=(28, 30, 46), grade=(1.01, 1.0, 1.0), grain=0.004,
            glow=0.02, vignette=0.06, curve=0.03, dim=(40, 30, 34))


# ================================================================= sets
class Dusk(Stage):
    name, plate, z = "dusk", "zv_dusk", 0


class Desk(Stage):
    name, plate, z = "desk", "zv_desk", 2


class Glass(Stage):
    name, plate, z = "glass", "zv_glass", 3


class End(Stage):
    name, plate, z = "end", "zv_end", 4


class Life(Item):
    """Ambient life over the plate: dust in the lamp light, a shimmer off the plain, weeds on the verge."""

    z = 8

    def __init__(self, film, doc):
        super().__init__(-2, None, 8, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        st = self.film._stage
        if st == "dusk":
            AMB.heat_shimmer(c, t, HORIZON + 40, amp=6.0, rows=7, a=0.07)
            AMB.grass_line(c, t, 1790, x0=-160, x1=1240, n=13, h=64, colour=(196, 150, 86), seed=3, a=0.45)
        elif st == "desk":
            AMB.dust(c, t, n=26, band=(300, 1200), colour=(255, 210, 150), seed=5, drift=20)
        elif st == "glass":
            AMB.dust(c, t, n=14, band=(200, 1700), colour=(180, 200, 240), seed=7, drift=16)
        else:
            AMB.dust(c, t, n=12, band=(200, 1500), colour=(255, 226, 190), seed=9, drift=10)


# ================================================================= cut-out art
def card_base(c, w, h, a, rgb=(250, 246, 236), edge=(196, 182, 160), r=18, shadow=1.0):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 6, -h / 2 + 12, w, h), r, r),
                P((10, 8, 12), 0.28 * a * shadow))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), P(rgb, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), LN(edge, 0.9 * a, 2.4))


def browser(c, t, k, a, w=560, h=420, skeleton=True, accent=None, dead=False):
    """a generic template site: identical blocks, identical everything"""
    c.save()
    c.scale(k, k)
    card_base(c, w, h, a)
    # chrome bar
    c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 2, -h / 2 + 2, w - 4, 54), P((232, 226, 214), a))
    for i, col in enumerate(((226, 112, 96), (226, 190, 96), (150, 200, 140))):
        c.drawCircle(-w / 2 + 30 + i * 26, -h / 2 + 29, 8, P(col, 0.9 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 100, -h / 2 + 18, w - 140, 22), 11, 11),
                P((244, 240, 232), a))
    y = -h / 2 + 92
    if skeleton:
        blocks = ((0.62, 34, (196, 190, 180)), (0.42, 18, (214, 208, 198)),
                  (0.86, 120, (206, 200, 190)), (0.70, 16, (216, 210, 200)), (0.50, 16, (216, 210, 200)))
        for frac, bh, col in blocks:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34, y, (w - 68) * frac, bh), 8, 8),
                        P(col, 0.95 * a))
            y += bh + 18
    if accent:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34, -h / 2 + 96, 180, 40), 10, 10),
                    P(accent, 0.95 * a))
    if dead:
        c.drawLine(-w / 2 + 26, -h / 2 + 26, w / 2 - 26, h / 2 - 26, LN((214, 74, 58), 0.75 * a, 12))
    c.restore()


def editor(c, t, k, a, t0=0.0, w=700, h=470):
    """hand-written source: a dark editor with real-looking lines typing themselves on"""
    c.save()
    c.scale(k, k)
    card_base(c, w, h, a, rgb=(26, 28, 40), edge=(58, 62, 82), r=16, shadow=1.2)
    c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 2, -h / 2 + 2, w - 4, 44), P((34, 37, 52), a))
    for i, col in enumerate(((226, 112, 96), (226, 190, 96), (150, 200, 140))):
        c.drawCircle(-w / 2 + 28 + i * 24, -h / 2 + 24, 7, P(col, 0.9 * a))
    lines = [
        [("<!doctype ", (140, 160, 200)), ("html", (226, 120, 90)), (">", (140, 160, 200))],
        [("<header ", (226, 120, 90)), ("class", (140, 190, 230)), ("=", (200, 200, 210)), ("\"masthead\"", (170, 220, 160)), (">", (226, 120, 90))],
        [("  <h1>", (226, 120, 90)), ("Built to perform.", (250, 244, 232)), ("</h1>", (226, 120, 90))],
        [("</header>", (226, 120, 90))],
        [("<main>", (226, 120, 90)), ("  ", (200, 200, 210)), ("<!-- 0 kB of framework -->", (120, 140, 130))],
    ]
    mono = ty.layout("M", str(FK.UI), 26)
    lh = 46
    y = -h / 2 + 96
    for i, parts in enumerate(lines):
        x = -w / 2 + 38
        total = sum(len(s) for s, _ in parts) or 1
        # each line types on over ~0.5 s, one after the other
        prog = clamp((t - (t0 + i * 0.26)) / 0.5)
        shown = int(total * prog)
        used = 0
        for text, col in parts:
            if used >= shown:
                break
            take = text[:max(0, shown - used)]
            used += len(text)
            if not take:
                continue
            ln = ty.layout(take, str(FK.UI), 26)
            cc = tuple(min(255, v) for v in col)
            ty.draw(c, ln, x, y, rgb=cc, a=a, align="left")
            x += ln.width
        if i == len(lines) - 1 and prog >= 1:
            # a green tick in the gutter once the file is written
            u = pop(t, t0 + 5 * 0.26 + 0.4, 0.35, 2.6)
            c.save(); c.translate(w / 2 - 46, y - 8); c.scale(u, u)
            c.drawCircle(0, 0, 15, P((120, 210, 150), a))
            c.drawLine(-7, 0, -1, 7, LN((20, 40, 28), a, 4))
            c.drawLine(-1, 7, 8, -6, LN((20, 40, 28), a, 4))
            c.restore()
        y += lh
    c.restore()


def bar_row(c, t, y, label, frac_target, t0, a, w=380, ok=(120, 210, 150)):
    """one Core Web Vital: a track, a fill, and the honest pass line it has to stay under"""
    ln = ty.layout(label, str(FK.LABEL_B), 30)
    ty.draw(c, ln, -w / 2 - 26, y + 12, rgb=(250, 244, 232), a=a, align="right")
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, y - 14, w, 28), 14, 14),
                P((44, 48, 66), 0.9 * a))
    u = ramp(t, t0, 0.75)
    fill = w * (frac_target * ease_out_cubic(u))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, y - 14, max(28.0, fill), 28), 14, 14),
                P(ok, 0.95 * a))
    # the budget line, standing where the bar must stop
    bx = -w / 2 + w * 0.74
    c.drawLine(bx, y - 26, bx, y + 26, LN((226, 190, 96), 0.9 * a, 3))
    ty.draw(c, ty.layout("budget", str(FK.LABEL), 22), bx, y - 34, rgb=(226, 190, 96), a=a * 0.9, align="center")


def phone(c, t, k, a, w=430, h=760, net="3G"):
    """the site on a cheap phone: the page paints before the network finishes coughing"""
    c.save()
    c.scale(k, k)
    card_base(c, w, h, a, rgb=(26, 28, 38), edge=(72, 76, 96), r=44, shadow=1.3)
    # screen
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 16, -h / 2 + 22, w - 32, h - 44), 34, 34),
                P((246, 243, 236), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-46, -h / 2 + 12, 92, 22), 11, 11), P((18, 20, 28), a))
    # the page: a masthead, a headline, two lines of body -- it is DONE by 0.5 s
    u = ramp(t, 0.0, 0.45)
    top = -h / 2 + 70
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top, w - 80, 34), 8, 8),
                P((228, 222, 210), a * u))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top + 58, (w - 80) * 0.86, 54), 10, 10),
                P(INK, a * u))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top + 128, (w - 80) * 0.95, 18), 9, 9),
                P((210, 204, 194), a * u))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top + 160, (w - 80) * 0.7, 18), 9, 9),
                P((210, 204, 194), a * u))
    cover = ramp(t, top + 190, 0.7)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top + 196, w - 80, 300), 14, 14),
                P((206, 200, 190), a * 0.9 * cover))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 40, top + 516, 170, 46), 23, 23),
                P(VERM, a * cover))
    # the network label: ugly on purpose, this is the point
    ln = ty.layout(net, str(FK.LABEL_B), 26)
    c.save()
    c.translate(w / 2 - 6, -h / 2 + 96)
    c.rotate(8)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-ln.width / 2 - 18, -26, ln.width + 36, 52), 8, 8),
                P((226, 190, 96), a))
    ty.draw(c, ln, 0, 9, rgb=(40, 30, 16), a=a, align="center")
    c.restore()
    c.restore()


def chip(c, x, y, text, a, rgb=(250, 244, 232), ink=INK, pad=26, size=32):
    ln = ty.layout(text, str(FK.UI), size)
    w, h = ln.width + pad * 2, 62
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h), 31, 31), P(rgb, a))
    ty.draw(c, ln, x, y + 11, rgb=ink, a=a, align="center")


def folder(c, t, k, a):
    """the handover: the repository, the deploy steps, the walkthrough -- handed over, not rented"""
    c.save()
    c.scale(k, k)
    w, h = 560, 380
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 8, -h / 2 + 14, w, h), 20, 20),
                P((10, 8, 12), 0.3 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2 + 40, w, h - 40), 20, 20),
                P((232, 196, 132), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, 210, 84), 16, 16), P((240, 206, 144), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 22, -h / 2 + 70, w - 44, h - 110), 12, 12),
                P((252, 246, 234), a))
    rows = (("repository", 0.0), ("deploy steps", 0.45), ("walkthrough", 0.9))
    for i, (text, dt) in enumerate(rows):
        u = ramp(t, dt, 0.4)
        if u <= 0:
            continue
        yy = -h / 2 + 118 + i * 68
        ln = ty.layout(text, str(FK.UI), 34)
        ty.draw(c, ln, -w / 2 + 74, yy, rgb=(38, 32, 30), a=a * u, align="left")
        c.drawCircle(-w / 2 + 46, yy - 12, 13, P((120, 210, 150), a * u))
        c.drawLine(-w / 2 + 40, yy - 12, -w / 2 + 44, yy - 7, LN((20, 40, 28), a * u, 4))
        c.drawLine(-w / 2 + 44, yy - 7, -w / 2 + 53, yy - 19, LN((20, 40, 28), a * u, 4))
    c.restore()


# ================================================================= type
class Furniture(ScreenCard):
    """the advert's own chrome: a kicker, a footnote, a progress hairline"""

    z = 64

    def __init__(self, film, doc):
        super().__init__(film, doc, 64)

    def draw(self, c, res, t):
        self.screen(c, t)
        L, E, dur = self.doc.L, self.doc.E, self.doc.timing["total_duration"]
        # kicker: the maker's own line, top of frame, for the first half
        a = ramp(t, L(1) - 0.5, 0.5) * (1 - ramp(t, L(3) - 0.2, 0.4))
        if a > 0.01:
            ln = ty.layout("ZERO VAST  ·  KHAMMAM, TELANGANA", str(FK.LABEL), 30)
            ty.draw(c, ln, 540, 128, rgb=(252, 246, 234), a=0.72 * a, align="center")
            u = ramp(t, L(1) - 0.35, 0.6)
            w = (ln.width + 60) * ease_out_cubic(u)
            c.drawLine(540 - w / 2, 152, 540 + w / 2, 152, LN((252, 246, 234), 0.30 * a, 2.0))
        # footnote during the performance run: the budget promise, in plain words
        a2 = ramp(t, L(6) - 0.2, 0.4) * (1 - ramp(t, L(8) - 0.75, 0.35))
        if a2 > 0.01:
            ln = ty.layout("BUDGETS SET BEFORE THE FIRST LINE OF CODE", str(FK.LABEL), 28)
            ty.draw(c, ln, 540, 1790, rgb=(250, 244, 232), a=0.62 * a2, align="center")
        # progress hairline
        c.drawRect(skia.Rect.MakeXYWH(0, SH - 5, SW * clamp(t / dur), 5), P(VERM, 0.85))
        c.restore()


class EndLockup(ScreenCard):
    """the mark, the promise, the address: everything a stranger needs to act"""

    z = 66

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        t0 = self.doc.cuts['end'] + 0.10
        if t < t0:
            return
        u = ramp(t, t0, 0.55)
        if u <= 0.01:
            return
        self.screen(c, t)
        # a hairline that draws itself across the frame above the mark
        w = 620 * ease_out_cubic(ramp(t, t0, 0.7))
        c.drawLine(540 - w / 2, 620, 540 + w / 2, 620, LN((255, 220, 170), 0.45 * u, 2.4))
        # ZERO VAST, wordmark
        k = pop(t, t0 + 0.16, 0.6, 2.2)
        c.save()
        c.translate(540, 840)
        c.scale(k, k)
        ln = ty.layout("ZERO VAST", str(FK.DISPLAY), 150)
        ty.draw(c, ln, 0, 0, rgb=(253, 246, 230), a=u, align="center")
        c.restore()
        # the promise
        ua = ramp(t, t0 + 0.35, 0.5)
        ln2 = ty.layout("Websites built to perform.", str(FK.LABEL), 40)
        ty.draw(c, ln2, 540, 946, rgb=(255, 214, 160), a=0.95 * u, align="center")
        # address + contact, each on its own beat
        u2 = ramp(t, t0 + 0.55, 0.45)
        if u2 > 0:
            ln3 = ty.layout("zero-vast.vercel.app", str(FK.UI), 46)
            ty.draw(c, ln3, 540, 1230, rgb=(250, 244, 232), a=u2, align="center")
            c.drawLine(540 - ln3.width / 2, 1252, 540 + ln3.width / 2, 1252, LN((224, 90, 43), 0.9 * u2, 3))
        u3 = ramp(t, t0 + 0.85, 0.45)
        if u3 > 0:
            ln4 = ty.layout("themerchantofdeath2011@gmail.com", str(FK.UI), 30)
            ty.draw(c, ln4, 540, 1330, rgb=(250, 244, 232), a=0.72 * u3, align="center")
            ln5 = ty.layout("ONE POINT OF CONTACT · YOU TALK TO THE PERSON WRITING IT", str(FK.LABEL), 24)
            ty.draw(c, ln5, 540, 1394, rgb=(250, 244, 232), a=0.55 * u3, align="center")
        c.restore()


class StrikeStamp(ScreenCard):
    """a red strike through the template card, and the word that names the problem"""

    z = 62

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        t0, t1 = L(2) + 0.55, self.doc.cuts['desk'] - 0.32
        if not (t0 <= t <= t1):
            return
        u = ramp(t, t0, 0.22)
        a = u * (1 - ramp(t, t1 - 0.3, 0.3))
        if a <= 0.01:
            return
        self.screen(c, t)
        c.save()
        c.translate(540, 760)
        c.rotate(-6)
        w = 720 * ease_out_cubic(u)
        c.drawLine(-w / 2, 0, w / 2, 0, LN((214, 74, 58), 0.92 * a, 16))
        k = pop(t, t0 + 0.08, 0.4, 2.6)
        c.save()
        c.translate(0, -96)
        c.rotate(3)
        c.scale(k, k)
        ln = ty.layout("TEMPLATE", str(FK.LABEL_B), 84)
        ty.draw(c, ln, 0, 0, rgb=(240, 240, 236), a=a, align="center", outline=(214, 74, 58), ow=10)
        c.restore()
        c.restore()


# ================================================================= film
def build_film(doc):
    L, E = doc.L, doc.E
    dur = doc.timing["total_duration"]

    film = Film(dur, fps=30, look=LOOK)
    film.fade_in, film.fade_out = 0.6, 1.1
    film.items.remove(film.board)
    cf = FK.CutFilm(film)
    film = cf

    # The four cuts, in one place. Everything in a shot must be gone before its cut: props hung off
    # a narration line's END look fine in a beat table and then float over the next set for half a
    # second, which is exactly how a film reads as "bad animation".
    C_DESK = L(3) - 0.35
    C_GLASS = L(5) - 0.30
    C_HAND = L(8) - 0.35
    C_END = L(9) - 0.50
    doc.cuts = dict(desk=C_DESK, glass=C_GLASS, hand=C_HAND, end=C_END)

    stages = {s.name: film.add(s(film, doc)) for s in (Dusk, Desk, Glass, End)}
    film._stage = "dusk"

    # the renderer asks which set is up; keep a cheap pointer for the ambient layer
    class StageProbe(Item):
        z = -40

        def __init__(self):
            super().__init__(-50, None, -40, sfx=False)

        def draw(self, c, res, t):
            for nm, st in stages.items():
                if st.active(t):
                    film._stage = nm
                    return

    film.add(StageProbe())
    film.add(Life(film, doc))

    # ---- the cast, each a cut-out placed on the set
    film.add(Prop(film, doc, lambda c, t, k, a: browser(c, t, k, a, w=560, h=430),
                  [(L(1) + 0.55, L(2) + 0.95, 470, 800, 1.0, 1.0)], z=22, enter=0.5, out=0.22, drift=5))
    film.add(Prop(film, doc, lambda c, t, k, a: browser(c, t, k, a, w=500, h=390, accent=(226, 120, 90)),
                  [(L(2) + 1.20, C_DESK - 0.50, 640, 960, 0.95, 1.0)], z=24, enter=0.45, out=0.22, drift=6))
    film.add(StrikeStamp(film, doc))

    film.add(Prop(film, doc, lambda c, t, k, a: editor(c, t, k, a, t0=L(3) + 0.25),
                  [(L(3) + 0.2, C_GLASS - 0.50, 540, 960, 1.0, 1.0)], z=25, enter=0.5, out=0.22, drift=3))

    film.add(Prop(film, doc, lambda c, t, k, a: phone(c, t, k, a),
                  [(C_GLASS + 0.06, L(7) - 0.55, 540, 1000, 1.18, 1.0)], z=26, enter=0.55, out=0.22, drift=4))

    # the budget bars, drawn straight onto the frame beside the phone
    class Budgets(ScreenCard):
        z = 27

        def __init__(self):
            super().__init__(film, doc, 27)

        def draw(self, c, res, t):
            t0, t1 = L(6) + 0.1, self.doc.cuts['hand'] - 0.45
            if not (t0 <= t <= t1):
                return
            a = ramp(t, t0, 0.3) * (1 - ramp(t, t1, 0.3))
            if a <= 0.01:
                return
            self.screen(c, t)
            c.save()
            c.translate(540, 330)
            for i, (lab, frac) in enumerate((("LCP", 0.42), ("CLS", 0.30), ("INP", 0.52))):
                bar_row(c, t, -60 + i * 92, lab, frac, t0 + 0.12 * i, a, w=330)
            c.restore()
            c.restore()

    film.add(Budgets())

    # the accessibility chips stack up one by one
    class Checks(ScreenCard):
        z = 28

        def __init__(self):
            super().__init__(film, doc, 28)

        def draw(self, c, res, t):
            t0, t1 = L(7) + 0.15, self.doc.cuts['hand'] - 0.45
            if not (t0 <= t <= t1):
                return
            a = ramp(t, t0, 0.3) * (1 - ramp(t, t1, 0.3))
            if a <= 0.01:
                return
            self.screen(c, t)
            for i, text in enumerate(("WCAG 2.2 AA", "keyboard", "focus states", "screen-reader tested")):
                u = ramp(t, t0 + 0.18 * i, 0.34)
                if u <= 0:
                    continue
                k = pop(t, t0 + 0.18 * i, 0.34, 2.4)
                c.save()
                c.translate(0, (1 - ease_out_cubic(u)) * 26)
                c.scale(k, k)
                chip(c, 540, 900 + i * 90, text, a * u, rgb=(250, 246, 236) if i % 2 else (226, 236, 222))
                c.restore()
            c.restore()

    film.add(Checks())

    film.add(Prop(film, doc, lambda c, t, k, a: folder(c, t, k, a),
                  [(L(8) + 0.15, C_END - 0.50, 540, 900, 1.0, 1.0)], z=26, enter=0.5, out=0.22, drift=3))

    film.add(Furniture(film, doc))
    film.add(Captions(film, doc, size=60, kind="ui", y=1640, plaque_a=0.50, skip=(9,)))
    film.add(EndLockup(film, doc))
    film.add(Embers(film, doc, n=14, colour=(255, 224, 180), a=0.16, seed=4))
    film.add(Vignette(film, doc, strength=0.34))
    film.add(Halftone(film, doc, pitch=8.0, radius=1.1, a=0.055, line_a=0.03))

    # ---- camera: a shot per set, one motivated move inside each
    cf.shot(0.0, 545, 900, 1.12)
    film.cam(0.0, 545, 900, 1.12)
    film.cam(L(2) - 0.4, 528, 860, 1.20)          # push under the opening line
    cf.shot(L(3) - 0.35, 540, 900, 1.16)          # cut: the desk
    film.cam(L(3) - 0.36, 540, 900, 1.16)
    film.cam(L(5) - 0.45, 536, 960, 1.24)         # drift down the source
    cf.shot(L(5) - 0.30, 520, 900, 1.10)          # cut: the phone in the dark
    film.cam(L(5) - 0.31, 520, 900, 1.10)
    film.cam(L(7) - 0.40, 540, 1040, 1.18)        # punch in on the checks
    cf.shot(L(8) - 0.35, 540, 900, 1.12)          # cut: handover
    film.cam(L(8) - 0.36, 540, 900, 1.12)
    cf.shot(L(9) - 0.50, 540, 960, 1.04)          # cut: the mark
    film.cam(L(9) - 0.50, 540, 960, 1.04)
    film.cam(dur - 0.1, 540, 940, 1.09)           # the one slow push out

    # ---- sound
    film.cue("whoosh", L(1) + 0.5, 0.4)
    film.cue("stamp", L(2) + 0.55, 0.45)
    film.cue("whoosh", L(3) - 0.3, 0.45)
    film.cue("tick", L(3) + 0.4, 0.5)
    film.cue("whoosh", L(5) - 0.25, 0.4)
    for i in range(3):
        film.cue("tick", L(6) + 0.15 + i * 0.12, 0.4)
    for i in range(4):
        film.cue("pop", L(7) + 0.18 + i * 0.18, 0.35)
    film.cue("whoosh", L(8) - 0.3, 0.4)
    film.cue("impact", L(9) - 0.35, 0.45)
    film.cue("shimmer", L(9) + 0.5, 0.5)
    return film
