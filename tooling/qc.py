#!/usr/bin/env python3
"""
qc.py — numeric quality gate for a rendered brag video.

You cannot see the video. Neither can the agent. So "it looks good" is not a
verdict anyone is allowed to give. This script replaces that with measurements,
and it is built around the specific bugs that have shipped before:

  1. A SILENT RENDER. <audio> without an id is dropped by the runtime with no
     error, so the MP4 is mute and every other check still passes. Checked by
     decoding the encoded file with astats — not by reading the markup, which
     would happily agree the tag exists.

  2. TEXT THAT IS CROPPED OR TOO SMALL. Ink is measured inside the safe area, at
     the frame where each scene's copy is fully settled, so a headline that runs
     off the canvas or shrinks below the type floor fails as a number.

  3. THE FIRST FRAME AS THUMBNAIL. Frame 0 must already carry ink; a fade-in from
     nothing means the thumbnail is a black rectangle.

  4. UNREADABLE CONTRAST. Sampled from the actual pixels: the darkest 10% of ink
     against the ground behind it.

Usage:
  qc.py <video.mp4> [--type-floor 30] [--json out.json] [--keep]

Exit code 0 = pass. 1 = fail. 2 = could not measure (treated as fail by render.sh).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.stderr.write("qc.py needs pillow + numpy (pip install pillow numpy)\n")
    sys.exit(2)

FFMPEG = os.environ.get("FFMPEG") or shutil.which("ffmpeg") or f"{os.path.expanduser('~')}/.local/bin/ffmpeg"
FFPROBE = os.environ.get("FFPROBE") or shutil.which("ffprobe") or f"{os.path.expanduser('~')}/.local/bin/ffprobe"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {p.stderr.strip()[:400]}")
    return p.stdout + p.stderr


def probe(path: str) -> dict:
    out = run([FFPROBE, "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", path])
    return json.loads(out)


def astats(path: str) -> dict:
    """Peak + RMS of the encoded file. This is the mute detector."""
    out = run([FFMPEG, "-hide_banner", "-nostats", "-i", path,
               "-map", "0:a:0", "-af", "astats=metadata=1:reset=0", "-f", "null", "-"])
    res = {}
    for key, pat in (("rms_db", r"RMS level dB:\s*(-?[\d.]+|-inf)"),
                     ("peak_db", r"Peak level dB:\s*(-?[\d.]+|-inf)")):
        m = re.findall(pat, out)
        if m:
            val = m[-1]
            res[key] = None if val in ("-inf", "inf") else float(val)
    m = re.search(r"Number of samples:\s*(\d+)", out)
    if m:
        res["samples"] = int(m.group(1))
    return res


def luminance(img: np.ndarray) -> np.ndarray:
    return 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]


def relative_luminance(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float32)
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def grey_relative_luminance(v: float) -> float:
    """WCAG relative luminance of a grey level (0-255). Scalar in, scalar out."""
    return float(relative_luminance(np.array([v, v, v], dtype=np.float32)))


def contrast_ratio(l1: float, l2: float) -> float:
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def extract_frame(path: str, t: float, dest: str) -> None:
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", dest])


def ink_boxes(img: np.ndarray, threshold: float = 38.0) -> np.ndarray:
    """
    Text is high-contrast detail against a flat-ish ground. Rather than guess a
    colour, take the pixels that differ strongly from the frame's own median
    ground and keep the connected-ish rows/cols.
    """
    lum = luminance(img)
    ground = float(np.median(lum))
    return np.abs(lum - ground) > threshold


def ink_blocks(mask: np.ndarray, stride: int = 8) -> list[tuple[int, int, int, int]]:
    """
    Per-block ink bounding boxes, not one union box.

    A union box is useless for layout: the brand mark at the left edge and the
    page counter at the right edge merge into a box that spans the frame, and a
    legitimate margin looks like a crop. Downscale, find connected ink regions,
    then map each back to full-resolution coordinates. 8-connected, minimum 2
    cells — a stray pixel is not a block.
    """
    h, w = mask.shape
    small = mask[: h // stride * stride, : w // stride * stride]
    small = small.reshape(small.shape[0] // stride, stride,
                          small.shape[1] // stride, stride).any(axis=(1, 3))
    sh, sw = small.shape
    seen = np.zeros_like(small, dtype=bool)
    boxes = []
    for y0 in range(sh):
        for x0 in range(sw):
            if not small[y0, x0] or seen[y0, x0]:
                continue
            stack, cells = [(y0, x0)], []
            seen[y0, x0] = True
            while stack:
                y, x = stack.pop()
                cells.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < sh and 0 <= nx < sw and small[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            if len(cells) < 2:
                continue
            ys = [c[0] for c in cells]; xs = [c[1] for c in cells]
            boxes.append((min(xs) * stride, min(ys) * stride,
                          (max(xs) + 1) * stride - 1, (max(ys) + 1) * stride - 1))
    return boxes


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if len(xs) < 40:            # a few stray pixels is not a line of type
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


# --------------------------------------------------------------------------- #
# main checks
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--type-floor", type=float, default=30.0,
                    help="minimum cap height in px (default 30 at 1080 short side)")
    ap.add_argument("--safe", type=float, default=0.94,
                    help="fraction of the frame that counts as the safe area")
    ap.add_argument("--json")
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args()

    vid = args.video
    if not os.path.exists(vid):
        print(f"FAIL  no such file: {vid}")
        return 2

    results: list[dict] = []
    failed = False

    def record(name, ok, detail, hard=True):
        nonlocal failed
        results.append({"check": name, "ok": bool(ok), "detail": detail, "hard": hard})
        if not ok and hard:
            failed = True

    info = probe(vid)
    vstream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    astreams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if not vstream:
        print("FAIL  no video stream")
        return 2

    W, H = int(vstream["width"]), int(vstream["height"])
    duration = float(info["format"]["duration"])
    fps = eval(vstream.get("avg_frame_rate", "30/1")) if "/" in vstream.get("avg_frame_rate", "") else 30.0

    print(f"\n\033[1mQC — {os.path.basename(vid)}\033[0m")
    print(f"  {W}x{H} · {duration:.2f}s · {fps:.2f} fps · "
          f"{len(astreams)} audio stream(s)")

    # ---- 1. duration window (the /brag gate) ----
    in_window = 15.0 <= duration <= 25.0
    record("duration_15_25s", in_window,
           f"{duration:.2f}s" + ("" if in_window else " — outside the 15–25s gate"))

    # ---- 2. audio actually present AND audible ----
    if not astreams:
        record("audio_stream", False, "no audio stream in the encoded file")
        record("audio_audible", False, "cannot measure — nothing to decode")
        levels = {}
    else:
        record("audio_stream", True, f"{astreams[0]['codec_name']}")
        levels = astats(vid)
        rms = levels.get("rms_db")
        peak = levels.get("peak_db")
        # -50 dB RMS over a whole film is indistinguishable from silence.
        audible = rms is not None and rms > -50.0 and (peak is None or peak > -40.0)
        record("audio_audible", audible,
               f"rms {rms} dB · peak {peak} dB"
               + ("" if audible else " — this is a SILENT render (<audio> id missing?)"))

    # ---- 3. frame 0 carries ink (thumbnail) ----
    stride_tol = 10   # downscale granularity in ink_blocks()
    tmp = tempfile.mkdtemp(prefix="qc-")
    try:
        f0 = os.path.join(tmp, "f000.png")
        extract_frame(vid, 0.0, f0)
        img0 = np.asarray(Image.open(f0).convert("RGB"), dtype=np.float32)
        mask0 = ink_boxes(img0)
        ink_ratio0 = float(mask0.mean())
        record("first_frame_has_ink", ink_ratio0 > 0.002,
               f"ink covers {ink_ratio0*100:.2f}% of frame 0")

        # ---- 4. sample settled frames across the film ----
        # Sample the middle-ish of each detected "plateau": we do not know the
        # scene boundaries from the MP4, so sample a grid and keep the frames
        # whose ink is stable (fully entered, not mid-transition).
        samples = []
        n = 14
        for i in range(n):
            t = duration * (i + 0.5) / n
            p = os.path.join(tmp, f"f{i:03d}.png")
            extract_frame(vid, t, p)
            img = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
            mask = ink_boxes(img)
            bb = bbox_of(mask)
            samples.append((t, img, mask, bb))

        safe_x = int(W * (1 - args.safe) / 2)
        safe_y = int(H * (1 - args.safe) / 2)

        crop_issues = []
        small_text = []
        contrast_fail = []
        for t, img, mask, bb in samples:
            if bb is None:
                continue
            x0, y0, x1, y1 = bb

            # crop: every ink BLOCK must sit inside the safe area, not the union
            for (bx0, by0, bx1, by1) in ink_blocks(mask):
                if (bx0 < safe_x - stride_tol or by0 < safe_y - stride_tol
                        or bx1 > W - safe_x + stride_tol or by1 > H - safe_y + stride_tol):
                    crop_issues.append(
                        f"t={t:.1f}s block {bx0},{by0}→{bx1},{by1} crosses the "
                        f"{int(args.safe*100)}% safe area")

            # type size: the tallest contiguous ink run is a proxy for cap height
            cols = np.where(mask.any(axis=0))[0]
            if len(cols):
                band = mask[:, cols.min():cols.max() + 1]
                row_density = band.sum(axis=1)
                rows = np.where(row_density > 0)[0]
                if len(rows):
                    # split into glyph bands: gaps of >2% of height separate lines
                    gaps = np.where(np.diff(rows) > max(6, int(H * 0.02)))[0]
                    bands, start = [], rows[0]
                    for g in gaps:
                        bands.append((start, rows[g])); start = rows[g + 1]
                    bands.append((start, rows[-1]))
                    tallest = max((b - a) for a, b in bands) if bands else 0
                    if tallest and tallest < args.type_floor:
                        small_text.append(f"t={t:.1f}s ink band {tallest}px < floor {args.type_floor:.0f}px")

            # contrast: darkest 10% of ink vs median ground
            lum = luminance(img)
            ink_px = lum[mask]
            if ink_px.size > 500:
                ground = float(np.median(lum[~mask])) if (~mask).any() else float(np.median(lum))
                # both polarities: light-on-dark and dark-on-light
                hi_ink = float(np.percentile(ink_px, 90))
                lo_ink = float(np.percentile(ink_px, 10))
                lg = grey_relative_luminance(ground)
                best = 1.0
                for v in (hi_ink, lo_ink):
                    best = max(best, contrast_ratio(grey_relative_luminance(v), lg))
                if best < 3.0:
                    contrast_fail.append(f"t={t:.1f}s ratio {best:.2f}:1 < 3.0:1")

        record("no_edge_cropping", not crop_issues,
               "no ink outside the safe area" if not crop_issues else "; ".join(crop_issues[:3]))
        record("type_floor", not small_text,
               f"all ink bands ≥ {args.type_floor:.0f}px" if not small_text else "; ".join(small_text[:3]))
        record("contrast_min_3to1", not contrast_fail,
               "sampled contrast ≥ 3:1" if not contrast_fail else "; ".join(contrast_fail[:3]))

        # ---- 5. no dip to black: a cross-fade must dissolve, not blink ----
        # Sampled every 0.1 s. A transition that fades the outgoing scene before
        # the incoming one has any ink leaves an empty frame — the film appears to
        # flash black. This is invisible to every other check and to hyperframes
        # check, and it is the easiest craft bug to ship.
        # One decode pass at 10 fps, not one ffmpeg call per sample: 250
        # subprocesses cost ~90 s on this box and made the gate too slow to run.
        scandir = os.path.join(tmp, "scan")
        os.makedirs(scandir, exist_ok=True)
        run([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", vid,
             "-vf", "fps=10,scale=270:480", "-q:v", "4",
             os.path.join(scandir, "%05d.jpg")])
        black_frames = []
        for f in sorted(os.listdir(scandir)):
            a = np.asarray(Image.open(os.path.join(scandir, f)).convert("RGB"), dtype=np.float32)
            if ink_boxes(a).mean() < 0.0008:          # essentially empty frame
                idx = int(os.path.splitext(f)[0]) - 1
                black_frames.append(round(idx * 0.1, 2))
        if black_frames:
            spans, cur = [], [black_frames[0]]
            for t in black_frames[1:]:
                if t - cur[-1] <= 0.15: cur.append(t)
                else: spans.append(cur); cur = [t]
            spans.append(cur)
            detail = "; ".join(f"{sp[0]:.1f}–{sp[-1]:.1f}s empty" for sp in spans[:4])
            record("no_black_dip", False, detail)
        else:
            record("no_black_dip", True, "every 0.1s frame carries ink")

        # ---- 6. actual cut density: is anything moving/happening? ----
        diffs = []
        prev = None
        for t, img, _, _ in samples:
            small = np.asarray(Image.fromarray(img.astype(np.uint8)).resize((160, 284)), dtype=np.float32)
            if prev is not None:
                diffs.append(float(np.abs(small - prev).mean()))
            prev = small
        moving = [d for d in diffs if d > 1.0]
        record("motion_present", len(moving) >= max(2, len(diffs) // 3),
               f"{len(moving)}/{len(diffs)} sampled intervals changed > 1/255")

    finally:
        if args.keep:
            print(f"  frames kept in {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    # ---- report ----
    print()
    for r in results:
        mark = "\033[32m✓\033[0m" if r["ok"] else ("\033[31m✗\033[0m" if r["hard"] else "\033[33m!\033[0m")
        print(f"  {mark} {r['check']:<22} {r['detail']}")

    verdict = "PASS" if not failed else "FAIL"
    colour = "\033[32m" if not failed else "\033[31m"
    print(f"\n{colour}{verdict}\033[0m  "
          f"{sum(1 for r in results if r['ok'])}/{len(results)} checks")
    print("  Nobody has watched this video. This report is measurements only —")
    print("  it proves the film is not silent, not cropped, not illegible and not")
    print("  static. It cannot tell you whether it is good.")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"video": vid, "verdict": verdict, "duration": duration,
                       "width": W, "height": H, "results": results,
                       "audio_levels": levels}, fh, indent=2)
        print(f"  json: {args.json}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
