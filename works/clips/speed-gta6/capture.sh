#!/usr/bin/env bash
# Cut one clip straight out of the source: no transcription, no whisper, no network.
#
#   ./capture.sh source.mp4 01          # -> shorts/clip-01.mp4
#   ./capture.sh source.mp4 all         # all five
#   FR=30 ./capture.sh source.mp4 03    # if the source is 30 fps (the upload is 29.97)
#
# The path for a machine that has the file but no Python packages: it only needs ffmpeg.
# Seconds come from candidates.json (capture.final), hand-checked against the transcript.
# Captions are the one thing this does not burn; build.sh does that once a transcript exists.
set -euo pipefail
PACK=$(cd "$(dirname "$0")" && pwd)
cd "$PACK"
REPO=$(git -C "$PACK" rev-parse --show-toplevel 2>/dev/null || echo "$PACK/../../..")
export CLIP_PACK="$PACK"
export CLIP_REPO="$REPO"
SRC=${1:?usage: ./capture.sh source.mp4 CLIP|all}
WHICH=${2:-all}
FR=${FR:-30000/1001}

FF=$(command -v ffmpeg || true)
if [[ -z $FF || ! -x $FF ]]; then
  [[ -x /tmp/fbin/ffmpeg ]] && FF=/tmp/fbin/ffmpeg
fi
[[ -n ${FF:-} && -x $FF ]] || { echo "ffmpeg is required (brew install ffmpeg / apt install ffmpeg)"; exit 1; }

PY=$(command -v python3 || true)
[[ -x ${PY:-} ]] || PY=/tmp/venv/bin/python

# REFRAME=fit  (default) keeps the WHOLE frame, 1080 wide, over a blurred fill of itself.
#              Nothing can be cropped off, which matters because the framing of the source is
#              unknown until the file lands.
# REFRAME=crop fills the frame with a 9:16 centre slice, for footage that is already tight on
#              one person.
CREDIT=assets/credit.png
[[ -f $CREDIT ]] || { "$PY" tools/credit_overlay.py >/dev/null; }
if [[ ${REFRAME:-fit} == crop ]]; then
  FG="crop=ih*9/16:ih,scale=1080:1920[fg2]"
else
  FG="scale=1080:-2[fg2]"
fi

VF="split=2[bg][fg];\
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=28,\
eq=brightness=-0.10[bg2];\
[fg]${FG};\
[bg2][fg2]overlay=(W-w)/2:(H-h)*0.40[frame];\
[frame][1:v]overlay=0:0[out]"

segs() {  # print "start end" for a clip id
  "$PY" - "$1" <<'PY'
import json, sys
d = json.load(open("candidates.json"))
f = d["capture"]["final"][sys.argv[1]]
print(f["start"], f["end"])
PY
}

cut() {
  local id=$1 a b len
  read -r a b <<< "$(segs "$id")"
  len=$("$PY" -c "print(round(float('$b') - float('$a'), 1))")
  echo "== clip $id  ${a}s -> ${b}s  (${len}s)"
  mkdir -p shorts
  "$FF" -nostdin -hide_banner -loglevel error -ss "$a" -to "$b" -i "$SRC" -i "$CREDIT" \
    -filter_complex "$VF" -map "[out]" -map 0:a? \
    -c:v libx264 -profile:v high -crf 19 -preset medium -pix_fmt yuv420p -r "$FR" \
    -c:a aac -b:a 192k -ar 48000 -movflags +faststart "shorts/clip-$id.mp4"
  echo "   shorts/clip-$id.mp4"
}

if [[ $WHICH == all ]]; then
  for id in 01 02 03 04 05; do cut "$id"; done
else
  cut "$WHICH"
fi
echo
echo "done. run: $PY tools/review.py   (embeds the clips in review.html)"
