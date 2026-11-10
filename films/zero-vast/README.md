# zero-vast — 24.9 s portrait film

Source of truth: <https://zero-vast.vercel.app>. Every claim in the film is either
lifted from the site or plainly true of it. The site publishes **no prices, no
testimonials, no client counts** — so the film makes none of those claims.

## What it is

24.9 s, 1080×1920, one voice, five scenes, cut to *measured* voice timings.

| # | t | Scene | Camera |
|---|---|---|---|
| 01 | 0.35 | "Websites built *to perform.*" | push-in |
| 02 | 3.57 | Hand-written, no framework tax + code plate | orbit (rotateY + x) |
| 03 | 9.18 | Budgets set before the code + measure bars | drift |
| 04 | 13.65 | Brief → Scope → Build → Handover | pull-back |
| 05 | 19.98 | "Let's build the next one." + URL | push-in |

## Look

Derived from the subject, not sampled: the browser here is network-isolated, so
`hyperframes capture` cannot reach the live site. The design is inferred from its
**content and positioning** — hand-written code, no framework, accessibility — and
becomes an instrument panel: mono labels, numbered sections, hairline rules,
measure bars, one blue accent on warm paper. No stock footage, no gradients.

## Reproduce

```bash
bash bootstrap.sh && source ~/.local/env.sh
scripts/new-film.sh myfilm portrait
#   copy index.html in, drop vo.wav + bed.wav into assets/
scripts/render.sh myfilm          # render + numeric QC gate
```

## Not committed

`out.mp4` and the wavs. Regenerate the voice mix from `timing.json`; the render is
~1 m 20 s on 2 cores, and `qc.py` must pass 9/9 before this is worth showing anyone.

**Nobody has watched this film.** The QC gate proves it is not silent, not
cropped, not illegible, not flashing black and not static. It cannot prove it is
good.
