"""
mix.py — put the score and the voice together, and master to delivery.

Nothing here assumes the assets are good. It measures them:

  * each voice line is trimmed of leading/trailing silence, then normalised to
    the same loudness (two of the five lines came back ~17 dB quieter than the
    others, which is a gain problem, not a read problem)
  * the score is sidechain-ducked under the voice, so the ducking follows the
    actual speech envelope rather than a hand-drawn automation curve
  * the voice gets a short plate: it must sound like it is in the same room as
    the piano, not pasted on top of it
  * the master is limited to -1.0 dBTP-ish and normalised to -14 LUFS, which is
    where Instagram / TikTok actually put a vertical film

    python3 mix.py --out ../audio-mix.wav --dur 25.4
"""
import argparse
import glob
import os
import re
import subprocess
import wave

import numpy as np

import score
from score import SR

# where each line lands in the film, and how loud it should sit.
# The picture cuts are 0, 3.2, 7.6, 11.2, 15.6.
# The story, one line per beat. The cuts are 0 / 2.9 / 6.8 / 10.2 / 14.0 / 17.8 /
# 21.4. Each line starts a beat AFTER its cut, so the picture lands first and the
# voice then says what we are looking at — the reverse reads as a slideshow.
VO = [
    ("01.wav", 0.60),    # "I need a thing made."
    ("02.wav", 3.40),    # every service starts with a sentence like that
    ("03.wav", 7.35),    # twenty-four services, four categories
    ("04.wav", 10.65),   # one of them is yours
    ("05.wav", 14.30),   # they said: make the story and visuals feel connected
    ("06.wav", 17.95),   # design. automate. edit. position.
    ("07.wav", 21.55),   # duable. a studio with a service for that.
]
VO_LEVEL_DB = -16.0      # speech loudness relative to full scale (LUFS-ish target)
BED_LEVEL_DB = -27.0     # score alone, before ducking
DUCK_DB = -7.0           # how far the score drops under a line


def read(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        n = int(round(len(x) * SR / sr))
        x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
    return x


def trim(x, thresh=0.012, pad=0.04):
    """Cut the air off both ends, keeping 40 ms so consonants are not clipped."""
    env = np.abs(x)
    # 10 ms smoothing so a single sample cannot define the start
    k = int(0.010 * SR)
    env = np.convolve(env, np.ones(k) / k, "same")
    idx = np.where(env > thresh)[0]
    if not len(idx):
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(0.12 * SR))
    return x[a:b]


def rms_db(x):
    return 20 * np.log10(max(float(np.sqrt(np.mean(x ** 2))), 1e-9))


def fades(x, fin=0.006, fout=0.030):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a) ** 0.5
    if b:
        x[-b:] *= np.linspace(1, 0, b) ** 0.5
    return x


def plate(x, wet=0.13, seconds=0.85):
    """A short room on the voice, so it shares a space with the score."""
    n_ir = int(seconds * SR)
    t = np.arange(n_ir) / SR
    rng = np.random.default_rng(19)
    ir = rng.standard_normal(n_ir) * np.exp(-t / (seconds * 0.20))
    ir = np.convolve(ir, np.ones(4) / 4, "same")
    ir[: int(0.008 * SR)] *= np.linspace(0, 1, int(0.008 * SR))
    ir /= np.sqrt(np.sum(ir ** 2))
    nfft = 1 << int(np.ceil(np.log2(len(x) + n_ir)))
    w = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[: len(x)]
    return x * (1 - wet) + w * wet


def build(dur=24.8, here=None):
    here = here or os.path.join(os.path.dirname(os.path.abspath(__file__)), "vo")
    n = int(dur * SR)
    voice = np.zeros(n)
    spikes = []          # for ducking

    for name, at in VO:
        p = os.path.join(here, name)
        if not os.path.exists(p):
            print(f"  !! missing {p}")
            continue
        x = trim(read(p))
        x = fades(x)
        x = plate(x)
        # match loudness: measured, not assumed
        x = x * (10 ** (VO_LEVEL_DB / 20) / max(np.sqrt(np.mean(x ** 2)), 1e-9))
        s = int(at * SR)
        e = min(n, s + len(x))
        if e - s < len(x):
            print(f"  !! {name} overruns by {(s+len(x)-e)/SR:.2f}s — truncated")
        voice[s:e] += x[: e - s]
        spikes.append((at, at + len(x) / SR))

    # the bed, at its own level, then ducked by the speech envelope
    bedfull = score.build(dur)
    bed = bedfull.mean(axis=1) if bedfull.ndim > 1 else bedfull
    bed = bed[:n].astype(np.float64)
    bed = bed * (10 ** (BED_LEVEL_DB / 20) / max(np.sqrt(np.mean(bed ** 2)), 1e-9))

    env = np.abs(voice)
    k = int(0.030 * SR)                       # 30 ms attack/release feel
    env = np.convolve(env, np.ones(k) / k, "same")
    env = env / max(env.max(), 1e-9)
    # smooth it further so the duck breathes instead of chattering
    env = np.convolve(env, np.ones(int(0.12 * SR)) / int(0.12 * SR), "same")
    duck = 10 ** ((DUCK_DB * np.clip(env * 1.6, 0, 1)) / 20)
    bed = bed * duck

    mix = bed + voice

    # master: compress for glue, then hit the target by measuring, not guessing
    mix = compress(mix, thr_db=-21.0, ratio=2.2, atk=0.010, rel=0.20)
    # A negative number to a fractional power is COMPLEX in Python, which
    # silently put complex samples in the wav. Keep the exponent outside.
    mix = limit(mix)
    mix = aim(mix, -14.0, "_aim_loud.wav")
    assert np.isrealobj(mix), "mix went complex — check the gain maths"

    # The music-only cut is NOT this mix: it is the ducked bed, mastered on its
    # own. (First attempt returned `mix` and shipped the narration twice.)
    bedout = limit(compress(bed / max(np.max(np.abs(bed)), 1e-9) * 0.5,
                            thr_db=-21.0, ratio=1.6, atk=0.010, rel=0.20))
    bedout = aim(bedout, -14.0, "_aim_bed.wav")
    return mix, voice, bedout, spikes


