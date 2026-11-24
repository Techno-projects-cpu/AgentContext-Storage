"""
scenes.py — the edit. Porcelain, ink, one olive signal.

    1  00.0 – 04.2   STATEMENT   "a studio with a service for that" — and the
                                 four counts land in the margin, on the beat
    2  04.2 – 09.0   THE MENU    48 lines of the site's own service names, one
                                 column running against a fixed index rail
    3  09.0 – 13.2   THE OBJECT  a 3D still life of the four stacks (8/4/5/7),
                                 shot on a turntable at dawn light
    4  13.2 – 18.0   CATEGORIES  four chapters: kicker, site headline, count
    5  18.0 – 22.8   THE CLOSE   line, rules converging, URL

Copy is the site's. Nothing is invented, no prices, no client counts.
"""
import math

import numpy as np
import skia

import kit as K
from kit import (W, H, M, PAPER, PAPER_D, INK, INK_SOFT, HAIR, OLIVE, OLIVE_L,
                 text, words, rise, rule, line, ring, disc, vgrad, soft, ease_out,
                 ease_io, ease_expo, span, clamp, fit, fit_tracked, tw, font)

# The site's four chapters, with its own counts, kickers and headlines.
CHAPTERS = [
    ("01 / DESIGN", "WEB & TECHNOLOGY", 8, "Digital foundations,",
     "built for real use."),
    ("02 / AUTOMATE", "AI & AUTOMATION", 4, "Use AI where",
     "it earns its place."),
    ("03 / EDIT", "CREATIVE & MEDIA", 5, "Make the story and",
     "visuals feel connected."),
    ("04 / POSITION", "MARKETING & GROWTH", 7, "Say what matters.",
     "Reach who matters."),
]

# All 24 service names, in the site's order — never re-sorted, never abridged.
SERVICES = [
    "WEBSITE DESIGN & PLANNING", "WEBSITE DEVELOPMENT", "WEB APPS & DASHBOARDS",
    "E-COMMERCE WEBSITES", "WEBSITE FIXES & MAINTENANCE",
    "WEBSITE AUDITS & OPTIMIZATION", "INTEGRATIONS & APIS", "MOBILE APP DEVELOPMENT",
    "WORKFLOW AUTOMATION", "AI-ASSISTED WORKFLOWS", "CUSTOM AI AGENTS",
    "AI PRODUCT FEATURES",
    "VIDEO EDITING", "IMAGE EDITING", "GRAPHIC DESIGN", "BRAND & CAMPAIGN VISUALS",
    "GENERATED CONTENT",
    "SOCIAL MEDIA MANAGEMENT", "CONTENT & COPYWRITING", "CAMPAIGN PLANNING",
    "PAID ADVERTISING", "POSITIONING & MESSAGING", "AUDIENCE RESEARCH",
    "GROWTH STRATEGY",
]
URL = "duableindustries.vercel.app"


def hud(c, t, film, shot):
    """The running head: brand left, chapter right, and a progress rule. Drawn in
    screen space, so it is the one thing that never moves."""
    idx = film.shots.index(shot)
    text(c, "DUABLE", M, 150, "caps", 30, INK, 0.72, tracking=7)
    text(c, f"{idx + 1:02d} / {len(film.shots):02d}", W - M, 150, "caps", 30,
         INK, 0.50, align="right", tracking=7)
    rule(c, M, 178, W - 2 * M, HAIR, 0.9)
    p = span(t, shot.t0, shot.t1)
    c.drawRect(skia.Rect.MakeXYWH(M, 176, (W - 2 * M) * p, 3), K.paint(OLIVE, 0.95))


