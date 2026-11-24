"""
scenes.py — the edit. Seven shots, six hard cuts.

THE RULE THIS FILE IS BUILT ON (learned by watching a frame strip of the first
cut, where shots 2–5 repeated identically for four seconds):
    a shot is not "an entrance, then a hold". Something must be MOVING at every
    single frame — either the camera is travelling, or a column is scrolling, or
    a number is counting, or a rule is drawing. If a frame could be swapped with
    the frame one second later, the shot is a slide and belongs in a deck.

So every scene below has three layers:
    1. a ground that drifts at its own speed (parallax; slower than the camera)
    2. subject matter that *continuously* moves — a scroll, a count, a sweep
    3. copy that arrives in pieces, never as one block

The camera lives in film.py's Shot rig: dy/dz are real travel, not a nudge.
"""
import math

import skia

import kit as K
from kit import (W, H, M, GND, GND_2, INK, DIM, GREEN, GREEN_DEEP, PAPER,
                 paint, stroke, rule, dot, ring, slab, grad_rect, radial_glow,
                 draw_text, mask_reveal, stagger_words, draw_rule_in, span,
                 ease_out, ease_io, ease_expo, back_out, lerp, clamp,
                 fit_width, text_w, font)

CATS = [("WEB & TECHNOLOGY", 8), ("AI & AUTOMATION", 4),
        ("CREATIVE & MEDIA", 5), ("MARKETING & GROWTH", 7)]

SERVICES = ["WEBSITE DESIGN & PLANNING", "WEBSITE DEVELOPMENT", "WEB APPS & DASHBOARDS",
            "E-COMMERCE WEBSITES", "WEBSITE FIXES & MAINTENANCE",
            "WEBSITE AUDITS & OPTIMIZATION", "INTEGRATIONS & APIS",
            "MOBILE APP DEVELOPMENT",
            "WORKFLOW AUTOMATION", "AI-ASSISTED WORKFLOWS", "CUSTOM AI AGENTS",
            "AI PRODUCT FEATURES",
            "VIDEO EDITING", "IMAGE EDITING", "GRAPHIC DESIGN",
            "BRAND & CAMPAIGN VISUALS", "GENERATED CONTENT",
            "SOCIAL MEDIA MANAGEMENT", "CONTENT & COPYWRITING", "CAMPAIGN PLANNING",
            "PAID ADVERTISING", "POSITIONING & MESSAGING", "AUDIENCE RESEARCH",
            "GROWTH STRATEGY"]

STEPS = ["TALK IT THROUGH", "SET THE SCOPE", "MAKE THE WORK", "HAND IT OVER"]
URL = "DUABLEINDUSTRIES.VERCEL.APP"
STATUS = {"number": "01 · THE MENU", "menu": "02 · FOUR CATEGORIES",
          "services": "03 · TWENTY-FOUR SERVICES", "process": "04 · FOUR STEPS",
          "count": "05 · THE SPLIT", "honest": "06 · WHAT IT REFUSES",
          "end": "07 · THE STUDIO"}


# --------------------------------------------------------------- furniture
def hud(c, t, film, shot, alpha=1.0):
    idx = film.shots.index(shot)
    total = len(film.shots)
    status = STATUS.get(shot.name, "")
    draw_text(c, "DUABLE", M, 132, "label", 32, DIM, alpha, tracking=5)
    draw_text(c, f"{idx + 1:02d} / {total:02d}", W - M, 132, "label", 32, DIM, alpha,
              align="right", tracking=5)
    rule(c, M, 160, W - M, 160, DIM, 2, 0.35 * alpha)
    p = clamp((t - shot.t0) / max(1e-6, shot.t1 - shot.t0))
    c.drawRect(skia.Rect.MakeXYWH(M, 158, (W - 2 * M) * p, 4), paint(GREEN, 0.9 * alpha))
    draw_text(c, status, M, H - 96, "label", 30, DIM, alpha, tracking=4)
    draw_text(c, f"{idx + 1:02d}", W - M, H - 96, "label", 30, DIM, alpha * 0.7,
              align="right", tracking=3)
    rule(c, M, H - 132, W - M, H - 132, DIM, 2, 0.30 * alpha)


