"""THE LOUDEST SOUND: Krakatoa, 27 August 1883. 1080x1920, about 112 s, one camera, two sheets.

The board holds two printed sheets:

  the strait sheet   the Sunda Strait at 10 m coastlines (mercator), Krakatoa at its origin
  the globe sheet    azimuthal equidistant on Krakatoa, so every distance from the volcano is a
                     true radius: the 40 mile ring, the 3,000 mile ring, the seven passes of the
                     air wave, all circles on the sheet

The camera rises off the strait, sees both sheets on the board, and comes down on the globe. Every
hit is timed to a spoken word through doc.W(). World units are 4K px at zoom 1: a 1080-wide frame
at zoom z shows 3840/z x 6827/z world px, so screen px = world px * S * z with S = 1080/3840.
"""
import math
import pathlib
import sys

import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
import filmkit                                     # noqa: E402
filmkit.apply_patch()

from engine import (CREAM, HILITE, INK, RUST, BigText, Counter, Film, GeoMap, Glow, Item,  # noqa: E402
                    PaperDoc, PenMark, Plume, Print, Route, RingWave, Stamp, XMarker, draw_text,
                    ease_in_out, ease_out_cubic, paint, paper_fill, partial_path, ramp, text_width,
                    tile_image)

W_PX = 1080
S = W_PX / 3840.0
KM = 6371.0
STRAIT_K = 150000.0                 # world px per projection unit (mercator on the strait sheet)
STRAIT_PPK = STRAIT_K / KM          # world px per km on the strait sheet
GLOBE_K = 6500.0                    # world px per radian of arc on the globe sheet
GLOBE_PPK = GLOBE_K / KM            # world px per km on the globe sheet
S0 = (-8200.0, 0.0)                 # where the strait sheet sits on the board
G0 = (19000.0, 0.0)                 # where the globe sheet sits on the board
W0 = (-41000.0, 0.0)                # and the world chart, far out on the other side

# palette: a 19th century chart in ink on toned paper, lit warm
C = dict(paper=(208, 190, 152), sea_a=(34, 70, 80), sea_b=(58, 100, 102), deep=(14, 36, 50),
         land=(200, 176, 132), line=(104, 76, 46), frame=(96, 74, 50), ink=(52, 40, 28))
CREAM2 = (246, 234, 208)
GOLD = (250, 214, 156)


def s2w(px, z):
    return px / (S * z)


def at(xy, dx, dy, z):
    x, y = (xy.x, xy.y) if hasattr(xy, "x") else xy
    k = s2w(1.0, z)
    return (x + dx * k, y + dy * k)


def txt(c, res, text, xy, z, size_px, font="cond", rgb=CREAM2, a=1.0, track=0.20, align="center"):
    draw_text(c, res, text, xy[0], xy[1], s2w(size_px, z), font, rgb, a, track, align)


# ------------------------------------------------------------------ items
class AtlasSheet(GeoMap):
    """A printed hydrographic sheet: toned paper, deep water, relief land, graticule, rings, compass.

    `rings` are true circle distances in km from `ring_place` (Krakatoa), so on the azimuthal sheet
    they are the distances they claim to be.
    """
    cache_res = 1.0
    LOOK = dict(paper=C["paper"], frame=C["frame"], relief=0.26)

    def __init__(self, data, K, origin=(0, 0), rings=(), ring_rgb=(158, 52, 34), ink=C["ink"],
                 title=None, sub=None, scale_km=None, compass=True, t_in=-1):
        super().__init__(data, K, origin, dict(self.LOOK), t_in)
        self.ring_km = list(rings)
        self.ppk = K / KM
        self.ring_rgb, self.ink_rgb = ring_rgb, ink
        self.title, self.sub, self.scale_km, self.compass = title, sub, scale_km, compass
        self.grid = {n: p for n, p in self.region_paths.items() if n.startswith("_grid")}
        ref = data.get("ring_place", "Krakatoa")
        self.centre = self.place(ref) if ref in data.get("places", {}) else (origin[0], origin[1])

    def _draw(self, c, res):
        L = self.look
        r = self.sheet()
        inner = r.makeInset(52, 52)
        cx, cy = self.centre

        c.drawRect(r.makeOffset(24, 40), paint((0, 0, 0), 0.66, blur=52))
        c.drawRect(r, paint(L["paper"]))
        paper_fill(c, res, r, 0.55, 1.0, skia.BlendMode.kMultiply)

        # water: a vertical wash, a light bloom round the volcano, a dark rim
        c.save(); c.clipRect(inner)
        g = skia.GradientShader.MakeLinear([skia.Point(cx, inner.top()), skia.Point(cx, inner.bottom())],
                                           [paint(C["sea_a"]).getColor(), paint(C["sea_b"]).getColor()])
        p = skia.Paint(); p.setShader(g); c.drawRect(inner, p)
        gr = skia.GradientShader.MakeRadial(skia.Point(cx, cy), max(inner.width(), inner.height()) * 0.62,
                                            [paint((132, 196, 190), 0.20).getColor(),
                                             paint((120, 170, 170), 0.02).getColor(),
                                             paint(C["deep"], 0.72).getColor()], [0.0, 0.34, 1.0])
        p = skia.Paint(); p.setShader(gr); c.drawRect(inner, p)
        paper_fill(c, res, inner, 0.34, 1.5, skia.BlendMode.kMultiply)
        c.restore()

        # land, relief, coast
        for path in self.region_paths.values():
            if path in self.grid.values():
                continue
            c.drawPath(path, paint(C["land"]))
        c.save(); c.clipRect(inner)
        c.save(); c.clipPath(self.path, skia.ClipOp.kIntersect, True)
        rp = skia.Paint(AntiAlias=True); rp.setBlendMode(skia.BlendMode.kOverlay); rp.setAlphaf(L["relief"])
        tile_image(c, res.image("relief.png", 1024), inner, self.relief_tile, rp)
        c.restore()
        for path in self.region_paths.values():
            if path in self.grid.values():
                continue
            c.drawPath(path, paint((168, 140, 96), 0.55, stroke=30, blur=22))
        for path in self.region_paths.values():
            if path in self.grid.values():
                continue
            c.drawPath(path, paint(C["line"], 0.95, stroke=3.2))
        c.restore()

        # graticule, then the distance rings
        gp = paint(self.ink_rgb, 0.30, stroke=2.0)
        for path in self.grid.values():
            c.drawPath(path, gp)
        c.save(); c.clipRect(inner)
        for km in self.ring_km:
            rr = km * self.ppk
            c.drawCircle(cx, cy, rr, paint(self.ring_rgb, 0.55, stroke=4.0))
            c.drawCircle(cx, cy, rr, paint(self.ring_rgb, 0.14, stroke=14, blur=7))
        c.restore()

        # furniture
        c.drawRect(inner, paint(C["frame"], 0.55, stroke=3.0))
        c.drawRect(r.makeInset(18, 18), paint(C["frame"], 0.32, stroke=1.5))
        self._ticks(c, r)
        if self.compass:
            self._compass(c, inner.right() - inner.width() * 0.07, inner.top() + inner.height() * 0.075,
                          inner.width() * 0.026)
        if self.scale_km:
            self._scale(c, inner.left() + inner.width() * 0.055, inner.bottom() - inner.height() * 0.05,
                        self.scale_km, inner.width() * 0.24)
        if self.title:
            draw_text(c, res, self.title, inner.centerX(), inner.top() + inner.height() * 0.046,
                      inner.width() * 0.0225, "cond", self.ink_rgb, 0.90, 0.30, "center")
            if self.sub:
                draw_text(c, res, self.sub, inner.centerX(), inner.top() + inner.height() * 0.069,
                          inner.width() * 0.0115, "mono", self.ink_rgb, 0.75, 0.22, "center")

    def _ticks(self, c, r):
        p = paint(C["frame"], 0.5, stroke=2.0)
        for i in range(1, 24):
            x = r.left() + r.width() * i / 24
            h = 22 if i % 2 == 0 else 12
            c.drawLine(x, r.top() + 18, x, r.top() + 18 + h, p)
            c.drawLine(x, r.bottom() - 18, x, r.bottom() - 18 - h, p)
        for i in range(1, 32):
            y = r.top() + r.height() * i / 32
            h = 22 if i % 2 == 0 else 12
            c.drawLine(r.left() + 18, y, r.left() + 18 + h, y, p)
            c.drawLine(r.right() - 18, y, r.right() - 18 - h, y, p)

    def _compass(self, c, x, y, k):
        col = self.ink_rgb
        c.drawCircle(x, y, k, paint(col, 0.40, stroke=2.2))
        for i in range(8):
            a = i * math.pi / 4
            ln = k * (1.0 if i % 2 == 0 else 0.5)
            c.drawLine(x, y, x + math.sin(a) * ln, y - math.cos(a) * ln,
                       paint(col, 0.55, stroke=2.4 if i % 2 == 0 else 1.2))
        self._label(c, "N", (x, y - k * 1.42), k * 1.1)

    def _scale(self, c, x, y, km, width):
        col = self.ink_rgb
        wpx = km * self.ppk
        for i in range(6):
            c.drawRect(skia.Rect.MakeXYWH(x + wpx * i / 6, y, wpx / 6, width * 0.10),
                       paint(col, 0.8 if i % 2 == 0 else 0.10))
        self._label(c, f"{km:,} KM", (x + wpx / 2, y - width * 0.10), width * 0.10)

    def _label(self, c, text, xy, size):
        draw_text(c, _RES[0], text, xy[0], xy[1], size, "mono", self.ink_rgb, 0.75, 0.16, "center")


