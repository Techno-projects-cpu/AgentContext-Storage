"""
film.py — render the studio film.

    LD_LIBRARY_PATH=/tmp/gl python3 film.py --still 2.0
    LD_LIBRARY_PATH=/tmp/gl python3 film.py --out ../05-duable-studio-1080x1920.mp4

The 3D plate (stage.py) is rendered per frame at 900x1600 in the same process and
composited by skia, so the film is one pipeline rather than two passes.
"""
import argparse
import os
import subprocess
import sys
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kit as K       # noqa: E402
import scenes as S    # noqa: E402


def make_film(fps=30, scale=1.0):
    size = (int(round(K.W * scale)), int(round(K.H * scale)))
    shots = S.build(None)
    film = K.Film(shots, fps=fps, size=size)
    film.hud = lambda c, t, shot: S.hud(c, t, film, shot)
    S.FILM = film
    return film


def audio(out, duration, cuts):
    """A bed you barely notice: sub drone, a soft hit per cut, air. No samples."""
    sr = 48000
    n = int(duration * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(5)
    mix = (np.sin(2 * np.pi * 48.0 * t) * 0.20
           + np.sin(2 * np.pi * 72.0 * t) * 0.09)
    mix *= 0.70 + 0.30 * np.sin(2 * np.pi * 0.05 * t + 0.4)
    air = np.convolve(rng.standard_normal(n), np.ones(320) / 320, "same") * 0.7
    mix += air * 0.20
    for i, ct in enumerate(cuts):
        m = int(0.8 * sr)
        f = 58.0 * np.exp(-np.arange(m) / sr * 3.0) + 30.0
        hit = np.sin(np.cumsum(2 * np.pi * f / sr)) * np.exp(-np.arange(m) / sr * 6.0)
        tone = np.sin(2 * np.pi * 1180 * np.arange(m) / sr) * np.exp(-np.arange(m) / sr * 24)
        s = int(ct * sr)
        e = min(n, s + m)
        seg = (hit * 0.42 + tone * 0.06)[: e - s]
        mix[s:e] += seg
    fade = int(1.4 * sr)
    mix[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(mix)) or 1.0
    mix = mix / peak * 0.78
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "05-duable-studio-1080x1920.mp4"))
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--ffmpeg", default=os.environ.get("FFMPEG", "/tmp/fbin/ffmpeg"))
    a = ap.parse_args()

    film = make_film(a.fps, a.scale)
    if a.still is not None:
        from PIL import Image
        p = os.path.join(HERE, "..", f"still-{a.still:05.1f}.png")
        Image.fromarray(film.draw(a.still)).save(p)
        print("wrote", os.path.abspath(p))
        return 0

    wav = os.path.join(HERE, "_bed.wav")
    audio(wav, film.duration, [s.t0 for s in film.shots[1:]])
    cmd = [a.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{film.W}x{film.H}",
           "-r", str(film.fps), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k", "-shortest", a.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    n_frames = int(round(film.duration * film.fps))
    try:
        for n in range(n_frames):
            proc.stdin.write(film.frame(n).tobytes())
            if n % 15 == 0:
                print(f"\r  {100*n/max(1,n_frames):5.1f}%  {n}/{n_frames}", end="", flush=True)
    except BrokenPipeError:
        pass
    proc.stdin.close()
    err = proc.stderr.read().decode()
    rc = proc.wait()
    if rc != 0:
        print("\nffmpeg failed:\n" + err[-2000:], file=sys.stderr)
        return 1
    os.remove(wav)
    print(f"\r  wrote {a.out} ({os.path.getsize(a.out)/1e6:.2f} MB, {film.duration:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
