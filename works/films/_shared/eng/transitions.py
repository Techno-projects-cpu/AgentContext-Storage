"""Transitions with depth -- the menu from `bang-motion/references/techniques.md` §4c.

The skill is blunt about the failure: a flat coloured rectangle sweeping a frame reads cheap, and
repeating one transition type at every cut reads like a template. What works has DEPTH: cards that
rotate in from behind, elements that pass the lens with thickness, a lens flare that only covers
part of the frame, a wipe that travels as a banded curtain rather than a flat slab.

Everything here is a pure function of (t, t_cut) drawn in screen space, so it can sit on top of
whatever the scene is doing on either side of the cut.

  Types: "whip" (direction blur), "card" (rotate in from depth), "leak" (bloom through part of the
  frame), "curtain" (banded wipe with thickness), "push" (3D push-through with parallax strata).
All are meant to be placed ON a cut: pass the cut time, and they close and open around it.
"""
import math

import skia

from filmkit import P, SW, SH, clamp, ease_out_cubic


def _ease_io(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


class Whip:
    """A hard slide with directional blur: the world whips sideways and snaps back.

    Drawing the blur honestly would need the framebuffer; instead we lay streak bands in the
    direction of travel over a brief flash, which reads the same at 30 fps and costs nothing.
    """

    name = "whip"

    def __init__(self, dur=0.26, direction=1):
        self.dur, self.direction = dur, direction

    def draw(self, c, t, t_cut):
        u = (t - (t_cut - self.dur / 2)) / self.dur
        if not 0.0 <= u <= 1.0:
            return
        a = math.sin(u * math.pi) ** 0.7
        # speed streaks: thin horizontal bars, denser near the top and bottom fifths
        step = 26
        rows = int(SH / step)
        for i in range(rows):
            y = i * step + (i * 37 % 11)
            k = 0.35 + 0.65 * abs(math.sin(i * 1.7)) * a
            x0 = (1 - a) * SW * self.direction * (0.3 + 0.7 * ((i * 53) % 29) / 29)
            ln = 90 + 260 * a * (((i * 17) % 13) / 13)
            c.drawRect(skia.Rect.MakeXYWH(x0 - ln / 2, y, ln, 3.0), P((255, 250, 240), 0.16 * k))
        # a wash of the same colour pulls the eye through
        c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), P((250, 244, 232), 0.10 * a))


class CardSwing:
    """The next shot arrives as a card rotating in from behind the frame, with its own shadow.

    The card is perspective-scaled on one axis (a cheap rotateY) so it has thickness as it lands.
    """

    name = "card"

    def __init__(self, dur=0.42, side=1, rgb=(18, 16, 24)):
        self.dur, self.side, self.rgb = dur, side, rgb

    def draw(self, c, t, t_cut):
        # closes into the cut, opens out of it: two halves, one card
        if t_cut - self.dur / 2 <= t <= t_cut + self.dur / 2:
            u = (t - (t_cut - self.dur / 2)) / self.dur
            # Coverage is a narrow pulse, not a sine: the card is fully in front of the lens for a
            # fifth of the move and accelerating in/out of that. Spread spectrum coverage over the
            # whole move and every cut lands on five dim frames -- the exact defect it is meant to fix.
            a = clamp(1.0 - (abs(2 * u - 1) / 0.34) ** 1.35)
            inward = u < 0.5
            sy = (1 - a) if inward else a
            w = SW * 1.15
            h = SH * (0.16 + 0.9 * a)
            y = SH * 0.5 + (1 if inward else -1) * (SH * 0.5 - h / 2) * (1 - a)
            c.save()
            c.translate(SW / 2, y)
            c.scale(1.0, max(0.02, sy))
            c.drawRect(skia.Rect.MakeXYWH(-w / 2 + 9, -h / 2 + 14, w, h), P((0, 0, 0), 0.22 * a))
            c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), P(self.rgb, 0.97 * a))
            c.restore()


