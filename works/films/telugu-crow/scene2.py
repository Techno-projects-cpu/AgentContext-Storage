"""దాహంగా ఉన్న కాకి (v2) -- the thirsty crow, rebuilt as a screen-space cartoon stage.

Everything is drawn in the pixels of a 1080x1920 design frame: at zoom 1 one unit is one output
pixel, so no art is rendered small and upscaled. The camera is the only thing that scales, and every
card undoes the camera before it draws, so text is always 1:1 crisp.

Stages
  field   the baked field: hot sky, a sun with opinions, cracked ground, a thirsty tree, dust, the pot
  pot     the story: a cut-away pot whose water line and stone pile are always visible together
  quiz    the question card

Every pose is a Track: (time, value) keys joined by smoothstep, so a beat can be nudged without
re-choreographing the shot. Pose times come from doc.L(i)/doc.E(i), never hard-coded.
"""
import math
import pathlib
import sys

import numpy as np
import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
import cartoon2 as K                                                        # noqa: E402
import ty                                                                   # noqa: E402

from engine import Film, Item, clamp, ease_in_out, ease_out_back, ease_out_cubic, paint, ramp  # noqa: E402

BOLD = HERE / "fonts" / "tel700.ttf"
REG = HERE / "fonts" / "tel400.ttf"

SW, SH = 1080.0, 1920.0
HORIZON = 1180.0
GROUND = HORIZON
POT = dict(x=548.0, top=980.0, w=470.0, h=560.0)
POT_GROUND = POT["top"] + POT["h"] * 0.97

LOOK = dict(board="studio.png", bg=(255, 214, 150), grade=(1.01, 1.0, 0.99), grain=0.004,
            glow=0.02, vignette=0.06, curve=0.03, dim=(150, 116, 86))


def lerp(a, b, u):
    return a + (b - a) * u


ALIAS = {"field": ("title",)}


def merge_spans(spans):
    """Union of [a, b] windows -- a stage that owns three separate beats paints them as one."""
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + 0.02:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


class Track:
    """Smoothstep interpolation through (time, value) keys, clamped outside."""

    def __init__(self, keys, ease=True):
        self.k = sorted(keys)
        self.ease = ease

    def __call__(self, t):
        ks = self.k
        if t <= ks[0][0]:
            return ks[0][1]
        if t >= ks[-1][0]:
            return ks[-1][1]
        for i in range(len(ks) - 1):
            (t0, v0), (t1, v1) = ks[i], ks[i + 1]
            if t0 <= t <= t1:
                u = (t - t0) / max(1e-6, t1 - t0)
                return lerp(v0, v1, ease_in_out(u) if self.ease else u)
        return ks[-1][1]


def pulse(t, t0, dur=0.42, s=2.2):
    return ease_out_back(clamp((t - t0) / dur), s)


def hit(t, t0, dur=0.30):
    u = clamp((t - t0) / dur)
    return 0.0 if u >= 1 else 1 - u


def blink_at(t, period=3.6, offset=0.0, dur=0.16):
    u = (t + offset) % period
    return 1.0 - abs(2 * u / dur - 1) if u < dur else 0.0


# ------------------------------------------------------------------ stages
class Stage(Item):
    """Base: a stage is a full-frame set. `name` matches the script's `stage` field."""

    z = 0
    name = "stage"

    def __init__(self, film, doc):
        super().__init__(-50, None, self.z, sfx=False)
        self.film, self.doc = film, doc
        self.spans = []
        mine = {self.name} | set(ALIAS.get(self.name, ()))
        for s in doc.timing["segments"]:
            if s.get("stage") in mine:
                self.spans.append((s["start"] - 0.45, s["end"] + 0.45))
        self.spans = merge_spans(self.spans)

    def active(self, t):
        return any(a <= t <= b for a, b in self.spans)

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        if not self.active(t):
            return
        self.paint(c, res, t)

    def paint(self, c, res, t):
        raise NotImplementedError


