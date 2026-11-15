"""
Software 3D renderer, version 2 — NumPy rasteriser with a real light rig.

No WebGL in this container, so this draws triangles itself: perspective
projection, z-buffer, per-face Blinn-Phong with three lights (warm key, cool
rim, ember fill), fresnel edge light, then bloom, ACES-ish tone map, vignette
and grain. Deterministic: no clock, no unseeded RNG.
"""
import numpy as np
from PIL import Image, ImageFilter

# ---------------------------------------------------------------- geometry ---


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def look_at(eye, target, up=(0, 1, 0)):
    eye = np.asarray(eye, float)
    tgt = np.asarray(target, float)
    up = np.asarray(up, float)
    f = tgt - eye
    f = f / (np.linalg.norm(f) + 1e-12)
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-8:
        r = np.cross(f, (0, 0, 1))
    r = r / (np.linalg.norm(r) + 1e-12)
    u = np.cross(r, f)
    return np.stack([r, u, -f]), eye


def cylinder(r=1.0, h=1.0, seg=24, r_top=None, cap=True):
    r_top = r if r_top is None else r_top
    ang = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    V = []
    for a in ang:
        V.append([r * np.cos(a), -h / 2, r * np.sin(a)])
        V.append([r_top * np.cos(a), h / 2, r_top * np.sin(a)])
    V = np.array(V, float)
    F = []
    n = len(ang)
    for i in range(n):
        a, b = 2 * i, 2 * ((i + 1) % n)
        F += [[a, a + 1, b + 1], [a, b + 1, b]]
    if cap:
        cb = len(V)
        V = np.vstack([V, [[0, -h / 2, 0], [0, h / 2, 0]]])
        for i in range(n):
            a, b = 2 * i, 2 * ((i + 1) % n)
            F += [[cb, b, a], [cb + 1, a + 1, b + 1]]
    return V, np.array(F, np.int64)


def bevel_box(sx=1.0, sy=1.0, sz=1.0, bevel=0.10):
    v = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    v *= np.array([sx, sy, sz]) / 2 * (1 - bevel)
    out = v + v * (bevel * 2.4)
    V = np.vstack([v, out])
    F = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
         [8, 10, 9], [8, 11, 10], [12, 13, 14], [12, 14, 15]]
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        F += [[a, b, 4 + b], [a, 4 + b, 4 + a]]
    return V, np.array(F, np.int64)


def wing_plate(span=3.0, chord=1.4, thick=0.06, sweep=0.9, taper=0.34,
               dihedral=0.0):
    V, F = [], []
    for s in (+1, -1):
        lead = np.array([0.0, 0.0, 0.0])
        root_f = np.array([0.0, 0.0, -chord])
        tip_l = np.array([s * span, dihedral * span, -sweep])
        tip_f = np.array([s * span, dihedral * span, -sweep - chord * taper])
        tip_r = np.array([s * span, dihedral * span, -sweep + chord * 0.16])
        m = len(V)
        for p in (lead, root_f, tip_l, tip_f, tip_r):
            V.append(p + np.array([0, thick / 2, 0]))
        for p in (lead, root_f, tip_l, tip_f, tip_r):
            V.append(p - np.array([0, thick / 2, 0]))
        F += [[m + 0, m + 2, m + 4], [m + 0, m + 4, m + 1]]
        F += [[m + 5, m + 9, m + 7], [m + 5, m + 6, m + 9]]
        F += [[m + 0, m + 5, m + 7], [m + 0, m + 7, m + 2]]
        F += [[m + 1, m + 4, m + 9], [m + 1, m + 9, m + 6]]
        F += [[m + 2, m + 7, m + 9], [m + 2, m + 9, m + 4]]
    return np.array(V, float), np.array(F, np.int64)


# ---------------------------------------------------------------- renderer ---

DEFAULT_LIGHTS = [
    # dir (world, pointing FROM surface TO light), colour, intensity
    (np.array([0.42, 0.80, 0.43]), np.array([1.00, 0.94, 0.86]), 1.55),   # warm key
    (np.array([-0.70, 0.35, -0.62]), np.array([0.42, 0.62, 1.00]), 1.35),  # cool rim
    (np.array([0.10, -0.85, 0.50]), np.array([1.00, 0.45, 0.18]), 0.30),   # ember fill
]


