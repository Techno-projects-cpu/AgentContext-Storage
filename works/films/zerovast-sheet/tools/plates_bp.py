#!/usr/bin/env python3
"""Paint the blueprint sheet for the ZeroVast "Sheet" ad: one large cyanotype sheet of the site,
drawn as a building, rendered in cumulative stages so the film can watch it being plotted.

Layout is a real drawing-sheet grid on a 1600 x 2844 page (9:16), because the film's camera moves
over it at four scales and every region has to work as a composition at each one:

    row A  y 250-1080   ELEVATION (x 150-600)   SECTION A-A (x 690-1180)   margin notes (x 1240-1520)
    row B  y 1150-1700  PLAN (x 150-600)        DETAIL 1, the budget (x 690-1180)
    row C  y 1770-2260  GENERAL NOTES (x 150-600)  STAGE SCHEDULE (x 690-1180)
    row D  y 2320-2500  scale, north             title block (x 940-1520, y 2450-2760)

Stages are cumulative: each saved image contains everything drawn so far, so the film reveals them
in order with a clip front and the drawing appears to be plotted.

  python3 tools/plates_bp.py --out assets/plates
"""
import argparse
import json
import pathlib
import sys

LIB = pathlib.Path("/tmp/sk/claude-drawing-skill/lib")
if not LIB.exists():
    sys.exit("claude-drawing-skill is not cloned (expected lib/ at /tmp/sk/claude-drawing-skill/lib)")
sys.path.insert(0, str(LIB))
from blueprint import Blueprint                                        # noqa: E402

W, H = 1600, 2844
SS = 3                      # supersample: the camera pushes in, so the ink has to hold up
INK = 2.9                   # heavy lettering pen (blueprint.text takes a width, not a name)

M = 54
X0, Y0, X1, Y1 = M, M, W - M, H - M


# ------------------------------------------------------------------ the sheet
def sheet():
    bp = Blueprint(W, H, seed=23, ss=SS)
    bp.time, bp.contact = 1.0, 0.9
    bp.border(X0, Y0, X1, Y1, zones=(4, 8), size=13)
    bp.text("ZERO VAST / GENERAL ARRANGEMENT", X0 + 26, Y0 + 66, 32, "ls", pen=INK, spacing=0.18)
    bp.text("THE SITE, DRAWN AS A BUILDING : ELEVATION, SECTION, PLAN, SCHEDULE", X0 + 26, Y0 + 98,
            15, "ls", spacing=0.26)
    bp.line([(X0 + 26, Y0 + 112), (X1 - 26, Y0 + 112)], "thin", pool=False)
    bp.text("SHEET 01", X1 - 26, Y0 + 66, 15, "rs", spacing=0.3)
    return bp


def title_block(bp):
    bx0, by0 = X1 - 596, Y1 - 300
    cells = bp.table(bx0, by0, [302, 294], [56, 56, 56, 72], pen="thin", outer="heavy")
    bp.text("ZERO VAST", bx0 + 14, by0 + 42, 28, "ls", pen=INK, spacing=0.16)
    bp.text("WEB STUDIO", bx0 + 316, by0 + 40, 15, "ls", spacing=0.28)
    bp.text("KHAMMAM / TELANGANA", bx0 + 14, by0 + 98, 14, "ls", spacing=0.24)
    bp.text("DRAWN BY ONE PERSON", bx0 + 316, by0 + 98, 14, "ls", spacing=0.24)
    bp.text("GENERAL ARRANGEMENT", bx0 + 14, by0 + 154, 13, "ls", spacing=0.26)
    bp.text("SCALE 1:1 / AS BUILT", bx0 + 316, by0 + 154, 13, "ls", spacing=0.26)
    bp.text("ZERO-VAST.VERCEL.APP", bx0 + 14, by0 + 216, 18, "ls", pen=INK, spacing=0.10)
    bp.text("SHEET 01 OF 01", bx0 + 316, by0 + 216, 13, "ls", spacing=0.26)
    return bx0, by0


