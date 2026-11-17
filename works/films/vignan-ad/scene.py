"""VIGNAN VIDYANIKETHAN AI -- "Your books. Your edge." (English, 9:16, ~40 s)

A student sits down with a question paper and a pile of textbooks. The app is the only thing on the
desk that answers: it names the page, opens the page, drills the paper, and then the data goes off --
and it still works.

Every claim on screen is from the product's own site (vignanvidyanikethanai.onrender.com) and its
repository: textbook-grounded answers with a page citation, a page reader, quiz, exam practice,
flashcards, on-device models (Llama 3.2 1B / SmolLM2 / Qwen2.5 via WebLLM) that run offline after one
download, an offline "Bolt" engine that needs no key or download, `npm run check` in CI, MIT licence,
free to try, built by a student of Vignan Vidyanikethan English Medium High School for INSPIRE-MANAK.
The demo answer on the glass (kinetic energy, ½mv²) is textbook physics, which is what the app cites.
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
from filmkit import (Captions, Embers, Halftone, Prop, ScreenCard, Stage, Vignette, P, LN,
                     pop, hit, ramp, clamp)
from engine import Film, Item, ease_out_cubic                                         # noqa: E402

SW, SH = 1080.0, 1920.0

INK = (18, 16, 20)
CREAM = (247, 241, 229)
MINT = (89, 255, 164)       # the app's own accent
GRAPE = (138, 5, 255)       # the app's own accent
LILAC = (230, 218, 255)
NIGHT = (8, 8, 8)           # the app's theme colour

LOOK = dict(board="studio.png", bg=(26, 26, 38), grade=(1.0, 1.0, 1.02), grain=0.004,
            glow=0.02, vignette=0.06, curve=0.03, dim=(28, 24, 34))


# ================================================================= sets
class Study(Stage):
    name, plate, z = "study", "vg_study", 0


class Pages(Stage):
    name, plate, z = "pages", "vg_pages", 2


class Map(Stage):
    name, plate, z = "map", "vg_map", 3


class Room(Stage):
    name, plate, z = "room", "vg_room", 4


class End(Stage):
    name, plate, z = "end", "vg_end", 5


class Life(Item):
    """Dust in the lamp light, and a moth at the window: the page is alive while the words land."""

    z = 8

    def __init__(self, film, doc):
        super().__init__(-2, None, 8, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        st = self.film._stage
        if st == "study":
            AMB.dust(c, t, n=24, band=(280, 1400), colour=(255, 216, 160), seed=5, drift=18)
        elif st == "pages":
            AMB.dust(c, t, n=20, band=(400, 1600), colour=(255, 226, 180), seed=11, drift=14)
        elif st == "map":
            AMB.dust(c, t, n=14, band=(300, 1500), colour=(210, 226, 255), seed=13, drift=12)
        else:
            AMB.dust(c, t, n=18, band=(300, 1700), colour=(255, 220, 170), seed=17, drift=16)


# ================================================================= cut-out art
def glass(c, w, h, a, r=34, rgb=(10, 10, 12), edge=(58, 58, 66)):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 8, -h / 2 + 16, w, h), r, r),
                P((4, 4, 6), 0.34 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), P(rgb, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), LN(edge, 0.9 * a, 2.6))


def app_frame(c, w, h, a, label="ASK"):
    """the app's chrome: near-black surface, mint status, a bottom tab bar -- exactly its palette"""
    glass(c, w, h, a)
    # status row
    c.drawCircle(-w / 2 + 34, -h / 2 + 36, 6, P(MINT, 0.9 * a))
    ln = ty.layout("VIGNAN AI", str(FK.LABEL), 22)
    ty.draw(c, ln, -w / 2 + 52, -h / 2 + 44, rgb=MINT, a=0.9 * a, align="left")
    ln2 = ty.layout("OFFLINE OK", str(FK.LABEL), 20)
    ty.draw(c, ln2, w / 2 - 30, -h / 2 + 44, rgb=(190, 200, 210), a=0.55 * a, align="right")
    # tab bar
    c.drawLine(-w / 2 + 16, h / 2 - 74, w / 2 - 16, h / 2 - 74, LN((70, 70, 78), 0.7 * a, 1.6))
    tabs = ("ASK", "LIBRARY", "QUIZ", "PROGRESS")
    for i, name in enumerate(tabs):
        x = -w / 2 + (i + 0.5) * (w / len(tabs))
        ln = ty.layout(name, str(FK.LABEL), 19)
        ty.draw(c, ln, x, h / 2 - 36, rgb=MINT if i == 0 else (150, 154, 164),
                a=(0.95 if i == 0 else 0.5) * a, align="center")


