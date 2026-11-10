#!/usr/bin/env bash
# make-demo-audio.sh <project-dir> [seconds]
#
# Generates PLACEHOLDER audio so the pipeline can be exercised end to end without
# a network voice model (Kokoro's weights are unreachable here).
#
#   assets/vo.wav     — a formant "speech-like" tone with word-length gaps.
#                       It is NOT words. It exists to prove the audio path works.
#   assets/music.wav  — a low bed, so ducking can be measured.
#
# Replace both with a real VO before calling anything finished. qc.sh reports the
# measured level of whatever is in there, so a silent file cannot pass unnoticed.
set -euo pipefail

DIR="${1:?usage: make-demo-audio.sh <project-dir> [seconds]}"
SECS="${2:-17.5}"
FF="${FF:-${HOME}/.local/bin/ffmpeg}"
[ -x "$FF" ] || FF="$(command -v ffmpeg)"

mkdir -p "$DIR/assets"

# --- voice: 4 "words" per ~3s phrase, then a gap, repeating -------------------
python3 - "$DIR/assets/vo.wav" "$SECS" <<'PY'
import math, random, struct, sys, wave

out, total = sys.argv[1], float(sys.argv[2])
SR = 48000
random.seed(7)                      # deterministic: no Math.random anywhere
frames = bytearray()

def envelope(i, n, attack=0.02, release=0.08):
    a, r = int(n * attack), int(n * release)
    if i < a: return i / max(a, 1)
    if i > n - r: return max(0.0, (n - i) / max(r, 1))
    return 1.0

t = 0.0
while t < total:
    phrase = min(2.6, total - t)
    if phrase <= 0.05: break
    # a phrase is ~4 syllables of 0.3-0.45s with 60ms gaps
    words, acc = [], 0.0
    while acc < phrase - 0.2:
        w = random.uniform(0.28, 0.46)
        words.append(w); acc += w + 0.06
    for w in words:
        n = int(w * SR)
        f0 = random.uniform(110, 150)
        for i in range(n):
            tt = i / SR
            # crude formants + glottal buzz
            v = 0.34 * math.sin(2 * math.pi * f0 * tt)
            v += 0.16 * math.sin(2 * math.pi * f0 * 2.7 * tt)
            v += 0.10 * math.sin(2 * math.pi * f0 * 5.1 * tt)
            v *= envelope(i, n)
            frames += struct.pack("<h", int(max(-1, min(1, v)) * 9000))
        gap = int(0.06 * SR)
        frames += b"\x00\x00" * gap
    pause = int(random.uniform(0.35, 0.6) * SR)
    frames += b"\x00\x00" * pause
    t += phrase + pause / SR

with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(bytes(frames))
print(f"vo: {out}")
PY

# --- music bed: slow minor triad, quiet -------------------------------------
"$FF" -y -hide_banner -loglevel error \
  -f lavfi -i "sine=frequency=55:duration=${SECS}" \
  -f lavfi -i "sine=frequency=82.4:duration=${SECS}" \
  -f lavfi -i "sine=frequency=110:duration=${SECS}" \
  -filter_complex "[0][1][2]amix=inputs=3:weights=1 0.6 0.4,volume=0.5,tremolo=f=0.18:d=0.4[a]" \
  -map "[a]" -ar 48000 -ac 1 "$DIR/assets/music.wav"

echo "music: $DIR/assets/music.wav"
echo
echo "These are PLACEHOLDERS. Swap in a real voiceover before delivery."
