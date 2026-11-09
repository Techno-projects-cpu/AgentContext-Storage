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
| [`scripts/new-project.sh`](scripts/new-project.sh) | Scaffolds a composition that renders here |
| [`scripts/fix-cdn.sh`](scripts/fix-cdn.sh) | Strips CDN refs that would abort a render |
| [`scripts/render.sh`](scripts/render.sh) | The render flags that survive 2 cores / software GL |

## Quick start

```bash
bash bootstrap.sh
source ~/.local/env.sh

scripts/new-project.sh intro portrait
scripts/render.sh intro            # -> intro/out.mp4
```

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

## Never commit

Video and audio deliverables. `.gitignore` blocks them — git stores every binary revision
and a free LFS allowance disappears fast.
