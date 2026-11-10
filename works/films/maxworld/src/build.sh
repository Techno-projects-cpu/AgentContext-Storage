#!/usr/bin/env bash
# build.sh — Max World localised ads: render, mix, encode, derive variants.
#
#   bash build.sh [en te hi ur]
#
# Per language:
#   1. hyperframes render  → silent master, 1080×1920 / 30 fps / 20 s
#   2. ffmpeg audio mix    → narration + music with fades and sidechain duck,
#                            four chip drops, bong, phone impact; summed with
#                            no auto-normalise
#   3. encode              → libx264 crf 20, yuv420p, +faststart, AAC 192k
#   4. variants            → 1080×1080 and 1920×1080, blurred-fill bars
#   5. poster              → the settled CTA frame
#
# Beat grid: cuts 3.27 / 8.74 / 13.11 · chips 4.91 / 5.34 / 6.00 / 6.56 ·
# bong 8.74 · phone punch 17.47 · music out 18.60 → 20.00.
#
# Narration: src/vo/vo-<lang>.mp3, starts at 0.45 s, and the music is
# sidechain-compressed under it so the voice always sits on top. The bed is
# ducked, never muted — the beat still carries the cuts.
set -euo pipefail

# Chrome, ffmpeg and GSAP live outside the repo; without this the hyperframes
# subshell cannot find a browser.
[ -f "$HOME/.local/env.sh" ] && . "$HOME/.local/env.sh"

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$HERE"                                        # brag-output/work
OUT="$(cd "$WORK/../.." && pwd)/brag-output"        # brag-output
FF="${FF:-$HOME/.local/bin/ffmpeg}"
A="$HERE/src/assets"
FRAMES="${FRAMES:-/tmp/mwframes}"
LANGS="${*:-en te hi ur}"

mkdir -p "$OUT" "$FRAMES"

mix_audio() {
  local dest="$1" vo="$2"
  # Order matters: the BED is loudnorm'd on its own and nothing else, so its
  # level is set rather than left to chance. Then the voice is placed on top and
  # the bed is sidechain-ducked under it. A final loudnorm would renormalise
  # whatever it is handed and silently undo that balance, so the sum is only
  # limited, never normalised.
  #
  # amix has no `normalize=0` on every ffmpeg build: padding each branch makes
  # amix's divide-by-N a constant, and a matching ×N gain undoes it exactly.
  # sidechaincompress needs both inputs at the same format or it renegotiates
  # mid-stream and dies with "Failed to inject frame"; hence the aformat pins.
  "$FF" -y -hide_banner -loglevel error \
    -stream_loop -1 -t 20 -i "$A/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3" \
    -i "$A/sfx/drop.ogg" -i "$A/sfx/bong.ogg" -i "$A/sfx/impact.ogg" \
    -i "$vo" \
    -filter_complex "\
[0:a]atrim=0:20,volume=0.35,afade=t=in:st=0:d=0.5,afade=t=out:st=18.6:d=1.4,apad[musraw];\
[1:a]asplit=4[d1][d2][d3][d4];\
[d1]adelay=4910|4910,volume=0.5,apad[s1];\
[d2]adelay=5340|5340,volume=0.5,apad[s2];\
[d3]adelay=6000|6000,volume=0.5,apad[s3];\
[d4]adelay=6560|6560,volume=0.5,apad[s4];\
[2:a]adelay=8740|8740,volume=0.45,apad[s5];\
[3:a]adelay=17470|17470,volume=0.55,apad[s6];\
[musraw][s1][s2][s3][s4][s5][s6]amix=inputs=7:duration=longest,volume=7,\
atrim=0:20,loudnorm=I=-26:TP=-9:LRA=7,aresample=48000,\
aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[bed];\
[4:a]atrim=0:19.6,aresample=48000,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,\
adelay=450|450,apad,asplit=2[vo][key];\
[bed][key]sidechaincompress=threshold=0.02:ratio=8:attack=6:release=280[bedduck];\
[bedduck][vo]amix=inputs=2:duration=longest,volume=2,\
atrim=0:20,alimiter=limit=0.891:attack=5:release=60[out]" \
    -map "[out]" -ac 2 -t 20 "$dest"
}

for L in $LANGS; do
  P="/home/user/mwproj/$L"
  SUF=$([ "$L" = "en" ] && echo "" || echo "-$L")
  echo "== $L =============================================="

  # 1. picture
  if [ ! -f "$FRAMES/$L.mp4" ]; then
    ( cd "$P" && npx hyperframes render -w 1 --low-memory-mode -o "$FRAMES/$L.mp4" 2>&1 | tail -2 )
  fi

  # 2. authored mix (narration + ducked bed)
  VO="$HERE/src/vo/vo-$L.mp3"
  if [ ! -f "$VO" ]; then echo "!! missing narration: $VO" >&2; exit 1; fi
  mix_audio "$FRAMES/$L.m4a" "$VO"

  # 3. vertical master
  "$FF" -y -hide_banner -loglevel error -i "$FRAMES/$L.mp4" -i "$FRAMES/$L.m4a" \
    -map 0:v:0 -map 1:a:0 \
    -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart \
    -c:a aac -b:a 192k -shortest "$OUT/brag${SUF}.mp4"

  # 4. square + wide: blurred-fill bars.
  #    Scale to FILL and blur = background; the untouched vertical is laid on
  #    top at full height and centred. Filling (not fitting) is what brings the
  #    fill to the edges — fitting leaves black bars down the sides.
  for spec in "1080:1080:square" "1920:1080:wide"; do
    W=${spec%%:*}; rest=${spec#*:}; H=${rest%%:*}; name=${rest#*:}
    "$FF" -y -hide_banner -loglevel error -i "$OUT/brag${SUF}.mp4" \
      -filter_complex "\
[0:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},\
gblur=sigma=30,eq=brightness=0.10:contrast=0.92:saturation=1.5[bg];\
[0:v]scale=-2:${H}[fg];\
[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]" \
      -map "[v]" -map 0:a:0 \
      -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart \
      -c:a aac -b:a 192k -shortest "$OUT/brag${SUF}-${name}.mp4"
  done

  # 5. poster
  "$FF" -y -hide_banner -loglevel error -ss 19.6 -i "$OUT/brag${SUF}.mp4" \
    -frames:v 1 -q:v 3 "$OUT/brag${SUF}.jpg"

  echo "   wrote brag${SUF}.mp4 / -square / -wide / .jpg"
done

echo "done → $OUT"
