# cinematic-skill (Moh4696) — found, read, and run here

**https://github.com/Moh4696/cinematic-skill** · 509 stars · MIT · Python
Author: **exploraX** (GitHub `Moh4696`, X `@exploraX_`). Last push at the time of
writing: 2026-11-09.

> "Agent skill for narrated cinematic films built entirely from code: one
> continuous camera over photos, maps and cards, timed to the voice. Claude Code,
> Codex, Cursor, Gemini CLI."

Install: `npx skills add Moh4696/cinematic-skill` — or the Claude Code plugin
marketplace, the Codex plugin, the Gemini extension, or `install.sh`. Runtime:
`pip install skia-python numpy pillow` (scipy optional) and ffmpeg on PATH.

## What it makes

One continuous camera move over **one designed world**: photos, torn newspaper
clippings, typeset documents with real quotes, clean cards, big distressed type
and rolling counters, stamps, pen circles, highlighter swipes, red string, and
maps of any country with filled regions, routes and markers. Every stamp and
number lands on the narrator's spoken word (`doc.W(line, "word")`), not on the
line boundary. Four looks — `wall`/`slate` (history, true crime),
`studio`/`charcoal` (product, founder), `blueprint`/`paper` (science),
`night` (tech, trailers) — and every item works on every look.

Every frame is drawn by **Skia in Python**, so renders are deterministic, a fix
is cheap, and a new voice re-times the whole film by itself.

Pipeline: `check_setup` → `new_project` → `make_beats` (a beat table with a
chronology lint, for your approval) → `tts_say`/`split_takes`/`build_narration`
(voice, split into timed lines) → `fetch_commons` (Wikimedia, licences recorded,
non-free refused) → `make_map` → `prep_assets` (one grade across all images +
board textures) → `scene.py` → `render` → `build_sfx` + `mix_soundtrack` →
`burn_captions`. It stops for approval at four gates: beat table, look, 30 s draft.

## Verified here, not just read

It runs in this container, which has **no libEGL/libGL, no libglvnd, no apt
network, and an ffmpeg without ffprobe**. Fixes that made it work:

- `skia-python` binds 110 GL/EGL symbols at import even though every path used is
  raster. Built a stub `libGL.so.1` / `libEGL.so.1` with gcc exposing exactly
  those symbols → `import skia` succeeds and draws.
- ffmpeg from `imageio-ffmpeg`; **ffprobe** from the npm package
  `ffprobe-static` (the static-ffmpeg route is Git-LFS-blocked here).
- Fonts: only DejaVu is installed, so `cond` and `hand` fall back — run
  `get_fonts.py` on a machine with GitHub reachable (it failed here: TLS reset).
- `check_setup.py` then reports **ready**.

End-to-end proof: starter project → synthesised stand-in voice takes →
`split_takes` → `build_narration` → `prep_assets` → `render`.

| Measured | Value |
|---|---|
| Output | 28.6 s, 720×1280, 859 frames, H.264 + AAC, 31.8 MB |
| Render time | 117 s (~7.3 fps on the one worker this box allows) |
| Narration chain | 6 lines, 21.6 s speech + 7.05 s pauses, tempo 1.0000 |

The README claims a 92 s film at 1080p in ~6 min on a 16 GB laptop — consistent.

## Why it is relevant to this repo

It is the packaged version of what the SR-71 short in `works/films/influx-sample`
does by hand: code-drawn frames, deterministic re-renders, timing locked to a
voice. What it adds is the part that was manual here — a single designed world
with a travelling camera, synthesised SFX from the cue list, a ducked and
loudness-normalised mix, four caption styles and an SRT.

Its rules line up with ours: one hero per line, hits land on the spoken word,
type readable on a phone in one second, nothing invented that looks real, credits
for archive images, and clear schematics over fake photorealism.

## Caveats

- The **demo is not a film**: the voice is a stand-in buzz so the timing chain
  could be exercised; no real narration, no researched script, no photographs.
- `get_fonts.py` and `fetch_commons.py` need GitHub/Wikimedia reachable; neither
  worked from here.
- Not vendored. This directory is a review, not a copy — the repo is MIT, but the
  engine is 75 KB of Python that belongs upstream.