_RES = [None]


class Inset(Item):
    """A chart inset: a bordered panel on the sheet for what is off its edge, with its own heading."""
    z = 9

    def __init__(self, x, y, w, h, t_in, heading, sub=None, rot=0.0, t_out=None, sfx=False):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.h, self.heading, self.sub, self.rot = x, y, w, h, heading, sub, rot
        self.box = skia.Rect.MakeXYWH(x - w * 1.4, y - h * 0.6, w * 2.6, h * 1.5)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = ease_out_cubic(ramp(t, self.t_in, 0.8)) * self.fade(t)
        if a <= 0:
            return
        c.save(); c.translate(self.x, self.y); c.rotate(self.rot)
        r = skia.Rect.MakeXYWH(-self.w / 2, -self.h / 2, self.w, self.h)
        c.drawRect(r.makeOffset(10, 18), paint((0, 0, 0), 0.55 * a, blur=26))
        c.drawRect(r, paint((214, 198, 164), 0.97 * a))
        paper_fill(c, res, r, 0.5 * a, 1.0, skia.BlendMode.kMultiply)
        c.drawRect(r, paint(C["frame"], 0.75 * a, stroke=max(2.0, self.w * 0.004)))
        c.drawRect(r.makeInset(self.w * 0.014, self.w * 0.014), paint(C["frame"], 0.4 * a,
                                                                       stroke=max(1.2, self.w * 0.002)))
        hh = self.w * 0.036
        draw_text(c, res, self.heading, 0, -self.h / 2 + hh * 1.5, hh, "cond", C["ink"], 0.9 * a, 0.28, "center")
        if self.sub:
            draw_text(c, res, self.sub, 0, -self.h / 2 + hh * 2.5, hh * 0.52, "mono", C["ink"], 0.75 * a, 0.16, "center")
        c.restore()


class Labels(Item):
    """Place names and small annotations, each with its own time, side and colour."""
    z = 34

    def __init__(self, labels, t_in=0.0, t_out=None, sfx=False):
        super().__init__(t_in, t_out, None, sfx)
        self.labels = labels
        box = None
        for lab in labels:
            x, y = lab[1]
            r = skia.Rect.MakeLTRB(x - 3000, y - 500, x + 3000, y + 500)
            box = r if box is None else skia.Rect.MakeLTRB(min(box.left(), r.left()), min(box.top(), r.top()),
                                                           max(box.right(), r.right()), max(box.bottom(), r.bottom()))
        self.box = box

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        for lab in self.labels:
            text, xy, side, t_on, size_px = lab[:5]
            z = lab[5] if len(lab) > 5 else 1.0
            rgb = lab[6] if len(lab) > 6 else CREAM2
            a = ramp(t, t_on, 0.6) * self.fade(t)
            if a <= 0:
                continue
            draw_text(c, res, text, xy[0], xy[1], s2w(size_px, z), "cond", rgb, 0.94 * a, 0.20,
                      "right" if side == "left" else "left" if side == "right" else "center")


class Trace(Item):
    """An instrument trace drawn left to right: barograph spikes, a falling temperature."""
    z = 47

    def __init__(self, x, y, w, h, t_in, dur=1.2, rgb=(148, 34, 26), width=None, pts=(), spike=None,
                 baseline=0.5, t_out=None, grid=True, paper=True, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.h = x, y, w, h
        self.rgb, self.dur, self.baseline, self.grid, self.paper = rgb, dur, baseline, grid, paper
        self.wd = width or h * 0.035
        self.pts, self.spike = list(pts), spike
        self.box = skia.Rect.MakeXYWH(x - w * 1.4, y - h * 0.6, w * 2.6, h * 1.5)

    def bounds(self, res):
        return self.box

    def cues(self):
        return [("pencil", self.t_in, 0.45, {"dur": round(self.dur, 2)})]

    def draw(self, c, res, t):
        u = ease_in_out(ramp(t, self.t_in, self.dur))
        a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        x0, x1, y0, y1 = self.x - self.w / 2, self.x + self.w / 2, self.y - self.h / 2, self.y + self.h / 2
        if self.paper:
            c.drawRect(skia.Rect.MakeLTRB(x0 - self.h * 0.10, y0 - self.h * 0.10, x1 + self.h * 0.10, y1 + self.h * 0.10),
                       paint((0, 0, 0), 0.45 * a, blur=self.h * 0.05))
            c.drawRect(skia.Rect.MakeLTRB(x0 - self.h * 0.10, y0 - self.h * 0.10, x1 + self.h * 0.10, y1 + self.h * 0.10),
                       paint((226, 214, 188), 0.96 * a))
        if self.grid:
            gp = paint((120, 100, 70), 0.20 * a, stroke=1.5)
            for i in range(1, 6):
                yy = y0 + self.h * i / 6
                c.drawLine(x0, yy, x1, yy, gp)
            for i in range(1, 8):
                xx = x0 + self.w * i / 8
                c.drawLine(xx, y0, xx, y1, gp)
        p = skia.Path()
        n = 260
        for i in range(n + 1):
            f = i / n
            if f > u:
                break
            v = self.baseline
            for (px, pv, pw) in self.pts:
                v -= pv * math.exp(-((f - px) / pw) ** 2)
            if self.spike:
                sx, sa, sw = self.spike
                v -= sa * math.exp(-((f - sx) / sw) ** 2)
                if abs(f - sx) < 4 * sw:
                    v += 0.18 * sa * math.exp(-((f - sx) / (sw * 2.2)) ** 2) * math.sin((f - sx) / sw * 6.0)
            yy = self.y - (v - 0.5) * self.h
            (p.moveTo if i == 0 else p.lineTo)(x0 + self.w * f, yy)
        if u > 0.004:
            c.drawPath(p, paint(self.rgb, 0.94 * a, stroke=self.wd))
            pm = skia.PathMeasure(p, False)
            pos = pm.getPosTan(pm.getLength())
            if pos:
                c.drawCircle(pos[0].x(), pos[0].y(), self.wd * 2.2, paint((70, 20, 14), 0.95 * a))


class Dip(Item):
    """A dip to near-black: hides a camera move the board cannot make in one shot."""
    z = 120

    def __init__(self, xy, t_in, hold, rise=0.5, fall=0.55, rgb=(7, 5, 4)):
        super().__init__(t_in, None, None, False)
        self.x, self.y, self.hold = xy[0], xy[1], hold
        self.rise, self.fall, self.rgb = rise, fall, rgb

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, self.rise) * (1 - ramp(t, self.t_in + self.hold, self.fall))
        if a <= 0.002:
            return
        c.drawRect(skia.Rect.MakeXYWH(self.x - 200000, self.y - 200000, 400000, 400000),
                   paint(self.rgb, min(1.0, a)))


