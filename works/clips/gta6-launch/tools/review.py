#!/usr/bin/env python3
"""Build a review page for the GTA 6 launch clips.

    python3 tools/review.py                      # page from candidates.json (+ any rendered clips)
    python3 tools/review.py --check              # also verify candidates.json against the rubric

The page is self-contained: it embeds the clip files as base64 when they exist, so it can be
opened from disk, sent as a file, or served anywhere without a bundle. When a clip has not
been rendered yet the card shows the hook, the verbatim start and end lines, and why it scored
what it scored, so the selection can be made before a single frame is cut.
"""
import argparse, base64, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOFT_MIN, SOFT_MAX, HARD_MAX = 15, 45, 60
STOP = set("a an the of to for and that with on in is so but i or at as if by from my your our it "
           "you we they this these those be was were do does did not no".split())


def load():
    cand = json.load(open(os.path.join(ROOT, "candidates.json"), encoding="utf-8"))
    return cand


def check(cand):
    problems, notes = [], []
    src = cand["source"]
    seen = []
    for c in cand["candidates"]:
        cid = c["id"]
        length = c["end"] - c["start"]
        score = c["score"]
        if not (SOFT_MIN <= length <= HARD_MAX):
            problems.append(f"clip {cid}: {length:.1f} s is outside 15-60 s")
        elif length > SOFT_MAX and score < 85:
            notes.append(f"clip {cid}: {length:.1f} s is over the 45 s default and scores {score}, "
                         f"so trim it under 45 s")
        elif length > 40 and score < 85:
            notes.append(f"clip {cid}: {length:.1f} s needs a turn around 15 s and 30 s to hold "
                         f"(rubric, clips over 40 s)")
        if not 3 <= len(c["hook"].split()) <= 8:
            problems.append(f"clip {cid}: hook is {len(c['hook'].split())} words, needs 3-8")
        if len(c["title"]) > 70:
            problems.append(f"clip {cid}: title is {len(c['title'])} chars, YouTube Shorts cuts at 70")
        # the rubric's rule is about content words; sharing "the" or "a" with the dialogue is fine
        spoken = {w for w in open_words(c["start_line"] + " " + c["end_line"]) if w not in STOP}
        hook = {w for w in open_words(c["hook"]) if w not in STOP}
        if spoken & hook:
            notes.append(f"clip {cid}: hook repeats spoken words ({', '.join(sorted(spoken & hook))}); "
                         f"the rubric warns the hook must not say what the clip is about to say")
        for other in seen:
            if not (c["end"] <= other["start"] or c["start"] >= other["end"]):
                problems.append(f"clip {cid} overlaps clip {other['id']}")
        seen.append(c)
        for a, b in c.get("cuts", []):
            if not (c["start"] < a < b < c["end"]):
                problems.append(f"clip {cid}: cut {a}-{b} is outside the clip")
    if src.get("timing_confidence") != "word":
        notes.append("timings are approximate (+/-2 s): every clip must be snapped to real word "
                     "timings before it is rendered")
    return problems, notes


def open_words(s):
    import re
    return re.findall(r"[a-z']+", s.lower())


def fmt(t):
    m, s = divmod(int(round(t)), 60)
    return f"{m}:{s:02d}"


def media(cid):
    for name in (f"clip-{cid}.mp4", f"clip-{cid}-540.mp4"):
        p = os.path.join(ROOT, "shorts", name)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return "data:video/mp4;base64," + base64.b64encode(f.read()).decode(), p
    return None, None


CARD = """
<article class="card">
  <div class="video">{video}</div>
  <div class="meta">
    <div class="row">
      <span class="id">CLIP {id}</span>
      <span class="score s{band}">{score}</span>
      <span class="len">{length:.1f}s &middot; {a} &rarr; {b}</span>
    </div>
    <h2>{hook}</h2>
    <p class="title">{title}</p>
    <p class="caption">{caption}</p>
    <dl>
      <dt>starts on</dt><dd>&ldquo;{start_line}&rdquo;</dd>
      <dt>ends on</dt><dd>&ldquo;{end_line}&rdquo;</dd>
      <dt>why</dt><dd>{why}</dd>
    </dl>
  </div>
</article>
"""


def page(cand, notes):
    cards = []
    for c in cand["candidates"]:
        data, path = media(c["id"])
        if data:
            cover = os.path.join(ROOT, "shorts", f"clip-{c['id']}-cover.jpg")
            poster = ""
            if os.path.exists(cover):
                with open(cover, "rb") as f:
                    poster = (' poster="data:image/jpeg;base64,'
                              + base64.b64encode(f.read()).decode() + '"')
            video = (f'<video controls playsinline preload="metadata"{poster}>'
                     f'<source src="{data}" type="video/mp4"></video>')
        else:
            video = ('<div class="pending"><span>not cut yet</span>'
                     '<small>needs the source file, see README</small></div>')
        band = "hi" if c["score"] >= 85 else ("mid" if c["score"] >= 70 else "lo")
        cards.append(CARD.format(
            video=video, id=c["id"], score=c["score"], band=band,
            length=c["end"] - c["start"], a=fmt(c["start"]), b=fmt(c["end"]),
            hook=html.escape(c["hook"]), title=html.escape(c["title"]),
            caption=html.escape(c["caption"]), start_line=html.escape(c["start_line"]),
            end_line=html.escape(c["end_line"]), why=html.escape(c["why"])))
    src = cand["source"]
    rejected = "".join(f"<li><b>{html.escape(r['ref'])}</b> &mdash; {html.escape(r['why'])}</li>"
                       for r in cand.get("rejected", []))
    note_html = "".join(f"<li>{html.escape(n)}</li>" for n in notes)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GTA 6 launch clips &mdash; review</title>
