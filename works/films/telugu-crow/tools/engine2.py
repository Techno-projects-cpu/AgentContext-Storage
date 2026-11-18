"""The cinematic-film renderer, re-based so one world unit is one pixel of a 1080-wide frame.

Two deliberate differences from engine.Renderer:

1. `s = width / 1080` instead of `width / 3840`. engine assumes a 3840-wide world (right for photos
   and print on a board) which shrinks vector art to 28 % and upscales it: soft edges, no detail.
   Here the design frame is 1080x1920, so at zoom 1 one unit is one output pixel.

2. A fresh raster surface per sub-frame. Reusing one surface through `with surface as canvas` and
   snapshotting it inside a motion-blurred frame corrupted every sub-frame after the first (the
   picture tore and ghosted). Allocation per frame costs a few ms and cannot go stale.
"""
import math
import pathlib
import sys

import numpy as np
import skia

for _p in ("/tmp/cs/skills/cinematic-film/skills/cinematic-film/scripts",):
    if _p not in sys.path and __import__("os").path.isdir(_p):
        sys.path.insert(0, _p)
from engine import Renderer, clamp, color  # noqa: E402

import os
DESIGN_W = 1080.0
ENGINE = os.environ.get("CF_ENGINE", "/tmp/cs/skills/cinematic-film/skills/cinematic-film/scripts")


class Plates:
    """The painted sets: one dry-brush gouache page per stage, blitted with the camera.

    Painted by tools/plates.py at 1080-design-pixel scale over PLATE = (x0, y0, w, h), so the same
    page serves every framing of a stage. `paper` is the stock the whole film is pressed onto; it
    rides in screen space, so the grain never swims when the camera moves.
    """

    def __init__(self, root, blur=0.55):
        import json
        self.rects, self.imgs, self.blur = {}, {}, blur
        d = root / "assets" / "plates"
        if not (d / "plates.json").exists():
            raise SystemExit(f"no painted plates in {d} -- run: python3 tools/plates.py --out assets/plates")
        meta = json.loads((d / "plates.json").read_text())
        for name, m in meta.items():
            path = d / f"{name}.jpg"
            if not path.exists():
                continue
            # decode with PIL and hand skia raw pixels: drawing a JPEG-decoded skia.Image inside a
            # scaled canvas segfaults this build, raw RGBA does not
            from PIL import Image
            a = np.asarray(Image.open(path).convert("RGB"), np.uint8)
            rgba = np.dstack([a, np.full(a.shape[:2], 255, np.uint8)])
            self.imgs[name] = skia.Image.fromarray(np.ascontiguousarray(rgba), skia.kRGBA_8888_ColorType)
            self.rects[name] = (m["x"], m["y"], m["w"], m["h"])

    def draw(self, c, name, a=1.0):
        if name not in self.imgs:
            return False
        x, y, w, h = self.rects[name]
        p = skia.Paint()
        p.setAlphaf(max(0.0, min(1.0, a)))
        p.setAntiAlias(True)
        # NO image filter here: a blur shader on a large image inside a scaled canvas crashes
        # this build of skia; the plate is painted soft anyway and only needs bilinear sampling
        c.drawImageRect(self.imgs[name], skia.Rect.MakeXYWH(0, 0, self.imgs[name].width(),
                                                           self.imgs[name].height()),
                        skia.Rect.MakeXYWH(x, y, w, h),
                        skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), p)
        return True


