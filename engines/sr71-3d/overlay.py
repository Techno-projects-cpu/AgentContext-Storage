"""
Draws the flat layer over the 3D plate: the channel's overline / headline /
note stack, a datum HUD, and the labels on mechanisms. Vertical 1080x1920.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "/tmp/fonts/ttf"
F = {
    "display": FONT_DIR + "/space-grotesk-700.ttf",
    "display_med": FONT_DIR + "/space-grotesk-500.ttf",
    "body": FONT_DIR + "/inter-400-normal.ttf" if False else FONT_DIR + "/inter-latin-400-normal.ttf",
    "body_med": FONT_DIR + "/inter-500-normal.ttf" if False else FONT_DIR + "/inter-latin-500-normal.ttf",
    "mono": FONT_DIR + "/jetbrains-mono-latin-500-normal.ttf",
    "mono_b": FONT_DIR + "/jetbrains-mono-latin-700-normal.ttf",
}

PAPER = (242, 241, 236)
DIM = (168, 170, 178)
ACCENT = (120, 160, 255)
WARM = (255, 150, 70)
GREEN = (120, 255, 190)

_cache = {}


def font(key, size):
    k = (key, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(F[key], size)
    return _cache[k]


def spaced(draw, xy, s, f, fill, tracking=0.0, anchor="ls"):
    """PIL has no letter-spacing; draw glyph by glyph."""
    x, y = xy
    total = sum(draw.textlength(ch, font=f) for ch in s) + tracking * max(0, len(s) - 1)
    if anchor.startswith("m"):
        x -= total / 2
    elif anchor.startswith("r"):
        x -= total
    for ch in s:
        draw.text((x, y), ch, font=f, fill=fill, anchor="ls")
        x += draw.textlength(ch, font=f) + tracking
    return total


def easer(t):
    """Expo-out: fast in, then hold. The channel's captions snap, they don't drift."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 5


def text_block_size(head, head_size, note=None, size_k=1.0):
    """Measure a block before drawing it, so nothing overlaps anything."""
    lines = head if isinstance(head, list) else [head]
    h = 0
    for ln in lines:
        h += int(head_size * 0.90) + 14
    if note:
        n_lines = 0
        for para in (note if isinstance(note, list) else [note]):
            n_lines += max(1, len(para) / 46)
        h += 18 + 42 * int(np.ceil(n_lines))
    return h


