# HANDOFF — brag video pipeline

Operational brief. Read this file first; only then open `BRAG-PROMPT.md`.

Last verified: 2026-11-09, in an Arena sandbox (2 cores / 3.8 GB / no GPU / no sudo-capable network).

---

## Me

- Guntur, AP, India. Personal brand **Nezaad** — web dev, Khammam TG, `zero-vast.vercel.app`.
- Starting a startup with a friend → this is a **pipeline**, not one-off videos. Expect many.
- Hates waiting. Prefer one strong pass over five re-renders. **Say how long a render will take before starting it.**
- Blunt feedback. If I say it's broken, find the root cause — don't tweak cosmetics.

## What we make

Short brand/launch videos with the **/brag** skill, rendered by **HyperFrames**
(HTML/CSS/GSAP → MP4 in headless Chrome).

The bar: **Nezaad — 22.5 s, 1080×1920, voiceover, 0 errors, 41/41 contrast pass.**

## State of this repo (read before assuming anything exists)

| Thing | Status |
|---|---|
| `bootstrap.sh`, `scripts/` | ✅ verified end-to-end today |
| `BRAG-PROMPT.md` | ✅ the reusable authoring prompt |
| `nezaad/` composition source | ❌ **not in this checkout** — the old workspace is gone. Ask me for it or rebuild from the brief |
| `HANDOFF-LONG.md` (489-line version) | ❌ not carried over |
| `~/brag2/work/score.py` (music+VO mix) | ❌ gone |
| any MP4 / mix.wav | ❌ deleted (keep it that way — see *Never commit*) |

## Rebuild the toolchain

```bash
bash bootstrap.sh
source ~/.local/env.sh
```

Idempotent, ~40 s cold. It installs, all from **npm only**:

1. **ffmpeg + ffprobe** — static builds via `@ffmpeg-installer` / `@ffprobe-installer`.
   (`apt-get` does not work here: no Debian mirror reachable.)
