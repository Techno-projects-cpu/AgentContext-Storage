"""ZERO VAST -- "Sheet" (9:16, 26.5 s, NO VOICEOVER)

The site drawn as a building on a cyanotype sheet, and then the sheet is plotted in front of you.

The medium is `claude-drawing-skill`'s blueprint engine: single-stroke draughting lettering, hatched
sections, dimension strings, a title block, and an engineer's red wax pencil over the print. Nothing
is a screen mock-up and nothing is flat vector -- the ink is on tracing linen, and the print is
imperfect on purpose.

The grammar is `huashu-art-motion`'s **t1 3B1B / technical** shot list: the camera holds on a large
view long enough to read it ("看得清就不动"), then moves ONCE to a new scale; every move has a reason
(the destination is already in frame), and the film is music-led -- no voice, the words are on the
sheet. `vox-director` supplies the beat structure: claim, evidence, address, with a beat change on
every cut, and no beat longer than 4 s.

The sheet is plotted in eight stages, so the drawing appears line by line under a travelling front:
that is the whole "performance" of the film, and it comes free from the engine's expose stage.
"""
import pathlib
import sys

import numpy as np
import skia

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "tools"))
sys.path.insert(0, str(HERE.parent / "_shared" / "eng"))

import filmkit as FK                                                     # noqa: E402
import transitions as TR                                                 # noqa: E402
import ty                                                                # noqa: E402
from filmkit import P, clamp, pop, hit, ramp                             # noqa: E402
from engine import Film, Item, ease_out_cubic                             # noqa: E402

W, H = 1080.0, 1920.0
SHEET_W, SHEET_H = 1600.0, 2844.0          # the drawn sheet, in the same units as the frame
BPM = 92.0
DUR = 26.5

CREAM = (250, 244, 232)
BLUE_INK = (16, 42, 78)
VERM = (233, 94, 40)

# One beat per line of the sheet's story: (t, camera centre x/y, zoom). Zoom 1.0 shows the frame;
# below 1 shows less of the sheet, i.e. pushes in. Values are sheet coordinates.
# Framing note: at zoom z the frame is 1080/z wide and 1920/z tall in sheet units, so every wide
# shot has to be checked against the sheet's own rectangle (0..1600, 0..2844) or the dark table shows
# through and the "print on a desk" illusion breaks. z = 0.675 makes the frame exactly the sheet.
SHOTS = [
    (0.00, 800, 1422, 0.675),     # the whole sheet, edge to edge: the object arrives already drawn
    (1.61, 790, 1210, 0.80),      # wider on the two views, the pen still plotting the lower half
    (5.22, 430, 800, 1.30),       # 1 ELEVATION: the page read as a facade
    (7.83, 380, 620, 1.70),       # push onto the masthead and the hero window
    (10.43, 950, 790, 1.34),      # 2 SECTION A-A: brief, scope, build, handover
    (13.04, 420, 1420, 1.30),     # 3 PLAN: three kinds of work on one floor
    (15.65, 1040, 1380, 1.26),    # 4 DETAIL: the budget, enlarged
    (18.26, 900, 1800, 0.95),     # schedule + general notes
    (20.87, 1150, 2040, 1.22),    # the title block: the address as it is printed
    (23.48, 800, 1422, 0.675),    # pull back to the whole sheet and hold it
]
CUTS = [s[0] for s in SHOTS[1:]]

# stage reveal times: the sheet is plotted, and each stage lands on a beat
STAGE_AT = [0.05, 2.40, 4.20, 6.00, 9.00, 15.50, 20.60]
# the near-empty first stage (border + title block only) is skipped: a sheet film cannot open on
# five seconds of blank linen, and the views are what the film is about
PLATES = ["bp_views", "bp_dims", "bp_plan", "bp_detail", "bp_notes", "bp_pencil", "bp_print"]
FRONT_AT = [0.05, 2.40, 4.20, 6.00, 9.00, 15.50, 20.60]

