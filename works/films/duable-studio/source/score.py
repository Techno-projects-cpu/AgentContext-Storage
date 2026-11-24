"""
score.py — the music, synthesised from first principles.

No samples, no libraries beyond numpy. Everything here is partials, envelopes
and an impulse response:

  * a felted piano-ish voice   six partials, each decaying at its own rate
  * a celesta / bell           inharmonic partials (1, 2, 3, 4.07, 5.43)
  * a warm pad                 additive harmonics through a one-pole lowpass
  * a soft sub                 sine plus a whisper of 2nd harmonic
  * a "room"                   convolution with a synthetic stereo impulse

The structure follows the picture: the harmony changes at the hard cuts, so the
score turns where the film turns rather than running over it.

    A minor — a calm, unhurried palette. Nothing modal or heroic: this is a
    studio that says "a service for that", so the music agrees rather than
    argues.

Sections (film cuts at 3.2 / 7.6 / 11.2 / 15.6, total 19.6 s):

    0.0  Am9      sparse: one arpeggio, wide room, nothing to prove
    3.2  Fmaj7 → G6   the pulse arrives, still soft
    7.6  Dm7 → Em7    the lift: bells enter over the turning object
    11.2 Cmaj7 → Am7 → Fmaj7   the fullest bar of the film
    15.6 G → Am9      resolve, ring out, one last bell

Run:  python3 score.py --out score.wav --dur 19.6
"""
import argparse
import wave

import numpy as np

SR = 48000


def midi(n):
    """MIDI note number -> Hz."""
    return 440.0 * 2.0 ** ((n - 69) / 12.0)


# --------------------------------------------------------------- instruments
def piano(f, dur, amp=1.0, decay=1.0, bright=1.0):
    """Felted piano-ish. Partials are inharmonic-ish and decay at their own rate.

    The trick that makes it read as a *felted* piano rather than a synth pluck
    is that high partials die fast (so the attack is soft and woody) and the
    whole note is rolled off, never a hard transient.
    """
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    out = np.zeros(n)
    # (ratio, amplitude, extra decay)
    partials = ((1.00, 1.00, 0.0), (2.00, 0.36, 0.8), (3.01, 0.17, 1.6),
                (4.02, 0.08, 2.6), (5.05, 0.035, 3.8), (6.10, 0.015, 5.2))
    for ratio, a, extra in partials:
        out += a * np.sin(2 * np.pi * f * ratio * t) * np.exp(-(1.15 + extra) * decay * t)
    # a second voice a few cents away: cheap chorus, reads as a real instrument
    out += 0.22 * np.sin(2 * np.pi * f * 1.0016 * t) * np.exp(-1.6 * decay * t)
    attack = 1.0 - np.exp(-t * 220.0)          # ~5 ms, soft not clicky
    out *= attack * bright
    # gentle body: a tiny bit of 1.5f adds weight without mud
    out += 0.08 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-2.4 * decay * t)
    return out * amp


def bell(f, dur, amp=1.0):
    """Celesta/bell: inharmonic partials, bright, gone in a second."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for ratio, a, d in ((1.0, 1.0, 1.6), (2.76, 0.42, 2.6), (5.40, 0.18, 4.0),
                        (8.93, 0.07, 6.0)):
        out += a * np.sin(2 * np.pi * f * ratio * t) * np.exp(-d * t)
    out *= 1.0 - np.exp(-t * 600.0)
    return out * amp


def pad(f, dur, amp=1.0, attack=0.9, release=1.1):
    """Warm pad: additive saw, then a one-pole lowpass, then a slow envelope."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 9):
        out += (1.0 / k) * np.sin(2 * np.pi * f * k * t + 0.3 * k)
    # one-pole lowpass, cutoff falling from 3 kHz to 700 Hz
    a = np.exp(-2 * np.pi * np.linspace(3000.0, 700.0, n) / SR)
    y = np.zeros(n)
    prev = 0.0
    for i in range(n):                       # 1-D recursive filter
        prev = (1 - a[i]) * out[i] + a[i] * prev
        y[i] = prev
    env = np.minimum(1.0, t / max(attack, 1e-3))
    env *= np.minimum(1.0, np.maximum(0.0, (dur - t) / max(release, 1e-3)))
    return y * env * amp * 0.55


def sub(f, dur, amp=1.0):
    """Soft sub-bass; the 2nd harmonic is what makes it audible on a phone."""
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    env = (1.0 - np.exp(-t * 18.0)) * np.exp(-t * 0.9)
    env *= np.minimum(1.0, np.maximum(0.0, (dur - t) / 0.35))
    return (np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * 2 * f * t)) * env * amp


