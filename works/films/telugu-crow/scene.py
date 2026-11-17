"""దాహంగా ఉన్న కాకి — the thirsty crow, as a cartoon for children. 1080x1920, about 2 minutes.

The film is one continuous cartoon stage (world units are 4K px at zoom 1, so at zoom z a
1080-wide 9:16 frame shows 3840/z x 6827/z world px and one screen px is 1/(1080/3840*z) world px).
Everything that moves is a pure function of t, so any frame can be rendered on its own:

  Backdrop   sky, a sun that gets crosser as the drought bites, hills, baked ground, heat shimmer
  Pot        the story's hero prop, drawn as a cut-away so the water level and the pile of stones
             are always both visible: the whole trick of the story in one picture
  Crow       the bird: flies, pants, perches, leans in, drops stones, drinks, cheers
  Liz        the comic sidekick lizard: blinks, gasps, wiggles
  Words      shaped Telugu (HarfBuzz, see tools/ty.py): title cards, speech bubbles, captions
  Sparkle    the cartoon punctuation: sweat, hearts, sparkles, questions, the idea bulb

Every beat is keyed off doc.L(i)/doc.E(i), the narration timing, so picture and voice stay locked.
"""
import math
import pathlib
import sys

import numpy as np
import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE.parents[2] / "tools"))
import cartoon as K                                    # noqa: E402
import ty                                              # noqa: E402

from engine import Film, Item, clamp, ease_in_out, ease_out_back, ease_out_cubic, paint, ramp  # noqa: E402

BOLD = HERE / "fonts" / "tel700.ttf"
REG = HERE / "fonts" / "tel400.ttf"

FRAME_H = 6827.0            # 4K units of frame height at zoom 1, for a 9:16 film
S1080 = 1080 / 3840.0

# palette: hot dry-season cartoon
SKY_HI = (255, 214, 138)
SKY_LO = (255, 243, 205)
SUN = (255, 196, 84)
HILL_FAR = (176, 206, 150)
HILL_NEAR = (146, 188, 126)
GROUND = (228, 176, 112)
GROUND_DARK = (206, 148, 92)
CLAY = (206, 132, 88)
CLAY_DARK = (150, 92, 62)
WATER = (108, 186, 216)
INK = (44, 34, 38)
CREAM = (255, 250, 238)
ORANGE = (226, 96, 44)
PINK = (232, 96, 120)
LEAF = (86, 148, 96)

LOOK = dict(board="studio.png", bg=(255, 240, 206), grade=(1.02, 1.0, 0.975), grain=0.010, glow=0.05,
            vignette=0.26, curve=0.10, dim=(126, 104, 84))

GROUND_Y = 700.0
POTX = 130.0
POT_W = 800.0
POT_H = 1000.0
POT_TOP = GROUND_Y - POT_H
CROW_S = 600.0
LIZ_S = 300.0


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(a, b, t):
    return ease_in_out(clamp((t - a) / max(1e-6, b - a)))


def seg(doc, i):
    return doc.L(i), doc.E(i)


def pop_in(t, t0, dur=0.42, s=2.0):
    """Scale for something that pops in at t0 (with a little overshoot) and is 1 after."""
    return ease_out_back(clamp((t - t0) / dur), s)


# --------------------------------------------------------------------------- backdrops
class Backdrop(Item):
    """Sky, sun, clouds, hills and the baked ground. `hot` rises through the drought and eases off
    once the crow has drunk; the sun's face follows it."""
    z = -50

    def __init__(self, film, doc):
        super().__init__(-2.0, None, -50, sfx=False)
        self.film, self.doc = film, doc
        self.hot_keys = [(0.0, 0.10), (doc.L(2), 0.55), (doc.L(3), 0.85), (doc.L(4), 0.95),
                         (doc.L(6), 1.0), (doc.L(15), 0.85), (doc.L(16), 0.45), (doc.L(19), 0.20), (doc.E(24), 0.1)]

    def hot(self, t):
        k = self.hot_keys
        if t <= k[0][0]:
            return k[0][1]
        for (t0, v0), (t1, v1) in zip(k, k[1:]):
            if t0 <= t <= t1:
                return lerp(v0, v1, ease_in_out((t - t0) / max(1e-6, t1 - t0)))
        return k[-1][1]

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        cx, cy, z, rot = self.film.camera(t)
        k = res.screen_scale
        halfh = FRAME_H / z / 2 * 1.35
        halfw = halfh * 0.5625 * 1.35
        x0, x1 = cx - halfw, cx + halfw
        y0, y1 = cy - halfh, cy + halfh
        # sky
        dusk = ease_in_out(clamp((t - (self.doc.L(20) + 0.5)) / max(1.0, self.doc.E(23) - self.doc.L(20) - 0.5)))
        hi = tuple(int(lerp(a, b, dusk)) for a, b in zip(SKY_HI, (250, 150, 108)))
        lo = tuple(int(lerp(a, b, dusk)) for a, b in zip(SKY_LO, (255, 206, 170)))
        g = skia.GradientShader.MakeLinear(
            [skia.Point(cx, y0), skia.Point(cx, y0 + halfh * 1.25)],
            [skia.Color(*hi), skia.Color(*lo)], [0.0, 1.0])
        p = skia.Paint(); p.setShader(g)
        c.drawRect(skia.Rect.MakeXYWH(x0, y0, x1 - x0, y1 - y0), p)
        # sun: high at noon, and it sets behind the hills once the story is told
        hot = self.hot(t)
        dusk = ease_in_out(clamp((t - (self.doc.L(20) + 0.5)) / max(1.0, self.doc.E(23) - self.doc.L(20) - 0.5)))
        sy = lerp(-2020 + 300 * (1 - hot), 700.0, dusk)
        # clouds drift slowly across, away from the sun's face
        span = halfw * 2 + 1600
        for i, (dx, dy, w, sp) in enumerate(((-0.30, -1420, 560, 14), (-0.70, -1080, 420, 9), (0.10, -1980, 380, 11))):
            drift = ((t * sp) % span) - span * 0.25
            K.cloud(c, cx + dx * halfw + drift, dy, w, a=0.8)
        c.save()
        c.translate(cx, sy)
        c.scale(1.0 - 0.22 * dusk, 1.0 - 0.22 * dusk)
        K.sun_face(c, 0 + 1160 + 90 * (1 - hot), 0, 300, t=t, hot=hot * (1 - dusk))
        c.restore()
        # hills
        K.hill(c, cx - halfw * 0.55, GROUND_Y, halfw * 1.5, 640, HILL_FAR)
        K.hill(c, cx + halfw * 0.62, GROUND_Y + 10, halfw * 1.4, 520, HILL_NEAR)
        # ground
        c.drawRect(skia.Rect.MakeXYWH(x0, GROUND_Y, x1 - x0, y1 - GROUND_Y + 200), K.P(GROUND, 1.0))
        c.drawRect(skia.Rect.MakeXYWH(x0, GROUND_Y, x1 - x0, 26), K.P((240, 196, 138), 1.0))
        K.dry_cracks(c, cx, GROUND_Y + 220, halfw * 1.5, 300, a=1.0 - 0.35 * hot)
        for i, (dx, h, sw) in enumerate(((-900, 150, 0.10), (-560, 110, -0.12), (620, 130, 0.14),
                                         (980, 100, -0.08), (-1180, 120, 0.06))):
            K.grass_tuft(c, cx + dx, GROUND_Y + 6, h, sway=sw * math.sin(t * 1.1 + i), n=5)
        # heat shimmer while the ground is baking
        if hot > 0.45:
            K.shimmer(c, cx, GROUND_Y - 40, halfw * 1.6, 120, t, a=(hot - 0.45) * 1.5)


