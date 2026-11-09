#!/usr/bin/env bash
# bootstrap.sh — rebuild the HyperFrames render toolchain in a fresh Arena sandbox.
#
# Design notes (learned the hard way, do not "simplify" these away):
#   * No sudo / no apt. This sandbox has no Debian mirror and no Google storage,
#     so `apt-get install ffmpeg` and `npx hyperframes browser ensure` both fail.
#   * Only registry.npmjs.org + github.com are reachable. Every binary below
#     therefore comes from npm.
#   * Chromium is the AWS-Lambda build (@sparticuz/chromium): it ships its own
#     NSS libs and SwiftShader, so it needs no system libraries. Its GL .so files
#     must be extracted NEXT TO the binary or GLDisplayEGL fails -> SIGTRAP.
#   * The HyperFrames scaffold loads GSAP from jsDelivr. That host is blocked, so
#     GSAP is vendored from npm and must be script-src'd locally.
#
# Idempotent. Safe to re-run. Takes ~40s cold, ~5s warm.

set -euo pipefail

ROOT="${ROOT:-$HOME/.local}"
BIN="$ROOT/bin"
HF_DIR="$ROOT/hf"            # hyperframes itself
RT_DIR="$ROOT/hf-runtime"    # ffmpeg, ffprobe, chromium, gsap, mespeak
CHROME="$ROOT/chrome"
VENDOR="$ROOT/vendor"
CACHE="$HOME/.cache"

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }

mkdir -p "$BIN" "$RT_DIR" "$CHROME" "$CACHE/hf-tmp" "$CACHE/hf-frames" "$VENDOR/gsap"

# ---------------------------------------------------------------------------
# 1. ffmpeg + ffprobe  (static builds published to npm)
# ---------------------------------------------------------------------------
if ! "$BIN/ffmpeg" -version >/dev/null 2>&1; then
  say "Installing ffmpeg + ffprobe from npm"
  cd "$RT_DIR"
  [ -f package.json ] || npm init -y >/dev/null 2>&1
  npm i --no-audit --no-fund @ffmpeg-installer/ffmpeg @ffprobe-installer/ffprobe >/dev/null
  ln -sf "$(node -e "console.log(require('@ffmpeg-installer/ffmpeg').path)")" "$BIN/ffmpeg"
  ln -sf "$(node -e "console.log(require('@ffprobe-installer/ffprobe').path)")" "$BIN/ffprobe"
else
  say "ffmpeg already present"
fi

