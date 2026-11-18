"""Picture-quality extensions for the cinematic-film engine, applied at scene import.

The stock engine (Moh4696/cinematic-skill, MIT) is built to look like printed paper on a board.
This film needs weather: fire, ash, shock rings, a sky that turns, and a finish that holds up at
1080x1920. Everything here is a monkeypatch or a new item class, so the engine stays unmodified
and the project stays reproducible from the skill.

  Plume        fire and ash rising with the column, one dot per particle, deterministic in t
  Glow         a soft light source (fire, the sun) that can pulse
  RingWave     an expanding shock ring, or a set of nested ones
  SkyBand      a banded sunset field that grades from one palette to another
  PrintDim     Print whose dim darkens by multiply (an overlay turned prints grey, not dark)
  Renderer     post(): 3x3 grade, full-resolution grain, glow that reads at 1080 wide

apply_patch() is idempotent: workers call it once per process.
"""
import math
import pathlib

import skia
import numpy as np
from PIL import Image, ImageFilter

import engine
from engine import Item, clamp, ease_in_out, ease_out_cubic, paint, ramp, SAMPLING


# ------------------------------------------------------------------ items
def _noise(seed, n):
    """Deterministic pseudo-random numbers: a plum of values from a seed, no global RNG state."""
    rng = np.random.default_rng(seed)
    return rng.random(n)


class Plume(Item):
    """A column of fire and ash: particles rise, spread, cool and fade, all a pure function of t.

    y0 is the vent. `rise` is how far the column climbs (world px). `spread` is its width there.
    kind 'fire' runs yellow -> orange -> red over the first 0.45 of the climb; 'ash' runs
    iron-grey and keeps going. `turb` adds lateral churn so the column never looks like a cone.
    """
    z = 40

    def __init__(self, x, y, t_in, rise, spread, count=340, t_out=None, seed=11, kind="fire",
                 rate=0.55, size=34, speed=1.0, turb=1.0, rgb=None, z=None, sfx=True):
        super().__init__(t_in, t_out, z, sfx)
        self.x, self.y, self.rise, self.spread = x, y, rise, spread
        self.count, self.kind, self.rate, self.size, self.speed, self.turb = count, kind, rate, size, speed, turb
        h = _noise(seed, 6 * count).reshape(count, 6)
        self.life = rate * (0.55 + 0.9 * h[:, 0])                  # each particle's own lifetime
        self.off = h[:, 1]                                          # stagger
        self.ang = h[:, 2] * 2 * math.pi                            # where in the column it starts
        self.rad = 0.25 + 0.75 * h[:, 3]                            # how far out from the axis
        self.wob = h[:, 4] * 2 * math.pi
        self.sz = 0.45 + 0.9 * h[:, 5]
        self.rgb = rgb
        self.box = skia.Rect.MakeLTRB(x - spread * 2.4, y - rise * 1.5, x + spread * 2.4, y + rise * 0.35)

    def bounds(self, res):
        return self.box

    def _colour(self, u, a):
        if self.rgb:
            return self.rgb
        if self.kind == "fire":
            if u < 0.18:
                return (255, 246, 214)
            if u < 0.42:
                return (255, 186, 92)
            if u < 0.7:
                return (243, 118, 46)
            return (176, 54, 32)
        return (108, 98, 92) if u < 0.5 else (64, 58, 56)

    def draw(self, c, res, t):
        a0 = self.fade(t)
        if a0 <= 0:
            return
        for i in range(self.count):
            u = (t - self.t_in) * self.speed / self.life[i] - self.off[i]
            if u <= 0 or u >= 1:
                continue
            # the climb: fast off the vent, slowing as the column loses lift
            climb = self.rise * (u ** 0.72)
            spread = self.spread * (0.12 + 0.88 * u ** 1.5)
            ang = self.ang[i] + 1.6 * u * self.turb
            rad = self.rad[i] * spread
            x = self.x + math.cos(ang) * rad * 0.55 + math.sin(self.wob[i] + 5.0 * u) * spread * 0.10
            y = self.y - climb + math.sin(ang) * rad * 0.16
            fade = min(1.0, u / 0.10) * (1.0 - u) ** 1.25
            r = self.size * self.sz[i] * (0.45 + 1.25 * u) * (0.7 + 0.3 * self.turb)
            c.drawCircle(x, y, r, paint(self._colour(u, fade), 0.72 * fade * a0, blur=r * 0.55))