def ask_card(c, t, k, a, w=760, h=560, answer_at=0.9):
    """the app answering: the question, then the answer, then the citation chip that names the page"""
    c.save()
    c.scale(k, k)
    app_frame(c, w, h, a)
    # the question bubble (user side), typed on
    q = "Why does a heavier ball not fall faster?"
    ln = ty.layout(q, str(FK.UI), 30)
    lines = ty.wrap(q, str(FK.UI), 30, w - 220)
    bw = max(l.width for l in lines) + 48
    bh = 30 * 1.5 * len(lines) + 36
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(w / 2 - bw - 30, -h / 2 + 76, bw, bh), 18, 18),
                P((36, 36, 44), a))
    for i, l in enumerate(lines):
        ty.draw(c, l, w / 2 - bw - 30 + 24, -h / 2 + 76 + 34 + i * 45, rgb=(238, 238, 240), a=a, align="left")
    # the answer: bright, grounded, with the formula pulled out
    u = ramp(t, answer_at, 0.5)
    if u > 0.01:
        aa = a * u
        y = -h / 2 + 96 + bh
        for i, l in enumerate(ty.wrap("Both fall at the same rate. Gravity gives every mass the same "
                                      "acceleration -- what changes is the air resistance.", str(FK.UI), 27, w - 120)):
            ty.draw(c, l, -w / 2 + 30, y + 34 + i * 40, rgb=(212, 214, 220), a=aa * 0.95, align="left")
        y += 40 * 4 + 34
        # the pulled-out line
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 26, y - 30, w - 52, 66), 12, 12),
                    P((18, 34, 26), aa))
        lnf = ty.layout("a = g   (independent of mass)", str(FK.UI), 28)
        ty.draw(c, lnf, -w / 2 + 46, y + 12, rgb=MINT, a=aa, align="left")
        # the citation chip -- the whole promise of the product in one pill
        chip_u = ramp(t, answer_at + 0.55, 0.4)
        if chip_u > 0:
            kk = pop(t, answer_at + 0.55, 0.4, 2.4)
            c.save()
            c.translate(-w / 2 + 30, y + 108)
            c.scale(kk, kk)
            label = "Physics · Class 9 · p. 148"
            lnc = ty.layout(label, str(FK.LABEL_B), 24)
            cw = lnc.width + 74
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(0, -26, cw, 52), 26, 26),
                        P((26, 40, 32), aa * chip_u))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(0, -26, cw, 52), 26, 26),
                        LN(MINT, 0.8 * aa * chip_u, 2.0))
            # a little book glyph, then the words
            c.drawRect(skia.Rect.MakeXYWH(14, -14, 20, 28), P(MINT, aa * chip_u))
            ty.draw(c, lnc, 46, 8, rgb=MINT, a=aa * chip_u, align="left")
            c.restore()
    c.restore()