def ground(c, t, speed=1.0, step=110, a=0.05, pool=None):
    """The drifting modular ground. `speed` is its parallax rate — slower than the
    camera, so the frame has depth instead of one flat plane."""
    K.grad_rect(c, skia.Rect.MakeXYWH(0, -200, W, H + 400), GND_2, GND, 1.0)
    K.grid(c, 0, -200, W, H + 400, step, INK, a, phase=t * speed * 0.16)
    if pool:
        px, py, rad, amt = pool
        radial_glow(c, px, py + t * 14, rad, GREEN_DEEP, amt)


# ------------------------------------------------------ 1 · the number lands
def s_number(c, t, shot, t_abs):
    """0–3.2 s. A count-up that decelerates into 24 while the counts 8/4/5/7
    arrive underneath it and a rule sweeps. The camera pushes the whole time."""
    ground(c, t, 1.0, 108, 0.055, (W * 0.28, H * 0.30, 620, 0.16))

    n = 24 * ease_expo(span(t, 0.02, 1.45))
    pump = 1.0 + 0.14 * (1 - ease_out(span(t, 0.0, 0.5)))
    draw_text(c, f"{int(round(n)):02d}", M - 12, 950, "display", 470 * pump, GREEN)
    draw_rule_in(c, M, 1024, W - 2 * M, GREEN, span(t, 1.15, 1.85), 10)

    stagger_words(c, "SERVICES", M, 1200, "display",
                  fit_width("SERVICES", "display", 168, W - 2 * M), INK,
                  span(t, 0.95, 1.75), "left")
    if t > 1.35:
        draw_text(c, "ONE STUDIO. A GENEROUS MENU.", M, 1310, "label", 40, DIM,
                  ease_out(span(t, 1.35, 1.7)), tracking=4)
    if t > 1.6:
        draw_rule_in(c, M, 1344, 420, GREEN, span(t, 1.6, 2.25), 4)

    # the split arrives as four counters, each rising on its own beat
    for i, (name, count) in enumerate(CATS):
        u = span(t, 1.25 + 0.20 * i, 1.75 + 0.20 * i)
        if u <= 0:
            continue
        e = ease_expo(u)
        y = 214 + i * 168 + (1 - e) * 54
        draw_text(c, f"{count:02d}", W - M, y, "display", 92,
                  GREEN if i % 2 == 0 else INK, e, align="right")
        draw_text(c, name, W - M, y + 44 + (1 - e) * 48, "label", 28, DIM, e,
                  align="right", tracking=2)


# --------------------------------------------------- 2 · the menu, by category
def s_menu(c, t, shot, t_abs):
    """3.2–6.8 s. The four categories travel UP through a fixed crop, one whole
    row per beat, so the shot is a scroll rather than four entrances. The numbers
    stay locked to their rows and slide sideways a little as they pass."""
    ground(c, t, 0.7, 96, 0.045, (W * 0.7, H * 0.26, 560, 0.15))

    travel = ease_io(span(t, 0.35, 3.1)) * 520          # continuous, never stops
    for i, (name, count) in enumerate(CATS):
        y = 470 + i * 372 - travel
        if y < 60 or y > H - 120:
            continue
        # rows passing the middle are the "active" one: scale + colour
        focus = 1.0 - min(1.0, abs(y - 780) / 700)
        nx = M + 26 * (1 - focus)          # drifts INWARD as it passes, never out
        big = 132 + 52 * focus
        draw_text(c, f"{count:02d}", nx, y + 60, "display", big,
                  GREEN if focus > 0.45 else DIM, 0.35 + 0.65 * focus)
        words = name.split(" & ")
        draw_text(c, words[0], W - M, y, "label", 54, INK if focus > 0.3 else DIM,
                  0.35 + 0.65 * focus, align="right", tracking=1)
        draw_text(c, "& " + words[1], W - M, y + 68, "label", 54,
                  INK if focus > 0.3 else DIM, 0.35 + 0.65 * focus, align="right", tracking=1)
        rule(c, M, y + 138, W - M, y + 138, DIM, 1, 0.10 + 0.28 * focus)

    # a fixed reading line the rows pass through, plus the running sum
    rule(c, M, 860, W - M, 860, GREEN, 3, 0.5)
    if t > 2.15:
        u = span(t, 2.15, 2.7)
        draw_text(c, "TWENTY-FOUR IN ALL", M, H - 300, "label", 44, INK,
                  ease_out(u), tracking=3)
        draw_text(c, "8 · 4 · 5 · 7", W - M, H - 302, "label", 44, GREEN,
                  ease_out(span(t, 2.35, 2.9)), align="right", tracking=3)