# --------------------------------------------------------- 1 · the statement
def s_statement(c, t, shot, t_abs):
    """Porcelain. One serif sentence, arriving in two halves, and the four counts
    landing in the right margin one beat apart. A rule grew under the first line,
    and the whole page creeps left the entire shot."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (242, 240, 232), (232, 229, 219), 1.0)
    soft(c, W * 0.18, H * 0.20, 760, OLIVE_L, 0.10)

    text(c, "INDEPENDENT CREATIVE TECHNOLOGY STUDIO", M, 320, "caps", 30, INK_SOFT,
         0.85, tracking=6)
    rule(c, M, 352, 190, OLIVE, 0.9, span(t, 0.05, 0.7), 3)

    # the line: serif, two halves, the second arriving a beat later
    s1, s2 = "A studio with", "a service for that."
    # each line is fitted on its own: fitting the pair forced the whole sentence
    # down to the width of the longer one, which left it looking timid
    n1 = min(fit(s1, "serif", 152, W - 2 * M), fit(s2, "serif", 152, W - 2 * M))
    rise(c, s1, M, 690, "serif", n1, INK, span(t, 0.10, 0.62))
    rise(c, s2, M, 690 + n1 * 1.02, "serif", n1, OLIVE, span(t, 0.34, 0.90))

    # the counts: right margin, each on its own beat, with a hairline under each
    for i, (label, cnt) in enumerate([("WEB & TECHNOLOGY", 8), ("AI & AUTOMATION", 4),
                                      ("CREATIVE & MEDIA", 5), ("MARKETING & GROWTH", 7)]):
        u = span(t, 0.78 + 0.15 * i, 1.18 + 0.15 * i)
        if u <= 0:
            continue
        y = 1090 + i * 112
        text(c, f"{cnt:02d}", W - M, y, "serif", 74, OLIVE, u, align="right")
        text(c, label, W - M, y + 34, "caps", 27, INK_SOFT, u * 0.9, align="right", tracking=4)
        rule(c, W - M - 300, y + 54, 300, HAIR, 0.9, span(t, 0.95 + 0.15 * i, 1.4 + 0.15 * i))

    # the floor: a single line of small print, and the URL
    rule(c, M, H - 300, W - 2 * M, HAIR, 0.9, span(t, 1.35, 1.85))
    foot = "TWENTY-FOUR SERVICES · FOUR CATEGORIES · ONE STUDIO"
    text(c, foot, M, H - 250, "caps",
         fit_tracked(foot, "caps", 28, W - 2 * M, 4), INK_SOFT,
         ease_out(span(t, 1.45, 1.8)), tracking=4)
    text(c, URL, M, H - 196, "ui", 30, INK, ease_out(span(t, 1.6, 1.95)))
    # a thin olive rule that keeps travelling under the line for the whole shot —
    # the page is never completely still, even after the copy lands
    sweep = ease_io(span(t, 0.0, 1.0))
    c.drawRect(skia.Rect.MakeXYWH(M + (W - 2 * M - 120) * sweep, H - 336, 120, 3),
               K.paint(OLIVE, 0.85))


# -------------------------------------------------------------- 2 · the menu
def s_menu(c, t, shot, t_abs):
    """Two lists running in opposite directions past a fixed index rail — the
    menu as a machine. The rail holds still; everything else moves."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (24, 24, 20), (16, 16, 13), 1.0)
    text(c, "THE MENU", M, 320, "serif", 96, PAPER)
    text(c, "TWENTY-FOUR PAGES", W - M, 320, "caps", 30, OLIVE_L, align="right", tracking=6)

    top, bot = 404, H - 400
    # the fixed rail: an index column that never scrolls. Drawn AFTER the lists so
    # nothing can bury it (the first pass lost it behind a scrim).
    RAIL = M + 84

    # left column: names, running up
    speed = 116
    n = len(SERVICES)
    for i in range(n + 8):
        y = bot + 40 - ((t * speed + i * 92) % (n * 92))
        if y < top or y > bot + 40:
            continue
        idx = i % n
        # only the row crossing the reading line is fully lit
        focus = 1.0 - min(1.0, abs(y - (top + bot) / 2) / 620)
        a = 0.26 + 0.74 * focus
        disc(c, RAIL, y - 12, 3 + 3 * focus, OLIVE_L, a)
        text(c, f"{idx + 1:02d}", M - 2, y, "caps", 26, OLIVE_L, a * 0.9, tracking=3)
        size = 34 + 12 * focus
        text(c, SERVICES[idx], RAIL + 46, y, "caps", size,
             PAPER if focus > 0.5 else (150, 150, 140), a, tracking=2)

    rule(c, RAIL, top - 30, bot - top + 60, OLIVE, 0.55, 1.0, 3, vertical=True)

    # the mask: the list falls away top and bottom instead of being cut
    for anchor, box in (("top", (0, top - 30, W, 200)), ("bot", (0, bot - 150, W, 210))):
        p = skia.GradientShader.MakeLinear(
            [skia.Point(0, box[1]), skia.Point(0, box[1] + box[3])],
            ([skia.Color(24, 24, 20, 255), skia.Color(24, 24, 20, 0)] if anchor == "top"
             else [skia.Color(16, 16, 13, 0), skia.Color(16, 16, 13, 255)]), [0, 1])
        c.drawRect(skia.Rect.MakeXYWH(*box), skia.Paint(Shader=p))

    # the running total, bottom right, ticking with the scroll
    total = min(n, int(t * 7) + 1)
    text(c, f"{total:02d}", W - M, H - 250, "serif", 120, OLIVE_L, align="right")
    text(c, "OF 24 IN VIEW", W - M, H - 208, "caps", 26, (150, 150, 140),
         align="right", tracking=5)


