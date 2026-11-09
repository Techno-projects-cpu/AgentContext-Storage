# AgentContext-Storage

Text kit for the **brag video pipeline** — brand/launch videos authored in HTML/CSS/GSAP
and rendered to MP4 with [HyperFrames](https://github.com/heygen-com/hyperframes).

This repo deliberately holds **text only**: prompts, handoff notes, and scripts that
rebuild the toolchain in a fresh sandbox. No videos, no audio, no model weights.

## Start here

| File | What it is |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | Operational brief — who I am, how to rebuild, traps, QC |
| [`BRAG-PROMPT.md`](BRAG-PROMPT.md) | The reusable video-authoring prompt |
| [`bootstrap.sh`](bootstrap.sh) | Rebuilds ffmpeg + Chromium + hyperframes + GSAP from npm |
| [`templates/brag/`](templates/brag) | Data-driven film template — edit one object |
| [`scripts/new-film.sh`](scripts/new-film.sh) | Stamps a new film from the template |
| [`scripts/render.sh`](scripts/render.sh) | Render flags that survive 2 cores / software GL, + QC |
| [`scripts/qc.py`](scripts/qc.py) | 9 numeric checks on the encoded MP4 |
| [`scripts/fix-cdn.sh`](scripts/fix-cdn.sh) | Strips CDN refs that would abort a render |
| [`scripts/make-demo-audio.sh`](scripts/make-demo-audio.sh) | Placeholder VO/music so the pipeline runs |

## Quick start

```bash
bash bootstrap.sh
source ~/.local/env.sh

scripts/new-film.sh intro portrait     # template + fonts + GSAP + demo audio
scripts/render.sh intro                # render, then the numeric QC gate
```

Edit only the `FILM` object in `intro/index.html`: scenes, copy, durations.
Starts, cross-fades, holds, entrances and camera moves are derived from it.

The gate **fails the render** if the film is silent, cropped, illegible, dips to
black between scenes, or has no motion. It cannot tell you the film is good —
nobody has watched it.

## Why the bootstrap is weird

The sandbox can only reach `registry.npmjs.org` and `github.com`. So:

- **ffmpeg/ffprobe** come from npm static builds (no apt mirror).
- **Chromium** is the AWS-Lambda build, which ships its own NSS + SwiftShader libraries —
  and its GL `.so` files must sit *beside* the binary or the browser dies with `SIGTRAP`.
- **GSAP** is vendored locally; `hyperframes init` points at jsDelivr, and a blocked CDN
  script aborts the entire render instead of degrading.

Known-unavailable: `hyperframes tts` (Kokoro weights are on HuggingFace), Parakeet models,
and `npx hyperframes browser ensure` (Google storage). See the boundaries section of
`HANDOFF.md`.

Two silent-failure traps the template closes for good: an `<audio>` tag without an `id`,
and an `<audio>` tag created from JavaScript — the runtime parses the HTML source, not the
live DOM, so a scripted track is never mixed and the MP4 comes out mute with no error.

## Never commit

Video and audio deliverables. `.gitignore` blocks them — git stores every binary revision
and a free LFS allowance disappears fast.