# ---------------------------------------------------------------------------
# 2. Chromium + SwiftShader  (works only because it is self-contained)
# ---------------------------------------------------------------------------
if ! "$BIN/chrome" --version >/dev/null 2>&1; then
  say "Installing Chromium (AWS Lambda build) from npm"
  cd "$RT_DIR"
  [ -f package.json ] || npm init -y >/dev/null 2>&1
  npm i --no-audit --no-fund @sparticuz/chromium >/dev/null
  node -e '
    const fs=require("fs"), zlib=require("zlib"), path=require("path");
    const bin=path.join("node_modules/@sparticuz/chromium/bin");
    const out=process.argv[1];
    fs.writeFileSync(path.join(out,"chromium"),
      zlib.brotliDecompressSync(fs.readFileSync(path.join(bin,"chromium.br"))));
    for (const [src,dst] of [["al2023.tar.br","al2023.tar"],["swiftshader.tar.br","swiftshader.tar"]]) {
      fs.writeFileSync(path.join(out,dst),
        zlib.brotliDecompressSync(fs.readFileSync(path.join(bin,src))));
    }
  ' "$CHROME"
  chmod +x "$CHROME/chromium"
  tar -xf "$CHROME/al2023.tar" -C "$CHROME" && rm -f "$CHROME/al2023.tar"
  # GL libs must live beside the binary — this is the SIGTRAP fix.
  tar -xf "$CHROME/swiftshader.tar" -C "$CHROME" && rm -f "$CHROME/swiftshader.tar"
  chmod 755 "$CHROME/chromium"
  chmod 644 "$CHROME"/*.so* 2>/dev/null || true
else
  say "Chromium already present"
fi

# Stable wrapper: hyperframes launches HYPERFRAMES_BROWSER_PATH, and any flag we
# put here is applied to every launch.
cat > "$BIN/chrome" <<WRAP
#!/bin/sh
CHROME_ROOT="\${CHROME_ROOT:-$CHROME}"
export LD_LIBRARY_PATH="\$CHROME_ROOT/lib:\$CHROME_ROOT:\$LD_LIBRARY_PATH"
[ -f "\$CHROME_ROOT/vk_swiftshader_icd.json" ] && export VK_ICD_FILENAMES="\$CHROME_ROOT/vk_swiftshader_icd.json"
exec "\$CHROME_ROOT/chromium" \\
  --no-sandbox --disable-setuid-sandbox --disable-dev-shm-usage \\
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \\
  --in-process-gpu --no-zygote \\
  "\$@"
WRAP
chmod +x "$BIN/chrome"

# ---------------------------------------------------------------------------
# 3. hyperframes + GSAP
# ---------------------------------------------------------------------------
if [ ! -x "$HF_DIR/node_modules/.bin/hyperframes" ]; then
  say "Installing hyperframes"
  mkdir -p "$HF_DIR" && cd "$HF_DIR"
  [ -f package.json ] || npm init -y >/dev/null 2>&1
  npm i --no-audit --no-fund hyperframes >/dev/null
else
  say "hyperframes already present"
fi

if [ ! -s "$VENDOR/gsap/gsap.min.js" ]; then
  say "Vendoring GSAP from npm (jsDelivr is blocked)"
  cd "$RT_DIR"
  npm i --no-audit --no-fund gsap >/dev/null
  cp node_modules/gsap/dist/gsap.min.js node_modules/gsap/dist/ScrollTrigger.min.js "$VENDOR/gsap/"
fi

# Fonts must be self-hosted: a font CDN is just another blocked host that aborts
# the render, and a fallback face silently changes every measurement.
if [ ! -s "$VENDOR/fonts/space-grotesk-latin-700-normal.woff2" ]; then
  say "Installing fonts from npm (@fontsource)"
  cd "$RT_DIR"
  npm i --no-audit --no-fund @fontsource/space-grotesk @fontsource/inter >/dev/null
  mkdir -p "$VENDOR/fonts"
  cp node_modules/@fontsource/space-grotesk/files/space-grotesk-latin-700-normal.woff2 \
     node_modules/@fontsource/space-grotesk/files/space-grotesk-latin-500-normal.woff2 \
     node_modules/@fontsource/inter/files/inter-latin-400-normal.woff2 \
     "$VENDOR/fonts/"
fi

# ---------------------------------------------------------------------------
# 4. env file + doctor
# ---------------------------------------------------------------------------
cat > "$ROOT/env.sh" <<ENV
# source this before any hyperframes command
export PATH="$BIN:\$PATH"
export TMPDIR="\$HOME/.cache/hf-tmp"
export HYPERFRAMES_EXTRACT_CACHE_DIR="\$HOME/.cache/hf-frames"
export HYPERFRAMES_BROWSER_PATH="$BIN/chrome"
export PRODUCER_PUPPETEER_PROTOCOL_TIMEOUT_MS=300000
# GSAP + fonts, copied into each new film by scripts/new-film.sh
export GSAP="$VENDOR/gsap"
export FONTS="$VENDOR/fonts"
# python used by scripts/qc.py (needs pillow + numpy)
export QC_PYTHON="$ROOT/venv/bin/python"
ENV

say "Wrote $ROOT/env.sh"
# shellcheck disable=SC1091
. "$ROOT/env.sh"

say "Doctor:"
cd "$HF_DIR"
npx hyperframes doctor 2>&1 | grep -E '✓|✗' | grep -vE 'whisper|Docker|TTS|BGM|onnxruntime|genai' || true

# ---------------------------------------------------------------------------
# 5. QC venv — pillow + numpy, used by scripts/qc.py
# ---------------------------------------------------------------------------
if [ ! -x "$ROOT/venv/bin/python" ] || ! "$ROOT/venv/bin/python" -c "import PIL, numpy" 2>/dev/null; then
  say "Setting up QC venv (pillow + numpy)"
  python3 -m venv "$ROOT/venv" 2>/dev/null || true
  "$ROOT/venv/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
  "$ROOT/venv/bin/pip" install --quiet pillow numpy >/dev/null
else
  say "QC venv already present"
fi

. "$ROOT/env.sh"

cat <<'DONE'

Next:
  source ~/.local/env.sh
  cd <project> && npx hyperframes render -w 1 --low-memory-mode

Blocked in this sandbox (budget for it):
  * hyperframes tts  -> Kokoro weights are on HuggingFace (unreachable)
  * models install parakeet -> same
  * any CDN asset    -> copy it into the project and script-src it locally
DONE
