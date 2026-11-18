"""
render.py — renders the film frame by frame and pipes it to ffmpeg.

    python3 render.py --w 540 --h 960 --ss 2 --fps 24 --out /tmp/prev.mp4 --shots 1,2

Frame pipeline:  3D plate (NumPy raster) -> heat haze -> type/HUD (PIL) -> RGB24
The camera, the subject and every text element are pure functions of time, so any
frame can be re-rendered on its own for inspection.
"""
import argparse
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

import model as M
from engine import Scene
from frame import orbit_cam
import overlay as OV
from shots import SHOTS, FPS, DURATION

LIGHT_PRESETS = {
    "cold": dict(
        bg=(0.010, 0.014, 0.024), bg_top=(0.030, 0.048, 0.082),
        lights=[
            (np.array([0.35, 0.86, 0.38]), np.array([0.86, 0.93, 1.00]), 1.55),
            (np.array([-0.75, 0.30, -0.55]), np.array([0.30, 0.55, 1.00]), 1.30),
            (np.array([0.10, -0.85, 0.45]), np.array([1.00, 0.48, 0.22]), 0.22),
        ], exposure=1.30, bloom=0.62),
    "hot": dict(
        bg=(0.020, 0.012, 0.010), bg_top=(0.075, 0.032, 0.018),
        lights=[
            (np.array([0.30, 0.80, 0.45]), np.array([1.00, 0.70, 0.46]), 1.45),
            (np.array([-0.70, 0.32, -0.62]), np.array([0.35, 0.52, 1.00]), 0.95),
            (np.array([0.05, -0.80, 0.55]), np.array([1.00, 0.30, 0.08]), 0.45),
        ], exposure=1.26, bloom=0.60),
    "green": dict(
        bg=(0.008, 0.020, 0.016), bg_top=(0.020, 0.070, 0.055),
        lights=[
            (np.array([0.20, 0.75, 0.30]), np.array([0.65, 1.00, 0.85]), 1.75),
            (np.array([-0.72, 0.28, -0.60]), np.array([0.30, 0.50, 1.00]), 0.85),
            (np.array([0.20, -0.70, 0.60]), np.array([0.30, 1.00, 0.65]), 0.45),
        ], exposure=1.38, bloom=0.92),
}

TEXT_BLOCKS = {
    # (overline, headline lines, note)
    "hook":   ("SR-71 Blackbird · 1964", ["THE SR-71", "LEAKED FUEL."], None),
    "gaps":   ("01 · on the ground", ["BUILT", "LOOSE."], None),
    "tank":   ("02 · no rubber bladder", ["THE SKIN", "IS THE TANK."], None),
    "heat":   ("03 · Mach 3 · 460–620 °F", ["THE METAL", "GROWS."], None),
    "seal":   ("04 · thermal expansion", ["IT SEALS", "ITSELF."],
               "open when cold. closed at Mach 3."),
    "fuel":   ("05 · JP-7", ["COOLANT", "FIRST."],
               "flash point 140 °F. too stable to spark."),
    "green":  ("06 · triethylborane", ["IT BURNS", "GREEN."], None),
    "close":  ("Mach 3 · no leaks", ["IT DIDN'T", "LEAK."],
               "it leaked because it grew."),
}

TEXT_TIMING = {
    "hook":   (0.10, 4.80, "ms"),
    "gaps":   (0.40, 6.00, "ls"),
    "tank":   (0.35, 5.60, "ms"),
    "heat":   (0.40, 6.20, "ls"),
    "seal":   (0.45, 6.80, "ms"),
    "fuel":   (0.35, 5.80, "ls"),
    "green":  (0.35, 4.60, "ms"),
    "close":  (0.50, 8.60, "ms"),
}

# Macro beats carry less copy: the plate fills the frame, so the type steps back.
TEXT_SCALE = {"tank": 0.86, "seal": 0.86, "close": 1.0}
# Never scrim above this fraction of frame height on the macro/aircraft beats.
SCRIM_TOP = {"tank": 0.52, "seal": 0.52, "hook": 0.34, "gaps": 0.40,
             "heat": 0.34, "fuel": 0.40, "green": 0.36, "close": 0.44}

# (time in, pixel position at 1080x1920, label, side). Every one is placed above
# the type block, on the object it names, and nothing shares a row with anything.
PIN_LABELS = {
    "gaps":  [(0.9, (215, 1020), "panel gap", "right")],
    "tank":  [(0.9, (200, 700), "the wall is the tank", "right")],
    "seal":  [(0.7, (200, 700), "the gap closes", "right"),
              (3.4, (200, 700), "sealed in flight", "right")],
    "fuel":  [(1.0, (250, 1000), "JP-7 as heat sink", "right")],
    "green": [(1.2, (250, 1180), "TEB injection", "right")],
}


