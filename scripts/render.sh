#!/usr/bin/env bash
# render.sh <project-dir> [output.mp4] [extra hyperframes render flags...]
#
# The render invocation that survives this box: 2 cores, ~3.8 GB RAM, no GPU,
# no chrome-headless-shell (screenshot capture path), software GL.
#
# Budget: ~1.9 s of wall clock per second of video, single worker.
#   22.5 s video  ->  ~45 s, plus encode
# Always tell the user that number before starting.
set -euo pipefail

DIR="${1:?usage: render.sh <project-dir> [out.mp4] [flags...]}"
[ -d "$DIR" ] || { echo "Not a directory: $DIR" >&2; exit 1; }
DIR="$(cd "$DIR" && pwd)"
shift

OUT=""
if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
  OUT="$1"; shift
fi
[ -n "$OUT" ] || OUT="$DIR/out.mp4"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac

[ -f "$HOME/.local/env.sh" ] && . "$HOME/.local/env.sh"

# -w 1              single worker: 2 cores cannot feed more
# --low-memory-mode keeps capture streaming under ~3.8 GB
# Never add --resolution upscale: it forces the slow path on software GL.
cd "$DIR"
exec npx hyperframes render -w 1 --low-memory-mode --output "$OUT" "$@"
