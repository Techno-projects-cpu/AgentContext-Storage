"""
stage.py — the 3D half of the film: geometry, camera, and the shadow pass.

The hero object is the catalogue made physical: four vertical stacks of thin
plates, 8 / 4 / 5 / 7, because those are the site's own category counts. The
stacks re-flow into one 6×4 grid at the end — "a studio with a service for that".

Everything is a pure function of time. `--still t` renders exactly that frame,
which is how the camera was tuned without re-rendering the film.
"""
import math
import sys

import numpy as np

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, "/home/user/AgentContext-Storage/engines/sr71-3d")

from engine import look_at                    # noqa: E402
from look import GalleryScene                 # noqa: E402

# matches the porcelain gradient the skia page uses, so the 3D plate can BE the
# background of its shot instead of a pasted rectangle with a visible seam
PAPER = (0.949, 0.941, 0.910)          # 242,240,232
PAPER_B = (0.910, 0.898, 0.859)        # 232,229,219


# ------------------------------------------------------------------ geometry
def box(sx, sy, sz, bevel=0.10):
    """A beveled slab. 8 corners pulled in, 24 faces out — cheap and it catches
    light on the chamfer, which is what stops it reading as a cube of clay."""
    unit = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                     [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    half = np.array([sx, sy, sz]) / 2
    # The two shells must share the SAME sign per axis, only differ in size:
    # the outer box is the true size, the inner one is pulled in by the bevel.
    # (Scaling the inner one outward — core + core*2*bevel — scaled from the
    #  origin instead, so on a thin slab it spawned a second floating plate and
    #  the hero plate read as a green card with a flap.)
    core = unit * half * (1 - bevel)
    shell = unit * half
    V = np.vstack([core, shell])
    F = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
         [8, 10, 9], [8, 11, 10], [12, 13, 14], [12, 14, 15]]
    # The bridge from the inner shell to the outer one. Its partner vertex is
    # `+8`, NOT `+4`: +4 is the inner box's opposite face, so bridging to it drew
    # a thin flap floating clear of every plate.
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        F += [[a, b, b + 8], [a, b + 8, a + 8]]
    return V, np.array(F, np.int64)


def torus(R=1.0, r=0.26, seg=96, ring=22):
    u = np.linspace(0, 2 * np.pi, seg, endpoint=False)
    v = np.linspace(0, 2 * np.pi, ring, endpoint=False)
    V = np.array([[(R + r * np.cos(b)) * np.cos(a), r * np.sin(b),
                   (R + r * np.cos(b)) * np.sin(a)] for a in u for b in v])
    F = []
    for i in range(seg):
        for j in range(ring):
            a = i * ring + j
            b = i * ring + (j + 1) % ring
            c = ((i + 1) % seg) * ring + (j + 1) % ring
            d = ((i + 1) % seg) * ring + j
            F += [[a, b, c], [a, c, d]]
    return V, np.array(F, np.int64)


def xf(V, rot=None, t=(0, 0, 0)):
    V = np.asarray(V, float)
    if rot is not None:
        V = V @ np.asarray(rot, float).T
    return V + np.asarray(t, float)


def rot_xyz(ax=0.0, ay=0.0, az=0.0):
    cx, sx = np.cos(ax), np.sin(ax)
    cy, sy = np.cos(ay), np.sin(ay)
    cz, sz = np.cos(az), np.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


# ------------------------------------------------------------------- palette
INK = dict(color=(0.075, 0.078, 0.084), metal=0.72, rough=0.22)
INK_SOFT = dict(color=(0.11, 0.115, 0.13), metal=0.35, rough=0.42)
BONE = dict(color=(0.72, 0.70, 0.66), metal=0.05, rough=0.72)
ACCENT = dict(color=(0.42, 0.62, 0.16), metal=0.45, rough=0.30,
              emit=(0.045, 0.075, 0.012))
BRASS = dict(color=(0.62, 0.49, 0.26), metal=0.95, rough=0.16)

