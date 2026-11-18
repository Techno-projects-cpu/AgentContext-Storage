#!/usr/bin/env python3
"""Write the film's music bed: a warm marimba-and-pad tune in C, 108 bpm, generated from scratch.

Nothing is sampled and nothing is downloaded, so the score can be rebuilt anywhere: the melody is a
list of (beat, midi note, length) phrases, the harmony a four-chord loop, and every voice is a few
sines and an envelope. The arrangement follows the story:

  bars 0-7    intro: pad and a slow marimba arpeggio, nothing else
  bars 8-23   the story: the full tune, bass and shaker in
  bars 24-39  the puzzle: the tune thins out to arpeggios, then climbs as the water rises
  bars 40-45  the moral: a held cadence, then a soft final chord under the end card

  python3 tools/make_score.py --seconds 115.2 --out audio/score.wav
"""
import argparse
import math
import pathlib
import wave

import numpy as np

SR = 48000
BPM = 108.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT

MIDI = lambda n: 440.0 * 2 ** ((n - 69) / 12)          # noqa: E731

CHORDS = {                                              # bar -> chord tones (midi, low to high)
    "C": [48, 55, 60, 64, 67],
    "G": [43, 50, 55, 59, 62],
    "Am": [45, 52, 57, 60, 64],
    "F": [41, 48, 53, 57, 60],
}
PROGRESSION = ["C", "G", "Am", "F", "C", "G", "F", "C"]

# the tune: (beat in the 8-bar phrase, midi, beats long)
MELODY = [
    (0.0, 72, 1.0), (1.0, 76, 0.5), (1.5, 79, 0.5), (2.0, 76, 1.5), (4.0, 74, 1.0), (5.0, 71, 1.0), (6.0, 67, 2.0),
    (8.0, 76, 1.0), (9.0, 79, 0.5), (9.5, 81, 0.5), (10.0, 79, 1.5), (12.0, 76, 1.0), (13.0, 74, 1.0), (14.0, 72, 2.0),
    (16.0, 72, 1.0), (17.0, 74, 0.5), (17.5, 76, 0.5), (18.0, 79, 2.0), (20.0, 76, 1.0), (21.0, 74, 1.0), (22.0, 71, 2.0),
    (24.0, 74, 1.0), (25.0, 76, 0.5), (25.5, 77, 0.5), (26.0, 79, 1.0), (27.0, 77, 1.0), (28.0, 72, 4.0),
]


def env(n, attack, decay, sustain=0.0, release=None):
    t = np.arange(n) / SR
    a = np.clip(t / max(1e-4, attack), 0, 1)
    d = np.exp(-np.clip(t - attack, 0, None) / max(1e-4, decay))
    e = a * (sustain + (1 - sustain) * d)
    if release:
        r = np.clip((t[-1] - t) / release, 0, 1)
        e = e * r
    return e