def wrap_text(d, s, f, max_w):
    words, lines, cur = s.split(), [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if d.textlength(cand, font=f) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_head_size(d, head, want, max_w):
    """Largest size <= want at which every headline line fits max_w."""
    lines = head if isinstance(head, list) else [head]
    size = want
    while size > 24:
        f = font("display", size)
        if max(d.textlength(ln, font=f) for ln in lines) <= max_w:
            return size
        size -= 2
    return size


def fit_track(d, s, f, max_w, start=5.0):
    """Tighten letter-spacing until a mono overline fits."""
    tr = start
    while tr > 0.4:
        w = sum(d.textlength(ch, font=f) for ch in s) + tr * max(0, len(s) - 1)
        if w <= max_w:
            return tr
        tr -= 0.4
    return 0.4


def draw_text_block(img, at, overline=None, head=None, note=None,
                    align="left", head_size=104, alpha=1.0, accent_word=None,
                    head_color=PAPER, accent_color=ACCENT, size_k=1.0):
    """
    Draw a block downward from `at` = (x, top). Overline sits above the headline
    by its own measured height, so the two can never collide again.
    """
    if alpha <= 0.004:
        return
    d = ImageDraw.Draw(img)
    x, y = at
    a = alpha
    max_w = img.size[0] - 2 * (56 + 6)
    if overline:
        f = font("mono", max(10, int(24 * size_k)))
        tr = fit_track(d, overline.upper(), f, max_w)
        spaced(d, (x, y + 26), overline.upper(), f,
               tuple(int(c * a) for c in DIM), tracking=tr, anchor=align)
        y += int(62 * size_k)
    if head:
        head_size = fit_head_size(d, head, head_size, max_w)
        fh = font("display", head_size)
        lines = head if isinstance(head, list) else [head]
        # baseline of line n = y + (n+1)*lineH - descender_allowance
        lineH = int(head_size * 1.02)
        for i, ln in enumerate(lines):
            by = y + i * lineH + int(head_size * 0.80)
            if accent_word and accent_word in ln:
                before, _, after = ln.partition(accent_word)
                cx = x
                if align == "ms":
                    cx = x - d.textlength(ln, font=fh) / 2
                if before:
                    d.text((cx, by), before, font=fh,
                           fill=tuple(int(c * a) for c in head_color), anchor="ls")
                    cx += d.textlength(before, font=fh)
                d.text((cx, by), accent_word, font=fh,
                       fill=tuple(int(c * a) for c in accent_color), anchor="ls")
                cx += d.textlength(accent_word, font=fh)
                if after:
                    d.text((cx, by), after, font=fh,
                           fill=tuple(int(c * a) for c in head_color), anchor="ls")
            else:
                d.text((x, by), ln, font=fh,
                       fill=tuple(int(c * a) for c in head_color), anchor=align)
        y += lineH * len(lines) + 8
    if note:
        f = font("body", max(12, int(30 * size_k)))
        wrap = img.size[0] - 2 * (56 + 6)
        for para in (note if isinstance(note, list) else [note]):
            for ln in wrap_text(d, para, f, wrap):
                d.text((x, y + 6), ln, font=f,
                       fill=tuple(int(c * 0.80 * a) for c in DIM), anchor=align)
                y += int(42 * size_k)


def gradient_scrim(img, top_frac=0.52, alpha=0.86, colour=(5, 6, 10)):
    """A soft bottom scrim: solid where the type sits, gone by mid-frame."""
    W, H = img.size
    layer = Image.new("L", (1, H), 0)
    px = layer.load()
    for y in range(H):
        f = y / H
        if f < top_frac:
            v = 0
        else:
            t = (f - top_frac) / (1 - top_frac)
            v = int(255 * alpha * (t ** 1.5))
        px[0, y] = v
    mask = layer.resize((W, H), Image.BILINEAR)
    scrim = Image.new("RGBA", (W, H), colour + (255,))
    scrim.putalpha(mask)
    img.alpha_composite(scrim)


def hud(img, t, shot_idx, shot_name, alpha=1.0, total=None, duration=None):
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    a = int(255 * alpha)
    # top rail
    d.line([(56, 96), (150, 96)], fill=(120, 160, 255, a), width=2)
    d.line([(1040 - 94, 96), (1040, 96)], fill=(255, 255, 255, 70), width=1)
    spaced(d, (56, 76), "CASE FILE 71", font("mono_b", 24), (255, 255, 255, a),
           tracking=4, anchor="l")
    n = total or shot_idx + 1
    spaced(d, (1040, 76), f"{shot_idx + 1:02d} / {n}", font("mono", 24),
           (150, 160, 180, a), tracking=3, anchor="rs")
    # bottom rule + timecode
    d.line([(56, 1842), (1040, 1842)], fill=(255, 255, 255, 42), width=1)
    secs = int(t)
    spaced(d, (56, 1888), f"{secs // 60:02d}:{secs % 60:02d}", font("mono", 22),
           (120, 130, 150, a), tracking=2, anchor="l")
    spaced(d, (1040, 1888), "SR-71 · TITANIUM · JP-7", font("mono", 22),
           (120, 130, 150, a), tracking=2, anchor="rs")
    # progress rail along the very bottom
    p = min(1.0, t / (duration or 51.0))
    d.line([(0, 1916), (W * p, 1916)], fill=(120, 160, 255, int(180 * alpha)), width=3)


def label_pin(img, xy, text, alpha=1.0, color=DIM, side="right", length=90):
    """
    A leader line from a mechanism to its name. All metrics scale with frame
    width so a 540p preview is a faithful reduction of the 1080p master, and the
    label picks whichever side actually has room instead of clipping.
    """
    d = ImageDraw.Draw(img, "RGBA")
    a = int(230 * alpha)
    W, H = img.size
    k = W / 1080.0
    f = font("mono", max(11, int(22 * k)))
    tr = 3 * k
    length = length * k
    tw = 0.0
    for ch in text.upper():
        tw += d.textlength(ch, font=f) + tr
    margin = 56 * k
    need = length + 14 * k + tw
    x, y = xy
    room_r = W - margin - x
    room_l = x - margin
    if side == "right" and room_r < need and room_l > room_r:
        side = "left"
    elif side == "left" and room_l < need and room_r > room_l:
        side = "right"
    if side == "right":
        d.line([(x, y), (x + length, y)], fill=color + (a,), width=max(1, int(2 * k)))
        d.ellipse([x - 4 * k, y - 4 * k, x + 4 * k, y + 4 * k], fill=color + (a,))
        spaced(d, (x + length + 14 * k, y + 10 * k), text.upper(), f,
               color + (a,), tracking=tr, anchor="l")
    else:
        d.line([(x, y), (x - length, y)], fill=color + (a,), width=max(1, int(2 * k)))
        d.ellipse([x - 4 * k, y - 4 * k, x + 4 * k, y + 4 * k], fill=color + (a,))
        spaced(d, (x - length - 14 * k, y + 10 * k), text.upper(), f,
               color + (a,), tracking=tr, anchor="r")


def glow_text(base, xy, text, size=54, color=(255, 190, 110), alpha=1.0, blur=18):
    """Additive glow under a hot label: heat, TEB flame, ignition."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text(xy, text, font=font("mono_b", size),
           fill=color + (int(255 * alpha),), anchor="ls")
    halo = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(halo)
    base.alpha_composite(halo)
    base.alpha_composite(layer)


def heat_haze(img, strength=0.0):
    """Cheap refraction: push rows sideways by a sine, plus a warm wash."""
    if strength <= 0.001:
        return img
    a = np.asarray(img.convert("RGB"), np.float32)
    H, W = a.shape[:2]
    yy = np.arange(H)[:, None]
    dx = (np.sin(yy * 0.09) * strength * 5.0).astype(np.int32)
    idx = (np.arange(W)[None, :] - dx) % W
    out = a[np.arange(H)[:, None], idx]
    warm = np.array([1.06, 0.98, 0.90], np.float32)
    out = out * warm
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def scanlines(img, amount=0.05):
    a = np.asarray(img.convert("RGB"), np.float32)
    H = a.shape[0]
    mask = 1.0 - amount * (np.arange(H) % 3 == 0)[:, None, None]
    return Image.fromarray(np.clip(a * mask, 0, 255).astype(np.uint8))


def safe(alpha=1.0):
    """Text safe margin for 1080x1920 with Shorts chrome on the right/bottom."""
    return dict(left=56, right=1040, top=140, bottom=1800)
