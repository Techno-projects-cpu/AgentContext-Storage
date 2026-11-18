"""Voice lines for the two English ads.

`generate_speech` writes clip N into audio/lines/segNN.mp3 (see the film's README); this module only
transcribes the script into the shapes the rest of the pipeline wants:

  python3 ../_shared/eng/vo.py --project . --lines      # print the exact text per clip
  python3 ../_shared/eng/vo.py --project . --join       # audio/narration.m4a + audio/timing.json

`--join` concatenates the clips with the scripted gaps, trims dead air off each take, and writes
the same timing.json contract the engine's Doc reads (segments with start / end / stage), so the
scene is timed from the voice rather than from guesses.
"""
import argparse
import json
import pathlib
import subprocess
import sys

TRIM = ("silenceremove=start_periods=1:start_silence=0:start_threshold=-45dB,areverse,"
        "silenceremove=start_periods=1:start_silence=0:start_threshold=-45dB,areverse")
LEAD, TAIL = 0.75, 1.9


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def dur(p):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--lines", action="store_true")
    ap.add_argument("--join", action="store_true")
    a = ap.parse_args()
    proj = pathlib.Path(a.project)
    adir = proj / "audio"
    segs = json.loads((adir / "segments.json").read_text())["segments"]

    if a.lines:
        for s in segs:
            print(f"{s['id']:2d}  {s['vo']}")
        return

    work = adir / "work"
    work.mkdir(parents=True, exist_ok=True)
    parts, cursor, timeline = [], LEAD, []

    def silence(sec, tag):
        p = work / f"sil_{tag}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
             "-t", f"{sec:.3f}", str(p)])
        return p

    parts.append(silence(LEAD, "lead"))
    for s in segs:
        src = next((p for p in (adir / "lines" / f"seg{s['id']:02d}{e}" for e in (".mp3", ".wav", ".m4a"))
                    if p.exists()), None)
        if src is None:
            sys.exit(f"missing clip for seg {s['id']}: {adir/'lines'}/seg{s['id']:02d}.mp3")
        trimmed = work / f"t{s['id']:02d}.wav"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", TRIM, "-ar", "48000", "-ac", "1", str(trimmed)])
        d = dur(trimmed)
        if d < 0.25:                       # the trimmer ate a short take: keep it whole
            run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", "anull", "-ar", "48000", "-ac", "1", str(trimmed)])
            d = dur(trimmed)
        # a hair of air on each side of the take, so lines do not butt against the music
        padded = work / f"p{s['id']:02d}.wav"
        # NB: `-t` must come BEFORE each `-i` (input trim); after it, it cuts the whole output instead
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-t", "0.09", "-i", "anullsrc=r=48000:cl=mono",
             "-i", str(trimmed), "-f", "lavfi", "-t", "0.12", "-i", "anullsrc=r=48000:cl=mono",
             "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1", "-ar", "48000", "-ac", "1", str(padded)])
        d = dur(padded)
        row = {k: v for k, v in s.items() if k not in ("start", "end")}
        row.update({"start": round(cursor, 3), "end": round(cursor + d, 3), "duration": round(d, 3)})
        timeline.append(row)
        parts.append(padded)
        cursor += d
        gap = s.get("gap_after", 0.3)
        if s is not segs[-1]:
            parts.append(silence(gap, f"g{s['id']}")); cursor += gap
    parts.append(silence(TAIL, "tail"))
    total = round(cursor + TAIL, 3)

    lst = work / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    track = adir / "narration.m4a"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000", "-c:a", "aac", "-b:a", "192k", str(track)])
    (adir / "timing.json").write_text(json.dumps(
        {"total_duration": total, "lead_in": LEAD, "tail_out": TAIL, "segments": timeline}, indent=2))
    print(f"{track}  {dur(track):.2f}s   timeline {total:.2f}s  {len(timeline)} lines")
    for r in timeline:
        print(f"  {r['id']:2d} {r['start']:6.2f} -> {r['end']:6.2f}  [{r['stage']:6s}] {r['caption']}")


if __name__ == "__main__":
    main()
