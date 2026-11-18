"""
The edit. One dict per shot; the camera AND the mechanism are functions of time.

Rewritten after reviewing the first cut. The previous one looked acceptable frame
by frame but two things were wrong underneath:

  1. the mechanism was faked — the seam gaps were static geometry, so the
     "it seals itself" beat showed nothing, and
  2. the argument skipped the middle — it went from "panels are loose" straight
     to "melt 300 °C of airframe" without ever saying why there was fuel loose
     in the first place.

What the sources actually support is a chain:

    loose panels  ->  the gaps are open when cold  ->  the skin IS the tank
    ->  so it drips on the ground  ->  Mach 3 heats the metal  ->  the joints
    close and it seals in flight

So the film states that chain, and every beat animates the thing it claims.

`hold` is a precomputed camera: (eye at cut, eye after the beat has landed,
look-at point). Holding the camera still while the seam closes is the whole
point — a camera that kept refitting the subject would give the reveal away.
"""
import numpy as np

FPS = 24

SHOTS = [
    # ---------------------------------------------------------- 1 · hook
    # Starts under the belly in the rain of fuel, pulls back and up to reveal the
    # whole aircraft. The paradox is legible in 1.2 s, which is what the format
    # is for.
    dict(name="hook", start=0.0, end=5.0,
         hold=([10.137, -3.197, 10.744], [2.826, 0.346, 8.740], [-0.003, -0.885, 0.243]),
         cam=dict(az=44, el=-9, fill=1.10, fov=34, target=(0.10, 0.05, 0.35), yshift=-0.10),
         orbit=dict(az=-26, el=13, fill=0.22),
         text="hook", light="cold", drips=1.0, gap0=0.52, gap1=0.62),

    # ---------------------------------------------------------- 2 · the gaps
    # The mechanism, stated: cold metal, wide joints, and the joints are what it
    # is leaking through.
    dict(name="gaps", start=5.0, end=11.0,
         hold=([15.432, 5.075, 6.260], [10.930, 2.607, 9.174], [0.220, -0.499, 0.723]),
         cam=dict(az=70, el=19, fill=1.28, fov=31, target=(0.02, 0.12, 0.65), yshift=-0.09),
         orbit=dict(az=-18, el=-7, fill=0.04),
         text="gaps", light="cold", drips=1.0, gap0=0.30, gap1=0.62),

    # ---------------------------------------------------------- 3 · skin = tank
    # The thing almost nobody knows: there was no tank inside. The panels are the
    # wall. Macro, and the gap between two panels is the shot.
    dict(name="tank", start=11.0, end=16.8,
         hold=([0.567, 6.654, 8.110], [-0.141, 5.302, 8.083], [0.062, -0.851, 0.880]),
         cam=dict(az=4, el=46, fill=1.34, fov=30, target=(0.0, 0.0, 0.0), yshift=-0.20),
         orbit=dict(az=-5, el=-6, fill=0.14),
         text="tank", light="cold", plate=True, plate_gap0=0.44, plate_gap1=0.44,
         plate_heat=0.0, plate_heat0=0.0),

    # ---------------------------------------------------------- 4 · the heat
    # Mach 3. The airframe goes emissive and the camera orbits: the turn of the
    # film, and the only place the metal is allowed to look hot.
    dict(name="heat", start=16.8, end=23.2,
         hold=([13.012, 6.461, 6.627], [5.276, 2.952, 9.370], [0.280, -0.448, 0.417]),
         cam=dict(az=64, el=26, fill=1.26, fov=33, target=(0.04, 0.10, 0.30), yshift=-0.09),
         orbit=dict(az=-34, el=-8, fill=0.10),
         text="heat", light="hot", drips=0.0, gap0=0.62, gap1=0.62),

    # ---------------------------------------------------------- 5 · it seals
    # THE beat. Same two panels as beat 3, now closing in real geometry with a
    # glowing edge that gets swallowed as they meet. Held camera.
    dict(name="seal", start=23.2, end=30.2,
         hold=([0.567, 6.654, 8.110], [-0.171, 6.219, 9.799], [0.062, -0.851, 0.880]),
         cam=dict(az=4, el=46, fill=1.34, fov=30, target=(0.0, 0.0, 0.0), yshift=-0.20),
         orbit=dict(az=-5, el=-7, fill=-0.26),
         text="seal", light="hot", plate=True, plate_gap0=0.44, plate_gap1=0.012,
         plate_heat=1.0, plate_heat0=0.42),

    # ---------------------------------------------------------- 6 · why JP-7
    # Back out to the aircraft. The fuel is the coolant, and it is too stable to
    # spark — which is the reason the next beat exists at all.
    dict(name="fuel", start=30.2, end=36.0,
         hold=([18.972, 3.255, 2.466], [14.039, 1.684, 7.905], [0.175, -0.780, -0.175]),
         cam=dict(az=82, el=12, fill=1.22, fov=31, target=(0.0, 0.05, -0.20), yshift=-0.10),
         orbit=dict(az=-22, el=-4, fill=0.08),
         text="fuel", light="cold", drips=0.0, gap0=0.30, gap1=0.0),

    # ---------------------------------------------------------- 7 · green
    # TEB burns green. One colour, one plume, out.
    dict(name="green", start=36.0, end=41.5,
         hold=([20.117, 2.833, -6.966], [20.075, 4.433, -2.100], [0.718, -0.692, -2.130]),
         cam=dict(az=104, el=10, fill=1.10, fov=30, target=(0.60, 0.00, -2.10), yshift=-0.10),
         orbit=dict(az=-14, el=5, fill=0.10),
         text="green", light="green", drips=0.0, gap0=0.0, gap1=0.0, flame=1.0),

    # ---------------------------------------------------------- 8 · close
    # Pays off the hook, then names the mechanism in five words.
    dict(name="close", start=41.5, end=51.0,
         hold=([10.091, 5.603, 11.363], [2.741, 2.440, 9.618], [0.085, -0.137, 0.250]),
         cam=dict(az=42, el=21, fill=1.06, fov=32, target=(0.04, 0.04, 0.20), yshift=-0.04),
         orbit=dict(az=-26, el=-6, fill=0.16),
         text="close", light="cold", drips=0.0, gap0=0.0, gap1=0.0),
]

DURATION = SHOTS[-1]["end"]