def page_reader(c, t, k, a, w=700, h=800, t0=0.0):
    """the page itself, opened at the cited number, with the cited line lit"""
    c.save()
    c.scale(k, k)
    # paper
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 6, -h / 2 + 14, w, h), 6, 6),
                P((0, 0, 0), 0.35 * a))
    c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), P((246, 240, 226), a))
    c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, 6, h), P((206, 196, 176), a))
    ln = ty.layout("148", str(FK.LABEL), 26)
    ty.draw(c, ln, 0, -h / 2 + 52, rgb=(150, 140, 122), a=a, align="center")
    y = -h / 2 + 108
    # body text as ruled lines, with two real sentences set in type
    ty.draw(c, ty.layout("LAWS OF MOTION", str(FK.LABEL_B), 34), -w / 2 + 40, y, rgb=(40, 36, 34), a=a, align="left")
    y += 58
    for text, hi in (("In the absence of air resistance, all bodies fall with the", False),
                     ("same acceleration, g, whatever their mass.", False),
                     ("A heavy stone and a light feather dropped together", True),
                     ("land together in a vacuum.", True)):
        u = ramp(t, t0 + 0.15 + 0.12 * (y / 60), 0.4)
        if hi:
            c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 30, y - 30, w - 62, 42), P(MINT, 0.18 * a * u))
        ty.draw(c, ty.layout(text, str(FK.UI), 25), -w / 2 + 40, y, rgb=(60, 54, 50), a=a * 0.95, align="left")
        y += 44
    y += 18
    rr = np.random.default_rng(5)
    for i in range(9):
        wid = (w - 90) * rr.uniform(0.55, 1.0)
        c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 40, y, wid, 12), P((206, 196, 178), a * 0.85))
        y += 30
    # the highlight sweeps across the cited sentence once the chip lands
    c.restore()


def quiz_card(c, t, k, a, w=720, h=620, pick=1.25):
    c.save()
    c.scale(k, k)
    app_frame(c, w, h, a, label="QUIZ")
    ty.draw(c, ty.layout("QUIZ · 10 QUESTIONS", str(FK.LABEL), 24), 0, -h / 2 + 92, rgb=(160, 166, 178), a=a,
            align="center")
    q = "A 2 kg ball moves at 3 m/s. Its kinetic energy?"
    yy = -h / 2 + 150
    for i, l in enumerate(ty.wrap(q, str(FK.UI), 32, w - 120)):
        ty.draw(c, l, 0, yy + i * 46, rgb=(240, 240, 244), a=a, align="center")
    opts = ("6 J", "9 J", "18 J", "36 J")
    for i, o in enumerate(opts):
        u = ramp(t, 0.25 + i * 0.12, 0.34)
        if u <= 0:
            continue
        row_y = yy + 130 + i * 92
        chosen = ramp(t, pick, 0.3) > 0
        right = i == 1
        bg = (18, 40, 30) if (chosen and right) else ((34, 34, 42) if not (chosen and right) else (34, 34, 42))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 46, row_y - 34, w - 92, 68), 16, 16),
                    P(bg, a * u))
        if chosen and right:
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 46, row_y - 34, w - 92, 68), 16, 16),
                        LN(MINT, 0.9 * a, 2.6))
        ty.draw(c, ty.layout(o, str(FK.UI), 30), -w / 2 + 90, row_y + 10,
                rgb=(MINT if chosen and right else (226, 226, 232)), a=a * u, align="left")
        if chosen and right:
            c.drawLine(w / 2 - 96, row_y - 4, w / 2 - 78, row_y + 12, LN(MINT, a, 5))
            c.drawLine(w / 2 - 78, row_y + 12, w / 2 - 52, row_y - 18, LN(MINT, a, 5))
    c.restore()


def exam_hud(c, t, k, a, w=540, h=210):
    """exam practice with real paper timing: a clock, a section, a question count"""
    c.save()
    c.scale(k, k)
    card(c, w, h, a)
    ln = ty.layout("EXAM PRACTICE", str(FK.LABEL), 24)
    ty.draw(c, ln, -w / 2 + 28, -h / 2 + 44, rgb=(60, 54, 48), a=a, align="left")
    ty.draw(c, ty.layout("JEE · NEET · EAPCET TIMING", str(FK.LABEL), 20), -w / 2 + 28, -h / 2 + 74,
            rgb=(130, 120, 110), a=a * 0.9, align="left")
    ty.draw(c, ty.layout("24:00", str(FK.DISPLAY), 62), -w / 2 + 30, h / 2 - 34, rgb=(24, 22, 26), a=a, align="left")
    ty.draw(c, ty.layout("Q 1 / 30", str(FK.LABEL_B), 26), w / 2 - 30, h / 2 - 40, rgb=(60, 54, 48), a=a, align="right")
    c.restore()


def card(c, w, h, a, rgb=(250, 246, 236), edge=(198, 186, 166), r=18):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 6, -h / 2 + 12, w, h), r, r),
                P((10, 8, 12), 0.28 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), P(rgb, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), LN(edge, 0.9 * a, 2.4))


