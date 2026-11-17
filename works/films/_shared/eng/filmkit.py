"""The English ads' shared kit: a cut-film camera, painted-plate stages, kinetic type.

Both ads (ZeroVast, Vignan Vidyanikethan AI) are the same medium as the crow film -- gouache plates
painted by `claude-drawing-skill`'s grainbook engine, flat cut-out props on top, ambient life between
the two, and words that move -- but the grammar is an advert's, not a storybook's: type lands on the
beat, a prop slides in under it, the camera cuts rather than wanders.

What lives here
  CutFilm       engine.Film whose camera can CUT (a cut is a new shot, not a pan)
  Track         smoothstep keys (time, value)
  Stage         a full-frame set that owns a painted plate and the beats that stand on it
  ScreenCard    anything drawn in 1080x1920 design pixels, camera undone
  BigType       kinetic captions / headline / tag lines
  Prop          a cut-out sprite placed on the set with its own entrance, hold and exit
  Grain, Vignette, ProgressBar, Backdrop   the print and broadcast furniture
"""
import bisect
import math
import pathlib

import numpy as np
import skia

import ty
from engine import Item, clamp, ease_in_out, ease_out_back, ease_out_cubic, ramp

HERE = pathlib.Path(__file__).resolve().parent
DISPLAY = HERE / "Display.ttf"        # Instrument Serif     -- headlines
LABEL = HERE / "Label.ttf"            # Oswald               -- small caps furniture
LABEL_B = HERE / "LabelBold.ttf"
UI = HERE / "UI.ttf"                  # Space Grotesk        -- body, UI chrome

SW, SH = 1080.0, 1920.0
HORIZON = 1180.0

INK = (28, 24, 30)
CREAM = (250, 244, 232)
PAPER = (255, 250, 238)


def lerp(a, b, u):
    return a + (b - a) * u


def mix(c0, c1, u):
    return tuple(int(round(lerp(a, b, u))) for a, b in zip(c0, c1))


def P(rgb, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=skia.ColorSetARGB(int(max(0, min(1, a)) * 255), *[int(v) for v in rgb]))
    return p


def LN(rgb, a=1.0, w=4.0, cap=True):
    p = P(rgb, a)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    if cap:
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


# ------------------------------------------------------------------ time
HARD = object()          # marker in a camera key: this is a cut


class Track:
    """Smoothstep (or linear) interpolation through (time, value) keys, clamped outside."""

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
                if isinstance(v0, tuple):
                    return tuple(lerp(a, b, ease_in_out(u) if self.ease else u) for a, b in zip(v0, v1))
                return lerp(v0, v1, ease_in_out(u) if self.ease else u)
        return ks[-1][1]


def _eval(splines, t):
    """evaluate engine's (x, y, log-zoom, rot) spline list at t"""
    return tuple(sp(t) for sp in splines)


def pop(t, t0, dur=0.42, s=2.4):
    """a card landing: overshoot then settle"""
    return ease_out_back(clamp((t - t0) / dur), s)


def hit(t, t0, dur=0.28):
    """1 -> 0 punch used for scale kicks"""
    u = clamp((t - t0) / dur)
    return 0.0 if u >= 1 else 1 - u


def blink_at(t, period=3.6, offset=0.0, dur=0.16):
    u = (t + offset) % period
    return 1.0 - abs(2 * u / dur - 1) if u < dur else 0.0