COUNTS = (8, 4, 5, 7)          # the site's own categories
GAP = 0.40                     # plate pitch inside a column
# The column's WIDTH is PX (a plate is stood on edge in the stacks), its depth is
# PZ, and PY is how thick one sheet is.
# column width, sheet thickness, depth. Broadside, this makes a 1 x 0.84 face.
PX, PY, PZ = 0.52, 0.13, 0.44


def stack_index():
    """Which (column, row) each of the 24 plates belongs to, and its stack height."""
    out = []
    for c, n in enumerate(COUNTS):
        for r in range(n):
            out.append((c, r, n))
    return out


def plate_positions(t, layout):
    """Two arrangements, morphed by `layout` (0 = stacks, 1 = the menu plane).

    stacks — four upright columns of unequal height (8 / 4 / 5 / 7), standing on
             the floor like a small city. PX is the column's WIDTH.
    plane  — the same 24 plates turned broadside and spaced into a 6 x 4 grid, so
             the whole menu appears at once. The plates do not move through each
             other; they rotate and settle.
    """
    u = max(0.0, min(1.0, layout))
    e = u * u * (3 - 2 * u)
    pos, rot = [], []
    for i, (c, r, n) in enumerate(stack_index()):
        # --- stacks: four measured columns, left to right
        sx = (c - 1.5) * 2.62
        sy = (r - (n - 1) / 2.0) * GAP
        sz = 0.0
        # --- plane: 6 x 4 lattice, broadside
        gx = (i % 6 - 2.5) * 0.98
        gy = (i // 6 - 1.5) * 0.98
        gz = 0.0
        pos.append((sx + (gx - sx) * e, sy + (gy - sy) * e, sz + (gz - sz) * e))
        rot.append((math.radians(90) * e, 0.0, 0.0))   # stand up as they spread
    return pos, rot


# -------------------------------------------------------------------- camera
def frame_camera(parts, az_deg, el_deg, fill, fov=30.0, W=720, H=1280,
                 yshift=0.0, centre=None):
    """Distance solved by bisection on PROJECTED WIDTH, then the look-at is walked
    until the subject's centre sits where the type needs it. Same machinery
    engines/sr71-3d/frame.py uses, re-derived here so the subject can be a
    multi-part assembly that changes shape between shots."""
    allv = np.vstack([p[0] for p in parts])
    lo, hi = allv.min(0), allv.max(0)
    c = np.asarray(centre if centre is not None else (lo + hi) / 2, float)
    a, e = np.radians(az_deg), np.radians(el_deg)
    d = np.array([np.sin(a) * np.cos(e), np.sin(e), np.cos(a) * np.cos(e)])
    fpx = (1.0 / np.tan(np.radians(fov) / 2)) * (H / 2)
    radius = max(0.3, float(np.max(np.linalg.norm(allv - c, axis=1))))
    ctr = c.copy()

    def span(ctr_, dist):
        eye = ctr_ + d * dist
        R, _ = look_at(eye, ctr_)
        Vc = (R @ (allv - eye).T).T
        z = np.maximum(-Vc[:, 2], 1e-3)
        x = Vc[:, 0] * fpx / z
        y = -Vc[:, 1] * fpx / z
        return (x.max() - x.min()) / W, (y.max() + y.min()) / 2 / H, R

    lo_d, hi_d = 0.4 * radius, 24.0 * radius
    dist = hi_d
    for _ in range(4):
        lo_d, hi_d = 0.4 * radius, 24.0 * radius
        for _ in range(44):
            dm = 0.5 * (lo_d + hi_d)
            rx, _, _ = span(ctr, dm)
            if rx > fill:
                lo_d = dm
            else:
                hi_d = dm
        dist = 0.5 * (lo_d + hi_d)
        _, ymid, R = span(ctr, dist)
        err = yshift - ymid
        if abs(err) < 0.004:
            break
        vis_h = 2.0 * dist * np.tan(np.radians(fov) / 2)
        ctr = ctr + R[1] * (err * vis_h)
    return ctr + d * dist, ctr


# --------------------------------------------------------------------- scene
LIGHTS = [
    (np.array([0.42, 0.82, 0.38]), np.array([1.00, 0.97, 0.92]), 2.35),   # key
    (np.array([-0.72, 0.28, -0.62]), np.array([0.52, 0.60, 0.76]), 0.85),  # cool fill
    (np.array([0.08, -0.92, 0.38]), np.array([1.00, 0.90, 0.76]), 0.55),   # paper bounce
]


def build(t, S):
    """Return [(V, F, mat), ...] for the shot's state. `S` is the scene spec."""
    parts = []
    layout = S.get("layout", 0.0)
    if callable(layout):
        layout = layout(t)
    drop = S.get("drop", 0.0)          # 0..1 plates still rising into place
    if callable(drop):
        drop = drop(t)

    # ONE PLATE LIFTS OUT OF THE STACK.
    # The story's hinge: twenty-four plates, and one of them is your answer. It
    # rises out of its slot, turns broadside and comes toward the viewer, while
    # the other twenty-three quieten down. `lift_u` runs 0..1.
    lift = S.get("lift")                 # (col, row) or None
    lu = S.get("lift_u", 0.0)
    if callable(lu):
        lu = lu(t)
    lu = max(0.0, min(1.0, lu))
    le = lu * lu * (3 - 2 * lu)
    # the twenty-three that stay behind lose their lustre, not their legibility
    dimmed = INK_SOFT if le > 0.02 else None

    only = S.get("only")            # render just this (col,row) — a hero plate
    positions, rots = plate_positions(t, layout)
    for i, ((c, r, n), p, rr) in enumerate(zip(stack_index(), positions, rots)):
        if only is not None and (c, r) != only:
            continue
        # each plate rises into its slot on a small stagger, then floats
        k = np.clip((drop - i * 0.012) / 0.55, 0.0, 1.0)
        e = 1 - (1 - k) ** 3
        y = p[1] - (1 - e) * 3.2
        breathe = math.sin(t * 1.1 + i * 0.7) * 0.018
        roll = math.sin(t * 0.7 + i * 0.9) * 0.05
        hot = S.get("hot")
        chosen = bool(hot is not None and hot(c, r, t))

        V, F = box(PX, PY, PZ, bevel=0.07)
        if chosen and lift is not None:
            # straight up out of its own column. It keeps its stacking pose: a
            # plate that turns broadside mid-rise reads as a card appearing, and
            # at these angles a broadside plate is nearly edge-on anyway.
            tx, ty, tz = S.get("lift_to", (p[0], p[1] + 1.9, 0.0))
            p = (p[0] + (tx - p[0]) * le, p[1] + (ty - p[1]) * le, p[2] + (tz - p[2]) * le)
            yaw = S.get("lift_yaw", 0.0) * le
            V = xf(V, rot_xyz(ax=rr[0], ay=yaw, az=roll * 0.20 + le * 0.22),
                   (p[0], p[1], p[2]))
            mat = ACCENT
        else:
            V = xf(V, rot_xyz(ax=rr[0] + roll * 0.3, az=roll), (p[0], y + breathe, p[2]))
            mat = (dimmed or INK) if not chosen else INK
        parts.append((V, F, mat))

    for extra in S.get("extra", []):
        parts.extend(extra(t))

    if S.get("ring"):
        u = S["ring"](t)
        V, F = torus(2.35, 0.030, 128, 12)
        V = xf(V, rot_xyz(ax=math.radians(78), az=t * 0.25), (0, 0.1, 0))
        parts.append((V, F, BRASS if u > 0.5 else INK_SOFT))
    return parts


def render(t, S, W, H, ss=1):
    parts = build(t, S)
    sc = GalleryScene(W, H, ss=ss, bg=PAPER, bg_top=PAPER)
    sc.lights = LIGHTS
    sc.glow = None
    for V, F, mat in parts:
        sc.add((V, F), mat)
    if S.get("eye") is not None and S.get("ctr") is not None:
        eye, ctr = S["eye"], S["ctr"]      # locked: solved once, held for the shot
    else:
        eye, ctr = frame_camera(parts, S["az"](t), S["el"](t), S["fill"](t),
                                fov=S.get("fov", 30.0), W=W, H=H,
                                yshift=S.get("yshift", 0.10))
    sc.set_camera(eye, ctr, fov=S.get("fov", 30.0))
    return sc.render()


def flatten(img):
    """Normalise a light-ground render so its paper becomes pure white.

    Then the plate can be composited with MULTIPLY: white leaves the page
    untouched, and the object darkens it exactly as it was lit. No alpha channel,
    no premultiplication, and therefore no way for a rectangle to leak through —
    which is what three attempts at an alpha cut-out kept doing.
    """
    a = np.asarray(img.convert("RGB"), np.float32)
    paper = np.percentile(a.reshape(-1, 3), 99, axis=0)
    out = np.clip(a * (255.0 / np.maximum(paper[None, None, :], 1.0)), 0, 255)
    # Snap the ground to pure white. The rasteriser's per-frame film grain lives
    # on the paper too, so a fixed 246 threshold left grey speckle that multiplied
    # into a visible rectangle. Anything within 4 % of the paper IS the paper.
    ground = out.mean(axis=2) >= float(paper.mean()) * 0.955
    out[ground] = 255
    return out.astype(np.uint8)


def content_window(images, pad=0.05):
    """The stable crop window for a shot's 3D plate.

    A frame solved by projected WIDTH leaves a multi-column subject floating in a
    mostly-empty canvas (measured: the stacks occupied the top third of an
    820x760 render). Cropping per frame is not an option — the bbox changes as the
    subject turns, so the crop would rescale every frame and the object would
    appear to pump. So: measure the bbox at the extremes of the shot, take the
    union, and use that ONE window for every frame.
    """
    boxes = []
    for img in images:
        a = np.asarray(img).mean(axis=2)
        ys, xs = np.where(a < 250)
        if len(xs):
            boxes.append((xs.min(), ys.min(), xs.max(), ys.max()))
    if not boxes:
        h, w = np.asarray(images[0]).shape[:2]
        return 0, 0, w, h
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    m = pad * max(1, max(x1 - x0, y1 - y0))
    h, w = np.asarray(images[0]).shape[:2]
    return (int(max(0, x0 - m)), int(max(0, y0 - m)),
            int(min(w, x1 + m + 1)), int(min(h, y1 + m + 1)))


def place_window(c, arr, win, cx, cy, max_w, max_h, scale=1.0, blend="multiply"):
    """Draw a flattened plate cropped to `win`, FITTED into a box at (cx, cy).

    Fitting matters: the crop's pixel size is whatever the shot's content window
    happened to be, so drawing it at raw size made the object's on-screen scale
    an accident of the render resolution.
    """
    import kit as K
    x0, y0, x1, y1 = win
    sub = np.asarray(arr)[y0:y1, x0:x1]
    h, w = sub.shape[:2]
    k = min(max_w / w, max_h / h) * scale
    pw, ph = w * k, h * k
    K.image(c, sub, cx - pw / 2, cy - ph / 2, pw, ph, 1.0, blend=blend)


def hero_plate(ax_deg, el_deg, yaw_deg, W=640, H=520, fill=0.80, mat=None):
    """One plate, framed as a product shot.

    `render(... only=(c,r))` keeps the plate in its stacking pose, i.e. lying flat,
    which makes it read as a card. This stands it broadside and lights it on its
    own, so the payoff frame is a plate and not a rectangle.
    """
    mat = mat or ACCENT
    V, F = box(PX, PY, PZ, bevel=0.09)
    V = xf(V, rot_xyz(ax=math.radians(ax_deg), az=math.radians(yaw_deg)), (0, 0, 0))
    sc = GalleryScene(W, H, bg=PAPER, bg_top=PAPER)
    sc.lights = LIGHTS
    sc.glow = None
    sc.add((V, F), mat)
    eye, ctr = frame_camera([(V, F, mat)], 0.0, el_deg, fill, fov=30.0,
                            W=W, H=H, yshift=0.0)
    sc.set_camera(eye, ctr, fov=30.0)
    return sc.render()
