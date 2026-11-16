"""THE CITY THAT REVERSED ITS RIVER: Chicago, 1900. About 94 s, one wall.

One continuous camera over one board. The printed map sheet is the world: the lake and the river at
Chicago, the canal west to the Des Plaines, the Illinois River down to the Mississippi at Grafton,
Missouri on the far bank. Documents, a section drawing, counters and stamps are pinned on the sheet
where their subject is, so the camera never leaves the map and every move is a move over geography.

Layout rule: every cluster is placed inside the frame its camera key sees, and sized with s2w() so
the type lands at a known on-screen size. Wides drop the spotlight (a harsher key would black out
the map); close work keeps it tight.

Every time comes from the voiceover: doc.L(i) starts line i, doc.W(i, "word") is when a spoken word
lands, so a new read re-times the whole film by itself.
World units are 4K pixels at zoom 1: a 720x1280 frame at zoom z shows 3840/z x 6827/z world px.
"""
import pathlib
import sys

import skia

from engine import (CREAM, HILITE, INK, MUSTARD, RUST, TEAL, WHITE, BigText, Counter, Film, GeoMap,
                    Item, PaperDoc, PenMark, RegionFill, Route, Stamp, StringLine, XMarker, draw_text,
                    ease_in_out, paint, ramp)

DOC = pathlib.Path(__file__).resolve().parent
K = 70000.0           # sheet: 4,794 x 8,210 world px, fills a phone at zoom 0.82
S = 0.1875                      # world px -> screen px at zoom 1, for a 720-wide render

P = {}                          # places in world px, filled in build_film


def s2w(screen_px, z):
    return screen_px / (S * z)


def at(xy, dx, dy, z):
    """A world point `dx`, `dy` screen px away from `xy` at zoom z (dy down). `xy` may be a place,
    a world point, or any item with .x/.y."""
    x, y = (xy.x, xy.y) if hasattr(xy, "x") else (xy[0], xy[1])
    k = s2w(1.0, z)
    return (x + dx * k, y + dy * k)


def marker(film, xy, text, t, z, side="right", px=26, rgb=None, t_out=None):
    """Pin whose ring reads `px`-ish screen px wide and whose label is `px` screen px tall at zoom z."""
    kw = dict(t_in=t, t_out=t_out, side=side, size=1.0, label_size=px / (S * z),
              label_rgb=rgb or INK, shadow=False)
    return film.add(XMarker(xy[0], xy[1], text, **kw))


class Sheet(GeoMap):
    """The printed map sheet: states and neighbours from the atlas files, the Great Lakes (which the
    state file does not carry) and the rivers, over the land in printed-map ink."""

    z = 0
    # an aged printed sheet: darker land than MAP_LOOKS["period"], so ink type always reads
    LOOK = dict(sheet=(196, 180, 146), water=(146, 172, 166), land=(186, 168, 132),
                border=(112, 82, 54), relief=0.20, neighbor=(178, 162, 128), neighbor_line=(132, 106, 76),
                dark=(150, 134, 106), dark_line=(104, 84, 60), frame=(96, 74, 52))

    def __init__(self, data, K, origin=(0, 0), look=None, lakes=(), t_in=-1):
        super().__init__(data, K, origin, look or dict(self.LOOK), t_in)
        self.lakes = [[self.w(p) for p in ring] for ring in lakes]
        self.rivers = [[self.w(p) for p in ring] for _, ring in sorted(data.get("river_rings", []))]

    @staticmethod
    def _ring(c, ring, fill):
        p = skia.Path()
        p.moveTo(*ring[0])
        for pt in ring[1:]:
            p.lineTo(*pt)
        p.close()
        c.drawPath(p, fill)

    def _draw(self, c, res):
        super()._draw(c, res)
        c.save(); c.clipRect(self.sheet().makeInset(70, 70))
        for ring in self.lakes:
            self._ring(c, ring, paint(self.look["water"], 0.95))
            self._ring(c, ring, paint((110, 100, 80), 0.55, stroke=5))
        for ring in self.rivers:
            self._ring(c, ring, paint((104, 142, 156), 0.85))
        c.restore()


