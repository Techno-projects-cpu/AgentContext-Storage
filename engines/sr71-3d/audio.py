"""
audio.py — a deterministic sound bed for the film, synthesized from scratch.

The channel declares ElevenLabs library SFX. I have no licensed library here, so
this builds the same *job* (low bed, impact on every cut, a riser into the hot
beat, a bell on the green flash) out of oscillators and noise. Everything is a
fixed-seed function of sample index, so the mix reproduces exactly.

    python3 audio.py --dur 48.5 --out /tmp/bed.wav
"""
import argparse
import wave

import numpy as np

SR = 48000


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2):
    a_n, d_n, r_n = int(a * SR), int(d * SR), int(r * SR)
    s_n = max(0, n - a_n - d_n - r_n)
    return np.concatenate([
        np.linspace(0, 1, a_n, endpoint=False),
        np.linspace(1, s, d_n, endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, n - a_n - d_n - s_n),
    ])[:n]


def lowpass(x, k):
    """One-pole low-pass; k in 0..1 (1 = no filtering)."""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += (x[i] - acc) * k
        y[i] = acc
    return y


def lowpass_fast(x, k):
    """Vectorised one-pole approximation via cumulative exponential smoothing."""
    b = 1.0 - k
    out = np.empty_like(x)
    acc = 0.0
    # block-wise for speed: same filter, but numpy inner loops
    block = 2048
    for s in range(0, len(x), block):
        e = min(s + block, len(x))
        seg = x[s:e]
        # exact recurrence unrolled with a geometric series precomputed
        alpha = b ** np.arange(1, e - s + 1)
        cs = np.cumsum(seg * (b ** -np.arange(e - s)))
        out[s:e] = alpha * (acc + cs)
        acc = out[e - 1]
    return out


def tone(freq, n, shape="sine", detune=0.0):
    t = np.arange(n) / SR
    if shape == "sine":
        return np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * (freq * 2.003) * t)
    if shape == "saw":
        ph = (freq * t) % 1.0
        return 2 * ph - 1
    if shape == "bell":
        return (np.sin(2 * np.pi * freq * t) * 0.6
                + np.sin(2 * np.pi * freq * 2.76 * t) * 0.25
                + np.sin(2 * np.pi * freq * 5.4 * t) * 0.12)


def build(duration, cut_times, hot_start, green_at, seed=71):
    n = int(duration * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2), np.float64)

    def place(sig, at, gain=1.0, pan=0.0):
        s = int(max(0, at * SR))
        e = min(n, s + len(sig))
        if e <= s:
            return
        seg = sig[: e - s] * gain
        out[s:e, 0] += seg * (1 - max(0.0, pan))
        out[s:e, 1] += seg * (1 + min(0.0, pan))

    # ---- bed: two detuned sub tones, each with a slow tremolo, plus air noise
    bed = (np.sin(2 * np.pi * 41.2 * t) * 0.30
           + np.sin(2 * np.pi * 61.7 * t) * 0.18
           + np.sin(2 * np.pi * 82.4 * t) * 0.09)
    lfo = 0.72 + 0.28 * np.sin(2 * np.pi * 0.055 * t + 0.7)
    bed = bed * lfo
    air = lowpass_fast(rng.standard_normal(n), 0.0022) * 0.55
    air *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.031 * t)
    out[:, 0] += bed * 0.55 + air * 0.5
    out[:, 1] += bed * 0.55 + air * 0.5

    # ---- a low hit on every cut: the edit's pulse
    for i, ct in enumerate(cut_times):
        m = int(0.9 * SR)
        f = 58.0 * np.exp(-np.arange(m) / SR * 3.2) + 28.0
        hit = tone(1, m) * 0  # placeholder shape reused below
        phase = np.cumsum(2 * np.pi * f / SR)
        hit = np.sin(phase) * np.exp(-np.arange(m) / SR * 5.0)
        hit += rng.standard_normal(m) * np.exp(-np.arange(m) / SR * 40.0) * 0.18
        place(hit, ct, gain=0.55 if i % 2 == 0 else 0.40)

    # ---- riser into the hot beat and into the green beat
    for rt, rt_len in ((hot_start - 2.6, 2.6), (green_at - 1.8, 1.8)):
        m = int(rt_len * SR)
        k = np.linspace(0.004, 0.09, m)
        noise = rng.standard_normal(m)
        sweep = np.zeros(m)
        acc = 0.0
        for i in range(m):
            acc += (noise[i] - acc) * k[i]
            sweep[i] = acc
        ramp = (np.arange(m) / m) ** 2.2
        place(sweep * ramp * 1.6, rt, gain=0.7)

    # ---- the green flash: a short bright bell, answered by a low thud
    m = int(2.2 * SR)
    bell = tone(880.0, m, "bell") * np.exp(-np.arange(m) / SR * 2.4)
    place(bell, green_at, gain=0.30, pan=0.15)
    place(bell * 0.5, green_at + 0.06, gain=0.22, pan=-0.15)
    mm = int(1.4 * SR)
    thud = np.sin(2 * np.pi * 44 * np.arange(mm) / SR) * np.exp(-np.arange(mm) / SR * 3.0)
    place(thud, green_at, gain=0.5)

    # ---- tail: fade the whole thing, and never let it clip
    fade = int(1.6 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    head = int(0.25 * SR)
    out[:head] *= np.linspace(0, 1, head)[:, None]
    peak = np.max(np.abs(out)) or 1.0
    out = out / peak * 0.72
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, default=48.5)
    ap.add_argument("--out", default="/tmp/bed.wav")
    ap.add_argument("--cuts", default="4.5,8.6,13.0,18.4,24.5,28.6,32.0,37.2,40.4")
    ap.add_argument("--hot", type=float, default=13.0)
    ap.add_argument("--green", type=float, default=37.6)
    a = ap.parse_args()
    cuts = [float(x) for x in a.cuts.split(",") if x]
    sig = build(a.dur, cuts, a.hot, a.green)
    pcm = (np.clip(sig, -1, 1) * 32767).astype("<i2")
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", a.out, f"{a.dur}s {SR}Hz stereo")


if __name__ == "__main__":
    main()
