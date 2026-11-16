"""Flat-vector cartoon bits for the crow story: a sun, hills, trees, a pot, a crow, stones, water.

Everything is drawn in world px at the scale the camera will see it, so it stays crisp. Shapes take a
`stroke` pass (a darker outline) and a `fill` pass, in that order, which is all this style needs.
"""
import math

import skia

CREAM = (248, 238, 218)
INK = (28, 24, 26)


def P(rgb, a=1.0):
    return skia.Paint(AntiAlias=True, Color=skia.Color(int(rgb[0]), int(rgb[1]), int(rgb[2]), int(255 * a)))


def line(rgb, a=1.0, w=6.0):
    p = P(rgb, a); p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(w); p.setStrokeCap(skia.Paint.kRound_Cap)
    p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def path_from(pts, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if close:
        p.close()
    return p


def circle(c, x, y, r, rgb, a=1.0, stroke=None, sw=None):
    if stroke:
        c.drawCircle(x, y, r, P(stroke, a))
    c.drawCircle(x, y, r, P(rgb, a))


def blob(c, cx, cy, rx, ry, rgb, a=1.0, rot=0.0, stroke=None, sw=0.0):
    c.save(); c.translate(cx, cy); c.rotate(rot)
    r = skia.Rect.MakeXYWH(-rx, -ry, rx * 2, ry * 2)
    if stroke:
        c.drawOval(r, P(stroke, a))
    c.drawOval(r, P(rgb, a))
    c.restore()


def sun(c, x, y, r, a=1.0, t=None, rays=14, rgb=(252, 196, 92), ray_rgb=(246, 168, 74)):
    """A cartoon sun, optionally turning (pass t and it rotates slowly)."""
    if t is not None:
        phase = t * 0.25
        c.save(); c.translate(x, y); c.rotate(math.degrees(phase) % 360); c.translate(-x, -y)
    for i in range(rays):
        ang = 2 * math.pi * i / rays
        x0, y0 = x + math.cos(ang) * r * 1.18, y + math.sin(ang) * r * 1.18
        x1, y1 = x + math.cos(ang) * r * 1.52, y + math.sin(ang) * r * 1.52
        c.drawLine(x0, y0, x1, y1, line(ray_rgb, a, r * 0.10))
    if t is not None:
        c.restore()
    c.drawCircle(x, y, r * 1.06, P((250, 176, 96), a))
    c.drawCircle(x, y, r, P(rgb, a))


def hill(c, x, y, w, h, rgb, a=1.0):
    """A rounded hill sitting on the line y."""
    p = skia.Path()
    p.moveTo(x - w / 2, y)
    p.cubicTo(x - w / 2, y - h * 1.55, x + w / 2, y - h * 1.55, x + w / 2, y)
    p.close()
    c.drawPath(p, P(rgb, a))


def tree(c, x, y, h, rgb=(64, 116, 78), trunk=(104, 74, 52), a=1.0, sway=0.0):
    """A cartoon tree; sway tilts the crown (radians) so it can breathe."""
    c.drawRect(skia.Rect.MakeXYWH(x - h * 0.045, y - h * 0.45, h * 0.09, h * 0.47), P(trunk, a))
    c.save(); c.translate(x, y - h * 0.45); c.rotate(math.degrees(sway))
    for (dx, dy, rr) in ((0.0, -0.30, 0.30), (-0.22, -0.16, 0.23), (0.22, -0.16, 0.23), (0.0, -0.02, 0.26)):
        c.drawCircle(dx * h, dy * h, rr * h, P(rgb, a))
    c.restore()


def pot(c, x, y, w, h, rgb=(188, 118, 78), rim=(214, 146, 100), a=1.0, water=0.0):
    """The water pot: a narrow-necked jar. `water` 0..1 fills it from the bottom."""
    body = skia.Path()
    body.moveTo(x - w * 0.34, y - h)
    body.cubicTo(x - w * 0.52, y - h * 0.55, x - w * 0.50, y, x - w * 0.30, y)
    body.lineTo(x + w * 0.30, y)
    body.cubicTo(x + w * 0.50, y, x + w * 0.52, y - h * 0.55, x + w * 0.34, y - h)
    body.close()
    c.save()
    c.clipPath(body, skia.ClipOp.kIntersect, True)
    c.drawRect(skia.Rect.MakeXYWH(x - w, y - h, w * 2, h), P(rgb, a))
    if water > 0:
        wy = y - h * water * 0.72
        c.drawRect(skia.Rect.MakeXYWH(x - w, wy, w * 2, y - wy), P((86, 168, 196), a))
        c.drawRect(skia.Rect.MakeXYWH(x - w, wy - h * 0.02, w * 2, h * 0.03), P((160, 220, 232), a))
    c.restore()
    # rim and a highlight
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.36, y - h - h * 0.05, w * 0.72, h * 0.11), P(rim, a))
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.36, y - h - h * 0.05, w * 0.72, h * 0.11), line((120, 72, 46), a * 0.6, w * 0.012))
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.22, y - h * 0.72, w * 0.10, h * 0.34), P((236, 196, 160), 0.35 * a), )
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.16, y - h * 0.60, w * 0.30, h * 0.22), P((236, 196, 160), 0.18 * a))


