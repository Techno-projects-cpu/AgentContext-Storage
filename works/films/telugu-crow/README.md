# ఇలా ఉండేది గాని — దాహంగా ఉన్న కాకి

A Telugu cartoon for children, built with the cinematic-film engine. 1080×1920, 24 lines, ~1:40 at
the time of writing.

## Status at hand-off

**Picture, sound design, music and captions are finished. The voice is 6 of 24 lines.**

The hosted speech service returns a busy-loop (50 s of one repeated syllable) for most long
sentences in Telugu. Short lines of two to four words come through fine, which is why the script
was rewritten as 24 short punchy lines — it reads better for children anyway.

| state | file |
|---|---|
| voiced and promoted | seg01–seg04, seg06, seg08–seg10 (`audio/lines/segNN.mp3`) |
| still a placeholder | everything else (`audio/lines/segNN.silent` marks them) |
| all gold takes (some rejected) | `audio/takes/` |

### Finishing the voice

1. Record into `audio/takes/segNN_x.mp3` (never straight into `audio/lines` — a loop must not
   overwrite a good take). At most ten clips per turn.
2. Audit: `python tools/audit_takes.py --project . --out /tmp/audit.png` draws a spectrogram per
   take. **Look at it.** Real speech has moving formants and gaps; a loop is one column repeating.
   The numeric score in `tools/check_takes.py` is a hint, not a verdict — repeated phonemes fool it.
3. Promote the good ones, and make `audio/segments.json`'s `vo`/`caption` say exactly what the clip
   says (word highlighting is timed off the caption).
4. `python tools/make_placeholders.py --project .` → `tools/build_narration_local.py` →
   `tools/make_score.py --seconds <total>` → `render.py --cues` → bundle `build_sfx.py` →
   `mix_soundtrack.py --music audio/score.wav --music-db -8 --sfx-db -6 --music-level 0.10`
   → `tools/make_srt.py` → full render.

## Rebuilding the toolchain (each fresh sandbox)

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip -q install skia-python numpy pillow imageio-ffmpeg fonttools brotli uharfbuzz
# skia needs libGL/libEGL stubs: build them from the shared object's own symbol strings
#   strings skia*.so | grep -E '^(egl|glX|gl)' → void name(void){} → gcc -shared -fPIC
# ffmpeg: imageio_ffmpeg.get_ffmpeg_exe(); ffprobe: npm @ffprobe-installer/linux-x64@5.2.0
git clone --depth 1 https://github.com/Moh4696/cinematic-skill.git /tmp/cs
export LD_LIBRARY_PATH=/tmp/gl PATH=/tmp/fbin:$PATH
```

## What is in here

| file | what it is |
|---|---|
| `scene.py` | the whole film: backdrop, pot, crow, lizard, pebbles, effects, seven screen-space text cards |
| `tools/ty.py` | **Telugu text that actually shapes.** uharfbuzz does the shaping, skia draws the outlines. Skia's own `drawString` scrambles Telugu conjuncts, so every glyph in the film goes through here. Gives word-by-word highlighting, per-cluster reveals and measurement |
| `tools/cartoon.py` | flat-vector primitives: the cut-away pot, crow with flapping wing, lizard, sun with a face, pebbles, bubbles, idea bulb, hearts, sweat |
| `tools/make_score.py` | the music bed, generated from scratch (marimba + pad, C major, 108 bpm) — no samples |
| `tools/make_placeholders.py` | silent clips at reading pace so the film can be cut and rendered before the voice exists |
| `tools/audit_takes.py`, `tools/check_takes.py` | telling real speech from the service's looped garbage |
| `fonts/tel400.ttf`, `tel700.ttf` | Noto Sans Telugu merged with Noto Sans latin (punctuation lives only in the latin file) |

## Design notes

- World units are 4K px at zoom 1. A 1080-wide 9:16 frame shows `3840/z × 6827/z` world px, and one
  screen px is `1/(1080/3840 · z)` world units.
- Text is drawn in **screen space**: each card converts its anchor through `Sc.p()` and then scales
  by `Sc.i` (= world px per screen px), so a caption is 58 px in every shot regardless of zoom.
- The pot is a cut-away: water level and the stone pile are visible at once, because the whole trick
  of the story is "the stones push the water up" and the audience must see both at the same time.
- Every stone landing comes from one list (`drops`), shared by the pot, the falling stones, the
  Telugu numerals (౧ ౨ ౩), the టప్! pops and the sound cues — so picture and sound cannot drift.
- The sun gets crosser as the drought bites and sets behind the hills for the moral.