# ------------------------------------------------------------------ row A
def elevation(bp, x0=150.0, x1=600.0, top=470.0, ground=1030.0):
    """The page as a facade: masthead over the door, a hero window, three floors of work, steps."""
    bp.ground([(x0 - 34, ground), (x1 + 40, ground)], depth=15, every=24)
    bp.centerline([(x0 - 18, ground + 10), (x0 - 18, top - 34)], "fine")
    bp.box(x0, top, x1, ground, "heavy")
    bp.line([(x0 - 14, top), (x1 + 14, top)], "heavy", pool=False)
    bp.line([(x0 - 14, ground - 24), (x1 + 14, ground - 24)], "medium", pool=False)
    # masthead
    bp.text("ZERO VAST", (x0 + x1) / 2, top + 56, 32, "ms", pen=INK, spacing=0.24)
    bp.line([(x0, top + 78), (x1, top + 78)], "medium", pool=False)
    # hero window: the headline, then a lead-in line, then the button
    hx0, hx1, hy0 = x0 + 40, x1 - 40, top + 108
    hy1 = hy0 + 250
    bp.box(hx0, hy0, hx1, hy1, "medium")
    for i, wdt in enumerate((310, 250, 176)):
        bp.line([(hx0 + 26, hy0 + 62 + i * 52), (hx0 + 26 + wdt, hy0 + 62 + i * 52)], "heavy", pool=False)
    bp.line([(hx0 + 26, hy1 - 34), (hx0 + 150, hy1 - 34)], "fine", pool=False)     # the button
    bp.box(hx0 + 26, hy1 - 48, hx0 + 152, hy1 - 20, "fine")
    bp.text("WEBSITES BUILT TO PERFORM", (hx0 + hx1) / 2, hy1 + 30, 15, "ms", spacing=0.28)
    # three floors of work, each a window with a sill
    for i in range(3):
        fy0 = top + 420 + i * 128
        bp.box(x0 + 44, fy0, x1 - 44, fy0 + 96, "medium")
        bp.line([(x0 + 36, fy0 + 96), (x1 - 36, fy0 + 96)], "medium", pool=False)
        bp.line([(x0 + 70, fy0 + 40), (x0 + 70 + 190, fy0 + 40)], "thin", pool=False)
        bp.line([(x0 + 70, fy0 + 66), (x0 + 70 + 132, fy0 + 66)], "fine", pool=False)
        bp.text(f"0{i + 1}", x1 - 76, fy0 + 44, 22, "ms", pen=INK)
    # entrance and steps
    bp.box(x0 + 130, ground - 150, x1 - 130, ground, "medium")
    bp.line([(x0 + 112, ground - 8), (x1 - 112, ground - 8)], "thin", pool=False)
    bp.view_title(x0 + 2, top - 66, "1 / ELEVATION", sub="THE PAGE, FACING THE READER", size=24)
    return x0, x1, top, ground


def elevation_dims(bp, x0, x1, top, ground):
    """Dimension strings and levels, kept inside the margin: the drawing reads like a check print."""
    ys = [ground, ground - 150, top + 548, top + 420, top + 250, top + 78, top]
    for a, b in zip(ys, ys[1:]):
        if abs(a - b) < 40:
            continue
        bp.dim((x0 - 30, a), (x0 - 30, b), 26, text=f"{(abs(a - b) / 58.0):.2f}", size=12)
    bp.level(x1 + 20, ground, "+0.000", size=12, length=62)
    bp.level(x1 + 20, top + 250, "+7.800", size=12, length=62)
    bp.level(x1 + 20, top, "+12.800", size=12, length=62)