class WaveBar(Item):
    """100 ft of water, drawn as a measured column against the coast, ticked every 25 ft."""
    z = 45

    def __init__(self, xy, h, t_in, t_out=None, z=1.0, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.h, self.z = xy[0], xy[1], h, z
        self.wd = s2w(92, z)
        self.box = skia.Rect.MakeXYWH(self.x - self.wd * 4, self.y - h * 1.4, self.wd * 8, h * 1.6)

    def bounds(self, res):
        return self.box

    def cues(self):
        return [("pop", self.t_in, 0.4, {})]

    def draw(self, c, res, t):
        u = ease_out_cubic(ramp(t, self.t_in, 0.8))
        a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        hh = self.h * u
        rect = skia.Rect.MakeXYWH(self.x - self.wd / 2, self.y - hh, self.wd, hh)
        g = skia.GradientShader.MakeLinear([skia.Point(rect.left(), rect.top()), skia.Point(rect.left(), self.y)],
                                           [paint((196, 232, 234)).getColor(), paint((74, 132, 148)).getColor(),
                                            paint((40, 84, 102)).getColor()], [0.0, 0.5, 1.0])
        pw = skia.Paint(); pw.setShader(g); pw.setAlphaf(0.88 * a)
        c.drawRect(rect, pw)
        c.drawRect(rect.makeOffset(self.wd * 0.9, 0), paint((0, 0, 0), 0.30 * a, blur=self.wd * 0.5))
        c.drawRect(rect, paint((250, 254, 254), 0.55 * a, stroke=max(2.5, self.wd * 0.05)))
        for i in range(1, 9):
            yy = self.y - hh * i / 8
            ln = 0.95 if i % 2 == 0 else 0.55
            c.drawLine(self.x - self.wd * (0.5 + ln), yy, self.x - self.wd * 0.5, yy,
                       paint(CREAM2, 0.8 * a, stroke=2.6 if i % 2 == 0 else 1.6))
        # a foam head: the water is moving
        for k in range(9):
            xx = self.x - self.wd / 2 + self.wd * (k + 0.5) / 7
            c.drawCircle(xx, self.y - hh, self.wd * 0.16, paint((246, 252, 252), 0.55 * a, blur=self.wd * 0.10))
        c.drawLine(self.x - self.wd * 0.8, self.y, self.x + self.wd * 1.0, self.y, paint(CREAM2, 0.9 * a, stroke=4))
        # a house at the foot, for scale: 25 ft to the roof
        hx, hs = self.x + self.wd * 1.45, self.h * 0.25
        c.drawRect(skia.Rect.MakeXYWH(hx, self.y - hs, hs * 0.85, hs), paint((52, 44, 36), 0.9 * a))
        roof = skia.Path(); roof.moveTo(hx - hs * 0.10, self.y - hs); roof.lineTo(hx + hs * 0.42, self.y - hs * 1.45)
        roof.lineTo(hx + hs * 0.95, self.y - hs); roof.close()
        c.drawPath(roof, paint((52, 44, 36), 0.9 * a))


class SunsetPlate(Item):
    """A pastel sky drawn as bands, after the Chelsea sketches of November 1883: a dark pillar of
    afterglow standing over a low horizon, the river catching it. Drawn, not photographed."""
    z = 34

    def __init__(self, x, y, w, h, t_in, t_out=None, rot=-1.2, seed=41):
        super().__init__(t_in, t_out, None, False)
        self.x, self.y, self.w, self.h, self.rot = x, y, w, h, rot
        self.seed = seed
        self.box = skia.Rect.MakeXYWH(x - w, y - h, w * 2, h * 2)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.7) * self.fade(t)
        if a <= 0:
            return
        u = ease_out_cubic(ramp(t, self.t_in, 1.6))
        w, h = self.w, self.h
        c.save()
        c.translate(self.x, self.y); c.rotate(self.rot)
        plate = skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h)
        pad = w * 0.045
        c.drawRect(plate.makeOffset(14, 22), paint((0, 0, 0), 0.55 * a, blur=26))
        c.drawRect(plate, paint((238, 230, 212), 1.0 * a))
        inner = plate.makeInset(pad, pad)
        c.save(); c.clipRect(inner)
        # sky: a graded wash that goes olive at the top and rose at the horizon
        g = skia.GradientShader.MakeLinear(
            [skia.Point(0, inner.top()), skia.Point(0, inner.bottom())],
            [paint((86, 92, 78), 1.0).getColor(), paint((196, 150, 92), 1.0).getColor(),
             paint((238, 176, 112), 1.0).getColor(), paint((226, 132, 96), 1.0).getColor(),
             paint((120, 96, 92), 1.0).getColor()], [0.0, 0.34, 0.56, 0.70, 1.0])
        ps = skia.Paint(); ps.setShader(g); ps.setAlphaf(a)
        c.drawRect(inner, ps)
        # the afterglow pillar: the ash cloud lit from below, drawn as soft rising lobes
        rng = filmkit._noise(self.seed, 150)
        for i in range(150):
            v = i / 150
            yy = inner.bottom() - inner.height() * (0.30 + 0.52 * v) * u
            spread = inner.width() * (0.06 + 0.20 * v ** 0.8)
            xx = inner.centerX() + (rng[i] - 0.5) * spread * 0.9
            rr = inner.width() * (0.045 + 0.10 * rng[(i + 17) % 150]) * (0.5 + v)
            tone = (236, 132, 84) if v < 0.45 else (214, 152, 128) if v < 0.75 else (150, 128, 124)
            c.drawCircle(xx, yy, rr, paint(tone, 0.20 * a * u, blur=rr * 0.7))
        # the streaks: pastel bands drawn horizontally, the way the sketches are built
        for i in range(46):
            v = rng[(i * 3) % 150]
            yy = inner.top() + inner.height() * v
            thick = inner.height() * (0.002 + 0.012 * rng[(i + 5) % 150])
            tone = ((246, 196, 150) if v < 0.55 else (188, 132, 108)) if i % 3 else (150, 130, 110)
            x0 = inner.left() + inner.width() * rng[(i + 9) % 150] * 0.45
            x1 = x0 + inner.width() * (0.25 + 0.5 * rng[(i + 23) % 150])
            c.drawOval(skia.Rect.MakeLTRB(x0, yy, x1, yy + thick), paint(tone, 0.14 * a * u, blur=thick * 2.2))
        # the river, and its reflection
        hz = inner.bottom() - inner.height() * 0.17
        c.drawRect(skia.Rect.MakeLTRB(inner.left(), hz, inner.right(), inner.bottom()),
                   paint((64, 70, 74), 0.72 * a))
        for i in range(20):
            v = rng[(i * 7) % 150]
            yy = hz + (inner.bottom() - hz) * v
            c.drawLine(inner.left() + inner.width() * rng[(i + 3) % 150] * 0.3, yy,
                       inner.right() - inner.width() * rng[(i + 11) % 150] * 0.3, yy,
                       paint((222, 150, 112), 0.22 * a * u, stroke=inner.height() * 0.004 * (1 + v)))
        # the far bank: a dark line of roofs and a mast
        bank = skia.Path(); bank.moveTo(inner.left(), hz)
        for i in range(24):
            xx = inner.left() + inner.width() * i / 23
            bank.lineTo(xx, hz - inner.height() * (0.006 + 0.014 * rng[(i + 31) % 150]))
        bank.lineTo(inner.right(), hz); bank.close()
        c.drawPath(bank, paint((38, 34, 34), 0.85 * a))
        c.drawLine(inner.centerX() - inner.width() * 0.18, hz, inner.centerX() - inner.width() * 0.18,
                   hz - inner.height() * 0.20, paint((38, 34, 34), 0.8 * a, stroke=max(1.5, w * 0.006)))
        c.restore()
        c.drawRect(inner, paint((74, 62, 50), 0.35 * a, stroke=max(1.2, w * 0.004)))
        c.restore()


