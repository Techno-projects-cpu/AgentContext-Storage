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
    """The running head. It is the ONLY thing that never changes, which is what
    makes the seven beats read as one film rather than seven frames."""
    idx = film.shots.index(shot)
    text(c, "DUABLE", M, 150, "caps", 30, INK, 0.72, tracking=7)
    text(c, f"{idx + 1:02d} / {len(film.shots):02d}", W - M, 150, "caps", 30,
         INK, 0.50, align="right", tracking=7)
    rule(c, M, 178, W - 2 * M, HAIR, 0.9)
    p = span(t, shot.t0, shot.t1)
    c.drawRect(skia.Rect.MakeXYWH(M, 176, (W - 2 * M) * p, 3), K.paint(OLIVE, 0.95))


def beat(c, s, t, a=0.0, b=0.6, size=30, rgb=None):
    """The story's own running head, top-left: which beat of the story this is."""
    text(c, s, M, 300, "caps", size, rgb or INK_SOFT, ease_out(span(t, a, b)), tracking=7)


# ------------------------------------------------------- 1 · a sentence (cold open)
def s_sentence(c, t, shot, t_abs):
    """COLD OPEN. A full stop, alone, then the sentence it belongs to.

    The first frame is also the thumbnail, so the sentence is already arriving at
    t=0 — a page with one dot on it reads as a broken frame, not as restraint.
    Nothing is still: the sentence lifts and recedes for the whole beat."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (243, 241, 234), (231, 228, 218), 1.0)
    soft(c, W * 0.5, H * 0.44, 720, OLIVE_L, 0.09)

    cy = H * 0.44
    # the full stop first, and it hands over as the sentence arrives
    dot = ease_out(span(t, 0.0, 0.30)) * (1.0 - ease_io(span(t, 0.30, 0.55)))
    if dot > 0.01:
        disc(c, W / 2, cy, 13 * dot, OLIVE, dot)

    # Frame 0 is the thumbnail, so the sentence must be ON it, not arriving after
    # it: at t=0 exactly, an entrance curve that starts at 0.02 gives alpha 0.
    n = fit("a thing made.", "serif", 140, W - 2 * M)
    lift = -16 * ease_io(span(t, 1.15, 1.9))
    fade = 1.0 - 0.30 * ease_io(span(t, 1.15, 1.85))
    rise(c, "I need", M, cy - n * 0.72 + lift, "serif", n, INK,
         (0.35 + 0.65 * ease_out(span(t, 0.0, 0.45))) * fade)
    rise(c, "a thing made.", M, cy + n * 0.34 + lift, "serif", n, INK,
         (0.22 + 0.78 * ease_out(span(t, 0.10, 0.60))) * fade)

    beat(c, "ONE · A SENTENCE", t, 0.0, 0.30)
    rule(c, M, H - 300, W - 2 * M, HAIR, 0.9, span(t, 1.5, 2.05))
    text(c, "DUABLE INDUSTRIES", M, H - 250, "caps", 28, INK_SOFT,
         ease_out(span(t, 1.6, 2.05)), tracking=5)
    text(c, "duableindustries.vercel.app", W - M, H - 250, "ui", 28, INK,
         ease_out(span(t, 1.7, 2.15)), align="right")


# ------------------------------------------------ 2 · that is what a service is
def s_service(c, t, shot, t_abs):
    """THE ANSWER. A request arrives, a service answers it, a line connects them.

    This is the film's whole argument in one frame: it is not a list of offerings,
    it is the shape of a conversation."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (242, 240, 232), (231, 228, 218), 1.0)
    beat(c, "TWO · A SERVICE", t, 0.1, 0.7)

    # --- the request, above the line
    text(c, "YOU SAY", M, 470, "caps", 26, INK_SOFT, ease_out(span(t, 0.15, 0.5)), tracking=6)
    q = "\u201cI need a thing made.\u201d"
    qs = fit(q, "serif", 84, W - 2 * M)
    rise(c, q, M, 600, "serif", qs, INK, span(t, 0.25, 0.9))

    # --- the line drawn between the two, left to right
    ly = 760
    lu = ease_io(span(t, 0.7, 1.7))
    rule(c, M, ly, W - 2 * M, HAIR, 0.95, lu)
    if lu > 0.02:      # the arrowhead lands last
        ax = M + (W - 2 * M) * lu
        line(c, ax - 16, ly - 12, ax, ly, OLIVE, 1.0, 3)
        line(c, ax - 16, ly + 12, ax, ly, OLIVE, 1.0, 3)

    # --- 24 dots on that line: one per service. The 20th lights.
    for i in range(24):
        x = M + (W - 2 * M) * (i + 0.5) / 24
        u = span(t, 0.9 + i * 0.028, 1.2 + i * 0.028)
        if u <= 0:
            continue
        lit = 1.0 if i == 19 else 0.0
        disc(c, x, ly, 4 + 3 * u * lit, OLIVE if i == 19 else INK, 0.35 + 0.65 * u)

    # --- the answer, below the line
    text(c, "WE HAVE", M, 880, "caps", 26, INK_SOFT, ease_out(span(t, 1.15, 1.5)), tracking=6)
    a1, a2 = "Paid advertising.", "One of twenty-four."
    asz = fit(a2, "serif", 88, W - 2 * M)
    rise(c, a1, M, 1010, "serif", asz, INK, span(t, 1.25, 1.85))
    rise(c, a2, M, 1010 + asz * 1.02, "serif", asz, OLIVE, span(t, 1.5, 2.1))

    # --- the punchline, small and late
    rule(c, M, H - 300, W - 2 * M, HAIR, 0.9, span(t, 2.0, 2.5))
    l = "THE MENU IS REALLY A LIST OF SENTENCES PEOPLE SAY."
    text(c, l, M, H - 250, "caps", fit_tracked(l, "caps", 27, W - 2 * M, 4),
         INK_SOFT, ease_out(span(t, 2.05, 2.5)), tracking=4)