class FieldStage(Stage):
    """Hot field: sky, sun, hills, cracked ground, a thirsty tree, dust, the pot's stage-hand props."""

    name = "field"
    z = 0

    def paint(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        hot = 0.34 + 0.5 * clamp((t - L(2)) / max(1.0, L(21) - L(2)))
        K.sky(c, t, hot=hot, horizon=HORIZON)
        K.sun(c, 848, 268, 112, t=t, hot=min(1.0, hot), rays=True)
        for i, (x, y, w, sp) in enumerate(((200, 300, 240, 9), (720, 430, 190, 6), (430, 210, 150, 13))):
            K.cloud(c, (x + t * sp) % 1500 - 200, y, w, a=0.80 - 0.2 * hot)
        K.hills(c, HORIZON + 2, dry=hot, scroll=0.0)
        K.ground(c, GROUND, dry=1.0)
        K.tree(c, 150, HORIZON + 60, 330, sway=0.02 * math.sin(t * 0.9), bare=0.55)
        K.tree(c, 946, HORIZON + 40, 388, sway=0.018 * math.sin(t * 0.8 + 1), bare=0.3)
        for i, (x, y, h) in enumerate(((74, 1660, 78), (250, 1740, 60), (940, 1690, 68), (1012, 1800, 84))):
            K.grass(c, x, y, h, sway=t * 1.1 + i, rgb=K.mix(K.LEAF, (182, 164, 96), 0.72))
        K.heat_lines(c, t, HORIZON + 30, HORIZON + 320, a=0.09)
        K.mote_field(c, t, n=24, a=0.85, origin=(K.WX0, 0))


class PotStage(Stage):
    """The pot's stage: same field, but the camera lives on the pot, so the props are few and near."""

    name = "pot"
    z = 5

    def paint(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        K.sky(c, t, hot=0.55, horizon=HORIZON)
        K.sun(c, 900, 250, 96, t=t, hot=0.6)
        for i, (x, y, w, sp) in enumerate(((120, 330, 200, 7), (760, 420, 160, 9))):
            K.cloud(c, (x + t * sp) % 1500 - 200, y, w, a=0.7)
        K.hills(c, HORIZON + 2, dry=0.8)
        K.ground(c, GROUND, dry=0.95, seed=9)
        for i, (x, y, h) in enumerate(((150, 1810, 74), (960, 1770, 66), (60, 1730, 60), (1030, 1850, 78))):
            K.grass(c, x, y, h, sway=t * 1.0 + i)
        K.mote_field(c, t, n=18, a=0.8, origin=(K.WX0, 0))


class QuizStage(Stage):
    """Quiet card stage: cooler sky, soft ground, nothing moving enough to fight the words."""

    name = "quiz"
    z = 8

    def paint(self, c, res, t):
        K.sky(c, t, hot=0.12, cool=0.42, horizon=HORIZON)
        K.sun(c, 872, 300, 86, t=t, hot=0.0, rays=True)
        K.hills(c, HORIZON + 2, dry=0.35)
        K.ground(c, HORIZON, dry=0.45, cracks=False)
        for i, (x, y, h) in enumerate(((120, 1790, 76), (952, 1830, 68))):
            K.grass(c, x, y, h, sway=t * 1.2 + i)
        K.mote_field(c, t, n=16, a=0.7, origin=(K.WX0, 0))


# ------------------------------------------------------------------ the performers
class CrowActor(Item):
    """The crow, driven by pose tracks: it flies, pants, perches, strains, drops stones, drinks, cheers."""

    z = 20

    def __init__(self, film, doc):
        super().__init__(-2, None, 20, sfx=False)
        self.film, self.doc = film, doc
        self.p = {}
        self._cued = None

    def key(self, name, keys, ease=True):
        self.p[name] = Track(keys, ease)
        return self

    def v(self, name, t, default=0.0):
        tr = self.p.get(name)
        return tr(t) if tr else default

    def draw(self, c, res, t):
        x, y = self.v("x", t, -400), self.v("y", t, 760)
        s = self.v("s", t, 300)
        a = self.v("alpha", t, 1)
        if s < 1 or a <= 0.01 or x < -700 or x > 1800:
            return
        L, E = self.doc.L, self.doc.E
        # panting while it walks thirsty; a happy bounce after the drink
        pant = 0.028 * math.sin(t * 11) * (1 if L(2) <= t <= E(4) else 0)
        joy = 0.05 * math.sin(t * 9) if L(16) <= t <= E(19) else 0.0
        K.crow(c, x, y, s, a=a, look=self.v("look", t, 1), flap=self.v("flap", t, 0),
               head=self.v("head", t, 0) + pant, beak=self.v("beak", t, 0),
               blink=self.v("blink", t, blink_at(t, 3.4, 0.4)), tilt=self.v("tilt", t, 0) + joy,
               bob=self.v("bob", t, 0) + 10 * math.sin(t * 3.1) * (1 - self.v("ground", t, 1)),
               tail=self.v("tail", t, 0), wing_open=self.v("wing_open", t, 0),
               leg=self.v("leg", t, 0.6 * math.sin(t * 6) * (1 - self.v("ground", t, 1))),
               crest=self.v("crest", t, 0), throat=self.v("throat", t, 0))


class PotActor(Item):
    """The pot with its live water line, driven by the one drop list the whole film shares."""

    z = 10

    def __init__(self, film, doc, drops):
        super().__init__(-2, None, 10, sfx=False)
        self.film, self.doc, self.drops = film, doc, sorted(drops)
        self.level0 = 0.06

    def level(self, t):
        lv = self.level0
        for td in self.drops:
            lv += 0.075 * ease_out_cubic(ramp(t, td, 0.5))
        return clamp(lv, 0, 1.0)

    def stones(self, t):
        return sum(1 for td in self.drops if t >= td - 0.02)

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        vis = ramp(t, L(4) + 0.25, 0.8) * (1 - ramp(t, E(18) + 0.7, 0.6))
        if vis <= 0.01:
            return
        K.pot(c, POT["x"], POT["top"], POT["w"], POT["h"], level=self.level(t), a=vis,
              stones=self.stones(t), ripple=(t * 0.7) % 1.0, wobble=t * 1.6)


class PebblePile(Item):
    """The heap of pebbles the crow raids, visibly smaller after every stone it takes."""

    z = 16

    def __init__(self, film, doc, drops):
        super().__init__(-2, None, 16, sfx=False)
        self.drops = sorted(drops)

    def draw(self, c, res, t):
        taken = sum(1 for td in self.drops if t >= td - 0.05)
        rng = np.random.default_rng(21)
        x0, y0 = 236, 1600
        for i in range(26 - taken * 2):
            dx = rng.uniform(-150, 150)
            dy = -rng.uniform(0, 54) - abs(dx) * 0.16
            r = rng.uniform(13, 24) * (1 - abs(dx) / 460)
            if r < 4:
                continue
            K.blob(c, x0 + dx, y0 + dy, r, r * 0.86, (128, 120, 114), 0.95)
            K.blob(c, x0 + dx - r * 0.2, y0 + dy - r * 0.25, r * 0.55, r * 0.40, (176, 166, 156), 0.8)


class LizardActor(Item):
    """The comic sidekick: sits by the pot, blinks, jabbers, then gasps at the end."""

    z = 22

    def __init__(self, film, doc):
        super().__init__(-2, None, 22, sfx=False)
        self.film, self.doc = film, doc

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        vis = ramp(t, L(9) - 0.3, 0.4) * (1 - ramp(t, E(19) + 0.6, 0.5))
        if vis <= 0.01:
            return
        talk = L(9) <= t <= E(10)
        wig = math.sin(t * 5.5) * 0.5 if talk else math.sin(t * 0.9) * 0.12
        gasp = pulse(t, E(18), 0.5, 2.4) if t > E(18) else 0.0
        K.lizard(c, 830, 1520 - gasp * 24, 214 + gasp * 26, a=vis, look=-1, wig=wig,
                 blink=blink_at(t, 3.1, 0.7),
                 mouth=(0.55 + 0.45 * math.sin(t * 9)) if talk else gasp,
                 tail=math.sin(t * 1.6) * 0.6 + (1.5 if gasp else 0), tilt=-0.10 * gasp)


class DropFX(Item):
    """Rings and droplets where each stone hits the water; a puff of dust on the ground."""

    z = 30

    def __init__(self, film, doc, drops):
        super().__init__(-2, None, 30, sfx=False)
        self.drops = sorted(drops)

    def draw(self, c, res, t):
        y = POT["top"] + POT["h"] * 0.90
        for td in self.drops:
            u = ramp(t, td, 0.55)
            if u <= 0 or u >= 1:
                continue
            K.ring(c, POT["x"], y, 12 + 96 * ease_out_cubic(u), 0.5 * (1 - u), w=7, rgb=K.WATER_FOAM)
            for k in range(5):
                ang = -math.pi * (0.15 + 0.7 * k / 4)
                d = 26 + 74 * ease_out_cubic(u)
                K.blob(c, POT["x"] + math.cos(ang) * d, y + math.sin(ang) * d * 0.8,
                       9 * (1 - u) + 2, 7 * (1 - u) + 2, K.WATER_FOAM, 0.8 * (1 - u))


# ------------------------------------------------------------------ text cards
class Card(Item):
    """Base for anything laid out in design pixels: it undoes the camera (and the render scale)."""

    z = 60

    def __init__(self, film, doc, z=60):
        super().__init__(-5, None, z, sfx=False)
        self.film, self.doc = film, doc

    def screen(self, c, t):
        """Undo the camera completely, then map the 1080x1920 design frame onto the output frame.

        The world transform is T(W/2,H/2).S(z.s).R(rot).T(-cx,-cy); a card that only divided by the
        zoom ended up placed in WORLD coordinates and drifted off frame whenever the camera panned.
        This is the exact inverse, so (x, y) below is a design pixel whatever the shot is doing.
        """
        cx, cy, z, rot = self.film.camera(t)
        sc = self.film.render_scale if getattr(self.film, "render_scale", None) else 1.0
        w, h = self.film.frame_w, self.film.frame_h
        k = z * sc
        c.save()
        c.translate(cx, cy)
        c.scale(1.0 / k, 1.0 / k)
        c.rotate(-rot)          # engine hands this straight to skia, so keep its units
        c.translate(-w / 2, -h / 2)
        c.scale(sc, sc)

    def layout(self, text, size, bold=True):
        return ty.layout(text, str(BOLD if bold else REG), size)


class TitleCard(Card):
    z = 61

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        a = ramp(t, L(1) - 0.35, 0.5) * (1 - ramp(t, E(1) + 0.8, 0.55))
        if a <= 0.01:
            return
        t0 = L(1) - 0.30
        self.screen(c, t)
        l1 = self.layout("దాహంగా", 132)
        l2 = self.layout("ఉన్న కాకి", 132)
        for i, ln in enumerate((l1, l2)):
            u = clamp((t - (t0 + i * 0.16)) / 0.55)
            if u <= 0:
                continue
            k = ease_out_back(u, 2.6)
            c.save()
            c.translate(540, 520 + i * 156)
            c.rotate(-1.8 + 1.8 * u + i * 1.2)
            c.scale(k * (1 + 0.015 * math.sin(t * 2.2 + i)), k)
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 244), a=a, align="center", outline=(184, 72, 36), ow=20,
                    shadow=(92, 40, 24))
            c.restore()
        sub = self.layout("ఒక చిన్న కథ", 52, bold=False)
        ua = clamp((t - (t0 + 0.55)) / 0.5)
        ty.draw(c, sub, 540, 830 + (1 - ease_out_cubic(ua)) * 22, rgb=(150, 74, 40), a=a * ua, align="center")
        c.restore()


