# Duable — two ads

Two 9:16 ads for **Duable**, built to the brag standard in
[`agent-context/BRAG-PROMPT.md`](../../../agent-context/BRAG-PROMPT.md).

| File | Length | Look | Angle |
|---|---|---|---|
| `01-duable-the-menu-1080x1920.mp4` | 20.0 s | grid + phosphor green on near-black | the breadth is the product |
| `02-duable-honest-mode-1080x1920.mp4` | 18.8 s | warm paper + deep green, quiet | the refusals are the product |

1080×1920 · 30 fps · H.264 + AAC · **no voiceover** (per standing instruction), a
synthesized music bed instead.

They are deliberately not reskins of each other: different palette, different
typographic voice, different pacing, different cards. Only the craft floor is shared.

---

## Where the facts came from

The site is live at **https://duableindustries.vercel.app** — that URL was correct.
I confirmed it through the Vercel connector rather than guessing: project
`duableindustries` = `prj_kiGYa9IRTXwV4eNl531iWET0jC8j`, production alias
`duableindustries.vercel.app`, production deployment
`dpl_D7puXA4semWYFT7Nz3qXDoNKLxWp`, `readyState: READY`.

Every claim on screen is a quote from that page or a number it prints:

| On screen | Source |
|---|---|
| 24 services, and 8 / 4 / 5 / 7 per category | the site's search label and category cards |
| web & technology · ai & automation · creative & media · marketing & growth | the four category cards, verbatim |
| talk it through · set the scope · make the work · hand it over | the four process steps, verbatim |
| "no magic numbers" | *"…practical growth strategy—without promising magic numbers"* |
| "your answers stay in this browser" / "nothing is sent. nothing is saved." | the project-starter panel |
| small team, hands-on work · based in india · working everywhere | the hero band |
| "a studio with a service for that." | the H1 |
| independent creative technology studio | the hero eyebrow |

**Nothing invented.** No prices, no client counts, no testimonials, no "trusted by",
no growth percentages. The two named people on the site are explicitly labelled
creative aliases and are not used in either ad.

## Deliverability note

Both are captioned films — silent autoplay-safe 9:16 spots for feed/reel placement, so
all meaning survives with the sound off. The bed is a synthesized low pulse plus a tick
on each card, so nothing here is licensed third-party audio.

---

## Build

```bash
cd works/films/duable-ads/source
/tmp/venv/bin/python render.py --audit                 # brag floor, as measurements
/tmp/venv/bin/python render.py --survey                # card timeline + contact sheet
/tmp/venv/bin/python render.py --ad menu   --out ../01-duable-the-menu-1080x1920.mp4
/tmp/venv/bin/python render.py --ad honest --out ../02-duable-honest-mode-1080x1920.mp4
```

* `brand.py` — the only file allowed to hold copy. Every string is sourced above.
* `kit.py` — type, easing, the two palettes, and the measured layout helpers.
* `ads.py` — the cards. A card is a pure `draw(t, dur)`, so a frame can be rendered in
  isolation for review.
* `render.py` — timeline, cross-fades, bed, ffmpeg, and `--audit`.

## What the brag rules cost me (the honest part)

Three real defects, all found by measuring rather than by looking:

1. **Ink height is not line advance.** `PIL.getbbox` on a 360 px numeral reports
   `top=108, bottom=379` — the em box is 360, the ink is 271. Stacking by em height
   over-lapped "24" and "SERVICES" by 80 px. `kit.draw_block` now aligns on ink boxes.
2. **QC's safe area is 94 % by default**, stricter than this design's 84 px margin.
   Three separate offenders — the corner ticks, the footer rule, and the footer
   baseline — each had to come inside the 54 px box. Fixed at source, not by passing
   `--safe`.
3. **A first draft of ad 2 was a stack of empty pages.** Measured blocks centred in a
   huge void read as unfinished, not as restraint. The fix was composition (moved to
   the lower two-thirds, added a sourced studio line) rather than more decoration.

## QC

`tooling/qc.py --safe 0.90` — **9/9 on both**, and `render.py --audit` passes the
brag floor (20.00 s / 18.80 s, smallest type 28 px, shortest card 3.4 s, frame 0 inked).

| | `01-the-menu` | `02-honest-mode` |
|---|---|---|
| duration_15_25s | 20.00 s ✓ | 18.80 s ✓ |
| audio_stream / audible | aac, rms −18.4 dB ✓ | aac, rms −18.7 dB ✓ |
| first_frame_has_ink | 0.46 % ✓ | 1.03 % ✓ |
| no_edge_cropping | ✓ | ✓ |
| type_floor | ✓ | ✓ |
| contrast_min_3to1 | ✓ | ✓ |
| no_black_dip | ✓ | ✓ |
| motion_present | 7/13 ✓ | 7/13 ✓ |

The report is measurements only — it proves the films are not silent, not cropped, not
illegible and not static. It cannot tell you whether they are good. That judgement is
still yours.

## Open question worth answering

Vercel has a **second** project from the same private repo: `duable`, alias
`duable.vercel.app` (prod `dpl_5YGcBWHfLLomrFaCqX3JzoZAbrSY`). These ads end on
`duableindustries.vercel.app`, which is the project you asked for. If the ads should
point at `duable.vercel.app` instead, it is a one-line change in `brand.py`.

The repo `Techno-projects-cpu/Duable` is private and this sandbox's token cannot read
it, so the copy came from the rendered production page, not the source.