class Glow(Item):
    """A soft light: the vent, the sun through ash, a lit patch of sky. Pulse is a slow sine."""
    z = 38

    def __init__(self, x, y, r, t_in=0.0, t_out=None, rgb=(255, 170, 80), a=0.8, pulse=0.0, z=None, sfx=False):
        super().__init__(t_in, t_out, z, sfx)
        self.x, self.y, self.r, self.rgb, self.a, self.pulse = x, y, r, rgb, a, pulse
        self.box = skia.Rect.MakeXYWH(x - r * 3, y - r * 3, r * 6, r * 6)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a = self.a * self.fade(t)
        if a <= 0:
            return
        if self.pulse:
            a *= 1 + self.pulse * math.sin(t * 6.1)
        g = skia.GradientShader.MakeRadial(skia.Point(self.x, self.y), self.r,
                                           [skia.Color(*self.rgb, int(255 * clamp(a))),
                                            skia.Color(*self.rgb, int(255 * clamp(a) * 0.45)),
                                            skia.Color(*self.rgb, 0)], [0.0, 0.38, 1.0])
        p = skia.Paint(); p.setShader(g)
        p.setBlendMode(skia.BlendMode.kScreen)
        c.drawRect(self.box, p)


class RingWave(Item):
    """Expanding rings: a shock front running out from a point, drawn as a soft band that thins."""
    z = 36

    def __init__(self, x, y, t_in, r_end, dur=1.4, width=90, rgb=(255, 236, 210), a=0.9, rings=1,
                 gap=0.22, t_out=None, z=None, sfx=False):
        super().__init__(t_in, t_out, z, sfx)
        self.x, self.y, self.r_end, self.dur, self.wd = x, y, r_end, dur, width
        self.rgb, self.a, self.rings, self.gap = rgb, a, rings, gap
        self.box = skia.Rect.MakeXYWH(x - r_end * 1.2, y - r_end * 1.2, r_end * 2.4, r_end * 2.4)

    def bounds(self, res):
        return self.box

    def draw(self, c, res, t):
        a0 = self.fade(t)
        if a0 <= 0:
            return
        for k in range(self.rings):
            u = ease_out_cubic(ramp(t, self.t_in + k * self.gap, self.dur))
            if u <= 0 or u >= 1:
                continue
            r = self.r_end * u
            a = self.a * a0 * (1 - u) ** 1.6 / (1 + 0.35 * k)
            wd = self.wd * (1.25 - 0.75 * u)
            c.drawCircle(self.x, self.y, r, paint(self.rgb, a * 0.85, stroke=wd, blur=wd * 0.5))


class SkyBand(Item):
    """A sky that grades from one palette to another: horizontal bands with a soft sun, so the
    Ashcroft plates in the next beat do not appear out of nowhere. Each band eases in a beat late.
    """
    z = 5

    def __init__(self, rect, t_in, t_out, pal0, pal1, t_change, seed=5, bands=7):
        super().__init__(t_in, t_out, None, False)
        self.rect, self.pal0, self.pal1, self.t_change = rect, pal0, pal1, t_change
        self.bands = bands
        h = _noise(seed, bands * 2)
        self.jitter = h[:bands]
        self.speed = 0.6 + 0.8 * h[bands:]

    def bounds(self, res):
        return self.rect.makeOutset(50, 50)

    def draw(self, c, res, t):
        a = self.fade(t)
        if a <= 0:
            return
        r = self.rect
        u = ease_in_out(ramp(t, self.t_change, 2.4))
        band_h = r.height() / self.bands
        for i in range(self.bands):
            k = i / max(1, self.bands - 1)
            c0 = tuple(self.pal0[i][j] + (self.pal1[i][j] - self.pal0[i][j]) * u for j in range(3))
            drift = math.sin(t * self.speed[i] + self.jitter[i] * 6.0) * band_h * 0.12
            rr = skia.Rect.MakeXYWH(r.left(), r.top() + i * band_h + drift, r.width(), band_h * 1.35)
            c.drawRect(rr, paint(c0, 0.92 * a))
        g = skia.GradientShader.MakeRadial(skia.Point(r.centerX(), r.bottom() - r.height() * 0.18), r.height() * 0.85,
                                           [skia.Color(255, 232, 178, int(150 * a)), skia.Color(255, 150, 70, int(60 * a)),
                                            skia.Color(255, 90, 40, 0)], [0.0, 0.35, 1.0])
        p = skia.Paint(); p.setShader(g); p.setBlendMode(skia.BlendMode.kScreen)
        c.drawRect(r, p)