class TitleSky(Item):
    """The opening card's sky: extra sunburst behind the title so the first frame has some lift."""
    z = -40

    def __init__(self, t_in, t_out, at):
        super().__init__(t_in, t_out, -40, sfx=False)
        self.at = at

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        a = (1 - ramp(t, self.t_out, 0.8)) * ramp(t, self.t_in, 0.5)
        if a <= 0:
            return
        c.save()
        c.translate(*self.at)
        for i in range(24):
            ang = 2 * math.pi * i / 24 + t * 0.10
            pth = skia.Path()
            pth.moveTo(0, 0)
            pth.lineTo(math.cos(ang - 0.045) * 3200, math.sin(ang - 0.045) * 3200)
            pth.lineTo(math.cos(ang + 0.045) * 3200, math.sin(ang + 0.045) * 3200)
            pth.close()
            c.drawPath(pth, K.P((255, 226, 158), 0.5 * a))
        c.restore()


# --------------------------------------------------------------------------- the pot
class Pot(Item):
    """The pot and everything inside it. Water level and the pile of stones are driven by the very
    same list of stone landings the sound cues use, so picture and 'టప్' never drift apart."""
    z = 5

    def __init__(self, film, doc, drops, start_water=0.12, per_stone=0.0375):
        super().__init__(-1.0, None, 5, sfx=False)
        self.film, self.doc, self.drops = film, doc, sorted(drops)
        self.start_water, self.per_stone = start_water, per_stone
        self.tilt = 0.0

    def level(self, t):
        """Water level 0..1, easing up after each stone lands."""
        lv = self.start_water
        for k, td in enumerate(self.drops):
            if t >= td:
                lv += self.per_stone
        # ease: the newest rise animates in over 0.55 s
        for td in reversed(self.drops):
            if t >= td:
                nxt = lv + self.per_stone
                return lerp(lv, nxt, ease_out_cubic(clamp((t - td) / 0.55)))
        return lv

    def stones(self, t):
        return sum(1 for td in self.drops if t >= td)

    def bounds(self, res):
        r = POT_W * 1.2
        return skia.Rect.MakeLTRB(POTX - r, POT_TOP - r, POTX + r, GROUND_Y + 200)

    def draw(self, c, res, t):
        lv = min(0.995, self.level(t))
        st = self.stones(t)
        # the pot slides in at the very start of the "found it" beat, thumping onto the ground
        t_in = self.doc.L(4) - 0.4
        u = clamp((t - t_in) / 0.5)
        if u <= 0:
            return
        drop = (1 - ease_out_cubic(u)) * 520
        a = clamp((t - t_in) / 0.18)
        c.save()
        c.translate(0, -drop)
        c.save()
        c.translate(POTX, GROUND_Y)
        c.rotate(self.tilt)
        c.translate(-POTX, -GROUND_Y)
        # contact shadow
        c.drawOval(skia.Rect.MakeXYWH(POTX - POT_W * 0.42, GROUND_Y - 26, POT_W * 0.84, 54), K.P((160, 112, 72), 0.45 * a))
        K.pot_cut(c, POTX, GROUND_Y, POT_W, POT_H, a=a, water=lv, stones=st, stone_r=POT_W * 0.052)
        # ripples on the surface for a moment after each landing
        wy = GROUND_Y - POT_H * lv
        for td in self.drops:
            if 0 <= t - td < 1.5:
                v = (t - td) / 1.5
                rr = POT_W * (0.06 + 0.20 * v)
                c.drawOval(skia.Rect.MakeXYWH(POTX - rr, wy - rr * 0.16, rr * 2, rr * 0.32),
                           K.line((226, 246, 252), 0.75 * (1 - v) * a, POT_W * 0.010))
        c.restore()
        c.restore()