# ------------------------------------------------- 3 · twenty-four pages, in metal
def _stacks_spec(u):
    return dict(az=lambda _t: 20 + 18 * u, el=lambda _t: 14 - 2 * u,
                fill=lambda _t: 0.92, layout=0.0,
                drop=lambda _t: span(u, 0.05, 0.95),
                yshift=0.02, hot=lambda col, row, _t: False)


# the crop window is solved from the extremes of each shot, once per run
_WIN = {}


def _win(name, shot, mk, size):
    """Crop window for a 3D plate, solved from the extremes of the shot.

    `mk(u)` returns either a finished image (hero plates) or a scene spec to
    render at `size`.
    """
    if name not in _WIN:
        import stage
        frames = []
        for u in (0.0, 0.5, 1.0):
            r = mk(u)
            if isinstance(r, np.ndarray) or hasattr(r, "convert"):
                frames.append(np.asarray(r))
            else:
                frames.append(stage.flatten(stage.render(0.0, r, *size)))
        _WIN[name] = stage.content_window(frames)
    return _WIN[name]


def s_stacks(c, t, shot, t_abs):
    """THE CATALOGUE, PHYSICAL. Four stacks of plates = four categories.

    Plates rise into their slots on a stagger, so the object is still being built
    when we arrive at it. Type stays at the top and bottom; the object owns the
    middle."""
    import stage
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (246, 244, 237), (228, 225, 214), 1.0)
    beat(c, "THREE · THE CATALOGUE", t, 0.1, 0.7)

    win = _win("stacks", shot, lambda u: _stacks_spec(max(u, 1.0)), (820, 760))
    S = _stacks_spec(span(t, 0.0, 1.0))
    plate = stage.flatten(stage.render(shot.t0 + t, S, 820, 760))
    sc = 0.94 + 0.06 * span(t, 0.0, 1.0)
    stage.place_window(c, plate, win, W / 2, 850, W - 120, 700, scale=sc)

    rise(c, "Twenty-four pages,", M, 1560, "serif", 66, INK, span(t, 0.5, 1.0))
    rise(c, "in four stacks.", M, 1560 + 68, "serif", 66, OLIVE, span(t, 0.7, 1.2))
    text(c, "EIGHT · FOUR · FIVE · SEVEN", M, 1732, "caps", 28, INK_SOFT,
         ease_out(span(t, 1.0, 1.5)), tracking=5)


