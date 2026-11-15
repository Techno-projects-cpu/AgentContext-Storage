"""
The edit. One dict per shot; the camera is a function of time inside each shot.

Format, after watching what the channel actually does: a vertical short whose
first two seconds state the paradox, then one clean mechanism per beat, then a
closing line that is the shareable sentence. 52 s total — a "test" at the length
where the format is legible, not a 20 s trailer.

Motion is explicit: every shot gets a camera rig plus the subject's own move,
so the 3D never stands still and never moves for no reason.
"""
import numpy as np

# ---- copy. nothing in this file is a claim the sources do not make ----------
COPY = {
    "hook_1": "THE SR-71",
    "hook_2": "LEAKED",
    "hook_3": "FUEL.",
    "hook_4": "ON PURPOSE.",
    "hook_sub": "A spy plane that dripped onto the runway",
    "cold_1": "Titanium grows when it gets hot.",
    "cold_2": "So they built the panels loose.",
    "cold_3": "Cold, the gaps are open.",
    "cold_4": "The skin is the tank.",
    "hot_1": "At Mach 3 the airframe runs 460–620 °F.",
    "hot_2": "The metal expands. The gaps close.",
    "hot_3": "The aircraft seals itself in flight.",
    "fuel_1": "JP-7 was the coolant first, fuel second.",
    "fuel_2": "Flash point 140 °F. A lit match goes out.",
    "fuel_3": "Too stable to spark — TEB lights it.",
    "fuel_4": "TEB burns green.",
    "close_1": "It didn't leak on the way up.",
    "close_2": "It leaked because it grew.",
    "disclaimer": "Schematic model, not to scale. Not an official depiction.",
}

FPS = 24

SHOTS = [
    # ------------------------------------------------ 1 · hook (0 – 4.5)
    dict(name="hook", start=0.0, end=4.5,
         cam=dict(az=58, el=-8, fill=3.10, fov=32, target=(0.30, -0.02, 1.25)),
         orbit=dict(az=-26, el=9, fill=-0.55),    # pulls back to reveal the airframe
         text="hook", light="cold"),

    # ------------------------------------------------ 2 · cold state (4.5 – 13)
    dict(name="cold_front", start=4.5, end=8.6,
         cam=dict(az=76, el=9, fill=1.75, fov=32, target=(0.05, 0.10, 0.45)),
         orbit=dict(az=-8, el=-2, fill=0.05),
         text="cold_a", light="cold", vent=True, drips=0.0, seams=0.0),

    dict(name="cold_side", start=8.6, end=13.0,
         cam=dict(az=98, el=3, fill=2.05, fov=28, target=(0.40, 0.02, 0.95)),
         orbit=dict(az=10, el=1, fill=0.06),
         text="cold_b", light="cold", vent=True, drips=0.2, seams=0.0),

    # ------------------------------------------------ 3 · hot state (13 – 24.5)
    dict(name="heat", start=13.0, end=18.4,
         cam=dict(az=64, el=24, fill=1.80, fov=32, target=(0.05, 0.02, 0.30)),
         orbit=dict(az=-26, el=-6, fill=0.04),
         text="hot_a", light="hot", drips=0.0, seams=1.0),

    dict(name="seal", start=18.4, end=24.5,
         cam=dict(az=104, el=8, fill=2.30, fov=26, target=(0.18, 0.04, -0.30)),
         orbit=dict(az=-16, el=-3, fill=0.06),
         text="hot_b", light="hot", drips=0.0, seams=0.0, seal=True),

    # ------------------------------------------------ 4 · the fuel (24.5 – 32)
    dict(name="fuel", start=24.5, end=28.6,
         cam=dict(az=52, el=15, fill=1.30, fov=34, target=(0, 0.02, 0)),
         orbit=dict(az=-22, el=-6, fill=0.06),
         text="fuel_a", light="cold", plate=True, plate_gap=0.60, drips=1.0),

    dict(name="match", start=28.6, end=32.0,
         cam=dict(az=78, el=9, fill=1.45, fov=32, target=(0, 0.02, 0)),
         orbit=dict(az=-16, el=3, fill=0.05),
         text="fuel_b", light="cold", plate=True, plate_gap=0.38, drips=0.0),

    # ------------------------------------------------ 5 · TEB / ignition (32 – 40)
    dict(name="teb", start=32.0, end=37.2,
         cam=dict(az=86, el=10, fill=1.95, fov=30, target=(0, 0.0, -0.85)),
         orbit=dict(az=-18, el=-2, fill=0.05),
         text="teb_a", light="cold", drips=0.0, ignite=0.35),

    dict(name="green", start=37.2, end=40.4,
         cam=dict(az=68, el=7, fill=1.75, fov=30, target=(0, -0.02, -1.35)),
         orbit=dict(az=-12, el=4, fill=0.04),
         text="teb_b", light="green", drips=0.0, ignite=1.0),

    # ------------------------------------------------ 6 · close (40.4 – 48.5)
    dict(name="close", start=40.4, end=48.5,
         cam=dict(az=30, el=12, fill=2.05, fov=30, target=(0.10, 0.03, 0.55)),
         orbit=dict(az=-19, el=5, fill=0.12),
         text="close", light="cold", drips=0.0),
]

DURATION = SHOTS[-1]["end"]