# --------------------------------------------------------------------------- the crow
class Crow(Item):
    """The hero. Position, pose and mood are all keyed off narration times."""
    z = 12

    def __init__(self, film, doc, drops):
        super().__init__(-1.0, None, 12, sfx=False)
        self.film, self.doc, self.drops = film, doc, sorted(drops)
        L, E = doc.L, doc.E
        # (t, x, y, s, lean, flap_amp, look, beak_open)
        self.keys = []
        # perch: feet exactly on the rim (the crow's feet sit 0.66 * size below its centre), body
        # left of the mouth so the beak reaches over the opening
        rim_x, rim_y = -170, POT_TOP - 0.60 * CROW_S
        ground_y = GROUND_Y - 0.66 * CROW_S
        self.keys.append((0.0, -1450, -700, 0.80, 0.0, 1.0, 1, 0.0))             # flies in from the left
        self.keys.append((L(1) - 0.2, -820, -640, 0.92, 0.0, 1.0, 1, 0.1))
        self.keys.append((L(2) + 0.4, -330, -560, 1.0, 0.0, 1.0, 1, 0.2))        # over the baked land
        self.keys.append((L(3) + 0.2, 220, -620, 1.0, 0.0, 1.0, 1, 0.55))        # panting, hot
        self.keys.append((L(3) + 2.4, -60, -560, 1.0, 0.0, 0.45, 1, 0.75))
        self.keys.append((L(4) + 0.4, 330, -680, 1.0, 0.0, 0.30, 1, 0.55))       # spots the pot
        self.keys.append((L(5) + 0.2, rim_x, rim_y, 1.0, 0.0, 0.10, 1, 0.15))    # lands on the rim
        self.keys.append((L(6) + 0.3, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.25))
        self.keys.append((L(6) + 1.4, rim_x - 14, rim_y + 26, 1.0, 34.0, 0.0, 1, 0.08))  # strains, cannot reach
        self.keys.append((L(7) + 0.4, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.45))
        self.keys.append((L(9) + 0.2, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.9))
        self.keys.append((L(10) + 0.3, 560, ground_y, 0.86, 0.0, 0.0, 1, 0.1))  # hops down to the pebbles
        self.keys.append((L(11), 620, ground_y - 6, 0.86, 0.0, 0.0, 1, 0.2))
        self.keys.append((L(11) + 0.6, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.3))     # back up with a stone
        self.keys.append((L(15) + 1.6, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.2))
        self.keys.append((L(16) + 0.15, rim_x - 30, rim_y + 44, 1.0, 40.0, 0.0, 1, 0.5))  # drinks
        self.keys.append((L(17) + 0.4, rim_x, rim_y - 30, 1.0, 0.0, 0.0, 1, 0.9))         # "అబ్బా!"
        self.keys.append((L(18) + 0.3, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.2))
        self.keys.append((L(19) + 0.2, rim_x - 40, rim_y - 120, 1.0, 0.0, 1.0, 1, 0.5))   # up and away
        self.keys.append((L(19) + 2.0, -420, -1250, 0.95, 0.0, 1.0, 1, 0.6))
        self.keys.append((L(19) + 3.4, -1500, -1900, 0.85, 0.0, 1.0, 1, 0.4))
        self.keys.append((L(23) + 0.2, -1500, -1400, 0.85, 0.0, 1.0, 1, 0.3))
        self.keys.append((L(23) + 2.0, rim_x, rim_y, 1.0, 0.0, 0.0, 1, 0.35))
        self.keys.sort(key=lambda k: k[0])

    def pose(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1:]
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                u = ease_in_out((t - a[0]) / max(1e-6, b[0] - a[0]))
                return tuple(lerp(a[i], b[i], u) for i in range(1, len(a)))
        return ks[-1][1:]

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-3000, -4000, 3000, 2000)

    def draw(self, c, res, t):
        x, y, s, lean, amp, look, beak = self.pose(t)
        s = s * CROW_S
        # flight flap: fast while airborne, still while perched
        flap = amp * math.sin(t * 11.0)
        bob = amp * math.sin(t * 11.0 + 1.2) * s * 0.05
        # a hop between beats and the odd blink keep it alive
        hop = math.sin(t * 3.1) * 4 * (1 if amp < 0.05 else 0)
        c.save()
        c.translate(x, y + bob + hop)
        if lean:
            c.translate(0, s * 0.66)          # pivot around the feet
            c.rotate(lean)
            c.translate(0, -s * 0.66)
        K.crow(c, 0, 0, s, flap=flap, look=look, beak_open=beak)
        c.restore()


# --------------------------------------------------------------------------- the lizard
class Liz(Item):
    z = 11

    def __init__(self, film, doc):
        super().__init__(-1.0, None, 11, sfx=False)
        self.film, self.doc = film, doc
        L, E = doc.L, doc.E
        self.keys = [(0.0, 980, GROUND_Y + 30, 0.0), (L(8) + 0.6, 930, GROUND_Y + 34, 0.0),
                     (E(18), 920, GROUND_Y + 38, 0.0), (L(19), 880, GROUND_Y + 44, 0.0), (E(19) + 1.0, 1700, GROUND_Y + 74, 0.0)]
        self.keys.sort()

    def pose(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return ks[0][1:]
        for a, b in zip(ks, ks[1:]):
            if a[0] <= t <= b[0]:
                u = ease_in_out((t - a[0]) / max(1e-6, b[0] - a[0]))
                return tuple(lerp(a[i], b[i], u) for i in range(1, len(a)))
        return ks[-1][1:]

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-2000, GROUND_Y - 600, 2000, GROUND_Y + 400)

    def draw(self, c, res, t):
        x, y, _ = self.pose(t)
        L, E = self.doc.L, self.doc.E
        appear = smooth(L(8) - 0.2, L(8) + 0.5, t) * (1 - smooth(E(19), E(19) + 0.8, t))
        if appear <= 0.01:
            return
        blink = 1.0
        for tb in (L(8) + 1.4, L(10) + 0.8, L(13) + 1.0, L(17) + 1.0):
            if 0 <= t - tb < 0.16:
                blink = 0.18
        amazed = 1.0 + 0.65 * smooth(L(18) - 0.4, L(18) + 0.3, t) * (1 - smooth(L(19) + 1.0, L(19) + 2.0, t))
        talking = 1.0 if (L(8) - 0.1 < t < E(9)) else 0.0
        mouth = (0.55 + 0.45 * math.sin(t * 16)) * talking + 0.85 * smooth(L(18), L(18) + 0.4, t)
        wig = math.sin(t * 2.6) * 0.35 + math.sin(t * 6.1) * 0.06
        a = appear
        c.save()
        c.translate(x, y)
        K.lizard(c, 0, 0, LIZ_S, a=a, wiggle=wig, eye=blink * amazed, mouth=clamp(mouth), look=1.0)
        c.restore()


