"""Flat-vector art for the crow story, drawn in SCREEN pixels of a 1080x1920 frame.

This replaces the v1 cartoon module, which drew in 4K "world units" that the renderer then shrank to
28 % and upscaled -- soft edges, thin detail, flat fills. Here every shape is drawn at the size it
lands on screen, so lines are crisp and the fills can carry gradients.

The vocabulary is a cartoon stage: a crow with a rigged head and wings, a cut-away pot whose water
level is the story, a lizard, a sun with opinions, and the punctuation (rings, bursts, sparkles).
Everything takes `a` (alpha) and animates from parameters, never from global time.
"""
import math

import numpy as np
import skia

# ------------------------------------------------------------------ palette
SKY_HI = (255, 173, 96)
SKY_LO = (255, 235, 190)
SKY_COOL = (150, 205, 232)
HOT = (255, 138, 64)
SUN = (255, 205, 96)
SUN_EDGE = (248, 158, 64)
HILL_FAR = (186, 206, 138)
HILL = (150, 184, 110)
GROUND = (226, 172, 108)
GROUND_LO = (198, 140, 84)
CRACK = (168, 112, 68)
CLAY = (200, 106, 74)
CLAY_HI = (232, 138, 100)
CLAY_LO = (150, 74, 52)
WATER = (86, 186, 220)
WATER_LO = (44, 140, 190)
WATER_FOAM = (206, 244, 250)
INK = (40, 28, 34)
INK_SOFT = (74, 56, 60)
CREAM = (255, 248, 232)
CREAM_DIM = (246, 228, 196)
ORANGE = (233, 94, 40)
CORAL = (233, 96, 84)
PINK = (232, 96, 132)
LEAF = (96, 158, 96)
LEAF_DARK = (68, 122, 76)
NIGHT = (72, 62, 110)


def P(rgb, a=1.0):
    return skia.Paint(AntiAlias=True, Color=skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(max(0, min(255, 255 * a)))))


def LN(rgb, a=1.0, w=6.0, cap=True):
    p = P(rgb, a)
    p.setStyle(skia.Paint.kStroke_Style)
    p.setStrokeWidth(w)
    if cap:
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def mul(rgb, k):
    return tuple(int(max(0, min(255, ch * k))) for ch in rgb)


def mix(c0, c1, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(c0[i] + (c1[i] - c0[i]) * u) for i in range(3))


def rect(x, y, w, h):
    return skia.Rect.MakeXYWH(x, y, w, h)


def rrect(x, y, w, h, r):
    return skia.RRect.MakeRectXY(rect(x, y, w, h), r, r)


def _colors(cols):
    """skia.Color accepts (r, g, b, a) or a positional a; normalise every stop through this."""
    return [skia.Color(c[0], c[1], c[2], c[3] if len(c) > 3 else 255) for c in cols]


def vgrad(c, x, y, w, h, c0, c1, a=1.0):
    """Vertical two-stop gradient fill."""
    g = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)],
                                       _colors([(*c0, int(255 * a)), (*c1, int(255 * a))]))
    p = skia.Paint(AntiAlias=True, Shader=g)
    c.drawRect(rect(x, y, w, h), p)


def vgrad3(c, x, y, w, h, c0, c1, c2, a=1.0):
    g = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)],
                                       _colors([(*c0, int(255 * a)), (*c1, int(255 * a)), (*c2, int(255 * a))]),
                                       [0.0, 0.55, 1.0])
    c.drawRect(rect(x, y, w, h), skia.Paint(AntiAlias=True, Shader=g))


def rgrad(c, cx, cy, r, c0, c1, a=1.0):
    g = skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1.0, r),
                                      [skia.Color(*c0, int(255 * a)), skia.Color(*c1, int(255 * a))])
    c.drawCircle(cx, cy, r, skia.Paint(AntiAlias=True, Shader=g))


def glow(c, cx, cy, r, rgb, a=0.5):
    """Soft radial bloom (no blur filter: a cheap radial alpha ramp)."""
    g = skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(1.0, r), [
        skia.Color(rgb[0], rgb[1], rgb[2], int(255 * a)),
        skia.Color(rgb[0], rgb[1], rgb[2], int(255 * a * 0.45)),
        skia.Color(rgb[0], rgb[1], rgb[2], 0)], [0.0, 0.45, 1.0])
    c.drawCircle(cx, cy, r, skia.Paint(AntiAlias=True, Shader=g))


def blob(c, cx, cy, rx, ry, rgb, a=1.0, rot=0.0):
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)
    c.drawOval(rect(-rx, -ry, rx * 2, ry * 2), P(rgb, a))
    c.restore()


