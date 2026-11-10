#!/usr/bin/env bash
# remix.sh — replace a finished film's audio with narration + ducked bed,
# reusing the existing H.264 video stream (no re-render, no re-encode of video).
#
#   bash remix.sh <lang> <existing-film.mp4> <output.mp4>
#
# Chain, in order — this order is the whole point:
#   1. bed  = music 0.35 + four drops + bong + impact, summed with a matching
#             ×7 undo (amix has no normalize=0), then loudnorm'd and NOTHING ELSE.
#             The bed's loudness is therefore SET, not left to chance.
#   2. voice = narration at 1.0, +2 dB, delayed 0.45 s.
#   3. music is sidechain-ducked by the voice.
#   4. bed + voice summed with a matching ×2 undo, then alimiter at −1 dBTP.
#
# Why not loudnorm at the end: loudnorm renormalises whatever it is given, so it
# silently undoes any voice/bed balance the earlier stages set. Normalising the
# bed alone and limiting the sum keeps the balance exactly where it was dialled.
set -euo pipefail
[ -f "$HOME/.local/env.sh" ] && . "$HOME/.local/env.sh"

HERE="$(cd "$(dirname "$0")" && pwd)"
FF="${FF:-$HOME/.local/bin/ffmpeg}"
A="$HERE/assets"
L="$1"; SRC="$2"; DEST="$3"
VO="${VO:-$HERE/vo/vo-$L.mp3}"
[ -f "$VO" ] || { echo "missing $VO" >&2; exit 1; }

"$FF" -y -hide_banner -loglevel error \
  -stream_loop -1 -t 20 -i "$A/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3" \
  -i "$A/sfx/drop.ogg" -i "$A/sfx/bong.ogg" -i "$A/sfx/impact.ogg" \
  -i "$VO" -i "$SRC" \
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
  -map 5:v:0 -map "[out]" \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "$DEST"
echo "remixed $L -> $DEST"