def chip_icon(c, x, y, text, glyph, a):
    ln = ty.layout(text, str(FK.UI), 30)
    w = ln.width + (78 if glyph else 40)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - 34, w, 68), 34, 34),
                P((252, 248, 238), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - w / 2, y - 34, w, 68), 34, 34),
                LN((206, 196, 178), a, 2.2))
    off = 0
    if glyph:
        off = 22
        c.drawCircle(x - w / 2 + 34, y, 15, LN((60, 160, 110), a, 3.2))
    ty.draw(c, ln, x + off, y + 10, rgb=(36, 32, 30), a=a, align="center")


def page_fan(c, t, k, a):
    """flashcards: a fanned stack, the front one flipping under the lamp"""
    c.save()
    c.scale(k, k)
    for i in range(4):
        ang = -16 + i * 9
        c.save()
        c.rotate(ang + 2 * math.sin(t * 0.8 + i) * (i + 1) * 0.3)
        c.translate(0, -i * 10)
        card(c, 420, 540, a * (0.55 + 0.12 * i), rgb=(250, 246, 236) if i else (255, 252, 244))
        if i == 0:
            ty.draw(c, ty.layout("KINETIC", str(FK.LABEL_B), 40), 0, -90, rgb=(28, 26, 30), a=a, align="center")
            ty.draw(c, ty.layout("ENERGY", str(FK.LABEL_B), 40), 0, -38, rgb=(28, 26, 30), a=a, align="center")
            c.drawLine(-90, 4, 90, 4, LN((200, 190, 172), a, 2.4))
            ty.draw(c, ty.layout("½mv²", str(FK.DISPLAY), 70), 0, 92, rgb=(40, 36, 34), a=a, align="center")
            ty.draw(c, ty.layout("tap to flip", str(FK.LABEL), 20), 0, 200, rgb=(150, 140, 128), a=a, align="center")
        c.restore()
    c.restore()


def progress_card(c, t, k, a, w=560, h=380):
    """streaks and progress: seven days, one lit per day, a calm bar chart"""
    c.save()
    c.scale(k, k)
    card(c, w, h, a)
    ty.draw(c, ty.layout("THIS WEEK", str(FK.LABEL), 24), -w / 2 + 28, -h / 2 + 46, rgb=(60, 54, 48), a=a, align="left")
    ty.draw(c, ty.layout("6 DAY STREAK", str(FK.LABEL_B), 28), w / 2 - 28, -h / 2 + 48, rgb=(46, 140, 98), a=a,
            align="right")
    for i in range(7):
        u = ramp(t, 0.2 + i * 0.09, 0.3)
        xx = -w / 2 + 60 + i * ((w - 100) / 6)
        hh = 60 + 130 * (0.4 + 0.6 * ((i * 37) % 11) / 11)
        col = (46, 150, 102) if i < 6 else (216, 210, 198)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(xx - 26, h / 2 - 40 - hh * u, 52, hh * u), 12, 12),
                    P(col, a))
    c.restore()


def friends_card(c, t, k, a, w=480, h=260):
    """study hall: three initials, a duel challenge, a shared quiz"""
    c.save()
    c.scale(k, k)
    card(c, w, h, a)
    ty.draw(c, ty.layout("STUDY HALL", str(FK.LABEL), 24), -w / 2 + 26, -h / 2 + 44, rgb=(60, 54, 48), a=a, align="left")
    for i, (ini, col) in enumerate((("A", (46, 150, 102)), ("R", (110, 70, 190)), ("S", (200, 96, 60)))):
        u = ramp(t, 0.25 + i * 0.12, 0.3)
        if u <= 0:
            continue
        c.drawCircle(-w / 2 + 60 + i * 66, -h / 2 + 110, 26 * u, P(col, a))
        ty.draw(c, ty.layout(ini, str(FK.LABEL_B), 28), -w / 2 + 60 + i * 66, -h / 2 + 120, rgb=(250, 248, 240),
                a=a * u, align="center")
    ty.draw(c, ty.layout("duel · 10 questions", str(FK.UI), 26), -w / 2 + 26, h / 2 - 46, rgb=(70, 64, 58), a=a,
            align="left")
    c.restore()