class Scene:
    def __init__(self, w=1080, h=1920, ss=2, bg=(0.012, 0.014, 0.022),
                 bg_top=None, fog=(0.0, 0.0, 0.0), fog_k=0.0):
        self.w, self.h, self.ss = w, h, ss
        self.W, self.H = w * ss, h * ss
        self.objs = []
        self.cam = None
        self.lights = list(DEFAULT_LIGHTS)
        self.bg = np.array(bg, float)
        self.bg_top = np.array(bg_top if bg_top is not None else bg, float)
        self.fog = np.array(fog, float)
        self.fog_k = fog_k
        self.ambient = 0.045
        self.exposure = 1.0
        self.bloom_amt = 0.55
        self.glow = None

    def add(self, mesh, mat):
        V, F = mesh
        self.objs.append((V, F, mat))
        return self

    def set_camera(self, eye, target, fov=42.0, up=(0, 1, 0)):
        self.cam = dict(eye=np.asarray(eye, float), target=np.asarray(target, float),
                        fov=fov, up=np.asarray(up, float))

    def background(self):
        H, W = self.H, self.W
        g = np.linspace(0, 1, H)[:, None]
        img = (self.bg[None, None, :] * (1 - g[..., None]) +
               self.bg_top[None, None, :] * g[..., None])
        img = np.repeat(img, W, axis=1).copy()
        # soft practical behind the subject: gives the frame a light source and
        # separates metal from background without a visible shape
        if self.glow is not None:
            col, cy, rad, inten = self.glow
            yy, xx = np.mgrid[0:H, 0:W]
            d2 = (((xx - W * 0.5) / (W * 0.62)) ** 2 + ((yy - H * cy) / (H * rad)) ** 2)
            m = np.exp(-d2 * 2.2)[..., None] * inten
            img = img + np.array(col, float)[None, None, :] * m
        return img

    def render(self, t=0.0):
        W, H, ss = self.W, self.H, self.ss
        eye, tgt = self.cam["eye"], self.cam["target"]
        R, e = look_at(eye, tgt, self.cam["up"])
        f = 1.0 / np.tan(np.radians(self.cam["fov"]) / 2)
        zbuf = np.full((H, W), np.inf, np.float32)
        img = self.background()
        Ls = [(d / np.linalg.norm(d), np.asarray(c, float), float(i))
              for d, c, i in self.lights]

        for V0, F, mat in self.objs:
            if V0 is None or len(F) == 0:
                continue
            Vc = (R @ (V0 - e).T).T
            z = -Vc[:, 2]
            x = (Vc[:, 0] * f) / np.maximum(z, 1e-6) * (H / 2) + W / 2
            y = (-Vc[:, 1] * f) / np.maximum(z, 1e-6) * (H / 2) + H / 2
            n = np.cross(V0[F[:, 1]] - V0[F[:, 0]], V0[F[:, 2]] - V0[F[:, 0]])
            n = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
            cen = V0[F].mean(axis=1)
            view = eye[None, :] - cen
            view = view / (np.linalg.norm(view, axis=1, keepdims=True) + 1e-12)
            # faces whose normal points away from the camera still rasterise for
            # closed shells, but they get no key light — correct and cheap
            col = self._shade(n, view, mat, Ls, z[F].mean(axis=1))
            for i in range(len(F)):
                a, b, c = F[i]
                za, zb_, zc = z[a], z[b], z[c]
                if za <= 0.06 or zb_ <= 0.06 or zc <= 0.06:
                    continue
                self._tri(img, zbuf, x[a], y[a], za, x[b], y[b], zb_, x[c], y[c], zc,
                          col[i])

        img = self._post(img)
        out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        return out.resize((self.w, self.h), Image.LANCZOS)

    def _shade(self, n, view, mat, Ls, depth):
        """
        Energy-ish PBR without a BRDF table:
          diffuse = base*(1-metal) * sum(NdL * light_colour)
          spec    = mix(base, white, metal) * GGX-ish lobe
          env     = fake studio: sky/ground gradient sampled by the reflection
                    vector, weighted by metal. Without this, metal renders black
                    because there is nothing to reflect.
        """
        base = np.array(mat.get("color", (0.35, 0.37, 0.42)), float)
        metal = float(mat.get("metal", 0.0))
        rough = float(mat.get("rough", 0.35))
        emit = np.array(mat.get("emit", (0, 0, 0)), float)
        fres = 0.04 + 0.96 * (1 - np.clip(np.sum(n * view, axis=1), 0, 1)) ** 5
        # reflect the view about the normal: what a mirror at this pixel sees
        rvec = 2 * np.sum(n * view, axis=1, keepdims=True) * n - view
        ry = np.clip(rvec[:, 1], -1, 1)
        # studio environment: cool ceiling, hot horizon band, dark floor
        env = (np.array([0.16, 0.22, 0.38])[None, :] * np.clip(ry[:, None], 0, 1)
               + np.array([0.05, 0.06, 0.09])[None, :] * np.clip(-ry[:, None], 0, 1))
        horizon = np.exp(-((ry - 0.18) ** 2) / 0.02)[:, None]
        env = env + horizon * np.array([0.55, 0.62, 0.80])[None, :]
        env = env * (0.35 + 0.65 * (1 - rough))
        diffuse = np.zeros_like(n)
        spec = np.zeros((len(n), 3))
        shin = 6 + 140 * (1 - rough) ** 2
        for d, c, inten in Ls:
            ndl = np.clip(n @ d, 0, None)
            diffuse += (c * inten)[None, :] * ndl[:, None]
            h = d[None, :] + view
            h = h / (np.linalg.norm(h, axis=1, keepdims=True) + 1e-12)
            ndh = np.clip(np.sum(n * h, axis=1), 0, None)
            spec += (c * inten)[None, :] * (ndh ** shin)[:, None] * ndl[:, None]
        spec_col = base[None, :] * metal + np.array([1.0, 1.0, 1.0])[None, :] * (1 - metal)
        col = (base[None, :] * (1 - metal) * (diffuse * 0.55 + self.ambient)
               + env * metal
               + spec_col * spec * (0.9 + 2.2 * metal) * (0.15 + 0.85 * fres)[:, None]
               + base[None, :] * 0.05)
        col += emit[None, :]
        if self.fog_k > 0:
            k = np.clip((depth - 6.0) * self.fog_k, 0, 0.85)[:, None]
            col = col * (1 - k) + self.fog[None, :] * k
        return np.clip(col, 0, 40)

    @staticmethod
    def _tri(img, zbuf, x0, y0, z0, x1, y1, z1, x2, y2, z2, col):
        H, W = zbuf.shape
        minx = max(int(np.floor(min(x0, x1, x2))), 0)
        maxx = min(int(np.ceil(max(x0, x1, x2))), W - 1)
        miny = max(int(np.floor(min(y0, y1, y2))), 0)
        maxy = min(int(np.ceil(max(y0, y1, y2))), H - 1)
        if minx > maxx or miny > maxy:
            return
        xs = np.arange(minx, maxx + 1) + 0.5
        ys = np.arange(miny, maxy + 1) + 0.5
        px, py = np.meshgrid(xs, ys)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(d) < 1e-9:
            return
        w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / d
        w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        if not inside.any():
            return
        zz = w0 * z0 + w1 * z1 + w2 * z2
        sub = zbuf[miny:maxy + 1, minx:maxx + 1]
        m = inside & (zz < sub)
        if not m.any():
            return
        sub[m] = zz[m]
        img[miny:maxy + 1, minx:maxx + 1][m] = col[None, :]

    def _post(self, img):
        img = img * self.exposure
        # bloom
        b = np.clip(img - 0.75, 0, None)
        bi = Image.fromarray(np.clip(b * 255 * 2.0, 0, 255).astype(np.uint8))
        bi = bi.resize((bi.width // 4, bi.height // 4), Image.BILINEAR)
        bi = bi.filter(ImageFilter.GaussianBlur(7))
        bi = bi.filter(ImageFilter.GaussianBlur(7))
        glow = np.asarray(bi.resize((img.shape[1], img.shape[0]), Image.BILINEAR),
                          np.float32) / 255
        img = img + glow * self.bloom_amt
        # ACES-ish filmic curve
        a, bb, c, d, e_ = 2.51, 0.03, 2.43, 0.59, 0.14
        img = np.clip((img * (a * img + bb)) / (img * (c * img + d) + e_), 0, 1)
        # vignette
        H, W = img.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        cx, cy = W / 2, H / 2
        r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2) / 1.414
        vig = np.clip(1 - (r ** 2.2) * 0.85, 0, 1)[..., None]
        img = img * vig
        # fine grain: fixed seed, so the render reproduces exactly
        rng = np.random.default_rng(1234)
        img = img + (rng.standard_normal((H, W, 1)) * 0.006)
        return np.clip(img, 0, 1)
