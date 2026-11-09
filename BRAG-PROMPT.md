# BRAG-PROMPT — the reusable authoring prompt

Paste the block below as the first message of a video task, after `HANDOFF.md` has been read.
It encodes the /brag standard. Keep it tool-agnostic where possible; the render notes are
specific to HyperFrames on a 2-core software-GL box.

---

You are authoring a short brand video, not a slideshow. Read `HANDOFF.md` first — the
trap list there is not optional.

## 0. Before you write anything

Ask me exactly these, in **one** message (blocking — wait for answers):

1. **Format**: vertical / landscape / square?
2. **Voice**: which Kokoro voice, or "no voiceover"?
3. **Subject source**: which site / repo / brief is the source of truth?
4. **Length**: default 15–25 s unless I say otherwise.

Then state your angle in **one sentence** and start building. Don't ask again — I'll
redirect you *before* the render, not after.

## 1. Script

- 15–25 s total. Hard gate.
- Words ≈ (duration_s − 1.5) × 2.6 at Kokoro default speed. Write the VO to fit the
  length, not the other way round.
- Narration **complements** the visuals. It must never read the on-screen captions.
- Never invent facts, prices, testimonials, or verbs the site doesn't support
  ("Notify me" ≠ "Buy now").
- Phone-test every line: could it be spoken out loud without sounding like ad copy?
  Cut it if not.

## 2. Voice first, then cut

Voice timing drives every cut. Order of operations:

1. Generate the VO (or receive the wav).
2. `ffprobe` the file; note real duration.
3. Keep the wav — never regenerate between renders, or the cut drifts.
4. Lay out scenes against **measured** word timings, not assumed ones.
5. Put music impacts on VO line starts.

## 3. Visual system

- The look is **derived from the subject** every time. What stays fixed is the craft floor:

| Rule | Value |
|---|---|
| Type floor | ≥ 28 px at 1080 short side |
| Text hold | 0.5 s + 0.3 s/word |
| Entrances | 0.4–0.7 s, `power4` / `expo` out |
| Camera ideas | exactly ONE per scene |
| Scene end | everything settles and holds ≥ 0.4 s |
| Transitions | 0.30 s cross-fade |
| Music | ducked under VO |
| Contrast | all text WCAG AA |

- **Frame 0 is the thumbnail.** Never fade scene 1 in from nothing.
- Camera, CSS 3D only: push-in, pull-back, orbit, tilt, pan, parallax multi-plane,
  crash zoom, perspective type, whip, rack focus (sparingly), drift (backgrounds only).

## 4. Hard constraints (soft GL, 2 cores)

- No `filter:blur()` on animated or large elements — the capture stalls.
- Self-host every font (woff2 + `@font-face`, `font-display:block`).
- No CDN `<script>` / `<link>` — the render **aborts**. Run `scripts/fix-cdn.sh` after
  every init or block install.
- `<audio>` needs an `id=` or the output is silent with no error.
- No `Math.random` / `Date.now` / network at runtime.
- Don't trust GSAP `steps()` easing — explicit `tl.set()` at computed times.

## 5. QC gate — report numbers, never impressions

```bash
npx hyperframes check                       # lint + runtime + layout + contrast
ffprobe -hide_banner out.mp4                # duration + streams + audio present
ffmpeg -i out.mp4 -af astats -f null -      # RMS proves the VO actually mixed in
```

Deliverable message must state: duration, resolution, contrast pass count, error count,
and the measured RMS. Say plainly that **nobody has watched it** — you have no vision.

## 6. Output

```
<project>/
  index.html        composition (single file unless it outgrows ~600 lines)
  vendor/gsap.min.js
  assets/           fonts, images, audio
  out.mp4           never committed
```