2. **Chromium** — the AWS-Lambda build (`@sparticuz/chromium`), extracted with its own
   NSS libs *and* SwiftShader `.so` files placed **beside the binary**, then wrapped in
   `~/.local/bin/chrome` with `--use-gl=angle --use-angle=swiftshader --in-process-gpu`.
   (`npx hyperframes browser ensure` cannot reach Google storage — don't try it.)
3. **hyperframes** — project-local in `~/.local/hf` (global install → EACCES).
4. **GSAP** — vendored to `~/.local/vendor/gsap` (jsDelivr is blocked; a CDN `<script>`
   kills the whole render, see traps).

Then:

```bash
scripts/new-project.sh intro portrait     # scaffolds + de-CDN's automatically
scripts/render.sh intro                   # -> intro/out.mp4
```

## Sandbox boundaries (learned the hard way)

- Reachable: `registry.npmjs.org`, `github.com`. **Nothing else.** No jsDelivr, no
  HuggingFace, no Google storage, no Debian mirrors.
- `hyperframes tts` **cannot** run here — Kokoro weights live on HuggingFace. Generate
  voice elsewhere (or on a box with internet) and drop the wav into the project.
  `models install parakeet` is blocked for the same reason.
- No `chrome-headless-shell` → capture runs on the slower **screenshot path**. Budget
  **≈1.9 s wall clock per second of video** (10 s video = 18 s; a 22.5 s video ≈ 45 s).
- 2 workers is worse than 1. Always `-w 1 --low-memory-mode`. Never `--resolution upscale`.

## Traps — each one costs a full render pass

**Sandbox-specific (new, cost a render each):**

1. **A CDN script aborts the render**, it does not degrade: `sub_timeline_script_failure
   [script_load: cdn/net::ERR_CONNECTION_CLOSED]`. Stock `hyperframes init` has exactly
   this bug (GSAP from jsDelivr). Run `scripts/fix-cdn.sh <dir>` after every init/blocks pull.
2. **SwiftShader `.so` must sit next to the chromium binary.** In a subfolder the browser
   dies with `GLDisplayEGL::Initialize failed` → `SIGTRAP` → "Target closed". The wrapper
   in `bootstrap.sh` handles this; don't relocate those files.
3. **Empty voiceover ≠ missing voiceover.** If TTS was skipped, the video renders fine and
   is silent. Check the mix with `ffprobe` RMS before delivering.

**Authoring traps (unchanged):**

4. `<audio>` MUST carry an `id=` — without it the render is **silent with no error**.
5. `.clip{inset:0}` stretches any corner-positioned element → add
   `right:auto;bottom:auto;height:auto`.
6. Don't trust GSAP `steps()` easing → use explicit `tl.set()` at computed times.
7. **Frame 0 is the thumbnail.** Never fade scene 1 in from nothing.
8. No `filter:blur()` on animated or large elements — software GL stalls.
9. Type ≥28 px · hold text `0.5 s + 0.3 s/word` · all text passes WCAG AA.
10. Self-host fonts (woff2 + `@font-face`, `font-display:block`). Never hotlink a CDN — see trap 1.
11. No `Math.random` / `Date.now` / network at runtime — the render must be deterministic.

## My standing preferences

1. **Format — always ask** (vertical / landscape / square). Never assume.
2. **Voice — always ask.** No house voice. Kokoro voices:
   `am_adam am_michael af_heart af_nova af_sky bm_george bf_emma bf_isabella ef_dora ff_siwis jf_alpha zf_xiaobei`
   (unavailable locally — see boundaries; still ask, then source the wav).
3. **One round of blocking questions, then build.** State your angle in one sentence and
   go — I'll redirect before the render.
4. **Look derived from the subject every time.** What stays fixed is the craft floor:
   type floor · read-time · 0.4–0.7 s entrances with `power4`/`expo` out · ONE camera idea
   per scene · everything settles and holds · 0.30 s cross-fade · duck music under VO ·
   numeric QC gate.

## Camera vocabulary (real CSS 3D — `perspective` + `translate3d`/`rotateX`/`rotateY` + `preserve-3d`)

push-in · pull-back · orbit · tilt · pan · **parallax multi-plane** (cheapest way to look
expensive) · crash zoom · perspective type · whip · rack focus (blur — sparingly, stalls
soft GL) · drift (backgrounds only)

## Rules I care about

- Narration **complements** visuals, never reads the captions.
- Never invent facts, prices, testimonials. If the site says "Notify me", never say "Buy now".
- Duration **15–25 s** (hard /brag gate).
- Build the cut around **measured** voice timings, not imagined ones.
- Put music impacts on VO line starts.
- **You have no vision.** QC is numeric (ink bounding boxes, contrast, RMS). Always say
  plainly that nobody has watched it.

## QC before delivering

```bash
npx hyperframes check                    # lint + runtime + layout + contrast
ffprobe -hide_banner <file>.mp4          # duration, streams, and that audio exists
ffmpeg -i <file>.mp4 -af astats -f null -   # RMS > ~-40 dB means there IS voice
```

Never claim a video "looks good". Claim what the numbers say.

## Next

1. Recover `nezaad/` source or rebuild it from the brief — nothing here references it yet.
2. Port Parakeet word-timings for karaoke captions (biggest gap; needs internet once).
3. First reusable template + `hyperframes render --batch rows.json`.
4. Landscape cut of the Nezaad video.
5. Verify how Kokoro pronounces "Nezaad".
6. Startup brand kit — no site, no tokens yet.

## Dead — don't revive

Eenadu series (abandoned) · KIRRAK & CO (finished, superseded, files deleted).

## Never commit

MP4 / MOV / WAV / mix files. Git keeps every binary revision and a free account's LFS
allowance dies fast. Text only — `.gitignore` already enforces this.
