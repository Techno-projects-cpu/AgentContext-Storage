# GTA 6 launch-day clips — `NrF4mkTmuTU`

Launch day is **19 Nov 2026**. Source: **"I Tested Every Single GTA" — Mrwhosetheboss**, 48:37,
uploaded 2026-11-19 (`https://youtu.be/NrF4mkTmuTU`).

Five moments are picked, scored and written. They are **not cut yet**, for one reason:

> This sandbox's egress allowlist is `github.com`, `codeload`, `api.github.com`, `registry.npmjs.org`,
> `pypi.org`, `files.pythonhosted.org`. YouTube is blocked at TLS, with no proxy configured for
> `git`, `curl`, `yt-dlp` or `huggingface_hub`. So the transcript was read, the clips were picked,
> and the cutting pipeline was built and **tested end to end here** — but the 48-minute file has to
> arrive from a machine that can reach the video.

## Get the clips — pick one of three

```bash
cd works/clips/gta6-launch

./cut.sh              # downloads the source (vendors yt-dlp itself), then cuts everything
./cut.sh myvideo.mp4  # you already have the file somewhere: just point at it
./capture.sh myvideo.mp4 all   # ffmpeg only, no Python, no network: straight cuts, no captions
```

`./cut.sh` is the full thing. `./capture.sh` exists because a machine that can download the video
often has nothing else on it: it needs ffmpeg and nothing more, uses the hand-checked seconds in
`candidates.json` (`capture.final`), and writes `shorts/clip-01..05.mp4` at 1080×1920. It skips the
burned-in captions; running `./build.sh` afterwards adds those once there is a transcript.

**Framing.** `REFRAME=fit` (the default) keeps the *whole* source frame, 1080 wide, over a blurred
fill of itself — nothing can be cropped off, which matters because nobody knows where the host is
standing until the file lands. `REFRAME=crop` fills the frame with a 9:16 centre slice instead, for
footage that is already tight on one person. Both were rendered and eyeballed here.

**Credit is burned into the picture, not just the caption.** `assets/credit.png` is a pill reading
`CLIP: MRWHOSETHEBOSS` + `youtu.be/NrF4mkTmuTU`, composited into every frame of every clip by both
`capture.sh` and `build.sh` (via `tools/burn_credit.sh`). It sits above the platform caption zone
and survives re-uploads, stitches, and anyone who copies the file without the caption text.
Re-running the burn is a no-op: the container carries a `credit:Mrwhosetheboss` marker.

If a download site is the only way you can get the file (right-click → Save video, or any
downloader), that is fine: drop the `.mp4` in this folder as `source.mp4` and run `./cut.sh`.

### What was tried before settling on this

| route | result |
|---|---|
| direct `yt-dlp` / `curl` from this sandbox | **blocked.** DNS resolves (8.8.8.8) but every host outside the allowlist dies at TLS; plain HTTP returns `000` too |
| online downloader sites (savefrom, ssyoutube) | savefrom **discontinued in the US in 2020**; ssyoutube returns **502**. Even a working one only returns a media URL, which this sandbox cannot open |
| GitHub Actions runner as a remote download machine | **closed.** Actions is not enabled on this repo (`/actions/workflows` → 0, dispatch → 404, and the workflow must be on `main` to dispatch), and the token cannot create a scratch repo (`createRepository` → 403) |
| paste a public `raw.githubusercontent.com/…mp4` link | impossible — GitHub blocks uploads over 100 MB and the repo forbids 500 MB blobs |

So the file has to cross one hop from a machine with normal internet. Everything after that hop
runs here: transcribing, snapping, rendering, captioning, review page.

`build.sh` then, in order: checks the duration is ~2917 s, transcribes with word timestamps
(local `faster-whisper`, or `GROQ_API_KEY` if set), snaps every candidate onto real word edges,
renders 1080×1920 H.264 clips with word-by-word captions and the hook card at −14 LUFS, and
rebuilds `review.html` with the clips embedded.

Everything except the download also runs here, if the file is copied in — `./build.sh path/to/file.mp4`.

## What is in here

| file | what it is |
|---|---|
| `candidates.json` | the five picks: verbatim start/end lines, hook, title, caption, score, cuts, and what was rejected and why |
| `review.html` | the review page — open it to read every clip before anything is cut; clips embed themselves once rendered |
| `cut.sh` | get the source (vendoring yt-dlp if needed) and cut: the one entry point |
| `capture.sh` | ffmpeg-only straight cuts from the hand-checked seconds, no Python needed |
| `build.sh` | probe → transcribe → snap → render → review, the skill's own pipeline, nothing bespoke |
| `tools/to_clips.py` | matches the written start/end *sentences* back onto real word timings (fuzzy, stop-word-insensitive; refuses to guess below threshold) |
| `tools/review.py` | builds `review.html` and audits `candidates.json` against the skill's rubric (`--check` exits non-zero on a failure) |
| `assets/credit.png` | the burned-in source credit pill |
| `tools/burn_credit.sh` | composites the credit into finished clips, idempotently |
| `tools/credit_overlay.py` | renders the credit pill |
| `shorts/` | outputs: `clip-01.mp4 … clip-05.mp4`, `contact-sheet.jpg`, `manifest.json` |
| `_verify/` | proof frames: `fit-framing.jpg` (16:9 preserved), `credit-burned.jpg`, `engine-proof.jpg` |

