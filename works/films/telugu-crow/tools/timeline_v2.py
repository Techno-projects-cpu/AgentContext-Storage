#!/usr/bin/env python3
"""Build audio/lines + timing.json for the v2 cut from the takes in audio/v2.

The v2 rules, learned the hard way: one short recorded line per segment, no tempo tricks, no
guessed durations. A segment whose take is missing or unusable is reported, not papered over --
so the timeline this writes is always the timeline the voice actually plays at.

  python3 tools/timeline_v2.py --project .
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

TRIM = ("silenceremove=start_periods=1:start_silence=0:start_threshold=-48dB,areverse,"
        "silenceremove=start_periods=1:start_silence=0:start_threshold=-48dB,areverse")
LOOP_LIMIT = 6.0          # longer than this for a <20-char line means the service looped


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def dur(p):
    out = run(["ffmpeg", "-v", "error", "-i", p, "-f", "null", "-"]) if False else None
    o = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p]).strip()
    return 0.0 if o in ("", "N/A") else float(o)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--lead", type=float, default=0.7)
    a = ap.parse_args()
    proj = pathlib.Path(a.project).resolve()
    adir = proj / "audio"
    segs = json.loads((adir / "v2" / "segments.json").read_text())["segments"]
    lines = adir / "lines"
    lines.mkdir(exist_ok=True)
    tmp = adir / "v2" / "trim"
    tmp.mkdir(parents=True, exist_ok=True)

    for f in lines.glob("*"):
        f.unlink()

    timeline, t = [], a.lead
    missing, loops = [], []
    for s in segs:
        sid = s["id"]
        src = adir / "v2" / f"seg{sid:02d}.mp3"
        if not src.exists():
            missing.append(sid)
            continue
        out = tmp / f"seg{sid:02d}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", TRIM, "-ar", "48000", "-ac", "1", out])
        d = dur(out)
        if d > LOOP_LIMIT and len(s["vo"]) < 24:
            loops.append((sid, round(d, 2)))
            continue
        shutil.copy(out, lines / f"seg{sid:02d}.wav")
        timeline.append(dict(id=sid, scene=s["scene"], stage=s["stage"], caption=s["caption"],
                             vo=s["vo"], start=round(t, 3), end=round(t + d, 3), dur=round(d, 3),
                             gap_after=s["gap_after"]))
        t += d + s["gap_after"]

    total = round(t + 1.2, 3)                       # a breath of black at the tail
    (adir / "timing.json").write_text(json.dumps(dict(total_duration=total, segments=timeline), indent=1))
    speech = sum(x["dur"] for x in timeline)
    print(f"total {total:.2f}s  speech {speech:.2f}s  {len(timeline)}/{len(segs)} lines voiced")
    for x in timeline:
        print(f"  {x['id']:2d} {x['start']:6.2f}-{x['end']:6.2f} ({x['dur']:5.2f}s) {x['caption']}")
    if missing:
        print("MISSING TAKES:", missing)
    if loops:
        print("REJECTED (loop):", loops)
    return 1 if (missing or loops) else 0


if __name__ == "__main__":
    sys.exit(main())