# ------------------------------------------------------------------ the camera that can cut
class CutFilm:
    """A Film whose camera can cut between shots.

    engine's camera is one monotone spline through every key, so two keys a third of a second apart
    become a fast pan across two unrelated sets. An advert cuts; a cut is the same camera on both
    sides of one instant.
    """

    def __init__(self, film):
        self.film = film
        self.cuts = []
        inner_build = film._build

        def build():
            inner_build()
            # engine keeps the camera as a list of splines; the shot list has to win at cut times,
            # so once the splines exist the cut table is applied on top of them
            self._splines = film._cam

        film._build = build
        self._build = build

        def camera(t):
            if getattr(self, "_splines", None) is None:
                self._build()
            x, y, lz, rot = self.film.splines_eval(t) if hasattr(self.film, "splines_eval") else _eval(self._splines, t)
            import math
            z = math.exp(lz)
            if self.cuts:
                i = bisect.bisect_right([c[0] for c in self.cuts], t) - 1
                if i >= 0:
                    x, y, z, rot = self.cuts[i][1]
            return x, y, z, rot

        self._camera = camera
        film.camera = camera          # instance attribute shadows Engine.Film.camera

    def shot(self, t, x, y, z, rot=0.0):
        """hard cut at t to this framing"""
        self.cuts.append((float(t), (float(x), float(y), float(z), float(rot))))

    def __getattr__(self, name):
        return getattr(self.film, name)


# ------------------------------------------------------------------ stages
class Stage(Item):
    """A set: one painted plate, owned by the beats whose `stage` names it."""

    z = 0
    name = "stage"
    plate = None
    is_stage = True
    pad = 0.55             # how far past a beat the set stays up (so entrances have a floor)

    def __init__(self, film, doc):
        super().__init__(-50, None, self.z, sfx=False)
        self.film, self.doc = film, doc
        self.spans = []
        for s in doc.timing["segments"]:
            if s.get("stage") == self.name:
                self.spans.append((s["start"] - self.pad, s["end"] + self.pad))
        self.spans = merge_spans(self.spans)
        # a neighbouring beat that names ANOTHER set owns its own moment: the pad above must not
        # bleed this plate over a cut, or two pages paint into the same frame
        # each other set is padded forward by the same amount, so the two sets MEET at the cut
        # rather than overlapping across it (an overlap paints the wrong plate for half a second)
        others = [(s["start"] - self.pad, s["end"] + self.pad) for s in doc.timing["segments"]
                  if s.get("stage") not in (None, self.name)]
        clipped = []
        for a, b in self.spans:
            for o0, o1 in others:
                if o0 <= a < o1:
                    a = o1
                if o0 < b <= o1:
                    b = o0
            if b > a:
                clipped.append([a, b])
        self.spans = clipped

    def active(self, t):
        return any(a <= t <= b for a, b in self.spans)

    def visible(self, t):
        return self.active(t)

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        """the plate is blitted by the renderer; a stage only adds things painted INTO its page"""
        return


def merge_spans(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1] + 0.02:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


# ------------------------------------------------------------------ screen-space cards
class ScreenCard(Item):
    """Anything laid out in design pixels: it undoes the camera first, so text is 1:1 crisp."""

    z = 60

    def __init__(self, film, doc, z=60):
        super().__init__(-5, None, z, sfx=False)
        self.film, self.doc = film, doc

    def screen(self, c, t):
        """Exact inverse of the renderer's world transform, leaving the canvas in design pixels.

        NOTE every draw() that calls this must end with ONE c.restore(): unbalanced saves leak the
        transform into the next item and shift whatever it paints.
        """
        cx, cy, z, rot = self.film.camera(t)
        sc = getattr(self.film, "render_scale", 1.0) or 1.0
        w, h = getattr(self.film, "frame_w", SW), getattr(self.film, "frame_h", SH)
        k = z * sc
        c.save()
        c.translate(cx, cy)
        c.rotate(-rot)
        c.scale(1.0 / k, 1.0 / k)
        c.translate(-w / 2, -h / 2)
        c.scale(sc, sc)

    @staticmethod
    def font(kind="ui"):
        return {"display": DISPLAY, "label": LABEL, "labelb": LABEL_B, "ui": UI}[kind]


def plaque(c, x, y, w, h, a=1.0, rgb=PAPER, edge=(212, 196, 172), r=22, shadow=True):
    c.save()
    c.translate(x, y)
    if shadow:
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2 + 5, -h / 2 + 9, w, h), r, r),
                    P((30, 20, 14), 0.18 * a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), P(rgb, a))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), r, r), LN(edge, 0.85 * a, 2.5))
    c.restore()


