# ZeroVast ad series — five cuts, five media, one set of facts

| # | project | length | medium | how it moves | sound |
|---|---|---|---|---|---|
| 1 | `zerovast-ad` | 34.9 s | gouache cut-outs, four painted sets | staged cuts + kinetic captions | **voice** + score |
| 2 | `zerovast-type` | 22.0 s | kinetic type, nine grounds | cuts on the beat, hard type entrances | music only |
| 3 | `zerovast-sheet` | 26.5 s | cyanotype drawing sheet | the sheet plots itself; camera cuts to six scales | music only |
| 4 | `zerovast-deco` | 23.0 s | 1930s airbrushed poster | the poster paints itself; camera walks into it | music only |
| 5 | *(vignan-ad, separate client)* | 26.6 s | gouache, page-cited answers | staged cuts | voice + score |

Contact sheet of the four ZeroVast cuts: `_shared/series_review.png`.

Rules held by all of them:

* Nothing invented. Every on-screen claim is on `zero-vast.vercel.app`; the address is on the end card.
* 1080×1920, 30 fps, −15 LUFS, deliverables `preview_540.mp4` per project.
* Each film invents its own palette, type treatment and background language (bang-motion's rule: no
  reusing a previous project's skin).
* Every cut in the four new films is also a hit in the score, and no transition is a flat colour slab.

## Shared engines added for the no-voiceover films

* `_shared/eng/make_track.py` — synthesised percussive bed: kick/clap/hats/sub/marimba, an energy
  curve in bars, and explicit accents at the cut times.
* `_shared/eng/mix_novo.py` — music + sfx mix at −15 LUFS. `mix_soundtrack.py` ducks the music against
  a voice track, so it cannot mix a film that has no voice.
* `_shared/eng/transitions.py` — whip, card swing, lens leak, banded curtain, push-through. All are
  narrow coverage pulses: a transition that covers the frame for a fifth of a second reads as a cut
  with depth, one that covers it across the whole move reads as five dim frames.

## Defects found and fixed while making the three

1. **Type ramping from zero after a cut** → five dark frames at every beat; the words now arrive at
   88 % and settle in 0.18 s.
2. **Transition envelopes spread over the whole duration** → the incoming shot arrives dim; coverage
   is now a narrow pulse (see above).
3. **Per-line auto-fit in kinetic type** → a two-word line doubles its neighbour; the smallest line
   now sets the block and others grow at most 20–30 %.
4. **A highlighter bar across a one-word line** → reads as a chip; single-word lines take a colour
   accent instead.
5. **Bare paper between painting stages** (deco) and **a bright horizon seam** where two plates meet.
6. **Wide shots on the drawing sheet** showing the desk through the frame: at zoom `z` the frame is
   `1080/z × 1920/z` sheet units, so every wide shot is checked against the sheet's own rectangle.
7. **A camera that glides between shots** on a document film makes a legible sheet illegible: the
   rostrum now hard-cuts and holds, and the motion comes from the plot front.