class ColumnCard(Item):
    """A cut-away plate of the column: dark stock, the trunk on the left, a ruled key on the right."""
    z = 44

    def __init__(self, x, y, w, h, t_in, marks, t_out=None, heading="THE COLUMN", sub=None):
        super().__init__(t_in, t_out, None, False)
        self.x, self.y, self.w, self.h, self.marks = x, y, w, h, marks
        self.heading, self.sub = heading, sub
        self.box = skia.Rect.MakeXYWH(x - w * 1.7, y - h * 1.3, w * 3.6, h * 1.5)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.6) * self.fade(t)
        if a <= 0:
            return
        x, y, w, h = self.x, self.y, self.w, self.h
        cx = x - w * 0.34
        plate = skia.Rect.MakeLTRB(x - w * 1.34, y - h * 1.44, x + w * 1.02, y + h * 0.14)
        c.drawRect(plate.makeOffset(10, 16), paint((0, 0, 0), 0.58 * a, blur=24))
        c.drawRect(plate, paint((27, 22, 19), 0.95 * a))
        # the stock: a dark ground and a hatch, so the plate reads as printed, not as fog
        c.drawRect(plate.makeInset(5, 5), paint((152, 124, 86), 0.42 * a, stroke=max(1.3, w * 0.006)))
        c.save(); c.clipRect(plate.makeInset(5, 5))
        step = max(5.0, w * 0.035)
        yy = plate.top() - plate.height()
        while yy < plate.bottom() + plate.height():
            c.drawLine(plate.left() - w, yy, plate.right() + w, yy - plate.width() * 0.55,
                       paint((196, 168, 126), 0.055 * a, stroke=1.6))
            yy += step
        c.restore()
        c.drawRect(plate.makeInset(5, 5), paint((20, 16, 14), 0.30 * a))

        # the column: a trunk that widens with height, then the cloud at the top
        rng = filmkit._noise(23, 130)
        c.save(); c.clipRect(plate.makeInset(6, 6))
        for i in range(130):
            u = i / 130
            yy = y - h * (u ** 0.88) * 0.80
            wob = (rng[i] - 0.5) * w * 0.34 * (0.08 + u)
            # trunk pinches above the vent, then the cloud spreads into an umbrella
            prof = 0.085 + 0.30 * max(0.0, (u - 0.34) / 0.66) ** 2.1 + 0.16 * u ** 5
            rr = w * prof * (0.78 + 0.48 * rng[(i + 11) % 130])
            if u < 0.09:
                col = (252, 214, 150)
            elif u < 0.27:
                col = (238, 158, 84)
            elif u < 0.48:
                col = (150, 118, 104)
            elif u < 0.72:
                col = (126, 124, 122)
            else:
                col = (172, 180, 182)
            c.drawCircle(cx + wob, yy, rr, paint(col, 0.60 * a, blur=rr * 0.34))
        # the cap: wisps of ash peeling off the umbrella, so the cloud has an edge
        rng2 = filmkit._noise(71, 96)
        for i in range(96):
            ang = -math.pi * (0.06 + 0.88 * rng2[i])
            rad = w * (0.42 + 0.30 * rng2[(i + 31) % 96])
            cxp = cx + math.cos(ang) * rad * 0.92
            cyp = y - h * 0.845 + math.sin(ang) * rad * 0.30
            rw = w * (0.05 + 0.10 * rng2[(i + 7) % 96])
            c.drawOval(skia.Rect.MakeXYWH(cxp - rw, cyp - rw * 0.42, rw * 2, rw * 0.84),
                       paint((150, 154, 156), 0.16 * a, blur=rw * 0.5))
        c.restore()

        for frac, text in self.marks:
            yy = y - h * frac * 0.80
            c.drawLine(x - w * 0.98, yy, x - w * 0.10, yy, paint((236, 224, 200), 0.30 * a,
                                                                 stroke=max(1.2, w * 0.006)))
            c.drawLine(x - w * 0.10, yy, x + w * 0.02, yy, paint((236, 224, 200), 0.55 * a,
                                                                stroke=max(1.2, w * 0.006)))
            draw_text(c, res, text, x + w * 0.06, yy + h * 0.012, h * 0.030, "mono",
                      (242, 230, 206), 0.94 * a, 0.12, align="left")
        c.drawLine(x - w * 0.98, y, x + w * 0.02, y, paint((236, 224, 200), 0.76 * a,
                                                           stroke=max(2.0, w * 0.010)))
        draw_text(c, res, "SEA LEVEL", x + w * 0.06, y + h * 0.010, h * 0.026, "mono",
                  (232, 216, 190), 0.8 * a, 0.12, align="left")

        draw_text(c, res, self.heading, x - w * 1.30, y - h * 1.56, h * 0.038, "cond",
                  (246, 234, 210), 0.96 * a, 0.20, align="left")
        if self.sub:
            draw_text(c, res, self.sub, x - w * 1.30, y - h * 1.485, h * 0.025, "mono",
                      (228, 208, 180), 0.85 * a, 0.14, align="left")


class Cone(Item):
    """The child cone rising out of the caldera, drawn as a marked profile."""
    z = 42

    def __init__(self, x, y, w, h, t_in, t_out=None):
        super().__init__(t_in, t_out, None, False)
        self.x, self.y, self.w, self.h = x, y, w, h
        self.box = skia.Rect.MakeXYWH(x - w, y - h * 1.4, w * 2, h * 1.8)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        u = ease_out_cubic(ramp(t, self.t_in, 1.8))
        a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        h = self.h * u
        p = skia.Path()
        p.moveTo(self.x - self.w / 2, self.y)
        p.lineTo(self.x - self.w * 0.11, self.y - h * 0.80)
        p.lineTo(self.x, self.y - h)
        p.lineTo(self.x + self.w * 0.13, self.y - h * 0.78)
        p.lineTo(self.x + self.w / 2, self.y)
        p.close()
        c.drawPath(p, paint((46, 38, 34), 0.95 * a))
        c.drawPath(p, paint((244, 178, 120), 0.60 * a, stroke=max(3.0, self.w * 0.014)))
        if u > 0.8:
            k = (u - 0.8) / 0.2
            c.drawCircle(self.x, self.y - h, self.w * 0.055, paint((255, 176, 84), 0.9 * k * a, blur=self.w * 0.04))


