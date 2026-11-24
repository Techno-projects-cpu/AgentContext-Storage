# Duable — the studio film

`05-duable-studio-1080x1920.mp4` · 19.6 s · 1080×1920 · 30 fps · H.264 + AAC · no voiceover

Minimal, editorial, and built from **three engines in one pipeline**:

| engine | what it contributes |
|---|---|
| `engines/sr71-3d` — NumPy software rasteriser | the hero object: 24 plates in four stacks (8 / 4 / 5 / 7), lit and turned in real 3D |
| `works/films/_shared/eng` — the brag kit's canvas | the type layer: skia, real glyph shaping, masks, arcs, hairlines |
| `engines/brag` under `agent-context/BRAG-PROMPT.md` | the grammar: the craft floor and the shot discipline |

There is no browser in this sandbox, so the brag *HTML* template cannot render. Its
canvas can: `works/films/_shared/eng/*` draws on skia, and `source/kit.py` here is a
compact re-implementation of that same kit — Instrument Serif, Oswald, Space Grotesk
on a porcelain ground, one olive signal, and the floor enforced in code (30 px type,
0.45 s expo entrances, frame 0 inked, one camera idea per shot, every frame a pure
function of `t`).

---

## The five shots

| # | Time | Shot | What moves, every frame |
|---|---|---|---|
| 01 | 0.0–3.2 | **Statement** | serif line rises in two halves; 8/4/5/7 land one per beat; an olive rule travels the page |
| 02 | 3.2–7.6 | **The menu** | all 24 service names run upward past a fixed index rail, sharpest at the reading line |
| 03 | 7.6–11.2 | **The object** | the 3D stacks turn on a turntable for the whole shot; plate #20 is olive |
| 04 | 11.2–15.6 | **Four ways in** | four chapters land; a marker walks the list and grows the live count |
| 05 | 15.6–19.6 | **The close** | hairlines converge, a ring sweeps, a second arc keeps turning, URL underlines |

## Things that were actually hard

1. **The 3D plate kept showing a rectangle.** Three attempts at alpha cut-outs
   leaked (premultiplication, stray grain, sampling). The fix was to stop cutting:
   normalise the render so its paper is pure white, then composite with
   **multiply**. White leaves the page untouched, so no rectangle can exist.
2. **A bbox fit pumps.** Fitting the cut-out to its bounding box rescales every
   frame as the stacks turn, which reads as the object breathing. It is placed on a
   fixed rect now and the rotation happens inside it.
3. **A vignette on porcelain looks like dirt.** The post pass applies grain always
   and the vignette only to the dark shot.
4. **`str.replace` silently no-opped** during one edit round, so tuning was landing
   on a stale build. Worth remembering: verify the edit, not the intent.

## Facts

The four chapter kickers and headlines are the site's own category pages:
`01 / DESIGN — "Digital foundations, built for real use."`,
`02 / AUTOMATE — "Use AI where it earns its place."`,
`03 / EDIT — "Make the story and visuals feel connected."`,
`04 / POSITION — "Say what matters. Reach who matters."`
Counts 8 / 4 / 5 / 7 and the 24 service names are the site's, in its order.
No prices, no client counts, no testimonials.

## Build

```bash
bash tools/skia_stubs.sh /tmp/gl        # CPU skia still links libEGL/libGL
cd source
LD_LIBRARY_PATH=/tmp/gl python3 film.py --still 9.6
LD_LIBRARY_PATH=/tmp/gl python3 film.py --out ../05-duable-studio-1080x1920.mp4
```

## QC

`tooling/qc.py --safe 0.90` → **9/9**, motion in 13/13 sampled intervals.
