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
import sys

import numpy as np
import skia

sys.path.insert(0, "/tmp/cs/skills/cinematic-film/scripts")
from engine import Renderer, clamp, color  # noqa: E402

DESIGN_W = 1080.0


class Renderer2(Renderer):
    def __init__(self, film, width=1080, height=1920, doc=None):
        super().__init__(film, width, height, doc)
        self.s = width / DESIGN_W

    def _surface(self):
        info = skia.ImageInfo.Make(self.W, self.H, skia.ColorType.kRGBA_8888_ColorType,
                                   skia.AlphaType.kPremul_AlphaType)
        return skia.Surface.MakeRaster(info)

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
        for it in self.items:
            if not it.visible(t):
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
        return img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)[..., :3].astype(np.float32)
