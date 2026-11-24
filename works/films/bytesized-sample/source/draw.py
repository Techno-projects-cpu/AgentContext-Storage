"""
draw.py — the schematic for each screen technology.

Flat vector-ish shapes only, drawn with PIL, in the channel's style: bright white
field, heavy black type, one accent colour per beat, diagram centred and filling
the frame. Each function draws into a 1080x1080 box and is a pure function of
(t, beat) so a frame can be re-rendered alone.
"""
import math

from PIL import Image, ImageDraw

W, H = 1080, 1080

INK = (17, 17, 17)
PAPER = (255, 255, 255)
GREY = (150, 150, 150)
LIGHT = (228, 228, 228)


_LABEL_CACHE = {}


def _label(size=34):
    """A font big enough to survive being scaled into the card."""
    from PIL import ImageFont
    if size not in _LABEL_CACHE:
        for path in (
            "/home/user/AgentContext-Storage/works/films/bytesized-sample/assets/fonts/Poppins-Bold.ttf",
            "/home/user/AgentContext-Storage/skills/video-to-shorts-skill/fonts/Poppins-Bold.ttf",
        ):
            try:
                _LABEL_CACHE[size] = ImageFont.truetype(path, size)
                break
            except OSError:
                continue
        else:
            _LABEL_CACHE[size] = ImageFont.load_default()
    return _LABEL_CACHE[size]


def _rr(d, xy, r, fill=None, outline=None, width=3):
    """xy is (x, y) top-left plus a size; callers pass either form."""
    if len(xy) == 2:
        x, y = xy
        box = (x, y, x + 90, y + 80)
    else:
        box = xy
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def _arrow(d, x1, y1, x2, y2, color, width=6, head=18):
    d.line([(x1, y1), (x2, y2)], fill=color, width=width)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (+1, -1):
        d.line(
            [
                (x2, y2),
                (
                    x2 - head * math.cos(ang - s * 0.5),
                    y2 - head * math.sin(ang - s * 0.5),
                ),
            ],
            fill=color,
            width=width,
        )


def draw_crt(d, t, color):
    """Electron gun at the back, beam sweeping a phosphor face, line by line."""
    # Tube: a funnel. Back narrow, front wide.
    d.polygon([(120, 470), (760, 250), (760, 830), (120, 610)], outline=INK, width=6)
    # Phosphor face
    d.rectangle([760, 250, 840, 830], outline=INK, width=6, fill=(240, 240, 240))
    for i in range(5):
        y = 250 + i * 145
        d.line([(760, y), (840, y)], fill=GREY, width=2)

    # Electron gun
    _rr(d, (40, 500), 16, outline=INK, width=6)
    d.rectangle([40, 500, 80, 580], fill=INK)

    # Beam: sweeps vertically with time, sweeping across the face.
    sweep = (t * 1.9) % 1.0
    y_face = 250 + sweep * 580
    d.line([(80, 540), (762, y_face)], fill=color, width=5)
    # beam spread as a narrow triangle
    d.polygon(
        [(80, 534), (80, 546), (762, y_face + 6), (762, y_face - 6)],
        fill=color,
    )
    # already-painted lines above the beam
    for i in range(5):
        y = 250 + i * 145
        if y < y_face:
            d.line([(762, y), (838, y)], fill=color, width=6)
    d.ellipse([752, y_face - 22, 796, y_face + 22], fill=color)

    # magnets
    for yy in (470, 620):
        _rr(d, (300, yy), 10, outline=INK, width=5)
        d.line([(300, yy + 25), (330, yy + 25)], fill=INK, width=5)

    d.text((120, 880), "ELECTRON GUN", fill=INK, font=_label())
    d.text((690, 880), "PHOSPHOR", fill=INK, font=_label())


def draw_lcd(d, t, color):
    """Backlight -> polariser -> crystal shutters -> polariser. Shutters animate."""
    layers = [
        ("BACKLIGHT", (232, 244, 255)),
        ("POLARISER", (205, 205, 205)),
        ("CRYSTALS", None),
        ("POLARISER", (205, 205, 205)),
    ]
    x = 110
    widths = [150, 60, 300, 60]
    for (label, fill), w in zip(layers, widths):
        if label == "CRYSTALS":
            d.rectangle([x, 200, x + w, 800], outline=INK, width=6, fill=PAPER)
            # 7 shutter cells, alternating open/closed, animating
            for i in range(7):
                cy = 230 + i * 80
                phase = math.sin(t * 2.4 + i * 0.8)
                open_amt = 0.5 + 0.5 * phase
                # crystal twist indicator: a bar whose width follows open_amt
                d.rectangle([x + 20, cy, x + w - 20, cy + 54], outline=INK, width=3)
                inner = int((w - 46) * open_amt)
                if inner > 2:
                    d.rectangle([x + 23, cy + 3, x + 23 + inner, cy + 51], fill=color)
        else:
            d.rectangle([x, 200, x + w, 800], outline=INK, width=6, fill=fill)
            d.text((x, 820), label, fill=INK)
        x += w + 18

    # light path arrows
    for yy in (330, 500, 670):
        _arrow(d, 60, yy, 106, yy, color, width=5, head=12)
    _arrow(d, 900, 500, 1000, 500, INK, width=5, head=14)
    d.text((905, 530), "EYE", fill=INK, font=_label())
    d.text((110, 130), "BACKLIGHT STAYS ON", fill=GREY, font=_label())