def poly(c, pts, rgb, a=1.0, close=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    c.drawPath(p, P(rgb, a))


def catmull(c, pts, rgb, a=1.0):
    """Smooth closed blob through points (draws a filled organic shape)."""
    p = skia.Path()
    p.moveTo(*pts[0])
    n = len(pts)
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        pm, nm = pts[(i - 1) % n], pts[(i + 2) % n]
        c1 = (p0[0] + (p1[0] - pm[0]) / 6, p0[1] + (p1[1] - pm[1]) / 6)
        c2 = (p1[0] - (nm[0] - p0[0]) / 6, p1[1] - (nm[1] - p0[1]) / 6)
        p.cubicTo(*c1, *c2, *p1)
    p.close()
    c.drawPath(p, P(rgb, a))


# ------------------------------------------------------------------ sky & ground
# The camera pans across the world, so every backdrop covers a generous box, not just the frame.
WORLD = (-1600.0, -1500.0, 2680.0, 3600.0)     # x0, y0, x1, y1 -- wider and taller than any shot
WX0, WY0, WX1, WY1 = WORLD
WW, WH = WX1 - WX0, WY1 - WY0


SKY_TOP = (104, 168, 226)        # a real child's-picture-book sky, warm only near the ground
SKY_MID = (168, 208, 240)
SKY_LOW = (255, 236, 196)
SKY_HOT = (255, 190, 120)


def sky(c, t, hot=0.55, cool=0.0, a=1.0, horizon=1178.0):
    """Sky gradient measured UP from the horizon, so panning never changes its colour.

    Blue rule: a blue sky is calm, and the drought is told by the GROUND, the sun and the haze -- not
    by an orange wash that flattens the whole frame. `hot` only warms the last 300 px above the hills.
    """
    hot = max(0.0, min(1.0, hot))
    top = mix(SKY_TOP, (96, 150, 208), cool)
    mid = mix(SKY_MID, (150, 196, 228), cool)
    lo = mix(mix(SKY_LOW, SKY_HOT, hot * 0.75), (240, 248, 250), cool)
    g = skia.GradientShader.MakeLinear(
        [skia.Point(0, horizon - 1900), skia.Point(0, horizon + 20)],
        _colors([(*top, int(255 * a)), (*mid, int(255 * a)), (*lo, int(255 * a)),
                 (*mix(lo, (255, 250, 238), 0.5), int(255 * a))]),
        [0.0, 0.62, 0.94, 1.0])
    c.drawRect(rect(WX0, horizon - 1300, WW, 1340), skia.Paint(AntiAlias=True, Shader=g))
    # the heat is a wash at the horizon, not a filter: it keeps the sun readable
    if hot > 0.01:
        g = skia.GradientShader.MakeLinear([skia.Point(0, horizon - 340), skia.Point(0, horizon)],
                                           _colors([(*HOT, 0), (*HOT, int(58 * hot * a))]))
        c.drawRect(rect(WX0, horizon - 340, WW, 340), skia.Paint(AntiAlias=True, Shader=g))


def sun(c, x, y, r, t=0.0, hot=0.0, a=1.0, rays=True, face=True):
    for i in range(16 if rays else 0):
        ang = 2 * math.pi * (i / 16) + t * 0.18
        l = r * (1.30 + 0.10 * math.sin(t * 1.7 + i))
        c.drawLine(x + math.cos(ang) * r * 1.22, y + math.sin(ang) * r * 1.22,
                   x + math.cos(ang) * l, y + math.sin(ang) * l, LN(SUN_EDGE, 0.6 * a, r * 0.085))
    glow(c, x, y, r * 2.6, SUN, 0.30 * a)
    c.drawCircle(x, y, r * 1.04, P(SUN_EDGE, a))
    rgrad(c, x - r * 0.25, y - r * 0.3, r * 1.5, (255, 236, 168), SUN, a)
    if not face:
        return
    # cross as the drought bites: brows sink, mouth goes flat then down
    ey = y - r * 0.10 + hot * r * 0.03
    for sgn in (-1, 1):
        ex = x + sgn * r * 0.33
        c.drawCircle(ex, ey, r * 0.072, P((120, 64, 30), a))
        c.drawCircle(ex + sgn * r * 0.02, ey - r * 0.02, r * 0.028, P((255, 248, 232), 0.9 * a))
        bx0, bx1 = ex - sgn * r * 0.13, ex + sgn * r * 0.13
        by = ey - r * 0.20 + hot * r * 0.10
        c.drawLine(bx0, by + hot * r * 0.09 * (1 if sgn < 0 else 1), bx1, by - 0.02 * r + hot * r * 0.02,
                   LN((150, 84, 36), 0.85 * a, r * 0.055))
    my = y + r * 0.36
    p = skia.Path()
    if hot < 0.55:
        p.moveTo(x - r * 0.24, my - r * 0.04)
        p.quadTo(x, my + r * 0.20 - hot * r * 0.24, x + r * 0.24, my - r * 0.04)
    else:
        p.moveTo(x - r * 0.22, my + r * 0.02)
        p.quadTo(x, my - r * 0.14, x + r * 0.22, my + r * 0.02)
    c.drawPath(p, LN((140, 72, 30), 0.9 * a, r * 0.06))


def cloud(c, x, y, w, a=1.0, rgb=(255, 250, 244), shade=(226, 220, 224)):
    h = w * 0.30
    for dx, dy, r in ((-0.3, 0.04, 0.30), (-0.02, -0.22, 0.38), (0.28, 0.02, 0.30), (0.06, 0.10, 0.26)):
        c.drawCircle(x + dx * w, y + dy * w, r * w * 0.62, P(shade, 0.92 * a))
    for dx, dy, r in ((-0.30, -0.02, 0.28), (-0.02, -0.28, 0.36), (0.28, -0.04, 0.28), (0.05, 0.03, 0.24)):
        c.drawCircle(x + dx * w, y + dy * w, r * w * 0.60, P(rgb, a))


def hills(c, y, a=1.0, dry=0.0, scroll=0.0):
    far = mix(HILL_FAR, (206, 190, 140), dry)
    near = mix(HILL, (176, 156, 104), dry)
    for ox, h, wd, col in ((-240, 210, 640, far), (250, 250, 720, far), (700, 180, 560, far)):
        p = skia.Path()
        p.moveTo(ox + scroll * 0.16 - wd / 2, y)
        p.cubicTo(ox + scroll * 0.16 - wd * 0.3, y - h * 1.35, ox + scroll * 0.16 + wd * 0.3, y - h * 1.35,
                  ox + scroll * 0.16 + wd / 2, y)
        p.close()
        c.drawPath(p, P(col, a))
    for ox, h, wd in ((90, 150, 700), (620, 190, 720), (-420, 130, 620)):
        p = skia.Path()
        p.moveTo(ox + scroll * 0.3 - wd / 2, y)
        p.cubicTo(ox + scroll * 0.3 - wd * 0.28, y - h * 1.3, ox + scroll * 0.3 + wd * 0.28, y - h * 1.3,
                  ox + scroll * 0.3 + wd / 2, y)
        p.close()
        c.drawPath(p, P(near, a))


def ground(c, y, dry=0.8, a=1.0, cracks=True, seed=3):
    vgrad(c, WX0, y, WW, WY1 - y, mix(GROUND, (232, 190, 150), dry * 0.4), mix(GROUND_LO, (190, 150, 112), dry))
    # a lighter lip where the ground meets the horizon
    c.drawRect(rect(WX0, y - 6, WW, 12), P(mix(GROUND, (255, 226, 178), 0.5), 0.5 * a))
    if not cracks:
        return
    rng = np.random.default_rng(seed)
    for i in range(7):
        x0 = rng.uniform(WX0, WX1)
        y0 = y + rng.uniform(30, 520)
        p = skia.Path()
        p.moveTo(x0, y0)
        x, yy = x0, y0
        for _ in range(4):
            x += rng.uniform(-70, 70)
            yy += rng.uniform(10, 46)
            p.lineTo(x, yy)
        c.drawPath(p, LN(CRACK, 0.42 * a, 5.0))
    for i in range(26):
        x, yy = rng.uniform(WX0, WX1), y + rng.uniform(20, 900)
        c.drawCircle(x, yy, rng.uniform(2, 5), P(mul(CRACK, 0.9), 0.5 * a))


def grass(c, x, y, h, a=1.0, sway=0.0, rgb=LEAF):
    for i, off in enumerate((-0.5, 0.0, 0.5)):
        tip = x + off * h * 0.55 + math.sin(sway + i) * h * 0.22
        p = skia.Path()
        p.moveTo(x + off * h * 0.22, y)
        p.quadTo(x + off * h * 0.4, y - h * 0.55, tip, y - h)
        c.drawPath(p, LN(mul(rgb, 0.9 + 0.1 * i), a, max(2.0, h * 0.07)))


def tree(c, x, y, h, a=1.0, sway=0.0, bare=1.0, rgb=LEAF_DARK):
    """A thirsty tree: bare branches when bare=1, a few leaves otherwise."""
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(sway))
    trunk = skia.Path()
    trunk.moveTo(-h * 0.05, 0)
    trunk.cubicTo(-h * 0.03, -h * 0.3, -h * 0.07, -h * 0.55, -h * 0.02, -h * 0.78)
    trunk.lineTo(h * 0.05, -h * 0.78)
    trunk.cubicTo(h * 0.02, -h * 0.5, h * 0.06, -h * 0.26, h * 0.06, 0)
    c.drawPath(trunk, P((112, 78, 54), a))
    for (bx, by, dx, dy) in ((-0.02, -0.62, -0.3, -0.22), (0.02, -0.68, 0.32, -0.2), (0.0, -0.76, -0.12, -0.22)):
        c.drawLine(bx * h, by * h, (bx + dx) * h, (by + dy) * h, LN((112, 78, 54), a, h * 0.03))
    if bare < 0.99:
        for (bx, by, rr) in ((-0.32, -0.84, 0.16), (0.34, -0.88, 0.15), (-0.08, -1.0, 0.18)):
            c.drawCircle(bx * h, by * h, rr * h, P(rgb, a * (1 - bare)))
    c.restore()