class RiverThread(Item):
    """A river or canal drawn on as one thread that follows the water."""

    z = 6

    def __init__(self, pts, t_in, dur=0.9, rgb=(120, 60, 40), width=10, t_out=None, sfx=True, z=None):
        super().__init__(t_in, t_out, z, sfx)
        self.rgb, self.wd, self.dur = rgb, width, dur
        self.p = skia.Path()
        self.p.moveTo(*pts[0])
        for a, b in zip(pts[1:-1], pts[2:]):
            self.p.quadTo(*a, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        self.p.lineTo(*pts[-1])
        self.box = self.p.getBounds().makeOutset(300, 300)

    def bounds(self, res):
        return self.box

    def cues(self):
        return [("whoosh", self.t_in, 0.35, {})]

    def draw(self, c, res, t):
        u = ease_in_out(ramp(t, self.t_in, self.dur)); a = self.fade(t)
        if u <= 0 or a <= 0:
            return
        pm = skia.PathMeasure(self.p, False)
        length = pm.getLength()
        n = max(2, int(length / 3.0))
        for i in range(int(n * u) + 1):
            pos = pm.getPosTan(length * min(1.0, i / n))
            if not pos:
                continue
            f = i / n
            c.drawCircle(pos[0].x(), pos[0].y(), self.wd * (0.45 + 0.55 * min(1.0, f / max(u, 1e-3))),
                         paint(self.rgb, 0.95 * a))
        if u < 1:
            pos = pm.getPosTan(length * u)
            if pos:
                c.drawCircle(pos[0].x(), pos[0].y(), self.wd * 1.9, paint(self.rgb, 0.7 * a))


class RidgeMark(Item):
    """The subcontinental divide: a dotted ridge, north to south just west of Chicago."""

    z = 5

    def __init__(self, pos, t_in, h=900, t_out=None, rgb=(170, 128, 46), sfx=False, z=None):
        super().__init__(t_in, t_out, z, sfx)
        self.x, self.y, self.h, self.rgb = pos[0], pos[1], h, rgb

    def bounds(self, res):
        return skia.Rect.MakeLTRB(self.x - 200, self.y - self.h, self.x + 200, self.y + self.h)

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 0.9) * self.fade(t)
        if a <= 0:
            return
        n = 24
        for i in range(n):
            u = i / (n - 1)
            if u > a:
                break
            yy = self.y - self.h / 2 + self.h * u
            c.drawCircle(self.x - 18, yy, 6, paint(self.rgb, 0.9))
            c.drawCircle(self.x + 18, yy, 6, paint(self.rgb, 0.9))


