"""
kit.py — an editorial drawing kit on skia.

This is the brag floor (agent-context/BRAG-PROMPT.md) plus a deliberately
minimal system: porcelain, ink, one olive accent. Three typefaces, three roles:
Instrument Serif for the three statements, Oswald caps for labels and counters,
Space Grotesk for the small print.

Rules encoded here, because the previous cuts failed them:
  * nothing is centred by eye — every block measures itself
  * caps are tracked, serif is not, and neither is scaled past the column
  * a hairline is 2 px at 1080 and never drawn from an edge
  * every frame carries a moving element (the caller's job) and grain (ours)
"""
import math
import os

import numpy as np
import skia

W, H = 1080, 1920
M = 96.0                      # margin: 96 px at 1080, inside any safe box
TYPE_FLOOR = 30
ENTRANCE = 0.45

FONT_DIR = "/home/user/AgentContext-Storage/works/films/_shared/eng"
FACE = {
    "serif": f"{FONT_DIR}/Display.ttf",     # Instrument Serif
    "caps": f"{FONT_DIR}/Label.ttf",        # Oswald
    "caps_b": f"{FONT_DIR}/LabelBold.ttf",
    "ui": f"{FONT_DIR}/UI.ttf",             # Space Grotesk
}

# ---- palette: porcelain and ink, with a single olive signal
PAPER = (238, 236, 228)
PAPER_D = (226, 223, 213)
INK = (18, 18, 15)
INK_SOFT = (86, 86, 78)
HAIR = (186, 182, 170)
OLIVE = (96, 112, 62)
OLIVE_L = (176, 196, 118)

_tf = {}


def face(k):
    if k not in _tf:
        _tf[k] = skia.Typeface.MakeFromFile(FACE[k])
    return _tf[k]


def font(k, size, bold=False):
    f = skia.Font(face(k), max(TYPE_FLOOR, float(size)))
    f.setSubpixel(True)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setHinting(skia.FontHinting.kNone)
    if bold:
        f.setEmbolden(True)
    return f


def tw(s, f, tracking=0.0):
    return float(f.measureText(s)) + tracking * max(0, len(s) - 1)


def paint(rgb, a=1.0):
    return skia.Paint(AntiAlias=True,
                      Color=skia.Color(*rgb, int(255 * max(0.0, min(1.0, a)))))


def spaint(rgb, w=2.0, a=1.0):
    p = paint(rgb, a)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    return p


# --------------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else (b if x > b else x)


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def ease_io(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_expo(u):
    u = clamp(u)
    return 1 - 2 ** (-9 * u) if u < 1 else 1.0


def span(t, a, b):
    return clamp((t - a) / max(1e-6, b - a))


# ----------------------------------------------------------------------- type
def text(c, s, x, y, k="serif", size=120, rgb=INK, a=1.0, align="left",
         tracking=0.0, bold=False):
    f = font(k, size, bold)
    w = tw(s, f, tracking)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    p = paint(rgb, a)
    if not tracking:
        c.drawString(s, x, y, f, p)
    else:
        xx = x
        for ch in s:
            c.drawString(ch, xx, y, f, p)
            xx += f.measureText(ch) + tracking
    return w


def height(k, size):
    m = font(k, size).getMetrics()
    return -m.fAscent + m.fDescent


def fit(s, k, want, max_w, floor=TYPE_FLOOR, tracking=0.0, bold=False):
    size = want
    while size > floor:
        if tw(s, font(k, size, bold), tracking) <= max_w:
            return size
        size -= 2
    return floor


def fit_tracked(s, k, want, max_w, tracking, floor=TYPE_FLOOR):
    """Caps with letterspacing overflow far earlier than their point size suggests."""
    size = want
    while size > floor:
        if tw(s, font(k, size), tracking) <= max_w:
            return size
        size -= 2
    return floor


def rise(c, s, x, y, k, size, rgb, u, align="left", tracking=0.0, travel=0.30):
    """The brag entrance: a line rises out of a clip box. Never a fade."""
    if u <= 0:
        return 0.0
    h = height(k, size)
    w = tw(s, font(k, size), tracking)
    x0 = x - (w / 2 if align == "center" else (w if align == "right" else 0))
    e = ease_expo(u)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x0 - 12, y - h * 1.05, w + 24, h * (0.30 + 0.95 * e)))
    text(c, s, x, y + (1 - e) * h * travel, k, size, rgb, 1.0, align, tracking)
    c.restore()
    return w