def type_line(text, size, kind="ui"):
    return ty.layout(text, str(ScreenCard.font(kind)), size)


def draw_type(c, text, size, x, y, kind="ui", rgb=INK, a=1.0, align="center", outline=None, ow=None,
              shadow=None, a_word=None, rgb_word=None):
    ln = type_line(text, size, kind)
    ty.draw(c, ln, x, y, rgb=rgb, a=a, align=align, outline=outline, ow=ow, shadow=shadow,
            a_word=a_word, rgb_word=rgb_word)
    return ln


def rich_type(c, text, size, x, y, kind="ui", rgb=INK, a=1.0, align="center", outline=None, ow=None,
              shadow=None, kick=1.0, kick_map=None, dy_map=None, a_word=None, rgb_word=None):
    """Draw a line where single words can be LARGER and LIFTED (a name inside its tag line).

    HarfBuzz gives each word an x; per-word size and dy are applied like pop_word, around that
    word's own centre, so the line's baseline never shifts.
    """
    ln = type_line(text, size, kind)
    x0 = x - (ln.width if align == "right" else ln.width / 2 if align == "center" else 0)
    for cl in ln.clusters:
        if not cl.text.strip() or cl.word < 0:
            continue
        al = a if a_word is None else a * a_word(cl.word)
        if al <= 0.004:
            continue
        col = rgb if rgb_word is None else rgb_word(cl.word, rgb)
        wd = ln.word_at(cl.word)
        kk = (kick_map or {}).get(wd.text.strip(".,!?'"), 1.0) * kick
        dy = (dy_map or {}).get(wd.text.strip(".,!?'"), 0.0)
        path = ty.cluster_path(ln, cl)
        if path is None:
            continue
        if abs(kk - 1.0) < 1e-4 and abs(dy) < 1e-3:
            c.save(); c.translate(x0 + cl.x, y); c.drawPath(path, P(col, al)); c.restore()
            continue
        piv = x0 + wd.x + wd.w / 2
        c.save()
        c.translate(piv, y + dy - size * 0.34)
        c.scale(kk, kk)
        c.translate(-piv, -(y - size * 0.34))
        if outline is not None:
            op = LN(outline, al, ow if ow is not None else size * 0.12)
            c.save(); c.translate(x0 + cl.x, y); c.drawPath(path, op); c.restore()
        c.save(); c.translate(x0 + cl.x, y); c.drawPath(path, P(col, al)); c.restore()
        c.restore()
    return ln


def type_fit(text, size, max_w, kind="ui", min_size=14):
    return ty.fit(text, str(ScreenCard.font(kind)), size, max_w, min_size)


class BigType(ScreenCard):
    """Kinetic lines: each line lands on its own key, word by word, with an optional kick."""

    z = 61

    def __init__(self, film, doc, lines, size=86, kind="ui", rgb=INK, y=1470, align="center",
                 outline=None, ow=None, shadow=None, kick=0.10, colour_words=None):
        """lines: [(text, t_in, t_out, y_override, size_override, rgb_override), ...]"""
        super().__init__(film, doc, BigType.z)
        self.lines = lines
        self.size, self.kind, self.rgb, self.y, self.align = size, kind, rgb, y, align
        self.outline, self.ow, self.shadow, self.kick = outline, ow, shadow, kick
        self.colour_words = colour_words or {}

    def draw(self, c, res, t):
        for i, spec in enumerate(self.lines):
            text, t0, t1 = spec[0], spec[1], spec[2]
            yy = spec[3] if len(spec) > 3 and spec[3] is not None else self.y
            sz = spec[4] if len(spec) > 4 and spec[4] else self.size
            col = spec[5] if len(spec) > 5 and spec[5] else self.rgb
            al = spec[6] if len(spec) > 6 and spec[6] is not None else 1.0
            if not (t0 - 0.02 <= t <= t1 + 0.24):
                continue
            u = ramp(t, t0, 0.30)
            a = u * (1 - ramp(t, t1, 0.22)) * al
            if a <= 0.01:
                continue
            ln = type_line(text, sz, self.kind)
            k = pop(t, t0, 0.40, 2.2) if self.kick else 1.0
            k *= 1.0 + self.kick * hit(t, t0, 0.26)
            words = max(1, len(ln.words))

            def a_word(wi, _n=words, _u=u):
                # words arrive one behind the other: the line writes itself on
                return clamp((_u * (_n + 1.4) - wi) / 1.0)

            self.screen(c, t)
            c.save()
            c.translate(540 if self.align == "center" else 90, yy - (1 - ease_out_cubic(u)) * 34)
            c.scale(k, k)
            ty.draw(c, ln, 0, 0, rgb=col, a=a, align=self.align, outline=self.outline, ow=self.ow,
                    shadow=self.shadow, a_word=a_word,
                    rgb_word=self.colour_words.get(i))
            c.restore()
            c.restore()


