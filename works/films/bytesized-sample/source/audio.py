"""
audio.py — the sound for the film.

Two layers, both synthesized here because no TTS voice is available in this
sandbox and no licensed library exists in the repo:

  1. A speech-shaped placeholder on every narration line. It is NOT words — it is
     formant noise with the length and rhythm of the line, panned centre, at a
     speech-like level. Its job is to prove the audio path and to hold the pacing
     the real VO will drop into. The channel itself declares text-to-speech
     narration, so a synthetic voice is faithful to the format, not a cheat.
  2. A quiet bed: a low pulse per card, a tick on each chip, a soft rise into the
     recap. Deterministic, fixed seed, no samples.

    python3 audio.py --out assets/narration.wav
"""
import argparse
import math
import os
import struct
import wave

import numpy as np

SR = 48000


def _rng(seed):
    return np.random.default_rng(seed)


def syllable(n, seed=1):
    """A short speech-like burst: two formants over a breathy carrier."""
    r = _rng(seed)
    t = np.arange(n) / SR
    f0 = 118 + 16 * r.standard_normal()
    carrier = 0.55 * np.sin(2 * math.pi * f0 * t)
    carrier += 0.25 * np.sin(2 * math.pi * 2 * f0 * t)
    carrier += 0.18 * np.sin(2 * math.pi * 3 * f0 * t)
    # formant-ish colouring with a slowly moving centre
    sweep = 0.5 + 0.5 * np.sin(2 * math.pi * 3.1 * t + r.random() * 6)
    carrier *= 0.65 + 0.35 * sweep
    noise = r.standard_normal(n) * 0.06
    env = np.minimum(1, np.linspace(0, 3, n)) * np.minimum(1, np.linspace(3, 0, n))
    return (carrier + noise) * np.clip(env, 0, 1)


def speech_line(duration, words, seed):
    """Fill `duration` seconds with `words` syllable bursts and gaps."""
    n = int(duration * SR)
    out = np.zeros(n)
    if words <= 0:
        return out
    # leave a tail of silence, then distribute the bursts across the rest
    usable = n * 0.86
    slot = usable / words
    r = _rng(seed)
    for k in range(words):
        length = int(slot * r.uniform(0.5, 0.85))
        start = int(k * slot + slot * 0.08)
        if start + length > n:
            break
        out[start:start + length] += syllable(length, seed * 31 + k) * r.uniform(0.7, 1.0)
    return out


def bed(total, cards):
    """A low pulse under the picture; a soft tick where each card begins."""
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    # 52 Hz bed with a slow tremolo, very low level
    out += 0.035 * np.sin(2 * math.pi * 52 * t) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.23 * t))
    out += 0.022 * np.sin(2 * math.pi * 104 * t)
    # a tick on each card start
    for start in cards:
        i = int(start * SR)
        ln = int(0.045 * SR)
        if i + ln < n:
            tick = _rng(int(start * 100)).standard_normal(ln)
            decay = np.exp(-np.linspace(0, 9, ln))
            out[i:i + ln] += tick * decay * 0.05
    return out


def write_wav(path, data):
    peak = np.max(np.abs(data)) or 1.0
    data = data / peak * 0.89              # -1 dBFS ceiling
    pcm = (data * 32767).astype(np.int16)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build(out, timeline, copy_mod):
    total = timeline[-1][1]
    mix = np.zeros(int(total * SR) + SR)

    cards = []
    for start, end, kind, i in timeline:
        cards.append(start)
        if kind == "beat":
            beat = copy_mod.BEATS[i]
            text = beat["line"].replace("\n", " ") + " " + " ".join(beat["detail"])
            words = len(text.split())
            # narration starts a moment into the card, like the channel's cut
            offset = start + 0.55
            line = speech_line(end - offset - 0.25, words, seed=i + 7)
            s = int(offset * SR)
            mix[s:s + len(line)] += line * 0.22
        elif kind == "title":
            text = copy_mod.SUB
            line = speech_line(end - start - 1.0, len(text.split()), seed=99)
            s = int((start + 0.6) * SR)
            mix[s:s + len(line)] += line * 0.22
        elif kind == "table":
            words = 26
            line = speech_line(end - start - 1.2, words, seed=41)
            s = int((start + 0.6) * SR)
            mix[s:s + len(line)] += line * 0.20
        elif kind == "sign":
            words = len(copy_mod.SIGN.split())
            line = speech_line(end - start - 0.8, words, seed=53)
            s = int((start + 0.5) * SR)
            mix[s:s + len(line)] += line * 0.24

    mix[:len(bed(total, cards))] += bed(total, cards)
    write_wav(out, mix[:int(total * SR)])
    return out


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import copy as C
    import render as R

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/narration.wav")
    a = ap.parse_args()
    path = build(a.out, R.timeline(), C)
    print("wrote", path, f"{os.path.getsize(path)/1e6:.1f} MB")
