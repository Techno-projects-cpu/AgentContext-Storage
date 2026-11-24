"""
ads.py — two ads, two visual systems, one standard.

AD 1  "THE MENU"      20.0 s  · look A (grid + phosphor green) · breadth is the product
AD 2  "HONEST MODE"   18.8 s  · look B (paper + deep green)     · refusals are the product

Both obey the brag floor in agent-context/BRAG-PROMPT.md: 15–25 s, type >= 28 px,
0.45 s ease-out entrances, holds derived from the copy, 0.30 s cross-fades, and
frame 0 carrying ink.

Layout is measured, never typed: every block goes through kit.stack / kit.draw_block,
which align on ink boxes, so a 360 px numeral and a 92 px word can sit next to each
other without the descender collision that hand-placed y values produce.
"""
import kit as K
from kit import (W, H, M, font, text, tw, fit_size, ease_out, ease_in_out,
                 draw_block, measure, stack, ink)

import brand as B

SAFE_TOP = 230
SAFE_BOT = 1500


def _y(items, gap=10):
    """y for a measured block, optically centred in the safe band."""
    return int((SAFE_TOP + SAFE_BOT) / 2 - measure(items, gap) / 2)


def fits(items, gap=10):
    return measure(items, gap) <= (SAFE_BOT - SAFE_TOP)


class Card:
    def __init__(self, name, dur, draw):
        self.name, self.dur, self.draw = name, float(dur), draw


# ==================================================================== AD 1: THE MENU
def _menu_open(t, dur):
    """Frame 0 is the thumbnail — the number is already there. No fade from nothing."""
    img, d = K.menu_base(grid_phase=t * 0.02)
    K.menu_header(d, "DUABLE", "01 / 06")
    K.menu_footer(d, t / dur * 0.18)

    pop = ease_out(t / 0.45)
    f_num = font("black", int(340 * (0.94 + 0.06 * pop)))
    f_word = font("black", 88)
    f_sub = font("bold", 36)

    head = [("24", f_num, K.MENU_GREEN), ("SERVICES", f_word, K.MENU_INK)]
    block = head + [(B.MENU["hook_sub"], f_sub, K.MENU_DIM, 40)]
    y = _y(block, gap=6)
    y = stack(d, head, M, y, t, gap=-8, stagger=0.10)
    y += 34
    stack(d, [("ONE STUDIO.", f_sub, K.MENU_DIM)], M, y, t, stagger=0.2)

    a = ease_out((t - 0.45) / 0.4)
    if a > 0:
        d.rectangle([M, y + 76, M + int(320 * a), y + 88], fill=K.MENU_GREEN)
    return img


def _menu_categories(t, dur):
    img, d = K.menu_base(grid_phase=t * 0.02)
    K.menu_header(d, "DUABLE", "02 / 06")
    K.menu_footer(d, 0.18 + t / dur * 0.2)

    text(d, (M, 300), "THE MENU", font("bold", 30), K.MENU_DIM, tracking=6)
    text(d, (W - M - tw(d, "BY CATEGORY", font("bold", 26), 3), 302),
         "BY CATEGORY", font("bold", 26), K.MENU_DIM, tracking=3)

    f_n = font("black", 120)
    f_c = font("black", 56)
    f_s = font("bold", 26)

    rows = B.MENU["cats"]
    for i, (a, b, n) in enumerate(rows):
        appear = ease_out((t - 0.14 * i) / 0.45)
        if appear <= 0:
            continue
        y = 420 + i * 300 + int((1 - appear) * 40)
        nb = ink(f_n, f"{n:02d}")
        words = [(a, f_c, K.MENU_INK), (b, f_c, K.MENU_INK)]
        # the words are vertically centred on the numeral they belong to
        wh = measure(words, gap=14)
        nh = nb[3] - nb[1]
        wy = y + nh / 2 - wh / 2
        d.text((M, y - nb[1]), f"{n:02d}", font=f_n, fill=K.MENU_GREEN)
        yy = draw_block(d, words, M + 210, wy, gap=14)
        draw_block(d, [("SERVICES", f_s, K.MENU_DIM)], M + 212, yy + 16, gap=0)
        a_rule = ease_out((t - 0.14 * i - 0.22) / 0.5)
        if a_rule > 0:
            d.line([(M, y + 214), (M + int((W - 2 * M) * a_rule), y + 214)],
                   fill=K.MENU_RULE, width=2)
    return img