<style>
 :root {{ --red:#E8312A; --ink:#0d0d0f; --paper:#f6f4ef; --mute:#8a8579; }}
 * {{ box-sizing:border-box; }}
 body {{ margin:0; background:var(--paper); color:var(--ink);
        font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
 header {{ padding:48px 24px 28px; max-width:1180px; margin:0 auto; }}
 .kicker {{ font:700 12px/1 ui-monospace,monospace; letter-spacing:.18em;
            text-transform:uppercase; color:var(--red); }}
 h1 {{ font-size:clamp(28px,4vw,44px); line-height:1.05; margin:.35em 0 .3em; letter-spacing:-.02em; }}
 .sub {{ color:var(--mute); max-width:62ch; }}
 .sub b {{ color:var(--ink); font-weight:600; }}
 main {{ max-width:1180px; margin:0 auto; padding:0 24px 64px;
         display:grid; gap:22px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }}
 .card {{ background:#fff; border:1px solid #e6e2d8; border-radius:14px; overflow:hidden;
          display:flex; flex-direction:column; box-shadow:0 1px 2px rgba(0,0,0,.04); }}
 .video {{ background:#0d0d0f; aspect-ratio:9/16; max-height:520px; display:grid; place-items:center; }}
 .video video {{ width:100%; height:100%; object-fit:contain; }}
 .pending {{ display:grid; gap:6px; place-items:center; color:#5c5850; text-align:center;
             font:600 13px/1.4 ui-monospace,monospace; letter-spacing:.08em; text-transform:uppercase; }}
 .pending small {{ color:#6f6a60; font:400 11px/1.5 ui-sans-serif,system-ui,sans-serif;
                   letter-spacing:0; text-transform:none; max-width:22ch; }}
 .meta {{ padding:16px 18px 20px; display:grid; gap:8px; }}
 .row {{ display:flex; align-items:center; gap:10px; font:600 11px/1 ui-monospace,monospace;
         letter-spacing:.12em; color:var(--mute); }}
 .score {{ padding:4px 8px; border-radius:999px; color:#fff; letter-spacing:.04em; }}
 .score.hi {{ background:var(--red); }} .score.mid {{ background:#a8802a; }} .score.lo {{ background:#777; }}
 .len {{ margin-left:auto; letter-spacing:.04em; }}
 h2 {{ margin:0; font-size:19px; line-height:1.25; letter-spacing:-.01em; }}
 .title {{ margin:0; color:#4b4740; font-size:14px; }}
 .caption {{ margin:2px 0 0; font-size:13px; color:#5d584f; background:#faf8f3;
             border-left:3px solid var(--red); padding:8px 10px; border-radius:0 6px 6px 0; }}
 dl {{ margin:6px 0 0; display:grid; grid-template-columns:auto 1fr; gap:4px 10px;
       font-size:13px; align-items:start; }}
 dt {{ font:600 10px/1.6 ui-monospace,monospace; letter-spacing:.1em; text-transform:uppercase;
       color:var(--mute); }}
 dd {{ margin:0; color:#33302b; }}
 footer {{ max-width:1180px; margin:0 auto; padding:0 24px 72px; color:var(--mute); font-size:14px; }}
 footer h3 {{ font:700 12px/1 ui-monospace,monospace; letter-spacing:.14em; text-transform:uppercase;
              color:#5d584f; margin:28px 0 10px; }}
 footer ul {{ margin:0; padding-left:18px; }}
 footer li {{ margin:6px 0; }}
 .warn li {{ color:#8a3320; }}
</style></head>
<body>
<header>
  <div class="kicker">Launch day &middot; 19 Nov 2026</div>
  <h1>GTA 6 is out. Here is what to clip.</h1>
  <p class="sub">Five moments from <b>{html.escape(src['title'])}</b>
  &mdash; {html.escape(src['channel'])}, {fmt(src['duration_s'])} &mdash; scored against the
  video-to-shorts rubric. Nothing posts without a yes, and the source is someone else&rsquo;s
  video, so the credit line stays in every caption.</p>
</header>
<main>{''.join(cards)}</main>
<footer>
  <h3>Checked before cutting</h3>
  <ul class="warn">{note_html}</ul>
  <h3>Left out on purpose</h3>
  <ul>{rejected}</ul>
</footer>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cand = load()
    problems, notes = check(cand)
    out = os.path.join(ROOT, "review.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(cand, notes))
    n_ready = sum(1 for c in cand["candidates"] if media(c["id"])[0])
    print(f"{out}  ({n_ready}/{len(cand['candidates'])} clips rendered)")
    if problems:
        print("rubric failures:")
        for p in problems:
            print("  - " + p)
    for n in notes:
        print("note: " + n)
    if a.check and problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
