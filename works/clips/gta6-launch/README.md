# GTA 6 launch-day clips — `NrF4mkTmuTU`

Launch day is **19 Nov 2026**. Source: **"I Tested Every Single GTA" — Mrwhosetheboss**, 48:37,
uploaded 2026-11-19 (`https://youtu.be/NrF4mkTmuTU`).

Five moments are picked, scored and written. They are **not cut yet**, for one reason:

> This sandbox's egress allowlist is `github.com`, `codeload`, `api.github.com`, `registry.npmjs.org`,
> `pypi.org`, `files.pythonhosted.org`. YouTube is blocked at TLS, with no proxy configured for
> `git`, `curl`, `yt-dlp` or `huggingface_hub`. So the transcript was read, the clips were picked,
> and the cutting pipeline was built and **tested end to end here** — but the 48-minute file has to
> arrive from a machine that can reach the video.

## Cut them (one command)

On any machine with internet and ffmpeg:

```bash
cd works/clips/gta6-launch
yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
       -o "source.%(ext)s" "https://youtu.be/NrF4mkTmuTU"
./build.sh
```

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
| `build.sh` | probe → transcribe → snap → render → review, the skill's own pipeline, nothing bespoke |
| `tools/to_clips.py` | matches the written start/end *sentences* back onto real word timings (fuzzy, stop-word-insensitive; refuses to guess below threshold) |
| `tools/review.py` | builds `review.html` and audits `candidates.json` against the skill's rubric (`--check` exits non-zero on a failure) |
| `shorts/` | outputs: `clip-01.mp4 … clip-05.mp4`, `contact-sheet.jpg`, `manifest.json` |

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

`skills/video-to-shorts-skill` is vendored and ran for real: a 15 s vertical clip was rendered from
our own Vignan film's preview with the hook card, word-by-word captions and the accent word, and
the rubric caught a hook that repeated the dialogue. Proof frame: `_verify/engine-proof.jpg`.
Its own output on the example transcript is in `skills/video-to-shorts-skill/examples/nasa-interview/`.

Environment notes, since this resets between sessions:

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy pillow skia-python \
    imageio-ffmpeg==0.6.0 faster-whisper opencv-python-headless yt-dlp
# ffmpeg is taken from imageio-ffmpeg 0.6.0 (a plain ffprobe does not exist there; a thin one
# reading `ffmpeg -i` output is enough for these scripts)
```