def stone(c, x, y, r, rgb=(126, 122, 128), a=1.0, rot=0.0):
    blob(c, x, y, r, r * 0.82, rgb, a, rot=rot)
    blob(c, x - r * 0.28, y - r * 0.26, r * 0.26, r * 0.18, (176, 172, 178), a * 0.7, rot=rot - 0.2)


def crow(c, x, y, s, a=1.0, flap=0.0, look=1.0, beak_open=0.0, body=(38, 40, 52), wing=(26, 28, 40),
         beak=(238, 176, 72)):
    """A cartoon crow, side view, facing right (look=-1 flips it). s = body size in world px.

    flap: -1..1, how far the near wing is through its stroke; beak_open: 0..1.
    """
    c.save(); c.translate(x, y); c.scale(look, 1)
    # tail
    tail = path_from([(-s * 0.62, -s * 0.05), (-s * 1.12, -s * 0.30), (-s * 1.05, s * 0.06), (-s * 0.60, s * 0.18)])
    c.drawPath(tail, P(body, a))
    # legs
    for dx in (-0.10, 0.10):
        c.drawLine(s * dx, s * 0.42, s * dx, s * 0.62, line((220, 150, 70), a, s * 0.045))
        c.drawLine(s * dx, s * 0.62, s * (dx + 0.10), s * 0.66, line((220, 150, 70), a, s * 0.045))
    # body
    blob(c, 0, s * 0.12, s * 0.52, s * 0.44, body, a, rot=-0.12)
    # head
    blob(c, s * 0.40, -s * 0.26, s * 0.28, s * 0.26, body, a)
    # beak
    bo = beak_open * s * 0.10
    upper = path_from([(s * 0.60, -s * 0.30), (s * 1.02, -s * 0.22), (s * 0.60, -s * 0.16)])
    lower = path_from([(s * 0.60, -s * 0.12 + bo), (s * 0.94, -s * 0.10 + bo), (s * 0.60, -s * 0.02 + bo)])
    c.drawPath(upper, P(beak, a)); c.drawPath(lower, P((214, 150, 58), a))
    # eye
    c.drawCircle(s * 0.46, -s * 0.32, s * 0.075, P((250, 248, 240), a))
    c.drawCircle(s * 0.48, -s * 0.32, s * 0.040, P(INK, a))
    c.drawCircle(s * 0.495, -s * 0.334, s * 0.013, P((255, 255, 255), a))
    # near wing: the flap swings it up and back
    ang = -0.9 + 1.4 * (flap + 1) / 2
    c.save(); c.translate(-s * 0.05, -s * 0.02); c.rotate(math.degrees(ang))
    wpath = path_from([(0, 0), (-s * 0.62, -s * 0.44), (-s * 0.50, -s * 0.02), (-s * 0.20, s * 0.24)])
    c.drawPath(wpath, P(wing, a))
    c.drawPath(path_from([(0, 0), (-s * 0.40, -s * 0.26), (-s * 0.34, -s * 0.02), (-s * 0.14, s * 0.14)]),
               P((58, 60, 76), a * 0.9))
    c.restore()
    c.restore()


def splash(c, x, y, r, a=1.0, t=0.0, rgb=(150, 216, 232)):
    """A little water crown; t animates the droplets outward."""
    u = (t * 1.4) % 1.0
    for i in range(7):
        ang = math.pi * (0.15 + 0.7 * i / 6)
        d = r * (0.6 + 0.9 * u)
        px, py = x + math.cos(ang) * d * (1 if i % 2 else -1), y - math.sin(ang) * d
        c.drawCircle(px, py, r * (0.10 + 0.08 * (1 - u)), P(rgb, a * (1 - u) * 0.9))
    c.drawOval(skia.Rect.MakeXYWH(x - r * 0.7, y - r * 0.10, r * 1.4, r * 0.20), P(rgb, a * 0.5))