class PrintDim(engine.Print):
    """Print, but `dimv` darkens it the way the room does: multiply, so the paper goes to shadow
    instead of grey. The stock `dim` paints black over the print, which flattens colour to chalk."""
    def __init__(self, *a, dimv=None, **kw):
        super().__init__(*a, **kw)
        self._dimv = dimv

    def draw(self, c, res, t):
        super().draw(c, res, t)
        if self._dimv is None:
            return
        d = clamp(self._dimv(t))
        if d <= 0:
            return
        w, h = self.size(res)
        b = 0 if self.paper else self.border * min(w, h)
        c.save()
        c.translate(self.x, self.y); c.rotate(self.rot)
        p = skia.Paint(); p.setColor(skia.Color(22, 16, 12, int(255 * d)))
        p.setBlendMode(skia.BlendMode.kMultiply); p.setAntiAlias(True)
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h / 2, w, h), p)
        c.restore()


# ------------------------------------------------------------------ finish
def _post(self, img, n):
    """Glow, S-curve, 3x3 grade (so a warm print can go cold at the end), vignette, fine grain."""
    L = self.film.look
    if not hasattr(self, "_grain2"):
        rng = np.random.default_rng(4242)
        # full-resolution grain, 12 plates: reads as film at 1080 wide, and still compresses
        self._grain2 = [np.clip(rng.standard_normal((self.H, self.W)) * 40, -110, 110).astype(np.float32)
                        for _ in range(12)]
    u8 = img if img.dtype == np.uint8 else img.astype(np.uint8)
    f = u8.astype(np.float32) * (1 / 255.0)
    if L["glow"] > 0:
        small = Image.fromarray(u8).reduce(4)
        hi = np.asarray(small, np.float32) * (1.55 / 255.0) - 0.66 * 1.55
        np.clip(hi, 0, 1, out=hi)
        hi = Image.fromarray((hi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)).resize((self.W, self.H), Image.BILINEAR)
        f += np.asarray(hi, np.float32) * (L["glow"] / 255.0)
        np.clip(f, 0, 1, out=f)
        del small, hi
    cv = L["curve"]
    f *= (1 - cv) + cv * f * (3 - 2 * f)
    m = L.get("grade3")
    if m:
        m = np.array(m, np.float32)
        f = (f.reshape(-1, 3) @ m.T).reshape(f.shape)     # 3x3, rows sum to ~1 so exposure holds
    f *= self.vignette
    tt = n / self.film.fps
    if self.film.fade_in > 0 and tt < self.film.fade_in:
        f *= ease_in_out(tt / self.film.fade_in)
    fo = self.film.fade_out
    if fo > 0 and tt > self.film.duration - fo:
        f *= 1 - ease_in_out((tt - (self.film.duration - fo)) / fo)
    if L["grain"] > 0:
        g = self._grain2[((n // 2) * 5) % len(self._grain2)]
        f += g[..., None] * (L["grain"] / 40.0 * 0.55)
    np.clip(f, 0, 1, out=f)
    return (f * 255).astype(np.uint8)


def apply_patch():
    if getattr(engine, "_krakatoa_patch", False):
        return
    engine._krakatoa_patch = True
    engine.Renderer.post = _post
    # the stock roles do not list every face these sheets use; make a project font win before the
    # installed-family search, so the project's type is what actually renders
    orig = engine.resolve_typeface

    def resolve(role, fonts_dir=None):
        if fonts_dir:
            for ext in (".ttf", ".otf"):
                p = pathlib.Path(fonts_dir) / f"{role}{ext}"
                if p.exists():
                    tf = skia.Typeface.MakeFromFile(str(p))
                    if tf:
                        return tf, f"{p.name} (project file)"
        return orig(role, fonts_dir)

    engine.resolve_typeface = resolve
    for name, obj in (("Plume", Plume), ("Glow", Glow), ("RingWave", RingWave), ("SkyBand", SkyBand), ("PrintDim", PrintDim)):
        setattr(engine, name, obj)