# ------------------------------------------------------- 4 · one of them is yours
def _lift_spec(u, eye=None, ctr=None):
    S = dict(az=lambda _t: 24, el=lambda _t: 14, fill=lambda _t: 0.90,
             layout=0.0, drop=lambda _t: 1.0, yshift=0.06,
             lift=(2, 3), lift_u=lambda _t: u,
             lift_to=(0.0, 2.95 + 1.85 * u, 0.85 * u),
             # yaw, not pitch: turning it about Y swings its broad faces into view,
             # while pitching it about X just rolls a wafer over and it vanishes.
             lift_yaw=1.35,
             hot=lambda col, row, _t: (col == 2 and row == 3))
    if eye is not None:
        S.update(eye=eye, ctr=ctr)
    return S


def s_lift(c, t, shot, t_abs):
    """THE TURN. The camera holds completely still and one plate rises out of its
    stack and hangs there. The only shot in the film where the geometry changes
    meaning: beat three was a catalogue of twenty-four, this is a catalogue of one."""
    import stage
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (246, 244, 238), (226, 223, 211), 1.0)
    beat(c, "FOUR · ONE OF THEM IS YOURS", t, 0.05, 0.6)

    base = _lift_spec(0.0)
    parts = stage.build(0.0, base)
    eye, ctr = stage.frame_camera(parts, 24, 14, 0.90, fov=30, W=820, H=760,
                                  yshift=0.06)
    win = _win("lift", shot, lambda u: _lift_spec(u, eye, ctr), (820, 760))

    u = ease_io(span(t, 0.20, 1.75))
    plate = stage.flatten(stage.render(shot.t0 + t, _lift_spec(u, eye, ctr), 820, 760))
    stage.place_window(c, plate, win, W / 2, 830, W - 100, 690,
                       scale=1.0 - 0.04 * u)

    if t > 1.3:
        rise(c, "One of them", M, 1500, "serif", 74, INK, span(t, 1.3, 1.8))
        rise(c, "is yours.", M, 1500 + 76, "serif", 74, OLIVE, span(t, 1.5, 2.0))
        text(c, "A PLATE LEAVES THE STACK", M, 1672, "caps", 27, INK_SOFT,
             ease_out(span(t, 1.65, 2.15)), tracking=5)
        text(c, "24", W - M, 1644, "serif", 92, OLIVE,
             ease_out(span(t, 1.75, 2.25)), align="right")


