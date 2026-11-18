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
from shots import SHOTS, COPY, FPS, DURATION

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
            (np.array([0.30, 0.80, 0.45]), np.array([1.00, 0.80, 0.62]), 1.85),
            (np.array([-0.70, 0.32, -0.62]), np.array([0.35, 0.52, 1.00]), 0.95),
            (np.array([0.05, -0.80, 0.55]), np.array([1.00, 0.34, 0.10]), 0.75),
        ], exposure=1.34, bloom=0.78),
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
    "hook":      ("SR-71 Blackbird · 1964", ["THE SR-71", "LEAKED FUEL."], None),
    "cold_a":    ("01 · the cold airframe", ["BUILT", "LOOSE."], None),
    "cold_b":    ("01 · expansion joints", ["GAPS AT", "EVERY SEAM."], None),
    "hot_a":     ("02 · Mach 3 · 460–620 °F", ["THE METAL", "GROWS."], None),
    "hot_b":     ("02 · thermal expansion", ["IT SEALS", "ITSELF."], None),
    "fuel_a":    ("03 · JP-7", ["COOLANT", "FIRST."], None),
    "fuel_b":    ("03 · flash point 140 °F", ["TOO STABLE", "TO SPARK."], None),
    "teb_a":     ("04 · triethylborane", ["TEB", "IGNITES IT."], None),
    "teb_b":     ("04 · ignition", ["IT BURNS", "GREEN."], "not a fuel leak — an engine start."),
    "close":     ("Zero leaks at Mach 3", ["IT DIDN'T", "LEAK."], None),
}

TEXT_TIMING = {
    # when the block in / out within its shot, plus whether it is centred
    "hook":   (0.15, 4.30, "ms"),
    "cold_a": (0.30, 3.95, "ls"),
    "cold_b": (0.30, 4.20, "ls"),
    "hot_a":  (0.30, 4.70, "ls"),
    "hot_b":  (0.35, 5.60, "ms"),
    "fuel_a": (0.25, 3.90, "ls"),
    "fuel_b": (0.25, 3.30, "ls"),
    "teb_a":  (0.30, 4.90, "ls"),
    "teb_b":  (0.30, 3.00, "ms"),
    "close":  (0.40, 8.30, "ms"),
}

PIN_LABELS = {
    # per-shot annotation: (time in shot, screen xy, text, side)
    "cold_a": [(0.9, (250, 1250), "panel gap", "right")],
    "cold_b": [(0.8, (250, 1150), "skin = tank wall", "right")],
    "hot_a":  [(0.7, (240, 1300), "hot skin", "right")],
    "hot_b":  [(1.0, (250, 1180), "seams closed", "right")],
    "teb_a":  [(0.8, (300, 1240), "TEB injector", "right")],
}


def ease_io(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 4


def build_parts(shot, tt):
    """Subject geometry for this frame, with time-dependent state."""
    heat = 0.0
    if shot.get("light") == "hot":
        heat = 0.55
    if shot.get("seams"):
        seams = 0.0
    else:
        seams = 0.0
    if shot.get("plate"):
        # macro beat: titanium panels, with the gap between them the subject
        gap = shot.get("plate_gap", 0.10)
        parts = M.build_plate(width=3.2, height=1.7, gap=gap, heat=0.0)
        return parts
    parts = M.build_sr71(seam_light=bool(shot.get("seams")),
                         heat=heat, seams_open=seams)
    if shot.get("drips"):
        parts += M.build_fuel_drops(n=26, t=tt)
    return parts


def render_frame(shot, t_abs, W, H, ss):
    tt = t_abs - shot["start"]
    parts = build_parts(shot, tt)
    # subject scale changes: the "seal" beat zooms the skin, the fuel beats show
    # a plate of titanium instead of the whole aircraft
    c = shot["cam"]
    o = shot["orbit"]
    prog = (tt / max(1e-6, shot["end"] - shot["start"]))
    e = ease_io(prog)
    az = c["az"] + (o["az"]) * e
    el = c["el"] + (o["el"]) * e
    fill = c["fill"] + o["fill"] * e
    tgt = np.array(c.get("target", (0, 0, 0)), float)
    eye, ctr = orbit_cam(parts, az=az, el=el, fill=fill, fov=c["fov"],
                         W=W, H=H, centre=tgt)
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
            head_size = int(H * 0.075)
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
                OV.gradient_scrim(scr, top_frac=max(0.30, top / H - 0.16),
                                  alpha=0.88 * alpha)
                img.alpha_composite(scr)
            OV.draw_text_block(img, at, overline, head, note, align=align,
                            head_size=head_size, alpha=alpha,
                            accent_word="LEAKED" if key == "hook" else None)
    # pins and hot labels
    if key in PIN_LABELS:
        for (pin_t, xy, txt, side) in PIN_LABELS[key]:
            if tt >= pin_t:
                a = ease_out((tt - pin_t) / 0.5)
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
    OV.hud(img, t_abs, SHOTS.index(shot), shot["name"], alpha=0.9)
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
            if total % 12 == 0:
                el = time.time() - t_start
                print(f"  {total} frames  {el:.0f}s  ({total / el:.2f} f/s)", flush=True)
    proc.stdin.close()
    proc.wait()
    print(f"done {total} frames in {time.time() - t_start:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
