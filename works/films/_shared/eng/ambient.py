"""Ambient life drawn ON TOP of the painted plates.

Replacing the old vector stages with painted pages took the motion out of the sets with them -- the
film's own skills are blunt about this: a still page with a camera move is a slideshow, and the
energy has to come from things moving *inside* the frame. Everything here is a pure function of t
(no clock, no random state), so a re-render is frame-identical.

All of it is determinism-first: positions come from hashed per-particle constants and sine sums,
never from np.random at draw time.
"""
import math

import skia

import cartoon2 as K
from engine import Item, clamp, ramp

SW, SH = 1080.0, 1920.0
HORIZON = 1180.0


def _hash(i, salt=0):
    """a stable 0..1 per index (no RNG at draw time, so every frame is reproducible)"""
    x = math.sin((i + 1) * 12.9898 + salt * 78.233) * 43758.5453
    return x - math.floor(x)


def dust(c, t, n=26, band=(300, 1800), colour=(255, 244, 214), seed=1, drift=26.0):
    """motes hanging in the hot air: slow, uneven, brighter when they cross the sun"""
    for i in range(n):
        u = (_hash(i, seed) + t * (0.008 + 0.014 * _hash(i, seed + 7))) % 1.0
        x = _hash(i, seed + 3) * (SW + 240) - 120 + math.sin(t * 0.7 + i) * drift
        y = band[0] + (_hash(i, seed + 11) * (band[1] - band[0]) + u * 90) % (band[1] - band[0])
        r = 2.0 + 3.0 * _hash(i, seed + 5)
        a = 0.16 + 0.22 * (0.5 + 0.5 * math.sin(t * 1.7 + i * 2.1))
        c.drawCircle(x, y, r, K.P(colour, a))


def heat_shimmer(c, t, y=HORIZON, amp=7.0, rows=9, a=0.10):
    """the horizon breathing: thin warm bands that slide sideways at different rates"""
    for k in range(rows):
        yy = y - 6 - k * 11
        ph = t * (0.55 + 0.11 * k) + k * 1.7
        for j in range(-1, 4):
            x = j * 320 + math.sin(ph) * 46 + k * 13
            w = 300 - k * 12
            c.drawOval(skia.Rect.MakeXYWH(x, yy, w, 6.0),
                       K.P((255, 238, 200), a * (1 - k / rows) * (0.6 + 0.4 * math.sin(ph * 1.3 + j))))


def grass_line(c, t, y, x0=-120, x1=1200, n=14, h=54, colour=(206, 168, 92), seed=5, a=0.9):
    """tussocks of dry grass along a verge: each tuft is a fan of short blades, and each blade sways
    on its own phase, so the fringe breathes instead of standing to attention"""
    for i in range(n):
        cx = x0 + (x1 - x0) * ((i + 0.5) / n + 0.34 * (_hash(i, seed + 23) - 0.5) / n)
        hh = h * (0.55 + 0.85 * _hash(i, seed) ** 1.3)
        lean = math.sin(t * (0.9 + 0.5 * _hash(i, seed + 2)) + i * 1.7) * hh * 0.16
        for b in range(5):
            f = (b - 2) / 2.0
            tipx = cx + f * hh * 0.42 + lean * (1 - abs(f) * 0.4)
            tipy = y - hh * (1.0 - abs(f) * 0.34)
            p = skia.Path()
            p.moveTo(cx + f * hh * 0.10, y + 2)
            p.quadTo(cx + f * hh * 0.26, y - hh * 0.52, tipx, tipy)
            c.drawPath(p, K.LN(K.mul(colour, 0.88 + 0.22 * _hash(i * 5 + b, seed + 4)),
                               a * (0.9 - 0.1 * abs(f)), max(2.0, hh * 0.055)))


def weeds(c, t, spots, seed=9):
    """little tufts: three blades each, in the cracks, never in the same place twice"""
    for i, (x, y, h) in enumerate(spots):
        for b in range(3):
            off = (b - 1) * h * 0.22
            sway = math.sin(t * 1.35 + i * 2.3 + b) * h * 0.24
            p = skia.Path()
            p.moveTo(x + off * 0.5, y)
            p.quadTo(x + off * 0.7, y - h * 0.5, x + off + sway, y - h)
            c.drawPath(p, K.LN((176, 158, 84), 0.8, max(2.0, h * 0.10)))


class AmbientField(Item):
    """the dry field's own weather -- shimmer, dust, the grass fringe and a drifting cloud shadow"""

    z = 6

    def __init__(self, film, doc):
        super().__init__(-1, None, 6, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        # only where the field is on screen
        L = self.doc.L
        if not (t <= L(20) + 0.2 or t >= L(23) - 0.4):
            return
        dust(c, t, n=30, band=(240, 1560), seed=3)
        heat_shimmer(c, t, y=HORIZON, amp=7)
        grass_line(c, t, HORIZON + 18, n=30, h=58, seed=5)
        grass_line(c, t, 1690, n=14, h=76, seed=8, a=0.75)
        weeds(c, t, [(120, 1760, 54), (980, 1810, 46), (300, 1610, 40)])


class AmbientPot(Item):
    """the pot yard: dust, the shimmer off the water, grass at the base, a lizard's shadow"""

    z = 6

    def __init__(self, film, doc):
        super().__init__(-1, None, 6, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        L = self.doc.L
        if not (L(4) - 0.2 <= t <= L(20) + 0.2):
            return
        dust(c, t, n=22, band=(500, 1700), seed=11, drift=18)
        heat_shimmer(c, t, y=HORIZON, amp=6)
        grass_line(c, t, HORIZON + 16, n=26, h=52, seed=13)
        # steam off the warmed water once the pot is full: a slow column that bends
        lv = clamp((t - L(12)) / max(0.1, L(16) - L(12)))
        if lv > 0.05:
            for k in range(7):
                u = ((t * 0.16 + k / 7) % 1.0)
                yy = 1500 - u * 420
                x = 548 + math.sin(u * 6 + k * 1.3 + t * 0.6) * (16 + 40 * u)
                r = 16 + 52 * u
                c.drawCircle(x, yy, r, K.P((236, 250, 255), 0.10 * lv * (1 - u) ** 1.4))


class AmbientQuiz(Item):
    z = 6

    def __init__(self, film, doc):
        super().__init__(-1, None, 6, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        L = self.doc.L
        if not (L(20) + 0.1 <= t <= L(23)):
            return
        dust(c, t, n=16, band=(520, 1700), seed=21, drift=14)
        grass_line(c, t, HORIZON + 14, n=22, h=44, seed=23, a=0.7)
        weeds(c, t, [(200, 1700, 44), (860, 1780, 38)])
