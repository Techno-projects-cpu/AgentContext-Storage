"""
layout.py — the page layout: header, index, diagram slot, mechanism line, chips.

The channel's type hierarchy, in order of visual weight:
    index number   (huge, accent)
    term           (huge, black)
    mechanism line (large, black, two lines max)
    detail lines   (small, grey)
    chips          (tiny caps, boxed)
Everything is left-aligned on a single 60 px margin; nothing is centred except the
title and sign-off cards.
"""
import os

from PIL import Image, ImageDraw, ImageFont

import copy as C
import draw as DR

W, H = 1080, 1920
M = 60                     # margin
INK = (17, 17, 17)
GREY = (128, 128, 128)
MID = (90, 90, 90)
PAPER = (255, 255, 255)
RULE = (226, 226, 226)

_HERE = os.path.dirname(os.path.abspath(__file__))
_FONT_DIRS = [
    os.path.join(_HERE, "..", "assets", "fonts"),
    "/home/user/AgentContext-Storage/skills/video-to-shorts-skill/fonts",
]

_cache = {}


def font(kind, size):
    key = (kind, size)
    if key in _cache:
        return _cache[key]
    names = {
        "display": ["Poppins-ExtraBold.ttf", "Display.ttf"],
        "semi": ["Poppins-Bold.ttf", "Label.ttf"],
        "body": ["Poppins-Regular.ttf", "UI.ttf", "Poppins-Bold.ttf"],
        "mono": ["UI.ttf", "Poppins-Regular.ttf"],
    }[kind]
    f = None
    for directory in _FONT_DIRS:
        for name in names:
            path = os.path.join(directory, name)
            if os.path.exists(path):
                f = ImageFont.truetype(path, size)
                break
        if f:
            break
    if f is None:
        f = ImageFont.load_default()
    _cache[key] = f
    return f


def _text_w(d, s, f, tracking=0):
    if not tracking:
        return d.textlength(s, font=f)
    return sum(d.textlength(ch, font=f) for ch in s) + tracking * max(0, len(s) - 1)


def _text(d, xy, s, f, fill, tracking=0):
    """Draw with optional letter tracking (PIL has no tracking support)."""
    x, y = xy
    if not tracking:
        d.text((x, y), s, font=f, fill=fill)
        return
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + tracking


def _wrap(d, s, f, max_w):
    out, cur = [], ""
    for word in s.split():
        cand = (cur + " " + word).strip()
        if d.textlength(cand, font=f) <= max_w or not cur:
            cur = cand
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def _ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def base():
    img = Image.new("RGB", (W, H), PAPER)
    return img, ImageDraw.Draw(img)


def header(d, i, beat, total=5, counter=None):
    """Top rule with tiny caps: brand left, counter right."""
    _text(d, (M, 108), "BYTE SIZED", font("semi", 26), INK, tracking=4)
    label = counter if counter is not None else f"{beat['n']} / {total:02d}"
    w = _text_w(d, label, font("semi", 26), 4)
    _text(d, (W - M - w, 108), label, font("semi", 26), INK, tracking=4)
    d.line([(M, 152), (W - M, 152)], fill=RULE, width=3)


def footer(d, text, progress):
    d.line([(M, H - 160), (W - M, H - 160)], fill=RULE, width=3)
    _text(d, (M, H - 140), text, font("semi", 22), GREY, tracking=3)
    # progress bar
    x0, x1 = W - M - 260, W - M
    d.rectangle([x0, H - 130, x1, H - 124], fill=RULE)
    d.rectangle([x0, H - 130, x0 + int(260 * progress), H - 124], fill=INK)