class Section(Item):
    """A pen section through the divide: the lake, eight feet of land, the fall to the Des Plaines."""

    z = 9

    def __init__(self, t_in, x, y, w, h, t_out=None, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.h = x, y, w, h

    def bounds(self, res):
        return skia.Rect.MakeXYWH(self.x - self.w / 2 - 200, self.y - self.h * 2.0, self.w + 400, self.h * 3.0)

    def draw(self, c, res, t):
        u = ramp(t, self.t_in, 1.1) * self.fade(t)
        if u <= 0:
            return
        W_, H_ = self.w, self.h
        x0, y0 = self.x - W_ / 2, self.y + H_ * 0.3
        top = y0 - H_ * 0.5
        p = skia.Path()
        p.moveTo(x0, y0)
        p.lineTo(x0 + W_ * 0.30, y0)
        p.lineTo(x0 + W_ * 0.38, top)
        p.lineTo(x0 + W_ * 0.60, top)
        p.lineTo(x0 + W_ * 0.68, y0 + H_ * 0.14)
        p.lineTo(x0 + W_, y0 + H_ * 0.14)
        pm = skia.PathMeasure(p, False); length = pm.getLength()
        n = max(2, int(170 * u))
        q = skia.Path(); pos = pm.getPosTan(0); q.moveTo(pos[0].x(), pos[0].y())
        for i in range(1, n):
            pos = pm.getPosTan(length * i / max(1, n - 1))
            if pos:
                q.lineTo(pos[0].x(), pos[0].y())
        c.drawPath(q, paint(INK, 0.9, stroke=5))
        if u > 0.15:
            a = ramp(u, 0.15, 0.5)
            c.drawRect(skia.Rect.MakeLTRB(x0, y0 + H_ * 0.02, x0 + W_ * 0.32, y0 + H_ * 0.16), paint(TEAL, 0.55 * a))
            c.drawRect(skia.Rect.MakeLTRB(x0 + W_ * 0.70, y0 + H_ * 0.16, x0 + W_, y0 + H_ * 0.30), paint(TEAL, 0.45 * a))
        if u > 0.5:
            a = ramp(u, 0.5, 0.5)
            cxx = x0 + W_ * 0.49
            red = paint((176, 40, 30), 0.95 * a, stroke=6)
            c.drawLine(cxx - 90, top, cxx - 90, y0, red)
            c.drawLine(cxx - 90, y0, cxx + 90, y0, red)
            c.drawLine(cxx + 90, y0, cxx + 90, top, red)
            draw_text(c, res, "8 FT", cxx, top - H_ * 0.14, H_ * 0.22, "cond", (176, 40, 30), a, 0.06, "center")
        draw_text(c, res, "LAKE MICHIGAN", x0 + W_ * 0.15, y0 + H_ * 0.26, H_ * 0.11, "cond", (52, 62, 62), 0.9 * u, 0.10, "center")
        draw_text(c, res, "DES PLAINES R.", x0 + W_ * 0.84, y0 + H_ * 0.38, H_ * 0.11, "cond", (52, 62, 62), 0.9 * u, 0.10, "center")
        draw_text(c, res, "SECTION THROUGH THE DIVIDE", x0 + W_ * 0.5, top - H_ * 0.30, H_ * 0.10, "mono", INK, 0.7 * u, 0.14, "center")


class Barrier(Item):
    """The electric fish barrier: a dashed fence across the canal, in caution yellow."""

    z = 12

    def __init__(self, x, y, t_in, w=200, h=120, rot=-8, t_out=None, sfx=True):
        super().__init__(t_in, t_out, None, sfx)
        self.x, self.y, self.w, self.h, self.rot = x, y, w, h, rot

    def bounds(self, res):
        return skia.Rect.MakeXYWH(self.x - self.w, self.y - self.h, self.w * 2, self.h * 2)

    def cues(self):
        return [("pop", self.t_in, 0.6, {})]

    def draw(self, c, res, t):
        u = ramp(t, self.t_in, 0.3) * self.fade(t)
        if u <= 0:
            return
        c.save(); c.translate(self.x, self.y); c.rotate(self.rot)
        p = paint(MUSTARD, 0.95 * u, stroke=5)
        for i in range(5):
            xx = -self.w / 2 + i * self.w / 4
            c.drawLine(xx, -self.h / 2, xx, self.h / 2, p)
        c.drawLine(-self.w / 2, -self.h / 2, self.w / 2, -self.h / 2, p)
        c.drawLine(-self.w / 2, self.h / 2, self.w / 2, self.h / 2, p)
        c.restore()


class PlaceNames(Item):
    """Printed town names on the sheet: small serif caps in the map's ink, like a real map's type."""

    z = 3

    def __init__(self, names, t_in=0.2, size=44, rgb=(64, 54, 40), t_out=None, sfx=False):
        super().__init__(t_in, t_out, None, sfx)
        self.names, self.size, self.rgb = names, size, rgb
        self.box = None
        for _, (x, y), _ in names:
            r = skia.Rect.MakeLTRB(x - 600, y - 120, x + 600, y + 120)
            self.box = r if self.box is None else skia.Rect.MakeLTRB(
                min(self.box.left(), r.left()), min(self.box.top(), r.top()),
                max(self.box.right(), r.right()), max(self.box.bottom(), r.bottom()))

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = ramp(t, self.t_in, 1.2) * self.fade(t)
        if a <= 0:
            return
        for text, (x, y), side in self.names:
            draw_text(c, res, text, x, y, self.size, "serif", self.rgb, 0.72 * a, 0.16,
                      "right" if side == "left" else "left")


def _lakes():
    sys.path.insert(0, str(DOC / "tools"))
    from lake import lake_outer
    return lake_outer()


def build_film(doc):
    L, E, W = doc.L, doc.E, doc.W
    res = doc.res()
    film = Film(doc.duration, fps=30, look="wall")
    cue = film.cue

    def shot(t, xy, z, strength=0.34):
        """Camera and a spotlight that always covers the frame, so the map never blacks out."""
        x, y = (xy.x, xy.y) if hasattr(xy, "x") else xy
        film.shot(t, x, y, z, radius=s2w(600, z), strength=strength)

    def wide(t, xy, z, strength=0.2):
        x, y = (xy.x, xy.y) if hasattr(xy, "x") else xy
        film.cam(t, x, y, z)
        film.focus(t, x, y, s2w(1500, z), strength)

    m = doc.map("mw")
    sheet = film.add(Sheet(m, K, (0, 0), look="period", lakes=_lakes()))
    for name in ("Chicago", "Kedzie", "Summit", "Lockport", "Grafton", "St. Louis", "Joliet",
                 "Morris", "Ottawa", "Peoria", "Havana", "Springfield", "Milwaukee", "Gary",
                 "Davenport", "Michigan City"):
        P[name] = sheet.place(name)
    film.add(PlaceNames([
        ("MILWAUKEE", at(P["Milwaukee"], -70, -30, 1), "left"),
        ("GARY", at(P["Gary"], 70, 30, 1), "left"),
        ("MICHIGAN CITY", at(P["Michigan City"], 60, 20, 1), "left"),
        ("JOLIET", at(P["Joliet"], -60, 40, 1), "left"),
        ("MORRIS", at(P["Morris"], 60, 60, 1), "left"),
        ("OTTAWA", at(P["Ottawa"], 60, 60, 1), "left"),
        ("PEORIA", at(P["Peoria"], 90, 30, 1), "left"),
        ("HAVANA", at(P["Havana"], -90, 30, 1), "left"),
        ("SPRINGFIELD", at(P["Springfield"], 90, 40, 1), "left"),
        ("DAVENPORT", at(P["Davenport"], 90, 40, 1), "left"),
        ("GRAFTON", at(P["Grafton"], 70, 40, 1), "left"),
    ], size=s2w(19, 4.0)))
    ch, kz, su, lp, st = P["Chicago"], P["Kedzie"], P["Summit"], P["Lockport"], P["St. Louis"]
    loop = (ch[0] - 8, ch[1] + 8)
    mouth = (ch[0] + 70, ch[1] - 34)

    # board slots, so no two clusters share a frame (the sheet runs x -2149..2639, y -3101..5110)
    SL = {"divide": (560.0, -1120.0), "dig": (1520.0, 340.0), "report": (240.0, 1520.0),
          "worked": (980.0, -60.0), "docket": (-260.0, 3350.0), "opinion": (-1080.0, 3980.0),
          "title": (210.0, 4300.0)}

    # ============================================================ 1-2  a river into the drinking water
    gone = L(3) - 0.15
    film.add(RiverThread([loop, mouth], W(1, "dumped") - 0.1, dur=0.35, t_out=gone,
                         rgb=(148, 38, 24), width=9, z=7))
    marker(film, at(loop, -100, -30, 3.2), "CHICAGO", L(1) + 0.1, 3.2, side="left", px=28)
    film.add(BigText("1900", *at(ch, -20, 250, 3.2), s2w(46, 3.2), L(1) - 0.2, t_out=gone,
                     font="cond", rgb=INK))
    film.add(Stamp("SEWER", *at(ch, 130, 360, 3.2), s2w(18, 3.2), rot=-11, t_in=W(1, "sewage"),
                   t_out=gone))
    marker(film, at(mouth, 170, -130, 3.2), "LAKE MICHIGAN", W(2, "lake"), 3.2, side="right",
           px=26, t_out=gone)
    film.add(StringLine(loop, at(ch, 430, 300, 3.2), t_in=W(2, "drank"), dur=0.5, sag=0.02,
                        width=3, t_out=gone))
    film.add(PaperDoc(*at(ch, 640, 360, 3.2), 250, 300, rot=1.4, t_in=W(2, "drank") - 0.1, t_out=gone,
                      header=(("CHICAGO", 32, "serif"), ("WATER WORKS", 19, "mono")), rows=6,
                      sentence_row=2, sentence_size=21,
                      sentence="The city drank from the lake. The river emptied into the lake."))


    # ============================================================ 3-4  the canal, the other way
    cap = E(4) + 0.5
    film.add(BigText("THE OTHER WAY", *at(ch, -10, -250, 2.4), s2w(26, 2.4), L(3) - 0.05,
                     t_out=cap, font="cond", rgb=INK, bar=HILITE, bar_h=0.9, type_on=0.6, shadow=False))
    film.add(RiverThread([loop, mouth], E(12) - 0.05, dur=0.9, t_out=L(13) + 1.2,
                         rgb=(238, 234, 220), width=9, z=7))
    film.add(RiverThread([loop, (ch[0] - 90, ch[1] + 6), su, lp], W(3, "other") + 0.25, dur=1.1,
                         rgb=(250, 246, 232), width=10, z=7))
    marker(film, at(lp, -40, 90, 3.9), "LOCKPORT", W(4, "canal"), 3.9, side="left", px=28)
    film.add(Counter(*at(lp, 210, 210, 3.9), s2w(48, 3.9), 28, W(4, "twenty") - 0.05, dur=0.9,
                     suffix=" MI", caption="CANAL LENGTH", rgb=INK, t_out=cap))


    # ============================================================ 5-6  the divide, the eight feet
    ridge_out = E(6) + 1.0
    film.add(RidgeMark((su[0] - 70, su[1] + 40), W(5, "ridge") - 0.2, h=s2w(200, 3.9), t_out=ridge_out, z=5))
    marker(film, at(su, -170, 130, 3.9), "THE DIVIDE", W(5, "ridge"), 3.9, side="left", px=28,
           rgb=MUSTARD, t_out=ridge_out)
    film.add(Section(L(6) - 0.3, *SL["divide"], s2w(330, 3.4), s2w(180, 3.4),
                     t_out=E(7) + 0.4))
    film.add(BigText("EIGHT FEET HIGH", *at(SL["divide"], 0, -300, 3.4), s2w(22, 3.4),
                     L(6) - 0.2, t_out=E(7) + 0.4, font="cond", rgb=INK, bar=HILITE, bar_h=0.9, shadow=False))


    # ============================================================ 7-9  the dig
    dig_out = L(10) - 0.4
    dx, dy = SL["dig"]
    film.add(BigText("1892 — 1900", dx, dy, s2w(44, 2.5), L(7) - 0.25, t_out=dig_out, font="cond", rgb=INK))
    film.add(PenMark("underline", dx, dy + s2w(20, 2.5), s2w(250, 2.5), 0, t_in=L(7) - 0.1, dur=0.6,
                     width=4, t_out=dig_out))
    film.add(Counter(dx, dy + s2w(150, 2.5), s2w(84, 2.5), 8, W(7, "eight") - 0.05, dur=0.9,
                     suffix=" YEARS", caption="DIGGING", rgb=INK, t_out=dig_out))
    film.add(Counter(dx, dy + s2w(330, 2.5), s2w(84, 2.5), 42, W(7, "forty") - 0.05, dur=1.4,
                     suffix="M CU YD", caption="ROCK AND CLAY MOVED", rgb=INK, t_out=dig_out))
    film.add(PenMark("underline", dx, dy + s2w(390, 2.5), s2w(280, 2.5), 0, t_in=W(7, "forty"),
                     dur=0.6, width=6, t_out=dig_out))
    film.add(Stamp("MORE THAN PANAMA", dx, dy + s2w(510, 2.5), s2w(30, 2.5), rot=-7,
                   t_in=W(8, "earth"), t_out=dig_out))
    film.add(StringLine(lp, (dx - s2w(210, 2.5), dy + s2w(120, 2.5)), t_in=W(8, "earth") + 0.1,
                        dur=0.7, sag=0.02, width=3, t_out=dig_out))
    film.add(BigText("THOSE CREWS WENT TO PANAMA", dx, dy + s2w(620, 2.5), s2w(22, 2.5),
                     W(9, "dug"), t_out=dig_out, font="cond", rgb=INK, bar=HILITE, bar_h=0.9))
    film.add(PenMark("underline", dx, dy + s2w(630, 2.5), s2w(250, 2.5), 0, t_in=W(9, "dug") + 0.35,
                     dur=0.5, width=3, t_out=dig_out))


    # ============================================================ 10-12  the morning the dam went
    dam_out = E(12) + 1.4
    report = film.add(PaperDoc(*at(SL["report"], 0, 120, 3.0), 380, 480, rot=-2.0,
                               t_in=L(10) + 0.05, t_out=dam_out,
                               header=(("THE SANITARY DISTRICT", 28, "serif"), ("JANUARY 2, 1900", 19, "mono")),
                               rows=8, sentence_row=2, sentence_size=21,
                               sentence="At dawn the trustees went out to the last earthen dam at Kedzie Avenue."))
    (hx, hy), hw = report.phrase_pos(res, "Kedzie Avenue")
    film.add(PenMark("highlight", hx, hy - 7, hw + 16, 0, t_in=W(10, "Kedzie") - 0.35, dur=0.45,
                     width=20, rot=-2.0, t_out=dam_out))
    marker(film, at(kz, -30, -150, 3.4), "KEDZIE AVENUE", W(10, "Kedzie"), 3.4, side="left",
           px=28, t_out=dam_out)
    film.add(Stamp("BY HAND", *at(kz, 190, -300, 3.4), s2w(26, 3.4), rot=8, t_in=W(10, "broke"),
                   t_out=dam_out))
    film.add(Stamp("BEFORE THE COURT", *at(kz, 120, 250, 3.4), s2w(26, 3.4), rot=-6,
                   t_in=W(11, "court"), t_out=dam_out))
    film.add(BigText("IT WORKED", *at(ch, 330, 200, 2.4), s2w(44, 2.4), L(12) + 0.1,
                     t_out=L(13) + 1.0, font="cond", rgb=CREAM, bar=(32, 24, 18), bar_h=0.94,
                     hit=0.75, shadow=False))
    film.add(Route(lp, P["Grafton"], t_in=E(12) - 0.1, dur=1.8, bend=-0.14, width=10,
                   rgb=(214, 176, 96)))
    marker(film, at(P["Grafton"], -40, -70, 1.05), "THE MISSISSIPPI", E(12) + 0.6, 1.05,
           side="left", px=30)
    marker(film, at(st, -40, 60, 1.05), "ST. LOUIS", W(13, "Missouri") + 0.3, 1.05, side="left", px=24)


    # ============================================================ 13-17  the case
    case_out = L(18) - 0.3
    film.add(RegionFill(sheet, ["Missouri"], RUST, W(13, "Missouri"), alpha=0.38))
    film.add(BigText("v.", *at(st, -30, 70, 1.9), s2w(34, 1.9), L(13) - 0.1, t_out=case_out,
                     font="cond", rgb=INK))
    marker(film, at(st, 30, -80, 1.7), "MISSOURI SUES", W(13, "sued"), 1.7, side="right", px=28,
           t_out=case_out)
    film.add(PaperDoc(*at(SL["docket"], 0, 0, 1.55), 400, 470, rot=2.0, t_in=L(14) + 0.05,
                      t_out=case_out,
                      header=(("SUPREME COURT", 28, "serif"), ("MISSOURI v. ILLINOIS", 15, "mono")),
                      rows=7, sentence_row=2, sentence_size=20,
                      sentence="Missouri asked the Court to stop Chicago turning the river."))
    film.add(Counter(*at(SL["docket"], 0, 300, 1.55), s2w(50, 1.55), 6, W(14, "six") - 0.05, dur=0.8,
                     suffix=" YEARS", caption="TO A DECISION", rgb=INK, t_out=case_out))
    film.add(Stamp("1906", *at(SL["docket"], 270, 10, 1.55), s2w(48, 1.9), rot=-9, t_in=W(15, "Court"),
                   t_out=case_out))
    film.add(Stamp("FOR CHICAGO", *at(SL["docket"], 270, 105, 1.55), s2w(27, 1.9), rot=-4,
                   t_in=W(15, "ruled"), t_out=case_out))
    quote = film.add(PaperDoc(*at(SL["opinion"], 0, 0, 1.9), 430, 300, rot=-1.4,
                              t_in=L(16) - 0.1, t_out=L(20) - 0.2,
                              header=(("FROM THE OPINION", 17, "mono"),), rows=5, sentence_row=2,
                              sentence_size=19,
                              sentence="The fate of the great rivers is not to be settled at one blow."))
    (qx, qy), qw = quote.phrase_pos(res, "at one blow")
    film.add(PenMark("underline", qx, qy + 6, qw, 0, t_in=W(16, "blow") - 0.35, dur=0.5, width=5,
                     t_out=L(20) - 0.2))
    film.add(Stamp("NOT TREATED", *at(lp, 120, 230, 4.2), s2w(24, 4.2), rot=6,
                   t_in=W(17, "untreated"), t_out=L(20) - 0.2))
    film.add(BigText("TOO SMALL", *at(lp, 60, 150, 4.2), s2w(28, 4.2), W(17, "small"), font="cond",
                     rgb=INK, bar=HILITE, bar_h=0.9, t_out=L(20) - 0.2))


    # ============================================================ 18-21  what it cost
    film.add(Route(lp, P["Grafton"], t_in=L(18) - 0.2, dur=2.4, bend=0.13, width=13,
                   rgb=(168, 42, 26)))
    marker(film, at(P["Grafton"], -80, 130, 1.05), "350 MILES DOWNRIVER", W(18, "still") + 0.5, 1.05,
           side="left", px=30)
    film.add(Barrier(*at(lp, 30, 300, 3.6), W(20, "barriers") - 0.2, w=s2w(120, 3.6), h=s2w(70, 3.6)))
    marker(film, at(lp, 120, 300, 3.6), "CARP BARRIER", W(20, "carp"), 3.6, side="left", px=28)
    film.add(BigText("IT STILL RUNS", *at(SL["title"], 0, 0, 0.55), s2w(46, 0.55),
                     W(21, "solved") + 0.3, font="cond", rgb=INK, type_on=0.8))
    film.add(BigText("BACKWARDS", *at(SL["title"], 0, 78, 0.55), s2w(46, 0.55),
                     W(21, "solved") + 0.9, font="cond", rgb=INK, bar=HILITE, bar_h=0.86, type_on=0.6))
    film.add(PenMark("underline", *at(SL["title"], 0, 120, 0.55), s2w(300, 0.55), 0,
                     t_in=W(21, "solved") + 1.6, dur=0.8, width=8))


    # ============================================================ camera: one ordered path
    # A key is a frame that holds while a line plays, or a move that starts when the narrator does.
    worked_pt = at(ch, 330, 200, 2.4)
    title_pt = at(SL["title"], 0, 40, 0.84)
    PATH = [
        ((ch[0] - 10, ch[1] + 40), 0.0, 3.2, 0.40),
        ((ch[0] + 40, ch[1] + 120), W(1, "sewage"), 3.9, 0.34),
        ((ch[0] + 90, ch[1] - 40), W(2, "lake"), 3.4, 0.34),
        (at(ch, 540, 340, 3.2), W(2, "drank") + 0.25, 3.1, 0.34),
        ((ch[0] - 40, ch[1] + 20), L(3) + 0.1, 2.4, 0.28),
        ((lp[0] + 120, lp[1] + 110), W(4, "canal") + 0.15, 3.9, 0.34),
        ((su[0] - 40, su[1] + 60), W(5, "ridge") - 0.1, 3.9, 0.34),
        (at(SL["divide"], 0, -30, 3.4), W(6, "Twelve") - 0.2, 3.4, 0.34),
        ((SL["dig"][0], SL["dig"][1] + s2w(150, 2.5)), L(7) - 0.2, 2.5, 0.28),
        ((SL["dig"][0], SL["dig"][1] + s2w(400, 2.5)), W(8, "earth") - 0.1, 2.5, 0.34),
        ((SL["dig"][0], SL["dig"][1] + s2w(560, 2.5)), W(9, "dug") - 0.1, 2.5, 0.34),
        (at(report, 40, 20, 2.9), L(10) + 0.1, 2.9, 0.34),
        (at(kz, -250, 40, 3.4), W(10, "Kedzie"), 3.4, 0.34),
        (at(kz, -250, 40, 3.4), W(11, "court") - 0.2, 3.4, 0.34),
        (worked_pt, L(12) - 0.1, 2.4, 0.36),
        ((220, 800), E(12) + 0.6, 0.95, 0.18),
        (at(st, -80, -40, 1.7), W(13, "Missouri"), 1.7, 0.34),
        (at(SL["docket"], 0, 50, 1.55), W(14, "case") - 0.1, 1.55, 0.34),
        (at(SL["docket"], 60, 100, 1.75), W(15, "Court") - 0.1, 1.75, 0.34),
        (at(SL["opinion"], 0, -20, 1.9), W(16, "fate") - 0.2, 1.9, 0.34),
        ((200, 1500), W(17, "small") + 0.2, 0.85, 0.18),
        (at(lp, 80, 180, 4.2), W(17, "untreated") - 0.1, 4.2, 0.34),
        ((320, 620), W(17, "untreated") + 1.5, 0.86, 0.18),
        ((-300, 1150), W(18, "still") + 0.2, 0.95, 0.20),
        (at(lp, 140, 250, 3.6), W(20, "barriers") - 0.2, 3.6, 0.34),
        (title_pt, W(21, "solved") + 1.5, 0.84, 0.18),
    ]
    for pt, t, z, strength in PATH:
        x, y = pt
        film.cam(t, x, y, z)
        film.focus(t, x, y, s2w(400, z) if strength > 0.3 else s2w(1500, z), strength)
    film.cam(doc.duration - 0.9, title_pt[0], title_pt[1], 0.81)
    film.focus(doc.duration - 0.9, title_pt[0], title_pt[1], s2w(1500, 0.81), 0.18)

    film.fade_in, film.fade_out = 1.0, 2.6
    cue("boom", E(12) - 0.4, 0.6)
    cue("boom", W(21, "solved") + 0.25, 0.5)
    return film
