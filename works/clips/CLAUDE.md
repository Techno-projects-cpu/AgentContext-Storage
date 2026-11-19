# For Claude Code running in this repo

You are on a machine with normal internet. The agent that set this up was not: its egress was
allowlisted to github.com, pypi.org and registry.npmjs.org, so it could build and test the whole
pipeline but could never fetch the source video. You can. Do the download, then run what is
already tested.

## Do this, in order, without asking

```bash
cd works/clips/gta6-launch
./cut.sh                      # vendors yt-dlp if absent, downloads 1080p, cuts all five
```

If YouTube bot-gates the download (403 / "Sign in to confirm you're not a bot"):

```bash
pip install --user yt-dlp
yt-dlp --cookies-from-browser chrome -f "bv*[height<=1080]+ba" \
       --merge-output-format mp4 -o source.mp4 "https://youtu.be/NrF4mkTmuTU"
./cut.sh source.mp4
```

`--cookies-from-browser` works because you are on the user's machine and their browser is there.
The allowlisted agent could not do this either: no browser, no profile, no cookies.

## What "done" looks like

- `works/clips/gta6-launch/shorts/clip-01.mp4 … clip-05.mp4` — 1080×1920, **with the source
  audio intact**, boss's credit burned into every frame.
- Five moments, already written and scored in `candidates.json`:
  01 the 1995 bug that saved GTA (92) · 02 the ramming-cop bug → wanted system (88) ·
  03 32 MB console, 100 MB city (84) · 04 the leak that did not matter (80) ·
  05 heat and the four star states (84).
- `tools/check.py` must exit 0. It fails on placeholders, >60 s, or wrong dimensions.

## Engines

`./cut.sh` → ffmpeg straight cuts (fast, no model). `./build.sh` → the vendored
`skills/video-to-shorts-skill` adds word-by-word captions from a transcript.
`tools/supaclip_render.py` → SupaClip's renderer (`skills/supaclip/`), styled on-screen text.

For SupaClip's engine: `pip install -e <clone of uditdc/supaclip>` then
`python3 tools/supaclip_render.py --source source.mp4`.

## Rules that are not negotiable

1. **Keep the source audio.** Muted clips are worthless; this was already a mistake once.
2. **Credit stays burned in** (`tools/burn_credit.sh`) and `Clip: Mrwhosetheboss` stays in every
   caption. It is his footage.
3. **No voiceover.** These are no-voiceover cuts by standing instruction.
4. **Never post anything.** No uploads, no scheduling, no API posting calls. Deliver files and
   links only, then stop and let the user decide.
5. **Verify before reporting**: decode a frame from each finished clip and confirm the credit is
   visible; confirm duration and 1080×1920 with ffprobe.

## Speed's stream (second pack)

`works/clips/speed-gta6/` is the same pipeline for IShowSpeed's GTA 6 stream
(`youtube.com/@IShowSpeed/streams`, started 18 Nov 2026 9pm ET). Its moments must be picked by
watching — `python3 tools/set_moment.py 01 4823.5 4851.0 --hook "..."` then
`FR=60 ./capture.sh stream.mp4 01`. Credit for that pack is `CLIP: IShowSpeed`
(`CREDIT_WHO=IShowSpeed CREDIT_URL=... python3 tools/credit_overlay.py` before burning).