def beat_card(i, t_local, t_global, total_dur):
    """One technology. t_local is seconds into this beat."""
    beat = C.BEATS[i]
    color = beat["color"]
    img, d = base()

    header(d, i, beat)
    footer(d, C.FOOTER, t_global / total_dur)

    appear = _ease_out(t_local / 0.45)

    # --- index + term -------------------------------------------------------
    y = 168
    _text(d, (M, y), beat["kicker"], font("semi", 24), GREY, tracking=2)

    # index number, huge, accent
    num_f = font("display", 118)
    _text(d, (M - 6, y + 40), beat["n"], num_f, color)
    num_w = _text_w(d, beat["n"], num_f)
    # term, huge, black
    term_f = font("display", 118)
    _text(d, (M + num_w + 34, y + 40), beat["term"], term_f, INK)

    # accent bar that grows in
    bar_w = int(180 * appear)
    d.rectangle([M, y + 190, M + bar_w, y + 202], fill=color)

    # --- diagram ------------------------------------------------------------
    slot_y = 428
    ART = 780
    art = DR.render(beat["kind"], t_local, color)
    art = art.resize((ART, ART), Image.LANCZOS)
    offset = int((1 - appear) * 26)
    img.paste(art, (M - 10 + offset, slot_y + offset))

    # --- mechanism line -----------------------------------------------------
    y = slot_y + ART + 40
    # Auto-fit: shrink the mechanism line until every one of its lines fits the
    # margin. Hard-coded line breaks plus a fixed size is how text runs off frame.
    lines = beat["line"].split("\n")
    size = 66
    while size > 38:
        f_line = font("display", size)
        if max(_text_w(d, ln, f_line) for ln in lines) <= W - 2 * M:
            break
        size -= 2
    f_line = font("display", size)
    step = int(size * 1.24)
    for k, line in enumerate(lines):
        _text(d, (M, y + k * step), line, f_line, INK)

    # --- detail lines -------------------------------------------------------
    y = y + step * len(lines) + 30
    f_detail = font("body", 32)
    for k, line in enumerate(beat["detail"]):
        _text(d, (M, y + k * 44), line, f_detail, MID)

    # --- chips --------------------------------------------------------------
    y = H - 250
    f_chip_b = font("semi", 21)
    f_chip_s = font("body", 18)
    widths = [
        max(_text_w(d, head, f_chip_b, 2), _text_w(d, sub, f_chip_s)) + 40
        for head, sub in beat["chips"]
    ]
    # If the row would overflow, shrink every box by the same factor.
    avail = W - 2 * M - 16 * (len(widths) - 1)
    scale = min(1.0, avail / sum(widths)) if sum(widths) else 1.0
    x = M
    for (head, sub), box_w in zip(beat["chips"], widths):
        box_w = int(box_w * scale)
        d.rounded_rectangle([x, y, x + box_w, y + 92], radius=14, outline=INK, width=3)
        _text(d, (x + 20, y + 16), head, f_chip_b, INK, tracking=2)
        _text(d, (x + 20, y + 50), sub, f_chip_s, GREY)
        x += box_w + 16
    return img


def title_card(t_local):
    img, d = base()
    appear = _ease_out(t_local / 0.5)


    _text(d, (M, 360), "TECH, EXPLAINED IN MINUTES", font("semi", 26), GREY, tracking=4)

    size = 132
    while size > 60:
        f = font("display", size)
        if max(_text_w(d, C.TITLE, f), _text_w(d, C.TITLE_2, f)) <= W - 2 * M:
            break
        size -= 4
    f = font("display", size)
    _text(d, (M - 6, 430), C.TITLE, f, INK)
    _text(d, (M - 6, 430 + size + 18), C.TITLE_2, f, (37, 99, 235))

    # growing rule
    rule_y = 430 + 2 * size + 46
    d.rectangle([M, rule_y, M + int(300 * appear), rule_y + 12], fill=(37, 99, 235))

    _text(d, (M, rule_y + 54), C.SUB, font("body", 36), MID)

    # five little screen glyphs, one per beat, lighting up in sequence
    y = 1120
    for k, beat in enumerate(C.BEATS):
        x = M + k * 196
        on = t_local > 0.5 + k * 0.28
        fill = beat["color"] if on else (243, 243, 243)
        d.rounded_rectangle([x, y, x + 160, y + 110], radius=10, fill=fill, outline=INK, width=3)
        _text(d, (x, y + 122), beat["term"], font("semi", 22), INK, tracking=1)

    _text(d, (M, 1400), "5 SCREENS · 90 YEARS · ONE QUESTION:", font("semi", 30), INK, tracking=2)
    _text(d, (M, 1452), "HOW DOES A PIXEL MAKE LIGHT?", font("display", 52), (37, 99, 235))

    footer(d, C.FOOTER, 0.0)
    return img