# ------------------------------------------------------------------ dry season props
def cloud(c, x, y, w, a=1.0, rgb=(252, 250, 246), shade=(226, 230, 236)):
    """A soft cartoon cloud; w is its overall width."""
    h = w * 0.34
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.5, y - h * 0.05, w, h * 0.62), P(shade, a))
    for dx, dy, r in ((-0.28, 0.0, 0.30), (0.0, -0.22, 0.40), (0.28, 0.02, 0.32), (0.10, 0.10, 0.34)):
        c.drawCircle(x + dx * w, y + dy * w, r * w * 0.55, P(shade, a))
    for dx, dy, r in ((-0.28, -0.04, 0.29), (0.0, -0.28, 0.38), (0.28, -0.02, 0.30)):
        c.drawCircle(x + dx * w, y + dy * w, r * w * 0.55, P(rgb, a))


def sun_face(c, x, y, r, t=0.0, a=1.0, hot=0.0):
    """The story's sun: rays, then a face that gets crosser as the drought goes on (hot 0..1)."""
    sun(c, x, y, r, a, t=t, rays=14)
    # eyes and a mouth that flattens out as hot rises
    for sgn in (-1, 1):
        ex = x + sgn * r * 0.33
        ey = y - r * 0.12
        c.drawCircle(ex, ey, r * 0.055, P((120, 70, 30), a))
    mw = r * 0.42
    my = y + r * 0.34
    mp = skia.Path()
    mp.moveTo(x - mw, my)
    curve = -r * (0.30 - 0.42 * hot)
    mp.quadTo(x, my + curve, x + mw, my)
    c.drawPath(mp, line((120, 70, 30), a, r * 0.055))


def grass_tuft(c, x, y, h, rgb=(148, 160, 96), a=1.0, sway=0.0, n=5):
    for i in range(n):
        dx = (i - (n - 1) / 2) * h * 0.16
        tilt = (i - (n - 1) / 2) * 0.22 + sway
        p = skia.Path()
        p.moveTo(x + dx, y)
        p.quadTo(x + dx + math.sin(tilt) * h * 0.3, y - h * 0.6, x + dx + math.sin(tilt) * h * 0.55, y - h)
        c.drawPath(p, line(rgb, a, h * 0.09))


def dry_cracks(c, x, y, w, h, a=1.0, seed=3, rgb=(168, 120, 78)):
    """Cracks in baked earth: a few branching strokes."""
    rng = __import__("numpy").random.default_rng(seed)
    for i in range(6):
        sx = x + (rng.random() - 0.5) * w
        sy = y + (rng.random() - 0.5) * h
        p = skia.Path()
        p.moveTo(sx, sy)
        cx, cy = sx, sy
        for _ in range(3):
            cx += (rng.random() - 0.5) * w * 0.22
            cy += (rng.random() - 0.3) * h * 0.25
            p.lineTo(cx, cy)
        c.drawPath(p, line(rgb, a * 0.55, max(2.0, h * 0.012)))


def sweat(c, x, y, r, a=1.0, rgb=(150, 208, 236)):
    """A cartoon sweat bead: round bottom, pointed top."""
    p = skia.Path()
    p.moveTo(x, y - r * 1.9)
    p.cubicTo(x + r * 0.95, y - r * 0.5, x + r, y + r * 0.35, x, y + r)
    p.cubicTo(x - r, y + r * 0.35, x - r * 0.95, y - r * 0.5, x, y - r * 1.9)
    p.close()
    c.drawPath(p, P(rgb, a))
    c.drawCircle(x - r * 0.3, y + r * 0.2, r * 0.25, P((236, 250, 255), a * 0.8))


def sparkle(c, x, y, r, a=1.0, rgb=(255, 236, 160)):
    """A four point star that twinkles."""
    p = skia.Path()
    p.moveTo(x, y - r)
    p.quadTo(x + r * 0.16, y - r * 0.16, x + r, y)
    p.quadTo(x + r * 0.16, y + r * 0.16, x, y + r)
    p.quadTo(x - r * 0.16, y + r * 0.16, x - r, y)
    p.quadTo(x - r * 0.16, y - r * 0.16, x, y - r)
    p.close()
    c.drawPath(p, P(rgb, a))


