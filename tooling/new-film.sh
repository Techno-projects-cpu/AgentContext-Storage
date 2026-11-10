#!/usr/bin/env bash
# new-film.sh <name> [portrait|landscape|square] [brag|3d]
#
# Stamps a fresh film into ./<name>/ from engines/brag (default) or
# engines/explainer3d (third argument "3d"):
#   index.html      the template (edit only the FILM object)
#   vendor/gsap     vendored, not CDN
#   assets/fonts    self-hosted, not CDN
#   assets/*.wav    placeholder audio (so the pipeline is runnable immediately)
#
# Then it runs the CDN check, because a blocked CDN aborts the render instead of
# degrading. If you add anything from the outside world, re-run fix-cdn.sh.
set -euo pipefail

NAME="${1:?usage: new-film.sh <name> [portrait|landscape|square] [brag|3d]}"
RES="${2:-portrait}"
ENGINE="${3:-brag}"
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(dirname "$HERE")"
case "$ENGINE" in
  brag) TPL="$REPO/engines/brag/template.html" ;;
  3d)   TPL="$REPO/engines/explainer3d/template.html" ;;
  *) echo "unknown engine: $ENGINE (brag|3d)"; exit 1 ;;
esac

[ -f "$HOME/.local/env.sh" ] && . "$HOME/.local/env.sh"
GSAP="${GSAP:-$HOME/.local/vendor/gsap}"
FONTS="${FONTS:-$HOME/.local/vendor/fonts}"

[ -s "$GSAP/gsap.min.js" ] || { echo "GSAP missing at $GSAP — run bootstrap.sh"; exit 1; }
[ -s "$FONTS/space-grotesk-latin-700-normal.woff2" ] || { echo "fonts missing at $FONTS — run bootstrap.sh"; exit 1; }
[ -d "$NAME" ] && { echo "refusing to overwrite existing $NAME"; exit 1; }

mkdir -p "$NAME/vendor" "$NAME/assets/fonts"
cp "$TPL" "$NAME/index.html"
cp "$GSAP/gsap.min.js" "$NAME/vendor/gsap.min.js"
cp "$FONTS"/*.woff2 "$NAME/assets/fonts/"

# Resolution is a data attribute + a viewport meta on the html element.
case "$RES" in
  portrait)      W=1080; H=1920 ;;
  landscape)     W=1920; H=1080 ;;
  square)        W=1080; H=1080 ;;
  *) echo "unknown resolution: $RES (portrait|landscape|square)"; exit 1 ;;
esac
sed -i "s/data-resolution=\"[a-z]*\"/data-resolution=\"$RES\"/" "$NAME/index.html"
sed -i "s|content=\"width=1080, height=1920\"|content=\"width=$W, height=$H\"|" "$NAME/index.html"
sed -i "s/data-width=\"1080\"/data-width=\"$W\"/; s/data-height=\"1920\"/data-height=\"$H\"/" "$NAME/index.html"
sed -i "s/width: 1080px;/width: ${W}px;/; s/height: 1920px;/height: ${H}px;/" "$NAME/index.html"

bash "$HERE/make-demo-audio.sh" "$NAME" >/dev/null
bash "$HERE/fix-cdn.sh" "$NAME"

cat <<EOF

$(printf '\033[1m')$(basename "$NAME")$(printf '\033[0m')  ·  $RES ($W×$H)

  1. edit the FILM object in $NAME/index.html  (scenes, copy, timing)
  2. replace $NAME/assets/vo.wav with a real voiceover
  3. npx hyperframes preview
  4. $HERE/render.sh $NAME      → render + numeric QC gate

The .wav files in there now are PLACEHOLDERS. They prove the audio path,
they are not words. Do not ship them.
EOF