# --------------------------------------------------------------------------- the flying stones
class StoneDrops(Item):
    """Each stone the crow carries: it appears at the beak, falls down the pot's mouth, and a splash
    of droplets marks the landing. Timing is the same list the pot and the sound cues use."""
    z = 14

    def __init__(self, film, doc, drops, beak_at, water_y):
        super().__init__(-1.0, None, 14, sfx=False)
        self.film, self.doc, self.drops = film, doc, sorted(drops)
        self.beak_at, self.water_y = beak_at, water_y

    def bounds(self, res):
        return skia.Rect.MakeLTRB(POTX - 1200, POT_TOP - 900, POTX + 1200, GROUND_Y)

    def draw(self, c, res, t):
        for k, td in enumerate(self.drops):
            t0 = td - 0.62
            if not (t0 <= t <= td + 0.9):
                continue
            bx, by = self.beak_at(k, t)
            wy = self.water_y(t, k)
            if t < td:
                u = clamp((t - t0) / 0.62)
                sx = lerp(bx, POTX - 90 + 30 * math.sin(k * 2.1), u * u)
                sy = lerp(by, wy, ease_in_cubic(u))
                a = 1.0
                rot = u * 300 * (1 if k % 2 else -1)
            else:
                v = (t - td) / 0.9
                sx, sy, a, rot = POTX - 90 + 30 * math.sin(k * 2.1), wy + 40 * v, 1 - v, 0
            if a <= 0.02:
                continue
            c.save()
            c.translate(sx, sy)
            c.rotate(rot)
            K.stone(c, 0, 0, POT_W * 0.045, a=a, rgb=(132, 126, 132))
            c.restore()
            # droplets flying up at the moment of the plop
            if td <= t <= td + 0.55:
                u = (t - td) / 0.55
                for j in range(6):
                    ang = math.pi * (0.12 + 0.76 * j / 5)
                    d = POT_W * (0.05 + 0.16 * u)
                    c.drawCircle(POTX - 90 + math.cos(ang) * d * (1 if j % 2 else -1),
                                 wy - math.sin(ang) * d * 1.3, POT_W * 0.012 * (1 - u),
                                 K.P(WATER, (1 - u) * 0.9))


def ease_in_cubic(x):
    x = clamp(x)
    return x * x * x


# --------------------------------------------------------------------------- screen-space text
class Sc:
    """Converts a 1080-wide portrait screen position into world coordinates for the camera at time t,
    and screen px into world units. Text is laid out in screen px so it never wobbles with the zoom."""

    SW, SH = 1080.0, 1920.0

    def __init__(self, cam):
        self.cx, self.cy, self.z, self.rot = cam
        self.k = S1080 * self.z
        self.i = 1.0 / self.k          # world px per screen px: local units in a card are screen px

    def p(self, sx, sy):
        """World point under screen pixel (sx, sy)."""
        return self.cx + (sx - self.SW / 2) / self.k, self.cy + (sy - self.SH / 2) / self.k

    def rect(self, c, x, y, w, h):
        """Start a screen-space transform whose origin is screen pixel (x, y) and whose units are
        screen px: callers then draw from (0, 0) to (w, h) and nothing depends on the zoom."""
        ox, oy = self.p(x, y)
        c.save()
        c.translate(ox, oy)
        c.scale(self.k, self.k)

    def px(self, v):
        """Screen px -> world units."""
        return v / self.k


