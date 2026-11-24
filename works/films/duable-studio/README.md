# Duable — the studio film

`05-duable-studio-1080x1920.mp4` · 20.4 s · 1080×1920 · 30 fps · H.264 + AAC ·
**score + narration, mastered to -14 LUFS**

`05-duable-studio-1080x1920-music-only.mp4` — the same picture, score only, for
anyone cutting against it.

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

## Sound

Three layers, all synthesised or recorded here — no samples, no stock library.

**`score.py` — the music.** Six-partial felted piano, an inharmonic celesta, a
filtered pad, a lowpassed bass voice and a soft felt thump, sent through a
synthetic convolution plate. The harmony turns where the picture cuts:

| time | harmony | what enters |
|---|---|---|
| 0.0 | Am9 | one arpeggio, wide room, nothing to prove |
| 3.2 | Fmaj7 → G6 | the pulse arrives, still soft |
| 7.6 | Dm7 → Em7 | bells over the turning object |
| 11.2 | Cmaj7 → Am7 → Fmaj7 | the fullest bar of the film |
| 15.6 | G → Am9 | resolve, ring out, one last bell |

The melodic material is one four-interval motif (`root, 2, 3, 1` of the chord)
transposed across every section. Measured after mixing: 17 % bass, 50 % mid,
centroid 543 Hz, stereo side/mid 0.24 — deliberately narrow, because a phone
speaker folds to mono and a wide bed phase-cancels.

**`vo/` — the narration.** Five lines, one per shot, recorded per line so each
can be placed against its own picture beat:

> A studio with a service for that. · Twenty-four services, in four categories.
> · Eight. Four. Five. Seven. · Design. Automate. Edit. Position. · Duable
> Industries. Independent creative technology studio.

Every line is the site's own copy. There is no invented claim in the film, spoken
or written.

**`mix.py` — the mix.** Trims and normalises each line (two of the five came back
17 dB quieter than the rest — a gain problem, not a performance problem),
sidechain-ducks the score by the *measured* speech envelope, puts a short plate
on the voice so it shares the piano's room, then bus-compresses and masters by
measuring with ffmpeg's BS.1770 meter rather than trusting an estimate.

### Two audio bugs worth remembering

1. `(-3.0) ** 0.85` is **complex** in Python. A loudness-correction loop that
   multiplied by a negative base raised to a fractional power silently wrote
   complex samples into the wav. Keep the exponent outside the sign.
2. My analytic loudness estimate read **3.5 dB optimistic** (-14.0 claimed,
   -10.5 measured). Aiming with it shipped an over-loud master. The fix was to
   stop guessing: write the wav, measure it with `ebur128`, correct.

## Build

```bash
bash tools/skia_stubs.sh /tmp/gl        # CPU skia still links libEGL/libGL
cd source
LD_LIBRARY_PATH=/tmp/gl python3 film.py --still 9.6
LD_LIBRARY_PATH=/tmp/gl python3 film.py \
    --out ../05-duable-studio-1080x1920.mp4 \
    --clean-out ../05-duable-studio-1080x1920-music-only.mp4

python3 score.py --out /tmp/score.wav      # music alone
python3 mix.py   --out /tmp/mix.wav        # score + voice, mastered
```

## QC

`tooling/qc.py --safe 0.90` → **10/10**, motion in 13/13 sampled intervals,
`audio_has_voice` false on the music-only cut and true on the narrated one,
measured -14.1 and -14.0 LUFS. The voice detector is envelope energy at speech
rate (1.5–9 Hz), not level spread: a bed with a hit on every cut also swings
20 dB and used to pass.