class CaptionCard(Card):
    """The caption children read: big, bottom, word by word, on a cream plaque with a colour tab."""

    SHOUT = {4, 7, 8, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24}
    HIDE = {1, 9, 10, 18, 19, 23, 24}   # title, the bubble lines, the end card: their words are already on screen

    def draw(self, c, res, t):
        for s in self.doc.timing["segments"]:
            if s["id"] in self.HIDE:
                continue
            t0, t1 = s["start"] - 0.12, s["end"] + 0.30
            if not (t0 <= t <= t1):
                continue
            u = ramp(t, t0, 0.22)
            a = u * (1 - ramp(t, s["end"] + 0.04, 0.26))
            if a <= 0.01:
                continue
            shout = s["id"] in self.SHOUT
            size = ty.fit(s["caption"], str(BOLD), 78 if shout else 62, 940)
            ln = self.layout(s["caption"], size)
            bw, bh = min(ln.width + 78, 1000), size * 1.68
            y = 1586 - (1 - ease_out_cubic(u)) * 40
            k = 1.0 + 0.09 * hit(t, s["start"], 0.26) if shout else 1.0
            self.screen(c, t)
            c.save()
            c.translate(540, y - (16 if shout else 0))
            c.rotate(-1.1 if shout else 0.0)
            c.scale(k, k)
            K.plaque(c, 0, 0, bw, bh, a=a)
            if shout:
                c.drawRRect(skia.RRect.MakeRectXY(K.rect(-bw / 2, -bh / 2, bw, bh), 24, 24),
                            K.LN(K.ORANGE, 0.8 * a, 5))
            prog = clamp((t - s["start"]) / max(0.2, s["end"] - s["start"]))
            cur = int(prog * max(1, len(ln.words)) + 1.02)
            ty.draw(c, ln, 0, size * 0.35, rgb=K.INK, a=a, align="center",
                    rgb_word=lambda wi, col: K.ORANGE if wi <= cur else col)
            c.restore()


