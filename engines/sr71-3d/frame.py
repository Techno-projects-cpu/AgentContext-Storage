"""Auto-framing: fit the *projected* subject to the frame, not its bounding sphere.
A long thin aircraft in a portrait frame wastes most of a sphere fit."""
import numpy as np
from engine import look_at
from PIL import Image  # noqa


def bbox(parts):
    allv = np.vstack([p[0] for p in parts if not _is_aux(p)])
    return allv.min(axis=0), allv.max(axis=0)


def _is_aux(part):
    """Particles (fuel drips) move through the frame; framing must ignore them
    or the aircraft shrinks every time a drop falls out of bounds."""
    return len(part) > 2 and isinstance(part[2], dict) and part[2].get("aux")


def orbit_cam(parts, az=38.0, el=16.0, fill=0.80, fov=32.0, W=1080, H=1920,
              centre=None, roll=0.0, yshift=0.0):
    """
    Frame the subject by its PROJECTED width, not its bounding sphere.

    `fill` is the fraction of frame WIDTH the subject should span: 1.0 touches
    both edges, >1 deliberately bleeds off them — which is how a machine reads
    as big on a 9:16 frame. `yshift` is where the subject's vertical centre
    should sit, in frame heights (negative = above centre), because the type
    owns the bottom third.

    Distance is solved by bisection (the projected width is monotone in
    distance), then the look-at point is walked up/down until the subject sits
    where asked. No gradient steps, so it cannot diverge.
    """
    allv = np.vstack([p[0] for p in parts if not _is_aux(p)])
    lo, hi = bbox(parts)
    c = np.asarray(centre if centre is not None else (lo + hi) / 2, float)
    a, e = np.radians(az), np.radians(el)
    d = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    fpx = 1.0 / np.tan(np.radians(fov) / 2) * (H / 2)
    radius = max(0.25, float(np.max(np.linalg.norm(allv - c, axis=1))))
    ctr = c.copy()

    def span(ctr, dist):
        eye = ctr + d * dist
        R, _ = look_at(eye, ctr)
        Vc = (R @ (allv - eye).T).T
        z = np.maximum(-Vc[:, 2], 1e-3)
        x = Vc[:, 0] * fpx / z
        y = -Vc[:, 1] * fpx / z
        return (x.max() - x.min()) / W, (y.max() + y.min()) / 2 / H, R

    dlo, dhi = 0.35 * radius, 22.0 * radius
    for _ in range(5):
        for _ in range(46):
            dm = 0.5 * (dlo + dhi)
            rx, _, _ = span(ctr, dm)
            if rx > fill:
                dlo = dm
            else:
                dhi = dm
        dist = 0.5 * (dlo + dhi)
        _, ymid, R = span(ctr, dist)
        err = yshift - ymid
        if abs(err) < 0.004:
            break
        # slide the look-at point along the camera's up axis by that fraction of
        # the visible height at the subject's depth
        vis_h = 2.0 * dist * np.tan(np.radians(fov) / 2)
        ctr = ctr + R[1] * (err * vis_h)
        dlo, dhi = 0.35 * radius, 22.0 * radius
    return ctr + d * dist, ctr
