#!/usr/bin/env bash
# Burn the source-credit overlay into finished clips.
#
#   tools/burn_credit.sh shorts/clip-01.mp4 [more.mp4 ...]
#
# Rewrites each file in place (via a temp), keeping resolution, frame rate and audio.
# The overlay is transient: it does not flash, fade or animate, it just sits there.
set -euo pipefail
cd "$(dirname "$0")/.."

FF=$(command -v ffmpeg || true)
[[ -x ${FF:-} ]] || FF=/tmp/fbin/ffmpeg
PY=$(command -v python3 || true); [[ -x ${PY:-} ]] || PY=/tmp/venv/bin/python
OVERLAY=${OVERLAY:-assets/credit.png}
[[ -f $OVERLAY ]] || { "$PY" tools/credit_overlay.py >/dev/null; }

MARK="credit:Mrwhosetheboss"      # written into the container so a re-run cannot double-burn
for f in "$@"; do
  [[ -f $f ]] || continue
  info=$("$FF" -nostdin -hide_banner -i "$f" 2>&1 || true)
  if [[ $info == *"$MARK"* ]]; then
    echo "already credited: $f"
    continue
  fi
  tmp="${f%.mp4}.credit.mp4"
  "$FF" -nostdin -hide_banner -loglevel error -i "$f" -i "$OVERLAY" \
    -filter_complex "[0:v][1:v]overlay=0:0:format=auto" -map 0:a? \
    -c:v libx264 -profile:v high -crf 19 -preset medium -pix_fmt yuv420p \
    -c:a copy -movflags +faststart -metadata comment="$MARK" "$tmp"
  mv "$tmp" "$f"
  echo "credited: $f"
done