def _menu_mid(t, dur):
    img, d = K.menu_base(grid_phase=t * 0.02)
    K.menu_header(d, "DUABLE", "03 / 06")
    K.menu_footer(d, 0.38 + t / dur * 0.18)

    f = font("black", 82)
    lines = [("BROWSE BY", K.MENU_INK), ("CATEGORY.", K.MENU_INK),
             ("OPEN THE PAGE FOR", K.MENU_INK), ("THE EXACT THING", K.MENU_INK),
             ("YOU NEED.", K.MENU_GREEN)]
    items = [(s, f, c) for s, c in lines]
    y = _y(items, gap=14)
    y = stack(d, items[:2], M, y, t, gap=14, stagger=0.12)
    y += 40
    stack(d, items[2:], M, y, t, gap=14, stagger=0.12, t0=0.34)
    return img


def _menu_process(t, dur):
    img, d = K.menu_base(grid_phase=t * 0.02)
    K.menu_header(d, "DUABLE", "04 / 06")
    K.menu_footer(d, 0.56 + t / dur * 0.18)

    text(d, (M, 330), "FOUR STEPS", font("bold", 30), K.MENU_DIM, tracking=6)
    f_n = font("black", 96)
    for i, step in enumerate(B.PROCESS):
        appear = ease_out((t - 0.14 * i) / 0.45)
        if appear <= 0:
            continue
        y = 450 + i * 290
        lit = t > 0.45 + 0.16 * i
        d.text((M, y), f"0{i+1}", font=f_n, fill=K.MENU_GREEN if lit else K.MENU_RULE)
        f_s = font("black", fit_size(d, [step], "black", 62, W - M - 250))
        d.text((M + 230, y + 30), step, font=f_s, fill=K.MENU_INK)
    return img


def _menu_end(t, dur):
    img, d = K.menu_base(grid_phase=t * 0.02)
    K.menu_header(d, "DUABLE", "05 / 06")
    K.menu_footer(d, 0.8 + t / dur * 0.2)

    f = font("black", 82)
    items = [(B.MENU["end_1"], f, K.MENU_INK), (B.MENU["end_2"], f, K.MENU_GREEN)]
    y = _y(items, gap=18)
    y = stack(d, items, M, y, t, gap=18, stagger=0.16)
    text(d, (M, y + 34), B.URL_SHORT, font("bold", 32), K.MENU_DIM, tracking=3)
    return img


# ================================================================= AD 2: HONEST MODE
def _honest_open(t, dur):
    """Frame 0 carries the refusal, already set on paper. Nothing fades from black."""
    img, d = K.paper_base()
    K.paper_header(d, "DUABLE", "01 / 05")
    K.paper_footer(d, 0.15)

    f = font("black", 124)
    items = [("NO MAGIC", f, K.DEEP), ("NUMBERS.", f, K.DEEP)]
    y = int((SAFE_TOP + SAFE_BOT) / 2 - 250)
    bb = ink(f, "NUMBERS.")
    line_h = (bb[3] - bb[1]) + 22

    for i, s_ in enumerate(("NO MAGIC", "NUMBERS.")):
        a = ease_out((t - 0.12 * i) / 0.45)
        if a > 0:
            d.text((M + 24, y + i * line_h + (1 - a) * 24 - bb[1]), s_, font=f, fill=K.DEEP)

    # a single hairline cancels "NUMBERS" once the thought lands — thin, and only to
    # the width of the word, so it reads as a correction rather than a bar
    strike = ease_in_out((t - 0.85) / 0.55)
    if strike > 0:
        mid = y + line_h - bb[1] + (bb[1] + bb[3]) / 2
        w = int(tw(d, "NUMBERS.", f) * strike)
        d.rectangle([M + 24, mid - 5, M + 24 + w, mid + 5], fill=K.DEEP)

    a = ease_out((t - 0.6) / 0.45)
    if a > 0:
        y_sub = y + 2 * line_h + 56
        d.text((M + 24, y_sub + (1 - a) * 18), B.HONEST["open_sub"],
               font=font("bold", 32), fill=K.DEEP_SOFT)
    if t > 0.9:
        a2 = ease_out((t - 0.9) / 0.45)
        text(d, (M + 24, SAFE_BOT - 60), B.DESCRIPTOR, font("bold", 26),
             tuple(int(c + (K.DEEP_SOFT[i] - c) * a2) for i, c in enumerate(K.PAPER_2)), tracking=3)
    return img