def bass(f, dur, amp=1.0):
    """The low end of the score: root + 2nd harmonic, lowpassed hard.

    A pad alone leaves the mix thin — measured, it put only ~5% of its energy
    below 160 Hz. This is what carries weight on a phone speaker.
    """
    n = max(1, int(dur * SR))
    t = np.arange(n) / SR
    out = (np.sin(2 * np.pi * f * t)
           + 0.30 * np.sin(2 * np.pi * 2 * f * t)
           + 0.10 * np.sin(2 * np.pi * 3 * f * t))
    a = np.exp(-2 * np.pi * 420.0 / SR)          # one-pole lowpass at 420 Hz
    y = np.zeros(n); prev = 0.0
    for i in range(n):
        prev = (1 - a) * out[i] + a * prev
        y[i] = prev
    env = np.minimum(1.0, t / 0.045)                     # soft, never a click
    env *= np.minimum(1.0, np.maximum(0.0, (dur - t) / 0.22))
    return y * env * amp


def thump(dur=0.5, amp=1.0):
    """A soft felted kick: 95 Hz falling to 46 Hz. Barely there, felt in the chest."""
    n = max(1, int(dur * SR))
    f = 95.0 * np.exp(-np.arange(n) / SR * 16.0) + 46.0
    phase = np.cumsum(2 * np.pi * f / SR)
    return np.sin(phase) * np.exp(-np.arange(n) / SR * 9.0) * amp


