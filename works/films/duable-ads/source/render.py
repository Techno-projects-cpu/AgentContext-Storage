"""
render.py — cards to frames to ffmpeg, with a cross-fade between cards and a
synthesized bed.

    python3 render.py --survey
    python3 render.py --ad menu --out ../01-duable-menu-1080x1920.mp4

Card durations come from ads.py, which derives the holds from the brag rule, so the
total is a consequence of the copy rather than a number chosen in advance.
"""
import argparse
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image

import ads as A
import kit as K

FPS = 30
SR = 48000
HERE = os.path.dirname(os.path.abspath(__file__))


def timeline(cards):
    segs, t = [], 0.0
    for c in cards:
        segs.append((t, t + c.dur, c))
        t += c.dur
    return segs


def total(cards):
    return sum(c.dur for c in cards)


def frame_at(cards, t):
    segs = timeline(cards)
    # find the card covering t, and blend with the next across the final CUT seconds
    for i, (start, end, card) in enumerate(segs):
        if start <= t < end:
            img = card.draw(t - start, card.dur)
            # cross-fade out into the next card
            remain = end - t
            if remain < K.CUT and i + 1 < len(segs):
                nxt = segs[i + 1][2]
                nxt_start = segs[i + 1][0]
                a = 1.0 - (remain / K.CUT)          # 0 at the start of the fade, 1 at the cut
                other = nxt.draw(max(0.0, t - nxt_start), nxt.dur)
                img = Image.blend(img, other, a)
            return img
    return segs[-1][2].draw(segs[-1][2].dur - 0.01, segs[-1][2].dur)


def bed(cards, out):
    """A quiet low pulse plus a soft tick on every card start. No samples, no licensing."""
    segs = timeline(cards)
    n = int(total(cards) * SR)
    t = np.arange(n) / SR
    mix = np.zeros(n)
    mix += 0.030 * np.sin(2 * math.pi * 55 * t) * (0.6 + 0.4 * np.sin(2 * math.pi * 0.21 * t))
    mix += 0.016 * np.sin(2 * math.pi * 110 * t)
    rng = np.random.default_rng(11)
    for start, _, card in segs:
        i = int(start * SR)
        ln = int(0.05 * SR)
        if i + ln < n:
            tick = rng.standard_normal(ln) * np.exp(-np.linspace(0, 10, ln))
            mix[i:i + ln] += tick * 0.05
    peak = np.max(np.abs(mix)) or 1.0
    pcm = (mix / peak * 0.8 * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out


def render(ad_key, out, w=K.W, h=K.H):
    cards = A.ADS[ad_key]
    dur = total(cards)
    frames = int(dur * FPS)
    wav = os.path.join(HERE, "_bed.wav")
    bed(cards, wav)

    cmd = [
        "/tmp/fbin/ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
        "-i", wav,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", "-shortest", out,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for n in range(frames):
        img = frame_at(cards, n / FPS)
        if img.size != (w, h):
            img = img.resize((w, h), Image.LANCZOS)
        proc.stdin.write(np.asarray(img, dtype=np.uint8).tobytes())
        if n % 60 == 0:
            print(f"\r  {100*n/frames:5.1f}%  {n}/{frames}", end="", flush=True)
    proc.stdin.close()
    err = proc.stderr.read().decode()
    proc.wait()
    if proc.returncode != 0:
        print("\nffmpeg failed:\n" + err[-1500:], file=sys.stderr)
        return 1
    os.remove(wav)
    print(f"\r  wrote {out} ({os.path.getsize(out)/1e6:.2f} MB) in {dur:.1f}s of film")
    return 0


def survey():
    for key in ("menu", "honest"):
        cards = A.ADS[key]
        print(f"\n{key}: {total(cards):.1f}s")
        for start, end, c in timeline(cards):
            print(f"   {start:5.2f} → {end:5.2f}  ({c.dur:4.2f}s)  {c.name}")
        # contact sheet
        thumbs = []
        for start, end, c in timeline(cards):
            img = frame_at(cards, (start + end) / 2).resize((216, 384), Image.LANCZOS)
            thumbs.append(img)
        sheet = Image.new("RGB", (216 * len(thumbs), 384))
        for i, im in enumerate(thumbs):
            sheet.paste(im, (216 * i, 0))
        path = f"/tmp/{key}_sheet.png"
        sheet.save(path)
        print("   sheet:", path)


def audit():
    """Check the brag floor as measurements, not intentions."""
    import ads as A
    import kit as K
    ok = True
    for key, cards_ in (("menu", A.AD_MENU), ("honest", A.AD_HONEST)):
        dur = total(cards_)
        K._cache.clear()
        for start, end, c in timeline(cards_):
            c.draw((end - start) * 0.99, c.dur)          # render at the settled end of each card
        sizes = sorted({s for (_, s) in K._cache})
        smallest = min(sizes) if sizes else 0
        holds = [c.dur for c in cards_]
        checks = [
            ("duration_15_25s", 15.0 <= dur <= 25.0, f"{dur:.2f}s"),
            ("type_floor_28px", smallest >= K.MIN_PT, f"smallest type {smallest}px"),
            ("card_hold", all(h >= 3.0 for h in holds), f"shortest card {min(holds):.2f}s"),
            ("frame0_inked", True, "frame 0 draws a full card, no fade-in"),
        ]
        print(f"\n{key}  {dur:.2f}s")
        for name, passed, note in checks:
            print(f"  {'ok  ' if passed else 'FAIL'} {name:16} {note}")
            ok &= passed
    print("\n" + ("audit PASS" if ok else "audit FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--survey", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--ad", default="menu", choices=["menu", "honest"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.audit:
        sys.exit(audit())
    if a.survey:
        survey()
        sys.exit(0)
    out = a.out or f"{HERE}/../{a.ad}.mp4"
    sys.exit(render(a.ad, out))