def marimba(freq, dur, amp=1.0, bright=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, (mult, g, tau) in enumerate(((1.0, 1.0, 0.55), (2.0, 0.32 * bright, 0.30), (4.04, 0.12 * bright, 0.14),
                                        (6.1, 0.05 * bright, 0.08))):
        out += g * np.sin(2 * math.pi * freq * mult * t) * np.exp(-t / tau)
    out *= np.clip(t / 0.004, 0, 1)
    out *= np.clip((dur - t) / 0.05, 0, 1)
    return out * amp * 0.28


def pad(freqs, dur, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.0018, 0.0, 0.0021):
            out += np.sin(2 * math.pi * f * (1 + det) * t + det * 900)
    out /= max(1, len(freqs) * 3)
    e = np.clip(t / 0.55, 0, 1) * np.clip((dur - t) / 0.9, 0, 1)
    trem = 1.0 + 0.05 * np.sin(2 * math.pi * 0.35 * t)
    return out * e * trem * amp * 0.22


def bass(freq, dur, amp=1.0):
    n = int(SR * dur)
    t = np.arange(n) / SR
    out = np.sin(2 * math.pi * freq * t) + 0.22 * np.sin(2 * math.pi * freq * 2 * t)
    e = np.clip(t / 0.02, 0, 1) * np.exp(-np.clip(t - 0.02, 0, None) / 0.55) * np.clip((dur - t) / 0.1, 0, 1)
    return out * e * amp * 0.30


def shaker(dur=0.11, amp=1.0, seed=0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    x = rng.standard_normal(n)
    # crude high band: first difference of the noise, then a short decay
    x = np.diff(x, prepend=0.0) * 0.5
    t = np.arange(n) / SR
    return x * np.exp(-t / 0.028) * amp * 0.05


def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0:
        x = x[-i:]
        i = 0
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * gain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--atempo", type=float, default=1.0, help="stretch the score to fit a longer film")
    a = ap.parse_args()
    total = a.seconds
    buf = np.zeros(int(SR * (total + 1.0)))

    def T(beat):
        return beat * BEAT

    bars = int(math.ceil(total / BAR)) + 1
    for b in range(bars):
        chord = CHORDS[PROGRESSION[b % len(PROGRESSION)]]
        bar_t = T(4 * b)
        if bar_t > total + BAR:
            break
        # section markers
        quiet = b < 8 or 24 <= b < 34
        moral = b >= 40
        # pad holds the chord for the bar
        add(buf, pad([MIDI(n) for n in chord[1:]], BAR * 1.05, amp=1.0 if not moral else 1.3), bar_t)
        # bass on 1 and 3
        if not quiet or b >= 4:
            add(buf, bass(MIDI(chord[0]), BEAT * 1.6, amp=0.9), bar_t, 1.0)
            add(buf, bass(MIDI(chord[0]), BEAT * 1.4, amp=0.7), bar_t + 2 * BEAT)
        # shaker on the off-eighths once the tune is going
        if not quiet and not moral:
            for k in range(8):
                g = 0.8 if k % 2 else 0.45
                add(buf, shaker(amp=g, seed=b * 8 + k), bar_t + k * BEAT / 2)
        # marimba arpeggio through the chord
        if quiet or moral or b % 2 == 1:
            pat = [1, 2, 3, 2, 1, 2, 3, 4]
            for k, idx in enumerate(pat):
                note = chord[min(idx, len(chord) - 1)] + (12 if b % 4 == 3 and k > 3 else 0)
                add(buf, marimba(MIDI(note), BEAT * 0.9, amp=0.55), bar_t + k * BEAT / 2)

    # the tune: eight-bar phrases, until the moral
    end_beat = (total - 4.0) / BEAT
    phrase = 0
    while True:
        start = T(4 * 8 + 32 * phrase)         # skip the intro (8 bars)
        if start > T(end_beat * 0.86) or phrase > 5:
            break
        octave = 12 if phrase in (2, 4) else 0
        for (beat, note, dur) in MELODY:
            at = start + T(beat)
            if at / BEAT > end_beat * 0.86:
                break
            add(buf, marimba(MIDI(note + octave), max(0.30, T(dur)), amp=1.0, bright=1.0), at)
            if phrase >= 2 or octave:
                add(buf, marimba(MIDI(note + octave + (4 if phrase % 2 else -5)), max(0.30, T(dur)),
                                 amp=0.45, bright=0.6), at + 0.012)
        phrase += 1

    # a closing cadence: G, then a long C, right under the end card
    cad = T(end_beat * 0.88)
    for k, note in enumerate((67, 71, 74, 79)):
        add(buf, marimba(MIDI(note), 0.7, amp=0.9), cad + k * BEAT * 0.5)
    add(buf, pad([MIDI(n) for n in CHORDS["C"][1:]] + [MIDI(72), MIDI(76)], 4.0, amp=1.5), cad + 2 * BEAT)

    buf = buf[:int(SR * total)]
    # gentle fade in and out, then a soft-knee limit so nothing clips under the voice
    n = len(buf)
    t = np.arange(n) / SR
    buf *= np.clip(t / 1.2, 0, 1) * np.clip((total - t) / 3.0, 0, 1)
    buf = np.tanh(buf * 1.15) * 0.72
    # a touch of air: wide the top end with a single-pole shelf (right channel delayed 9 ms)
    right = np.concatenate([np.zeros(int(0.009 * SR)), buf])[:n]
    stereo = np.stack([buf, 0.75 * buf + 0.25 * right], axis=1)
    peak = np.abs(stereo).max() or 1.0
    stereo = stereo / peak * 0.85
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())
    print(f"score: {out}  {n / SR:.1f}s")


if __name__ == "__main__":
    main()
