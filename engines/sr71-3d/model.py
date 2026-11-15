"""The subject: a schematic SR-71 built from primitives. Not to scale, not a
blueprint — the channel's own videos disclaim the same thing. What it has to do
is read instantly in silhouette and give the camera something to move over."""
import numpy as np
from engine import rot_x, rot_y, rot_z, bevel_box, cylinder, wing_plate


def panel_seam_quads(x0, x1, y, z0, z1, gap=0.02):
    """Expansion joints — the reason the aircraft leaks. Literal seams."""
    V, F = [], []
    n = max(2, int(abs(x1 - x0) / 0.22))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        m = len(V)
        V += [[x, y, z0], [x, y, z1], [x + gap, y, z1], [x + gap, y, z0]]
        F += [[m, m + 3, m + 2], [m, m + 2, m + 1]]
    return np.array(V, float), np.array(F, np.int64)

TITANIUM = dict(color=(0.50, 0.55, 0.63), metal=0.95, rough=0.30)
TITANIUM_DARK = dict(color=(0.30, 0.34, 0.40), metal=0.95, rough=0.38)
BLACK_PAINT = dict(color=(0.13, 0.14, 0.17), metal=0.80, rough=0.42)
SEAM = dict(color=(0.05, 0.06, 0.08), metal=0.3, rough=0.85)
ACCENT = dict(color=(0.10, 0.30, 1.0), metal=0.2, rough=0.6,
              emit=(0.06, 0.16, 0.55))
HOT = dict(color=(1.0, 0.42, 0.10), metal=0.2, rough=0.5,
           emit=(0.55, 0.16, 0.02))


def _xform(V, R, t):
    return (R @ V.T).T + np.asarray(t, float)


def fuselage():
    """Long faceted body: ring-stack, wider at the chine, tapering to the nose."""
    rings = [
        # (z, half_w, half_h, y_offset)
        (3.55, 0.02, 0.02, 0.00),
        (3.10, 0.16, 0.12, 0.00),
        (2.40, 0.36, 0.22, 0.00),
        (1.55, 0.52, 0.30, 0.01),
        (0.60, 0.58, 0.36, 0.02),
        (-0.60, 0.56, 0.38, 0.02),
        (-1.80, 0.48, 0.34, 0.00),
        (-2.80, 0.34, 0.26, -0.01),
        (-3.45, 0.20, 0.17, -0.02),
        (-3.75, 0.10, 0.10, -0.02),
    ]
    V, F = [], []
    prof = 8
    for (z, hw, hh, yo) in rings:
        for k in range(prof):
            a = 2 * np.pi * k / prof + np.pi / prof
            # squarish cross-section reads more like a chine than an ellipse
            cx, cy = np.cos(a), np.sin(a)
            px = np.sign(cx) * (abs(cx) ** 0.62) * hw
            py = np.sign(cy) * (abs(cy) ** 0.72) * hh + yo
            V.append([px, py, z])
    for i in range(len(rings) - 1):
        for k in range(prof):
            a0 = i * prof + k
            b0 = i * prof + (k + 1) % prof
            a1 = (i + 1) * prof + k
            b1 = (i + 1) * prof + (k + 1) % prof
            F += [[a0, a1, b1], [a0, b1, b0]]
    return np.array(V, float), np.array(F, np.int64)


def nacelle(side=1, x=0.60, z=-0.85):
    out = []
    R = rot_z(np.radians(-6 * side))
    # body of the engine nacelle, drifting back past the wing
    V, F = cylinder(r=0.26, h=3.9, seg=20, r_top=0.23)
    V = _xform(V, rot_x(np.radians(90)) @ R, (x * side, -0.02, z))
    out.append((V, F, TITANIUM_DARK))
    # intake spike
    V, F = cylinder(r=0.175, h=0.85, seg=14, r_top=0.015)
    V = _xform(V, rot_x(np.radians(-90)), (x * side, -0.03, z + 2.30))
    out.append((V, F, dict(color=(0.42, 0.45, 0.52), metal=0.9, rough=0.35)))
    # exhaust lip, hot
    V, F = cylinder(r=0.235, h=0.20, seg=20, r_top=0.255)
    V = _xform(V, rot_x(np.radians(90)), (x * side, -0.03, z - 2.00))
    out.append((V, F, dict(color=(0.20, 0.18, 0.16), metal=0.9, rough=0.3,
                                 emit=(0.30, 0.10, 0.02))))
    return out