# ------------------------------------------------- 5 · the same sentence, then
def s_map(c, t, shot, t_abs):
    """THE ANSWER, UNPACKED. They said it; Duable named it.

    Two lines close the distance between what the client says and the menu entry
    that answers it. The whole shot is that one gesture, repeated four times, so
    it reads as a method rather than a slide."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (240, 238, 230), (228, 225, 215), 1.0)
    beat(c, "FIVE · WHAT THEY ASKED FOR", t, 0.1, 0.7)

    # the chapter the answer sits in, stated once
    text(c, "03 / EDIT", M, 430, "caps", 28, OLIVE, ease_out(span(t, 0.15, 0.55)), tracking=6)
    text(c, "CREATIVE & MEDIA", W - M, 430, "caps", 26, INK_SOFT,
         ease_out(span(t, 0.15, 0.55)), align="right", tracking=5)

    rows = [("THEY SAID", "\u201cMake the story and visuals feel connected.\u201d"),
            ("DUABLE SAYS", "Video editing. Image editing. Graphic design.")]
    y = 560
    for i, (tag, line) in enumerate(rows):
        u = span(t, 0.30 + 0.36 * i, 0.85 + 0.36 * i)
        text(c, tag, M, y, "caps", 26, INK_SOFT, ease_out(u), tracking=6)
        sz = fit(line, "serif", 60, W - 2 * M)
        rise(c, line, M, y + 92, "serif", sz,
             INK if i == 0 else OLIVE, span(t, 0.36 + 0.36 * i, 0.92 + 0.36 * i))
        # a rule that draws toward the right: the answer travelling away from the ask
        rule(c, M, y + 132, W - 2 * M, HAIR, 0.9, span(t, 0.5 + 0.36 * i, 1.1 + 0.36 * i))
        y += 400

    # the site's own headline, as the closing beat of the beat
    if t > 1.5:
        rule(c, M, H - 320, W - 2 * M, HAIR, 0.9, span(t, 1.45, 1.9))
        text(c, "MAKE THE STORY AND VISUALS FEEL CONNECTED.", M, H - 276, "caps",
             fit_tracked("MAKE THE STORY AND VISUALS FEEL CONNECTED.", "caps", 27,
                         W - 2 * M, 4), INK_SOFT, ease_out(span(t, 1.5, 1.95)), tracking=4)
        text(c, "/services/creative-media/", M, H - 226,
             "ui", 28, INK, ease_out(span(t, 1.6, 2.05)))


# ------------------------------------------------- 6 · four ways in, one method
def s_four(c, t, shot, t_abs):
    """FOUR CHAPTERS, AS ONE MOVEMENT. The camera walks the list; each chapter
    lands with its own count, and the marker keeps moving so it never freezes."""
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (240, 238, 230), (229, 226, 216), 1.0)
    beat(c, "SIX · FOUR WAYS IN", t, 0.05, 0.6)

    y0 = 400
    marker = ease_io(span(t, 0.2, 3.4)) * 3.0
    for i, (kick, name, cnt, l1, l2) in enumerate(CHAPTERS):
        u = span(t, 0.10 + 0.42 * i, 0.50 + 0.42 * i)
        if u <= 0:
            continue
        y = y0 + i * 372
        rule(c, M, y - 30, W - 2 * M, HAIR, 1.0, span(t, 0.06 + 0.42 * i, 0.5 + 0.42 * i))
        text(c, kick, M, y + 26, "caps", 28, OLIVE, u, tracking=6)
        text(c, name, W - M, y + 26, "caps", 26, INK_SOFT, u * 0.9, align="right", tracking=5)
        size = fit(l1, "serif", 66, W - 2 * M - 130)
        rise(c, l1, M, y + 104, "serif", size, INK, u)
        rise(c, l2, M, y + 104 + size * 0.99, "serif", size, INK, clamp(u * 1.25 - 0.15))
        near = 1.0 - min(1.0, abs(marker - i) / 1.15)
        text(c, f"{cnt}", W - M, y + 146 + 8 * near, "serif", 80 + 30 * near,
             OLIVE if near > 0.35 else INK_SOFT, u, align="right")
        text(c, "SERVICES", W - M, y + 176, "caps", 24, INK_SOFT, u * 0.85,
             align="right", tracking=5)
        if near > 0.02:
            c.drawRect(skia.Rect.MakeXYWH(M, y + 240, 110 * near, 4),
                       K.paint(OLIVE, 0.9 * near))


# --------------------------------------------------- 7 · the answer, incoming
def _answer_spec(u):
    """The stacks, finished and settled, with the chosen plate hovering in front.

    The payoff is the bookend: the cold open ended on a sentence, this ends on the
    studio that finishes it — and it is the SAME plate that left the stack in
    beat four, now come to rest over the twenty-three it left behind."""
    return dict(az=lambda _t: 26 - 12 * u, el=lambda _t: 11 + 1.5 * u,
                fill=lambda _t: 0.90, layout=0.0, drop=lambda _t: 1.0,
                yshift=0.0, hot=lambda col, row, _t: (col == 2 and row == 3))


def s_answer(c, t, shot, t_abs):
    import stage
    vgrad(c, skia.Rect.MakeXYWH(0, 0, W, H), (244, 242, 235), (229, 226, 214), 1.0)
    soft(c, W * 0.5, H * 0.34, 780, OLIVE_L, 0.10)
    beat(c, "SEVEN · THE ANSWER", t, 0.05, 0.6)

    win = _win("answer", shot, _answer_spec, (820, 700))
    plate = stage.flatten(stage.render(shot.t0 + t,
                                       _answer_spec(span(t, 0.0, 1.0)), 820, 700))
    stage.place_window(c, plate, win, W / 2, 640, W - 150, 470, scale=1.0)

    # the full stop from the cold open comes back, and settles under the object
    dot = ease_out(span(t, 0.3, 0.9))
    if dot > 0.01:
        disc(c, W / 2, 930, 11 * dot, OLIVE, dot)

    text(c, "DUABLE", W / 2, 1020, "serif", 88, INK, 1.0, align="center")
    sub = "INDEPENDENT CREATIVE TECHNOLOGY STUDIO"
    text(c, sub, W / 2, 1070, "caps", fit_tracked(sub, "caps", 25, W - 2 * M - 60, 5),
         INK_SOFT, ease_out(span(t, 0.45, 0.95)), align="center", tracking=5)

    cs = fit("A studio with a service for that.", "serif", 80, W - 2 * M)
    rise(c, "A studio with", M, 1250, "serif", cs, INK, span(t, 0.9, 1.35))
    rise(c, "a service for that.", M, 1250 + cs * 1.02, "serif", cs, OLIVE,
         span(t, 1.1, 1.55))

    rule(c, M, H - 340, W - 2 * M, HAIR, 0.9, span(t, 1.5, 2.0))
    text(c, "duableindustries.vercel.app", M, H - 282, "serif", 50, INK,
         ease_out(span(t, 1.6, 2.0)))
    ou = ease_out(span(t, 1.8, 2.2))
    text(c, "OPEN THE MENU", W - M - 44, H - 288, "caps", 28, OLIVE, ou,
         align="right", tracking=4)
    if ou > 0:      # drawn arrow: the caps face has no arrow glyph
        ax, ay = W - M - 20, H - 300
        line(c, ax - 15, ay + 15, ax, ay, OLIVE, ou, 3)
        line(c, ax - 13, ay + 1, ax, ay + 1, OLIVE, ou, 3)
        line(c, ax - 1, ay, ax - 1, ay + 13, OLIVE, ou, 3)
    rule(c, M, H - 250, 280, OLIVE, 0.95, span(t, 1.85, 2.3), 4)
    text(c, "TWENTY-FOUR SERVICES · FOUR CATEGORIES", W - M, H - 206, "caps", 26,
         INK_SOFT, 0.65 * ease_out(span(t, 1.9, 2.3)), align="right", tracking=4)


FILM = None


def build(film):
    global FILM
    FILM = film
    # Seven beats. The first and last are the same sentence, one cold, one warm.
    return [
        K.Shot("sentence", 0.0, 2.8, dict(dz=0.008), s_sentence),
        K.Shot("service", 2.8, 6.6, dict(dz=0.010), s_service),
        K.Shot("stacks", 6.6, 9.9, dict(dy=-14, dz=0.012), s_stacks),
        K.Shot("lift", 9.9, 13.6, dict(dz=0.010), s_lift),
        K.Shot("map", 13.6, 17.2, dict(dy=-16, dz=0.010), s_map),
        K.Shot("four", 17.2, 20.8, dict(dy=-18, dz=0.010), s_four),
        K.Shot("answer", 20.8, 24.8, dict(dz=0.012), s_answer),
    ]