class Renderer2(Renderer):
    def __init__(self, film, width=1080, height=1920, doc=None):
        super().__init__(film, width, height, doc)
        self.s = width / DESIGN_W

    def _surface(self):
        info = skia.ImageInfo.Make(self.W, self.H, skia.ColorType.kRGBA_8888_ColorType,
                                   skia.AlphaType.kPremul_AlphaType)
        return skia.Surface.MakeRaster(info)

    def attach(self, root):
        """hand the renderer the painted plates; call once, after construction"""
        self.plates = Plates(pathlib.Path(root))
        return self

    # which painted page is the room in? the stage owns the answer; the plate is only the paint
    PLATE_OF = {"field": "field", "title": "field", "end": "end", "pot": "pot",
                "beak": "pot", "drop": "pot", "rise": "pot", "drink": "pot", "happy": "pot",
                "idea": "pot", "lizard": "pot", "stones": "pot", "fly": "pot",
                "quiz": "quiz", "moral": "quiz"}

    def stage_at(self, t):
        """the stage live at t: the first one in the list whose span covers this moment"""
        for it in self.items:
            if type(it).__name__.endswith("Stage") and it.visible(t):
                return getattr(it, "name", None)
        return None

    def paint_plate(self, c, t):
        """the set: a gouache page, blitted in world space under the cut-outs"""
        name = self.stage_at(t)
        plate = self.PLATE_OF.get(name)
        if not plate or not getattr(self, "plates", None):
            return False
        return self.plates.draw(c, plate)

    def draw_world(self, t):
        f = self.film
        cx, cy, z, rot = f.camera(t)
        k = z * self.s
        self.res.screen_scale = k
        hw, hh = self.W / 2 / k * 1.10, self.H / 2 / k * 1.10
        self.res.view = view = skia.Rect.MakeLTRB(cx - hw, cy - hh, cx + hw, cy + hh)
        surface = self._surface()
        c = surface.getCanvas()
        c.clear(color(f.look["bg"]))
        c.save()
        c.translate(self.W / 2, self.H / 2)
        c.scale(k, k)
        c.rotate(rot)
        c.translate(-cx, -cy)
        if not self.paint_plate(c, t):
            for it in self.items:
                if not it.visible(t):
                    continue
                b = it.bounds(self.res)
                if b is None or skia.Rect.Intersects(b, view):
                    it.draw(c, self.res, t)
            c.restore()
            img = surface.makeImageSnapshot()
            out = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
            return self.press(out)

        for it in self.items:
            if not it.visible(t) or type(it).__name__.endswith("Stage"):
                continue
            b = it.bounds(self.res)
            if b is None or skia.Rect.Intersects(b, view):
                it.draw(c, self.res, t)
        foc = f.focus_at(t)
        if foc:
            fx, fy, fr, fs = foc
            dr, dg, db = f.look.get("dim", (6, 4, 3))
            g = skia.GradientShader.MakeRadial(
                skia.Point(fx, fy), max(10.0, fr * 2.4),
                [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0),
                 skia.Color(dr, dg, db, int(255 * clamp(fs))),
                 skia.Color(dr, dg, db, int(255 * min(0.92, fs + 0.25)))], [0.0, 0.3, 0.68, 1.0])
            p = skia.Paint()
            p.setShader(g)
            c.drawRect(skia.Rect.MakeXYWH(cx - 60000, cy - 60000, 120000, 120000), p)
        c.restore()
        img = surface.makeImageSnapshot()
        out = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
        return self.press(out)

    def press(self, out):
        """the print pass: a sheet of the book's paper over everything (screen-space, so it never swims)

        Screen space is the point: a grain that rides in world space slides across the picture whenever
        the camera moves, which reads as noise rather than as stock.
        """
        if getattr(self, "_paper", None) is None:
            path = pathlib.Path(getattr(self, "_root", ".")) / "assets" / "plates" / "paper.jpg"
            self._paper = None if not path.exists() else np.asarray(
                __import__("PIL.Image", fromlist=["Image"]).open(path).convert("L"), np.float32) / 255.0
        pap = self._paper
        if pap is not None:
            h, w = out.shape[:2]
            ys = (np.arange(h) * pap.shape[0] // h) % pap.shape[0]
            xs = (np.arange(w) * pap.shape[1] // w) % pap.shape[1]
            g = pap[ys][:, xs]
            out *= (0.94 + 0.12 * g)[..., None]
        # the frame() path casts straight to uint8: anything above 255 would wrap and turn the
        # picture into garbage, so the press has to clamp
        return np.clip(out, 0.0, 255.0)