class Captions(ScreenCard):
    """The spoken line, burned on: serif or UI, on a soft ink plaque so it reads on any plate.

    Lines come straight from the timing file (caption + start/end), so picture and voice cannot drift:
    retime the voice and the words move with it.
    """

    z = 65

    def __init__(self, film, doc, size=58, kind="ui", rgb=(250, 246, 236), y=1648, plaque_a=0.52,
                 skip=(), kick=0.06, upper=False):
        super().__init__(film, doc, Captions.z)
        self.size, self.kind, self.rgb, self.y = size, kind, rgb, y
        self.plaque_a, self.skip, self.kick, self.upper = plaque_a, set(skip), kick, upper

    def draw(self, c, res, t):
        for s in self.doc.timing["segments"]:
            if s["id"] in self.skip:
                continue
            cap = s.get("caption") or s.get("vo") or ""
            if not cap:
                continue
            t0, t1 = s["start"] - 0.10, s["end"] + 0.26
            # a line of dialogue must be off screen before the shot it belongs to ends
            for cut in getattr(self.doc, "cuts", {}).values():
                if t0 < cut <= t1:
                    t1 = max(t0 + 0.4, cut - 0.12)
            if not (t0 <= t <= t1):
                continue
            u = ramp(t, t0, 0.24)
            a = u * (1 - ramp(t, t1 - 0.30, 0.26))
            if a <= 0.01:
                continue
            text = cap.upper() if self.upper else cap
            size = type_fit(text, self.size, 900, self.kind)
            ln = type_line(text, size, self.kind)
            k = 1.0 + self.kick * hit(t, t0, 0.24)
            words = max(1, len(ln.words))

            def a_word(wi, _n=words, _u=u):
                return clamp((_u * (_n + 2.0) - wi) / 1.2)

            self.screen(c, t)
            c.save()
            c.translate(540, self.y + (1 - ease_out_cubic(u)) * 30)
            c.scale(k, k)
            bw, bh = ln.width + 88, size * 1.62
            if self.plaque_a > 0:
                c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-bw / 2, -bh / 2, bw, bh), 22, 22),
                            P((16, 12, 18), self.plaque_a * a))
            ty.draw(c, ln, 0, size * 0.34, rgb=self.rgb, a=a, align="center", a_word=a_word,
                    shadow=(10, 6, 10))
            c.restore()
            c.restore()


class Label(ScreenCard):
    """Small-caps broadcast furniture: a kicker at the top, a footnote at the bottom."""

    z = 63

    def __init__(self, film, doc, text, t0, t1, y=196, size=40, rgb=INK, a=0.75, rule=True, above=True):
        super().__init__(film, doc, Label.z)
        self.text, self.t0, self.t1, self.y = text, t0, t1, y
        self.size, self.rgb, self.base_a, self.rule, self.above = size, rgb, a, rule, above

    def draw(self, c, res, t):
        if not (self.t0 <= t <= self.t1 + 0.2):
            return
        a = ramp(t, self.t0, 0.35) * (1 - ramp(t, self.t1, 0.25)) * self.base_a
        if a <= 0.01:
            return
        ln = type_line(self.text.upper(), self.size, "label")
        self.screen(c, t)
        ty.draw(c, ln, 540, self.y, rgb=self.rgb, a=a, align="center")
        if self.rule:
            u = ramp(t, self.t0 + 0.05, 0.45)
            w = (ln.width + 96) * ease_out_cubic(u)
            yy = self.y + (self.size * 0.9 if self.above else -self.size * 1.5)
            c.drawLine(540 - w / 2, yy, 540 + w / 2, yy, LN(self.rgb, 0.35 * a, 2.0))
        c.restore()