# ------------------------------------------------------------------ the crow
def crow(c, x, y, s, a=1.0, look=1, flap=0.0, head=0.0, beak=0.0, blink=0.0, tilt=0.0, bob=0.0,
         tail=0.0, wing_open=0.0, body=(46, 48, 68), wing=(32, 34, 52), beak_rgb=(250, 186, 82),
         leg=0.0, crest=0.0, throat=0.0):
    """A cartoon crow, side view, facing +x (look=-1 mirrors it). s = body length in screen px.

    Local units (fractions of s, feet on y = +0.46): body -0.42..+0.30, tail to -0.95, head centre
    (+0.33, -0.40) with a 0.17 radius, beak to +0.72. One shape per limb, thin tips, so at 150 px it
    still reads as a bird and at 430 px it reads as a character.

    flap: wing stroke -1 down .. +1 up.  head: neck tilt (rad).  beak: 0..1 open.
    blink: 0..1 lid.  bob: body lift.  tilt: whole-body rotation (rad).  wing_open: 0 folded, 1 spread.
    leg: stride -1..1.  crest: hackle feathers 0..1.  throat: swallow bulge 0..1.
    """
    c.save()
    c.translate(x, y + bob)
    c.rotate(math.degrees(tilt))
    c.scale(look, 1)

    def fe(pts):
        return [(px * s, py * s) for px, py in pts]

    # ---- far wing: a slim leaf behind the body, only its edge showing
    fa = -0.50 + 1.30 * (flap + 1) / 2
    c.save()
    c.translate(s * 0.02, -s * 0.16)
    c.rotate(math.degrees(fa * (0.4 + 0.6 * wing_open)))
    wl = 0.40 + 0.42 * wing_open
    catmull(c, fe([(0.0, 0.02), (-0.26 * wl, -0.30 * wl), (-0.56 * wl, -0.36 * wl), (-0.46 * wl, -0.10 * wl),
                   (-0.14, 0.06)]), mul(wing, 0.92), a)
    c.restore()

    # ---- tail: one narrow wedge, fanned by `tail`
    c.save()
    c.translate(-s * 0.30, -s * 0.04)
    c.rotate(math.degrees(-0.10 + tail))
    for k, (ln, spread, shade) in enumerate(((1.00, 0.00, 1.00), (0.84, 0.10, 0.93), (0.68, 0.18, 0.86))):
        catmull(c, fe([(0.10, -0.10), (-0.24 * ln, -(0.14 + spread)), (-0.40 * ln, -(0.10 + spread * 0.6)),
                       (-0.38 * ln, -(0.02 + spread * 0.2)), (-0.16, 0.04), (0.08, 0.02)]),
                mul(body, shade), a)
    c.restore()

    # ---- legs
    for i, dx in enumerate((0.04, -0.12)):
        st = leg if i == 0 else -leg
        hx, hy = s * dx, s * 0.16
        kx, ky = hx + s * (0.02 + 0.02 * st), hy + s * 0.17
        fx, fy = kx + s * (0.05 + 0.08 * st), s * 0.46
        c.drawLine(hx, hy, kx, ky, LN((240, 172, 84), a, s * 0.032, cap=False))
        c.drawLine(kx, ky, fx, fy, LN((240, 172, 84), a, s * 0.026, cap=False))
        for j in (-1, 0, 1):
            c.drawLine(fx, fy, fx + s * (0.075 + 0.012 * j), fy + s * 0.026 * j,
                       LN((240, 172, 84), a, s * 0.020, cap=False))

    # ---- body: an egg tilted nose-up, chest forward, narrow at the tail root
    catmull(c, fe([(-0.40, 0.02), (-0.30, -0.20), (-0.06, -0.30), (0.20, -0.24), (0.30, -0.04),
                   (0.20, 0.18), (-0.04, 0.26), (-0.28, 0.20)]), body, a)
    catmull(c, fe([(0.02, -0.16), (0.18, -0.12), (0.22, 0.02), (0.12, 0.14), (-0.02, 0.12)]),
            mul(body, 1.5), a * 0.40)

    # ---- neck + head
    c.save()
    c.translate(s * 0.20, -s * 0.24)
    c.rotate(math.degrees(head))
    catmull(c, fe([(-0.06, 0.06), (0.02, -0.08), (0.16, -0.12), (0.18, 0.02), (0.08, 0.10)]), body, a)
    hx, hy, hr = s * 0.15, -s * 0.17, s * 0.155
    c.drawCircle(hx, hy, hr, P(body, a))
    c.drawCircle(hx - hr * 0.25, hy - hr * 0.28, hr * 0.55, P(mul(body, 1.28), 0.45 * a))
    if crest > 0.01:
        for k in range(3):
            ang = -2.30 + k * 0.24 - crest * 0.26
            x0, y0 = hx - hr * 0.35, hy - hr * 0.72
            c.drawLine(x0, y0, x0 + math.cos(ang) * s * (0.08 + 0.10 * crest),
                       y0 + math.sin(ang) * s * (0.08 + 0.10 * crest), LN(mul(body, 1.35), a, s * 0.032))
    # beak: upper wedge and a lower mandible that swings
    bx, by = hx + hr * 0.55, hy + hr * 0.16
    poly(c, fe([(bx / s, by / s), ((bx + s * 0.30) / s, (by - s * 0.030) / s),
                ((bx + s * 0.02) / s, (by + s * 0.030) / s)]), beak_rgb, a)
    bo = beak * s * 0.13
    poly(c, [(bx, by + s * 0.030), (bx + s * 0.22, by + s * 0.036 + bo * 0.55), (bx, by + s * 0.070 + bo)],
         mul(beak_rgb, 0.85), a)
    # eye
    ex, ey, er = hx + s * 0.045, hy - s * 0.030, s * 0.058
    if blink < 0.62:
        c.drawCircle(ex, ey, er, P((252, 250, 244), a))
        c.drawCircle(ex + er * 0.16, ey, er * 0.60, P(INK, a))
        c.drawCircle(ex + er * 0.34, ey - er * 0.28, er * 0.22, P((255, 255, 255), a))
        if blink > 0.01:
            c.save()
            c.clipRect(rect(ex - er * 1.2, ey - er * 1.2, er * 2.4, er * 2.4 * (blink / 0.62)), True)
            c.drawCircle(ex, ey, er * 1.02, P(mul(body, 1.02), a))
            c.restore()
    else:
        c.drawLine(ex - er, ey + er * 0.15, ex + er, ey - er * 0.15, LN(INK, a, s * 0.026))
    if throat > 0.01:
        c.drawCircle(s * 0.09, -s * 0.04 + throat * s * 0.07, s * (0.045 + 0.025 * throat), P(mul(body, 1.18), a))
    c.restore()

    # ---- near wing: a shoulder at (0.02, -0.16) and one tapered quill fan
    ang = -0.70 + 1.35 * (flap + 1) / 2
    c.save()
    c.translate(s * 0.04, -s * 0.16)
    c.rotate(math.degrees(ang * (0.45 + 0.55 * (1 - wing_open))))
    for k, (ln, lift) in enumerate(((1.0, 0.0), (0.76, 0.08), (0.54, 0.14))):
        catmull(c, fe([(0.02, 0.06), (-0.22 * ln, -(0.12 + lift)), (-0.42 * ln, -(0.16 + lift)),
                       (-0.38 * ln, -(0.02 + lift * 0.4)), (-0.10 * ln, 0.08)]),
                mul(wing, 1.0 + 0.14 * k), a)
    c.restore()
    c.restore()