def table_card(t_local):
    img, d = base()
    header(d, 0, C.BEATS[0], 5, counter="RECAP")
    footer(d, C.FOOTER, 1.0)

    _text(d, (M, 190), "ALL FIVE, SIDE BY SIDE", font("semi", 26), GREY, tracking=3)
    _text(d, (M, 236), "THE WHOLE BOARD", font("display", 96), INK)

    cols = [M, M + 300, M + 470, M + 640, M + 810]
    y = 430
    f_h = font("semi", 24)
    f_c = font("semi", 34)
    f_s = font("body", 28)

    for x, head in zip(cols, C.TABLE_HEAD):
        _text(d, (x, y), head, f_h, GREY, tracking=2)
    d.line([(M, y + 46), (W - M, y + 46)], fill=INK, width=4)

    row_h = 116
    for r, row in enumerate(C.TABLE):
        y = 520 + r * row_h
        reveal = t_local > 0.25 + r * 0.18
        if not reveal:
            continue
        d.line([(M, y + 92), (W - M, y + 92)], fill=RULE, width=2)
        color = C.BEATS[r]["color"]
        # screen name with accent dot
        d.ellipse([M, y + 34, M + 22, y + 56], fill=color)
        _text(d, (M + 38, y + 22), row[0], f_c, INK)
        for x, cell in zip(cols[1:], row[1:]):
            f = f_s if not cell.isdigit() and len(cell) < 10 else f_s
            _text(d, (x, y + 28), cell, f, MID)

    _text(d, (M, 1300), "BLACKS = how dark an off pixel gets.", font("body", 27), GREY)
    _text(d, (M, 1342), "BRIGHT = how hard it fights a sunlit room.", font("body", 27), GREY)

    # the takeaway box: dense, opinionated, quotable
    y = 1416
    d.rectangle([M, y, W - M, y + 292], fill=(17, 17, 17))
    _text(d, (M + 34, y + 30), "SO WHICH ONE?", font("semi", 24), (170, 170, 170), tracking=3)
    _text(d, (M + 34, y + 76), "Dark room: OLED.", font("display", 42), PAPER)
    _text(d, (M + 34, y + 136), "Bright room: LCD.", font("display", 42), PAPER)
    _text(d, (M + 34, y + 196), "Both, forever: MICROLED.", font("display", 42), (120, 170, 255))
    return img


def sign_card(t_local):
    img, d = base()

    n = 0.9 + 0.05 * (t_local % 1.0)
    _text(d, (M, 300), "THAT'S ALL FIVE.", font("semi", 26), GREY, tracking=4)

    f = font("display", 92)
    lines = _wrap(d, C.SIGN, f, W - 2 * M)
    for k, line in enumerate(lines):
        _text(d, (M - 4, 370 + k * 110), line, f, INK)

    d.rectangle([M, 700, M + 300, 712], fill=(37, 99, 235))

    _text(d, (M, 780), "DROP YOURS IN THE COMMENTS.", font("body", 36), MID)
    _text(d, (M, 840), "NEXT: EVERY CHARGING CABLE EXPLAINED", font("semi", 30), (37, 99, 235), tracking=2)

    footer(d, C.FOOTER, 1.0)
    return img
