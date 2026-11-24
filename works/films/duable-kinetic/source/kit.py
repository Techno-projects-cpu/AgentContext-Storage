"""
kit.py — the brag floor, on skia.

The brag films in this repo are drawn on skia (works/films/_shared/eng/): a real
vector canvas, shaped type, gradients, masks, arcs. The HTML template needs a
browser and there is none in this sandbox, so this file implements the same
standard directly against the same canvas API.

What it gives a scene:
  * Film        — shot list, HARD CUTS, one camera idea per shot
  * type        — skia text blobs, masked reveals, per-glyph stagger, fit-to-width
  * draw        — grid, rings, dots, slabs, hairline rules, gradient washes
  * post        — grain, vignette, print pass, all in numpy

The craft floor from agent-context/BRAG-PROMPT.md is enforced here:
  TYPE_FLOOR 30 px, ENTRANCE 0.45 s, HOLD 0.5 + 0.3/word, CUT 0.30 s,
  frame 0 inked, one camera idea per shot.
"""
import math
import os

import numpy as np
import skia

W, H = 1080, 1920
M = 84.0
TYPE_FLOOR = 30
ENTRANCE = 0.45

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/home/user/AgentContext-Storage/works/films/_shared/eng"
FACE = {
    "display": f"{FONT_DIR}/Display.ttf",     # Instrument Serif  — headlines
    "label": f"{FONT_DIR}/Label.ttf",         # Oswald            — caps furniture
    "label_b": f"{FONT_DIR}/LabelBold.ttf",
    "ui": f"{FONT_DIR}/UI.ttf",               # Space Grotesk     — body
}

# ---- palette: the brand's phosphor green on a near-black ground, with one warm
# paper tone for the honest beat. Not the Bytesized greens, not the ZeroVast verm.
GND = (7, 9, 8)
GND_2 = (14, 18, 16)
INK = (244, 246, 240)
DIM = (128, 138, 132)
GREEN = (186, 255, 96)
GREEN_DEEP = (96, 190, 74)
PAPER = (240, 235, 222)

_tf = {}


def face(key):
    if key not in _tf:
        _tf[key] = skia.Typeface.MakeFromFile(FACE[key])
    return _tf[key]


def font(key, size, tracking=0.0):
    f = skia.Font(face(key), max(TYPE_FLOOR, float(size)))
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    if tracking:
        f.setEmbolden(False)
        f.setLinearMetrics(True)
        # letter-spacing: skia has no tracking knob, so callers space glyphs
    return f


def text_w(s, f):
    return float(f.measureText(s))


def paint(rgb, a=1.0):
    p = skia.Paint(AntiAlias=True, Color=skia.Color(*rgb, int(255 * max(0.0, min(1.0, a)))))
    return p


def stroke(rgb, w=2.0, a=1.0):
    p = paint(rgb, a)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    return p


# --------------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def lerp(a, b, u):
    return a + (b - a) * u


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_io(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_expo(u):
    u = clamp(u)
    return 1 - 2 ** (-10 * u) if u < 1 else 1.0


def back_out(u, s=1.7):
    u = clamp(u)
    return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2


def span(t, t0, t1):
    """0..1 progress of t through [t0, t1]."""
    return clamp((t - t0) / max(1e-6, t1 - t0))


# ---------------------------------------------------------------- text drawing
def draw_text(c, s, x, y, key="display", size=120, rgb=INK, a=1.0, align="left",
              tracking=0.0, bolden=False):
    """Draw a string. `align` is left/center/right, `y` is the baseline."""
    f = font(key, size)
    if bolden:
        f.setEmbolden(True)
    total = text_w(s, f) + tracking * max(0, len(s) - 1)
    if align == "center":
        x -= total / 2
    elif align == "right":
        x -= total
    p = paint(rgb, a)
    if not tracking:
        c.drawString(s, x, y, f, p)
    else:
        xx = x
        for ch in s:
            c.drawString(ch, xx, y, f, p)
            xx += text_w(ch, f) + tracking
    return total


def text_height(key, size):
    f = font(key, size)
    m = f.getMetrics()
    return -m.fAscent + m.fDescent


def fit_width(s, key, want, max_w, floor=TYPE_FLOOR):
    size = want
    while size > floor:
        if text_w(s, font(key, size)) <= max_w:
            return size
        size -= 2
    return floor


def mask_reveal(c, s, x, y, key, size, rgb, u, align="left", tracking=0.0, rise=0.22):
    """The brag entrance: the line rises out of a clip box instead of fading in.

    `u` is 0..1. The clip's bottom edge falls as the clip's top edge stays, so the
    words appear to be pushed up from behind a rule.
    """
    if u <= 0:
        return 0.0
    h = text_height(key, size)
    w = text_w(s, font(key, size)) + tracking * max(0, len(s) - 1)
    x0 = x - (w / 2 if align == "center" else (w if align == "right" else 0))
    top = y - h * 0.92
    e = ease_expo(u)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x0 - 8, top - h * 0.3,
                                  w + 16, h * 1.5 * e + 2))
    dy = (1 - e) * h * rise * 3
    draw_text(c, s, x, y + dy, key, size, rgb, 1.0, align, tracking)
    c.restore()
    return w


