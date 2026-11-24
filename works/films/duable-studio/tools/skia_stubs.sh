#!/usr/bin/env bash
# A CPU-only skia wheel still links libEGL/libGL. This writes minimal stubs so
# `import skia` succeeds on a box with no GL stack. Nothing on our path ever
# creates a GPU context, so every stub returning 0 is correct.
set -euo pipefail
OUT=${1:-/tmp/gl}
mkdir -p "$OUT"
cd "$OUT"
PY=${PYTHON:-python3}
# locate the extension module directly: importing it would fail before the stubs exist
SKIA_SO=$($PY - <<'EOF'
import glob, os, sysconfig
pats = ["skia*.so", "skia*.pyd"]
for d in (sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]):
    for pat in pats:
        hits = glob.glob(os.path.join(d, pat))
        if hits:
            print(hits[0]); raise SystemExit
EOF
)
SYMS=$(nm -D --undefined-only "$SKIA_SO" 2>/dev/null \
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
echo "run with: LD_LIBRARY_PATH=$OUT $PY ..."