class TextLayer(Item):
    """All the written Telugu. One item draws everything in screen space, on top of the cartoon."""

    z = 45

    def __init__(self, film, doc, drops, pot):
        super().__init__(-2.0, None, 45, sfx=False)
        self.film, self.doc, self.drops, self.pot = film, doc, sorted(drops), pot

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        sc = Sc(self.film.camera(t))
        # the camera never rotates in this film, so this single offset+scale turns world units into
        # screen px with the frame's top-left at the origin
        ox, oy = sc.p(0, 0)
        c.save()
        c.translate(ox, oy)
        c.scale(sc.k, sc.k)
        self.title(c, t)
        self.caption(c, t)
        self.bubbles(c, t)
        self.counting(c, t)
        self.quiz(c, t)
        self.endcard(c, t)
        c.restore()

    # ---- opening title
    def title(self, c, t):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(1) - 0.5, L(1) + 0.35, t) * (1 - smooth(L(2) - 1.0, L(2) - 0.2, t))
        if a <= 0.01:
            return
        big1 = ty.layout("దాహంగా", str(BOLD), 146)
        big2 = ty.layout("ఉన్న కాకి", str(BOLD), 146)
        sub = ty.layout("ఒక చిన్న కథ — గులకరాళ్ళు", str(REG), 50)
        for i, ln in enumerate((big1, big2)):
            u = clamp((t - (L(1) - 0.45 + i * 0.20)) / 0.5)
            if u <= 0:
                continue
            pop = ease_out_back(u, 2.2)
            c.save()
            c.translate(540, 640 + i * 168)
            c.scale(pop, pop)
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 242), a=a, align="center", outline=(176, 76, 40), ow=16,
                    shadow=(60, 30, 20))
            c.restore()
        aa = a * ramp(t, L(1) + 0.9, 0.5)
        ty.draw(c, sub, 540, 968, rgb=(146, 76, 42), a=aa, align="center")

    # ---- caption band, word by word as it is spoken
    def caption(self, c, t):
        sc = Sc(self.film.camera(t))
        for s in self.doc.timing["segments"]:
            if s["id"] in (1, 24):
                continue
            if not (s["start"] - 0.14 <= t <= s["end"] + 0.36):
                continue
            u = ramp(t, s["start"] - 0.14, 0.26)
            a = u * (1 - ramp(t, s["end"] + 0.06, 0.30))
            if a <= 0.01:
                continue
            size = ty.fit(s["caption"], str(BOLD), 60, 900)
            ln = ty.layout(s["caption"], str(BOLD), size)
            bw = ln.width + 54
            bh = size * 1.62
            y = 1608 - (1 - ease_out_cubic(u)) * 46
            x0, y0 = sc.p(540 - bw / 2, y - bh * 0.72)
            k = sc.k
            c.save()
            c.translate(x0, y0)
            c.scale(k, k)
            r = skia.Rect.MakeXYWH(0, 0, bw, bh)
            c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 7), 30, 30), K.P((62, 40, 34), 0.20 * a))
            c.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), K.P(CREAM, 0.95 * a))
            c.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), K.line((222, 176, 134), 0.85 * a, 3))
            prog = clamp((t - s["start"]) / max(0.2, s["end"] - s["start"]))
            cur = int(prog * max(1, len(ln.words)))
            ty.draw(c, ln, bw / 2, bh * 0.72 + size * 0.30, rgb=INK, a=a, align="center",
                    rgb_word=lambda wi, col: ORANGE if wi <= cur else col)
            c.restore()

    # ---- speech bubbles
    def bubbles(self, c, t):
        L, E = self.doc.L, self.doc.E
        items = [("నాకు ఒక ఐడియా\nవచ్చింది!", L(7) + 1.6, E(7) + 0.5, 300, 330, 1),
                 ("ఏం చేస్తున్నావ్\nకాకీ?", L(8) + 1.4, E(9) - 0.1, 660, 470, -1),
                 ("చూస్తూ ఉండు!", L(9) + 0.2, E(9) + 0.4, 320, 300, 1),
                 ("అబ్బా!", L(17) + 0.1, E(17) + 0.55, 330, 260, 1),
                 ("వావ్!", L(18) + 0.7, E(18) + 0.9, 700, 560, -1),
                 ("కా! కా!", L(19) + 0.3, L(19) + 2.1, 350, 250, 1)]
        for text, t0, t1, sx, sy, who in items:
            if not (t0 <= t <= t1 + 0.28):
                continue
            a = ramp(t, t0, 0.16) * (1 - ramp(t, t1, 0.24))
            if a <= 0.01:
                continue
            sc = pop_in(t, t0, 0.32, 2.8)
            lines = [ty.layout(s, str(BOLD), 54) for s in text.split("\n")]
            w = max(l.width for l in lines) + 96
            h = 54 * 1.28 * len(lines) + 60
            c.save()
            c.translate(sx, sy)
            c.scale(sc, sc)
            K.bubble(c, 0, 0, w, h, rgb=(255, 250, 240), a=a, tail=(0.6 if who < 0 else -0.6, 1.0))
            for i, ln in enumerate(lines):
                ty.draw(c, ln, 0, (h / 2 - 54 * 1.05) + i * 54 * 1.28, rgb=(52, 36, 44), a=a, align="center")
            c.restore()

    # ---- counting: Telugu numerals, one per stone
    def counting(self, c, t):
        L, E = self.doc.L, self.doc.E
        if not (L(11) - 0.3 <= t <= L(15) + 1.0):
            return
        nums = ["౧", "౨", "౩", "౪", "౫", "౬", "౭", "౮", "౯", "౧౦", "౧౧", "౧౨", "౧౩", "౧౪", "౧౫", "౧౬"]
        for i, td in enumerate(self.drops[:len(nums)]):
            if not (td - 0.05 <= t <= td + 1.0):
                continue
            a = ramp(t, td - 0.05, 0.10) * (1 - ramp(t, td + 0.62, 0.30))
            sc = pop_in(t, td - 0.05, 0.28, 3.2)
            ln = ty.layout(nums[i], str(BOLD), 92)
            c.save()
            c.translate(850, 640 + (i % 6) * 96 - 240)
            c.scale(sc, sc)
            ty.draw(c, ln, 0, 0, rgb=(255, 250, 236), a=a, align="center", outline=(214, 100, 46), ow=12)
            c.restore()

    # ---- the quiz beat
    def quiz(self, c, t):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(20), L(20) + 0.4, t) * (1 - smooth(E(20) + 0.2, E(20) + 0.8, t))
        if a <= 0.01:
            return
        l1 = ty.layout("కాకి బలంగా ఉందా?", str(BOLD), 66)
        l2 = ty.layout("తెలివిగా ఉందా?", str(BOLD), 66)
        for i, ln in enumerate((l1, l2)):
            u = clamp((t - (L(20) + 0.3 + i * 0.45)) / 0.4)
            if u <= 0:
                continue
            c.save()
            c.translate(540, 430 + i * 120)
            c.scale(ease_out_back(u, 2.4), ease_out_back(u, 2.4))
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 244), a=a, align="center", outline=(206, 92, 52), ow=13)
            c.restore()

    # ---- closing card
    def endcard(self, c, t):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(23) - 0.2, L(23) + 0.7, t)
        if a <= 0.01:
            return
        l1 = ty.layout("ఓపిక ఉంటే", str(BOLD), 104)
        l2 = ty.layout("ఏదీ అసాధ్యం కాదు!", str(BOLD), 104)
        sub = ty.layout("దాహంగా ఉన్న కాకి · ఒక తెలుగు కథ", str(REG), 44)
        for i, ln in enumerate((l1, l2)):
            u = clamp((t - (L(23) - 0.2 + i * 0.36)) / 0.5)
            if u <= 0:
                continue
            c.save()
            c.translate(540, 560 + i * 150)
            c.scale(ease_out_back(u, 2.0), ease_out_back(u, 2.0))
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 242), a=a, align="center", outline=(176, 76, 40), ow=15,
                    shadow=(60, 30, 20))
            c.restore()
        ty.draw(c, sub, 540, 900, rgb=(140, 78, 46), a=a * ramp(t, L(23) + 0.6, 0.6), align="center")


# --------------------------------------------------------------------------- cartoon effects
class Effects(Item):
    """The jokes: sweat, the idea bulb, hearts, a question mark, sparkles. All pure functions of t."""
    z = 30

    def __init__(self, film, doc, crow):
        super().__init__(-1.0, None, 30, sfx=False)
        self.film, self.doc, self.crow = film, doc, crow

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-4000, -5000, 4000, 2400)

    def draw(self, c, res, t):
        L, E = self.doc.L, self.doc.E
        s0 = CROW_S

        # sweat while the bird is hot, and after its beak cannot reach the water
        for t0, t1 in ((L(2) + 0.2, E(3) + 0.3), (L(6) + 1.1, E(6) + 0.4)):
            if t0 <= t <= t1:
                x, y, s, lean, amp, look, beak = self.crow.pose(t)
                S = s * s0
                wob = math.sin(t * 2.4)
                K.sweat(c, x - S * 0.56, y - S * 0.62 + 16 * wob, S * 0.075, a=0.95)
                K.sweat(c, x - S * 0.80, y - S * 0.44 - 10 * wob, S * 0.055, a=0.8)

        # the idea: a bulb over the crow's head with twinkles
        if L(7) + 1.0 <= t <= E(7) + 1.1:
            u = clamp((t - L(7) - 1.0) / 0.42)
            x, y, s, lean, amp, look, beak = self.crow.pose(t)
            S = s * s0
            c.save()
            c.translate(x + S * 0.16, y - S * 0.98)
            c.scale(ease_out_back(u, 2.6), ease_out_back(u, 2.6))
            K.lightbulb(c, 0, 0, S * 0.40, glow=1.0 + 0.2 * math.sin(t * 7))
            for j in range(6):
                ang = -2.6 + j * 0.42
                rr = S * (0.70 + 0.05 * math.sin(t * 5 + j))
                K.sparkle(c, math.cos(ang) * rr, math.sin(ang) * rr, S * 0.055, a=0.85)
            c.restore()

        # the question in the quiz
        if L(20) - 0.2 <= t <= E(20) + 0.9:
            u = clamp((t - L(20) + 0.2) / 0.4)
            sc = Sc(self.film.camera(t))
            c.save()
            c.translate(*sc.p(250, 760))
            c.rotate(0.16 * math.sin(t * 2.2))
            c.scale(sc.i * ease_out_back(u, 2.2), sc.i * ease_out_back(u, 2.2))
            ty.draw(c, ty.layout("?", str(BOLD), 230), 0, 90, rgb=(255, 252, 244), align="center",
                    outline=(226, 96, 44), ow=16)
            c.restore()

        # hearts over the moral
        if L(21) - 0.2 <= t <= E(22) + 0.8:
            sc = Sc(self.film.camera(t))
            for j in range(3):
                ph = (t * 0.5 + j * 0.33) % 1.0
                x, y = sc.p(300 + j * 110 + 26 * math.sin(ph * 7), 1180 - 420 * ph)
                K.heart(c, x, y, sc.i * (30 + 8 * math.sin(ph * 5)), a=0.8 * (1 - ph))

        # sparkles while the bird drinks and cheers
        if L(16) <= t <= E(17) + 0.5:
            u = clamp((t - L(16)) / max(0.4, E(17) + 0.5 - L(16)))
            sc = Sc(self.film.camera(t))
            for j in range(12):
                ang = j * 0.523 + t * 0.7
                rr = 0.30 + 0.16 * u
                x, y = sc.p(540 + math.cos(ang) * rr * 1080, 820 + math.sin(ang) * rr * 1080)
                K.sparkle(c, x, y, sc.i * (16 + 12 * math.sin(t * 8 + j)), a=0.5 * (1 - 0.5 * u))