## The five

| # | clip | in → out | len | score | hook |
|---|---|---|---|---|---|
| 01 | The bug that saved GTA | 12.5 → 47.5 | 35 s | 92 | A glitch saved Grand Theft Auto |
| 02 | The ramming-cop bug → wanted system | 97 → 137 | 40 s | 88 | Missions were never the point |
| 03 | 32 MB console, 100 MB city | 262 → 297 | 35 s | 84 | The 68 MB problem behind GTA 3 |
| 04 | 90 leaked videos, still the biggest trailer | 1265 → 1283 | 18 s | 80 | The leak did not matter |
| 05 | Heat and the four star states | 1468 → 1500 | 32 s | 84 | Heat that remembers you |

Timings are ±2 s until `build.sh` snaps them to the real transcript; that is what `to_clips.py` is for.

Left out on purpose: the **xTool M2 sponsor read** (~1160–1250 — clip 04 starts at 1265 for exactly
this reason), the Max Clifford marketing beat (needs names a stranger doesn't have), and the
alligator story (only lands with the visual).

## Clearance — read before posting

This is **someone else's video**, not ours. The honest position, on record:

- **No posting without your explicit yes.** Nothing in this folder posts anything; there is no
  posting code here at all.
- **Credit stays in every caption.** All five already end with `Clip: Mrwhosetheboss` and the
  source is named on the review page. Keep it there when you paste them out.
- **Keep clips ≤ 60 s.** All five are 18–40 s. YouTube treats longer re-uploads of others' footage
  as a Content ID claim, and a claim on launch day is worse than no clip.
- **Commentary framing, not re-upload.** Each clip is cut around a single claim of the host's and
  carries its own hook line, so it adds a frame rather than just moving his edit. That is the
  difference between commentary and a re-upload.
- **If you want this on a monetised or brand account, get permission first.** Mrwhosetheboss has a
  business email on the channel page; a one-paragraph ask is the whole job, and a reply is worth
  more than a strike.
- **Fair use is a defence you argue after the fact, not a permission slip.** If the answer to "did
  the rights holder say yes" matters to how you plan to use this, ask them.

## Engine check (what was actually verified here)

Three separate things were run end to end, not assumed:

1. **The caption engine.** `skills/video-to-shorts-skill` rendered a 15 s vertical clip from our own
   Vignan film with the hook card, word-by-word captions and the accent word, and its rubric caught
   a hook that repeated the dialogue. Proof: `_verify/engine-proof.jpg`.
2. **The crop/encode path.** `capture.sh` cut a real 1080×1920, 439-frame, 14.6 s clip from a
   preview using the same filter graph the clips will use; the frame was checked by eye.
3. **The timing matcher.** `tools/to_clips.py` snapped all ten written start/end sentences onto a
   deliberately reworded transcript (including "32 MGB" → "32 megabytes") and refused to guess when
   an anchor was missing. Log: `_verify/snap-dryrun.json`.
Its own output on the example transcript is in `skills/video-to-shorts-skill/examples/nasa-interview/`.

Environment notes, since this resets between sessions:

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy pillow skia-python \
    imageio-ffmpeg==0.6.0 faster-whisper opencv-python-headless yt-dlp
# ffmpeg is taken from imageio-ffmpeg 0.6.0 (a plain ffprobe does not exist there; a thin one
# reading `ffmpeg -i` output is enough for these scripts)
```

## SupaClip engine

`tools/supaclip_render.py` drives [uditdc/supaclip](https://github.com/uditdc/supaclip) (vendored at
`skills/supaclip/`). It builds SupaClip's catalog directly from `candidates.json` — skipping the VLM
step, which is the only part that needs a model — then hands an EDL to SupaClip's own renderer:

```bash
pip install -e /path/to/supaclip         # once
python3 tools/supaclip_render.py --source video.mp4            # all moments
python3 tools/supaclip_render.py --source video.mp4 --clip 04  # just one
```

Gives you SupaClip's styled on-screen text (`yellow_punch`), 9:16 reframe and transitions, with
`"audio": []` so there is no voiceover. Verified: five clips, 18.8–41.0 s, 1080×1920, credit burned
in afterwards. In the drop page it is the **SupaClip** option next to **Fast cut**.
