# sr71-3d — a software 3D renderer that runs without a GPU

`works/films/influx-sample` was rendered with these files. There is no WebGL in
this container (ANGLE/SwiftShader cannot initialise — no Vulkan loader, no Mesa),
so this rasterises triangles in NumPy instead of faking depth with CSS.

| file | what it is |
|---|---|
| `engine.py` | rasteriser: perspective projection, z-buffer, Blinn-Phong + fake studio environment, three-light rig, bloom, ACES-ish tone map, vignette, grain |
| `model.py` | the subject: ~40 primitives (faceted fuselage, chined body, delta wing, nacelles, canted tails), panel seams, titanium plates, fuel drops |
| `frame.py` | auto-framing — backs the camera off until the *projected* subject fills the frame, rather than fitting a bounding sphere (which wastes a portrait frame) |
| `overlay.py` | the flat layer: overline/headline/note stack, HUD, leader-line labels, gradient scrim, heat haze |
| `shots.py` | the whole edit: one dict per shot, each with a camera rig, an orbit delta and the copy |
| `render.py` | frame loop → raw RGB → ffmpeg; `--still` renders one frame for inspection |
| `audio.py` | deterministic sound bed: low drone, a hit on every cut, risers, a bell for the green flash |

## The rule that made this fast to iterate

**Every frame is a pure function of time.** No clock, no unseeded RNG, no
timeline state. `--still 12.4` renders the exact frame at 12.4 s, so camera and
type fixes are checked in a second instead of a render. The whole film was tuned
this way; the 71-minute master was rendered once.

## Numbers that matter

- 1080×1920 at `--ss 2` (2× supersample, downsampled with LANCZOS): **3.7 s/frame**
- 540×960 at `--ss 1` for previews: **~0.2 s/frame**
- the full 48.5 s film at 24 fps = 1164 frames = **71 minutes**

If that is too slow: render at `--ss 1` (three times faster, slightly aliased
edges) or cut the frame rate to 24 only where it matters. Do not drop resolution;
1080×1920 is the floor for a vertical upload.

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