class BubbleCards(Card):
    """Diegetic speech: the lizard and the crow talk in bubbles whose tails point at their heads."""

    z = 62

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        items = [("ఏం చేస్తున్నావ్\nకాకీ?", L(9) + 0.05, E(9) + 0.40, 700, 800, 168, 0.68),
                 ("చూస్తూ ఉండు!", L(10) + 0.05, E(10) + 0.30, 700, 800, 154, 0.66),
                 ("అబ్బా!\nబాగుంది!", E(18) - 0.55, E(18) + 0.95, 700, 452, 166, 0.34),
                 ("వావ్!", L(19) + 0.10, E(19) + 0.55, 700, 560, 152, 0.30)]
        for text, t0, t1, sx, sy, size, tailx in items:
            if not (t0 <= t <= t1 + 0.3):
                continue
            a = ramp(t, t0, 0.16) * (1 - ramp(t, t1, 0.22))
            if a <= 0.01:
                continue
            k = pulse(t, t0, 0.34, 2.8)
            while size > 90:
                lines = [self.layout(part, size) for part in text.split("\n")]
                w = max(l.width for l in lines) + 104
                if w <= SW - 110:
                    break
                size -= 6
            h = size * 1.30 * len(lines) + 74
            kk = min(k, 1.0)
            sx = min(max(sx, w / 2 + 26), SW - w / 2 - 26)
            sy = min(max(sy, h / 2 + 160), 1500 - h / 2)
            self.screen(c, t)
            c.save()
            c.translate(sx, sy)
            c.scale(kk, kk)
            K.bubble(c, 0, 0, w, h, a=a, tail=(tailx, 1.0))
            for i, ln in enumerate(lines):
                ty.draw(c, ln, 0, (h / 2 - size * 1.02) + i * size * 1.30 + size * 0.22, rgb=(56, 38, 46),
                        a=a, align="center")
            c.restore()


