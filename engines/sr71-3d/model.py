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


def hoop_seams(expand=0.0, gap=0.02, prof=30, spacing=0.30, lift=1.006):
    """
    The panel joints, wrapped around the actual skin. Each hoop sits on the
    interpolated hull surface and stands slightly proud of it, so as the skin
    expands the seams ride out with it and the gap between the bands widens.
    """
    z0, z1 = -3.55, 3.25
    zs = np.arange(z0, z1, spacing)
    V, F = [], []
    for z in zs:
        hw, hh, yo = _station(z, expand)
        hw2, hh2, _ = _station(z + gap, expand)
        base = len(V)
        for sub in (0.0, 1.0):
            if sub == 0.0:
                a_w, a_h, s = hw, hh, z
            else:
                a_w, a_h, s = hw2, hh2, z + gap
            for k in range(prof):
                a = 2 * np.pi * k / prof
                cx, cy = np.cos(a), np.sin(a)
                px = np.sign(cx) * (abs(cx) ** 0.86) * a_w * lift
                py = np.sign(cy) * (abs(cy) ** 0.90) * a_h * lift + yo
                V.append([px, py, s])
        for k in range(prof):
            k2 = (k + 1) % prof
            a, b = base + k, base + k2
            c, d = base + prof + k2, base + prof + k
            F += [[a, c, d], [a, d, b]]
    return np.array(V, float), np.array(F, np.int64)


def spine_seams(expand=0.0, gap=0.02, prof=30, lift=1.007):
    """Longitudinal joint lines: four runs along the upper and lower skin."""
    V, F = [], []
    hw, hh, yo = _station(0.0, expand)
    for ang_deg in (52, 128, 232, 308):
        a = np.radians(ang_deg)
        zs = np.arange(-3.45, 3.15, 0.5)
        for i in range(len(zs) - 1):
            base = len(V)
            for z in (zs[i], zs[i + 1]):
                w, h, yoff = _station(z, expand)
                for da in (0.0, np.radians(1.6)):
                    cx, cy = np.cos(a + da), np.sin(a + da)
                    px = np.sign(cx) * (abs(cx) ** 0.86) * w * lift
                    py = np.sign(cy) * (abs(cy) ** 0.90) * h * lift + yoff
                    V.append([px, py, z])
            # 0/1 = this z either side of the line, 2/3 = the next z
            F += [[base, base + 2, base + 3], [base, base + 3, base + 1]]
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


SECTIONS = [
    # (z, half_w, half_h, y_offset) — the aircraft's stations, nose to tail
    (3.62, 0.010, 0.010, 0.000),
    (3.30, 0.090, 0.070, 0.000),
    (2.85, 0.215, 0.150, 0.000),
    (2.35, 0.365, 0.225, 0.005),
    (1.75, 0.485, 0.285, 0.010),
    (1.15, 0.555, 0.330, 0.015),
    (0.55, 0.580, 0.360, 0.020),
    (-0.05, 0.575, 0.375, 0.020),
    (-0.65, 0.560, 0.380, 0.020),
    (-1.30, 0.520, 0.360, 0.012),
    (-1.95, 0.465, 0.330, 0.000),
    (-2.55, 0.390, 0.285, -0.010),
    (-3.10, 0.290, 0.225, -0.018),
    (-3.55, 0.175, 0.145, -0.022),
    (-3.80, 0.085, 0.080, -0.024),
]