def tail_fin(side=1):
    """Canted fin: SR-71's tails lean inward."""
    V = np.array([
        [0.0, 0.0, 1.05], [0.0, 0.0, -0.75], [0.0, 0.86, -0.62],
        [0.0, 0.92, 0.26], [0.06, 0.0, 1.05], [0.06, 0.0, -0.75],
        [0.06, 0.86, -0.62], [0.06, 0.92, 0.26],
    ])
    F = np.array([[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
                  [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                  [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7]])
    R = rot_y(np.radians(-19 * side)) @ rot_z(np.radians(13))
    V = _xform(V, R, (0.30 * side, 0.14, -1.35))
    return V, F


def build_sr71(seam_light=False, heat=0.0, seams_open=0.0, detail=True):
    """Returns a list of (V, F, material). heat 0..1 drives a temp colour."""
    parts = []
    body_mat = BLACK_PAINT
    if heat > 0.01:
        # hot skin: shift toward ember
        body_mat = dict(color=(0.13 + 0.10 * heat, 0.13 + 0.04 * heat, 0.15),
                        metal=0.88, rough=0.34,
                        emit=(0.16 * heat, 0.045 * heat, 0.008 * heat))
    V, F = fuselage()
    parts.append((V, F, body_mat))

    # chine: thin knife edge running the length, the shape's signature
    for s in (+1, -1):
        V = np.array([
            [0.44 * s, 0.03, 2.35], [0.56 * s, 0.02, 1.45],
            [0.52 * s, 0.02, 0.0], [0.44 * s, 0.01, -1.30],
            [0.56 * s, 0.0, 2.10], [0.68 * s, 0.0, 1.45],
            [0.64 * s, 0.0, 0.0], [0.56 * s, 0.0, -1.30],
        ])
        F = np.array([[0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
                      [2, 3, 7], [2, 7, 6]])
        parts.append((V, F, dict(color=(0.55, 0.60, 0.68), metal=0.95, rough=0.22)))

    # delta wing
    for s in (+1, -1):
        V, F = wing_plate(span=1.92, chord=1.75, thick=0.045, sweep=1.62,
                          taper=0.22, dihedral=-0.03)
        V[:, 0] *= s
        V = _xform(V, np.eye(3), (0.30 * s, -0.06, 0.55))
        parts.append((V, F, body_mat))

    for s in (+1, -1):
        parts.extend(nacelle(s))
        parts.append((*tail_fin(s), body_mat))

    # canopy / cockpit spine
    V = np.array([
        [0.0, 0.30, 2.05], [0.20, 0.20, 1.55], [0.0, 0.34, 1.20],
        [-0.20, 0.20, 1.55], [0.0, 0.325, 1.62],
    ])
    F = np.array([[0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]])
    parts.append((V, F, dict(color=(0.16, 0.20, 0.26), metal=0.85, rough=0.10)))

    if detail:
        # panel seams across the upper skin — the film's whole argument
        mat = ACCENT if seam_light else SEAM
        for i, z in enumerate(np.arange(-2.6, 2.7, 0.46)):
            gap = 0.02 + seams_open * 0.09
            V, F = panel_seam_quads(-0.50, 0.50, 0.375, z, z + gap)
            parts.append((V, F, mat))
        # wing seams
        for s in (+1, -1):
            for i, x in enumerate(np.arange(0.55, 2.6, 0.42)):
                gap = 0.02 + seams_open * 0.07
                V = np.array([
                    [x * s, -0.035, 0.30 - i * 0.02], [x * s, -0.035, -0.95],
                    [(x + gap) * s, -0.035, -0.95], [(x + gap) * s, -0.035, 0.30 - i * 0.02],
                ])
                F = np.array([[0, 1, 2], [0, 2, 3]])
                parts.append((V, F, ACCENT if seam_light else SEAM))
    return parts


def build_plate(width=2.0, height=1.1, thick=0.10, heat=0.0, gap=0.06):
    """Two titanium panels with a gap between them — the cold, unsealed state."""
    parts = []
    mats = dict(color=(0.50 + 0.2 * heat, 0.55 - 0.1 * heat, 0.63 - 0.2 * heat),
                metal=0.95, rough=0.30,
                emit=(0.5 * heat, 0.14 * heat, 0.02 * heat))
    for s in (-1, 1):
        V, F = bevel_box(width / 2, thick, height / 2, bevel=0.06)
        V = _xform(V, np.eye(3), (s * (width / 4 + gap / 2), 0, 0))
        parts.append((V, F, mats))
        # a machined lip along the facing edge, so the gap has two real walls
        V2, F2 = bevel_box(0.05, thick * 0.86, height / 2 * 0.98, bevel=0.04)
        V2 = _xform(V2, np.eye(3), (s * (gap / 2 + 0.03), 0, 0))
        parts.append((V2, F2, dict(color=(0.62, 0.66, 0.74), metal=0.97, rough=0.18,
                                   emit=(0.10 * heat, 0.03 * heat, 0.0))))
    return parts


def build_fuel_drops(n=26, seed=7, spread=1.5, t=0.0, start=0.30):
    """JP-7 falling from the belly. Positions are deterministic in t."""
    rng = np.random.default_rng(seed)
    xs = rng.uniform(-spread, spread, n)
    zs = rng.uniform(-2.6, 2.2, n)
    ph = rng.uniform(0, 1, n)
    parts = []
    for i in range(n):
        y = start - ((t * 1.9 + ph[i]) % 1.0) * 2.9
        if y < -2.4:
            continue
        r = 0.028 + 0.016 * ph[i]
        V, F = cylinder(r=r * 0.85, h=0.10 + r * 2.2, seg=7, r_top=r * 0.55)
        V = _xform(V, np.eye(3), (xs[i], y, zs[i]))
        parts.append((V, F, dict(color=(0.65, 0.72, 0.85), metal=0.35, rough=0.18,
                                 emit=(0.02, 0.03, 0.05))))
    return parts
