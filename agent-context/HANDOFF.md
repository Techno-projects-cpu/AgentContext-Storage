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
| `templates/brag/` | ✅ working template — 17.5 s film, 9/9 QC |
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
scripts/new-film.sh intro portrait        # template + fonts + GSAP + demo audio
scripts/render.sh intro                   # render, then the QC gate
```

`new-film.sh` stamps `templates/brag` into a new project. You edit **one object**
(`FILM` in `index.html`: scenes, copy, durations) and nothing else. Scene start
times, cross-fades, holds, entrances and the camera move are derived.

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

4. **Audio must be static markup, and must have an `id=`.** Two ways to ship a mute
   film, neither with an error:
   * no `id` → the compiler scans `audio[id]` and skips it;
   * created from JavaScript → the runtime parses the **HTML source, not the live
     DOM**, so a scripted `<audio>` is never mixed. It renders perfect and weighs
     nothing. This bit me on 2026-11-09; `qc.py` now decodes the MP4 to catch it.
5. `.clip{inset:0}` stretches any corner-positioned element → add
   `right:auto;bottom:auto;height:auto`.
6. Don't trust GSAP `steps()` easing → use explicit `tl.set()` at computed times.
7. **Frame 0 is the thumbnail.** Never fade scene 1 in from nothing.
8. No `filter:blur()` on animated or large elements — software GL stalls.
9. Type ≥28 px · hold text `0.5 s + 0.3 s/word` · all text passes WCAG AA.
10. Self-host fonts (woff2 + `@font-face`, `font-display:block`). Never hotlink a CDN — see trap 1.
11. No `Math.random` / `Date.now` / network at runtime — the render must be deterministic.
12. **Never fade the copy while the scene is cross-fading.** Two opacity narratives
    at the same instant both go dark and the frame dips to black — a flash nobody
    catches in code review. Scene dissolves, copy *slides* in. `qc.py` samples every
    0.1 s and fails on any empty frame.

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

`scripts/render.sh` runs the gate for you; exit code is the render's verdict.

```bash
scripts/qc.py out.mp4                    # 9 numeric checks on the encoded file
npx hyperframes check                    # lint + runtime + layout + contrast
```

What the gate proves, and what it cannot:

| Check | Catches |
|---|---|
| `audio_stream` / `audio_audible` | the silent render (decodes the MP4, doesn't trust markup) |
| `duration_15_25s` | the /brag gate |
| `first_frame_has_ink` | a black thumbnail |
| `no_edge_cropping` | text running off the canvas |
| `type_floor` | copy below 30 px |
| `contrast_min_3to1` | ink that can't be read against the ground |
| `no_black_dip` | transitions that flash to black |
| `motion_present` | a film that is accidentally a slideshow |

It cannot tell you the film is *good*. Never claim it looks good — claim exactly
what the table says, and say plainly that nobody has watched it.

### One expected warning

`hyperframes check` reports `content_overlap: Two text blocks overlap` at each
cross-fade (on a 17.5 s film: ≈5.6 s, 9.6 s, 14.6 s). That is the dissolve —
two scenes are legitimately on screen together for 0.3 s. Confirm it is *only*
at the transitions before ignoring it; an overlap anywhere else is real.

## Next

1. Recover `nezaad/` source or rebuild it on the template — the old source is gone.
2. Port Parakeet word-timings for karaoke captions (biggest gap; needs internet once).
3. Batch renders: `hyperframes render --batch rows.json` over one template.
4. Landscape / square variants are already supported by `new-film.sh`.
5. Verify how Kokoro pronounces "Nezaad".
6. Startup brand kit — no site, no tokens yet.

## Dead — don't revive

Eenadu series (abandoned) · KIRRAK & CO (finished, superseded, files deleted).

## Never commit

MP4 / MOV / WAV / mix files. Git keeps every binary revision and a free account's LFS
allowance dies fast. Text only — `.gitignore` already enforces this.
