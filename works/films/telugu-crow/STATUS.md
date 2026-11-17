# తెలుగు కాకి కథ — v2 state

## What is finished (verified this session)

- **Shot list instead of one drifting camera.** `scene2.py` now has `shots = [...]` with hard cuts at
  beat boundaries (`L(n)`) and *one* motivated move inside each shot (push under the title, pull back
  at the reveal, slow push through the stone sequence). No more panning between unrelated setups.
- **Card transform fixed.** Captions/bubbles/quiz are drawn with the exact inverse of the renderer's
  world transform (`T(c) R(-rot) S(1/k) T(-W/2,-H/2) S(sc)`), so design-space coordinates are
  deterministic: captions are centred and stop creeping sideways as the camera moves.
- **Every beat has a set.** `ALIAS` maps each script beat to `field` / `pot` / `quiz`; before, beats
  without a stage fell back to the bare clear colour (that is where the flat cream frames came from).
- **Bubbles measure themselves.** `BubbleCards` lays out the text first, sizes the bubble to it,
  shrinks on overflow and clamps inside the safe area — no more text spilling out of the bubble.
- **Quiz card** re-laid out (plaque 548, chips 730 / 878), stars on the answer chip; the lizard no
  longer stands on top of the correct answer.
- **Stone pile** moved to (252,1560) with bigger stones so "పక్కనే గులకరాళ్ళు!" shows stones.
- **Sky** is a proper vertical gradient again (the cream wash was a 4-stop ramp that read as a band).
- Narration timing rebuilt from the real takes; sfx (30 cues) + score + mix at -15.0 LUFS.

## What is broken: the voice takes

`audio/lines/seg01..10.mp3` and `seg21..24.mp3` hold **silence** (TTS placeholder) because the
sandbox reset wiped the recordings — `*.mp3` is git-ignored, so only the ones recorded after the last
reset survived (`seg11..20`, which are real). Everything downstream was rebuilt from what exists.

**Next step, in this order:**

1. Re-record voice lines 1–10 and 21–24 with `voice-07` (**10 calls per turn**, so two turns),
   saving to `works/films/telugu-crow/audio/v2/segNN.mp3`. Short lines only (2–5 words) — long
   sentences make the TTS loop.
2. `cp audio/v2/seg*.mp3 audio/lines/` and delete the matching `*.silent` markers.
3. Rebuild audio and re-render:
   ```
   python3 tools/make_placeholders.py --project . --cps 16.5
   python3 tools/build_narration_local.py --project . --lead 0.7 --tail 1.8
   python3 tools/render2.py --project . --cues
   python3 /tmp/cs/skills/cinematic-film/scripts/build_sfx.py --project .
   python3 tools/make_score.py --seconds 54.9 --out audio/score.wav
   python3 /tmp/cs/skills/cinematic-film/scripts/mix_soundtrack.py --project . \
       --music audio/score.wav --music-db -10 --sfx-db -8 --music-level 0.10 --music-eq-dip 2
   python3 tools/render2.py --project . --size 1080x1920 --audio audio/mix.m4a --out out/final.mp4
   ffmpeg -i out/final.mp4 -c:v libx264 -crf 30 -pix_fmt yuv420p -c:a aac -b:a 112k preview_v2_540.mp4
   ```
4. **Commit the mp3s.** `git add -f audio/v2/*.mp3` — otherwise the next reset loses them again.

## Toolchain (rebuild every session, /tmp is ephemeral)

```
python3 -m venv /tmp/venv
/tmp/venv/bin/pip install skia-python numpy pillow fonttools uharfbuzz imageio-ffmpeg
# ffmpeg -> /tmp/fbin/ffmpeg from imageio_ffmpeg.get_ffmpeg_exe()
# ffprobe -> /tmp/fbin/node_modules/@ffprobe-installer/linux-x64/ffprobe
# skia needs stub libEGL.so.1 / libGL.so.1 in /tmp/gl (nm -D --undefined-only, emit void f(void){})
```

Render: `PATH=/tmp/fbin:$PATH LD_LIBRARY_PATH=/tmp/gl PYTHONPATH=tools /tmp/venv/bin/python tools/render2.py …`