def dev_card(c, t, k, a, w=440, h=180):
    c.save()
    c.scale(k, k)
    card(c, w, h, a, rgb=(26, 28, 34), edge=(70, 74, 88))
    ln = ty.layout("$ npm run check", str(FK.UI), 30)
    ty.draw(c, ln, -w / 2 + 26, -h / 2 + 52, rgb=(200, 206, 220), a=a, align="left")
    u = ramp(t, 0.3, 0.4)
    if u > 0:
        ty.draw(c, ty.layout("secrets ✓  tests ✓  offline ✓", str(FK.UI), 22), -w / 2 + 26, h / 2 - 34,
                rgb=MINT, a=a * u, align="left")
    c.restore()


# ================================================================= type
class Furniture(Item):
    z = 64

    def __init__(self, film, doc):
        super().__init__(-5, None, 64, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        dur = self.doc.timing["total_duration"]
        a = ramp(t, L(1) - 0.5, 0.5) * (1 - ramp(t, L(3) - 0.2, 0.4))
        if a > 0.01:
            ln = ty.layout("VIGNAN VIDYANIKETHAN AI", str(FK.LABEL), 30)
            ty.draw(c, ln, 540, 126, rgb=(250, 246, 236), a=0.72 * a, align="center")
            w = (ln.width + 60) * ease_out_cubic(ramp(t, L(1) - 0.35, 0.6))
            c.drawLine(540 - w / 2, 150, 540 + w / 2, 150, LN((250, 246, 236), 0.3 * a, 2.0))
        cm = self.doc.cuts.get('map', L(9))
        a2 = ramp(t, L(8) - 0.1, 0.4) * (1 - ramp(t, cm - 0.5, 0.35))
        if a2 > 0.01:
            ty.draw(c, ty.layout("BOOKS IN. PAGES OUT.", str(FK.LABEL), 28), 540, 1788, rgb=MINT,
                    a=0.7 * a2, align="center")
        c.drawRect(skia.Rect.MakeXYWH(0, SH - 5, SW * clamp(t / dur), 5), P(MINT, 0.8))


class EndLockup(ScreenCard):
    z = 66

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        t0 = self.doc.cuts['end'] + 0.10
        if t < t0:
            return
        u = ramp(t, t0, 0.5)
        if u <= 0.01:
            return
        self.screen(c, t)
        # the mark: two words, the second in the app's mint
        k = pop(t, t0 + 0.05, 0.55, 2.2)
        c.save()
        c.translate(540, 700)
        c.scale(k, k)
        ty.draw(c, ty.layout("YOUR BOOKS.", str(FK.DISPLAY), 118), 0, 0, rgb=(250, 246, 236), a=u, align="center")
        ty.draw(c, ty.layout("YOUR EDGE.", str(FK.DISPLAY), 118), 0, 128, rgb=MINT, a=u, align="center")
        c.restore()
        # the honest subtitle: what it is, and who made it
        u1 = ramp(t, t0 + 0.30, 0.45)
        if u1 > 0:
            for i, line in enumerate(("A textbook-grounded study assistant.", "Every answer cites its page.")):
                ty.draw(c, ty.layout(line, str(FK.UI), 36), 540, 1010 + i * 54, rgb=(238, 234, 226),
                        a=0.92 * u1, align="center")
        u2 = ramp(t, t0 + 0.6, 0.45)
        if u2 > 0:
            ty.draw(c, ty.layout("vignanvidyanikethanai.onrender.com", str(FK.UI), 40), 540, 1230,
                    rgb=(250, 246, 236), a=u2, align="center")
            c.drawLine(540 - 360, 1252, 540 + 360, 1252, LN(MINT, 0.85 * u2, 3))
        u3 = ramp(t, t0 + 0.85, 0.45)
        if u3 > 0:
            for i, line in enumerate(("Free to try · works offline · MIT licensed",
                                      "Built by a student of Vignan Vidyanikethan English Medium High School",
                                      "for the INSPIRE-MANAK science fair")):
                ty.draw(c, ty.layout(line, str(FK.LABEL), 24 if i else 26), 540, 1330 + i * 40,
                        rgb=(228, 226, 220), a=(0.72 if i else 0.86) * u3, align="center")
        c.restore()


class OfflineBadge(ScreenCard):
    """the network goes off: a struck-through signal and the two words that matter"""

    z = 63

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        t0, t1 = L(7) + 0.15, self.doc.cuts['map'] - 0.45
        if not (t0 <= t <= t1):
            return
        u = ramp(t, t0, 0.28)
        a = u * (1 - ramp(t, t1 - 0.35, 0.3))
        if a <= 0.01:
            return
        self.screen(c, t)
        k = pop(t, t0, 0.4, 2.6)
        c.save()
        c.translate(300, 452)
        c.scale(k, k)
        # signal bars, then the slash
        for i in range(4):
            hh = 14 + i * 12
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-46 + i * 26, -12 - hh, 18, hh + 12), 5, 5),
                        P((236, 232, 226), 0.5 * a))
        w = 150 * ease_out_cubic(ramp(t, t0 + 0.12, 0.3))
        c.drawLine(-56, 14, -56 + w, -66, LN((226, 88, 62), 0.95 * a, 12))
        c.restore()
        ua = ramp(t, t0 + 0.18, 0.4)
        if ua > 0:
            ln = ty.layout("NO DATA", str(FK.LABEL_B), 54)
            ty.draw(c, ln, 540, 452, rgb=(250, 246, 236), a=ua * a, align="center")
            ln2 = ty.layout("STILL WORKING", str(FK.LABEL_B), 46)
            ty.draw(c, ln2, 540, 514, rgb=MINT, a=ua * a, align="center")
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
    # the cuts, in one place (see the ZeroVast scene for why every prop is keyed off these)
    C_PAGES = L(2) - 0.30
    C_DESK = L(5) - 0.30
    C_OFF = L(7) - 0.30
    C_MAP = L(9) - 0.30
    C_END = L(10) - 0.50
    doc.cuts = dict(pages=C_PAGES, desk=C_DESK, off=C_OFF, map=C_MAP, end=C_END)

    stages = {s.name: film.add(s(film, doc)) for s in (Study, Pages, Map, Room, End)}
    film._stage = "study"

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

    # ---- the cast (every prop dies before the cut: see C_* above)
    # 1. the desk: the question paper the whole thing starts from
    film.add(Prop(film, doc, lambda c, t, k, a: question_paper(c, t, k, a),
                  [(L(1) + 0.25, C_PAGES - 0.55, 540, 900, 1.0, 1.0)], z=22, enter=0.5, out=0.24, drift=3))
    # 2-4. the app answering, and the page it cites
    film.add(Prop(film, doc, lambda c, t, k, a: ask_card(c, t, k, a),
                  [(C_PAGES + 0.12, L(4) + 0.74, 540, 860, 1.0, 1.0)], z=24, enter=0.5, out=0.16, drift=4))
    film.add(Prop(film, doc, lambda c, t, k, a: page_reader(c, t, k, a, t0=L(4) + 0.92),
                  [(L(4) + 0.92, C_DESK - 0.40, 640, 980, 0.78, 1.0)], z=25, enter=0.45, out=0.22, drift=2, spin=1.2))
    # 5-6. the drill: quiz, exam clock, flashcards
    film.add(Prop(film, doc, lambda c, t, k, a: quiz_card(c, t, k, a),
                  [(C_DESK + 0.12, L(6) - 0.45, 500, 860, 0.94, 1.0)], z=25, enter=0.5, out=0.24, drift=3))
    film.add(Prop(film, doc, lambda c, t, k, a: exam_hud(c, t, k, a),
                  [(L(6) + 0.15, C_OFF - 0.55, 560, 1300, 0.95, 1.0)], z=26, enter=0.5, out=0.24, drift=3))
    film.add(Prop(film, doc, lambda c, t, k, a: page_fan(c, t, k, a),
                  [(L(6) + 0.60, C_OFF - 0.55, 300, 900, 0.62, 1.0)], z=24, enter=0.55, out=0.24, drift=2, spin=2))
    # 7-8. offline: the phone with the radio off, and the badge
    film.add(Prop(film, doc, lambda c, t, k, a: offline_phone(c, t, k, a),
                  [(C_OFF + 0.10, C_MAP - 0.55, 540, 1090, 0.95, 1.0)], z=22, enter=0.55, out=0.24, drift=4))
    film.add(OfflineBadge(film, doc))
    # 9. the story of the build: the roadmap sheet
    film.add(Prop(film, doc, lambda c, t, k, a: dev_card(c, t, k, a),
                  [(C_MAP + 0.55, C_END - 0.55, 540, 1440, 0.95, 1.0)], z=27, enter=0.5, out=0.24, drift=2))

    film.add(Furniture(film, doc))
    film.add(FK.Captions(film, doc, size=58, kind="ui", y=1650, plaque_a=0.50, skip=(10,)))
    film.add(EndLockup(film, doc))
    film.add(Embers(film, doc, n=12, colour=(255, 226, 190), a=0.15, seed=9))
    film.add(Vignette(film, doc, strength=0.36, warm=(20, 16, 26)))
    film.add(Halftone(film, doc, pitch=8.0, radius=1.05, a=0.05, line_a=0.028))

    # ---- camera: one framing per set, one move inside each shot, a cut between sets
    cf.shot(0.0, 540, 950, 1.06)
    film.cam(0.0, 540, 950, 1.06)
    film.cam(C_PAGES - 0.45, 530, 900, 1.14)
    cf.shot(C_PAGES, 540, 900, 1.20)              # the book opens
    film.cam(C_PAGES + 0.01, 540, 900, 1.20)
    film.cam(C_DESK - 0.45, 556, 940, 1.32)       # push into the citation
    cf.shot(C_DESK, 540, 900, 1.12)               # back to the desk for the drill
    film.cam(C_DESK + 0.01, 540, 900, 1.12)
    film.cam(L(6) + 0.20, 546, 1000, 1.24)
    cf.shot(C_OFF, 540, 940, 1.16)                # data off
    film.cam(C_OFF + 0.01, 540, 940, 1.16)
    film.cam(C_MAP - 0.45, 534, 1000, 1.26)
    cf.shot(C_MAP, 540, 900, 1.10)                # the roadmap
    film.cam(C_MAP + 0.01, 540, 900, 1.10)
    film.cam(C_END - 0.45, 540, 960, 1.16)
    cf.shot(C_END, 540, 960, 1.03)                # sign-off
    film.cam(C_END + 0.01, 540, 960, 1.03)
    film.cam(dur - 0.1, 540, 950, 1.08)

    # ---- sound
    film.cue("whoosh", L(1) + 0.2, 0.35)
    film.cue("whoosh", C_PAGES - 0.2, 0.4)
    film.cue("tick", C_PAGES + 0.3, 0.4)
    film.cue("pop", L(4) + 0.35, 0.45)
    film.cue("shimmer", L(4) + 0.75, 0.45)
    film.cue("whoosh", C_DESK - 0.2, 0.4)
    film.cue("tick", C_DESK + 0.3, 0.4)
    film.cue("pop", L(5) + 1.2, 0.4)
    film.cue("drop", C_OFF + 0.2, 0.5)
    film.cue("shimmer", L(8) + 0.3, 0.5)
    film.cue("whoosh", C_MAP - 0.2, 0.4)
    film.cue("stamp", L(9) + 0.15, 0.45)
    film.cue("impact", C_END + 0.05, 0.45)
    film.cue("shimmer", C_END + 0.7, 0.5)
    return film