def ease_io(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


HOLD_AT = 0.55


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 4


def build_parts(shot, tt, prog=0.0):
    """
    Subject geometry for this frame. The mechanism is animated HERE, in 3D —
    the seam gap and the skin expansion are real geometry that moves, not a
    painted line, so the 'it seals itself' beat actually shows sealing.
    """
    heat = 0.0
    if shot.get("light") == "hot":
        heat = 0.55
    g0 = shot.get("gap0", 0.0)
    g1 = shot.get("gap1", g0)
    gaps = g0 + (g1 - g0) * ease_io(prog)
    if shot.get("plate"):
        # macro beat: two titanium panels whose gap closes as they heat up
        pg0 = shot.get("plate_gap0", 0.60)
        pg1 = shot.get("plate_gap1", 0.06)
        # the joint closes over most of the beat, not in its first third: this is
        # the shot the film exists for, so it gets the whole runtime
        u = min(1.0, max(0.0, (prog - 0.06) / 0.74))
        ease = ease_io(u)
        gap = pg0 + (pg1 - pg0) * ease
        h0 = shot.get("plate_heat0", 0.0)
        hot = h0 + (shot.get("plate_heat", 0.0) - h0) * ease_io(prog)
        return M.build_plate(width=3.2, height=1.7, gap=gap, heat=hot)
    parts = M.build_sr71(seam_light=bool(shot.get("gap1", 0) > 0.25),
                         heat=heat, seams_open=gaps, expand=gaps * 1.15)
    if shot.get("drips"):
        parts += M.build_fuel_drops(t=tt)
    if shot.get("flame"):
        # lights a beat after the cut, so the cut itself is the reveal
        parts += M.build_flame(t=max(0.0, tt - 0.5), length=1.30)
    return parts


def _breathe(eye, ctr, prog, sweep=3.2, push=0.038):
    """
    A slow, continuous camera move that never changes the framing decision.

    A locked-off frame with a static mechanism measures as a freeze (the diff
    pass flags it), and it feels dead. So every held shot still sweeps a couple of
    degrees and pushes in ~2% across its length, with a slight vertical float at a
    different period so the two never beat together.
    """
    v = eye - ctr
    r = np.linalg.norm(v)
    a = np.radians(sweep) * (prog - 0.5)
    c, s_ = np.cos(a), np.sin(a)
    # rotate about the world Y axis
    vx = c * v[0] + s_ * v[2]
    vz = -s_ * v[0] + c * v[2]
    v = np.array([vx, v[1], vz])
    v = v * (1.0 - push * (prog - 0.5))
    v[1] += r * 0.012 * np.sin(2 * np.pi * (prog * 0.7 + 0.15))
    return ctr + v, ctr


def shot_cam(shot, prog, W, H):
    """
    The camera for one moment.

    A shot may carry a precomputed `hold`: an (eye, ctr) read off after the beat
    has landed. That keeps the frame still while the mechanism moves — a camera
    that keeps fitting a shrinking object would drift backwards and give the
    'sealed' reveal away. Before the hold, the camera is solved from the geometry.
    """
    c = shot["cam"]
    o = shot["orbit"]
    e = ease_io(prog)
    az = c["az"] + o["az"] * e
    el = c["el"] + o["el"] * e
    fill = c["fill"] + o["fill"] * e
    tgt = np.array(c.get("target", (0, 0, 0)), float)
    ysh = c.get("yshift", -0.06)
    hold = shot.get("hold")
    if hold is not None:
        eye0, eye1 = np.array(hold[0], float), np.array(hold[1], float)
        ctr = np.array(hold[2], float)
        if prog >= HOLD_AT:
            eye = eye1
        else:
            eye = eye0 + (eye1 - eye0) * ease_io(prog / HOLD_AT)
        return _breathe(eye, ctr, prog)
    # frame on the subject with the particles switched off
    rig = build_parts(dict(shot, drips=0.0), prog * (shot["end"] - shot["start"]), prog)
    return orbit_cam(rig, az=az, el=el, fill=fill, fov=c["fov"], W=W, H=H,
                     centre=tgt, yshift=ysh)


def render_frame(shot, t_abs, W, H, ss):
    tt = t_abs - shot["start"]
    prog = tt / max(1e-6, shot["end"] - shot["start"])
    parts = build_parts(shot, tt, prog)
    c = shot["cam"]
    eye, ctr = shot_cam(shot, prog, W, H)
    # a slow lateral drift in screen space, so even a "static" beat breathes
    drift = np.array([np.sin(prog * np.pi * 0.9) * 0.06, 0, 0])

    preset = LIGHT_PRESETS[shot.get("light", "cold")]
    sc = Scene(W, H, ss=ss, bg=preset["bg"], bg_top=preset["bg_top"])
    sc.lights = preset["lights"]
    sc.exposure = preset["exposure"]
    sc.bloom_amt = preset["bloom"]
    for V, F, mat in parts:
        sc.add((V, F), mat)
    sc.glow = {"cold": ((0.10, 0.20, 0.42), 0.40, 0.55, 0.55),
               "hot": ((0.55, 0.22, 0.06), 0.44, 0.55, 0.50),
               "green": ((0.10, 0.45, 0.30), 0.42, 0.55, 0.45)}[shot.get("light", "cold")]
    sc.set_camera(eye + drift, ctr, fov=c["fov"])
    sc.grain_seed = 1234 + int(round(t_abs * 24)) % 4096
    img = sc.render()

    # --- flat layer -------------------------------------------------------
    if shot.get("light") == "hot":
        img = OV.heat_haze(img, 0.35 + 0.25 * np.sin(prog * 6))
    img = img.convert("RGBA")

    key = shot["text"]
    if key in TEXT_BLOCKS:
        t_in, t_out, align = TEXT_TIMING[key]
        overline, head, note = TEXT_BLOCKS[key]
        if tt >= t_in - 0.02 and tt <= t_out:
            k = ease_out((tt - t_in) / 0.55)
            alpha = k * (1 - ease_io((tt - (t_out - 0.5)) / 0.5) if tt > t_out - 0.5 else 1.0)
            alpha = max(0.0, min(1.0, alpha))
            head_size = int(H * 0.075 * TEXT_SCALE.get(key, 1.0))
            lines = head if isinstance(head, list) else [head]
            blk_h = OV.text_block_size(head, head_size, note)
            top = int(H * 0.905 - blk_h)
            if align == "ms":
                at = (W / 2, top)
            else:
                at = (OV.safe()["left"] + 6, top)
            # a soft scrim that fades out: type never fights the metal, and the
            # plate is never cut by a visible rectangle
            if alpha > 0.02:
                scr = Image.new("RGBA", img.size, (0, 0, 0, 0))
                # start the scrim below the mechanism: the plate must never sit
                # on top of a panel and dim it
                floor = SCRIM_TOP.get(key, 0.30)
                OV.gradient_scrim(scr, top_frac=max(floor, top / H - 0.05),
                                  alpha=0.90 * alpha)
                img.alpha_composite(scr)
            OV.draw_text_block(img, at, overline, head, note, align=align,
                            head_size=head_size, alpha=alpha,
                            accent_word="LEAKED" if key == "hook" else None,
                            size_k=TEXT_SCALE.get(key, 1.0))
    # pins and hot labels. Only the MOST RECENT one is drawn: two labels that
    # share a position overprinted each other into gibberish in v1 of this cut.
    if key in PIN_LABELS:
        active = None
        for (pin_t, xy, txt, side) in PIN_LABELS[key]:
            if tt >= pin_t:
                active = (pin_t, xy, txt, side)
        if active is not None:
            pin_t, xy, txt, side = active
            # fade the outgoing label as the next one arrives, not on top of it
            fade = 1.0
            for (nxt_t, *_rest) in PIN_LABELS[key]:
                if nxt_t > pin_t:
                    fade = 1.0 - ease_io((tt - (nxt_t - 0.45)) / 0.45)
                    break
            a = max(0.0, min(1.0, ease_out((tt - pin_t) / 0.5) * fade))
            if a > 0.01:
                OV.label_pin(img, (xy[0] * W / 1080, xy[1] * H / 1920), txt,
                             alpha=a, color=OV.ACCENT, side=side)
    if key == "teb_b" and tt > 0.4:
        a = ease_out((tt - 0.4) / 0.8)
        OV.glow_text(img, (W * 0.07, H * 0.30), "GREEN FLASH", size=int(H * 0.032),
                     color=OV.GREEN, alpha=a)
    if key == "close" and tt > 2.2:
        a = ease_out((tt - 2.2) / 0.8)
        d = OV.ImageDraw.Draw(img)
        d.text((W / 2, H * 0.955), "Schematic model, not to scale",
               font=OV.font("mono", max(11, int(22 * W / 1080))),
               fill=(150, 158, 172, int(210 * a)), anchor="ms")
    OV.hud(img, t_abs, SHOTS.index(shot), shot["name"], alpha=0.9,
           total=len(SHOTS), duration=DURATION)
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--ss", type=int, default=2)
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--out", default="/tmp/zv71.mp4")
    ap.add_argument("--shots", default="")
    ap.add_argument("--still", default="")
    ap.add_argument("--stride", type=float, default=1.0)
    args = ap.parse_args()

    shots = SHOTS
    if args.shots:
        idx = [int(x) - 1 for x in args.shots.split(",")]
        shots = [SHOTS[i] for i in idx]

    if args.still:
        t = float(args.still)
        shot = [s for s in SHOTS if s["start"] <= t < s["end"]][0]
        img = render_frame(shot, t, args.w, args.h, args.ss)
        img.save("/tmp/still.png")
        print("wrote /tmp/still.png at", t)
        return

    cmd = ["/home/user/.local/bin/ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{args.w}x{args.h}",
           "-r", str(args.fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_start = time.time()
    total = 0
    for shot in shots:
        n = int(round((shot["end"] - shot["start"]) * args.fps / args.stride))
        for i in range(n):
            t = shot["start"] + i * args.stride / args.fps
            img = render_frame(shot, t, args.w, args.h, args.ss)
            proc.stdin.write(img.tobytes())
            total += 1
            if total % 40 == 0:
                el = time.time() - t_start
                print(f"  {total} frames  {el:.0f}s  ({total / el:.2f} f/s)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"done {total} frames in {time.time() - t_start:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
