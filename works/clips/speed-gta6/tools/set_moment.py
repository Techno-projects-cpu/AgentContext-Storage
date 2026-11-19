#!/usr/bin/env python3
"""Record a real moment in candidates.json, by timestamp, from the command line.

    python3 tools/set_moment.py 01 4823.5 4851.0 \
        --hook "First frame of GTA 6" \
        --title "IShowSpeed sees GTA 6 for the first time" \
        --start-line "oh my god oh my god" \
        --why "his face before the game loads, then the cut to gameplay"

    python3 tools/set_moment.py --list      # show what is filled in and what is not

This is deliberately the fastest possible path from "I saw it at 1:20:23" to a rendered clip:
one command records the seconds, and capture.sh cuts them straight away. The moment does not
need a transcript, because Speed's clips are found by watching, not by reading.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLIP_PACK") or os.path.dirname(HERE)
PATH = os.path.join(ROOT, "candidates.json")


def load():
    return json.load(open(PATH, encoding="utf-8"))


def save(d):
    json.dump(d, open(PATH, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def list_(d):
    filled = d.get("capture", {}).get("final", {})
    ids = {c["id"] for c in d["candidates"]} | set(filled)
    for cid in sorted(ids):
        c = next((x for x in d["candidates"] if x["id"] == cid), None)
        f = filled.get(cid)
        if f:
            print(f"  {cid}  {f['start']:>8.1f} -> {f['end']:>8.1f}  "
                  f"({f['end'] - f['start']:.1f}s)  {c['hook'] if c else ''}")
        else:
            print(f"  {cid}  (empty)                              {c['hook'] if c else '(new)'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id", nargs="?")
    ap.add_argument("start", nargs="?", type=float)
    ap.add_argument("end", nargs="?", type=float)
    ap.add_argument("--hook")
    ap.add_argument("--title")
    ap.add_argument("--caption")
    ap.add_argument("--start-line")
    ap.add_argument("--end-line")
    ap.add_argument("--why")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    d = load()

    if a.list or not a.id:
        list_(d)
        return

    if a.end is None:
        sys.exit("need: id start end")
    if a.end <= a.start:
        sys.exit("end must be after start")
    length = a.end - a.start
    if length > 60:
        print(f"note: {length:.0f}s is over the 60s ceiling for reused footage; "
              f"the skill caps these at 60", file=sys.stderr)

    c = next((x for x in d["candidates"] if x["id"] == a.id), None)
    if c is None:
        c = {"id": a.id, "cuts": []}
        d["candidates"].append(c)
        d["candidates"].sort(key=lambda x: x["id"])
    c.update({"start": a.start, "end": a.end})
    for key, val in (("hook", a.hook), ("title", a.title), ("caption", a.caption),
                     ("start_line", a.start_line), ("end_line", a.end_line), ("why", a.why)):
        if val:
            c[key] = val
    for key in ("hook", "title", "start_line"):
        if not c.get(key) or str(c[key]).startswith("(to be written"):
            print(f"warning: clip {a.id} has no {key} yet; review.py will flag it", file=sys.stderr)

    d.setdefault("capture", {}).setdefault("final", {})[a.id] = {
        "start": a.start, "end": a.end,
        "note": (a.why or c.get("why") or "")[:160],
    }
    save(d)
    print(f"clip {a.id}: {a.start:.1f} -> {a.end:.1f} ({length:.1f}s)")
    print(f"next: FR=60 ./capture.sh SOURCE.mp4 {a.id}")


if __name__ == "__main__":
    main()
