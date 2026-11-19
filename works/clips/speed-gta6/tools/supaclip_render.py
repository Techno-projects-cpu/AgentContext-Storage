#!/usr/bin/env python3
"""Drive the SupaClip skill's renderer from this repo's moment sheets.

SupaClip's pipeline is `extract` (VLM analysis) -> `catalog` -> `stitch render` (EDL -> mp4).
Only the middle step needs a model. This adapter skips the VLM entirely and builds the catalog
directly from a moment sheet, which means SupaClip's own renderer — its 9:16 reframe, its OST
styles, its transitions — is available on a machine with no Ollama, no Ollama key and no network.

    python3 tools/supaclip_render.py --pack gta6-launch --source video.mp4 --out shorts/
    python3 tools/supaclip_render.py --pack speed-gta6 --source stream.mp4 --clip 02

Requires the SupaClip skill to be installed (pip install -e . in a clone of uditdc/supaclip).
If it is not importable, this exits with the install line rather than a traceback.
"""
import argparse, json, os, shutil, sqlite3, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.environ.get("CLIP_PACK") or os.path.dirname(HERE)
try:
    from supaclip.catalog import db as scdb
    from supaclip.catalog.schema import SCHEMA_SQL, CLIPS_FTS_DDL
    HAVE = True
except Exception:
    HAVE = False


def require():
    if HAVE:
        return
    sys.exit("SupaClip is not installed. One command:\n"
             "  git clone https://github.com/uditdc/supaclip && cd supaclip\n"
             "  python -m venv .venv && . .venv/bin/activate && pip install -e .")


def ffprobe(path):
    exe = os.environ.get("FFPROBE") or "ffprobe"
    out = subprocess.run([exe, "-v", "error", "-show_entries",
                          "format=duration:stream=width,height,r_frame_rate", "-of", "json", path],
                         capture_output=True, text=True)
    d = json.loads(out.stdout)
    st = next(s for s in d["streams"] if "width" in s)
    num, _, den = st.get("r_frame_rate", "30/1").partition("/")
    return (float(d["format"]["duration"]), st["width"], st["height"],
            float(num) / float(den or 1))


def build_catalog(source, clips, path):
    """One source, one extract, one row per moment. Scores are the sheet's own."""
    dur, w, h, fps = ffprobe(source)
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.executescript(SCHEMA_SQL)
    c.executescript(CLIPS_FTS_DDL)
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    c.execute("INSERT INTO sources(file_path,fingerprint,duration,resolution,fps,has_audio) "
              "VALUES (?,?,?,?,?,1)", (os.path.abspath(source), "local-" + str(int(time.time())),
                                       dur, f"{w}x{h}", fps))
    sid = c.execute("SELECT id FROM sources").fetchone()[0]
    c.execute("INSERT INTO extracts(source_id,segmenter,analyzer,game_profile,taxonomy_json,"
              "created_at,manifest_path) VALUES (?,?,?,?,?,?,?)",
              (sid, "manual", "hand-picked", "generic", "[]", now, "(built by supaclip_render.py)"))
    eid = c.execute("SELECT id FROM extracts").fetchone()[0]
    ids = {}
    for cl in clips:
        c.execute("INSERT INTO clips(extract_id,clip_local_id,file,source_in,source_out,duration,"
                  "resolution,fps,description,dialogue,score,segment_source) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (eid, cl["id"], os.path.abspath(source), cl["start"], cl["end"],
                   cl["end"] - cl["start"], f"{w}x{h}", fps,
                   cl.get("why") or cl.get("hook", ""), "", int(cl.get("score") or 70), "manual"))
        cid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        ids[cl["id"]] = cid
        c.execute("INSERT INTO clips_fts(rowid,description,dialogue,audio_cues,tags) "
                  "VALUES (?,?,?,?,?)", (cid, cl.get("hook", ""), "", "", "gta"))
    c.commit()
    c.close()
    return ids


def edl_for(clips, ids, fps=30):
    """video + OST from the sheet. No voiceover: these packs are silent by design,
    and SupaClip burns styled on-screen text with no TTS at all."""
    video, ost = [], []
    t = 0.0
    for cl in clips:
        d = round(cl["end"] - cl["start"], 2)
        video.append({"start": round(t, 2), "end": round(t + d, 2), "clip_id": ids[cl["id"]],
                      "source_in": 0.0, "reframe": "crop_center", "effect": "none",
                      "transition_in": "cut", "transition_duration": 0.0})
        if cl.get("hook"):
            ost.append({"start": round(t + 0.15, 2), "end": round(min(t + d, t + 3.6), 2),
                        "text": cl["hook"].upper(), "style": "yellow_punch", "position": "top"})
        t += d
    return {"schema_version": 1, "title": "GTA 6 launch clips",
            "output": {"width": 1080, "height": 1920, "fps": int(fps), "duration": round(t, 2)},
            "video": video, "audio": [], "ost": ost}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=os.path.basename(PACK))
    ap.add_argument("--source", required=True)
    ap.add_argument("--clip", help="one clip id, default all recorded")
    ap.add_argument("--out", default=os.path.join(PACK, "shorts"))
    ap.add_argument("--keep", action="store_true", help="keep the catalog and EDL")
    a = ap.parse_args()
    require()

    sheet = json.load(open(os.path.join(PACK, "candidates.json"), encoding="utf-8"))
    final = sheet.get("capture", {}).get("final", {})
    clips = []
    for c in sheet["candidates"]:
        if c["id"] not in final:
            continue
        if a.clip and c["id"] != a.clip:
            continue
        f = final[c["id"]]
        clips.append({**c, "start": f["start"], "end": f["end"]})
    if not clips:
        sys.exit("no moments recorded in candidates.json (capture.final is empty)")

    work = os.path.join(PACK, "work")
    os.makedirs(work, exist_ok=True)
    os.makedirs(a.out, exist_ok=True)
    cat = os.path.join(work, "supaclip-catalog.db")
    ids = build_catalog(a.source, clips, cat)
    edl = edl_for(clips, ids, fps=sheet.get("style", {}).get("fps", 30))
    edl_path = os.path.join(work, "edl.json")
    json.dump(edl, open(edl_path, "w"), indent=1)
    print(f"catalog: {len(ids)} clip(s) · edl: {edl_path}")

    out = os.path.join(a.out, f"supaclip-{a.clip or 'all'}.mp4")
    cmd = [sys.executable, "-m", "supaclip.stitch.cli", "render", edl_path,
           "-o", out, "--catalog", cat, "--resolution", "1080p", "--encoder", "libx264"]
    print("rendering with SupaClip's own renderer…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    print((r.stdout or "").strip()[-1500:])
    if r.returncode != 0:
        print((r.stderr or "")[-1500:], file=sys.stderr)
        sys.exit(r.returncode)
    if not a.keep:
        for p in (cat, edl_path):
            if os.path.exists(p):
                os.remove(p)
    print(f"done: {out}")


if __name__ == "__main__":
    main()
