#!/usr/bin/env python3
"""The two ads' music bed: a restrained piano-and-pad cue, generated from scratch.

Same engine as the crow film's score (sines, envelopes, no samples), but an advert's harmonic plan:
a slow four-chord loop in A minor that resolves upward on the sign-off, a pulse under the middle,
and silence-shaped space for the voice. Everything is deterministic, so the cues rebuild anywhere.

  python3 tools/make_score.py --seconds 29.6 --out audio/score.wav --mood zerovast
  python3 tools/make_score.py --seconds 41.0 --out audio/score.wav --mood vignan
"""
import argparse
import math

import numpy as np

SR = 48000
BPM = 84.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT

MIDI = lambda n: 440.0 * 2 ** ((n - 69) / 12)          # noqa: E731

CH = {
    "Am": [45, 57, 60, 64, 69],
    "F": [41, 53, 57, 60, 65],
    "C": [48, 55, 60, 64, 67],
    "G": [43, 55, 59, 62, 67],
    "Dm": [50, 57, 62, 65, 69],
    "E": [40, 52, 56, 59, 64],
}
MOODS = {
    # confident, dry, a little wry -> Am F C G, resolving on C
    "zerovast": dict(prog=["Am", "F", "C", "G", "Am", "F", "C", "C"],
                     arp=[69, 72, 76, 72, 69, 65, 64, 60], lead=0.55, pulse=0.5),
    # warm, curious, hopeful -> Am F C G then Dm E Am, resolving on Am
    "vignan": dict(prog=["Am", "F", "C", "G", "Dm", "E", "Am", "Am"],
                   arp=[64, 69, 72, 76, 72, 69, 65, 62], lead=0.42, pulse=0.36),
}


def env(t, attack, decay, sustain=0.0):
    a = np.clip(t / max(1e-4, attack), 0, 1)
    d = np.exp(-np.clip(t - attack, 0, None) / max(1e-4, decay))
    return a * (sustain + (1 - sustain) * d)


def piano(freq, dur, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for mult, g, tau in ((1.0, 1.0, 1.15), (2.0, 0.34, 0.62), (3.0, 0.13, 0.34), (4.02, 0.05, 0.2)):
        out += g * np.sin(2 * math.pi * freq * mult * t) * np.exp(-t / tau)
    out *= np.clip(t / 0.006, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    return out * amp * 0.26


def pad(freqs, dur, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.0016, 0.0, 0.0019):
            out += np.sin(2 * math.pi * f * (1 + det) * t + det * 700)
    out /= max(1, len(freqs) * 3)
    e = np.clip(t / 0.7, 0, 1) * np.clip((dur - t) / 1.0, 0, 1)
    return out * e * (1 + 0.04 * np.sin(2 * math.pi * 0.28 * t)) * amp * 0.20


def sub(freq, dur, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.sin(2 * math.pi * freq * t) + 0.18 * np.sin(2 * math.pi * freq * 2 * t)
    return out * env(t, 0.02, 0.7) * np.clip((dur - t) / 0.12, 0, 1) * amp * 0.26


def tick(dur=0.07, amp=1.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = np.diff(rng.standard_normal(n), prepend=0.0) * 0.5
    t = np.arange(n) / SR
    return x * np.exp(-t / 0.018) * amp * 0.035


def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * gain


def build(seconds, mood):
    m = MOODS[mood]
    buf = np.zeros(int(SR * (seconds + 1.2)))
    bars = int(math.ceil(seconds / BAR)) + 1
    for b in range(bars):
        chord = CH[m["prog"][b % len(m["prog"])]]
        t0 = b * BAR
        if t0 > seconds:
            break
        # the last bar of the film thins to a held chord, so the sign-off has air around it
        last = t0 + BAR >= seconds - 1.0
        add(buf, pad([MIDI(n) for n in chord[1:]], BAR * (1.6 if last else 1.02), amp=1.15 if last else 1.0), t0)
        if not last:
            add(buf, sub(MIDI(chord[0]), BEAT * 1.5), t0)
            add(buf, sub(MIDI(chord[0]), BEAT * 1.2, 0.7), t0 + 2 * BEAT)
        # the arpeggio carries the cue: an eighth-note figure that climbs through the bar
        arp = m["arp"]
        for k in range(6 if not last else 2):
            note = arp[(b * 3 + k) % len(arp)]
            add(buf, piano(MIDI(note), 1.4, amp=(0.9 - 0.07 * k) * m["lead"]), t0 + k * BEAT * 0.66)
        # a pulse in the middle section only, and never under the last bar
        if not last and 2 <= b < bars - 2:
            for k in range(4):
                add(buf, tick(amp=m["pulse"], seed=b * 7 + k), t0 + k * BEAT)
    buf *= 0.9 / max(1e-6, np.abs(buf).max())
    return buf[: int(SR * seconds)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mood", choices=sorted(MOODS), default="zerovast")
    a = ap.parse_args()
    x = build(a.seconds, a.mood)
    import wave
    with wave.open(a.out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    print(f"{a.out}  {len(x) / SR:.2f}s  mood={a.mood}")


if __name__ == "__main__":
    main()