# ------------------------------------------------------------ 3 · the object
def s_object(c, t, shot, t_abs):
    """The one art moment: the 3D still life of the four stacks.

    The plate is normalised to pure white and composited with MULTIPLY, so the
    paper of the render disappears into the paper of the page — no alpha channel
    to leak a rectangle, and the object keeps its real shading.
    """
    import stage
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (246, 244, 237), (228, 225, 214), 1.0)

    # the turntable never stops, and the camera creeps in the whole shot
    az = 12 + 34 * span(t, 0.0, 1.0)
    el = 15 - 5 * span(t, 0.0, 1.0)
    S = dict(az=lambda _t: az, el=lambda _t: el,
             fill=lambda _t: 0.74 + 0.05 * span(t, 0, 1),
             layout=0.0, drop=lambda _t: ease_out(span(t, 0.0, 0.9)),
             yshift=0.34, hot=lambda col, row, _t: (col == 2 and row == 3))
    plate = stage.flatten(stage.render(shot.t0 + t, S, 760, 1000))
    # fixed rect, growing only slightly: a bbox fit rescales every frame as the
    # stacks turn, which reads as the object pumping
    sc = 1.05 + 0.05 * span(t, 0.0, 1.0)
    K.place_plate(c, plate, W / 2, 940, 760 * sc, 1000 * sc)

    text(c, "THE MENU, IN METAL", M, 300, "caps", 30, INK_SOFT, tracking=7)
    rule(c, M, 330, 170, OLIVE, 0.9, span(t, 0.2, 0.8), 3)
    if t > 0.85:
        rise(c, "Eight. Four. Five. Seven.", M, 1742, "serif", 66, INK,
             span(t, 0.85, 1.3))
        text(c, "ONE PLATE IS ONE SERVICE PAGE", M, 1792, "caps", 26, INK_SOFT,
             ease_out(span(t, 1.2, 1.6)), tracking=4)
        text(c, "24", W - M, 1782, "serif", 92, OLIVE,
             ease_out(span(t, 1.35, 1.75)), align="right")