def words(c, s, x, y, k, size, rgb, u, align="left", per=0.12, tracking=0.0):
    """Word-by-word rise on the same 0.45 s window — for lines that carry a beat."""
    ws = s.split()
    f = font(k, size)
    space = f.measureText(" ") + tracking
    total = sum(f.measureText(w) for w in ws) + space * max(0, len(ws) - 1)
    xx = x - (total / 2 if align == "center" else (total if align == "right" else 0))
    for i, w in enumerate(ws):
        ww = f.measureText(w)
        uu = clamp((u - i * per) / max(0.2, 1 - per * max(1, len(ws) - 1)))
        if uu > 0:
            e = ease_expo(uu)
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(xx - 8, y - size * 1.05, ww + 16, size * (0.3 + 0.95 * e)))
            text(c, w, xx, y + (1 - e) * size * 0.42, k, size, rgb, 1.0)
            c.restore()
        xx += ww + space
    return total


# ---------------------------------------------------------------- primitives
def rule(c, x0, y, w, rgb=HAIR, a=1.0, u=1.0, thickness=2.0, vertical=False):
    """A hairline that draws itself from x0. `u` is the drawn fraction."""
    if u <= 0:
        return
    e = ease_io(u)
    if vertical:
        c.drawRect(skia.Rect.MakeXYWH(x0, y, thickness, w * e), paint(rgb, a))
    else:
        c.drawRect(skia.Rect.MakeXYWH(x0, y, w * e, thickness), paint(rgb, a))


def line(c, x0, y0, x1, y1, rgb=HAIR, a=1.0, thickness=2.0):
    c.drawLine(x0, y0, x1, y1, spaint(rgb, thickness, a))


def ring(c, x, y, r, rgb, thickness=2.0, a=1.0, u=1.0, start=-90.0):
    if u <= 0:
        return
    c.drawArc(skia.Rect.MakeLTRB(x - r, y - r, x + r, y + r), start, 359.9 * ease_io(u),
              False, spaint(rgb, thickness, a))


def disc(c, x, y, r, rgb=INK, a=1.0):
    c.drawCircle(x, y, r, paint(rgb, a))


def vgrad(c, r, top, bottom, a=1.0):
    sh = skia.GradientShader.MakeLinear(
        [skia.Point(r.left(), r.top()), skia.Point(r.left(), r.bottom())],
        [skia.Color(*top, int(255 * a)), skia.Color(*bottom, int(255 * a))])
    c.drawRect(r, skia.Paint(Shader=sh))


def soft(c, cx, cy, rad, rgb, a=0.20):
    sh = skia.GradientShader.MakeRadial(
        skia.Point(cx, cy), rad, [skia.Color(*rgb, int(255 * a)), skia.Color(*rgb, 0)], [0, 1])
    c.drawRect(skia.Rect.MakeXYWH(cx - rad, cy - rad, rad * 2, rad * 2),
               skia.Paint(Shader=sh, AntiAlias=True))


def image(c, img_arr, x, y, w, h, a=1.0, blend=None):
    """Composite an RGB array or PIL image (the 3D plate) into the canvas."""
    if img_arr is None:
        return
    if hasattr(img_arr, "convert"):        # stage.render returns a PIL image
        img_arr = np.asarray(img_arr.convert("RGB"), np.uint8)
    img_arr = np.asarray(img_arr, np.uint8)
    if img_arr.ndim == 3 and img_arr.shape[2] == 4:
        rgba = np.ascontiguousarray(img_arr)      # premultiplied RGBA, by contract
    else:
        rgba = np.dstack([img_arr, np.full(img_arr.shape[:2], 255, np.uint8)])
    si = skia.Image.fromarray(np.ascontiguousarray(rgba), skia.kRGBA_8888_ColorType)
    p = skia.Paint()
    p.setAlphaf(clamp(a))
    if blend == "multiply":
        p.setBlendMode(skia.BlendMode.kMultiply)
    c.drawImageRect(si, skia.Rect.MakeXYWH(0, 0, si.width(), si.height()),
                    skia.Rect.MakeXYWH(x, y, w, h),
                    skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kNone), p)