def bubble(c, x, y, w, h, rgb=(255, 252, 244), line_rgb=(60, 50, 56), a=1.0, tail=(0, 1), kind="speech"):
    """Speech or thought bubble; tail is a direction (dx, dy) the balloon's little tail points."""
    r = min(w, h) * 0.30
    rect = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), P(line_rgb, a))
    inner = rect.makeInset(3.0, 3.0)
    c.drawRRect(skia.RRect.MakeRectXY(inner, r, r), P(rgb, a))
    if kind == "thought":
        for k, (dx, dy, rr) in enumerate(((0.55, 1.0, 0.055), (0.72, 1.2, 0.035), (0.86, 1.34, 0.022))):
            cx = x + tail[0] * w * dx
            cy = y + tail[1] * h * dy
            c.drawCircle(cx, cy, w * rr, P(line_rgb, a))
            c.drawCircle(cx, cy, w * rr - 3, P(rgb, a))
    else:
        # tail: a wedge whose base sits on the balloon edge, pointing along `tail`
        ang = math.atan2(tail[1] * h, tail[0] * w)
        rx, ry = w / 2 - r * 0.2, h / 2 - r * 0.2
        ex = x + math.cos(ang) * rx * 0.96
        ey = y + math.sin(ang) * ry * 0.96
        nx, ny = -math.sin(ang), math.cos(ang)
        base = min(w, h) * 0.14
        tipx = x + math.cos(ang) * (w / 2 + min(w, h) * 0.26)
        tipy = y + math.sin(ang) * (h / 2 + min(w, h) * 0.26)
        p = skia.Path()
        p.moveTo(ex + nx * base, ey + ny * base)
        p.lineTo(tipx, tipy)
        p.lineTo(ex - nx * base, ey - ny * base)
        p.close()
        c.drawPath(p, P(line_rgb, a))
        p2 = skia.Path()
        p2.moveTo(ex + nx * base * 0.72, ey + ny * base * 0.72)
        p2.lineTo(tipx - math.cos(ang) * 5, tipy - math.sin(ang) * 5)
        p2.lineTo(ex - nx * base * 0.72, ey - ny * base * 0.72)
        p2.close()
        c.drawPath(p2, P(rgb, a))


def exclaim(c, x, y, s, a=1.0, rgb=(232, 74, 62)):
    """A cartoon exclamation mark that pops."""
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - s * 0.13, y - s * 0.9, s * 0.26, s * 0.66), s * 0.12, s * 0.12), P(rgb, a))
    c.drawCircle(x, y - s * 0.06, s * 0.135, P(rgb, a))


# ------------------------------------------------------------------ the lizard
def lizard(c, x, y, s, a=1.0, wiggle=0.0, eye=1.0, mouth=0.0, look=1.0, body=(118, 176, 96),
           belly=(176, 214, 148), shade=(84, 140, 74)):
    """A small sidekick lizard on the ground: s = body length; wiggle swings the tail, eye scales the
    eyes (1 = normal, 1.6 = amazed), mouth 0..1 opens it."""
    c.save(); c.translate(x, y); c.scale(look, 1)
    # tail: a wavy taper
    tail = skia.Path()
    tail.moveTo(-s * 0.42, -s * 0.10)
    tail.cubicTo(-s * 0.85, -s * 0.10 + wiggle * s * 0.30, -s * 1.10, -s * 0.55 + wiggle * s * 0.50, -s * 1.45, -s * 0.30 + wiggle * s * 0.55)
    c.drawPath(tail, line(body, a, s * 0.13))
    # back legs and front legs
    for (lx, ang) in ((-s * 0.26, -0.5), (s * 0.24, -0.6)):
        c.drawLine(lx, -s * 0.14, lx + s * 0.16, -s * 0.02, line(shade, a, s * 0.075))
        c.drawLine(lx + s * 0.16, -s * 0.02, lx + s * 0.30, s * 0.02, line(shade, a, s * 0.055))
    # body + belly
    blob(c, -s * 0.02, -s * 0.20, s * 0.42, s * 0.19, body, a, rot=-0.06)
    blob(c, s * 0.02, -s * 0.13, s * 0.30, s * 0.09, belly, a * 0.85, rot=-0.05)
    # head
    hx = s * 0.44
    blob(c, hx, -s * 0.30, s * 0.24, s * 0.19, body, a)
    blob(c, hx + s * 0.06, -s * 0.24, s * 0.15, s * 0.10, belly, a * 0.5)
    # mouth
    if mouth > 0.02:
        mp = skia.Path()
        mp.moveTo(hx + s * 0.10, -s * 0.20)
        mp.quadTo(hx + s * 0.24, -s * 0.20 - s * 0.06 * mouth, hx + s * 0.30, -s * 0.24)
        c.drawPath(mp, line((70, 44, 40), a * 0.8, s * 0.028))
    # eyes: big domes with a glint
    er = s * 0.075 * eye
    for ex in (hx + s * 0.02, hx + s * 0.19):
        top = -s * 0.40
        c.drawCircle(ex, top, er * 1.25, P((250, 250, 240), a))
        c.drawCircle(ex, top - er * 0.1, er * 0.62, P(INK, a))
        c.drawCircle(ex + er * 0.18, top - er * 0.34, er * 0.20, P((255, 255, 255), a))
    # spine spots
    for i in range(3):
        c.drawCircle(-s * 0.30 + i * s * 0.16, -s * 0.31, s * 0.026, P(shade, a * 0.8))
    c.restore()


