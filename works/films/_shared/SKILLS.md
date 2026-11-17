# Two English ads, same medium as the crow film

`zerovast-ad` (29.5 s) and `vignan-ad` (26.6 s), both 1080x1920, English, one American voice.

## What the five skills actually do here

| Skill | Contribution |
|---|---|
| **claude-drawing-skill** (`grainbook`) | Paints every set, in `_shared/eng/platekit.py`. Four ZeroVast plates (Khammam dusk, midnight desk, dark room, sign-off) and five Vignan plates (study, textbook spread, roadmap sheet, room, sign-off). Built as three values plus one light source per plate; light pools are concentric washes, not glow ellipses. `paper.jpg` is pressed over every frame in screen space. |
| **cinematic-skill** (`engine.py`) | The renderer, camera splines, sound bed (`build_sfx.py`, `mix_soundtrack.py`) and the mix at -15 LUFS. `engine2.py` re-bases the world so one design unit is one output pixel. |
| **bang-motion** | One stage per beat, camera *inside* the set (never a wide of a wide), hard cuts between sets, no caption blocks that fight the props. |
| **huashu-art-motion** | Cut on the breath between lines; entry moves 0.6-1.5 s eased; **one** motivated move per shot; pull out after a push. The shot lists follow it literally. |
| **vox-director** | "Camera move and element motion are separate axes." Hence the props (browser, editor, phone, folder, app cards) landing and drifting inside a locked framing, plus the ambient layer. |

## The five defects that made it look unfinished (all now fixed)

1. **Unbalanced `c.save()`** in screen-space cards left the camera transform applied to the next
   item, so a panel of the previous scene appeared over the new one. Every `screen()` now has exactly
   one matching restore.
2. **Motion blur across a cut.** engine averages sub-frames; where the exposure window straddled a cut
   the outgoing set and the incoming one were drawn into the same frame. `Renderer2.frame` now forces
   a single sub-frame at (and near) any cut and at any set change.
3. **Stage pads overlapping.** Each set's beats were padded by 0.55 s, so two plates covered the same
   instant, and the plate could switch to the NEXT set before its cut. Pads are now 0.22 s, meeting at
   the cut, and when two sets do overlap the one that started most recently owns the frame.
4. **Props outliving their shot.** Keys hung off a narration line's END look fine in a beat table and
   then float over the next set. Every prop is now keyed off the film's named cut constants (`C_DESK`,
   `C_GLASS`, ...) and exits before them; captions are clipped at the cut too.
5. **A `-t` after the `-i`** in the voice-padding filter cut every take to 0.09 s. `-t` is an input
   option: it belongs before the input.

## Pipeline (rebuild from scratch)

```sh
# toolchain (per session; /tmp is wiped)
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install skia-python numpy pillow uharfbuzz freetype-py imageio-ffmpeg==0.6.0
#   + GL stub libs in /tmp/gl, ffmpeg symlinked into /tmp/fbin, cinematic-skill cloned to /tmp/cs

# sets
cd works/films/zerovast-ad && python3 ../_shared/eng/platekit.py --which zerovast --out assets/plates

# voice -> timing (the scene is timed from the voice, never from guesses)
python3 ../_shared/eng/vo.py --project . --join

# cues -> score -> mix
CF=/tmp/cs/cinematic-skill/skills/cinematic-film/scripts
python3 tools/render2.py --project . --cues
python3 ../_shared/eng/make_score.py --seconds 29.53 --out audio/score.wav --mood zerovast
python3 $CF/build_sfx.py --project .
python3 $CF/mix_soundtrack.py --project . --music audio/score.wav --music-db -7 --sfx-db -8

# picture
python3 tools/render2.py --project . --size 1080x1920 --audio audio/mix.m4a --out out/final.mp4 --workers 2
ffmpeg -i out/final.mp4 -c:v libx264 -crf 27 -pix_fmt yuv420p -c:a aac -b:a 128k preview_540.mp4
```

`_shared/run.sh` sets `CF_ENGINE`, the GL stub path and the shared art library in one go.

## Facts used on screen (verified, not invented)

**ZeroVast** -- from `zero-vast.vercel.app`: hand-written semantic HTML/modern CSS/vanilla JS, no
page-builder bloat or framework tax, Core Web Vitals budgets (LCP, CLS, INP) set before the build,
WCAG 2.2 AA built in, repository + deploy steps + walkthrough handed over, one point of contact,
Khammam, Telangana, `themerchantofdeath2011@gmail.com`. No prices, testimonials or client counts.

**Vignan Vidyanikethan AI** -- live at **`vignanvidyanikethanai.onrender.com`** (note: no dashes; the
dashed host 404s). From the app and its repo: textbook-grounded answers that cite the page, a page
reader, quiz, exam practice with JEE/NEET/AP EAPCET timing, flashcards, an offline engine that needs
no key or download, on-device models (Llama 3.2 1B / SmolLM2 / Qwen2.5) after one download, `npm run
check` in CI, free to try, MIT licensed, built by a student of Vignan Vidyanikethan English Medium
High School for the INSPIRE-MANAK science fair.

The demo answer on screen (a heavier ball does not fall faster; `a = g`) is textbook physics, which is
the kind of thing the app cites -- it is not a screenshot of someone else's session.
