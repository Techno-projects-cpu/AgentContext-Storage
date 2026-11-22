#!/usr/bin/env python3
"""Turn candidates.json into the clips.json that make_shorts.py expects.

    python3 tools/to_clips.py --transcript work/transcript.json -o clips.json

The interesting part is step 2. The candidates were written from a transcript without word
timestamps, so every start/end is a sentence the clip must begin and end on, give or take two
seconds. Here those sentences are matched back against the real transcript:

  * norm() flattens both sides to bare lowercase words, so "32 MGB of memory" in the public
    transcript and "32 megabytes of memory" in the Whisper transcript are not the same string,
    which is why the match is fuzzy (fuzzy = fraction of the anchor's words found in order);
  * the start is pulled to the first word of the matched sentence, minus a 0.05 s breath;
  * the end is pulled to the last word of the matched sentence, plus 0.35 s so the consonant
    is not clipped;
  * a match under --min-match is reported and left alone rather than guessed at silently.

Anything the matcher could not place is printed with a suggestion, and the script exits 1 while
--strict is on, so a bad transcript can never quietly produce a clip that starts mid-sentence.
"""
import argparse, difflib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STOP = set("a an the of to for and that with on in is so but i or at as if by from my your our it "
           "you we they this these those be was were do does did not no".split())


def words(s):
    return re.findall(r"[a-z0-9']+", s.lower())


def norm(toks):
    return [t for t in toks if t not in STOP]


def load_transcript(path):
    d = json.load(open(path, encoding="utf-8"))
    ws = d["words"] if isinstance(d, dict) else d
    for w in ws:
        w["w"] = w.get("w") or w.get("word") or ""
    return ws


def find(anchor, ws, from_s=0.0, span=20.0):
    """Best (score, first_index, last_index) for an anchor sentence inside ws.

    Slides a window the length of the anchor across the transcript from from_s onwards and
    keeps the window with the most anchor words in order. Fast enough for 8k words x 5 clips.
    """
    a = norm(words(anchor))
    if not a:
        return 0.0, None, None
    cand = [i for i, w in enumerate(ws) if w["start"] >= from_s - 0.5]
    best = (0.0, None, None)
    n = max(3, len(a))
    for k, i in enumerate(cand):
        if ws[i]["start"] > from_s + span:
            break
        for j in range(i, min(i + n + 8, len(ws))):
            win = norm(words(" ".join(w["w"] for w in ws[i:j + 1])))
            if not win:
                continue
            sm = difflib.SequenceMatcher(None, a, win)
            score = sm.ratio() * (0.6 + 0.4 * sm.find_longest_match(0, len(a), 0, len(win)).size /
                                  max(1, len(a)))
            if score > best[0]:
                best = (score, i, j)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", "--source", dest="source", default="source.mp4")
    ap.add_argument("--transcript", default="work/transcript.json")
    ap.add_argument("-o", "--out", default="clips.json")
    ap.add_argument("--min-match", type=float, default=0.55,
                    help="below this the clip keeps its written timings and is flagged")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any clip needs a human")
    a = ap.parse_args()

    cand = json.load(open(os.path.join(ROOT, "candidates.json"), encoding="utf-8"))
    ws = load_transcript(os.path.join(ROOT, a.transcript) if not os.path.isabs(a.transcript)
                         else a.transcript)
    clips, bad = [], []
    for c in cand["candidates"]:
        s_score, si, _ = find(c["start_line"], ws, max(0.0, c["start"] - 6), span=12)
        e_score, ei, ej = find(c["end_line"], ws, max(0.0, c["end"] - 8), span=14)
        start = ws[si]["start"] - 0.05 if si is not None and s_score >= a.min_match else c["start"]
        end = ws[ej]["end"] + 0.35 if ej is not None and e_score >= a.min_match else c["end"]
        flag = ""
        if s_score < a.min_match or e_score < a.min_match:
            flag = f"  <- CHECK (start {s_score:.2f}, end {e_score:.2f})"
            bad.append(c["id"])
        print(f"clip {c['id']}: {c['start']:.1f}->{start:.1f}  {c['end']:.1f}->{end:.1f}  "
              f"{end - start:.1f}s{flag}")
        clips.append({
            "id": c["id"], "start": round(start, 2), "end": round(end, 2),
            "hook": c["hook"], "title": c["title"], "caption": c["caption"],
            "reframe": "auto", "snap": False, "cuts": c.get("cuts", []),
        })

    out = {"video": os.path.basename(a.source), "style": dict(cand["style"]),
           "clips": clips}
    out["style"].pop("note", None)
    with open(os.path.join(ROOT, a.out), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(f"wrote {a.out}")
    if bad:
        print(f"needs a human look before rendering: clips {', '.join(bad)}")
        if a.strict:
            sys.exit(1)


if __name__ == "__main__":
    main()
