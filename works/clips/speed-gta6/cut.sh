#!/usr/bin/env bash
# Get the source video into this folder, then cut the clips.
#
#   ./cut.sh                          # cut ./source.mp4, or download it if missing
#   ./cut.sh file.mp4                 # use a file you already have
#   ./cut.sh https://host/file.mp4    # or any direct video URL you can host
#
# yt-dlp is fetched into ./.vendor if it is not already installed: no root, no pip needed.
set -euo pipefail
PACK=$(cd "$(dirname "$0")" && pwd)
cd "$PACK"
REPO=$(git -C "$PACK" rev-parse --show-toplevel 2>/dev/null || echo "$PACK/../../..")
export CLIP_PACK="$PACK"
export CLIP_REPO="$REPO"

URL="https://youtu.be/NrF4mkTmuTU"
ARG="${1:-source.mp4}"
export PATH="$PWD/.vendor/bin:$PATH"
PY=${PY:-python3}

have_ytdlp() { command -v yt-dlp >/dev/null 2>&1; }

# --------------------------------------------------------------- yt-dlp, no root
if ! have_ytdlp; then
  echo "== getting yt-dlp (none installed)"
  mkdir -p .vendor/bin
  ok=0
  # a) static release binary
  if command -v curl >/dev/null 2>&1 &&
     curl -fsSL --max-time 120 -o .vendor/bin/yt-dlp \
       "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp" 2>/dev/null; then
    chmod +x .vendor/bin/yt-dlp && ok=1
  fi
  # b) a plain python copy from PyPI, into ./.vendor (no root, works with PEP 668)
  if (( !ok )); then
    if "$PY" -m pip install --quiet --target .vendor/py yt-dlp >/dev/null 2>&1; then
      printf '#!/bin/sh\nexec "%s" -m yt_dlp "$@"\n' "$PY" > .vendor/bin/yt-dlp
      chmod +x .vendor/bin/yt-dlp
      PYTHONPATH="$PWD/.vendor/py" "$PY" -c "import yt_dlp" 2>/dev/null && ok=1
    fi
  fi
  if (( !ok )); then
    echo "   could not fetch yt-dlp here (no route to GitHub releases or PyPI)."
    echo "   On any normal machine: pip install --user yt-dlp"
  fi
fi

SRC=""
if [[ $ARG == http* ]]; then
  echo "== downloading $ARG"
  yt-dlp --no-warnings --newline -o "source.%(ext)s" "$ARG" || true
  SRC=$(ls -1 source.mp4 source.mkv source.webm source.mov 2>/dev/null | head -1 || true)
elif [[ -f $ARG ]]; then
  SRC=$ARG
else
  echo "== downloading the source video (1080p, roughly 500 MB)"
  rc=0
  if have_ytdlp; then
    yt-dlp --no-warnings --newline \
      -f "bv*[height<=1080]+ba/b[height<=1080]/b" --merge-output-format mp4 \
      -o "source.%(ext)s" "$URL" || rc=$?
  else
    rc=1
  fi
  SRC=$(ls -1 source.mp4 source.mkv source.webm 2>/dev/null | head -1 || true)
  if [[ -z $SRC ]]; then
    cat <<'MSG'

== no source video yet, so there is nothing to cut

Everything else is ready: candidates.json has the five picks, build.sh does the rest the
moment a file exists. Two ways to get one in:

  A. From this machine, if it can reach YouTube:
       pip install --user yt-dlp
       yt-dlp -f "bv*[height<=1080]+ba" -o source.mp4 "https://youtu.be/NrF4mkTmuTU"
       ./cut.sh

  B. With no command line at all:
       open the video, play it, right-click > "Save video as" (or use any download site),
       then drop the .mp4 into this folder as source.mp4 and run ./cut.sh

  C. If YouTube is bot-gating the request, add your browser's cookies:
       yt-dlp --cookies-from-browser chrome -f "bv*[height<=1080]+ba" -o source.mp4 URL

Then ./cut.sh does: probe, transcribe with word timings, snap the five clips onto real word
edges, render 1080x1920 with captions and hooks, rebuild review.html with them embedded.
MSG
    exit 1
  fi
fi

echo "== source: $SRC"
exec ./build.sh "$SRC"