class Leak:
    """A lens flare that blooms through 45-60% of the frame at the cut -- never the whole frame."""

    name = "leak"

    def __init__(self, dur=0.5, colour=(255, 196, 120), x=0.5, y=0.45):
        self.dur, self.colour, self.x, self.y = dur, colour, x, y

    def draw(self, c, t, t_cut):
        u = (t - (t_cut - self.dur / 2)) / self.dur
        if not 0.0 <= u <= 1.0:
            return
        a = math.sin(u * math.pi) ** 1.3
        cx, cy = SW * self.x, SH * self.y
        g = skia.GradientShader.MakeRadial(
            skia.Point(cx, cy), SH * 0.42,
            [skia.ColorSetARGB(int(230 * a), *self.colour), skia.ColorSetARGB(int(90 * a), *self.colour),
             skia.ColorSetARGB(0, *self.colour)], [0.0, 0.45, 1.0])
        c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
        # a couple of ghost discs along the flare axis, the way a real lens does it
        for i, (d, r) in enumerate(((0.42, 46), (0.72, 24), (0.95, 68))):
            gx = cx + (SW / 2 - cx) * d * 1.4
            gy = cy + (SH / 2 - cy) * d * 1.4
            c.drawCircle(gx, gy, r * (0.6 + 0.6 * a), P(self.colour, 0.10 * a))


class Curtain:
    """A banded wipe with thickness: alternating tone bands travel across the frame.

    Not a flat slab (the failure the skill names): each band has a lit edge and a shadow edge, so
    the sweep reads as a physical curtain moving in front of the lens.
    """

    name = "curtain"

    def __init__(self, dur=0.34, direction=1, rgb=(233, 94, 40), bands=7):
        self.dur, self.direction, self.rgb, self.bands = dur, direction, rgb, bands

    def draw(self, c, t, t_cut):
        u = (t - (t_cut - self.dur / 2)) / self.dur
        if not 0.0 <= u <= 1.0:
            return
        a = clamp(1.0 - (abs(2 * u - 1) / 0.40) ** 1.3)   # narrow coverage, as CardSwing
        h = SH / self.bands
        for i in range(self.bands):
            off = (i * 0.09) * self.direction
            x = (u * 1.4 + off) * SW * self.direction - SW * 0.2 * self.direction
            w = SW * (0.30 + 0.10 * (i % 3)) * a
            c.drawRect(skia.Rect.MakeXYWH(x, i * h, w, h * 0.92), P(self.rgb, 0.72 * a))
            c.drawRect(skia.Rect.MakeXYWH(x, i * h, w, 3.0), P((255, 246, 232), 0.35 * a))
            c.drawRect(skia.Rect.MakeXYWH(x + w - 4, i * h, 4.0, h * 0.92), P((0, 0, 0), 0.20 * a))


class PushThrough:
    """Layers leave at different speeds: the set pushes past the lens and the new one arrives behind it.

    Strata of the outgoing frame are drawn as expanding rectangles with parallax, which gives the
    push a depth the flat zoom-in lacks.
    """

    name = "push"

    def __init__(self, dur=0.40, rgb=(30, 26, 34)):
        self.dur, self.rgb = dur, rgb

    def draw(self, c, t, t_cut):
        u = (t - (t_cut - self.dur / 2)) / self.dur
        if not 0.0 <= u <= 1.0:
            return
        a = math.sin(u * math.pi) ** 0.9
        cx, cy = SW / 2, SH * 0.55
        for i in range(5):
            k = 1.0 + i * 0.55 + u * (3.2 + i * 0.9)
            w, h = SW * k, SH * k
            c.drawRect(skia.Rect.MakeXYWH(cx - w / 2, cy - h / 2, w, h),
                       P(self.rgb, (0.10 + 0.05 * i) * a))


TYPES = {"whip": Whip, "card": CardSwing, "leak": Leak, "curtain": Curtain, "push": PushThrough}