CAPS = [
    (0.30, 1.50, "A site is a building.", None),
    (1.75, 5.05, "It has a facade, a section and a plan.", None),
    (5.40, 7.70, "The elevation is what people see first.", "hand-written HTML"),
    (8.00, 10.30, "A masthead, a hero, three kinds of work.", None),
    (10.60, 12.90, "The section is how it gets made.", "brief > scope > build > handover"),
    (13.20, 15.50, "Four stages, in order, on one floor.", None),
    (15.80, 18.10, "And the budgets set before the first line.", "LCP  ·  CLS  ·  INP"),
    (18.40, 20.70, "Checked against the live site.", None),
    (21.00, 23.30, "Drawn, checked, handed over.", "one point of contact"),
    (23.60, 26.20, None, None),
]
# ------------------------------------------------------------------ the sheet on screen
class Sheet(Item):
    """The drawn sheet, blitted as a world object, with the plot front running down it.

    The renderer's own plate path is one image per stage and would have to re-render for every
    frame; here the eight stages are loaded once and the last one is drawn, then the front (a soft
    cyan-white band with the pen line at its edge) travels down the page as the plot advances.
    Rebuilding the artwork is the honest way to show a plotter, but at 30 fps it costs 16 s a frame.
    """

    z = 0

    def __init__(self):
        super().__init__(-10, None, 0, sfx=False)
        self.stages = [None] * len(PLATES)
        self.front_y = {}

    def visible(self, t):
        return True

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-40, -40, SHEET_W + 40, SHEET_H + 40)

    def _img(self, i):
        # only the stage on screen is ever needed; keep a couple of neighbours so a rewind does not
        # re-decode, and let the rest go (eight 1600x2844 plates is 130 MB of RGBA)
        for k in range(len(self.stages)):
            if k not in (i, i - 1, i + 1):
                self.stages[k] = None
        if self.stages[i] is None:
            from PIL import Image
            path = HERE / "assets" / "plates" / f"{PLATES[i]}.jpg"
            a = np.asarray(Image.open(path).convert("RGB"), np.float32) / 255.0
            a = np.clip((a - 0.5) * 1.16 + 0.52, 0.0, 1.0)     # a touch more contrast: the ink must bite
            a = (a * 255).astype(np.uint8)
            rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
            self.stages[i] = skia.Image.fromarray(np.ascontiguousarray(rgba), skia.kRGBA_8888_ColorType)
        return self.stages[i]

    def draw(self, c, res, t):
        # which stage is up: the last one whose reveal time has passed (they are cumulative)
        k = -1
        for i, ts in enumerate(STAGE_AT):
            if t >= ts:
                k = i
        if k < 0:
            return
        img = self._img(k)
        p = skia.Paint()
        p.setAntiAlias(True)
        c.drawImageRect(img, skia.Rect.MakeXYWH(0, 0, img.width(), img.height()),
                        skia.Rect.MakeXYWH(0, 0, SHEET_W, SHEET_H),
                        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
        # the plot front: the stage's progress down the sheet, as a soft band with a bright pen edge
        if k < len(STAGE_AT) - 1:
            u = clamp((t - STAGE_AT[k]) / max(0.35, STAGE_AT[k + 1] - STAGE_AT[k] - 0.5))
            fy = SHEET_H * (u ** 0.85)
            g = skia.GradientShader.MakeLinear(
                [skia.Point(0, fy - 110), skia.Point(0, fy)],
                [skia.ColorSetARGB(0, 210, 240, 255), skia.ColorSetARGB(26, 200, 236, 255),
                 skia.ColorSetARGB(96, 236, 250, 255)], [0.0, 0.88, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, fy - 110, SHEET_W, 111), skia.Paint(Shader=g))


class SheetBed(Item):
    """Under the sheet: the dark studio the print is lying on. Keeps the frame from being all blue."""

    z = -20

    def __init__(self):
        super().__init__(-50, None, -20, sfx=False)

    def visible(self, t):
        return True

    def bounds(self, res):
        return None

    def draw(self, c, res, t):
        c.drawRect(skia.Rect.MakeXYWH(-3000, -3000, 12000, 12000), P((13, 13, 16)))
        g = skia.GradientShader.MakeRadial(
            skia.Point(600, 600), 3400,
            [skia.ColorSetARGB(46, 120, 128, 150), skia.ColorSetARGB(0, 13, 13, 16)], [0.0, 1.0])
        c.drawRect(skia.Rect.MakeXYWH(-3000, -3000, 12000, 12000), skia.Paint(Shader=g))


class Front(Item):
    """The strip of bare linen along the top edge of the print, so the sheet reads as an object."""

    z = 5

    def visible(self, t):
        return True

    def bounds(self, res):
        return skia.Rect.MakeLTRB(-80, -80, SHEET_W + 80, SHEET_H + 80)

    def draw(self, c, res, t):
        # the print's edge: bare linen, a lit lip, and a shadow falling onto the dark bed
        e = 12.0
        c.drawRect(skia.Rect.MakeXYWH(-e, -e, SHEET_W + 2 * e, e), P((238, 235, 226)))
        c.drawRect(skia.Rect.MakeXYWH(-e, SHEET_H, SHEET_W + 2 * e, e), P((238, 235, 226)))
        c.drawRect(skia.Rect.MakeXYWH(-e, 0, e, SHEET_H), P((238, 235, 226)))
        c.drawRect(skia.Rect.MakeXYWH(SHEET_W, 0, e, SHEET_H), P((238, 235, 226)))
        for i in range(14):
            a = 0.20 * (1 - i / 14.0) ** 1.6
            c.drawRect(skia.Rect.MakeXYWH(-e - i, SHEET_H + e + i, SHEET_W + 2 * e + 2 * i, 1.0),
                       P((0, 0, 0), a))
            c.drawRect(skia.Rect.MakeXYWH(SHEET_W + e + i, -e - i, 1.0, SHEET_H + 2 * e + 2 * i),
                       P((0, 0, 0), a))


# ------------------------------------------------------------------ type
class Caps(FK.ScreenCard):
    """Two registers only: a cream clause, and the sheet's own wording under it in small caps."""

    z = 40

    def __init__(self, film):
        super().__init__(film, None, self.z)

    def draw(self, c, res, t):
        for (t0, t1, line, sub) in CAPS:
            if line is None or not (t0 <= t <= t1 + 0.3):
                continue
            a = ramp(t, t0, 0.26) * (1 - ramp(t, t1, 0.18))
            if a <= 0.01:
                continue
            self.screen(c, t)
            # a soft bed under the words so they never fight the drawing
            gh = 210 if sub else 150
            g = skia.GradientShader.MakeLinear(
                [skia.Point(0, 1560), skia.Point(0, 1560 + gh)],
                [skia.ColorSetARGB(0, 5, 9, 16), skia.ColorSetARGB(int(214 * a), 5, 9, 16),
                 skia.ColorSetARGB(int(226 * a), 5, 9, 16)], [0.0, 0.30, 1.0])
            c.drawRect(skia.Rect.MakeXYWH(0, 1560, W, gh + 300), skia.Paint(Shader=g))
            k = 1.0 + 0.05 * (1 - pop(t, t0, 0.5, 2.2))
            c.save()
            c.translate(W / 2, 1692)
            c.scale(k, k)
            ln = ty.wrap(line, str(FK.UI), 58, W - 104)
            yy = -((len(ln) - 1) * 72) / 2
            for l in ln:
                ty.draw(c, l, 0, yy, rgb=CREAM, a=a, align="center")
                yy += 72
            if sub:
                sl = ty.layout(sub, str(FK.LABEL), 26)
                ty.draw(c, sl, 0, yy + 18, rgb=(255, 202, 150), a=a * 0.9, align="center")
            c.restore()
            c.restore()


class EndMark(FK.ScreenCard):
    """The address, on top of the title block it is also printed in."""

    z = 42

    def __init__(self, film):
        super().__init__(film, None, self.z)

    def draw(self, c, res, t):
        t0, t1 = 23.9, DUR
        if not (t0 <= t <= t1):
            return
        a = ramp(t, t0, 0.45)
        self.screen(c, t)
        sz = FK.type_fit("ZERO VAST", 200, W - 260, kind="display", min_size=60)
        ty.draw(c, ty.layout("ZERO VAST", str(FK.DISPLAY), sz), W / 2, 980, rgb=CREAM, a=a, align="center")
        c.drawRect(skia.Rect.MakeXYWH(W / 2 - 190, 1030, 380, 3.0), P(VERM, a))
        ty.draw(c, ty.layout("zero-vast.vercel.app", str(FK.UI), 58), W / 2, 1132,
                rgb=CREAM, a=ramp(t, t0 + 0.3, 0.4), align="center")
        ty.draw(c, ty.layout("Khammam, Telangana   ·   one point of contact", str(FK.UI), 28), W / 2, 1190,
                rgb=(240, 226, 210), a=ramp(t, t0 + 0.55, 0.4), align="center")
        c.restore()


class Cuts(Item):
    z = 70

    def __init__(self):
        super().__init__(-5, None, 70, sfx=False)
        self.tr = [(CUTS[1], TR.Leak(dur=0.55, colour=(150, 210, 255), x=0.5, y=0.35)),
                   (CUTS[2], TR.Whip(dur=0.22, direction=1)),
                   (CUTS[3], TR.PushThrough(dur=0.34, rgb=(14, 18, 26))),
                   (CUTS[5], TR.CardSwing(dur=0.36, rgb=(236, 233, 224))),
                   (CUTS[6], TR.Whip(dur=0.20, direction=-1))]

    def draw(self, c, res, t):
        for t_cut, tr in self.tr:
            if abs(t - t_cut) < 0.45:
                tr.draw(c, t, t_cut)


class Grain(Item):
    z = 71

    def __init__(self, a=0.05):
        super().__init__(-5, None, 71, sfx=False)

    def draw(self, c, res, t):
        n = int(t * 30)
        for i in range(130):
            x = (i * 769.0 + n * 91) % W
            y = (i * 431.0 + n * 137) % H
            c.drawRect(skia.Rect.MakeXYWH(x, y, 2.0, 2.0), P((255, 250, 240), 0.045))


def build_film(doc):
    """Timed from the shot list above, not from a recorded take: no timing.json is read."""
    film = Film(DUR, fps=30, look=dict(board="studio.png", bg=(11, 12, 15), grade=(1.0, 1.0, 1.0),
                                       grain=0.0, glow=0.0, vignette=0.08, curve=0.02, dim=(10, 12, 16)))
    film.fade_in, film.fade_out = 0.35, 1.0
    film.items.remove(film.board)
    film.add(SheetBed())
    film.add(Sheet())
    film.add(Front())

    # One framing per shot, hard cut between them. A sheet film wants a rostrum that HOLDS: if the
    # view is legible, moving the camera only makes it harder to read (huashu: 看得清就不动). The
    # motion on screen comes from the plot front, not from a drifting frame.
    film.cam(0.0, SHOTS[0][1], SHOTS[0][2], SHOTS[0][3])     # the spline path needs at least one key
    cf = FK.CutFilm(film)
    film = cf
    for (t, cx, cy, z) in SHOTS:
        cf.shot(t, cx, cy, z)

    film.add(Caps(film))
    film.add(EndMark(film))
    film.add(Cuts())
    film.add(Grain())
    film.add(FK.Vignette(film, None, strength=0.30, warm=(8, 10, 14)))

    # music: a hit on every cut, a pen tick on every plot stage
    for i, c in enumerate(CUTS):
        film.cue("impact" if i % 2 == 0 else "stamp", c, 0.45)
    for i, ts in enumerate(FRONT_AT[1:]):
        film.cue("tick", ts, 0.30)
    film.cue("shimmer", 20.4, 0.35)
    film.cue("impact", 23.9, 0.5)
    return film