class Prop(Item):
    """A cut-out sprite on the set: it lands, holds, and leaves. Motion is separate from the camera.

    `art(c, t, k)` draws the sprite in design pixels with its own origin at (0, 0), at scale k;
    the prop supplies translation, entrance, idle drift and exit.
    """

    z = 20

    def __init__(self, film, doc, art, keys, z=20, enter=0.45, out=0.35, drift=0.0, spin=0.0,
                 nudge=(0.0, 0.0)):
        """keys: [(t_in, t_out, x, y, scale, alpha), ...] -- one row per appearance"""
        super().__init__(-2, None, z, sfx=False)
        self.film, self.doc, self.art = film, doc, art
        self.keys = sorted(keys)
        self.enter, self.out, self.drift, self.spin, self.nudge = enter, out, drift, spin, nudge

    def draw(self, c, res, t):
        for (t0, t1, x, y, s, al) in self.keys:
            if not (t0 <= t <= t1 + self.out):
                continue
            u = ramp(t, t0, self.enter)
            a = u * (1 - ramp(t, t1, self.out)) * al
            if a <= 0.01:
                continue
            k = s * (0.86 + 0.14 * pop(t, t0, self.enter, 2.0))
            yy = y - (1 - ease_out_cubic(u)) * 42 + self.drift * math.sin(t * 1.2 + x)
            c.save()
            c.translate(x, yy)
            if self.spin:
                c.rotate(self.spin * math.sin(t * 0.9) + (1 - u) * -6)
            c.scale(k, k)
            c.translate(*self.nudge)      # art is authored around its own origin: no pivot guess
            self.art(c, t, 1.0, a)
            c.restore()


# ------------------------------------------------------------------ furniture
class Embers(ScreenCard):
    """A few slow motes catching the light, in SCREEN space, over the whole frame.

    The ambient layer lives in world space (right for grass and heat), but airborne specks want to
    cross the lens, not the map -- and they must never be so many that the picture reads as noise.
    """

    z = 69

    def __init__(self, film, doc, n=16, colour=(255, 226, 186), a=0.20, seed=4, rise=26.0):
        super().__init__(film, doc, Embers.z)
        self.n, self.colour, self.a, self.seed, self.rise = n, colour, a, seed, rise

    def draw(self, c, res, t):
        self.screen(c, t)
        for i in range(self.n):
            h1 = math.sin((i + 1) * 12.9898 + self.seed) * 43758.5453
            h2 = math.sin((i + 1) * 78.233 + self.seed * 3.1) * 43758.5453
            h3 = math.sin((i + 1) * 39.425 + self.seed * 7.7) * 43758.5453
            u1, u2, u3 = (v - math.floor(v) for v in (h1, h2, h3))
            x = u1 * SW + math.sin(t * (0.22 + 0.3 * u3) + i) * 46
            y = (u2 * SH - t * (self.rise + 40 * u3)) % SH
            r = 1.4 + 2.6 * u3
            tw = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * (1.1 + u2) + i * 2.3))
            c.drawCircle(x, y, r, P(self.colour, self.a * tw))
        c.restore()