class Caldera(Item):
    """A dashed outline over water where the island was."""
    z = 41

    def __init__(self, pts, t_in, dur=1.1, rgb=(196, 66, 42), width=None, t_out=None, z=3.0, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.rgb, self.dur = rgb, dur
        self.wd = width or s2w(7, z)
        p = skia.Path(); p.moveTo(*pts[0])
        for a, b in zip(pts[1:], pts[2:]):
            p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        p.lineTo(*pts[-1]); p.close()
        self.p = p
        self.box = p.getBounds().makeOutset(600, 600)

    def bounds(self, res):
        return self.box

    def cues(self):
        return [("pencil", self.t_in, 0.5, {"dur": round(self.dur, 2)})]

    def draw(self, c, res, t):
        u = ease_in_out(ramp(t, self.t_in, self.dur))
        a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        pa = paint(self.rgb, 0.9 * a, stroke=self.wd)
        pa.setPathEffect(skia.DashPathEffect.Make([self.wd * 7, self.wd * 5], 0))
        c.drawPath(partial_path(self.p, u), pa)


class WaveBands(Item):
    """The sea coming ashore: bands sweeping out of the strait and piling up on the coast."""
    z = 44

    def __init__(self, x, y, t_in, r_end, n=4, dur=2.6, rgb=(206, 238, 240), t_out=None, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.r_end, self.n, self.dur, self.rgb = x, y, r_end, n, dur, rgb
        self.box = skia.Rect.MakeXYWH(x - r_end, y - r_end, r_end * 2, r_end * 2)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = self.fade(t)
        if a <= 0:
            return
        for i in range(self.n):
            u = ramp(t, self.t_in + i * self.dur * 0.26, self.dur * 0.7)
            if u <= 0 or u >= 1:
                continue
            r = self.r_end * (0.22 + 0.78 * u)
            al = 0.7 * (1 - u) ** 0.7 * a
            c.drawCircle(self.x, self.y, r, paint(self.rgb, al * 0.55, stroke=30 + 50 * (1 - u), blur=10))
            c.drawCircle(self.x, self.y, r * 0.985, paint((255, 255, 250), al * 0.6, stroke=7))


class BoardTitle(Item):
    """A lockup set straight on the board."""
    z = 50

    def __init__(self, x, y, t_in, lines, rgb=CREAM2, sfx=False):
        super().__init__(t_in, None, None, sfx)
        self.x, self.y, self.lines, self.rgb = x, y, lines, rgb
        self.box = skia.Rect.MakeXYWH(x - 9000, y - 4000, 18000, 8000)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        yy = self.y
        for text, size, font, dt, track in self.lines:
            a = ramp(t, self.t_in + dt, 0.9)
            if a > 0:
                draw_text(c, res, text, self.x, yy, size, font, self.rgb, a * 0.95, track, "center")
            yy += size * 1.22


# ------------------------------------------------------------------ build
def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    res = doc.res()
    film = Film(doc.duration, fps=30, look=dict(
        board="cork_dark.png", bg=(16, 12, 9), grain=0.030, glow=0.32, vignette=0.55, curve=0.26, dim=(6, 5, 5),
        grade3=((1.05, 0.014, -0.014), (0.006, 1.006, 0.004), (-0.026, 0.012, 0.975))))
    film.fade_in, film.fade_out = 1.2, 2.6

    strait = film.add(AtlasSheet(doc.map("strait"), STRAIT_K, S0, rings=(64,),
                                 title="KAART VAN DEN SUNDA STRAAT",
                                 sub="OPGENOMEN 1883 · ZEEMIJLEN", scale_km=25))
    world = film.add(AtlasSheet(doc.map("world"), 2000.0, W0, rings=(),
                                title="THE WORLD · 27 AUGUST 1883",
                                sub="STATIONS AND THE AIR WAVE", scale_km=4000))
    _RES[0] = res

    P = {}
    for nm in ("Krakatoa", "Batavia", "Merak", "Anyer", "Teluk Betung", "Sebesi", "Ketimbang"):
        P[nm] = strait.place(nm)
    for nm in ("London", "New York", "Washington", "Marseille", "Suez", "Aden", "Colombo", "Calcutta",
               "Singapore", "Batavia", "Krakatoa", "Rodrigues", "Mauritius", "Perth", "Cape Town",
               "Tokyo", "Bombay", "Cairo", "Hong Kong", "Sydney"):
        P["w_" + nm] = world.place(nm)
    k = P["Krakatoa"]
    wk = P["w_Krakatoa"]
    wl, wn = P["w_London"], P["w_New York"]

    # ================================================================= 1-2  the strait, the blast
    film.add(Glow(k[0], k[1], s2w(420, 0.42), t_in=L(1) + 0.5, rgb=(255, 150, 70), a=0.45, pulse=0.06, z=33))
    film.add(Plume(k[0], k[1], 0.2, rise=s2w(300, 0.42), spread=s2w(70, 0.42), count=180, rate=1.6,
                   size=s2w(9, 0.42), speed=0.9, turb=1.6, kind="ash", z=39))
    plume_t = W(2, "blast") - 0.45
    film.add(Glow(k[0], k[1], s2w(300, 0.86), t_in=plume_t, rgb=(255, 142, 62), a=0.62, pulse=0.14, z=33))
    film.add(Plume(k[0], k[1], plume_t, rise=s2w(900, 0.86), spread=s2w(200, 0.86), count=420, rate=1.4,
                   size=s2w(16, 0.86), speed=0.9, turb=1.1, kind="fire", z=39))
    film.add(Plume(k[0], k[1], plume_t + 0.35, rise=s2w(1700, 0.86), spread=s2w(430, 0.86), count=520, rate=2.4,
                   size=s2w(34, 0.86), speed=0.45, turb=1.5, kind="ash", z=38))
    film.add(RingWave(k[0], k[1], W(2, "blast"), r_end=s2w(700, 0.86), dur=1.5, width=s2w(12, 0.86),
                      rings=2, gap=0.3, rgb=(255, 238, 214), a=0.9))
    film.add(Labels([
        ("KRAKATOA", at(k, -40, 10, 0.42), "left", L(1) + 1.0, 20, 0.42),
        ("JAVA", at(k, 420, 300, 0.42), "center", L(1) + 2.6, 19, 0.42, (228, 208, 172)),
        ("SUMATRA", at(k, -460, -60, 0.42), "center", L(1) + 3.3, 19, 0.42, (228, 208, 172)),
        ("SUNDA STRAIT", at(k, 0, -250, 0.42), "center", L(1) + 4.0, 16, 0.42, (210, 226, 224)),
    ], t_out=E(3)))
    film.add(Labels([("JAVA", at(k, 520, 170, 0.86), "center", L(1) + 2.6, 19, 0.86, (232, 212, 176)),
                     ("SUMATRA", at(k, -520, -120, 0.86), "center", L(1) + 3.3, 19, 0.86, (232, 212, 176))],
                    t_out=E(3)))
    tcam = at(k, 235, 10, 0.86)
    film.add(BigText("27 AUGUST 1883", *at(tcam, 0, -160, 0.86), s2w(28, 0.86), t_in=L(2) + 0.15, font="serifb",
                     rgb=CREAM2, track=0.16, type_on=0.8, t_out=E(4) + 0.9))
    film.add(BigText("10:02", *at(tcam, 0, -76, 0.86), s2w(72, 0.86), t_in=W(2, "blast"), font="cond",
                     rgb=(252, 246, 228), track=0.02, hit=1.0, t_out=E(4) + 0.9))
    lid = film.add(Print("P_LITHO", *at(k, 250, 320, 0.86), s2w(290, 0.86), rot=-2.2,
                         t_in=W(2, "loudest") - 0.3, t_out=E(4) + 0.7, z=32))
    lid.dim = None
    film.add(Labels([("ROYAL SOCIETY PLATE · 1888", at(k, 250, 320, 0.86), "center", W(2, "loudest") + 0.4,
                      12, 0.86, (232, 214, 184))], t_out=E(4) + 0.7))

    # 3  forty miles;  4  Batavia and the trace
    film.add(RingWave(k[0], k[1], W(3, "forty") - 0.3, r_end=64 * STRAIT_PPK, dur=1.6, width=s2w(9, 1.5),
                      rings=2, gap=0.4, rgb=(255, 228, 192), a=0.6))
    film.add(Labels([("40 MILES", at(k, 64 * STRAIT_PPK * 0.62, -64 * STRAIT_PPK * 0.62, 1.5), "right",
                      W(3, "forty"), 26, 1.5, GOLD),
                     ("NORHAM CASTLE", at(k, 64 * STRAIT_PPK * 0.72, -64 * STRAIT_PPK * 0.72, 1.5), "right",
                      W(3, "broke"), 15, 1.5, (238, 220, 190))], t_out=E(4) + 0.5))
    film.add(Stamp("EARDRUMS BURST", *at(k, -330, 300, 1.5), s2w(26, 1.9), rot=-7, t_in=W(3, "eardrums"),
                   t_out=E(4) + 0.3, rgb=(176, 34, 26)))
    film.add(XMarker(P["Batavia"][0], P["Batavia"][1], None, t_in=L(4) - 0.2, t_out=E(4) + 0.6, size=0.5))
    bcam = at(P["Batavia"], -200, -300, 0.95)
    film.add(PaperDoc(*bcam, s2w(250, 0.95), s2w(320, 0.95), rot=1.6, t_in=L(4) + 0.1, t_out=E(4) + 0.6,
                      header=(("GASOMETER TRACE", s2w(15, 0.95), "cond"),
                              ("BATAVIA · 27 AUG 1883", s2w(9, 0.95), "mono")),
                      rows=8, sentence_row=2, sentence_size=s2w(8.5, 0.95),
                      sentence="The pressure jumped, then rang like a bell."))
    film.add(Trace(*bcam, s2w(180, 0.95), s2w(115, 0.95), W(4, "gasometer") + 0.1, dur=1.5,
                   spike=(0.45, 0.75, 0.02), pts=((0.12, 0.04, 0.05), (0.82, 0.07, 0.07))))
    film.add(Labels([("BAROMETERS FELL OFF THE PAGE", at(bcam, 0, -190, 0.95), "center",
                      W(4, "trace") + 0.2, 13, 0.95, (238, 218, 188))], t_out=E(4) + 0.6))

    # ================================================================= 5-6  wall of air, the sea
    film.add(RingWave(k[0], k[1], W(5, "sound") + 0.4, r_end=s2w(1600, 0.62), dur=2.2, width=s2w(14, 0.62),
                      rings=3, gap=0.40, rgb=(255, 244, 224), a=0.85))
    film.add(Labels([("PRESSURE, NOT SOUND", at(k, 0, 340, 0.62), "center", W(5, "sound") + 0.8, 22, 0.62, CREAM2)],
                    t_out=E(6) + 0.4))
    film.add(WaveBands(k[0], k[1], L(6) - 0.15, s2w(1500, 0.70), n=4, dur=2.8, t_out=E(8) + 0.2))

    # ================================================================= 7-11  the sea, the dead, Sebesi, the caldera, the Berouw
    tb = P["Teluk Betung"]
    film.add(WaveBar(at(tb, -430, 210, 1.05), s2w(340, 1.05), W(7, "hundred"), t_out=W(8, "thirty") - 0.7,
                     z=1.05))
    film.add(Labels([("100 FT", at(tb, -430, -40, 1.05), "center", W(7, "hundred") + 0.3, 32, 1.05,
                      (140, 38, 26)),
                     ("TELUK BETUNG", at(tb, -430, 330, 1.05), "center", W(7, "high"), 14, 1.05, (250, 238, 212)),
                     ("THE HOUSE IS 25 FT", at(tb, -160, 240, 1.05), "center", W(7, "feet") + 0.1, 11, 1.05,
                      (250, 238, 212))], t_out=W(8, "thirty") - 0.7))
    count_t = W(8, "thirty") - 0.2
    count_out = W(8, "people") + 1.1
    film.add(Counter(*at(tb, 40, 70, 1.05), s2w(96, 1.05), 36417, count_t, dur=2.4,
                     caption="OFFICIAL DUTCH COUNT", rgb=(40, 28, 20), t_out=count_out))
    film.add(Labels([("DROWNED, NOT BURNED", at(tb, 40, 260, 1.05), "center", count_t + 0.9, 21, 1.05,
                      (44, 30, 22))], t_out=count_out))
    sb = P["Sebesi"]
    film.add(XMarker(sb[0], sb[1], None, t_in=W(9, "Sebesi") - 0.3, t_out=E(10), size=0.55))
    film.add(Labels([("SEBESI", at(sb, 40, -30, 2.3), "right", W(9, "Sebesi") - 0.1, 26, 2.3, CREAM2),
                     ("3,000 LIVED HERE", at(sb, 40, 20, 2.3), "right", W(9, "three") + 0.1, 16, 2.3, (236, 216, 184))],
                    t_out=E(10)))
    film.add(Stamp("NO SURVIVORS", *at(sb, 30, 300, 2.3), s2w(32, 2.9), rot=-6, t_in=W(9, "survived") - 0.1,
                   t_out=E(10) + 0.4, rgb=(176, 30, 24)))
    cal = [at(k, -150, 60, 2.7), at(k, 30, -200, 2.7), at(k, 260, -70, 2.7), at(k, 290, 150, 2.7),
           at(k, 110, 300, 2.7), at(k, -130, 230, 2.7)]
    film.add(Caldera(cal, W(10, "third") - 0.1, dur=1.2, t_out=E(11) + 0.3, z=2.7))
    film.add(BigText("TWO THIRDS", *at(k, 60, -430, 2.7), s2w(42, 2.7), t_in=W(10, "third") + 0.15,
                     font="cond", rgb=CREAM2, track=0.06, t_out=E(11) + 0.3))
    film.add(Labels([("THIS IS WATER NOW", at(k, 60, 380, 2.7), "center", W(10, "sea"), 17, 2.7, (232, 214, 184))],
                    t_out=E(11) + 0.3))
    film.add(Route(tb, at(tb, -260, 120, 0.9), t_in=W(11, "Dutch") - 0.2, dur=1.3, bend=-0.2, width=s2w(8, 0.9),
                   rgb=(214, 70, 44), t_out=E(12) + 0.3))
    film.add(Labels([("H.M. BEROUW", at(tb, -260, 120, 0.9), "left", W(11, "gunboat"), 18, 0.9, CREAM2),
                     ("CARRIED 2 MILES INLAND", at(tb, -260, 170, 0.9), "left", W(11, "inland") + 0.1,
                      15, 0.9, (238, 216, 184))], t_out=E(12) + 0.3))

    # ================================================================= 12-19  the world chart
    film.add(Route(wk, P["w_Rodrigues"], W(12, "Nearly") - 0.2, dur=2.0, bend=-0.10, width=s2w(7, 0.55),
                   rgb=(255, 210, 160), t_out=E(16)))
    film.add(Labels([("RODRIGUES", at(P["w_Rodrigues"], -40, -96, 0.55), "right", W(12, "harbour") - 0.2,
                      19, 0.55, CREAM2),
                     ("NEARLY 3,000 MILES", at(P["w_Rodrigues"], -40, -62, 0.55), "right",
                      W(12, "thousand") + 0.1, 13, 0.55, GOLD),
                     ("LONDON", at(wl, -26, -8, 0.55), "left", W(13, "London") - 0.3, 18, 0.55, CREAM2),
                     ("WASHINGTON", at(P["w_Washington"], 26, 10, 0.55), "right", W(13, "Washington") - 0.2,
                      15, 0.55, (238, 220, 190))], t_out=E(14) + 0.2))
    film.add(Labels([("LONDON", at(wl, 26, -26, 0.40), "left", L(14) - 0.2, 16, 0.40, CREAM2),
                     ("WASHINGTON", at(P["w_Washington"], 26, -26, 0.40), "left", L(14) - 0.1, 14, 0.40,
                      (238, 220, 190))], t_out=E(19) + 0.4))
    for nm, xy, rot in (("LONDON", at(wl, -70, 90, 1.05), -1.4),
                        ("WASHINGTON", at(P["w_Washington"], 50, 120, 1.05), 2.2)):
        film.add(PaperDoc(*xy, s2w(250, 1.05), s2w(190, 1.05), rot=rot, t_in=W(13, nm.lower()) - 0.1,
                          t_out=E(16) + 0.2,
                          header=((nm, s2w(14, 1.05), "cond"), ("BAROGRAPH · 27 AUG 1883", s2w(7.5, 1.05), "mono")),
                          rows=3, sentence=None, pin=False))
        film.add(Trace(*xy, s2w(210, 1.05), s2w(90, 1.05), W(13, nm.lower()) + 0.1, dur=1.3,
                       spike=(0.5, 0.62, 0.02), pts=((0.13, 0.05, 0.05),), paper=False))
    # seven passes: rings round the source, ticked on as the stations log them
    for i in range(7):
        film.add(RingWave(wk[0], wk[1], W(14, "seven") + 0.3 + i * 0.5, r_end=4900 * GLOBE_PPK, dur=3.6,
                          width=s2w(5, 0.40), rings=1, rgb=(255, 204, 156), a=0.40 - 0.03 * i))
    film.add(Counter(*at(wk, 260, 470, 0.40), s2w(88, 0.40), 7, W(14, "seven") + 0.2, dur=2.0,
                     caption="PASSES · FIVE DAYS", rgb=CREAM2, t_out=E(16)))
    film.add(Labels([("BATAVIA", at(P["w_Batavia"], -24, 16, 0.40), "left", W(14, "planet"), 13, 0.40,
                      (232, 214, 184)),
                     ("THE PLANET RANG", at(wk, 0, 380, 0.40), "center", W(14, "planet") + 0.2, 15, 0.40,
                      CREAM2)], t_out=E(16)))
    # the column: a schematic pinned over the Indian Ocean
    col = at(wk, 690, -760, 0.62)
    film.add(ColumnCard(col[0], col[1], s2w(300, 0.68), s2w(440, 0.68), L(15) - 0.2,
                        marks=((0.20, "12 KM · AIRLINERS"), (0.44, "STRATOSPHERE"), (1.0, "80 KM · 50 MILES")),
                        heading="THE COLUMN, 27 AUGUST 1883",
                        sub="THE ASH TURNS THE SUNSETS", t_out=E(16) + 0.2))
    # Ashcroft, the New York alarm, the cooling, the wire
    ap = at(wl, -120, 300, 0.72)
    film.add(SunsetPlate(ap[0], ap[1], s2w(250, 0.72), s2w(310, 0.72), W(16, "Ashcroft") - 0.3,
                         t_out=E(19) + 0.3))
    film.add(Labels([("AFTER WILLIAM ASCROFT · CHELSEA", at(wl, 320, 62, 0.86), "center",
                      W(16, "Ashcroft") + 0.1, 14, 0.86, CREAM2),
                     ("26 NOVEMBER 1883", at(wl, 320, -110, 0.86), "center", W(16, "London") + 0.4, 12, 0.86,
                      (232, 212, 180))], t_out=E(19) + 0.3))
    nyc = at(wn, -200, -180, 0.86)
    film.add(PaperDoc(*nyc, s2w(230, 0.86), s2w(300, 0.86), rot=2.6, t_in=W(17, "New") - 0.1, t_out=E(19) + 0.3,
                      header=(("NEW YORK", s2w(17, 0.86), "cond"), ("8 PM · 27 NOV 1883", s2w(9, 0.86), "mono")),
                      rows=7, sentence_row=1, sentence_size=s2w(10, 0.86),
                      sentence="Fire engines were called to a fire on the horizon."))
    film.add(Stamp("THE SKY", *at(nyc, 70, 200, 0.86), s2w(26, 1.05), rot=-8, t_in=W(17, "sky"),
                   t_out=E(19) + 0.3, rgb=(176, 34, 26)))
    cool = at(P["w_Marseille"], 205, 170, 0.86)
    film.add(PaperDoc(*cool, s2w(240, 0.86), s2w(250, 0.86), rot=-1.2, t_in=L(18) - 0.1, t_out=E(18) + 0.2,
                      header=(("GLOBAL TEMPERATURE", s2w(13, 0.86), "cond"), ("1883–1888", s2w(9, 0.86), "mono")),
                      rows=3, sentence=None, pin=False))
    film.add(Trace(*at(cool, 0, 30, 0.86), s2w(170, 0.86), s2w(90, 0.86), W(18, "cooled") + 0.1, dur=2.0,
                   pts=((0.3, 0.5, 0.09), (0.75, 0.62, 0.12)), baseline=0.72, t_out=E(18) + 0.2))
    film.add(Counter(*at(cool, 0, 240, 0.86), s2w(44, 0.86), 0.5, W(18, "half") - 0.1, dur=1.4, prefix="-",
                     suffix=" °C", rgb=(238, 224, 198), t_out=E(18) + 0.2))
    wire = [P["w_Batavia"], P["w_Singapore"], P["w_Colombo"], P["w_Aden"], P["w_Suez"], P["w_Marseille"], wl]
    for i, (a, b) in enumerate(zip(wire, wire[1:])):
        film.add(Route(a, b, W(19, "telegraph") - 0.2 + 0.10 * i, dur=0.45, bend=0.05, width=s2w(4.5, 0.40),
                       rgb=(240, 216, 168), t_out=E(20) + 0.3))
    film.add(Labels([("THE WIRE · ONE DAY", at(wire[4], -30, -70, 0.40), "right", W(19, "telegraph") + 0.5,
                      16, 0.40, GOLD)], t_out=E(20) + 0.3))

    # ================================================================= 20-21  home
    film.add(Cone(k[0], k[1] + s2w(30, 1.95), s2w(72, 1.95), s2w(92, 1.95), W(20, "seven") + 0.5))
    film.add(Caldera([at(k, -170, 80, 1.95), at(k, 40, -150, 1.95), at(k, 220, 40, 1.95),
                      at(k, 120, 230, 1.95), at(k, -110, 200, 1.95)], W(20, "seven") + 1.2, dur=1.0,
                     rgb=(214, 96, 60), z=1.95, t_out=E(21) + 0.4))
    film.add(BigText("1927", *at(k, 40, -330, 1.95), s2w(52, 1.95), t_in=W(20, "seven"), font="cond",
                     rgb=CREAM2, track=0.06, hit=0.8, t_out=E(21)))
    film.add(Labels([("ANAK KRAKATAU", at(k, 40, 240, 1.95), "center", W(20, "Anak") - 0.1, 19, 1.95, CREAM2),
                     ("THE CHILD OF KRAKATOA", at(k, 40, 288, 1.95), "center", W(20, "rose") + 0.2, 12, 1.95,
                      (232, 212, 180))], t_out=E(21) + 1.0))

    # the sound, at the end: the stations the wave reached light up as they log it
    def lamp(name, t, xy, size=12, text=True):
        film.add(Glow(xy[0], xy[1], s2w(110, 0.40), t_in=t, rgb=(255, 200, 136), a=0.42, pulse=0.05, z=37))
        if text:
            film.add(Labels([(name, at(xy, 0, 26, 0.40), "center", t + 0.05, size, 0.40, (244, 226, 196))],
                            t_out=E(21) + 0.5))
    lamp("COLOMBO", W(14, "seven") + 0.5, P["w_Colombo"])
    lamp("CALCUTTA", W(14, "seven") + 1.3, P["w_Calcutta"])
    lamp("PERTH", W(14, "seven") + 2.1, P["w_Perth"])
    lamp("RODRIGUES", W(14, "in") + 0.2, P["w_Rodrigues"], text=False)
    lamp("LONDON", W(14, "back"), wl, text=False)
    lamp("NEW YORK", W(14, "way"), wn)

    # the closing lockup, set on the sea of the strait sheet
    # the lockup goes on the sea west of the strait, so it never sits on the sheet's own title
    film.add(BoardTitle(*at(k, -90, -700, 0.42), W(21, "loudest") + 0.5, [
        ("THE LOUDEST SOUND", s2w(34, 0.42), "cond", 0.0, 0.30),
        ("EVER RECORDED", s2w(34, 0.42), "cond", 0.30, 0.30),
        ("KRAKATAU · 27 AUGUST 1883", s2w(22, 0.42), "serifb", 0.9, 0.22),
        ("THE ROYAL SOCIETY · 1888", s2w(17, 0.42), "mono", 1.4, 0.24),
    ], rgb=CREAM2))

    # ================================================================= camera
    PATH = [
        (at(k, -60, -30, 0.42), 0.0, 0.42, 0.28),
        (at(k, -20, -10, 0.50), W(1, "Sunda") - 1.0, 0.50, 0.28),
        (at(k, 120, 10, 0.86), W(2, "third") - 0.5, 0.86, 0.32),
        (at(k, 125, 20, 0.88), E(4) - 0.3, 0.88, 0.32),
        (at(k, 40, 20, 1.5), W(3, "forty") + 0.2, 1.5, 0.34),
        (at(P["Batavia"], -200, -300, 0.95), W(4, "Batavia") - 0.2, 0.95, 0.32),
        (at(P["Batavia"], -200, -305, 0.95), E(4) + 0.3, 0.95, 0.32),
        (at(k, 0, 120, 0.62), W(5, "sound") + 0.2, 0.62, 0.30),
        (at(k, 20, 90, 0.70), L(6) + 0.2, 0.70, 0.30),
        (at(tb, -430, 210, 1.05), W(7, "hundred") - 0.1, 1.05, 0.34),
        # the count gets the frame to itself, then the camera dives to Sebesi
        (at(tb, 40, 70, 1.05), W(8, "thirty") - 0.4, 1.05, 0.34),
        (at(tb, 40, 70, 1.05), count_out + 0.55, 1.05, 0.34),
        (at(tb, 190, -110, 0.92), W(8, "people") - 0.3, 0.92, 0.32),
        (at(sb, 60, 150, 2.3), W(9, "Sebesi") + 0.1, 2.3, 0.36),
        (at(k, 60, 120, 2.7), W(10, "third") - 0.1, 2.7, 0.36),
        (at(tb, -120, 20, 0.9), W(11, "Dutch") - 0.2, 0.9, 0.32),
        # 12  rise off the strait, across the board, down on the world chart
        (at(k, 60, 300, 0.30), W(11, "inland") + 0.4, 0.30, 0.18),
        ((W0[0] - 900, W0[1] - 300), W(12, "Nearly") - 0.9, 0.44, 0.22),
        (at(P["w_Rodrigues"], 70, 60, 0.60), W(12, "Nearly") + 0.1, 0.60, 0.30),
        # 13  the barographs, Atlantic in frame
        (at(wl, -160, 130, 0.62), W(13, "London") - 0.2, 0.62, 0.30),
        # 14  the passes
        (at(wk, 300, 260, 0.40), W(14, "seven") - 0.4, 0.40, 0.24),
        # 15  the column
        (col, L(15) + 0.3, 0.68, 0.30),
        (col, E(15) - 0.3, 0.68, 0.30),
        # 16  Ashcroft: hold the Thames plate at the left edge, London's barograph on the right
        (at(wl, 0, 100, 0.72), W(16, "artist") - 0.25, 0.72, 0.30),
        (at(wl, 0, 100, 0.72), E(16) - 0.15, 0.72, 0.30),
        # 17  New York
        (at(wn, -170, -150, 0.86), W(17, "New") - 0.2, 0.86, 0.32),
        # 18  the cooling
        (at(P["w_Marseille"], 205, 170, 0.86), W(18, "cooled") - 0.2, 0.86, 0.32),
        (at(P["w_Marseille"], 205, 170, 0.86), E(18) + 0.15, 0.86, 0.32),
        # 19  the wire: pull back off the card to the whole chart, then run the cable
        (at(wk, 350, 330, 0.40), W(19, "telegraph") - 0.4, 0.40, 0.22),
        (at(wk, 350, 330, 0.40), E(19) - 0.15, 0.40, 0.22),
        # 20  home: the dip hides the crossing, then the strait comes back and the cone rises
        (at(wk, 300, 260, 0.44), W(20, "seven") - 1.15, 0.44, 0.20),
        (at(k, 30, 50, 0.90), W(20, "seven") - 0.75, 0.90, 0.30),
        (at(k, 30, 50, 1.25), W(20, "seven") - 0.2, 1.25, 0.34),
        (at(k, 24, 40, 1.95), W(20, "Anak") + 0.1, 1.95, 0.36),
        # 21  the last line on the whole sheet
        (at(k, 30, 120, 0.50), W(21, "loudest") + 0.1, 0.50, 0.24),
        (at(k, 30, 120, 0.42), doc.duration + 1.2, 0.42, 0.20),
    ]
    for (xy, t, z, strength) in PATH:
        film.cam(t, xy[0], xy[1], z)
        film.focus(t, xy[0], xy[1], s2w(780, z), strength)

    film.add(Dip(wk, W(20, "seven") - 1.60, hold=0.80, rise=0.30, fall=0.50))
    film.cue("boom", W(2, "blast"), 1.0)
    film.cue("stamp", W(2, "blast"), 0.4)
    film.cue("boom", L(6), 0.7)
    film.cue("impact", L(11), 0.5)
    film.cue("ticks", W(14, "seven"), 0.5)
    film.cue("impact", W(20, "seven"), 0.8)
    film.room_tone = [[0.0, doc.duration]]

    report_placement(doc, PATH, P, film)
    return film


def report_placement(doc, path, P, film):
    """Does each held cluster sit inside the frame of the key that holds while it plays?"""
    keys = [(t, x, y, z) for (x, y), t, z, _ in path]
    checks = [(1, P["Krakatoa"]), (4, P["Batavia"]), (7, P["Teluk Betung"]), (9, P["Sebesi"]),
              (11, P["Teluk Betung"]), (13, P["w_London"]), (16, P["w_London"]),
              (17, P["w_New York"]), (18, P["w_Marseille"]), (20, P["Krakatoa"])]
    rows = []
    for line, pt in checks:
        t = doc.L(line) + 0.4 * (doc.E(line) - doc.L(line))
        last = keys[0]
        for kk in keys:
            if kk[0] <= t:
                last = kk
        kt, x, y, z = last
        rows.append(f"  line {line:>2}: dx {(pt[0] - x) * S * z:7.0f}  dy {(pt[1] - y) * S * z:7.0f}"
                    f"   (key {kt:5.1f}s z {z:.2f}, frame +/-540 x +/-960)")
    print("placement:\n" + "\n".join(rows))
    # every BigText and Counter must fit the frame of the key that holds while it is up
    for it in film.items:
        if not isinstance(it, (BigText, Counter)) or it.t_in is None:
            continue
        keys_ = sorted([kk for kk in keys if kk[0] <= it.t_in + 0.3])
        if not keys_:
            continue
        kt, x, y, z = keys_[-1]
        tr = getattr(it, "track", 0.04)
        label = getattr(it, "text", None) or f"counter {it.prefix}{it.value}{it.suffix}"
        try:
            import engine as _e
            wpx = _e.text_width(None, label, it.size, getattr(it, "font", "cond"), tr)
        except Exception:
            wpx = len(label) * it.size * 0.62 * (1 + tr)
        hw = wpx / 2 * S * z
        hh = it.size * 0.9 * S * z
        dx = (it.x - x) * S * z
        dy = (it.y - y) * S * z
        bad = abs(dx) + hw > 540 or abs(dy) + hh > 960
        if bad:
            print(f"  TEXT OUT OF FRAME: {getattr(it, 'text', 'counter'):<22} dx {dx:6.0f} dy {dy:6.0f}"
                  f" half-width {hw:5.0f} half-height {hh:5.0f} at z {z:.2f}")
