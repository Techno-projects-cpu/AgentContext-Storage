"""Auto-framing: fit the *projected* subject to the frame, not its bounding sphere.
A long thin aircraft in a portrait frame wastes most of a sphere fit."""
import numpy as np
from engine import look_at
from PIL import Image  # noqa


def bbox(parts):
    allv = np.vstack([p[0] for p in parts])
    return allv.min(axis=0), allv.max(axis=0)


def orbit_cam(parts, az=38.0, el=16.0, fill=0.80, fov=32.0, W=1080, H=1920,
              centre=None, roll=0.0):
    allv = np.vstack([p[0] for p in parts])
    lo, hi = bbox(parts)
    c = np.asarray(centre if centre is not None else (lo + hi) / 2, float)
    a, e = np.radians(az), np.radians(el)
    d = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    fpx = 1.0 / np.tan(np.radians(fov) / 2) * (H / 2)
    dist = float(np.max(np.linalg.norm(allv - c, axis=1))) * 2.2
    for _ in range(24):
        eye = c + dist * d
        R, _e = look_at(eye, c)
        Vc = (R @ (allv - eye).T).T
        z = -Vc[:, 2]
        z = np.maximum(z, 1e-3)
        x = Vc[:, 0] * fpx / z
        y = -Vc[:, 1] * fpx / z
        rx = np.max(np.abs(x)) / (W / 2)
        ry = np.max(np.abs(y)) / (H / 2)
        r = max(rx, ry)
        dist *= r / fill
        if abs(r / fill - 1) < 0.002:
            break
    eye = c + dist * d
    return eye, c
