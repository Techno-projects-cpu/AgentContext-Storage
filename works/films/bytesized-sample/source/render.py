"""
render.py — frames to ffmpeg, then a narration track, then the two are muxed.

    python3 render.py --survey                  # timings + a contact sheet, no video
    python3 render.py --w 540 --h 960 --out /tmp/prev.mp4 --beat 2
    python3 render.py --out out.mp4            # full render at 1080x1920

Beat durations are derived from the copy: the narration length of each line sets
how long its card stays up, which is how the real channel is paced — the cut
follows the sentence, not a fixed template.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image

import copy as C
import layout as L

FPS = 30
W, H = 1080, 1920

# Measured pace of the channel: ~2.6 words per second, unhurried, with a beat of
# silence between cards. Used only to size the cards before real audio exists.
WPS = 2.6
BEAT_PAD = 0.45
TITLE_DUR = 4.0
TABLE_DUR = 11.0
SIGN_DUR = 5.5


def _words(s):
    return len(s.replace("\n", " ").split())


def beat_duration(beat):
    spoken = _words(beat["line"]) + sum(_words(x) for x in beat["detail"])
    dur = max(7.0, spoken / WPS + 2.4)
    return round(dur, 2)


BEAT_DURS = [beat_duration(b) for b in C.BEATS]
TOTAL = TITLE_DUR + sum(BEAT_DURS) + TABLE_DUR + SIGN_DUR


def timeline():
    """[(start, end, kind, index)] for the whole film."""
    segs = []
    t = 0.0
    segs.append((t, t + TITLE_DUR, "title", -1))
    t += TITLE_DUR
    for i, dur in enumerate(BEAT_DURS):
        segs.append((t, t + dur, "beat", i))
        t += dur
    segs.append((t, t + TABLE_DUR, "table", -1))
    t += TABLE_DUR
    segs.append((t, t + SIGN_DUR, "sign", -1))
    t += SIGN_DUR
    return segs


def frame_at(t):
    for start, end, kind, i in timeline():
        if start <= t < end:
            local = t - start
            if kind == "title":
                return L.title_card(local)
            if kind == "beat":
                return L.beat_card(i, local, t, TOTAL)
            if kind == "table":
                return L.table_card(local)
            return L.sign_card(local)
    # past the end: hold the last frame
    return L.sign_card(SIGN_DUR - 0.01)


def survey(outdir):
    segs = timeline()
    print(f"total {TOTAL:.1f}s  ({TOTAL/60:.2f} min)")
    for start, end, kind, i in segs:
        label = kind if i < 0 else f"{kind} {C.BEATS[i]['n']} {C.BEATS[i]['term']}"
        print(f"  {start:6.2f} → {end:6.2f}  ({end-start:5.2f}s)  {label}")
    os.makedirs(outdir, exist_ok=True)
    # contact sheet: one frame mid-way through each card
    picks = []
    for start, end, kind, i in segs:
        picks.append((start + end) / 2)
    thumbs = []
    for t in picks:
        img = frame_at(min(t, TOTAL - 0.05)).resize((270, 480), Image.LANCZOS)
        thumbs.append(img)
    sheet = Image.new("RGB", (270 * len(thumbs), 480), (255, 255, 255))
    for k, img in enumerate(thumbs):
        sheet.paste(img, (270 * k, 0))
    path = os.path.join(outdir, "contact.png")
    sheet.save(path)
    print("contact sheet:", path)
    return path


def render(out, w, h, only_beat=None, ss=None, dur=None):
    fps = FPS
    total = TOTAL if dur is None else min(dur, TOTAL)
    frames = int(total * fps)

    has_audio = os.path.exists(AUDIO_PATH)
    cmd = [
        "/tmp/fbin/ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
        "-i", "-",
    ]
    if has_audio:
        cmd += ["-i", AUDIO_PATH]
    cmd += [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
    ]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
    cmd += [out]

    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    t0 = 0.0 if ss is None else ss
    scale = (w, h)
    for n in range(frames):
        t = t0 + n / fps
        if only_beat is not None:
            seg = [s for s in timeline() if s[2] == "beat" and s[3] == only_beat][0]
            t = seg[0] + (n / fps) % (seg[1] - seg[0])
        img = frame_at(t)
        if img.size != scale:
            img = img.resize(scale, Image.LANCZOS)
        proc.stdin.write(np.asarray(img, dtype=np.uint8).tobytes())
        if n % 60 == 0:
            pct = 100 * n / max(1, frames)
            print(f"\r  {pct:5.1f}%  frame {n}/{frames}", end="", flush=True)
    proc.stdin.close()
    err = proc.stderr.read().decode() if proc.stderr else ""
    proc.wait()
    if proc.returncode != 0:
        print("ffmpeg failed:\n" + err[-2000:], file=sys.stderr)
    print(f"\rwrote {out} ({os.path.getsize(out)/1e6:.1f} MB)" if os.path.exists(out) else "FAILED")
    return proc.returncode


AUDIO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "narration.wav")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--out", default="/tmp/bytesized.mp4")
    ap.add_argument("--w", type=int, default=W)
    ap.add_argument("--h", type=int, default=H)
    ap.add_argument("--beat", type=int, default=None)
    ap.add_argument("--ss", type=float, default=None)
    ap.add_argument("--dur", type=float, default=None)
    a = ap.parse_args()
    if a.survey:
        survey("/tmp/bs")
        sys.exit(0)
    sys.exit(render(a.out, a.w, a.h, a.beat, a.ss, a.dur))