# --------------------------------------------------------------------------- the film
def build_film(doc):
    L, E = doc.L, doc.E
    duration = doc.duration

    # the stones: first one, then a couple, then a run of them, then a last push — every landing is
    # the same number the pot, the flying stones, the numerals and the sound cues all use
    drops = [L(11) + 1.05]
    drops += [L(12) + 0.35, L(12) + 0.95, L(12) + 1.75]
    t = L(13) + 0.45
    while t < E(14) - 0.3 and len(drops) < 11:
        drops.append(t)
        t += 0.30
    t = L(15) + 0.25
    while len(drops) < 15 and t < L(15) + 1.9:
        drops.append(t)
        t += 0.26
    drops = sorted(drops)
    doc.game_drops = drops

    film = Film(duration, fps=30, look=LOOK)
    film.fade_in, film.fade_out = 0.8, 2.4
    film.items.remove(film.board)              # this film paints its own sky

    film.add(Backdrop(film, doc))
    film.add(Pebbles(film, doc, drops))
    pot = film.add(Pot(film, doc, drops))
    crow = film.add(Crow(film, doc, drops))
    film.add(Liz(film, doc))
    film.add(StoneDrops(film, doc, drops,
                        beak_at=lambda k, tt: (crow.pose(tt)[0] + crow.pose(tt)[2] * CROW_S * 0.62,
                                               crow.pose(tt)[1] + crow.pose(tt)[2] * CROW_S * 0.10),
                        water_y=lambda tt, k: GROUND_Y - POT_H * pot.level(tt)))
    film.add(Effects(film, doc, crow))
    film.add(TitleCard(film, doc, t_on=-1.0))
    film.add(CaptionCard(film, doc))
    film.add(BubbleCards(film, doc))
    film.add(CountCard(film, doc, drops))
    film.add(QuizCard(film, doc))
    film.add(EndCard(film, doc))

    # ---- camera: a wide opening, a slow push to the pot, tight on the crow, then out for the moral
    cam = [
        (0.0, 0, -560, 1.00),
        (L(1) + 0.6, -20, -640, 1.06),
        (L(2), -330, -560, 1.10),
        (L(3), 200, -620, 1.20),
        (E(3) - 0.4, -40, -640, 1.10),
        (L(4) - 0.1, 60, -500, 0.98),        # pull out: there is the pot!
        (L(4) + 0.9, POTX, -420, 1.16),
        (L(5), POTX, -460, 1.30),
        (L(6) + 0.2, 30, -480, 1.62),       # tight: the beak strains at the rim
        (L(7) + 0.2, -40, -520, 1.74),      # the idea
        (L(8) + 0.2, 240, -100, 1.24),      # the lizard has opinions
        (L(9) + 0.3, 200, -180, 1.30),
        (L(10) + 0.2, 260, 210, 1.44),      # the stones on the ground
        (L(11) + 0.4, POTX, -300, 1.30),
        (L(12) + 0.6, POTX, -340, 1.42),
        (L(13) + 0.4, POTX, -360, 1.52),
        (L(15), POTX, -470, 1.94),          # the water climbs into reach
        (L(16) + 0.4, POTX - 40, -560, 2.16),   # drinking
        (L(17) + 0.4, POTX - 30, -520, 2.02),
        (L(18) + 0.4, 420, -240, 1.30),     # the lizard's jaw drops
        (L(19) + 0.4, 420, -780, 0.96),     # away!
        (L(20), 260, -420, 1.05),           # quiz
        (L(21), 180, -300, 0.92),           # moral: settle back
        (L(22) + 0.6, 180, -320, 0.88),
        (L(24) - 0.5, 180, -360, 0.84),
        (duration, 180, -380, 0.82),
    ]
    for tt, x, y, z in cam:
        film.cam(tt, x, y, z)

    # ---- sound: the story's own noises, on the beats
    film.cue("shimmer", L(2) + 0.4, 0.5)
    film.cue("whoosh", L(3) + 0.3, 0.4)
    film.cue("boom", L(4) + 0.45, 0.55)                  # the pot thumps down
    film.cue("impact", L(5), 0.35)
    film.cue("tick", L(6) + 1.5, 0.6)                    # beak knocks the rim
    film.cue("shimmer", L(7) + 1.0, 0.7)                 # the idea
    film.cue("pop", L(8) + 1.4, 0.5)
    film.cue("tick", L(10), 0.35)
    for i, td in enumerate(drops):                       # టప్!
        film.cue("tick" if i % 2 else "drop", td, 0.55 if i < 4 else 0.45)
    film.cue("riser", L(15) - 0.2, 0.5)
    film.cue("shimmer", L(16) + 0.3, 0.55)
    film.cue("pop", L(17) + 0.1, 0.45)
    film.cue("shimmer", L(18) + 0.5, 0.6)
    film.cue("whoosh", L(19) + 0.2, 0.55)
    film.cue("stamp", L(20), 0.5)
    film.cue("impact", L(21), 0.45)
    film.cue("shimmer", L(23) + 0.2, 0.45)
    return film


