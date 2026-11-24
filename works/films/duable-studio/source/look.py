"""
look.py — a gallery-grade variant of the sr71 rasteriser.

engines/sr71-3d/engine.py is a good software renderer but its shader hard-codes a
cool-blue studio environment, so every metal reads navy, and its post pass is
built for a black background (bloom, ACES, heavy vignette). This subclasses Scene
and replaces exactly two methods — the shading environment and the post chain —
so the object can sit on warm paper without looking like a spaceship.

Nothing in engines/ is touched; that folder is read-only by policy.
"""
import numpy as np
import sys

sys.path.insert(0, "/home/user/AgentContext-Storage/engines/sr71-3d")
from engine import Scene, look_at  # noqa: E402


class GalleryScene(Scene):
    """Neutral-warm studio: a soft ceiling, a warm bounce from the paper below,
    one hot key. Metal reads as graphite/brass rather than blue."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.ambient = 0.30
        self.env_key = np.array([0.96, 0.94, 0.90])     # warm paper bounce, below
        self.env_top = np.array([0.72, 0.75, 0.80])     # cool ceiling, above
        self.contact = 0.28                              # soft floor shadow

    def _shade(self, n, view, mat, Ls, depth):
        base = np.array(mat.get("color", (0.3, 0.3, 0.3)), float)
        metal = float(mat.get("metal", 0.0))
        rough = float(mat.get("rough", 0.4))
        emit = np.array(mat.get("emit", (0, 0, 0)), float)
        fres = 0.04 + 0.96 * (1 - np.clip(np.sum(n * view, axis=1), 0, 1)) ** 5

        rvec = 2 * np.sum(n * view, axis=1, keepdims=True) * n - view
        ry = np.clip(rvec[:, 1], -1, 1)
        # a two-tone environment: cool above, warm paper below, a tight horizon
        env = (self.env_top[None, :] * np.clip(ry[:, None], 0, 1) ** 0.7
               + self.env_key[None, :] * np.clip(-ry[:, None], 0, 1) ** 0.8)
        horizon = np.exp(-((ry - 0.06) ** 2) / 0.010)[:, None]
        env = env * (0.55 + 0.45 * (1 - rough)) + horizon * 0.85

        diffuse = np.zeros_like(n)
        spec = np.zeros((len(n), 3))
        shin = 8 + 190 * (1 - rough) ** 2
        for d, c, inten in Ls:
            ndl = np.clip(n @ d, 0, None)
            diffuse += (c * inten)[None, :] * ndl[:, None]
            h = d[None, :] + view
            h = h / (np.linalg.norm(h, axis=1, keepdims=True) + 1e-12)
            ndh = np.clip(np.sum(n * h, axis=1), 0, None)
            spec += (c * inten)[None, :] * (ndh ** shin)[:, None] * ndl[:, None]

        spec_col = base[None, :] * metal + (1 - metal)
        col = (base[None, :] * (1 - metal) * (diffuse * 0.62 + self.ambient)
               + env * metal
               + spec_col * spec * (0.35 + 1.5 * metal) * (0.25 + 0.75 * fres)[:, None])
        col += emit[None, :]
        return np.clip(col, 0, 8)

    def _post(self, img):
        """No bloom, no ACES. A shoulder that only engages above 0.75 keeps the
        paper background exactly where it was authored — the first version's
        global shoulder turned a 237 paper into a 184 grey."""
        img = np.clip(img, 0, None)
        knee = 0.75
        over = np.clip(img - knee, 0, None)
        img = np.where(img > knee, knee + over / (1.0 + over * 1.6), img)
        return np.clip(img, 0, 1)
