#!/usr/bin/env bash
# tooling/render.sh <project-dir> [output.mp4] [extra hyperframes render flags...]
#
# Render, then measure. The QC gate runs by default and its exit code is this
# script's exit code: a render that is silent, cropped, illegible or static
# fails here, not in front of the person you made it for.
#
# Budget: ~2.1 s of wall clock per second of video on this box
# (measured: 17.5 s film -> 37 s, 10 s film -> 18 s). Say the number out loud
# before you start.
#
#   --no-qc   skip the gate (you are now the only check — don't)
set -euo pipefail

DIR="${1:?usage: render.sh <project-dir> [out.mp4] [flags...]}"
[ -d "$DIR" ] || { echo "Not a directory: $DIR" >&2; exit 1; }
DIR="$(cd "$DIR" && pwd)"
shift

RUN_QC=1
OUT=""
ARGS=()
for a in "$@"; do
  case "$a" in
    --no-qc) RUN_QC=0 ;;
    *)
      if [ -z "$OUT" ] && [ "${a#-}" = "$a" ]; then OUT="$a"; else ARGS+=("$a"); fi
      ;;
  esac
done
[ -n "$OUT" ] || OUT="$DIR/out.mp4"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac

[ -f "$HOME/.local/env.sh" ] && . "$HOME/.local/env.sh"

# Cheap pre-flight: a CDN reference aborts the render 30 s in, not at the start.
if ! bash "$(dirname "$0")/fix-cdn.sh" "$DIR" >/dev/null 2>&1; then
  echo "WARNING: external CDN references found — the render will fail." >&2
  bash "$(dirname "$0")/fix-cdn.sh" "$DIR" >&2 || true
  exit 1
fi

cd "$DIR"
# -w 1              single worker: 2 cores cannot feed more
# --low-memory-mode keeps capture streaming under ~3.8 GB
# Never add --resolution upscale: it forces the slow path on software GL.
npx hyperframes render -w 1 --low-memory-mode --output "$OUT" ${ARGS+"${ARGS[@]}"}

if [ "$RUN_QC" -eq 1 ]; then
  PY="${QC_PYTHON:-$HOME/.local/venv/bin/python}"
  [ -x "$PY" ] || PY="$(command -v python3)"
  echo
  "$PY" "$(dirname "$0")/qc.py" "$OUT"
fi
