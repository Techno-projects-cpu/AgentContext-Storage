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

import score          # noqa: E402
import kit as K       # noqa: E402
import scenes as S    # noqa: E402


def make_film(fps=30, scale=1.0):
    size = (int(round(K.W * scale)), int(round(K.H * scale)))
    shots = S.build(None)
    film = K.Film(shots, fps=fps, size=size)
    film.hud = lambda c, t, shot: S.hud(c, t, film, shot)
    S.FILM = film
    return film


def audio(out, duration):
    """The finished mix: score + voice, mastered. See score.py and mix.py."""
    import mix
    m, voice, bed, _ = mix.build(duration)
    score.write(out, np.stack([m, m], 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", default=os.path.join(HERE, "..", "05-duable-studio-1080x1920.mp4"))
    ap.add_argument("--still", type=float, default=None)
    ap.add_argument("--ffmpeg", default=os.environ.get("FFMPEG", "/tmp/fbin/ffmpeg"))
    ap.add_argument("--clean-out", default=None,
                    help="also write a music-only cut here (video stream copied)")
    ap.add_argument("--audio-only", action="store_true",
                    help="render the mix to _mix.wav and stop")
    a = ap.parse_args()

    film = make_film(a.fps, a.scale)
    if a.still is not None:
        from PIL import Image
        p = os.path.join(HERE, "..", f"still-{a.still:05.1f}.png")
        Image.fromarray(film.draw(a.still)).save(p)
        print("wrote", os.path.abspath(p))
        return 0

    wav = os.path.join(HERE, "_mix.wav")
    print("  building the mix (score + voice)…")
    audio(wav, film.duration)
    if a.audio_only:
        print("  wrote", wav)
        return 0
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
    print(f"\r  wrote {a.out} ({os.path.getsize(a.out)/1e6:.2f} MB, {film.duration:.2f}s)")

    if a.clean_out:
        # music only, for anyone who wants to cut against the picture themselves
        import mix as _mix
        clean = os.path.join(HERE, "_score.wav")
        _, _, bedout, _ = _mix.build(film.duration)   # the mastered BED, no voice
        _mix.score.write(clean, np.stack([bedout, bedout], 1))
        subprocess.run([a.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", a.out, "-i", clean, "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-movflags", "+faststart", "-shortest", a.clean_out], check=False)
        os.remove(clean)
        print(f"  wrote {a.clean_out} ({os.path.getsize(a.clean_out)/1e6:.2f} MB, music only)")
    os.remove(wav)
    return 0


if __name__ == "__main__":
    sys.exit(main())
