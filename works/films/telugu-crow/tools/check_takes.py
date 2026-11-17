#!/usr/bin/env python3
"""Score staging takes in audio/takes and promote the good ones to audio/lines.

The speech service sometimes returns a busy-loop instead of speech (50 s of the same syllable). A
real line ends in silence, is not periodic, and is roughly as long as its text. Anything that fails
stays behind in audio/takes so it can be asked for again with a fresh file path.

  python3 tools/check_takes.py --project . [--promote]
"""
import argparse
import json
import pathlib
import subprocess

import numpy as np


def envelope(path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000",
                    "/tmp/_ck.raw"], check=True)
    a = np.fromfile("/tmp/_ck.raw", dtype=np.int16).astype(np.float32) / 32768
    if len(a) == 0:
        return np.zeros(10, np.float32), 0.0
    w = 160
    n = len(a) // w
    return np.sqrt((a[:n * w].reshape(n, w) ** 2).mean(axis=1)), len(a) / 16000


def periodicity(env):
    e = env - env.mean()
    den = float((e * e).sum()) or 1e-9
    best, lag_best = 0.0, 0
    for lag in range(20, min(200, max(21, len(e) // 2))):
        r = float((e[:-lag] * e[lag:]).sum()) / den * (len(e) / max(1, len(e) - lag))
        if r > best:
            best, lag_best = r, lag
    return best, lag_best / 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--min-gap-tail", type=float, default=0.004)
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    segs = {s["id"]: s for s in json.loads((proj / "audio" / "segments.json").read_text())["segments"]}
    takes = proj / "audio" / "takes"
    good = []
    for p in sorted(takes.glob("seg*.mp3")):
        sid = int(p.name[3:5])
        env, dur = envelope(p)
        r, lag = periodicity(env)
        n_chars = len(segs[sid]["vo"])
        expect = n_chars / 13.0
        looped = r > 0.62 and dur > 6.0
        wild = dur < 0.35 * expect or dur > 3.0 * expect + 4
        ok = not looped and not wild and dur > 0.8
        print(f"{p.name:14s} {dur:6.2f}s  expect~{expect:5.2f}s  periodicity {r:.2f}@{lag:.2f}s  "
              f"{'OK' if ok else ('LOOP' if looped else 'LENGTH')}")
        if ok:
            good.append((sid, p))
    if a.promote:
        for sid, p in good:
            dst = proj / "audio" / "lines" / f"seg{sid:02d}.mp3"
            dst.write_bytes(p.read_bytes())
            sid_silent = proj / "audio" / "lines" / f"seg{sid:02d}.silent"
            if sid_silent.exists():
                sid_silent.unlink()
            p.unlink()
        print(f"promoted {len(good)} takes")
    print("good:", [s for s, _ in good])


if __name__ == "__main__":
    main()