# ---------------------------------------------------------- 4 · the chapters
def s_chapters(c, t, shot, t_abs):
    """Four chapters on one page, each landing in its own quarter of the shot:
    kicker, the site's own headline in serif, and the count. The divider rules
    draw themselves, and the whole block slides up a touch the whole time."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (240, 238, 230), (229, 226, 216), 1.0)
    text(c, "FOUR WAYS IN", M, 306, "caps", 30, INK_SOFT, tracking=7)

    y0 = 400
    # which chapter owns the frame right now — it drives the marker and the accent
    live = int(min(3, max(0, (t - 0.2) / 1.05)))
    marker = ease_io(span(t, 0.2, 3.4)) * 3.0
    for i, (kick, name, cnt, l1, l2) in enumerate(CHAPTERS):
        u = span(t, 0.10 + 0.62 * i, 0.55 + 0.62 * i)
        if u <= 0:
            continue
        y = y0 + i * 372
        rule(c, M, y - 34, W - 2 * M, HAIR, 1.0, span(t, 0.06 + 0.62 * i, 0.6 + 0.62 * i))
        text(c, kick, M, y + 26, "caps", 28, OLIVE, u, tracking=6)
        text(c, name, W - M, y + 26, "caps", 26, INK_SOFT, u * 0.9, align="right", tracking=5)
        size = fit(l1, "serif", 68, W - 2 * M - 130)
        rise(c, l1, M, y + 108, "serif", size, INK, u)
        rise(c, l2, M, y + 108 + size * 1.02, "serif", size, INK, clamp(u * 1.25 - 0.15))
        near = 1.0 - min(1.0, abs(marker - i) / 1.15)      # 1 when the marker is here
        text(c, f"{cnt}", W - M, y + 150 + 10 * near, "serif", 84 + 34 * near,
             OLIVE if near > 0.35 else INK_SOFT, u, align="right")
        text(c, "SERVICES", W - M, y + 182, "caps", 24, INK_SOFT, u * 0.85,
             align="right", tracking=5)
        if near > 0.02:      # a tab under the live chapter
            c.drawRect(skia.Rect.MakeXYWH(M, y + 250, 120 * near, 4),
                       K.paint(OLIVE, 0.9 * near))


# ------------------------------------------------------------- 5 · the close
def s_close(c, t, shot, t_abs):
    """Porcelain again. Rules converge to the mark, the line lands in two halves,
    the URL underlines itself and holds. Nothing blinks."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (243, 241, 234), (231, 228, 218), 1.0)
    soft(c, W * 0.5, H * 0.38, 700, OLIVE_L, 0.13)

    # converging hairlines — the only motion, and it keeps the frame alive
    cx, cy = W / 2, 660
    for i, ang in enumerate((-90, -30, 30, 90, 150, 210)):
        u = span(t, 0.02 + 0.05 * i, 0.75 + 0.05 * i)
        r0, r1 = 470 - 120 * ease_io(u), 470
        a = math.radians(ang)
        line(c, cx + math.cos(a) * r0, cy + math.sin(a) * r0,
             cx + math.cos(a) * r1, cy + math.sin(a) * r1, HAIR, 0.9, 2)
    ring(c, cx, cy, 250, OLIVE, 3, 0.9, span(t, 0.1, 0.95))
    # a second ring that never stops turning: after everything lands, this is what
    # keeps the close from freezing
    c.drawArc(skia.Rect.MakeLTRB(cx - 286, cy - 286, cx + 286, cy + 286),
              -90 + 40 * t, 70, False, K.spaint(OLIVE, 2, 0.35))
    disc(c, cx, cy, 9, OLIVE, ease_out(span(t, 0.5, 0.9)))

    text(c, "DUABLE", cx, cy + 24, "serif", 96, INK, 1.0, align="center")
    sub = "INDEPENDENT CREATIVE TECHNOLOGY STUDIO"
    text(c, sub, cx, cy + 78, "caps", fit_tracked(sub, "caps", 26, W - 2 * M - 40, 5),
         INK_SOFT, 0.9, align="center", tracking=5)

    cs = fit("A studio with a service for that.", "serif", 88, W - 2 * M)
    rise(c, "A studio with", M, 1210, "serif", cs, INK, span(t, 0.85, 1.3))
    rise(c, "a service for that.", M, 1210 + cs * 1.04, "serif", cs, OLIVE,
         span(t, 1.05, 1.5))

    rule(c, M, H - 330, W - 2 * M, HAIR, 0.9, span(t, 1.5, 2.0))
    text(c, URL, M, H - 270, "serif", 52, INK, ease_out(span(t, 1.6, 2.0)))
    ou = ease_out(span(t, 1.8, 2.2))
    text(c, "OPEN THE MENU", W - M - 44, H - 276, "caps", 28, OLIVE, ou,
         align="right", tracking=4)
    if ou > 0:      # a drawn arrow: the caps face has no arrow glyph
        ax, ay = W - M - 20, H - 288
        line(c, ax - 15, ay + 15, ax, ay, OLIVE, ou, 3)
        line(c, ax - 13, ay + 1, ax, ay + 1, OLIVE, ou, 3)
        line(c, ax - 1, ay, ax - 1, ay + 13, OLIVE, ou, 3)
    rule(c, M, H - 240, 300, OLIVE, 0.95, span(t, 1.85, 2.35), 4)
    text(c, "TWENTY-FOUR SERVICES · FOUR CATEGORIES", W - M, H - 190, "caps", 26,
         INK_SOFT, 0.6 * ease_out(span(t, 1.9, 2.3)), align="right", tracking=4)


FILM = None


def build(film):
    global FILM
    FILM = film
    return [
        K.Shot("statement", 0.0, 3.2, dict(dx=-26, dz=0.012), s_statement),
        K.Shot("menu", 3.2, 7.6, dict(dz=0.010), s_menu),
        K.Shot("object", 7.6, 11.2, dict(dy=-24, dz=0.016), s_object),
        K.Shot("chapters", 11.2, 15.6, dict(dy=-30, dz=0.012), s_chapters),
        K.Shot("close", 15.6, 19.6, dict(dz=0.014, dy=-12), s_close),
    ]