class CountCard(Card):
    """Telugu numerals ౧ ౨ ౩ popped on every stone, stacked up the left of the pot."""

    z = 63

    def __init__(self, film, doc, drops):
        super().__init__(film, doc, 63)
        self.drops = sorted(drops)

    def draw(self, c, res, t):
        if not self.drops:
            return
        if not (self.drops[0] - 0.1 <= t <= self.drops[-1] + 1.1):
            return
        nums = "౧౨౩౪౫౬౭౮౯౧౦౧౧౧౨౧౩౧౪౧౫"
        self.screen(c, t)
        for i, td in enumerate(self.drops[:16]):
            u = ramp(t, td - 0.04, 0.30)
            if u <= 0:
                continue
            a = u * (1 - ramp(t, td + 0.85, 0.45))
            if a <= 0.01:
                continue
            ln = self.layout(nums[i], 140)
            xx = 214 + (i // 8) * 136
            yy = 1120 - (i % 8) * 112
            k = ease_out_back(u, 2.4) * (1 + 0.14 * hit(t, td, 0.22))
            c.save()
            c.translate(xx + 54 * (1 - ease_out_cubic(u)), yy)
            c.rotate(-8 + 10 * u)
            c.scale(k, k)
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 244), a=a, align="center", outline=K.ORANGE, ow=13,
                    shadow=(96, 44, 26))
            c.restore()


class IdeaCard(Card):
    """The idea: a bulb pops over the crow's head with a ring of rays."""

    z = 58

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        t0, t1 = L(8) - 0.35, E(8) + 1.0
        if not (t0 <= t <= t1):
            return
        a = ramp(t, t0, 0.18) * (1 - ramp(t, t1, 0.3))
        if a <= 0.01:
            return
        k = pulse(t, t0, 0.5, 3.4)
        self.screen(c, t)
        c.save()
        c.translate(600, 762)
        c.scale(k, k)
        for i in range(10):
            ang = 2 * math.pi * i / 10 + t * 0.4
            r0, r1 = 96, 126 + 18 * math.sin(t * 6)
            c.drawLine(math.cos(ang) * r0, math.sin(ang) * r0, math.cos(ang) * r1, math.sin(ang) * r1,
                       K.LN((255, 208, 112), 0.9 * a, 8))
        K.glow(c, 0, -12, 150, (255, 226, 140), 0.45 * a)
        c.drawCircle(0, -20, 54, K.P((255, 224, 116), a))
        c.drawCircle(-16, -36, 19, K.P((255, 250, 220), 0.9 * a))
        c.drawRRect(K.rrect(-23, 32, 46, 30, 8), K.P((152, 142, 130), a))
        for k2 in range(3):
            K.star(c, -108 + k2 * 108, -104 + 18 * k2, 15 + 6 * math.sin(t * 5 + k2), a=a * 0.9, rot=t * 2)
        c.restore()