def _resample(sections, step=0.16):
    """Cubic-ish resampling of the stations, so the hull has no visible facets
    along its length. Catmull-Rom on each of hw/hh/y."""
    z = np.array([s[0] for s in sections])
    cols = [np.array([s[i] for s in sections]) for i in (1, 2, 3)]
    out = []
    for i in range(len(sections) - 1):
        n = max(2, int(abs(z[i] - z[i + 1]) / step))
        for k in range(n):
            u = k / n
            vals = []
            for c in cols:
                p0 = c[max(i - 1, 0)]
                p1, p2 = c[i], c[i + 1]
                p3 = c[min(i + 2, len(c) - 1)]
                # Catmull-Rom
                vals.append(0.5 * ((2 * p1) + (-p0 + p2) * u
                                   + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2
                                   + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
            out.append((z[i] + (z[i + 1] - z[i]) * u, *vals))
    out.append(sections[-1])
    return out


def skin(expand=0.0, prof=30, step=0.16, ecc=(0.86, 0.90)):
    """
    The fuselage shell. Rounded superellipse section, resampled stations, and a
    thermal-expansion term that lifts the skin off the frame along its own
    normal — that lift is the mechanism the film is about.
    """
    rings = _resample(SECTIONS, step)
    V = []
    for (z, hw, hh, yo) in rings:
        hw_e = hw * (1.0 + expand * 0.020)
        hh_e = hh * (1.0 + expand * 0.030)
        for k in range(prof):
            a = 2 * np.pi * k / prof
            cx, cy = np.cos(a), np.sin(a)
            px = np.sign(cx) * (abs(cx) ** ecc[0]) * hw_e
            py = np.sign(cy) * (abs(cy) ** ecc[1]) * hh_e + yo
            V.append([px, py, z])
    V = np.array(V, float)
    F = []
    n = len(rings)
    for i in range(n - 1):
        for k in range(prof):
            a0 = i * prof + k
            b0 = i * prof + (k + 1) % prof
            a1 = (i + 1) * prof + k
            b1 = (i + 1) * prof + (k + 1) % prof
            F += [[a0, a1, b1], [a0, b1, b0]]
    return V, np.array(F, np.int64)


def fuselage(expand=0.0):
    return skin(expand=expand)


def _station(z, expand=0.0):
    """Interpolate the section at any z — how a seam knows where the skin is."""
    rings = _resample(SECTIONS, 0.10)
    zs = np.array([r[0] for r in rings])
    hw = np.interp(z, zs, [r[1] for r in rings])
    hh = np.interp(z, zs, [r[2] for r in rings])
    yo = np.interp(z, zs, [r[3] for r in rings])
    return hw * (1 + expand * 0.020), hh * (1 + expand * 0.030), yo


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


def build_sr71(seam_light=False, heat=0.0, seams_open=0.0, detail=True,
               expand=0.0):
    """Returns a list of (V, F, material). heat 0..1 drives a temp colour."""
    parts = []
    body_mat = BLACK_PAINT
    if heat > 0.01:
        # hot skin: shift toward ember
        # Hot skin stays BLACK. Tinting the whole hull orange turns it into clay;
        # what actually reads is a dark airframe whose edges are going ember.
        body_mat = dict(color=(0.118, 0.114, 0.118),
                        metal=0.50, rough=0.62,
                        emit=(0.075 * heat, 0.020 * heat, 0.004 * heat),
                        rim=(0.95 * heat, 0.30 * heat, 0.055 * heat))
    V, F = fuselage(expand=expand)
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

    # canopy: a low spine that HUGS the hull. The old version was three points on
    # a flat triangle, which poked through the smoothed skin as a white needle.
    cV, cF = [], []
    for (cz, cw, cy) in [(2.42, 0.055, 0.215), (2.15, 0.135, 0.255),
                         (1.85, 0.150, 0.295), (1.60, 0.105, 0.315)]:
        cV += [[-cw, cy, cz], [cw, cy, cz], [0.0, cy + 0.055, cz]]
    for i in range(3):
        a = i * 3
        b = (i + 1) * 3
        cF += [[a, b, b + 2], [a, b + 2, a + 2],      # left slope
               [a + 2, b + 2, b + 1], [a + 2, b + 1, a + 1],  # right slope
               [a, b, b + 1], [a, b + 1, a + 1]]      # hull-facing underside
    parts.append((np.array(cV, float), np.array(cF, np.int64),
                  dict(color=(0.18, 0.22, 0.29), metal=0.88, rough=0.12,
                       emit=(0.02, 0.03, 0.05))))

    if detail:
        # the film's whole argument, as geometry: joints wrapped round a skin
        # that moves. mach 3 closes them; on the ground they are open.
        if heat > 0.01:
            mat = dict(color=(1.0, 0.42, 0.12), metal=0.25, rough=0.55,
                       emit=(0.85 * heat, 0.24 * heat, 0.03 * heat))
        else:
            mat = ACCENT if seam_light else SEAM
        gap = 0.013 + seams_open * 0.062
        V, F = hoop_seams(expand=expand, gap=gap, spacing=0.285)
        parts.append((V, F, mat))
        V, F = spine_seams(expand=expand, gap=gap)
        parts.append((V, F, mat))
    return parts


def build_plate(width=1.05, height=0.86, thick=0.055, heat=0.0, gap=0.06):
    """Two titanium panels with a gap between them — the cold, unsealed state."""
    parts = []
    base = np.array((0.50, 0.55, 0.63)) * (1.0 - 0.62 * heat)
    mats = dict(color=tuple(float(c) for c in base), metal=0.95, rough=0.30,
                emit=(0.10 * heat, 0.026 * heat, 0.004 * heat))
    # the wall behind: no rubber bladder on this aircraft, so what the joint
    # opens onto is the inside of the tank
    Vb, Fb = bevel_box(width + gap + 0.14, 0.03, height + 0.10, bevel=0.04)
    Vb = _xform(Vb, np.eye(3), (0, -thick * 1.35, 0))
    parts.append((Vb, Fb, dict(color=(0.045, 0.042, 0.040), metal=0.30, rough=0.85,
                               emit=(0.045 * heat, 0.012 * heat, 0.002 * heat))))
    for s in (-1, 1):
        V, F = bevel_box(width / 2, thick, height / 2, bevel=0.06)
        V = _xform(V, np.eye(3), (s * (width / 4 + gap / 2), 0, 0))
        parts.append((V, F, mats))
        # a machined lip along the facing edge, so the gap has two real walls
        V2, F2 = bevel_box(0.028, thick * 0.86, height / 2 * 0.98, bevel=0.04)
        V2 = _xform(V2, np.eye(3), (s * (gap / 2 + 0.017), 0, 0))
        parts.append((V2, F2, dict(color=(0.62, 0.66, 0.74), metal=0.97, rough=0.18,
                                   emit=(0.42 * heat, 0.12 * heat, 0.01 * heat))))
        # two rows of rivets at panel scale: the macro beat needs something in
        # its own size class, or it reads as a bare rectangle
        rivet = dict(color=(0.40, 0.43, 0.50), metal=0.95, rough=0.30,
                     emit=(0.05 * heat, 0.015 * heat, 0.0))
        for row_x in (width / 2 - 0.055, width / 2 - 0.135):
            for k in range(9):
                pz = -height / 2 + 0.055 + k * (height - 0.11) / 8
                Vr, Fr = bevel_box(0.016, thick * 1.06, 0.016, bevel=0.10)
                Vr = _xform(Vr, np.eye(3),
                            (s * (row_x + gap / 2 * 0), 0, pz))
                parts.append((Vr, Fr, rivet))
    # the hot core: a thin glowing strip that only shows while the joint is open,
    # and gets swallowed by the panels as they close on it
    if heat > 0.01:
        V3, F3 = bevel_box(0.010, thick * 0.5, height / 2 * 0.92, bevel=0.03)
        parts.append((V3, F3, dict(color=(1.0, 0.55, 0.25), metal=0.1, rough=0.6,
                                   emit=(2.4 * heat, 0.8 * heat, 0.18 * heat), aux=1)))
    return parts


def build_flame(t=0.0, seed=11, length=1.30):
    """TEB ignition: two short green plumes off the exhausts, flickering as a
    fixed function of t. Emissive only — no light transport, no faked volumetrics."""
    rng = np.random.default_rng(seed)
    parts = []
    for s in (+1, -1):
        ph = rng.uniform(0, 6.28, 3)
        L = length * (0.82 + 0.18 * np.sin(t * 21.0 + ph[0]))
        R = rot_x(np.radians(90))
        V, F = cylinder(r=0.21, h=L, seg=16, r_top=0.055, cap=True)
        V = _xform(V, R, (0.60 * s, -0.03, -2.92 - L / 2))
        r = 0.30 + 0.06 * np.sin(t * 17.0 + ph[1])
        parts.append((V, F, dict(color=(0.35, 1.0, 0.55), metal=0.0, rough=0.6,
                                 emit=(0.75 * r, 2.3 * r, 1.15 * r), aux=1)))
        V, F = cylinder(r=0.10, h=L * 0.7, seg=12, r_top=0.02, cap=True)
        V = _xform(V, R, (0.60 * s, -0.03, -2.96 - L * 0.35))
        parts.append((V, F, dict(color=(0.7, 1.0, 0.8), metal=0.0, rough=0.5,
                                 emit=(1.6, 3.4, 1.9), aux=1)))
    return parts


def build_fuel_drops(n=46, seed=7, spread=1.55, t=0.0, start=0.26, belt=1.0):
    """JP-7 falling from the belly. Deterministic in t.

    `belt=0` returns only the drops currently inside the belly width and with the
    whole path ahead of them — that is "the aircraft with nothing falling yet",
    which is what the camera should be framed on.
    """
    rng = np.random.default_rng(seed)
    xs = rng.uniform(-spread, spread, n)
    zs = rng.uniform(-2.6, 2.2, n)
    ph = rng.uniform(0, 1, n)
    parts = []
    for i in range(n):
        cyc = (t * 1.9 + ph[i]) % 1.0
        y = start - cyc * 2.9
        if y < -2.4:
            continue
        if belt == 0.0 and not (abs(xs[i]) <= spread * 0.22 and cyc < 0.06):
            continue
        r = 0.013 + 0.010 * ph[i]
        V, F = cylinder(r=r * 0.9, h=0.055 + r * 3.4, seg=6, r_top=r * 0.45)
        V = _xform(V, np.eye(3), (xs[i], y, zs[i]))
        parts.append((V, F, dict(color=(0.72, 0.80, 0.95), metal=0.45, rough=0.10,
                                 emit=(0.03, 0.045, 0.075), aux=1)))
    return parts