def section(bp, x0=690.0, x1=1180.0, top=470.0, base=1030.0):
    """Section A-A through the build: four chambers from BRIEF to HANDOVER, walls hatched, one stair."""
    bp.centerline([(x0 - 40, top - 26), (x0 - 40, base + 26)], "fine")
    bp.box(x0, top, x1, base, "heavy")
    bp.hatch([[(x0, top), (x0 + 40, top), (x0 + 40, base), (x0, base)]], 45, 7)
    bp.hatch([[(x1 - 40, top), (x1, top), (x1, base), (x1 - 40, base)]], 45, 7)
    bp.hatch([[(x0, base - 34), (x1, base - 34), (x1, base), (x0, base)]], -45, 8)
    names = ["BRIEF", "SCOPE", "BUILD", "HANDOVER"]
    for i, nm in enumerate(names):
        y0 = top + i * 140
        bp.text(nm, x0 + 64, y0 + 58, 28, "ls", pen=INK, spacing=0.20)
        bp.text(f"STAGE 0{i + 1}", x1 - 78, y0 + 58, 12, "rm", spacing=0.24)
        if i < 3:
            bp.hatch([[(x0 + 40, y0 + 140), (x1 - 40, y0 + 140),
                       (x1 - 40, y0 + 152), (x0 + 40, y0 + 152)]], 45, 7)
    # the pipeline runs up through all four chambers
    px = x1 - 26
    bp.line([(px, base - 44), (px, top + 26)], "thin", pool=False)
    bp.arrowhead((px, top + 22), (0, -1), 15, "filled")
    bp.text("STAGES IN ORDER", px - 12, (top + base) / 2, 11, "ms", rot=90, spacing=0.22)
    bp.view_title(x0 + 2, top - 66, "2 / SECTION A-A", sub="FOUR STAGES, IN ORDER", size=24)
    return x0, x1, top, base


def margin_notes(bp, x=1240.0, y=430.0):
    """The right margin, the way a drawing keeps its callouts and its sign-off out of the views."""
    bp.text("CALLOUTS", x, y, 15, "ls", pen=INK, spacing=0.3)
    bp.line([(x, y + 12), (x + 232, y + 12)], "thin", pool=False)
    items = [("1", "ELEVATION. THE PAGE AS", "IT IS FIRST SEEN."),
             ("2", "SECTION. FOUR STAGES", "IN THE ORDER THEY RUN."),
             ("3", "PLAN. THREE KINDS", "OF WORK ON ONE FLOOR."),
             ("4", "BUDGET. SET BEFORE", "THE FIRST LINE.")]
    yy = y + 52
    for num, a, b in items:
        bp.bubble(x + 16, yy + 10, 15, num, size=13)
        bp.text(a, x + 44, yy, 13, "ls", spacing=0.22)
        bp.text(b, x + 44, yy + 20, 13, "ls", spacing=0.22)
        yy += 84
    bp.text("WCAG 2.2 AA", x, y + 430, 15, "ls", pen=INK, spacing=0.26)
    bp.text("BUILT IN, NOT", x, y + 452, 13, "ls", spacing=0.24)
    bp.text("BOLTED ON", x, y + 472, 13, "ls", spacing=0.24)
    bp.text("NO FRAMEWORK", x, y + 530, 15, "ls", pen=INK, spacing=0.26)
    bp.text("HAND-WRITTEN", x, y + 552, 13, "ls", spacing=0.24)
    bp.text("HTML / CSS / JS", x, y + 572, 13, "ls", spacing=0.24)


# ------------------------------------------------------------------ row B
def plan(bp, x0=150.0, x1=600.0, top=1150.0, base=1640.0):
    """Plan: one floor divided into the three kinds of work, with door swings and a boundary."""
    bp.box(x0, top, x1, base, "heavy")
    # the party wall splits the plan in two, the corridor cuts across
    bp.line([(x0 + 250, top), (x0 + 250, base)], "medium", pool=False)
    bp.line([(x0, top + 300), (x1, top + 300)], "medium", pool=False)
    rooms = [("BROCHURE", x0 + 16, top + 16, x0 + 234, top + 284),
             ("STORE", x0 + 266, top + 16, x1 - 16, top + 284),
             ("LANDING", x0 + 16, top + 316, x0 + 234, base - 16),
             ("SERVICE", x0 + 266, top + 316, x1 - 16, base - 16)]
    for nm, rx0, ry0, rx1, ry1 in rooms:
        bp.text(nm, (rx0 + rx1) / 2, (ry0 + ry1) / 2, 17, "mm", spacing=0.3)
        bp.text("3.6 x 4.2", (rx0 + rx1) / 2, (ry0 + ry1) / 2 + 24, 11, "mm", spacing=0.2)
    # doors: a leaf and its swing arc, one into each side of the corridor
    for dx, dy, a0, a1 in ((x0 + 250, top + 300, 0, 90), (x0 + 250, base, 270, 360)):
        bp.line([(dx, dy), (dx + 54, dy)], "medium", pool=False)
        bp.arc(dx + 54, dy, 54, a0, a1, pen="fine")
    # the boundary and the site hatch outside it
    bp.dashed([(x0 - 24, top - 24), (x1 + 24, top - 24), (x1 + 24, base + 24), (x0 - 24, base + 24),
               (x0 - 24, top - 24)], "fine", (14, 6))
    bp.view_title(x0 + 2, top - 66, "3 / PLAN", sub="THREE KINDS OF WORK", size=24)
    bp.north(x1 + 40, top + 44, r=26)
    bp.dim((x0, base + 44), (x1, base + 44), -28, text=f"{(x1 - x0) / 58.0:.2f}", size=12)
    return x0, x1, top, base


