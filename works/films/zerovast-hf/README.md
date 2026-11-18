# ZeroVast — three HyperFrames films

Films for **[zero-vast.vercel.app](https://zero-vast.vercel.app)**, written as
HTML compositions and rendered to MP4 with
[HyperFrames](https://github.com/heygen-com/hyperframes) (`npx hyperframes render`).
The creative approach — 15–25 s, hook first, show the actual thing, no generic
SaaS language, fast in then hold — follows the
[Brag](https://github.com/latent-spaces/brag) skill.

| # | Film | Length | What it is |
|---|---|---|---|
| 01 | [Site tour](01-hyperframes-site-tour-1080p.mp4) | 25 s | Six scenes: a type-only hook, the real page in a browser window, a lateral truck across three work cards, a 3D deck of four disciplines, the four limits, the close. |
| 02 | [Camera moves](02-hyperframes-camera-moves-1080p.mp4) | 22 s | Six shots, one move each — push in, tilt, truck, rack focus, pull back — over full-frame captures of the live page. Letterbox, viewfinder corners, shot counter. |
| 03 | [Kinetic type](03-hyperframes-kinetic-type-1080p.mp4) | 20 s | The site's own sentences set at full frame on a 4 s bar, with crops of the real page flashing past as evidence. No page is ever shown as a page. |

Sources: [`source/`](source) — one self-contained `index.html` per film (the
composition is the deliverable; the MP4 is a render of it).
Share copy: [`share-copy.txt`](share-copy.txt).

## Numbers, not adjectives

Measured on the delivered MP4s with `ffprobe`/`ffmpeg`:

| File | Duration | Frame | Audio | Loudness | True peak | Dead-frame samples |
|---|---|---|---|---|---|---|
| 01 site tour | 25.000 s | 1920×1080 @30 | AAC | −16.34 LUFS | −2.89 dBTP | 1 (fade-out) |
| 02 camera moves | 22.000 s | 1920×1080 @30 | AAC | −16.30 LUFS | −1.02 dBTP | 1 (fade-out) |
| 03 kinetic type | 20.000 s | 1920×1080 @30 | AAC | −16.74 LUFS | −1.20 dBTP | 0 |

"Dead-frame samples" comes from `tblend=difference,signalstats` sampled every
30 frames: a count of one-second windows whose mean frame difference is under
0.15 AVG. Those are the tail fades, where a still frame is correct.

Each composition passes the HyperFrames gate — lint, runtime, layout, motion and
contrast — with **0 errors and 0 warnings**, verified with
`npx hyperframes check`.

## What was actually fixed while making these

These are the defects the gate and frame review caught, not things that were
right the first time:

- **Type over the hero photograph is a trap.** The site's own display headline
  reads straight through any overlay; a gradient scrim and a hard 3840 px crop
  both bled. Film 01's hook became type-only, and the photograph moved into a
  separate browser-window scene.
- **`nth-of-type` on a lone child selects nothing.** In film 03 every animated
  word reported "GSAP target not found" — 21 runtime warnings — and lines 2 and
  3 of each chapter never animated. The index had to go on the line wrapper.
- **A near-black site makes a camera move look like a still.** The captures
  measure 7–27 YAVG out of 255. Films 02 lifts the plate on those shots
  (brightness 1.85–2.15) so a truck actually reads as movement.
- **Text over text needs a ground.** Captions sitting on the real page collided
  with the page's own copy; they became lower-thirds with a scrim, a hairline and
  an accent rule.
- **Static holds read as stills.** Film 03 originally held one frame for 2.9 s;
  every chapter now carries a slow drift, and the film has zero dead samples.
- **Two renders competing for one port silently stall.** The first full render
  sat at 0.5 % CPU for 16 minutes; one worker at a time finishes in 1–2.5 min.
- **Caption numbering was off by one** in film 02 (kickers said "01" on shot 02).

## Honest caveat

**Nobody has watched these.** The verification above is numeric: correct
duration, resolution and audio track; loudness inside the −16 LUFS band; no dead
frames; gate green. Frames were reviewed as stills. That proves these are not
cropped, silent, illegible, frozen or mislabelled. It cannot tell you the edit is
good or the pacing lands — that needs a person watching, once.