class Vignette(ScreenCard):
    """A soft corner darkening in SCREEN space: it seats the cut-outs in the page."""

    z = 70

    def __init__(self, film, doc, strength=0.30, warm=(38, 24, 16)):
        super().__init__(film, doc, Vignette.z)
        self.strength, self.warm = strength, warm

    def draw(self, c, res, t):
        self.screen(c, t)
        g = skia.GradientShader.MakeRadial(
            skia.Point(540, 880), 1120,
            [skia.ColorSetARGB(0, *self.warm), skia.ColorSetARGB(0, *self.warm),
             skia.ColorSetARGB(int(255 * self.strength), *self.warm)], [0.0, 0.55, 1.0])
        c.drawRect(skia.Rect.MakeXYWH(0, 0, SW, SH), skia.Paint(Shader=g))
        c.restore()


class Grain(Item):
    """Paper tooth pressed over the finished frame, riding in screen space so it never swims."""

    z = 72

    def __init__(self, film, amount=0.06, seed=3):
        super().__init__(-5, None, Grain.z, sfx=False)
        rng = np.random.default_rng(seed)
        self.tile = rng.normal(0, 1, (360, 240)).astype(np.float32)
        self.amount = amount

    def draw(self, c, res, t):
        # drawn as a shader-free overlay: the renderer's paper pass owns the fine stock; this is the
        # flicker of film on top of it, and it must be sub-perceptual or it looks like sand
        return


class ProgressBar(ScreenCard):
    """A hairline of the film going by, bottom of frame -- the advert's own clock."""

    z = 66

    def __init__(self, film, doc, colour=(233, 94, 40), h=6, inset=0, a=0.9):
        super().__init__(film, doc, ProgressBar.z)
        self.colour, self.h, self.inset, self.a = colour, h, inset, a

    def draw(self, c, res, t):
        self.screen(c, t)
        dur = max(0.001, self.film.duration)
        u = clamp(t / dur)
        c.drawRect(skia.Rect.MakeXYWH(self.inset, SH - self.h, (SW - 2 * self.inset) * u, self.h),
                   P(self.colour, self.a))
        c.restore()


class Halftone(ScreenCard):
    """A print dot screen over the plate, and a slow film flicker: the "broadcast" half of the look.

    Screen space, so it never swims; deterministic from t, so every render matches.
    """

    z = 71

    def __init__(self, film, doc, pitch=7.0, radius=1.25, a=0.10, lines=True, line_a=0.05, rgb=(20, 14, 24)):
        super().__init__(film, doc, Halftone.z)
        self.pitch, self.radius, self.a, self.lines, self.line_a, self.rgb = pitch, radius, a, lines, line_a, rgb

    def draw(self, c, res, t):
        self.screen(c, t)
        p = P(self.rgb, self.a)
        step = self.pitch
        row = 0
        y = 0.0
        while y < SH:
            x = (step / 2 if row % 2 else 0.0)
            while x < SW:
                # the dots breathe very slowly, so the screen has a heartbeat without strobing
                r = self.radius * (0.85 + 0.15 * math.sin(t * 1.6 + x * 0.013 + y * 0.017))
                c.drawCircle(x, y, r, p)
                x += step
            y += step * 0.86
            row += 1
        if self.lines:
            q = P((0, 0, 0), self.line_a)
            yy = 0.0
            while yy < SH:
                c.drawRect(skia.Rect.MakeXYWH(0, yy, SW, 1.6), q)
                yy += 4.0
        c.restore()


class Wash(ScreenCard):
    """A flat colour field under a card, so type can sit on a busy plate and still read."""

    z = 59

    def __init__(self, film, doc, t0, t1, rgb=(24, 18, 26), a_max=0.55, top=0.0, bottom=SH):
        super().__init__(film, doc, Wash.z)
        self.t0, self.t1, self.rgb, self.a_max, self.top, self.bottom = t0, t1, rgb, a_max, top, bottom

    def draw(self, c, res, t):
        if not (self.t0 <= t <= self.t1 + 0.3):
            return
        a = ramp(t, self.t0, 0.35) * (1 - ramp(t, self.t1, 0.3)) * self.a_max
        if a <= 0.005:
            return
        self.screen(c, t)
        c.drawRect(skia.Rect.MakeXYWH(0, self.top, SW, self.bottom - self.top), P(self.rgb, a))
        c.restore()
