#!/usr/bin/env python3
"""Draw a spectrogram contact sheet of every narration take, one row per line, so a human (or a
model looking at the image) can tell real speech from the busy-loop the speech service returns.

Real speech: formants that move, gaps between phrases, a shape that never repeats.
A loop: the same syllable column repeating at a fixed period for the whole clip.

  python3 tools/audit_takes.py --project . --out /tmp/thumbs/audit.png [--dir audio/takes]
"""
import argparse
import pathlib
import subprocess

import numpy as np
from PIL import Image, ImageDraw


def spec(path, seconds=12.0, sr=16000, n=512, hop=256):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", str(seconds), "-i", str(path),
                    "-f", "s16le", "-ac", "1", "-ar", str(sr), "/tmp/_au.raw"], check=True)
    a = np.fromfile("/tmp/_au.raw", dtype=np.int16).astype(np.float32) / 32768
    if len(a) < n:
        return None
    F = np.lib.stride_tricks.sliding_window_view(a, n)[::hop] * np.hanning(n)
    S = 20 * np.log10(np.abs(np.fft.rfft(F, axis=1))[:, :220] + 1e-6)
    S = np.clip((S + 55) / 55, 0, 1)
    return (S.T[::-1] * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dir", default="audio/takes")
    ap.add_argument("--seconds", type=float, default=12.0)
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    files = sorted((proj / a.dir).glob("seg*.mp3"))
    rows = []
    for p in files:
        img = spec(p, a.seconds)
        if img is None:
            continue
        rows.append((p.name, img, p))
    W, H, LAB = 900, 150, 120
    sheet = Image.new("L", (W + LAB, (H + 6) * len(rows)), 30)
    d = ImageDraw.Draw(sheet)
    for i, (name, img, p) in enumerate(rows):
        y = i * (H + 6)
        sheet.paste(Image.fromarray(img).resize((W, H)), (LAB, y))
        d.text((4, y + H // 2), name[:14], fill=210)
    sheet.save(a.out)
    print(f"{a.out}  {len(rows)} rows")


if __name__ == "__main__":
    main()