class Pebbles(Item):
    """The pile of pebbles the crow raids: a heap on the ground that visibly shrinks as the bird
    carries stones to the pot — one heap, counted with the same drop list as the pot."""
    z = 8

    def __init__(self, film, doc, drops, x=700.0, n=26):
        super().__init__(-1.0, None, 8, sfx=False)
        self.film, self.doc, self.drops = film, doc, sorted(drops)
        self.x, self.n = x, n
        rng = np.random.default_rng(23)
        self.stones = []
        for i in range(n):
            a = rng.random() * math.tau
            rr = rng.random() ** 0.6
            sx = x + math.cos(a) * rr * 260
            sy = GROUND_Y + 26 - abs(math.sin(a * 1.7)) * (1 - rr) * 130
            self.stones.append((sx, sy, 26 + 20 * rng.random(), rng.random()))

    def bounds(self, res):
        return skia.Rect.MakeLTRB(self.x - 420, GROUND_Y - 250, self.x + 420, GROUND_Y + 200)

    def draw(self, c, res, t):
        taken = sum(1 for td in self.drops if t >= td - 0.75)
        for i, (sx, sy, r, ph) in enumerate(self.stones):
            if i < taken:
                continue
            a = ramp(t, 0.4 + 0.02 * i, 0.3)
            K.stone(c, sx, sy, r, a=a, rot=ph * 3.0)


class Card(Item):
    """Every piece of type sits in its own screen-space item: a card's origin is a screen pixel and
    its units are screen px, so a caption is 60 px in every shot whatever the camera is doing."""
    z = 45

    def __init__(self, film, doc, drops=None, t_on=0.0, t_off=None):
        super().__init__(t_on, t_off, 45, sfx=False)
        self.film, self.doc = film, doc
        self.drops = sorted(drops or [])

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        sc = Sc(self.film.camera(t))
        self.paint(c, t, sc)

    def paint(self, c, t, sc):
        pass


class TitleCard(Card):
    def paint(self, c, t, sc):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(1) - 0.5, L(1) + 0.35, t) * (1 - smooth(L(2) - 1.0, L(2) - 0.2, t))
        if a <= 0.01:
            return
        big1 = ty.layout("దాహంగా", str(BOLD), 146)
        big2 = ty.layout("ఉన్న కాకి", str(BOLD), 146)
        sub = ty.layout("ఒక చిన్న కథ — గులకరాళ్ళు", str(REG), 48)
        for i, ln in enumerate((big1, big2)):
            u = clamp((t - (L(1) - 0.45 + i * 0.20)) / 0.5)
            if u <= 0:
                continue
            pop = ease_out_back(u, 2.2)
            c.save()
            c.translate(*sc.p(540, 690 + i * 168))
            c.scale(sc.i * pop, sc.i * pop)
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 242), a=a, align="center", outline=(176, 76, 40), ow=17,
                    shadow=(70, 34, 22))
            c.restore()
        aa = a * ramp(t, L(1) + 0.9, 0.5)
        ty.draw(c, sub, *sc.p(540, 1030), rgb=(150, 78, 42), a=aa, align="center")


class CaptionCard(Card):
    def paint(self, c, t, sc):
        for s in self.doc.timing["segments"]:
            if s["id"] in (1, 24):
                continue
            if not (s["start"] - 0.14 <= t <= s["end"] + 0.36):
                continue
            u = ramp(t, s["start"] - 0.14, 0.26)
            a = u * (1 - ramp(t, s["end"] + 0.06, 0.30))
            if a <= 0.01:
                continue
            size = ty.fit(s["caption"], str(BOLD), 58, 880)
            ln = ty.layout(s["caption"], str(BOLD), size)
            bw = ln.width + 56
            bh = size * 1.62
            y = 1616 - (1 - ease_out_cubic(u)) * 46
            c.save()
            c.translate(*sc.p(540 - bw / 2, y - bh * 0.72))
            c.scale(sc.i, sc.i)
            r = skia.Rect.MakeXYWH(0, 0, bw, bh)
            c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 8), 32, 32), K.P((62, 40, 34), 0.18 * a))
            c.drawRRect(skia.RRect.MakeRectXY(r, 32, 32), K.P(CREAM, 0.95 * a))
            c.drawRRect(skia.RRect.MakeRectXY(r, 32, 32), K.line((222, 176, 134), 0.85 * a, 3))
            prog = clamp((t - s["start"]) / max(0.2, s["end"] - s["start"]))
            cur = int(prog * max(1, len(ln.words)))
            ty.draw(c, ln, bw / 2, bh * 0.72 + size * 0.30, rgb=INK, a=a, align="center",
                    rgb_word=lambda wi, col: ORANGE if wi <= cur else col)
            c.restore()


class BubbleCards(Card):
    def paint(self, c, t, sc):
        L, E = self.doc.L, self.doc.E
        items = [("నాకు ఒక ఐడియా\nవచ్చింది!", L(7) + 1.6, E(7) + 0.5, 300, 400, 1),
                 ("ఏం చేస్తున్నావ్\nకాకీ?", L(8) + 1.4, E(9) - 0.1, 660, 560, -1),
                 ("చూస్తూ ఉండు!", L(9) + 0.2, E(9) + 0.4, 320, 380, 1),
                 ("అబ్బా!", L(17) + 0.1, E(17) + 0.55, 330, 330, 1),
                 ("వావ్!", L(18) + 0.7, E(18) + 0.9, 700, 700, -1),
                 ("కా! కా!", L(19) + 0.3, L(19) + 2.1, 350, 300, 1)]
        for text, t0, t1, sx, sy, who in items:
            if not (t0 <= t <= t1 + 0.28):
                continue
            a = ramp(t, t0, 0.16) * (1 - ramp(t, t1, 0.24))
            if a <= 0.01:
                continue
            pop = pop_in(t, t0, 0.32, 2.8)
            lines = [ty.layout(x, str(BOLD), 54) for x in text.split("\n")]
            w = max(l.width for l in lines) + 96
            h = 54 * 1.28 * len(lines) + 58
            c.save()
            c.translate(*sc.p(sx, sy))
            c.scale(sc.i * pop, sc.i * pop)
            K.bubble(c, 0, 0, w, h, rgb=(255, 250, 240), a=a, tail=(0.6 if who < 0 else -0.6, 1.0))
            for i, ln in enumerate(lines):
                ty.draw(c, ln, 0, (h / 2 - 54 * 1.02) + i * 54 * 1.28, rgb=(52, 36, 44), a=a, align="center")
            c.restore()