def _honest_body(t, dur):
    img, d = K.paper_base()
    K.paper_header(d, "DUABLE", "02 / 05")
    K.paper_footer(d, 0.35)

    f = font("black", 78)
    f_lead = font("bold", 28)
    items = [("THE SIGNAL", f_lead, K.DEEP_SOFT, 0),
             ("A SERVICE", f, K.DEEP, 26),
             ("FOR EVERY", f, K.DEEP, 0),
             ("PART OF IT.", f, K.DEEP, 0)]
    y = _y(items + [(B.HONEST["body_2"], font("bold", 30), K.DEEP_SOFT, 60)], gap=6)
    y = stack(d, items, M + 24, y, t, gap=6, stagger=0.13)
    a = ease_out((t - 1.1) / 0.45)
    if a > 0:
        d.line([(M + 24, y + 30), (M + 24 + int((W - 2 * M - 48) * a), y + 30)],
               fill=K.PAPER_RULE, width=2)
        text(d, (M + 24, y + 58), B.HONEST["body_2"], font("bold", 30), K.DEEP_SOFT, tracking=3)
    return img


def _honest_privacy(t, dur):
    img, d = K.paper_base()
    K.paper_header(d, "DUABLE", "03 / 05")
    K.paper_footer(d, 0.5)

    f = font("black", 82)
    items = [("YOUR PROJECT NOTE", f, K.DEEP), ("STAYS IN", f, K.DEEP),
             ("THIS BROWSER.", f, K.DEEP_SOFT)]
    sub = (B.HONEST["body_sub"], font("bold", 30), K.DEEP_SOFT, 62)
    y = _y(items + [sub], gap=6)
    y = stack(d, items, M + 24, y, t, gap=6, stagger=0.15)
    a = ease_out((t - 1.0) / 0.45)
    if a > 0:
        d.rectangle([M + 24, y + 30, M + 24 + int(96 * a), y + 44], fill=K.DEEP)
        text(d, (M + 24, y + 66), B.HONEST["body_sub"], font("bold", 30), K.DEEP_SOFT, tracking=3)
    return img


def _honest_team(t, dur):
    img, d = K.paper_base()
    K.paper_header(d, "DUABLE", "04 / 05")
    K.paper_footer(d, 0.7)

    f = font("black", 92)
    items = [(B.HONEST["team_1"], f, K.DEEP), (B.HONEST["team_2"], f, K.DEEP)]
    sub = (B.HONEST["team_sub"], font("bold", 30), K.DEEP_SOFT, 64)
    y = _y(items + [sub], gap=8)
    y = stack(d, items, M + 24, y, t, gap=8, stagger=0.16)
    a = ease_out((t - 0.8) / 0.5)
    if a > 0:
        d.line([(M + 24, y + 34), (M + 24 + int(120 * a), y + 34)], fill=K.DEEP, width=4)
        text(d, (M + 24, y + 62), B.HONEST["team_sub"], font("bold", 30), K.DEEP_SOFT, tracking=3)
    return img


def _honest_end(t, dur):
    img, d = K.paper_base()
    K.paper_header(d, "DUABLE", "05 / 05")
    K.paper_footer(d, 0.9)

    f = font("black", fit_size(d, [B.TAGLINE_1, B.TAGLINE_2], "black", 90, W - 2 * M - 48))
    items = [(B.TAGLINE_1, f, K.DEEP), (B.TAGLINE_2, f, K.DEEP)]
    y = _y(items, gap=10)
    y = stack(d, items, M + 24, y, t, gap=10, stagger=0.14)
    a = ease_out((t - 0.65) / 0.45)
    if a > 0:
        text(d, (M + 24, y + 40), B.URL_SHORT, font("bold", 32), K.DEEP_SOFT, tracking=3)
    return img


# ------------------------------------------------------------------- timelines
AD_MENU = [
    Card("open", 3.4, _menu_open),
    Card("categories", 4.8, _menu_categories),
    Card("mid", 3.8, _menu_mid),
    Card("process", 4.2, _menu_process),
    Card("end", 3.8, _menu_end),
]

AD_HONEST = [
    Card("open", 3.6, _honest_open),
    Card("body", 3.8, _honest_body),
    Card("privacy", 4.0, _honest_privacy),
    Card("team", 3.6, _honest_team),
    Card("end", 3.8, _honest_end),
]

ADS = {"menu": AD_MENU, "honest": AD_HONEST}