# ---------------------------------------------------------- 3 · the services
def s_services(c, t, shot, t_abs):
    """6.8–10.4 s. The actual twenty-four, running past like credits — accelerating
    the whole shot, with the headline swapping mid-shot so the frame never settles."""
    ground(c, t, 1.4, 132, 0.035, (W * 0.72, H * 0.20, 560, 0.13))

    speed = 250 + 420 * ease_io(span(t, 0.0, 1.0))      # it speeds up
    scroll = t * speed
    for i in range(len(SERVICES) + 14):
        y = 240 + i * 118 - scroll
        if y < 170 or y > H - 640:
            continue
        a = 1.0 if 240 < y < H - 700 else 0.45
        draw_text(c, f"{i % 24 + 1:02d}", M, y, "label", 30, GREEN, 0.8 * a)
        draw_text(c, SERVICES[i % 24], M + 78, y, "label", 44, INK, a, tracking=2)
        rule(c, M, y + 30, W - M, y + 30, DIM, 1, 0.16 * a)

    sh = skia.GradientShader.MakeLinear(
        [skia.Point(0, H - 780), skia.Point(0, H - 250)],
        [skia.Color(7, 9, 8, 0), skia.Color(7, 9, 8, 248), skia.Color(7, 9, 8, 252)],
        [0.0, 0.5, 1.0])
    c.drawRect(skia.Rect.MakeXYWH(0, H - 780, W, 780), skia.Paint(Shader=sh))

    # headline one, then headline two replaces it on a cut of its own
    if t < 1.55:
        K.save_clip(c, M - 8, H - 620, W, 190, ease_expo(span(t, 0.02, 0.5)))
        draw_text(c, "EVERY PART OF IT.", M, H - 470, "display",
                  fit_width("EVERY PART OF IT.", "display", 104, W - 2 * M), INK)
        K.restore(c)
    else:
        K.save_clip(c, M - 8, H - 620, W, 190, ease_expo(span(t, 1.55, 2.0)))
        draw_text(c, "ON ITS OWN PAGE.", M, H - 470, "display",
                  fit_width("ON ITS OWN PAGE.", "display", 104, W - 2 * M), GREEN)
        K.restore(c)

    if t > 0.6:
        draw_text(c, "WEB · AI · MEDIA · GROWTH", M, H - 380, "label", 36, GREEN,
                  ease_out(span(t, 0.6, 1.0)), tracking=5)
    if t > 1.05:
        draw_text(c, "CHOOSE THE EXACT THING YOU NEED", M, H - 314, "ui", 32, DIM,
                  ease_out(span(t, 1.05, 1.4)), tracking=2)


# --------------------------------------------------------- 4 · four steps
def s_process(c, t, shot, t_abs):
    """10.4–13.6 s. The camera travels DOWN the track: the steps are fixed to the
    track and the track scrolls, so the shot is a journey with one idea."""
    ground(c, t, 0.9, 120, 0.04, (W * 0.4, H * 0.5, 620, 0.12))

    x = M + 40
    travel = ease_io(span(t, 0.15, 3.0)) * 260
    y0, gap = 420 - travel, 300
    draw_rule_in(c, x, y0 - 120, gap * 3 + 380, DIM, 1.0, 3, vertical=True)
    ry = y0 - 120 + (gap * 3 + 380) * clamp((t - 0.1) / 3.2)
    dot(c, x + 1, ry, 10, GREEN, 1.0)

    for i, s in enumerate(STEPS):
        y = y0 + gap * i
        if y < 120 or y > H - 140:
            continue
        u = span(t, 0.18 + 0.28 * i, 0.62 + 0.28 * i)
        e = ease_expo(u)
        lit = 1.0 if ry > y - 20 else 0.45
        dot(c, x + 1, y - 16, 13, GREEN if lit > 0.9 else INK, lit)
        draw_text(c, f"0{i+1}", x + 54, y, "display", 52, GREEN, 0.45 + 0.55 * lit)
        draw_text(c, s, W - M - (1 - e) * 30, y, "label", 52, INK, 0.35 + 0.65 * e,
                  align="right", tracking=2)
        if i < len(STEPS) - 1:
            draw_rule_in(c, x + 54, y + 44, 520, DIM, span(t, 0.4 + 0.28 * i, 1.0 + 0.28 * i), 1)

    if t > 1.9:
        draw_text(c, "AGREE THE DELIVERABLES BEFORE WORK BEGINS", M, H - 240, "ui", 31,
                  DIM, ease_out(span(t, 1.9, 2.3)), tracking=2)