QTEXT = "కాకి ఏం చేసింది?"      # the on-screen question (the spoken line is కా! కా!)


class QuizCard(Card):
    """The question, two answer chips, then the right one lights up when the film says the moral."""

    z = 64

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        if not (L(20) - 0.4 <= t <= min(E(22) + 1.3, L(23) - 0.45)):
            return
        self.screen(c, t)
        q = self.layout(QTEXT, 66)
        u = ramp(t, self.doc.q_at - 0.35, 0.45)
        c.save()
        c.translate(540, 470 - (1 - ease_out_cubic(u)) * 30)
        k = ease_out_back(u, 2.2)
        c.scale(k, k)
        K.plaque(c, 0, 0, 840, 168, a=u)
        ty.draw(c, q, 0, 22, rgb=K.INK, a=u, align="center")
        c.restore()
        chips = [("రాళ్ళు వేసింది", self.doc.chip_at, 596),
                 ("నిద్రపోయింది", self.doc.chip_at + 0.55, 742)]
        for text, t0, y in chips:
            uu = ramp(t, t0, 0.36)
            if uu <= 0:
                continue
            ln = self.layout(text, 54)
            c.save()
            c.translate(540, y + (1 - ease_out_cubic(uu)) * 40)
            kk = ease_out_back(uu, 2.0)
            c.scale(kk, kk)
            K.plaque(c, 0, 0, ln.width + 100, 118, a=uu, rgb=(255, 246, 226))
            ty.draw(c, ln, 0, 19, rgb=(70, 50, 44), a=uu, align="center")
            c.restore()
        ans = ramp(t, self.doc.ans_at, 0.30)
        if ans > 0:
            ln = self.layout("రాళ్ళు వేసింది", 54)
            c.save()
            c.translate(540, 596)
            c.scale(1 + 0.05 * hit(t, self.doc.ans_at, 0.4), 1 + 0.05 * hit(t, self.doc.ans_at, 0.4))
            K.plaque(c, 0, 0, ln.width + 100, 118, a=ans, rgb=(200, 238, 190), edge=(96, 158, 88))
            ty.draw(c, ln, 0, 19, rgb=(30, 84, 40), a=ans, align="center")
            c.restore()
            for k3 in range(4):
                a2 = ramp(t, self.doc.ans_at + 0.04 + k3 * 0.08, 0.22) * (1 - ramp(t, E(22) + 0.5, 0.45))
                K.star(c, 540 + (-1 if k3 % 2 else 1) * (110 + k3 * 62), 596 - 52 - 16 * k3,
                       26 * a2 + 5, a=a2, rot=t * 1.6 + k3)


class EndCard(Card):
    """The moral on a paper card that lands, then the goodbye."""

    z = 65

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        if t < L(23) - 0.42:
            return
        self.screen(c, t)
        u = ramp(t, L(23) - 0.45, 0.55)
        if u <= 0:
            return
        c.save()
        c.translate(540, 1236)
        k = ease_out_back(u, 2.0)
        c.scale(k, k)
        K.plaque(c, 0, 0, 912, 272, a=u, rgb=(255, 248, 232))
        l1 = self.layout("ఓపిక ఉంటే,", 60)
        l2 = self.layout("ఏదీ అసాధ్యం కాదు!", 66)
        ty.draw(c, l1, 0, -36, rgb=(140, 74, 44), a=u, align="center")
        ty.draw(c, l2, 0, 54, rgb=K.INK, a=u, align="center")
        c.restore()
        b = ramp(t, E(23) - 0.05, 0.4)
        if b > 0:
            ln = self.layout("బై బై!", 96)
            c.save()
            c.translate(540, 1580 + 34 * math.sin(t * 2.4))
            kk = ease_out_back(b, 2.6)
            c.scale(kk, kk)
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 244), a=b, align="center", outline=(184, 72, 36), ow=16,
                    shadow=(92, 40, 24))
            c.restore()


