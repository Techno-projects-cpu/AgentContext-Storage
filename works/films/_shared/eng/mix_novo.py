#!/usr/bin/env python3
"""Mix a film with NO VOICE: music + effects only, normalised to a target loudness.

`mix_soundtrack.py` ducks the music against the narration, so it needs a voice track; a music-led ad
has nothing to duck against and nothing to cut around. What it does need is the opposite: the music
IS the foreground, so the effects sit close under it and the whole mix is levelled to the same
-15 LUFS the voiced films hit, which keeps a playlist of all four ads consistent.

  python3 mix_novo.py --project . --music audio/score.wav --sfx audio/sfx.wav --out audio/mix.m4a

Two passes of ffmpeg loudnorm (measure, then apply linearly) rather than one, so no dynamic
compression smears the transients -- the hits on the cuts are the whole point of the track.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--music", default="audio/score.wav")
    ap.add_argument("--sfx", default="audio/sfx.wav")
    ap.add_argument("--out", default="audio/mix.m4a")
    ap.add_argument("--music-db", type=float, default=-2.0, help="music bus gain")
    ap.add_argument("--sfx-db", type=float, default=-8.0, help="effects bus gain")
    ap.add_argument("--lufs", type=float, default=-15.0)
    ap.add_argument("--fade-in", type=float, default=0.25)
    ap.add_argument("--fade-out", type=float, default=1.0)
    a = ap.parse_args()

    proj = pathlib.Path(a.project)
    timing = proj / "audio" / "timing.json"
    dur = (json.loads(timing.read_text())["total_duration"] if timing.exists()
           else float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                           "-of", "csv=p=0", str(proj / a.music)]).stdout.strip() or 0.0))
    music = proj / a.music
    sfx = proj / a.sfx
    inputs = ["-i", str(music)]
    parts = [f"[0:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
             f"aformat=sample_rates=48000:channel_layouts=stereo,"
             f"afade=t=in:d={a.fade_in},afade=t=out:st={max(0.0, dur - a.fade_out):.3f}:d={a.fade_out},"
             f"volume={a.music_db}dB[mu];"]
    mix = ["[mu]"]
    if sfx.exists():
        inputs += ["-i", str(sfx)]
        parts.append(f"[1:a]atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
                     f"aformat=sample_rates=48000:channel_layouts=stereo,volume={a.sfx_db}dB[sfx];")
        mix.append("[sfx]")
    else:
        print(f"no {sfx}: mixing music only")
    graph = "".join(parts) + ("".join(mix) +
                              f"amix=inputs={len(mix)}:duration=first:normalize=0,"
                              f"alimiter=limit=0.9:level=disabled")

    r = run(["ffmpeg", "-v", "info", "-y", *inputs, "-filter_complex",
             graph + f",loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}:linear=true")
    out = proj / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    p = run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", graph + "," + ln + ",aresample=48000",
             "-c:a", "aac", "-b:a", "256k", str(out)])
    if p.returncode:
        sys.exit(p.stderr[-1200:])
    print(f"mix: {out}  (measured {m['input_i']} LUFS -> {a.lufs})")


if __name__ == "__main__":
    main()