# ------------------------------------------------------------------ the pot (the story's hero prop)
def pot_paths(x, y, w, h):
    """Outer silhouette and the cut-away window, both as skia paths. (x, y) = top-centre."""
    def body(inset):
        p = skia.Path()
        r = w / 2 - inset
        p.moveTo(x - r, y + h * 0.02)
        p.cubicTo(x - r * 1.10, y + h * 0.42, x - r * 0.78, y + h * 0.86, x - r * 0.52, y + h * 0.97)
        p.lineTo(x + r * 0.52, y + h * 0.97)
        p.cubicTo(x + r * 0.78, y + h * 0.86, x + r * 1.10, y + h * 0.42, x + r, y + h * 0.02)
        p.close()
        return p

    def window(inset):
        p = skia.Path()
        r = w / 2 - inset
        p.moveTo(x - r, y + h * 0.10)
        p.cubicTo(x - r * 0.98, y + h * 0.46, x - r * 0.70, y + h * 0.83, x - r * 0.46, y + h * 0.90)
        p.lineTo(x + r * 0.46, y + h * 0.90)
        p.cubicTo(x + r * 0.70, y + h * 0.83, x + r * 0.98, y + h * 0.46, x + r, y + h * 0.10)
        p.close()
        return p

    return body, window


def pot(c, x, y, w, h, level=0.0, a=1.0, stones=0, ripple=0.0, seed=7, water=True, wobble=0.0):
    """A cut-away clay pot: the water line and the pile of stones are visible at the same time.

    level: 0 = empty, 1 = full to the window's top.  stones: how many have been dropped in.
    ripple: 0..1 phase for rings on the water surface (call with (t*2)%1 for a live surface).
    """
    body, window = pot_paths(x, y, w, h)
    # contact shadow on the ground
    c.drawOval(rect(x - w * 0.55, y + h * 0.94, w * 1.1, h * 0.10), P((90, 54, 34), 0.22 * a))
    # body fill: clay, lit from the left, darker at the belly
    g = skia.GradientShader.MakeLinear([skia.Point(x - w / 2, y), skia.Point(x + w / 2, y)],
                                       _colors([(*CLAY_HI, int(255 * a)), (*CLAY_LO, int(255 * a))]),
                                       [0.0, 1.0])
    c.drawPath(body(0), skia.Paint(AntiAlias=True, Shader=g))
    # painted bands (they curve with the pot, so the pot reads as round)
    c.save()
    c.clipPath(body(0), skia.ClipOp.kIntersect, True)
    for fy, wid, col in ((0.30, 0.030, mul(CLAY_LO, 0.92)), (0.36, 0.012, CREAM_DIM), (0.66, 0.030, mul(CLAY_LO, 0.92)),
                         (0.72, 0.012, CREAM_DIM)):
        c.drawRect(rect(x - w, y + h * fy, w * 2, h * wid), P(col, 0.75 * a))
    c.restore()
    # inner wall + water + stones inside the window
    wpath = window(w * 0.075)
    c.save()
    c.clipPath(wpath, skia.ClipOp.kIntersect, True)
    vgrad(c, x - w, y + h * 0.06, w * 2, h * 0.86, (176, 110, 78), (132, 76, 54), a)
    if water:
        top = y + h * (0.90 - 0.78 * max(0.0, min(1.0, level)))
        vgrad(c, x - w / 2, top, w, h, WATER, WATER_LO, a)
        # surface line with a wobble
        p = skia.Path()
        p.moveTo(x - w / 2, top)
        n = 12
        for i in range(1, n + 1):
            u = i / n
            p.lineTo(x - w / 2 + w * u, top + math.sin(u * 9 + wobble * 6) * 3.5)
        c.drawPath(p, LN(WATER_FOAM, 0.75 * a, 5))
        for k in range(3):
            rr = (ripple + k / 3) % 1.0
            c.drawOval(rect(x - 40 - rr * 120, top - rr * 26, 80 + rr * 240, 22 + rr * 52),
                       LN(WATER_FOAM, 0.45 * (1 - rr) * a, 3))
    # the pile of stones: deterministic, and it only ever grows
    rng = np.random.default_rng(seed)
    for i in range(int(stones)):
        sw = w * rng.uniform(0.045, 0.075)
        sy = y + h * 0.86 - (i // 6) * sw * 0.9 - rng.uniform(0, sw * 0.35)
        sx = x + (i % 6 - 2.5) * sw * 1.35 + rng.uniform(-sw * 0.3, sw * 0.3)
        c.drawOval(rect(sx - sw, sy - sw * 0.8, sw * 2, sw * 1.6), P(rng.choice([(126, 118, 112), (108, 100, 96),
                                                                                 (146, 134, 122)]), a))
        c.drawOval(rect(sx - sw * 0.55, sy - sw * 0.62, sw * 0.9, sw * 0.7), P((170, 160, 150), 0.6 * a))
    c.restore()
    # window rim (the thickness of the clay wall we cut through)
    c.drawPath(wpath, LN(mul(CLAY_LO, 0.86), a, w * 0.028))
    # mouth of the pot + rim highlight
    c.drawOval(rect(x - w / 2, y - h * 0.028, w, h * 0.10), P(mul(CLAY_LO, 0.9), a))
    c.drawOval(rect(x - w / 2 + w * 0.02, y - h * 0.020, w * 0.96, h * 0.086), P((70, 38, 30), a))
    c.drawPath(skia.Path(), P(CREAM, 0))
    # a specular streak down the left shoulder
    c.save()
    c.clipPath(body(0), skia.ClipOp.kIntersect, True)
    c.drawOval(rect(x - w * 0.40, y + h * 0.10, w * 0.13, h * 0.52), P((255, 226, 196), 0.20 * a))
    c.restore()


# ------------------------------------------------------------------ the lizard
def lizard(c, x, y, s, a=1.0, look=-1, wig=0.0, blink=0.0, mouth=0.0, tail=0.0, tilt=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(tilt))
    c.scale(look, 1)
    green = (118, 186, 118)
    dark = (86, 148, 96)
    # tail: a curve that whips
    p = skia.Path()
    p.moveTo(-s * 0.42, s * 0.02)
    p.cubicTo(-s * 0.72, s * (0.02 + 0.16 * math.sin(tail)), -s * 0.92, -s * 0.10 + s * 0.30 * math.sin(tail * 1.4),
              -s * 1.10, s * 0.10 + s * 0.26 * math.sin(tail * 1.9))
    c.drawPath(p, LN(green, a, s * 0.16))
    # back legs / front legs (short, splayed)
    for (bx, by, fx, fy) in ((-0.22, 0.06, -0.34, 0.26), (0.22, 0.04, 0.34, 0.24)):
        c.drawLine(s * bx, s * by, s * fx, s * fy, LN(dark, a, s * 0.09))
        for k in (-1, 0, 1):
            c.drawLine(s * fx, s * fy, s * (fx + 0.05 + 0.03 * k), s * (fy + 0.06),
                       LN(dark, a, s * 0.05))
    # body
    catmull(c, [(-s * 0.48, 0.0), (-s * 0.20, -s * 0.18), (s * 0.14, -s * 0.16), (s * 0.34, -s * 0.02),
                (s * 0.16, s * 0.14), (-s * 0.22, s * 0.16)], green, a)
    # scale speckles
    for (dx, dy) in ((-0.26, -0.02), (-0.06, 0.04), (0.10, -0.06), (-0.14, 0.08)):
        c.drawCircle(s * dx, s * dy, s * 0.035, P(mul(green, 1.22), 0.85 * a))
    # head
    c.save()
    c.translate(s * 0.30, -s * 0.10)
    c.rotate(s * 2.5 * math.sin(wig * 6))
    catmull(c, [(-s * 0.10, -s * 0.02), (s * 0.02, -s * 0.13), (s * 0.20, -s * 0.10), (s * 0.24, s * 0.02),
                (s * 0.08, s * 0.12), (-s * 0.08, s * 0.08)], mul(green, 1.06), a)
    # eye
    ex, ey = s * 0.09, -s * 0.05
    c.drawCircle(ex, ey, s * 0.075, P((252, 248, 230), a))
    if blink < 0.6:
        c.drawCircle(ex + s * 0.012, ey, s * 0.040, P(INK, a))
        c.drawCircle(ex + s * 0.022, ey - s * 0.016, s * 0.014, P((255, 255, 255), a))
    else:
        c.drawLine(ex - s * 0.06, ey, ex + s * 0.06, ey, LN(INK, a, s * 0.022))
    # mouth
    c.drawLine(ex - s * 0.04, s * 0.06, s * 0.20, s * 0.05 + mouth * s * 0.06, LN(mul(green, 0.6), a, s * 0.022))
    c.restore()
    c.restore()


# ------------------------------------------------------------------ effects
def ring(c, x, y, r, a=1.0, w=8, rgb=CREAM):
    c.drawCircle(x, y, r, LN(rgb, a, w))


def burst(c, x, y, r, a=1.0, n=9, rgb=CREAM, inner=0.45, rot=0.0):
    p = skia.Path()
    for i in range(n * 2):
        ang = rot + math.pi * i / n
        rr = r if i % 2 == 0 else r * inner
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        p.moveTo(x, y) if i == 0 else p.lineTo(px, py)
    p.close()
    c.drawPath(p, P(rgb, a))


def star(c, x, y, r, a=1.0, rgb=(255, 236, 150), rot=0.0):
    p = skia.Path()
    for i in range(10):
        ang = rot + math.pi * i / 5
        rr = r if i % 2 == 0 else r * 0.42
        px, py = x + math.cos(ang) * rr, y + math.sin(ang) * rr
        p.moveTo(px, py) if i == 0 else p.lineTo(px, py)
    p.close()
    c.drawPath(p, P(rgb, a))


def sparkle(c, x, y, r, a=1.0, rgb=(255, 246, 200)):
    c.drawCircle(x, y, r, P(rgb, a * 0.85))
    for ang in (0, math.pi / 2):
        c.drawLine(x - math.cos(ang) * r * 1.9, y - math.sin(ang) * r * 1.9,
                   x + math.cos(ang) * r * 1.9, y + math.sin(ang) * r * 1.9, LN(rgb, a, r * 0.5))


def speed_lines(c, x, y, w, h, a=0.6, n=4, rgb=CREAM):
    for i in range(n):
        yy = y + (i - (n - 1) / 2) * h / max(1, n - 1)
        c.drawLine(x, yy, x + w * (0.6 + 0.4 * (i % 2)), yy, LN(rgb, a * (0.5 + 0.2 * (i % 2)), 5))


def sweat(c, x, y, s, a=1.0):
    p = skia.Path()
    p.moveTo(x, y - s)
    p.cubicTo(x + s * 0.8, y - s * 0.1, x + s * 0.55, y + s * 0.7, x, y + s * 0.7)
    p.cubicTo(x - s * 0.55, y + s * 0.7, x - s * 0.8, y - s * 0.1, x, y - s)
    c.drawPath(p, P((176, 224, 244), a))


def heart(c, x, y, s, a=1.0, rgb=PINK):
    p = skia.Path()
    p.moveTo(x, y + s * 0.75)
    p.cubicTo(x - s * 1.5, y - s * 0.35, x - s * 0.45, y - s * 1.25, x, y - s * 0.35)
    p.cubicTo(x + s * 0.45, y - s * 1.25, x + s * 1.5, y - s * 0.35, x, y + s * 0.75)
    c.drawPath(p, P(rgb, a))


def bubble(c, x, y, w, h, a=1.0, tail=(0.5, 1.0), rgb=(255, 250, 240), line_rgb=(206, 168, 128),
           flip=False):
    """Speech bubble centred on (x, y). tail = fractional anchor on the bubble's bottom edge
    (flip=True points the tail back UP at a speaker above the bubble)."""
    body = rrect(x - w / 2, y - h / 2, w, h, min(w, h) * 0.34)
    tx = x + (tail[0] - 0.5) * w
    ty = y + h / 2 if not flip else y - h / 2
    sgn = 1.0 if not flip else -1.0
    p = skia.Path()
    p.moveTo(tx - w * 0.09, ty - h * 0.02 * sgn)
    p.lineTo(tx + w * 0.02, ty + h * 0.30 * sgn)
    p.lineTo(tx + w * 0.13, ty - h * 0.02 * sgn)
    p.close()
    c.drawRRect(skia.RRect.MakeRectXY(rect(x - w / 2, y - h / 2 + 8, w, h), min(w, h) * 0.34, min(w, h) * 0.34),
                P((90, 56, 40), 0.18 * a))
    c.drawPath(p, P(rgb, a))
    c.drawRRect(body, P(rgb, a))
    c.drawPath(p, LN(line_rgb, 0.9 * a, 3))
    c.drawRRect(body, LN(line_rgb, 0.9 * a, 3))


def plaque(c, x, y, w, h, a=1.0, rgb=CREAM, edge=(214, 170, 122), rot=0.0):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.drawRRect(skia.RRect.MakeRectXY(rect(-w / 2 + 6, -h / 2 + 10, w, h), 24, 24), P((80, 50, 36), 0.22 * a))
    c.drawRRect(skia.RRect.MakeRectXY(rect(-w / 2, -h / 2, w, h), 24, 24), P(rgb, a))
    c.drawRRect(skia.RRect.MakeRectXY(rect(-w / 2, -h / 2, w, h), 24, 24), LN(edge, 0.9 * a, 3))
    c.restore()


def mote_field(c, t, n=26, a=1.0, w=1080, h=1920, rgb=(255, 236, 196), seed=11, origin=(0, 0)):
    """Dust drifting in the heat -- cheap, deterministic, and it stops the sky reading as a still."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        x0, y0, sp, rr = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(8, 30), rng.uniform(1.6, 4.4)
        x = (x0 + origin[0] + t * sp * 0.5 + 40 * math.sin(t * 0.6 + i)) % (w + 80) - 40
        y = (y0 + origin[1] - t * sp) % (h + 80) - 40
        al = a * (0.20 + 0.18 * math.sin(t * 1.7 + i * 2.1))
        c.drawCircle(x, y, rr, P(rgb, al))


def heat_lines(c, t, y0, y1, a=0.16, n=9, x0=-200.0, x1=1280.0):
    """Horizontal shimmer bands: the air over baked ground."""
    for i in range(n):
        yy = y0 + (y1 - y0) * i / max(1, n - 1)
        p = skia.Path()
        p.moveTo(x0, yy)
        for k in range(1, 13):
            x = x0 + (x1 - x0) * k / 12
            p.lineTo(x, yy + math.sin(t * 2.2 + k * 0.9 + i) * 7)
        c.drawPath(p, LN((255, 246, 220), a, 6))
