# ZERO VAST — "Type" (no voiceover)

22.0 s, 1080×1920, 30 fps. Music-led: no narrator, the cut sheet is the script.

| | |
|---|---|
| Style | kinetic type over nine evolving grounds (`huashu` y5 动态文字 grammar) |
| Track | `audio/score.wav` — synthesised beat bed, 96 bpm, hits on every cut (`_shared/eng/make_track.py`) |
| Mix | `audio/mix.m4a` — music + sfx only, −15 LUFS (`_shared/eng/mix_novo.py`) |
| Transitions | card swing, whip, push-through, curtain, lens leak (`_shared/eng/transitions.py`) |
| End card | `zero-vast.vercel.app` |

Rebuild:

```bash
export CF_ENGINE=/tmp/cs/cinematic-skill/skills/cinematic-film/scripts
SCENE=scene.py /tmp/py tools/render2.py --project . --cues
/tmp/py $CF_ENGINE/build_sfx.py --project .
/tmp/py ../_shared/eng/mix_novo.py --project . --music audio/score.wav --music-db -2 --sfx-db -8
SCENE=scene.py /tmp/py tools/render2.py --project . --size 1080x1920 --audio audio/mix.m4a --out out/final.mp4 --workers 2
```

Every word on screen is from zero-vast.vercel.app: hand-written HTML/CSS/JS, LCP/CLS/INP budgets set
before the build, WCAG 2.2 AA, repository + deploy steps + walkthrough handed over, Khammam
Telangana, one point of contact. No prices, no client counts, no invented metrics.

## What this one taught the shared library

* **A no-VO film has no voice bus**, so `mix_soundtrack.py` (which ducks music against narration)
  cannot mix it — hence `_shared/eng/mix_novo.py`.
* **A cut on a beat is an arrival, not a fade.** Ramping type from zero after a hit leaves five dim
  frames at every cut; the words now start at 88 % and settle in 0.18 s.
* **Transition coverage must be a narrow pulse.** With a sine envelope the card/curtain covered the
  incoming shot for 0.2 s on either side of every cut and each cut looked like a glitch.
* **A type block is one size.** Auto-fitting each line independently makes a two-word line twice its
  neighbour's size; the smallest-fitting line sets the block and the rest may grow 20–30 %.
* **A highlighter bar through a whole-word line reads as a chip**, not as emphasis.