# ------------------------------------------------------------ 5 · the split
def s_count(c, t, shot, t_abs):
    """13.6–16.4 s. Four tall columns that GROW the whole shot, each with its
    count running up beside it. One idea: a chart drawing itself."""
    ground(c, t, 1.1, 112, 0.045)
    draw_text(c, "BY CATEGORY", M, 330, "label", 34, DIM, tracking=6)

    base = 1480
    for i, (name, count) in enumerate(CATS):
        u = span(t, 0.10 + 0.17 * i, 1.35 + 0.17 * i)     # grows for most of the shot
        e = ease_io(u)
        bw = 150
        x = M + 26 + i * 214
        h = 150 + count * 96 * e
        slab(c, x, base - h, bw, h, GREEN if i % 2 == 0 else (54, 92, 58), None, 0.95)
        # the count ticks up with its column
        draw_text(c, f"{int(round(count * e)):02d}", x + bw / 2, base - h - 34,
                  "display", 84, INK, 0.5 + 0.5 * e, align="center")
        draw_text(c, name.split(" & ")[0], x + bw / 2, base + 56, "label", 30,
                  DIM, 0.6, align="center", tracking=1)
        draw_text(c, name.split(" & ")[1] if " & " in name else "", x + bw / 2,
                  base + 94, "label", 30, DIM, 0.6, align="center", tracking=1)

    rule(c, M, base + 8, W - M, base + 8, DIM, 2, 0.5)
    if t > 1.3:
        draw_text(c, "THE MENU'S OWN COUNTS — 8 · 4 · 5 · 7", M, H - 250,
                  "label", 32, DIM, ease_out(span(t, 1.3, 1.7)), tracking=3)


# ------------------------------------------------------------ 6 · honest
def s_honest(c, t, shot, t_abs):
    """16.4–19.4 s. The warm beat. Paper, one sentence, and a strike that draws
    across the word it cancels. The camera pushes slowly the whole time."""
    K.grad_rect(c, skia.Rect.MakeXYWH(0, 0, W, H), (30, 27, 22), (16, 15, 12), 1.0)
    radial_glow(c, W * 0.5 + math.sin(t * 0.8) * 40, H * 0.30, 700, (124, 98, 58), 0.17)
    c.drawRect(skia.Rect.MakeXYWH(M - 16, M + 96, W - 2 * M + 32, H - 2 * M - 150),
               stroke(PAPER, 2, 0.16))

    mask_reveal(c, "NO MAGIC", M + 20, 700, "display",
                fit_width("NO MAGIC", "display", 132, W - 2 * M - 40), PAPER,
                span(t, 0.05, 0.55), "left")
    w2 = mask_reveal(c, "NUMBERS.", M + 20, 858, "display",
                     fit_width("NUMBERS.", "display", 132, W - 2 * M - 40), PAPER,
                     span(t, 0.35, 0.85), "left")
    su = span(t, 0.85, 1.35)
    if su > 0:
        c.drawRect(skia.Rect.MakeXYWH(M + 22, 800, (w2 - 6) * ease_io(su), 7), paint(GREEN))
    if t > 1.2:
        draw_text(c, "PRACTICAL GROWTH STRATEGY —", M + 20, 1000, "label", 40, PAPER,
                  ease_out(span(t, 1.2, 1.55)), tracking=3)
    if t > 1.45:
        stagger_words(c, "WITHOUT PROMISING THEM.", M + 20, 1070, "label", 40, GREEN,
                      span(t, 1.45, 2.0), "left", per=0.16)
    # the proof, drawn as a small diagram: a note going into a box that closes
    if t > 1.75:
        u = span(t, 1.75, 2.35)
        e = ease_expo(u)
        bx, by, bw2, bh = M + 20, H - 620, 380, 220
        c.drawRect(skia.Rect.MakeXYWH(bx, by, bw2, bh), stroke(PAPER, 2, 0.28 * e))
        for ln in range(3):                       # the note's rules, drawing in
            draw_rule_in(c, bx + 26, by + 44 + ln * 46, (bw2 - 52) * (1 - 0.3 * ln),
                         PAPER, span(t, 1.9 + 0.1 * ln, 2.4 + 0.1 * ln), 3)
        # the "never leaves" arrow: a line out that stops dead at the frame
        draw_rule_in(c, bx + bw2 + 40, by + bh / 2, 150, GREEN, span(t, 2.15, 2.7), 3)
        c.drawRect(skia.Rect.MakeXYWH(bx + bw2 + 186, by + bh / 2 - 16, 6, 32),
                   paint(GREEN, e))
        draw_text(c, "NOTHING SENT", bx + bw2 + 36, by + bh / 2 + 56, "label", 26,
                  DIM, ease_out(span(t, 2.3, 2.7)), tracking=2)
    if t > 2.0:
        draw_text(c, "YOUR PROJECT NOTE STAYS IN THIS BROWSER", M + 20, H - 330, "label",
                  34, PAPER, ease_out(span(t, 2.0, 2.35)) * 0.95, tracking=2)