def detail(bp, bx=722.0, by=1200.0):
    """Detail 4: the performance budget, enlarged -- the one technical claim the site makes."""
    bp.text("DETAIL 4 / PERFORMANCE BUDGET", bx, by - 36, 20, "ls", pen=INK, spacing=0.2)
    bx0 = bx
    w = [238, 198, 152]
    cells = bp.table(bx0, by, w, [64, 64, 64, 64], pen="thin", outer="heavy")
    hdr = ["METRIC", "BUDGET", "MEASURED"]
    for i, h in enumerate(hdr):
        bp.text(h, bx0 + sum(w[:i]) + 18, by + 42, 14, "ls", spacing=0.26)
    rows = ["LCP", "CLS", "INP"]
    for j, k in enumerate(rows):
        yy = by + 64 * (j + 1) + 42
        bp.text(k, bx0 + 18, yy, 24, "ls", pen=INK)
        bp.text("BUDGETED", bx0 + w[0] + 18, yy, 14, "ls", spacing=0.26)
        bp.text("AT BUILD", bx0 + w[0] + w[1] + 18, yy, 14, "ls", spacing=0.26)
    bp.dim((bx0 + 16, by + 300), (bx0 + 570, by + 300), -28,
           text="SET BEFORE THE FIRST LINE OF CODE", size=13)
    bp.text("NO PAGE-BUILDER PAYLOAD IS SHIPPED TO MAKE THESE.", bx, by + 350, 12, "ls", spacing=0.20)
    bp.text("THE PAGE IS HTML, CSS AND A LITTLE JAVASCRIPT.", bx, by + 370, 12, "ls", spacing=0.20)
    return bx0, by, w


# ------------------------------------------------------------------ row C
def schedule(bp, x0=690.0, y0=1770.0):
    """A schedule of the four stages: what you get, who does it, when. The honest version of a Gantt."""
    bp.text("STAGE SCHEDULE", x0, y0, 18, "ls", pen=INK, spacing=0.24)
    widths = [92, 268, 156, 126]
    cells = bp.table(x0, y0 + 20, widths, [46, 54, 54, 54, 54], pen="thin", outer="medium")
    hdr = ["STAGE", "DELIVERABLE", "BY", "WHEN"]
    for i, h in enumerate(hdr):
        bp.text(h, x0 + sum(widths[:i]) + 14, y0 + 52, 12, "ls", spacing=0.26)
    rows = [("01", "BRIEF", "YOU", "DAY 1"),
            ("02", "SCOPE", "TOGETHER", "WEEK 1"),
            ("03", "BUILD", "ONE PERSON", "WEEK 1-3"),
            ("04", "HANDOVER", "REPO + TOUR", "WEEK 4")]
    for j, (n, d, by_, when) in enumerate(rows):
        yy = y0 + 20 + 46 + 54 * j + 36
        bp.text(n, x0 + 14, yy, 13, "ls", spacing=0.24)
        bp.text(d, x0 + widths[0] + 14, yy, 13, "ls", spacing=0.22)
        bp.text(by_, x0 + widths[0] + widths[1] + 14, yy, 12, "ls", spacing=0.2)
        bp.text(when, x0 + widths[0] + widths[1] + widths[2] + 14, yy, 12, "ls", spacing=0.2)
    bp.text("EVERY STAGE ENDS WITH THE REPOSITORY IN YOUR HANDS.", x0, y0 + 300, 13, "ls", spacing=0.22)
    return x0, y0