# ---------------------------------------------------------------- two pieces of the cast that need the doc
def question_paper(c, t, k, a):
    """the paper the whole thing starts from: cream sheet, a printed header, ruled answers"""
    c.save()
    c.scale(k, k)
    w, h = 700, 760
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 8, -h / 2 + 16, w, h), 8, 8),
                P((0, 0, 0), 0.34 * a))
    c.save()
    c.rotate(-3)
    c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), P((249, 244, 232), a))
    ty.draw(c, ty.layout("PHYSICS · CLASS 9", str(FK.LABEL_B), 30), 0, -h / 2 + 60, rgb=(40, 36, 34), a=a,
            align="center")
    ty.draw(c, ty.layout("UNIT TEST — 30 MARKS — 45 MIN", str(FK.LABEL), 22), 0, -h / 2 + 92, rgb=(120, 112, 100),
            a=a, align="center")
    c.drawLine(-w / 2 + 40, -h / 2 + 120, w / 2 - 40, -h / 2 + 120, LN((190, 180, 164), a, 2.2))
    qs = ("1.  Why does a heavier ball not fall faster?",
          "2.  A 2 kg ball moves at 3 m/s. Find its KE.",
          "3.  State Newton's third law with one example.")
    for i, q in enumerate(qs):
        yy = -h / 2 + 170 + i * 92
        ty.draw(c, ty.layout(q, str(FK.UI), 27), -w / 2 + 40, yy, rgb=(52, 46, 44), a=a, align="left")
        for j in range(2):
            c.drawLine(-w / 2 + 60, yy + 34 + j * 34, w / 2 - 60, yy + 34 + j * 34, LN((210, 200, 184), a, 1.8))
    # a pencil laid across the bottom right
    c.save()
    c.translate(w / 2 - 150, h / 2 - 120)
    c.rotate(-24)
    c.drawRect(skia.Rect.MakeXYWH(-150, -12, 300, 24), P((226, 176, 74), a))
    c.drawRect(skia.Rect.MakeXYWH(-150, -12, 44, 24), P((220, 120, 110), a))
    c.drawPath(skia.Path().moveTo(150, -12).lineTo(178, 0).lineTo(150, 12).close(), P((232, 214, 186), a))
    c.restore()
    c.restore()
    c.restore()