# ---------------------------------------------------------------------- film
class Shot:
    def __init__(self, name, t0, t1, cam, draw):
        self.name, self.t0, self.t1, self.cam, self._draw = name, t0, t1, cam, draw


class Film:
    def __init__(self, shots, fps=30, size=(W, H), seed=11):
        self.shots = shots
        self.fps = fps
        self.S = size[0] / float(W)
        self.W, self.H = size
        self.seed = seed
        self.duration = shots[-1].t1
        self.hud = None

    def shot_at(self, t):
        for s in self.shots:
            if s.t0 <= t < s.t1:
                return s
        return self.shots[-1]

    def draw(self, t):
        shot = self.shot_at(t)
        c0 = shot.cam
        u = span(t, shot.t0, shot.t1)
        z = c0.get("z", 1.0) * (1 + c0.get("dz", 0.0) * ease_io(u))
        dx = c0.get("dx", 0.0) * ease_io(u)
        dy = c0.get("dy", 0.0) * ease_io(u)
        surf = skia.Surface.MakeRaster(skia.ImageInfo.Make(
            self.W, self.H, skia.ColorType.kRGBA_8888_ColorType,
            skia.AlphaType.kPremul_AlphaType))
        c = surf.getCanvas()
        c.clear(skia.Color(*c0.get("bg", PAPER)))
        c.save()
        c.scale(self.S, self.S)
        c.translate(W / 2 + dx, H / 2 + dy)
        c.scale(z, z)
        c.translate(-W / 2, -H / 2)
        shot._draw(c, t - shot.t0, shot, t)
        c.restore()
        if self.hud:
            c.save()
            c.scale(self.S, self.S)
            self.hud(c, t, shot)
            c.restore()
        arr = surf.makeImageSnapshot().toarray(
            colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
        return self.post(arr, t, shot.name)

    def post(self, arr, t, shot=""):
        """Grain always; vignette ONLY on the dark shot.

        A vignette on a porcelain page darkens the paper toward the edges, which
        makes the page look dirty and — worse — makes the 3D plate's frame read as
        a pasted rectangle. On light ground the page stays flat and clean.
        """
        h, w = arr.shape[:2]
        rng = np.random.default_rng((self.seed * 1013 + int(t * self.fps)) % 2 ** 31)
        arr = arr * (0.993 + 0.014 * rng.random((h, w, 1), dtype=np.float32))
        if shot == "menu":
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            dx = (xx - w / 2) / (w / 2)
            dy = (yy - h / 2) / (h / 2)
            d = np.sqrt(dx * dx + dy * dy) / math.sqrt(2)
            arr = arr * (1.0 - 0.22 * np.clip((d - 0.45) / 0.55, 0, 1)[..., None] ** 1.5)
        return np.clip(arr, 0, 255).astype(np.uint8)

    def frame(self, n):
        return self.draw(n / self.fps)


def place_cutout(c, arr, cx, cy, max_w, max_h, scale=1.0, fade=1.0):
    """Place an RGBA cut-out by its ALPHA BOUNDING BOX, centred on (cx, cy).

    Placing the raw render puts the object wherever the camera happened to leave
    it — it drifted into the bottom-right corner on one shot. Measuring the alpha
    bbox first makes the placement deterministic: the object is always centred
    where the composition wants it, whatever the camera did.
    """
    a = np.asarray(arr).mean(axis=2)
    ys, xs = np.where(a < 235)          # the object is everything darker than paper
    if len(xs) == 0:
        return
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    sub = np.asarray(arr)[y0:y1, x0:x1]
    if len(xs) == 0:
        return
    h, w = sub.shape[:2]
    k = min(max_w / w, max_h / h) * scale
    pw, ph = w * k, h * k
    image(c, sub, cx - pw / 2, cy - ph / 2, pw, ph, fade, blend="multiply")


def place_plate(c, arr, cx, cy, w, h):
    """Draw a WHITE-GROUND plate at a fixed rect with multiply.

    Deliberately not bbox-fitted: as the object turns, its bounding box changes
    width, so a bbox fit rescales every frame and the object appears to pump and
    drift. A fixed rect keeps it nailed to the composition; the rotation happens
    inside it.
    """
    image(c, arr, cx - w / 2, cy - h / 2, w, h, 1.0, blend="multiply")
