#!/usr/bin/env python3
"""Write silent clips at reading-pace durations for any line that has no usable recording yet.

The film's timing comes from its clips, so a project can be cut, previewed and rendered before the
voice exists: each missing line gets a silent clip as long as its caption takes to read aloud
(Telugu runs about 13 characters a second at storytelling pace, plus a beat). When a real take is
dropped into audio/lines, the same pipeline simply times the film off that instead.

  python3 tools/make_placeholders.py --project .
"""
import argparse
import json
import pathlib
import subprocess

CPS = 13.0
HOLD = {1: 1.0, 4: 1.0, 6: 0.8, 7: 0.9, 8: 0.9, 10: 0.8, 11: 1.2, 12: 1.4, 13: 1.6, 14: 1.4, 15: 1.6,
        16: 1.2, 17: 0.8, 18: 1.0, 19: 1.4, 20: 1.6, 21: 1.2, 22: 1.2, 23: 1.6, 24: 1.6}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    lines = proj / "audio" / "lines"
    segs = json.loads((proj / "audio" / "segments.json").read_text())["segments"]
    for s in segs:
        sid = s["id"]
        live = lines / f"seg{sid:02d}.mp3"
        silent = lines / f"seg{sid:02d}.silent"
        if live.exists() and not silent.exists() and not a.force:
            print(f"seg{sid:02d} kept (recorded)")
            continue
        # reading pace, plus room for the beat the picture holds on that line (a stone landing, a
        # gasp), so the silent cut is not faster than the voiced one will be
        dur = max(1.8, len(s["caption"]) / CPS) + HOLD.get(sid, 0.0)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
                        "-t", f"{dur:.2f}", str(live)], check=True)
        silent.touch()
        print(f"seg{sid:02d} placeholder {dur:.2f}s")


if __name__ == "__main__":
    main()
