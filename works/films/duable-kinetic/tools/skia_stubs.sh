#!/usr/bin/env bash
# A CPU-only skia wheel still links libEGL/libGL. This writes minimal stubs so
# `import skia` succeeds on a box with no GL stack. Nothing on our path ever
# creates a GPU context, so every stub returning 0 is correct.
set -euo pipefail
OUT=${1:-/tmp/gl}
mkdir -p "$OUT"
cd "$OUT"
SYMS=$(nm -D --undefined-only "$(python3 -c 'import skia,os;print(skia.__file__)')" 2>/dev/null \
        | awk '{print $2}' | grep -E '^(gl|egl)' | sort -u || true)
if [ -z "${SYMS:-}" ]; then
  echo "skia not importable yet — install skia-python first" >&2
  exit 1
fi
{ echo '/* auto-generated GL/EGL stubs */'; echo 'typedef void* P;'
  while read -r s; do echo "P $s(){return 0;}"; done <<< "$SYMS"; } > stubs.c
gcc -shared -fPIC -o libEGL.so.1 stubs.c
gcc -shared -fPIC -o libGL.so.1  stubs.c
echo "wrote $OUT/libEGL.so.1 and $OUT/libGL.so.1 ($(wc -l < stubs.c) lines)"
echo "run with: LD_LIBRARY_PATH=$OUT python3 ..."