class CountCard(Card):
    """Telugu numerals counting the stones, and a comic "టప్!" on each landing: the onomatopoeia is
    what makes the stone beat funny for a child, and it keeps working with the sound off."""

    def paint(self, c, t, sc):
        L, E = self.doc.L, self.doc.E
        if not (L(11) - 0.3 <= t <= L(15) + 1.0):
            return
        nums = ["౧", "౨", "౩", "౪", "౫", "౬", "౭", "౮", "౯", "౧౦", "౧౧", "౧౨", "౧౩", "౧౪", "౧౫", "౧౬"]
        for i, td in enumerate(self.drops[:len(nums)]):
            if not (td - 0.05 <= t <= td + 1.0):
                continue
            a = ramp(t, td - 0.05, 0.10) * (1 - ramp(t, td + 0.62, 0.30))
            pop = pop_in(t, td - 0.05, 0.28, 3.2)
            ln = ty.layout(nums[i], str(BOLD), 88)
            c.save()
            c.translate(*sc.p(880, 500 + (i % 7) * 92 - 200))
            c.scale(sc.i * pop, sc.i * pop)
            ty.draw(c, ln, 0, 0, rgb=(255, 250, 236), a=a, align="center", outline=(214, 100, 46), ow=12)
            c.restore()
            # the plop itself, thrown out of the pot's mouth and drifting up
            tp = ty.layout("టప్!", str(BOLD), 66)
            lift = (t - td) * 60
            c.save()
            c.translate(*sc.p(430 + (i % 2) * 40, 1180 - lift))
            c.rotate((-0.10 if i % 2 else 0.08) + 0.05 * math.sin(t * 9))
            c.scale(sc.i * pop, sc.i * pop)
            aa = a * (1 - ramp(t, td + 0.55, 0.45))
            ty.draw(c, tp, 0, 0, rgb=(255, 252, 244), a=aa, align="center", outline=(206, 92, 44), ow=11)
            c.restore()


class QuizCard(Card):
    """The question, then two answer cards a child can shout at, then the tick."""

    def paint(self, c, t, sc):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(20), L(20) + 0.4, t) * (1 - smooth(E(20) + 0.6, E(20) + 1.2, t))
        if a <= 0.01:
            return
        l1 = ty.layout("కాకి బలంగా ఉందా?", str(BOLD), 62)
        l2 = ty.layout("లేక తెలివిగా ఉందా?", str(BOLD), 62)
        for i, ln in enumerate((l1, l2)):
            u = clamp((t - (L(20) + 0.2 + i * 0.40)) / 0.40)
            if u <= 0:
                continue
            c.save()
            c.translate(*sc.p(540, 480 + i * 104))
            c.scale(sc.i * ease_out_back(u, 2.4), sc.i * ease_out_back(u, 2.4))
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 244), a=a, align="center", outline=(206, 92, 52), ow=13)
            c.restore()
        # two answer cards
        picked = smooth(E(20) - 1.4, E(20) - 0.7, t)
        for i, (word, col) in enumerate((("బలం", (196, 186, 172)), ("తెలివి", (240, 150, 60)))):
            u = clamp((t - (L(20) + 1.5 + i * 0.22)) / 0.36)
            if u <= 0:
                continue
            dim = (1.0 - 0.55 * picked) if i == 0 else 1.0
            c.save()
            c.translate(*sc.p(300 + i * 480, 800))
            c.scale(sc.i * ease_out_back(u, 2.2), sc.i * ease_out_back(u, 2.2))
            r = skia.Rect.MakeXYWH(-190, -86, 380, 172)
            c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 10), 42, 42), K.P((60, 34, 26), 0.18 * a))
            c.drawRRect(skia.RRect.MakeRectXY(r, 42, 42), K.P(col, (0.97 if i == 1 else 0.85) * a * dim))
            c.drawRRect(skia.RRect.MakeRectXY(r, 42, 42), K.line((255, 250, 240), 0.8 * a, 6))
            ty.draw(c, ty.layout(word, str(BOLD), 78), 0, 26, rgb=(255, 252, 244),
                    a=a * dim, align="center", outline=(150, 70, 34), ow=9)
            c.restore()
        # the tick lands on తెలివి
        if picked > 0.02:
            u = ease_out_back(clamp(picked * 1.6), 2.6)
            c.save()
            c.translate(*sc.p(780, 800))
            c.scale(sc.i * u, sc.i * u)
            tick = skia.Path()
            tick.moveTo(-52, 4); tick.lineTo(-12, 44); tick.lineTo(58, -46)
            tp = K.line((40, 150, 72), a, 24)
            c.drawPath(tick, tp)
            c.restore()
            cap = ty.layout("సరైన సమాధానం!", str(BOLD), 44)
            ca = a * ramp(t, E(20) - 1.0, 0.35)
            ty.draw(c, cap, *sc.p(540, 960), rgb=(255, 252, 244), a=ca, align="center",
                    outline=(40, 140, 70), ow=9)


class EndCard(Card):
    def paint(self, c, t, sc):
        L, E = self.doc.L, self.doc.E
        a = smooth(L(23) - 0.2, L(23) + 0.7, t)
        if a <= 0.01:
            return
        l1 = ty.layout("ఓపిక ఉంటే", str(BOLD), 100)
        l2 = ty.layout("ఏదీ అసాధ్యం కాదు!", str(BOLD), 100)
        sub = ty.layout("దాహంగా ఉన్న కాకి · ఒక తెలుగు కథ", str(REG), 50)
        for i, ln in enumerate((l1, l2)):
            u = clamp((t - (L(23) - 0.2 + i * 0.36)) / 0.5)
            if u <= 0:
                continue
            c.save()
            c.translate(*sc.p(540, 620 + i * 142))
            c.scale(sc.i * ease_out_back(u, 2.0), sc.i * ease_out_back(u, 2.0))
            ty.draw(c, ln, 0, 0, rgb=(255, 252, 242), a=a, align="center", outline=(176, 76, 40), ow=15,
                    shadow=(70, 34, 22))
            c.restore()
        ty.draw(c, sub, *sc.p(540, 620 + 320), rgb=(146, 80, 46), a=a * ramp(t, L(23) + 0.6, 0.6), align="center")