# ------------------------------------------------------------------ the pot, cut away
def pot_cut(c, x, y, w, h, a=1.0, water=0.0, stones=0, stone_r=None, rgb=(206, 132, 88),
            inner=(150, 92, 62), water_rgb=(116, 190, 218), rim=(228, 164, 116), wall=None):
    """The pot as a cut-away, seen from the side: the far wall behind, the near wall's cut edge as a
    band around the cavity, water inside and stones piled at the bottom. This is the shot the whole
    film turns on, so it has to read instantly even at 300 px wide."""
    h = float(h)
    r = stone_r or w * 0.055
    wall = wall if wall is not None else w * 0.085
    ytop = y - h

    def silhouette(half_top, half_belly, half_bot):
        p = skia.Path()
        p.moveTo(x - half_top, ytop)
        p.cubicTo(x - half_belly, y - h * 0.52, x - half_belly, y - h * 0.04, x - half_bot, y)
        p.lineTo(x + half_bot, y)
        p.cubicTo(x + half_belly, y - h * 0.04, x + half_belly, y - h * 0.52, x + half_top, ytop)
        p.close()
        return p

    outer = silhouette(w * 0.30, w * 0.52, w * 0.29)
    cavity_shape = silhouette(w * 0.30 - wall, w * 0.52 - wall, w * 0.29 - wall)
    c.drawPath(outer, P(rgb, a))                       # the near wall (clay), full silhouette
    # cavity: the inside of the pot, seen through the near wall
    cav = cavity_shape
    cav.offset(0, wall * 1.15)
    c.drawPath(cav, P(inner, a))
    c.save()
    c.clipPath(cav, skia.ClipOp.kIntersect, True)
    # water first, then the stones on top of it: a cut-away has to show both, so the stones read
    # as sitting *in* the water (slightly blue-shifted) instead of disappearing under it
    wy = y - h * water if water > 0 else y
    if water > 0:
        c.drawRect(skia.Rect.MakeXYWH(x - w, wy, w * 2, y - wy), P(water_rgb, a))
    if stones > 0:
        rng = __import__("numpy").random.default_rng(11)
        per_row = max(3, int(w * 0.80 / (r * 2.05)))
        for i in range(int(stones)):
            row, col = divmod(i, per_row)
            sx = x - w * 0.20 + col * (w * 0.40 / max(1, per_row - 1)) + (rng.random() - 0.5) * r * 0.6
            sy = y - r * (0.9 + row * 1.45)
            wet = sy > wy
            stone(c, sx, sy, r * (0.78 + rng.random() * 0.36), a=a * (0.92 if wet else 1.0),
                  rgb=(112, 132, 150) if wet else (126, 122, 128))
    if water > 0:
        c.drawRect(skia.Rect.MakeXYWH(x - w, wy, w * 2, h * 0.014), P((210, 242, 252), a * 0.95))
        for k in range(2):
            c.drawOval(skia.Rect.MakeXYWH(x - w * 0.24 + k * w * 0.26, wy + h * 0.055, w * 0.15, h * 0.014),
                       P((228, 248, 252), a * 0.5))
    c.restore()
    # cut edges: a darker lip around the cavity where the near wall was sliced
    c.drawPath(cav, line((116, 66, 44), a * 0.75, w * 0.012))
    # rim: a thin band of clay around the mouth, and the highlight down the outside
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.315, ytop - h * 0.030, w * 0.63, h * 0.062), P(rim, a))
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.315, ytop - h * 0.030, w * 0.63, h * 0.062), line((132, 78, 50), a * 0.45, w * 0.005))
    c.drawOval(skia.Rect.MakeXYWH(x - w * 0.215, y - h * 0.78, w * 0.055, h * 0.28), P((246, 206, 174), a * 0.22))