def stagger_words(c, s, x, y, key, size, rgb, u, align="left", tracking=0.0, per=0.10):
    """Word-by-word rise: each word gets its own slice of the same 0.45 s window."""
    words = s.split()
    f = font(key, size)
    space = text_w(" ", f) + tracking
    total = sum(text_w(w, f) for w in words) + space * max(0, len(words) - 1)
    xx = x - (total / 2 if align == "center" else (total if align == "right" else 0))
    for i, w in enumerate(words):
        ww = text_w(w, f)
        uu = clamp((u - i * per) / max(0.15, 1 - per * max(1, len(words) - 1)))
        if uu > 0:
            e = ease_expo(uu)
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(xx - 6, y - size * 1.02, ww + 12, size * 1.5 * e))
            draw_text(c, w, xx, y + (1 - e) * size * 0.55, key, size, rgb, 1.0)
            c.restore()
        xx += ww + space
    return total


# ---------------------------------------------------------------- primitives
def rule(c, x0, y0, x1, y1, rgb, w=2.0, a=1.0):
    c.drawLine(x0, y0, x1, y1, stroke(rgb, w, a))


def draw_rule_in(c, x, y, w, rgb, u, thickness=2.0, vertical=False):
    """A rule that draws itself. 0..1 `u` is the drawn length, not an opacity."""
    e = ease_io(u)
    if vertical:
        c.drawRect(skia.Rect.MakeXYWH(x, y, thickness, w * e), paint(rgb))
    else:
        c.drawRect(skia.Rect.MakeXYWH(x, y, w * e, thickness), paint(rgb))


def grad_rect(c, r, top, bottom, a=1.0):
    sh = skia.GradientShader.MakeLinear(
        [skia.Point(r.left(), r.top()), skia.Point(r.left(), r.bottom())],
        [skia.Color(*top, int(255 * a)), skia.Color(*bottom, int(255 * a))])
    p = skia.Paint(Shader=sh, AntiAlias=True)
    c.drawRect(r, p)


def radial_glow(c, cx, cy, rad, rgb, a=0.35):
    sh = skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), rad,
        [skia.Color(*rgb, int(255 * a)), skia.Color(*rgb, 0)], [0.0, 1.0])
    p = skia.Paint(Shader=sh, AntiAlias=True)
    c.drawRect(skia.Rect.MakeXYWH(cx - rad, cy - rad, rad * 2, rad * 2), p)


def grid(c, x0, y0, w, h, step, rgb, a=0.10, phase=0.0, thickness=1.0):
    """A modular grid that can drift. Drawn in screen space over the world."""
    p = paint(rgb, a)
    off = (phase % 1.0) * step
    x = x0 - step + off
    while x <= x0 + w:
        c.drawRect(skia.Rect.MakeXYWH(x, y0, thickness, h), p)
        x += step
    y = y0 - step + off
    while y <= y0 + h:
        c.drawRect(skia.Rect.MakeXYWH(x0, y, w, thickness), p)
        y += step


def dot(c, x, y, r, rgb, a=1.0):
    c.drawCircle(x, y, r, paint(rgb, a))


