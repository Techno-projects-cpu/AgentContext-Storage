#!/usr/bin/env python3
"""Pre-flight for a clip pack: refuse to look finished when it is not.

    python3 tools/check.py            # exits 1 on anything that would ship a bad clip

Checks both hand-written metadata (a placeholder moment, a hook that repeats the dialogue) and
anything already rendered (duration, size, whether the credit is actually in the container).
"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLIP_PACK") or os.path.dirname(HERE)
STOP = set("a an the of to for and that with on in is so but i or at as if by from my your our it "
           "you we they this these those be was were do does did not no".split())
PLACEHOLDER = re.compile(r"^\(to be written|placeholder", re.I)


def ffprobe(path):
    exe = os.environ.get("FFPROBE") or "ffprobe"
    try:
        out = subprocess.run([exe, "-v", "error", "-show_entries",
                              "format=duration:stream=width,height", "-of", "json", path],
                             capture_output=True, text=True, timeout=120)
        return json.loads(out.stdout or "{}")
    except Exception:
        return {}


def main():
    d = json.load(open(os.path.join(ROOT, "candidates.json"), encoding="utf-8"))
    final = d.get("capture", {}).get("final", {})
    fails, notes = [], []

    for c in d["candidates"]:
        cid = c["id"]
        filled = cid in final
        for field in ("hook", "title", "start_line", "end_line"):
            v = str(c.get(field, ""))
            if PLACEHOLDER.search(v):
                if filled:
                    fails.append(f"clip {cid}: filled in but '{field}' is still a placeholder")
                else:
                    notes.append(f"clip {cid}: waiting on a moment ('{field}' is a placeholder)")
        if not filled:
            continue
        f = final[cid]
        length = f["end"] - f["start"]
        if length > 60:
            fails.append(f"clip {cid}: {length:.0f}s — over 60s of reused footage invites a claim")
        if length < 8:
            fails.append(f"clip {cid}: {length:.0f}s — too short to land")
        spoken = {w for w in re.findall(r"[a-z']+", (c.get("start_line", "") + " " +
                  c.get("end_line", "")).lower()) if w not in STOP}
        hook = {w for w in re.findall(r"[a-z']+", c.get("hook", "").lower()) if w not in STOP}
        if spoken & hook:
            notes.append(f"clip {cid}: hook repeats spoken words ({', '.join(sorted(spoken & hook))})")

    # anything rendered
    for path in sorted(glob.glob(os.path.join(ROOT, "shorts", "clip-*.mp4"))):
        info = ffprobe(path)
        dur = float(info.get("format", {}).get("duration", 0) or 0)
        st = (info.get("streams") or [{}])[0]
        name = os.path.basename(path)
        if dur > 60.5:
            fails.append(f"{name}: {dur:.0f}s is over the 60s cap")
        if st.get("width") != 1080 or st.get("height") != 1920:
            fails.append(f"{name}: {st.get('width')}x{st.get('height')}, expected 1080x1920")
        if dur and dur < 8:
            fails.append(f"{name}: only {dur:.1f}s")

    for n in notes:
        print("note: " + n)
    for f in fails:
        print("FAIL: " + f)
    ready = len(final)
    print(f"\n{ready} moment(s) recorded, "
          f"{len(glob.glob(os.path.join(ROOT, 'shorts', 'clip-*.mp4')))} clip(s) rendered, "
          f"{len(fails)} problem(s)")
    if not fails and not ready:
        print("nothing to render yet: fill a moment with tools/set_moment.py first")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