# ------------------------------------------------------------------ film
def build_film(doc):
    L, E = doc.L, doc.E
    duration = doc.duration

    # ---- scripted instants, measured from the words themselves
    def at(i, part):
        """Time inside line i where `part` starts, by letter share (Telugu has no spaces to trust)."""
        s = doc.seg[i]
        vo = s["vo"]
        k = vo.find(part)
        if k < 0:
            return s["start"]
        return s["start"] + (s["end"] - s["start"]) * k / max(1, len(vo))

    doc.q_at = at(20, "ఏం")
    doc.chip_at = at(20, "రాళ్ళు")
    doc.ans_at = at(22, "తెలివి") - 0.15

    # ---- the stone drops: one list drives the pot, the numerals, the rings and the sound
    drops = []
    t = L(12) + 0.45
    while t < E(13) + 0.2:
        drops.append(t)
        t += 0.62
    t = L(14) + 0.25
    while len(drops) < 12 and t < E(15) + 0.6:
        drops.append(t)
        t += 0.42
    drops = sorted(drops)
    doc.drops = drops

    film = Film(duration, fps=30, look=LOOK)
    film.fade_in, film.fade_out = 0.7, 1.6
    film.items.remove(film.board)                 # the stage paints its own sky

    for st in (FieldStage(film, doc), PotStage(film, doc), QuizStage(film, doc)):
        film.add(st)
    film.add(PotActor(film, doc, drops))
    film.add(PebblePile(film, doc, drops))
    crow = film.add(CrowActor(film, doc))
    film.add(LizardActor(film, doc))
    film.add(DropFX(film, doc, drops))
    film.add(IdeaCard(film, doc))
    film.add(TitleCard(film, doc))
    film.add(CaptionCard(film, doc))
    film.add(BubbleCards(film, doc))
    film.add(CountCard(film, doc, drops))
    film.add(QuizCard(film, doc))
    film.add(EndCard(film, doc))

    # ---- the crow's life, as pose tracks (times are the narration's, not guesses)
    crow.key("ground", [(0, 0), (L(2) + 0.35, 0), (L(2) + 0.45, 1), (L(19) - 0.2, 1), (L(19) + 0.15, 0),
                        (E(19) + 0.1, 0), (E(19) + 0.3, 1), (duration, 1)])
    crow.key("x", [(0, -520), (E(1), -120), (L(2) + 0.3, 300), (L(3), 470), (E(3), 300),
                   (L(4) - 0.15, 430), (E(4) + 0.15, 548), (L(5) - 0.1, 548), (E(18) + 0.2, 548),
                   (L(19) - 0.1, 560), (E(19) + 0.1, 380), (L(19) + 0.5, 540), (L(20) - 0.2, 430),
                   (E(20), 430), (L(21) + 0.4, 300), (duration, 300)])
    rim = POT["top"] - 0.46 * 300 + 16
    crow.key("y", [(0, 560), (E(1), 660), (L(2) + 0.3, 1240), (L(3), 1300), (L(4) - 0.15, 980),
                   (E(4), 980), (L(5) - 0.1, rim + 14), (E(18) + 0.2, rim + 14), (L(19), 900), (E(19) + 0.1, 560),
                   (L(19) + 0.5, 940), (L(20), 1300), (E(20), 1300), (L(21), 1360), (duration, 1360)])
    crow.key("s", [(0, 250), (E(1), 300), (L(2) + 0.3, 330), (L(3), 330), (L(4) - 0.15, 260),
                   (E(4), 270), (L(5) - 0.1, 330), (L(6), 350), (E(7), 360), (L(8), 330),
                   (E(10), 320), (L(11), 300), (E(18) + 0.2, 300), (L(19), 250), (E(19), 220),
                   (L(20), 290), (E(20), 290), (L(21), 280), (duration, 280)])
    crow.key("flap", [(0, 0.6), (L(2) + 0.1, 0.6), (L(2) + 0.4, 0), (L(19) - 0.3, 0), (L(19) - 0.05, 0.8),
                      (E(19) + 0.2, 0.2), (E(19) + 0.35, 0), (duration, 0)])
    crow.key("wing_open", [(0, 1.0), (L(2) + 0.4, 0.0), (L(19) - 0.35, 0.0), (L(19) - 0.05, 1.0),
                           (E(19) + 0.3, 1.0), (E(19) + 0.45, 0.0), (duration, 0.0)])
    crow.key("look", [(0, 1), (L(19) - 0.35, 1), (L(19) - 0.05, -1), (E(19) + 0.4, 1), (duration, 1)])
    crow.key("crest", [(0, 0), (L(8) - 0.25, 0), (L(8) + 0.3, 1), (E(8) + 0.7, 0.25),
                       (L(22), 0.45), (duration, 0.35)])
    crow.key("alpha", [(0, 1), (L(9) - 0.25, 1), (L(9), 0.0), (L(11) - 0.15, 0.0), (L(11) + 0.1, 1),
                       (L(19) - 0.1, 1), (E(19) + 0.1, 0.0), (L(20) - 0.1, 0.0),
                       (L(20) - 0.05, 0.0), (duration, 0.0)])
    # small acting beats: lean in to strain, hop of surprise, nod of satisfaction
    crow.key("tilt", [(0, 0), (L(6), 0), (L(6) + 0.5, 0.16), (E(7), 0.16), (E(7) + 0.3, 0.0),
                      (E(18), 0.0), (E(18) + 0.25, -0.14), (E(18) + 0.8, 0.0), (duration, 0.0)])
    crow.key("beak", [(0, 0), (L(7) - 0.2, 0), (E(7) + 0.4, 0.55), (L(8) - 0.1, 0), (L(16), 0),
                      (L(17), 0.9), (E(18), 0.2), (E(18) + 0.3, 0.85), (E(18) + 1.0, 0), (duration, 0)])
    crow.key("throat", [(0, 0), (L(16), 0), (L(16) + 0.3, 1), (L(16) + 0.6, 0), (L(16) + 0.9, 1),
                        (E(17), 0), (duration, 0)])

    # ---- camera: a framing per beat; cuts between stages, pushes inside them
    cam = [(0, 540, 720, 1.00), (E(1) - 0.25, 500, 780, 1.04),
           (L(2), 400, 960, 1.16), (E(2), 560, 1080, 1.22),
           (L(3), 480, 1240, 1.34), (E(3), 400, 1300, 1.40),
           (L(4) - 0.15, 520, 1000, 1.06), (L(4) + 0.55, 548, 1240, 1.42),
           (L(5), 548, 1240, 1.62), (L(6), 566, 1130, 1.92), (E(7), 566, 1120, 2.02),
           (L(8), 520, 1000, 1.70), (E(8) + 0.2, 508, 980, 1.64),
           (L(9), 760, 1180, 1.42), (E(10), 780, 1160, 1.36),
           (L(11) - 0.25, 420, 1300, 1.40), (E(11) + 0.2, 470, 1240, 1.46),
           (L(12), 548, 1180, 1.62), (E(13), 548, 1150, 1.68),
           (L(14), 548, 1120, 1.74), (L(15) + 0.15, 548, 1100, 1.80),
           (L(16), 570, 1080, 1.96), (E(18) + 0.25, 556, 1080, 2.04),
           (L(19) - 0.05, 520, 900, 1.40), (E(19) + 0.15, 460, 740, 1.24),
           (L(20) - 0.35, 540, 1080, 1.16), (E(22) + 0.35, 540, 1080, 1.12),
           (L(23) - 0.3, 540, 1240, 1.08), (duration, 540, 1270, 1.03)]
    for tt, x, y, z in cam:
        film.cam(tt, x, y, z)

    # ---- sound: the story's own noises on the beats
    film.cue("whoosh", L(2) + 0.05, 0.45)
    film.cue("drop", L(4) + 0.4, 0.5)
    film.cue("impact", L(5), 0.4)
    film.cue("tick", L(6) + 0.8, 0.5)
    film.cue("shimmer", L(8), 0.65)
    film.cue("pop", L(9) + 0.15, 0.5)
    film.cue("tick", L(11), 0.35)
    for i, td in enumerate(drops):
        film.cue("drop" if i % 2 == 0 else "tick", td, 0.55 if i < 3 else 0.42)
    film.cue("riser", L(15) - 0.1, 0.45)
    film.cue("shimmer", L(16) + 0.1, 0.5)
    film.cue("whoosh", L(19) + 0.1, 0.5)
    film.cue("stamp", L(20), 0.45)
    film.cue("shimmer", L(22), 0.5)
    film.cue("impact", L(23), 0.4)
    return film
