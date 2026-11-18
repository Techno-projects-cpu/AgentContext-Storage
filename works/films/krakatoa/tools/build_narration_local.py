#!/usr/bin/env python3
"""Assemble per-line narration clips into one track and the timing the film is built on.

Same contract as the skill's build_narration.py (audio/segments.json + audio/lines/segNN.*), but it
accepts any format ffmpeg reads (this project's lines come out as .mp3), so a project whose speech
was produced outside the skill's take flow can still be timed exactly.

  python3 tools/build_narration_local.py --project .
"""
import argparse
import json
import pathlib
import subprocess
import sys

TRIM = ("silenceremove=start_periods=1:start_silence=0:start_threshold=-50dB,areverse,"
        "silenceremove=start_periods=1:start_silence=0:start_threshold=-50dB,areverse")
TEMPO_LIMITS = (0.90, 1.15)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stderr[-2500:]}")
    return r.stdout


def duration(p):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip()
    return 0.0 if out in ("", "N/A") else float(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--target", type=float, default=0.0)
    ap.add_argument("--lead", type=float, default=0.9)
    ap.add_argument("--tail", type=float, default=2.6)
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    adir = proj / "audio"
    segments = json.loads((adir / "segments.json").read_text())["segments"]
    work = adir / "trimmed"; work.mkdir(exist_ok=True)
    pdir = work / "parts"; pdir.mkdir(parents=True, exist_ok=True)

    for seg in segments:
        sid = seg["id"]
        src = next((p for p in (adir / "lines" / f"seg{sid:02d}{e}" for e in (".wav", ".mp3", ".m4a"))
                    if p.exists()), None)
        if src is None:
            sys.exit(f"missing line clip for seg {sid} in {adir/'lines'}")
        # a silent placeholder (before its line is recorded) keeps its full length: no trim
        silent = (adir / "lines" / f"seg{sid:02d}.silent").exists()
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", "anull" if silent else TRIM,
             "-ar", "48000", "-ac", "1", str(work / f"raw{sid:02d}.wav")])

    raw = sum(duration(work / f"raw{s['id']:02d}.wav") for s in segments) or 1.0
    fixed = a.lead + a.tail + sum(s["gap_after"] for s in segments[:-1])
    tempo = 1.0 if a.target <= 0 else raw / (a.target - fixed)
    if not TEMPO_LIMITS[0] <= tempo <= TEMPO_LIMITS[1]:
        sys.exit(f"tempo {tempo:.3f} outside {TEMPO_LIMITS}: {raw:.1f}s speech + {fixed:.1f}s pauses")
    print(f"speech {raw:.2f}s + pauses {fixed:.2f}s, tempo {tempo:.4f}")

    timeline, parts, cursor = [], [], a.lead

    def silence(sec, tag):
        p = pdir / f"sil_{tag}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{sec:.3f}", str(p)])
        return p

    parts.append(silence(a.lead, "lead"))
    for i, seg in enumerate(segments):
        dst = work / f"seg{seg['id']:02d}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(work / f"raw{seg['id']:02d}.wav"), "-af", f"atempo={tempo:.6f}",
             "-ar", "48000", "-ac", "1", str(dst)])
        d = duration(dst)
        timeline.append({"id": seg["id"], "scene": seg["scene"], "caption": seg["caption"], "vo": seg["vo"],
                         "start": round(cursor, 3), "end": round(cursor + d, 3), "duration": round(d, 3)})
        parts.append(dst); cursor += d
        if i < len(segments) - 1:
            parts.append(silence(seg["gap_after"], f"g{seg['id']}")); cursor += seg["gap_after"]
    parts.append(silence(a.tail, "tail"))
    total = round(cursor + a.tail, 3)

    lst = pdir / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    track = adir / "narration.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", str(track)])
    (adir / "timing.json").write_text(json.dumps(
        {"total_duration": total, "lead_in": a.lead, "tail_out": a.tail, "tempo": round(tempo, 4),
         "segments": timeline}, indent=2))
    print(f"narration {track} ({duration(track):.2f}s), timeline {total:.2f}s, {len(timeline)} lines")


if __name__ == "__main__":
    main()