# ------------------------------------------------------------------ effects
def shimmer(c, x, y, w, h, t, a=1.0, n=6, rgb=(255, 250, 230)):
    """Heat haze: short wavy strokes rising off the ground (a cheat, but it reads as heat)."""
    import random
    for i in range(n):
        ph = t * 1.7 + i * 1.3
        sx = x + (i / max(1, n - 1) - 0.5) * w
        sy = y + (math.sin(ph) * 0.5 + 0.5) * h
        amp = w * 0.012
        p = skia.Path()
        p.moveTo(sx - w * 0.03, sy)
        p.quadTo(sx, sy - amp * 2, sx + w * 0.03, sy)
        c.drawPath(p, line(rgb, a * (0.20 + 0.22 * (0.5 + 0.5 * math.sin(ph * 1.7))), w * 0.006))


def heart(c, x, y, s, a=1.0, rgb=(236, 96, 120)):
    p = skia.Path()
    p.moveTo(x, y + s * 0.35)
    p.cubicTo(x - s * 0.95, y - s * 0.25, x - s * 0.42, y - s * 0.95, x, y - s * 0.42)
    p.cubicTo(x + s * 0.42, y - s * 0.95, x + s * 0.95, y - s * 0.25, x, y + s * 0.35)
    p.close()
    c.drawPath(p, P(rgb, a))


def burst(c, x, y, r, a=1.0, n=12, rgb=(252, 214, 96), rot=0.0):
    """A starburst behind a shout word."""
    p = skia.Path()
    for i in range(n * 2):
        ang = rot + math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.74
        (p.moveTo if i == 0 else p.lineTo)(x + math.cos(ang) * rr, y + math.sin(ang) * rr)
    p.close()
    c.drawPath(p, P(rgb, a))


def lightbulb(c, x, y, s, a=1.0, glow=1.0):
    """Idea bulb: a warm halo, the glass, the filament and the screw base."""
    if glow > 0:
        g = skia.GradientShader.MakeRadial(skia.Point(x, y - s * 0.1), s * 2.6,
                                           [skia.Color(255, 240, 170, int(190 * a * glow)),
                                            skia.Color(255, 236, 160, 0)])
        p = skia.Paint(); p.setShader(g)
        c.drawCircle(x, y - s * 0.1, s * 2.6, p)
    c.drawCircle(x, y - s * 0.55, s * 0.62, P((255, 246, 206), a))
    c.drawCircle(x, y - s * 0.55, s * 0.62, line((208, 168, 74), a, s * 0.06))
    c.drawRect(skia.Rect.MakeXYWH(x - s * 0.26, y + s * 0.02, s * 0.52, s * 0.34), P((186, 160, 124), a))
    for k in range(3):
        c.drawLine(x - s * 0.26, y + s * 0.10 + k * s * 0.10, x + s * 0.26, y + s * 0.10 + k * s * 0.10,
                   line((146, 122, 92), a, s * 0.035))
    pth = skia.Path()
    pth.moveTo(x - s * 0.16, y - s * 0.42)
    pth.lineTo(x, y - s * 0.18)
    pth.lineTo(x + s * 0.16, y - s * 0.42)
    c.drawPath(pth, line((240, 176, 60), a, s * 0.05))


def question_mark(c, x, y, s, a=1.0, rgb=(206, 88, 72)):
    p = skia.Path()
    p.addCircle(x, y - s * 0.62, s * 0.42, skia.PathDirection.kCW)
    p.addRect(skia.Rect.MakeXYWH(x - s * 0.10, y - s * 0.62, s * 0.20, s * 0.52))
    c.drawPath(p, P(rgb, a))
    c.drawCircle(x, y + s * 0.10, s * 0.135, P(rgb, a))