def offline_phone(c, t, k, a):
    """the same answered question on the phone, with the radio switched off"""
    c.save()
    c.scale(k, k)
    w, h = 460, 820
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 8, -h / 2 + 16, w, h), 48, 48),
                P((0, 0, 0), 0.36 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), 48, 48), P((16, 16, 18), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 14, -h / 2 + 20, w - 28, h - 40), 38, 38),
                P((10, 10, 12), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-52, -h / 2 + 10, 104, 24), 12, 12), P((30, 30, 34), a))
    # status: a struck signal and the word OFFLINE
    for i in range(4):
        hh = 10 + i * 8
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34 + i * 18, -h / 2 + 70 - hh, 12, hh + 10),
                                          3, 3), P((120, 124, 132), 0.55 * a))
    c.drawLine(-w / 2 + 26, -h / 2 + 78, -w / 2 + 100, -h / 2 + 32, LN((226, 88, 62), 0.9 * a, 6))
    ty.draw(c, ty.layout("OFFLINE", str(FK.LABEL_B), 22), w / 2 - 30, -h / 2 + 70, rgb=MINT, a=0.95 * a, align="right")
    # the answer, still there
    y = -h / 2 + 140
    for i, l in enumerate(ty.wrap("Both fall at the same rate. Gravity gives every mass the same acceleration.",
                                  str(FK.UI), 26, w - 80)):
        ty.draw(c, l, -w / 2 + 40, y + i * 38, rgb=(226, 226, 230), a=a, align="left")
    y += 38 * 3 + 30
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34, y - 26, w - 68, 58), 12, 12),
                P((18, 34, 26), a))
    ty.draw(c, ty.layout("a = g", str(FK.UI), 28), -w / 2 + 54, y + 12, rgb=MINT, a=a, align="left")
    y += 74
    lnc = ty.layout("Physics · Class 9 · p. 148", str(FK.LABEL_B), 22)
    cw = lnc.width + 60
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34, y - 24, cw, 48), 24, 24), P((26, 40, 32), a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 34, y - 24, cw, 48), 24, 24), LN(MINT, 0.8 * a, 2))
    ty.draw(c, lnc, -w / 2 + 34 + cw / 2 + 8, y + 8, rgb=MINT, a=a, align="center")
    # the book stack, drawn small at the foot: the knowledge base, on the device
    by = h / 2 - 120
    for i, col in enumerate(("bolt", "grape", "vermilion")):
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-110, by + i * 30, 220 - i * 10, 26), 4, 4),
                    P({"bolt": (46, 143, 102), "grape": (91, 63, 156), "vermilion": (217, 85, 42)}[col], a))
    c.restore()