def brush(dur=0.35, amp=0.05, seed=1):
    """Filtered noise tick for section changes — the only 'percussion' allowed."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.standard_normal(n)
    x = np.convolve(x, np.ones(24) / 24, "same")       # lowpass a little
    x = x - np.convolve(x, np.ones(240) / 240, "same")  # then remove the lows
    env = np.exp(-np.arange(n) / SR * 12.0) * (1.0 - np.exp(-np.arange(n) / SR * 900.0))
    return x * env * amp


# --------------------------------------------------------------------- reverb
def room(dry, wet=0.30, seconds=2.0, seed=7):
    """Convolution with a synthetic stereo impulse.

    The impulse is noise under an exponential decay with a slightly longer tail
    at low frequencies (a plate, not a room) — it gives the piano somewhere to
    sit without smearing the transients.
    """
    n_ir = int(seconds * SR)
    t = np.arange(n_ir) / SR
    out = np.zeros_like(dry)
    for ch, s in enumerate((seed, seed + 1)):
        rng = np.random.default_rng(s)
        ir = rng.standard_normal(n_ir) * np.exp(-t / (seconds * 0.34))
        ir = np.convolve(ir, np.ones(6) / 6, "same")       # soften the very top
        ir[:int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))  # pre-delay ramp
        ir /= np.sqrt(np.sum(ir ** 2))                     # energy-normalise
        nfft = 1 << int(np.ceil(np.log2(dry.shape[0] + n_ir)))
        w = np.fft.irfft(np.fft.rfft(dry[:, ch], nfft) * np.fft.rfft(ir, nfft), nfft)
        out[:, ch] += w[: dry.shape[0]]
    return dry * (1.0 - wet) + out * wet


# ------------------------------------------------------------------ the score
# The story in harmony. Seven sections on the seven cuts, so the music turns
# where the film turns. It opens unresolved (A minor, no third in the bass), turns
# warmer as the studio answers, and lands on the same chord it started on — the
# bookend, in music.
SECTIONS = [
    # (start, end, chord as MIDI, arpeggio step, pad weight, sub weight, bells)
    (0.0, 2.8, [57, 60, 64, 71], 0.44, 0.26, 0.10, False),    # Am9     — alone
    (2.8, 6.6, [53, 57, 60, 64], 0.26, 0.32, 0.34, False),    # Fmaj7   — an answer
    (6.6, 9.9, [55, 58, 62, 65], 0.26, 0.32, 0.36, False),    # G7      — the catalogue
    (9.9, 13.6, [52, 55, 59, 62], 0.24, 0.34, 0.40, True),    # Em7     — the lift
    (13.6, 17.2, [48, 52, 55, 59], 0.24, 0.36, 0.42, True),   # Cmaj7   — the answer
    (17.2, 20.8, [50, 53, 57, 60], 0.22, 0.36, 0.44, True),   # Dm7     — four ways
    (20.8, 24.8, [45, 52, 57, 64], 0.48, 0.40, 0.40, True),   # Am(add9) — home
]

# the motif: root, fifth, ninth, third — the same four intervals all the way
# through, transposed. It is the only melodic material in the film.
MOTIF = [0, 2, 3, 1]


def build(dur=24.8, tail=1.2):
    total = dur + tail
    n = int(total * SR)
    dry = np.zeros((n, 2))
    lead = np.zeros((n, 2))          # bells go through their own, wetter room

    def add(buf, sig, at, pan=0.0):
        s = int(at * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        seg = sig[: e - s]
        # constant-power pan
        l = np.sqrt((1.0 - pan) / 2.0) * np.sqrt(2)
        r = np.sqrt((1.0 + pan) / 2.0) * np.sqrt(2)
        buf[s:e, 0] += seg * l
        buf[s:e, 1] += seg * r

    for i, (t0, t1, chord, step, padw, subw, bells) in enumerate(SECTIONS):
        length = t1 - t0
        notes = [midi(x) for x in chord]

        # pad: the chord bed, always two voices an octave apart for body
        add(dry, pad(notes[0] / 2, length + 0.5, padw * 0.5, attack=0.8), t0, -0.12)
        add(dry, pad(notes[2] * 0.5, length + 0.4, padw * 0.35, attack=0.9), t0, 0.14)

        # the bass line: root an octave under the chord, held for the section
        add(dry, bass(notes[0] / 2, min(length + 0.25, 2.4), 0.15), t0, 0.0)
        # sub on the root, only where the harmony needs an anchor
        if subw:
            add(dry, sub(notes[0] / 4, min(length, 1.6), subw * 0.30), t0, 0.0)

        # the motif, as an arpeggio: it never repeats the same octave twice
        k = 0
        time = t0
        while time < t1 - 0.02:
            note = notes[MOTIF[k % len(MOTIF)]]
            oct_ = 12 * ((k // 4) % 2)          # alternate root and root+8ve
            vel = 0.34 if k % 2 == 0 else 0.25
            add(dry, piano(note * 2 ** ((12 + oct_) / 12.0), 1.9, vel, decay=0.9),
                time, pan=0.0)
            k += 1
            time += step

        # a melody note on the change: the top of the chord, held
        add(dry, piano(notes[-1] * 2, 2.6, 0.26, decay=0.55), t0 + 0.02, 0.05)

        # bells over the object and the resolve
        if bells:
            for j, m in enumerate(chord[1:]):
                add(lead, bell(midi(m) * 4, 1.8, 0.17), t0 + 0.05 + j * 0.19, 0.25 * (1 - j))

        # felt thumps: on the cut, and half-way through a long section
        add(dry, thump(0.55, 0.20), t0, 0.0)
        if length > 2.0:
            add(dry, thump(0.45, 0.12), t0 + length / 2, 0.0)
        add(dry, brush(0.5, 0.030, seed=10 + i), t0 + 0.01, 0.0)

    wet = room(dry, wet=0.30, seconds=2.0, seed=7)
    wetlead = room(lead, wet=0.55, seconds=2.6, seed=31)
    mix = wet + wetlead * 1.25

    # Fold towards mono. Measured side/mid was 0.65, which phase-cancels on a
    # phone speaker; 0.28 keeps the width as depth rather than as sides.
    mid = mix.mean(axis=1, keepdims=True)
    mix = mid * 0.86 + (mix - mid) * 0.34

    # final: fade in over 80 ms, fade the tail out, and normalise the music to
    # -20 dBFS RMS so a voiceover can sit on top of it without a fight
    fi = int(0.08 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(1.4 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.6
    mix = mix[: int(dur * SR)]

    rms = np.sqrt(np.mean(mix ** 2))
    target = 10 ** (-20.0 / 20)
    mix *= target / max(rms, 1e-9)
    peak = np.max(np.abs(mix))
    if peak > 0.89:                      # never clip a bed
        mix *= 0.89 / peak
    return mix


def write(path, stereo):
    pcm = np.clip(stereo, -1, 1)
    pcm = (pcm * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="score.wav")
    ap.add_argument("--dur", type=float, default=24.8)
    a = ap.parse_args()
    mix = build(a.dur)
    write(a.out, mix)
    rms = 20 * np.log10(np.sqrt(np.mean(mix ** 2)))
    peak = 20 * np.log10(np.max(np.abs(mix)))
    print(f"wrote {a.out}  {mix.shape[0]/SR:.2f}s  rms {rms:.1f} dB  peak {peak:.1f} dB")
    # a section-by-section view, so a dead patch or a clipping patch is visible
    for t0, t1, *_ in SECTIONS:
        seg = mix[int(t0 * SR):int(t1 * SR)]
        print(f"  {t0:5.1f}-{t1:5.1f}s  rms {20*np.log10(max(np.sqrt(np.mean(seg**2)),1e-9)):6.1f} dB"
              f"  peak {20*np.log10(max(np.max(np.abs(seg)),1e-9)):6.1f} dB")


if __name__ == "__main__":
    main()