def aim(x, target_db, tmp_name):
    """Master to a loudness target by measuring the real thing.

    My analytic estimate was 3.5 dB optimistic on this material, so aiming with
    it shipped a -10.5 LUFS file while claiming -14. Measure the wav with
    ffmpeg's BS.1770 meter and correct — twice is enough, but it verifies.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), tmp_name)
    for _ in range(3):
        score.write(path, np.stack([x, x], 1))
        cur = measure_db(path)
        if cur is None:
            break
        need = target_db - cur
        if abs(need) < 0.3:
            break
        x = limit(x * (10.0 ** (need / 20.0)))
    try:
        os.remove(path)
    except OSError:
        pass
    return x


def compress(x, thr_db=-20.0, ratio=2.2, atk=0.012, rel=0.22, makeup_db=0.0):
    """Bus compression, sample by sample. This is what gives the mix glue and
    the crest factor a real delivery needs: measured, the raw sum was -22 LUFS
    at a -0.5 dBFS peak, which is a 21 dB crest — far too spiky for social."""
    thr = 10 ** (thr_db / 20)
    a_att = np.exp(-1.0 / (atk * SR))
    a_rel = np.exp(-1.0 / (rel * SR))
    env = 0.0
    out = np.empty_like(x)
    for i in range(len(x)):
        v = abs(x[i])
        if v > env:
            env = a_att * env + (1 - a_att) * v
        else:
            env = a_rel * env + (1 - a_rel) * v
        g = 1.0
        if env > thr:
            g = (env / thr) ** (1.0 / ratio - 1.0)
        out[i] = x[i] * g
    return out * 10 ** (makeup_db / 20)


def limit(x, ceiling=0.89, knee=0.80):
    """Soft ceiling. Above the knee the curve is tanh, so a transient is rounded
    rather than squared off — no audible crackle on the piano attacks."""
    y = x.copy()
    over = np.abs(y) > knee
    y[over] = np.sign(y[over]) * (knee + (ceiling - knee) *
                                  np.tanh((np.abs(y[over]) - knee) / (ceiling - knee)))
    return y


# My own K-weight approximation read 4 dB louder than ffmpeg's BS.1770 meter on
# this mix (said -14.0, measured -10.5), so it is deliberately not used to aim
# the master any more: measure with ffmpeg and correct. The estimate below is
# only a starting guess for the first iteration.
CAL = {"db": 0.0}


def measure_db(path):
    """Integrated loudness as ffmpeg's BS.1770 meter reports it. This is the
    number a platform will see, so it is the only one worth aiming at."""
    p = subprocess.run([os.environ.get("FFMPEG", "/tmp/fbin/ffmpeg"), "-hide_banner",
                        "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    hits = re.findall(r"I:\s*(-?[\d.]+) LUFS", p.stderr)
    return float(hits[-1]) if hits else None


def lufs_approx(x):
    """K-weighted-ish loudness estimate. Superseded by measure_db() for the
    final aim; kept for the first pass and for reporting."""
    b = 0.995
    y = np.zeros_like(x)
    prev = 0.0
    for i in range(len(x)):
        prev = b * prev + (1 - b) * x[i]
        y[i] = x[i] - prev
    # gated: ignore 400 ms blocks under -70 LUFS relative
    blk = int(0.4 * SR)
    m = [np.mean(z ** 2) for z in np.array_split(y, max(1, len(y) // blk))]
    m = np.array(m)
    if not len(m):
        return -70.0
    loud = -0.691 + 10 * np.log10(np.maximum(m, 1e-12))
    keep = m[loud > (loud.max() - 20)]
    return float(-0.691 + 10 * np.log10(max(np.mean(keep), 1e-12)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="audio-mix.wav")
    ap.add_argument("--dur", type=float, default=24.8)
    a = ap.parse_args()
    mix, voice, bed, _ = build(a.dur)
    score.write(a.out, np.stack([mix, mix], 1))
    print(f"wrote {a.out}  {len(mix)/SR:.2f}s")
    measured = measure_db(a.out)
    print(f"  measured {measured if measured is None else round(measured,1)} LUFS "
          f"peak {20*np.log10(np.max(np.abs(mix))):.1f} dBFS")
    for name, at in VO:
        s, e = int(at * SR), min(len(voice), int((at + 4.2) * SR))
        print(f"  vo {name} @ {at:5.2f}s  rms {rms_db(voice[s:e]):6.1f} dB")


if __name__ == "__main__":
    main()
