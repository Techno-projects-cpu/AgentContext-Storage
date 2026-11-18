#!/usr/bin/env python3
"""Find narration clips the speech service returned as loops instead of speech.

A few requests come back as 50 s of a repeated 0.5 s syllable pattern (same file size, flat energy,
no pauses). A real line ends, has silence gaps and its envelope is not periodic, so test the envelope
with an autocorrelation peak over lags of 0.2-2.0 s: a looped clip scores far above real speech.

  python3 tools/check_lines.py --project . [--fix]
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np


def envelope(path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000",
                    "/tmp/_ck.raw"], check=True)
    a = np.fromfile("/tmp/_ck.raw", dtype=np.int16).astype(np.float32) / 32768
    w = 160                                  # 10 ms frames
    n = len(a) // w
    return np.sqrt((a[:n * w].reshape(n, w) ** 2).mean(axis=1)), len(a) / 16000


def periodicity(env):
    e = env - env.mean()
    denom = float((e * e).sum()) or 1e-9
    best, lag_best = 0.0, 0
    for lag in range(20, min(200, len(e) // 2)):        # 0.2 s .. 2.0 s
        num = float((e[:-lag] * e[lag:]).sum())
        r = num / denom * (len(e) / max(1, len(e) - lag))
        if r > best:
            best, lag_best = r, lag
    quiet_tail = float(np.median(env[-150:])) / (float(np.median(env)) or 1e-9)
    return best, lag_best / 100.0, quiet_tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--fix", action="store_true", help="mark bad clips as needing a re-record")
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    segs = json.loads((proj / "audio" / "segments.json").read_text())["segments"]
    bad = []
    for s in segs:
        p = proj / "audio" / "lines" / f"seg{s['id']:02d}.mp3"
        if not p.exists():
            print(f"seg{s['id']:02d}  MISSING")
            bad.append(s["id"])
            continue
        env, dur = envelope(p)
        r, lag, tail = periodicity(env)
        looped = r > 0.62 and dur > 6.0
        flag = "LOOP" if looped else "ok"
        if looped:
            bad.append(s["id"])
        print(f"seg{s['id']:02d}  {dur:6.2f}s  periodicity {r:.2f} @ {lag:.2f}s  tail {tail:.2f}  {flag}")
        if looped and a.fix:
            dst = proj / "audio" / "lines" / f"seg{s['id']:02d}.bad.mp3"
            p.rename(dst)
            (proj / "audio" / "lines" / f"seg{s['id']:02d}.silent").touch()
    print("bad:", bad)


if __name__ == "__main__":
    main()