# -------------------------------------------------------------- 7 · the end
def s_end(c, t, shot, t_abs):
    """19.4–22.4 s. Rings sweep in, a satellite keeps orbiting, the camera pushes
    the whole way, and the URL underlines itself. Never a still."""
    ground(c, t, 0.6, 128, 0.035, None)
    radial_glow(c, W * 0.5, H * 0.30, 780, GREEN_DEEP, 0.18 * ease_out(span(t, 0, 1.0)))

    cy = H * 0.315
    ring(c, W / 2, cy, 236, GREEN, 16, 0.92, start=-90,
         sweep=360 * ease_io(span(t, 0.0, 0.8)))
    ring(c, W / 2, cy, 300, GREEN, 2, 0.30, start=-90,
         sweep=360 * ease_io(span(t, 0.2, 1.15)))
    ring(c, W / 2, cy, 165, INK, 2, 0.22, start=0, sweep=360 * ease_io(span(t, 0.4, 1.4)))
    ang = math.radians(-90 + 330 * ease_io(span(t, 0.15, 2.6)))
    dot(c, W / 2 + math.cos(ang) * 236, cy + math.sin(ang) * 236, 15, GREEN, 1.0)

    mask_reveal(c, "A STUDIO WITH", W / 2, 1210, "display",
                fit_width("A STUDIO WITH", "display", 92, W - 2 * M), INK,
                span(t, 0.30, 0.9), "center")
    mask_reveal(c, "A SERVICE FOR THAT.", W / 2, 1322, "display",
                fit_width("A SERVICE FOR THAT.", "display", 92, W - 2 * M), GREEN,
                span(t, 0.50, 1.1), "center")
    if t > 0.85:
        draw_text(c, URL, W / 2, 1452, "label", 42, INK,
                  ease_out(span(t, 0.85, 1.25)), align="center", tracking=6)
        draw_rule_in(c, W / 2 - 216, 1496, 432, GREEN, span(t, 1.0, 1.6), 3)
        draw_text(c, "INDEPENDENT CREATIVE TECHNOLOGY STUDIO", W / 2, 1560, "label",
                  26, DIM, ease_out(span(t, 1.5, 1.9)), align="center", tracking=3)


FILM = None


def build(film):
    global FILM
    FILM = film
    return [
        K.Shot("number", 0.0, 3.2, dict(z=1.0, dz=0.042, dy=-70), s_number),
        K.Shot("menu", 3.2, 6.8, dict(z=1.0, dz=0.040, dy=-90), s_menu),
        K.Shot("services", 6.8, 10.4, dict(z=1.0, dz=0.038, dx=30), s_services),
        K.Shot("process", 10.4, 13.6, dict(z=1.0, dz=0.045, dy=-40), s_process),
        K.Shot("count", 13.6, 16.4, dict(z=1.0, dz=0.040), s_count),
        K.Shot("honest", 16.4, 19.4, dict(z=1.0, dz=0.040, dy=-20), s_honest),
        K.Shot("end", 19.4, 22.4, dict(z=1.0, dz=0.045), s_end),
    ]