def notes(bp, x=150.0, y=1770.0):
    bp.text("GENERAL NOTES", x, y, 18, "ls", pen=INK, spacing=0.24)
    bp.line([(x, y + 14), (x + 440, y + 14)], "thin", pool=False)
    lines = [("01", "HAND-WRITTEN HTML, CSS, VANILLA JS."),
             ("02", "NO FRAMEWORK, NO PAGE-BUILDER BLOAT."),
             ("03", "WCAG 2.2 AA, BUILT IN NOT BOLTED ON."),
             ("04", "LCP / CLS / INP BUDGETED BEFORE BUILD."),
             ("05", "REPOSITORY, DEPLOY STEPS, WALKTHROUGH."),
             ("06", "NO LOCK-IN. NO SEAT LICENCES."),
             ("07", "ONE POINT OF CONTACT, START TO FINISH.")]
    for i, (num, tx) in enumerate(lines):
        yy = y + 56 + i * 34
        bp.text(num, x, yy, 13, "ls", spacing=0.3)
        bp.text(tx, x + 44, yy, 14, "ls", spacing=0.20)
    bp.scale_bar(x + 4, y + 340, 118.0, units=(0, 1, 2, 3), sub=10, label="GRAPHIC SCALE 1:1", size=12)
    return x, y


# ------------------------------------------------------------------ the engineer's pencil
def red_pencil(bp, tb, dx):
    """Red wax pencil over the print: circle, ticks, a margin note. This is what makes it a document."""
    bx0, by0 = tb
    # a ring round the studio name in the title block, and a tick down the budget rows
    bp.red([(bx0 + 6, by0 + 6), (bx0 + 300, by0 + 4), (bx0 + 302, by0 + 56), (bx0 + 8, by0 + 58),
            (bx0 + 6, by0 + 6)], width=3.2, smooth=True)
    ebx, eby, w = dx
    for j in range(3):
        yy = eby + 64 * (j + 1) + 40
        bp.red([(ebx + 582, yy), (ebx + 600, yy + 14), (ebx + 632, yy - 22)], width=4.0)
    # the margin note, written up the right edge of the sheet
    bp.text("CHECKED AGAINST THE LIVE SITE", X1 - 62, 1520, 15, "ms", rot=90, pen=INK, spacing=0.28)
    bp.red([(X1 - 26, 1640), (X1 - 16, 1560), (X1 - 28, 1470), (X1 - 18, 1390)], width=3.4)
    # and the one thing an engineer would write on it: it is live
    bp.red([(760, 2240), (860, 2234), (960, 2244), (1060, 2232)], width=3.4)
    bp.red([(760, 2262), (900, 2258), (1040, 2266)], width=2.4)


# ------------------------------------------------------------------ build
def build(out_dir):
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    bp = sheet()
    tb = title_block(bp)
    bp.stage("sheet")

    ax0, ax1, atop, aground = elevation(bp)
    cx0, cx1, ctop, cbase = section(bp)
    bp.stage("views")

    elevation_dims(bp, ax0, ax1, atop, aground)
    margin_notes(bp)
    bp.stage("dims")

    plan(bp)
    bp.stage("plan")

    dx = detail(bp)
    schedule(bp)
    bp.stage("detail")

    notes(bp)
    bp.stage("notes")

    red_pencil(bp, tb, dx)
    bp.stage("pencil")

    bp.expose(time=1.02, contact=0.8)
    bp.stage("print")

    meta = {}
    for name, im in bp.stages:
        path = out / f"bp_{name}.jpg"
        im.save(path, quality=90, subsampling=0)
        meta[f"bp_{name}"] = {"x": 0.0, "y": 0.0, "w": float(W), "h": float(H)}
        print("wrote", path)
    (out / "plates.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/plates")
    build(ap.parse_args().out)
