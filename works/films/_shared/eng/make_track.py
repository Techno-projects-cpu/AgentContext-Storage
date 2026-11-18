#!/usr/bin/env python3
"""A percussive, music-led bed for the no-voiceover ads.

Without a narrator the track has to carry the film: the silence between hits is the grammar, and the
hits land ON the cuts. So instead of a chord loop this builds a real bar of drums (kick, clap, hats),
a sub under it, and one tuned motif, then drives the arrangement from an energy curve measured in
bars, with explicit accents at the exact times the picture cuts.

Everything is synthesised here (no samples), so the cue rebuilds anywhere.

  python3 make_track.py --seconds 24 --bpm 96 --out audio/score.wav \
      --energy "0:0.25,4:0.55,8:0.8,12:1.0,16:0.7,20:0.45,23:0.9" \
      --hits "2.5,6.2,9.8,13.4,17.0,21.2"
"""
import argparse
import math
import wave

import numpy as np

SR = 48000


def _t(d):
    return np.arange(int(SR * d)) / SR


def kick(dur=0.42, amp=1.0, f0=118.0, f1=44.0, punch=1.6):
    t = _t(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    body = np.sin(2 * math.pi * np.cumsum(f) / SR)
    click = np.exp(-t * 320) * 0.5
    return (body * np.exp(-t * punch) + click) * amp


def clap(dur=0.30, amp=1.0, seed=1, bright=1.0):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    n = rng.standard_normal(len(t))
    n = np.diff(n, prepend=0.0)                      # crude high band
    env = np.exp(-t * 26) * (1 + 0.6 * np.exp(-((t - 0.012) * 120) ** 2))
    return n * env * amp * 0.22 * bright


def hat(dur=0.09, amp=1.0, seed=2, open_=False):
    rng = np.random.default_rng(seed)
    t = _t(dur)
    n = np.diff(rng.standard_normal(len(t)), prepend=0.0)
    return n * np.exp(-t * (16 if open_ else 70)) * amp * 0.10


def sub(freq=48.0, dur=0.6, amp=1.0):
    t = _t(dur)
    x = np.sin(2 * math.pi * freq * t) + 0.16 * np.sin(2 * math.pi * freq * 2 * t)
    return x * np.clip(t / 0.01, 0, 1) * np.exp(-t * 2.2) * np.clip((dur - t) / 0.1, 0, 1) * amp * 0.30


def marimba(freq, dur=0.9, amp=1.0):
    t = _t(dur)
    out = np.zeros(len(t))
    for mult, g, tau in ((1.0, 1.0, 0.46), (2.0, 0.30, 0.26), (4.04, 0.10, 0.13)):
        out += g * np.sin(2 * math.pi * freq * mult * t) * np.exp(-t / tau)
    return out * np.clip(t / 0.004, 0, 1) * np.clip((dur - t) / 0.06, 0, 1) * amp * 0.22


def metal(dur=1.2, amp=1.0, seed=3):
    """an accent: a short bright noise-and-tone swell for a cut that matters"""
    rng = np.random.default_rng(seed)
    t = _t(dur)
    n = np.diff(rng.standard_normal(len(t)), prepend=0.0)
    tone = 0.5 * np.sin(2 * math.pi * 1180 * t) + 0.3 * np.sin(2 * math.pi * 1760 * t)
    env = np.exp(-t * 6.5) * np.clip(t / 0.004, 0, 1)
    return (n * 0.5 + tone) * env * amp * 0.20


def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * gain


def energy_at(keys, t):
    ks = sorted(keys)
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t0 <= t <= t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            u = u * u * (3 - 2 * u)
            return v0 + (v1 - v0) * u
    return ks[-1][1]


def parse_keys(s):
    out = []
    for part in s.split(","):
        if not part.strip():
            continue
        k, v = part.split(":")
        out.append((float(k), float(v)))
    return out


def build(seconds, bpm, energy, hits, swing=0.0, base_note=57):
    beat = 60.0 / bpm
    step = beat / 4.0                                   # sixteenths
    buf = np.zeros(int(SR * (seconds + 1.0)))
    n_steps = int(seconds / step) + 1
    # a minor pentatonic motif, played on the marimba, moved by the energy curve
    scale = [0, 3, 5, 7, 10, 12]
    for k in range(n_steps):
        t = k * step + (swing * step if k % 4 == 2 else 0.0)
        e = energy_at(energy, t)
        in_bar = k % 16
        bar = k // 16
        # kick: four on the floor at full energy, sparse when low
        if in_bar in (0, 8) or (e > 0.72 and in_bar in (6, 14)) or (e > 0.9 and in_bar == 11):
            add(buf, kick(amp=0.75 + 0.25 * e), t, 1.0)
        # clap on 2 and 4 once the track is moving
        if e > 0.42 and in_bar in (4, 12):
            add(buf, clap(seed=k, amp=0.55 + 0.35 * e), t, 1.0)
        # hats: eighth notes, opening up with energy
        if k % 2 == 0:
            add(buf, hat(seed=k, amp=0.30 + 0.55 * e, open_=(in_bar == 14 and e > 0.6)), t)
        # sub follows the kick, one octave down from the motif root
        if in_bar in (0, 6, 8, 14) and e > 0.3:
            add(buf, sub(freq=48.0 * 2 ** ((base_note - 45) / 12), amp=0.7 * e), t)
        # the motif: steps that make a phrase, thinning out at low energy
        if e > 0.30 and (in_bar % 4 == 0 or (e > 0.8 and in_bar % 2 == 0)):
            deg = scale[(bar * 2 + k // 8) % len(scale)]
            add(buf, marimba(440.0 * 2 ** ((base_note + deg - 69) / 12), amp=0.55 * e), t)
    for n, t in enumerate(hits):
        add(buf, metal(amp=1.0, seed=n), t, 1.0)
        add(buf, kick(amp=0.9), t, 1.0)
    peak = np.abs(buf).max() or 1.0
    buf *= 0.92 / peak
    return buf[: int(SR * seconds)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--bpm", type=float, default=96.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--energy", default="0:0.3,4:0.6,8:0.85,12:1.0,16:0.6")
    ap.add_argument("--hits", default="")
    ap.add_argument("--swing", type=float, default=0.0)
    ap.add_argument("--note", type=int, default=57)
    a = ap.parse_args()
    hits = [float(x) for x in a.hits.split(",") if x.strip()]
    x = build(a.seconds, a.bpm, parse_keys(a.energy), hits, a.swing, a.note)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"{a.out}  {len(x) / SR:.2f}s  bpm={a.bpm}  hits={len(hits)}")


if __name__ == "__main__":
    main()