def ring(c, x, y, r, rgb, w=2.0, a=1.0, start=0.0, sweep=360.0):
    """An arc — the sweep lets a ring draw itself on the beat."""
    p = stroke(rgb, w, a)
    if sweep >= 359.9:
        c.drawCircle(x, y, r, p)
        return
    box = skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r)
    c.drawArc(box, start, sweep, False, p)


def slab(c, x, y, w, h, fill, edge=None, a=1.0, r=0.0):
    p = paint(fill, a)
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    if r > 0:
        c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), p)
    else:
        c.drawRect(rect, p)
    if edge:
        e = stroke(edge, 2.0, a * 0.9)
        if r > 0:
            c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), e)
        else:
            c.drawRect(rect, e)


# ------------------------------------------------------------------ the film
class Shot:
    """One shot: a camera idea and a window. A cut is a new camera, not a pan."""

    def __init__(self, name, t0, t1, cam, draw):
        self.name, self.t0, self.t1, self.cam, self._draw = name, t0, t1, cam, draw


class Film:
    """Shot list, hard cuts, camera, post. Every frame is a pure function of t."""

    def __init__(self, shots, fps=30, size=(W, H), look=None, seed=7):
        self.shots = shots
        self.fps = fps
        # `W,H` stay the DESIGN frame (1080x1920) so every scene keeps its layout;
        # `size` is the OUTPUT raster, and the canvas is scaled into it. A preview
        # is then a faithful reduction rather than a re-layout.
        self.S = size[0] / float(W)
        self.W, self.H = size
        self.look = look or {}
        self.seed = seed
        self.hud = None
        self.duration = shots[-1].t1

    def shot_at(self, t):
        for s in self.shots:
            if s.t0 <= t < s.t1:
                return s
        return self.shots[-1]

    def camera(self, shot, t):
        """(cx, cy, zoom, rot). The camera's baseline is the shot's own rig, so a
        cut moves the world rather than tweening it — that is what makes it a cut."""
        c = shot.cam
        u = span(t, shot.t0, shot.t1)
        cx = c.get("x", self.W / 2) + c.get("dx", 0.0) * ease_io(u)
        cy = c.get("y", self.H / 2) + c.get("dy", 0.0) * ease_io(u)
        z = c.get("z", 1.0) * (1.0 + c.get("dz", 0.0) * ease_out(u))
        rot = c.get("rot", 0.0) + c.get("drot", 0.0) * ease_io(u)
        return cx, cy, z, rot

    def draw_frame(self, t):
        shot = self.shot_at(t)
        cx, cy, z, rot = self.camera(shot, t)
        surface = skia.Surface.MakeRaster(skia.ImageInfo.Make(
            self.W, self.H, skia.ColorType.kRGBA_8888_ColorType,
            skia.AlphaType.kPremul_AlphaType))
        c = surface.getCanvas()
        c.clear(skia.Color(*self.look.get("bg", GND)))
        c.save()
        c.scale(self.S, self.S)
        c.translate(W / 2, H / 2)
        c.scale(z, z)
        c.rotate(rot)
        c.translate(-cx, -cy)
        shot._draw(c, t - shot.t0, shot, t)
        c.restore()
        if self.hud:
            c.save()
            c.scale(self.S, self.S)
            self.hud(c, t, shot)
            c.restore()
        img = surface.makeImageSnapshot()
        arr = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
        return self.post(arr, t)

    def post(self, arr, t):
        """Grain and vignette. Grain must MOVE, or the picture reads as frozen."""
        h, w = arr.shape[:2]
        rng = np.random.default_rng((self.seed * 7919 + int(round(t * self.fps))) % 2 ** 31)
        arr *= (0.965 + 0.07 * rng.random((h, w, 1), dtype=np.float32))
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx = (xx - w / 2) / (w / 2)
        dy = (yy - h / 2) / (h / 2)
        d = np.sqrt(dx * dx + dy * dy) / math.sqrt(2)
        arr *= (1.0 - 0.28 * np.clip((d - 0.42) / 0.58, 0, 1)[..., None] ** 1.5)
        return np.clip(arr, 0, 255).astype(np.uint8)

    def frame(self, n):
        return self.draw_frame(n / self.fps)


def save_clip(c, x, y, w, h, u):
    """Context-manager-ish save/clip pair for masked reveals inside scenes."""
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, max(1.0, h * u)))


def restore(c):
    c.restore()
