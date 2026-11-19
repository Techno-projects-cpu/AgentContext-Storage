#!/usr/bin/env bash
# Cut the GTA 6 launch clips from the source video.
#
#   ./build.sh                    # use ./source.mp4 (or $SOURCE)
#   ./build.sh talk.mp4           # or pass a path
#
# What it does, in order (this is the video-to-shorts-skill pipeline, nothing bespoke):
#   1. probe the source, check it is the video the candidates were written against
#   2. transcribe with word timestamps   (existing .srt/.vtt > local faster-whisper > Groq)
#   3. turn candidates.json into clips.json, snapping every start/end onto real word edges
#   4. render 1080x1920 H.264 clips with word-by-word captions, hook card, -14 LUFS
#   5. rebuild review.html with the clips embedded
#
# Nothing here posts anything. Posting is a separate, explicit step.
set -euo pipefail
cd "$(dirname "$0")"

SKILL=../../skills/video-to-shorts-skill
SOURCE=${1:-${SOURCE:-source.mp4}}
PY=${PY:-python3}
[[ -x /tmp/venv/bin/python ]] && PY=/tmp/venv/bin/python
[[ -d /tmp/fbin ]] && export PATH=/tmp/fbin:$PATH

# 1 ---------------------------------------------------------------- the source
if [[ ! -f $SOURCE ]]; then
  cat <<'MSG'
No source file.

This sandbox cannot reach video hosts, so the 48-minute file has to be dropped in first, on a
machine that can. One command, from the video, unlisted, at 1080p:

  yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4 \
         -o "source.%(ext)s" "https://youtu.be/NrF4mkTmuTU"

Then copy source.mp4 next to this script and run ./build.sh again.
MSG
  exit 2
fi

echo "== source: $SOURCE"
DUR=$("$PY" - "$SOURCE" <<'PY'
import json,subprocess,sys
o=json.loads(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",
                             sys.argv[1]],capture_output=True,text=True).stdout)
print(round(float(o["format"]["duration"])))
PY
)
echo "   ${DUR}s"
if (( DUR < 2800 || DUR > 3100 )); then
  echo "   !! expected ~2917 s (48:37). This does not look like the right video; stopping."
  exit 3
fi

# clearance: this is someone else's video, so make the credit line impossible to forget
echo "== clearance"
echo "   source: Mrwhosetheboss, https://youtu.be/NrF4mkTmuTU"
echo "   every caption in candidates.json already carries the credit line."

# 2 ------------------------------------------------------------ transcription
if [[ -f ${SUBS:-} ]]; then
  echo "== transcribe (from $SUBS)"
  "$PY" "$SKILL/scripts/transcribe.py" "$SOURCE" --out work/ --from "$SUBS"
else
  echo "== transcribe (local faster-whisper; set GROQ_API_KEY for a faster run)"
  "$PY" "$SKILL/scripts/transcribe.py" "$SOURCE" --out work/ --model small
fi

# 3 ------------------------------------------------------------------ clips
echo "== snapping candidates onto word timings"
"$PY" tools/to_clips.py --source "$SOURCE" --transcript work/transcript.json -o clips.json

# 4 ----------------------------------------------------------------- render
echo "== preview crops"
"$PY" "$SKILL/scripts/make_shorts.py" clips.json --transcript work/transcript.json \
      --out shorts/ --preview
echo "== render 1080x1920"
"$PY" "$SKILL/scripts/make_shorts.py" clips.json --transcript work/transcript.json --out shorts/

# 4b ---------------------------------------------------------------- credit
echo "== burning the source credit into every clip"
"$PY" tools/credit_overlay.py >/dev/null
tools/burn_credit.sh shorts/clip-*.mp4

# 5 ----------------------------------------------------------------- review
echo "== review page"
"$PY" tools/review.py
echo
echo "done: shorts/ + review.html"
echo "watch the first 5 s of every clip and open shorts/contact-sheet.jpg before posting."
