# Duable — the kinetic film

`04-duable-kinetic-1080x1920.mp4` · 22.4 s · 1080×1920 · 30 fps · H.264 + AAC · no voiceover

Built **on skia** — the same canvas the brag films in this repo draw on
(`works/films/_shared/eng/`) — with real type shaping, gradients, masks and arcs,
and a cut-based camera. Not cards held on screen: every shot has continuous
movement behind and inside it.

---

## The seven shots

| # | Time | Shot | What actually moves |
|---|---|---|---|
| 01 | 0.0–3.2 | **The number** | 24 counts up and decelerates; 8/4/5/7 arrive one beat each; rule sweeps |
| 02 | 3.2–6.8 | **The menu** | four category rows **scroll up through a fixed reading line**, focusing as they pass |
| 03 | 6.8–10.4 | **The services** | the real 24-item list runs past like credits and **accelerates**; headline swaps mid-shot |
| 04 | 10.4–13.6 | **Four steps** | a track the camera travels down; a rider runs the rail; steps light as it passes |
| 05 | 13.6–16.4 | **The split** | four columns **grow continuously**, each count ticking up with its bar |
| 06 | 16.4–19.4 | **Honest** | a strike draws across NUMBERS; a note drops into a box that never opens |
| 07 | 19.4–22.4 | **The end** | rings sweep, a satellite orbits, the URL underlines itself |

Six hard cuts. One camera idea per shot (push, scroll, travel, grow). The ground
drifts at 0.6–1.4× the camera's speed, so the frame has parallax instead of one
flat plane.

## What changed after the first cut, and why

The first version **was** a slideshow, and a frame strip proved it: shots 2–5 were
byte-identical for four seconds after their entrances. The fix was structural, not
cosmetic:

1. **Every shot now has a subject that moves continuously** — a scroll, a travel,
   a growth, a count. An entrance is a beginning, not the whole shot.
2. **Copy arrives in pieces.** Headline, sub-line and note land on separate beats,
   and one shot (03) swaps its headline halfway through.
3. **The camera travels.** `dz`/`dy` per shot, capped at a 4.5 % push — a zoom moves
   margin content outward by `(W/2 − M)(z − 1)`, so anything above ~6.5 % crops the
   frame. That budget is why the push is small and the *internal* motion is large.
4. **The split got its own shot.** The numbers were carrying the story from a
   corner; now four columns grow and count for three seconds.

## The floor, as code

From `agent-context/BRAG-PROMPT.md`, enforced in `source/kit.py` rather than
remembered:

- type floor 30 px (`TYPE_FLOOR`, applied in `font()`)
- entrances 0.45 s, expo/power4 out (`mask_reveal`, `stagger_words`)
- frame 0 inked — the count starts at 00 and the camera is already moving
- one camera idea per shot, cuts not tweens
- every frame a pure function of `t` — `film.py --still 12.4` is exact

## Facts

Every string is the site's own: the 24 services **in the site's order**, the four
category names with counts 8/4/5/7, the four process steps, "without promising
magic numbers", the project-note privacy line, the H1. Site:
`https://duableindustries.vercel.app` (verified through the Vercel connector,
prod `dpl_D7puXA4semWYFT7Nz3qXDoNKLxWp`, `READY`).

No prices, no client counts, no testimonials, no invented metrics.

## Build

Needs a CPU-raster skia (the wheel still links `libEGL`/`libGL`, so stub libs go on
the loader path — see `tools/skia_stubs.sh`) and a real ffmpeg with libx264:

```bash
bash tools/skia_stubs.sh                      # writes /tmp/gl/lib{EGL,GL}.so.1
cd source
LD_LIBRARY_PATH=/tmp/gl python3 film.py --still 12.4        # one frame
LD_LIBRARY_PATH=/tmp/gl python3 film.py --out ../04-duable-kinetic-1080x1920.mp4
```

`--scale 0.5` renders a faithful half-size preview in ~30 s (the canvas scales, so
the layout is identical).

## QC

`tooling/qc.py --safe 0.90` → **9/9**: 22.40 s · aac, rms −16.5 dB · frame 0 inked
2.87 % · no edge cropping · 28 px type floor · contrast ≥ 3:1 · no black dip ·
**motion in 13/13 sampled intervals**.

Two QC failures were fixed at source rather than by loosening the gate: the HUD was
sitting at y=80 (inside the 54 px safe inset) and the menu's focus-scaling number
drifted 40 px *left* of the margin as it passed. Both were geometry bugs, not
taste.

---

### Note on the earlier attempts

`works/films/duable-vector-ad/` is a 3D vector-geometry attempt (the sr71
rasteriser) that was abandoned mid-build: it renders fine but the camera work was
weak and the film read as slides. `works/films/duable-ads/` holds the two earlier
typographic ads. This folder is the film.
