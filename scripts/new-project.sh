#!/usr/bin/env bash
# new-project.sh <name> [portrait|landscape|square|portrait-4k|landscape-4k|square-4k]
#
# Scaffolds a hyperframes composition that is ALREADY renderable in this sandbox:
#   * GSAP vendored locally (the stock scaffold points at jsDelivr, which is blocked)
#   * no CDN <link>/<script> survives  (see scripts/fix-cdn.sh)
#
# Usage:
#   source ~/.local/env.sh
#   scripts/new-project.sh intro portrait
set -euo pipefail

NAME="${1:?usage: new-project.sh <name> [resolution]}"
RES="${2:-portrait}"
GSAP="${GSAP:-$HOME/.local/vendor/gsap}"
HERE="$(cd "$(dirname "$0")" && pwd)"

[ -f "$GSAP/gsap.min.js" ] || { echo "GSAP missing at $GSAP — run bootstrap.sh"; exit 1; }

HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes init "$NAME" \
  --resolution "$RES" --non-interactive --skip-skills >/dev/null

cp -r "$GSAP" "$NAME/vendor"
"$HERE/fix-cdn.sh" "$NAME"

cat <<EOF

Project ready: $NAME  ($RES)

  cd $NAME
  npx hyperframes preview          # iterate visually
  npx hyperframes check            # lint + runtime + layout gate
  $HERE/render.sh $NAME            # -> $NAME/out.mp4

GSAP is at $NAME/vendor/gsap.min.js — reference it as ./vendor/gsap.min.js.
Never add a CDN URL: nothing outside npmjs.org / github.com resolves here.
EOF
