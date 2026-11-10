#!/usr/bin/env bash
# fix-cdn.sh <project-dir>
#
# This sandbox resolves ONLY registry.npmjs.org and github.com. A CDN <script> or
# <link> does not degrade gracefully: HyperFrames aborts the render with
#   sub_timeline_script_failure ... [script_load: cdn/net::ERR_CONNECTION_CLOSED]
# and you lose the whole render pass.
#
# Run this after every init / template pull / block install.
# It reports what it finds; it auto-fixes GSAP (the only lib we vendor) and
# loudly flags everything else.
set -uo pipefail

DIR="${1:?usage: fix-cdn.sh <project-dir>}"
cd "$DIR"
GSAP="${GSAP:-$HOME/.local/vendor/gsap}"
status=0

mapfile -t files < <(grep -rlE 'https?://(cdn\.|unpkg|jsdelivr|esm\.sh|fonts\.googleapis|fonts\.gstatic)' \
  --include='*.html' --include='*.css' --include='*.js' --include='*.json' . 2>/dev/null \
  | grep -v node_modules || true)

for f in "${files[@]:-}"; do
  [ -z "$f" ] && continue
  # GSAP: swap for the vendored copy.
  if grep -q 'cdn.jsdelivr.net/npm/gsap' "$f"; then
    mkdir -p "$(dirname "$f")/vendor"
    cp "$GSAP/gsap.min.js" vendor/gsap.min.js 2>/dev/null || true
    sed -i 's|https://cdn.jsdelivr.net/npm/gsap@[0-9.]*/dist/gsap.min.js|./vendor/gsap.min.js|g' "$f"
    echo "fixed  gsap  -> ./vendor/gsap.min.js   ($f)"
  fi
  # Everything else: manual work, but say so now, not at render time.
  if grep -qE 'https?://(cdn\.|unpkg|jsdelivr|esm\.sh|fonts\.googleapis|fonts\.gstatic)' "$f"; then
    echo "BLOCKED (fix by hand) in $f:"
    grep -oE 'https?://[^"'"'"' )]+' "$f" \
      | grep -E '(cdn\.|unpkg|jsdelivr|esm\.sh|fonts\.googleapis|fonts\.gstatic)' \
      | sort -u | sed 's/^/    /'
    status=1
  fi
done

if [ "$status" -eq 0 ]; then
  echo "no external CDN references — render will not be blocked"
fi
exit "$status"
