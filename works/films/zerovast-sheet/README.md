# ZERO VAST — "Sheet" (no voiceover)

26.5 s, 1080×1920, 30 fps. The site drawn as a **building on a cyanotype drawing sheet**, plotted
line by line in front of you.

| | |
|---|---|
| Style | `claude-drawing-skill` blueprint engine — single-stroke draughting lettering, hatched sections, dimension strings, title block, red wax pencil |
| Artwork | `tools/plates_bp.py` → one 1600×2844 sheet (1600 px wide, 3× supersampled), eight cumulative plot stages |
| Camera | one framing per shot, **hard cut**, six scales — the rostrum holds and the plot front does the moving |
| Type | two registers only: a cream clause, and the sheet's own wording under it in small caps |
| Track | `audio/score.wav` — 92 bpm, hits on every cut (`_shared/eng/make_track.py`) |
| Mix | `audio/mix.m4a` — music + sfx, −15 LUFS (`_shared/eng/mix_novo.py`) |

Rebuild:

```bash
export CF_ENGINE=/tmp/cs/cinematic-skill/skills/cinematic-film/scripts
/tmp/py tools/plates_bp.py --out assets/plates      # ~16 s, owns the look
SCENE=scene.py /tmp/py tools/render2.py --project . --cues
/tmp/py $CF_ENGINE/build_sfx.py --project .
/tmp/py ../_shared/eng/mix_novo.py --project .
SCENE=scene.py /tmp/py tools/render2.py --project . --size 1080x1920 --audio audio/mix.m4a \
    --out out/final.mp4 --workers 2                  # ~120 s
```

Facts on the sheet are all from zero-vast.vercel.app: hand-written HTML/CSS/JS, LCP/CLS/INP budgets
set before the first line, WCAG 2.2 AA, brief → scope → build → handover with repo and walkthrough,
Khammam Telangana, one point of contact. No prices, no client counts, no invented metrics. The
"schedule" is the site's own four stages, given the days a drawing sheet would give them.

## What this one taught the shared library

* **A dark sheet on a dark desk loses its edge.** The print has to be a lit object: a linen border, a
  drop shadow, and a corner light — otherwise the frame is a flat blue rectangle.
* **Wide shots have a hard geometry limit.** At zoom `z` the frame covers `1080/z × 1920/z` sheet
  units; if any shot is wider than 1600×2844 the desk shows through and the illusion breaks.
* **Re-rendering the artwork per frame is impossible** (16 s a stage). Drawing the last cumulative
  stage and running a plot front down it is free, and reads the same at 30 fps.
* Type never touches the drawing: one soft shadow-to-black gradient under the caption, no plaque.
