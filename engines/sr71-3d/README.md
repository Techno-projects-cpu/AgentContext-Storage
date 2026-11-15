# sr71-3d — a software 3D renderer that runs without a GPU

`works/films/influx-sample` was rendered with these files. There is no WebGL in
this container (ANGLE/SwiftShader cannot initialise — no Vulkan loader, no Mesa),
so this rasterises triangles in NumPy instead of faking depth with CSS.

| file | what it is |
|---|---|
| `engine.py` | rasteriser: perspective projection, z-buffer, crease-aware smooth normals with Gouraud interpolation, Blinn-Phong + fake studio environment, three-light rig, rim emission for hot edges, bloom, ACES-ish tone map, vignette, per-frame grain |
| `model.py` | the subject: a Catmull-Rom-resampled superellipse hull, seam hoops and spine seams generated *on* that hull, chine, delta wing, nacelles with spikes and lips, canted tails, canopy, titanium plates with rivets, fuel drops, TEB plumes |
| `frame.py` | auto-framing — solves distance by bisection so the *projected* subject spans a given fraction of frame WIDTH, then walks the look-at point until it sits where asked; particles are excluded from the fit |
| `overlay.py` | the flat layer: overline/headline/note stack, HUD, leader-line labels, gradient scrim, heat haze |
| `shots.py` | the whole edit: one dict per shot, each with a camera rig, an orbit delta and the copy |
| `render.py` | frame loop → raw RGB → ffmpeg; `--still` renders one frame for inspection |
| `audio.py` | deterministic sound bed: low drone, a hit on every cut, risers, a bell for the green flash |

## The rule that made this fast to iterate

**Every frame is a pure function of time.** No clock, no unseeded RNG, no
timeline state. `--still 12.4` renders the exact frame at 12.4 s, so camera and
type fixes are checked in a second instead of a render. The whole film was tuned
this way; the 71-minute master was rendered once.

## Engine v2 — what changed after the first film

The first cut shipped, then got re-reviewed and rebuilt, because two things were
wrong *underneath* the look:

1. **Smoothness.** The hull was 8 sections per ring with hard facet edges; it read
   as 2004. `engine.py` now averages incident face normals per triangle corner and
   keeps them hard where the crease exceeds 42°, then interpolates colour across
   every triangle. The hull itself is resampled from 15 stations to ~45 with
   Catmull-Rom. Wing leading edges and plate corners stay sharp.
2. **The mechanism was faked.** The plate gap and the seam gaps are now real
   parameters of the mesh geometry, driven per shot — so "it seals itself"
   actually shows the joint closing. Skin expansion lifts the hull along its own
   normal and every seam rides with it.
3. **Framing was guessed.** It is now measured: the distance solve is a bisection
   on projected width, the vertical placement is walked to a target, and a
   precomputed `hold` keeps the camera still while the mechanism moves — a camera
   that keeps re-fitting a shrinking object drifts back and gives the reveal away.

## Numbers that matter (measured on 2 vCPU)

- 1080×1920 at `--ss 2` (2× supersample, LANCZOS downsample): **3.3–4.6 s/frame**
- 1080×1920 at `--ss 1`: **0.9 s/frame**
- 540×960 at `--ss 1` for previews: **~2.0 s/frame** at 12 fps
- the 51.0 s film at 24 fps = 1224 frames ≈ **80 minutes**, rendered as eight
  per-shot segments and concatenated. Two shots were re-rendered at ss 2 when
  the plate framing changed; that is the cheapest unit of rework.
- 11 max-render minutes is not a typo either side of these numbers: per-shot
  segmenting plus `-c copy` concat means a bad beat costs one shot, not the film.

## Traps this cost, in order

1. **Metal renders black without an environment.** Direct lights alone give a
   black aircraft on black. Sample a fake studio (cool sky, hot horizon band,
   dark floor) along the reflection vector and weight it by metalness — that is
   what makes the fuselage read as titanium instead of plastic.
2. **Salmon skin.** Mixing a hot body colour with ember emission produced a
   pink aircraft. Heat belongs in the *lighting* (warm key, ember fill) and a
   faint emission, not in the base colour.
3. **Stills are not motion.** A shot can look perfect as a frame and be frozen
   for two seconds — sampling with `tblend=difference` catches it. Three separate
   freezes were found this way, including one where a plate started off-frame and
   only entered after 1.5 s.
4. **Text metrics must be measured, not guessed.** Headline, overline and note
   collided until each block measured itself and drew downward from a computed
   top. Notes wrap; headlines shrink to fit the column; labels flip side rather
   than clipping.
5. **Everything must scale from frame width.** A 540px preview that is not a
   faithful reduction is worthless for review — sizes, tracking and leader lines
   are all multiplied by `W / 1080`.