def draw_plasma(d, t, color):
    """A grid of gas cells; a few ignite and glow."""
    gx, gy = 8, 6
    size = 96
    gap = 18
    x0 = (W - (gx * size + (gx - 1) * gap)) // 2
    y0 = 300
    for j in range(gy):
        for i in range(gx):
            x = x0 + i * (size + gap)
            y = y0 + j * (size + gap)
            # glow wave travelling diagonally
            phase = math.sin(t * 2.0 - (i + j) * 0.7)
            lit = phase > 0.25
            if lit:
                # halo
                for r in range(26, 6, -4):
                    a = int(60 * (1 - r / 30))
                    d.ellipse(
                        [x + size / 2 - r - 20, y + size / 2 - r - 20,
                         x + size / 2 + r + 20, y + size / 2 + r + 20],
                        fill=tuple(min(255, c + a) for c in (255, 255, 255)),
                    )
                d.rectangle([x, y, x + size, y + size], fill=color, outline=INK, width=3)
            else:
                d.rectangle([x, y, x + size, y + size], fill=PAPER, outline=INK, width=3)
    d.text((x0, y0 - 50), "EACH CELL: NEON + XENON", fill=INK, font=_label())
    d.text((x0, y0 + gy * (size + gap) + 30), "VOLTAGE → PLASMA → UV → PHOSPHOR", fill=GREY)


def draw_oled(d, t, color):
    """Two pixels: dark (off) and lit. Emphasis on 'off is truly off'."""
    # left: OFF
    d.rectangle([90, 260, 470, 800], outline=INK, width=6, fill=(8, 8, 8))
    d.text((110, 820), "PIXEL OFF", fill=INK, font=_label())
    d.text((110, 860), "0% LIGHT EMITTED", fill=GREY, font=_label())

    # right: ON
    d.rectangle([610, 260, 990, 800], outline=INK, width=6, fill=PAPER)
    pulse = 0.75 + 0.25 * math.sin(t * 3.0)
    for r in range(150, 20, -14):
        k = int(255 * (1 - r / 170) * pulse)
        d.ellipse([800 - r, 530 - r, 800 + r, 530 + r], fill=(k, 255, k - 40 if k > 40 else k))
    d.ellipse([740, 470, 860, 590], fill=color)
    d.text((630, 820), "PIXEL ON", fill=INK, font=_label())
    d.text((630, 860), "ORGANIC FILM EMITS", fill=GREY, font=_label())

    d.text((90, 200), "NO BACKLIGHT — NOTHING BEHIND THE PIXELS", fill=INK, font=_label())
    _arrow(d, 470, 530, 610, 530, INK, width=4, head=14)
    d.text((480, 490), "SAME", fill=GREY, font=_label())
    d.text((480, 556), "PANEL", fill=GREY, font=_label())


def draw_microled(d, t, color):
    """A dense grid of individual LEDs, each with its own driver line."""
    gx, gy = 10, 6
    r = 22
    gapx = 96
    gapy = 96
    x0 = (W - ((gx - 1) * gapx)) // 2
    y0 = 340
    for j in range(gy):
        for i in range(gx):
            cx = x0 + i * gapx
            cy = y0 + j * gapy
            phase = math.sin(t * 2.2 - (i * 0.5 + j * 0.9))
            on = phase > -0.2
            if on:
                for halo in range(30, 8, -6):
                    d.ellipse([cx - r - halo, cy - r - halo, cx + r + halo, cy + r + halo],
                              outline=tuple(min(255, c) for c in (255, 220, 150)))
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=INK, width=3)
            else:
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PAPER, outline=INK, width=3)
    # a driver line to one pixel
    d.line([(540, 250), (540, y0 - 60)], fill=INK, width=4)
    d.line([(540, y0 - 60), (x0 + 4 * gapx, y0 - 60)], fill=INK, width=4)
    d.line([(x0 + 4 * gapx, y0 - 60), (x0 + 4 * gapx, y0 - r - 8)], fill=INK, width=4)
    d.text((430, 210), "ONE DRIVER PER PIXEL", fill=INK, font=_label())
    d.text((x0 - 40, y0 + gy * gapy - 20), "INORGANIC CRYSTALS — NOTHING TO FADE", fill=GREY, font=_label())


DRAW = {
    "crt": draw_crt,
    "lcd": draw_lcd,
    "plasma": draw_plasma,
    "oled": draw_oled,
    "microled": draw_microled,
}


def render(kind, t, color):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    DRAW[kind](d, t, color)
    return img
