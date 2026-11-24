# Byte Sized Explainer — how the channel is built, and what I copied

Analysis of **[@bytesizedexplainer](https://youtube.com/@bytesizedexplainer)** (~136K
YouTube, 178.9K TikTok), then a sample film made in this repo with the same grammar.

Everything here comes from the channel's public pages, its own descriptions, and the
standard reference facts about display engineering. No claim in the film is the
channel's opinion, and nothing is copied from its audio or footage.

## 1 · What the channel actually is

Not a talking-head account. It is **"Every X Explained"** — a catalogue channel where
the title is always a complete set:

> Every GPU Feature Explained · Every TV Screen Explained · Every Mobile Network
> Generation Explained · Every RAM Size Explained · Every Intel CPU Explained ·
> Every Computer Port Explained · Every Wi-Fi Generation Explained

The niche is precise: **take a thing you own and use daily, enumerate its whole family,
and give each member one mechanism and one tradeoff.** The value is not depth. It is
*completeness plus a comparison* — you leave knowing why the cheap one is cheap.

| what | detail |
|---|---|
| length | 3–8 minutes on YouTube; the same edit is cut into vertical Shorts per beat |
| narration | **text-to-speech**, and the channel says so openly ("my place is too noisy to record clean audio") |
| visuals | flat diagrams, big labels, one accent colour per subject — no footage, no stock |
| structure | cold open → one beat per member → comparison table → question |
| growth | TikTok is where the reach is (3.6M likes); YouTube is the long-form home |

That last row is the actual business model and it is worth stating plainly: the same
material is published twice, as a long-form video and as a series of vertical clips.

## 2 · The edit, which is what makes it work

The channel does five things in this order, every time:

1. **Name the number immediately.** "Every", stated in the first second. The viewer
   knows the shape and length of the promise before deciding to stay.
2. **One beat per member, always the same filling order** — index number, term,
   then *how it works*, never *what it is*. CRT is not "an old TV"; it is "an electron
   gun paints one dot at a time."
3. **A diagram that is drawn as it is described.** The beam sweeps the phosphor while
   the narration says so. Nothing decorative, nothing animated for its own sake.
4. **A spec chip row** — three numbers or tradeoffs, boxed, tiny, at the bottom.
   This is where the viewer learns the catch.
5. **A comparison table, then a question.** The table pays off the "every" in the
   title; the question is the comment section.

The close is the distribution. "Which one did you grow up with?" is a question nobody
can answer silently.

## 3 · The sample: *Every TV Screen Explained*, 80 s

`01-every-tv-screen-vertical-1080x1920.mp4` — 1080×1920, 30 fps, H.264 + AAC, 4.0 MB.

Five screens, in the order the technology arrived: **CRT → LCD → Plasma → OLED →
MicroLED.** Each beat gets an index, a mechanism sentence, three chips, and a drawing
that moves while the sentence is read.

The comparison table is the payoff:

| screen | blacks | bright | burns in | from |
|---|---|---|---|---|
| CRT | perfect | dim | no | 1934 |
| LCD | grey | high | no | 1973 |
| Plasma | perfect | medium | yes | 1997 |
| OLED | perfect | medium | yes | 2007 |
| MicroLED | perfect | very high | no | 2020s |

### What is faithful, and what is a placeholder

Being clear about this matters more than the render:

| element | status |
|---|---|
| structure, pacing hook, beat order, chip row, table, sign-off | **faithful to the channel** |
| diagrams (CRT funnel, LCD shutters, plasma cells, OLED pixel, MicroLED array) | **real schematics**, not decoration |
| facts and figures | **standard display engineering**; figures are typical values, not guarantees |
| type hierarchy, one accent colour per beat, white field | **faithful** — the channel's own look |
| narration | **placeholder.** There is no TTS voice in this sandbox, so `audio.py` synthesizes formant bursts with the rhythm and length of each line. It is not words. It proves the audio path and fixes the pacing a real voice will drop into. |
| music | none, deliberately — the channel has none either |

The voice is the one thing to replace before this is publishable. Everything else is
the finished grammar.

## 4 · How it is built

Three files, no browser, no WebGL, no CDN — it renders here:

```
source/copy.py     the script: five beats, the table, the sign-off
source/draw.py     one schematic function per screen, all PIL shapes
source/layout.py   the page: header, index, term, mechanism line, chips
source/audio.py    the narration placeholder and the bed
source/render.py   frames → ffmpeg; also rewrites beat durations from word count
```

Beat length is **derived from the copy**, not fixed: words ÷ 2.6 words-per-second,
plus padding. Change a sentence and the card resizes, which is how the real channel is
paced — the cut follows the line.

```bash
python3 render.py --survey                  # timings + a contact sheet, no video
python3 render.py --out out.mp4             # full 1080x1920 render (~2.5 min)
python3 audio.py --out ../assets/narration.wav
```

## 5 · What the QC gate caught

Nothing here was trusted by eye. `tooling/qc.py` measured the render, and it found
four real bugs that would have shipped:

- **A line of copy ran off the right edge.** The LCD mechanism sentence was hard-coded
  to break at a point that no longer fit at 66 px. Fixed by auto-fitting the type to
  the margin — the fix, not the instance.
- **The header sat outside the safe area** at y=78, which a phone's status bar covers.
- **The footer sat outside it at the bottom**, under the gesture bar.
- **The `★` glyph rendered as tofu** — the bundled font has no such character.

It also exposed a **fake `ffprobe`** left in this sandbox from an earlier session: a
shim that hardcoded "one video stream, no audio" for every file. The QC gate was
therefore passing audio checks that it never actually made. Replaced with a real
parser before any of the above was believed.

Final measurement: **8/9 gates pass.** The one that fails is `duration_15_25s`,
which is correct for this repo's 20-second shorts and wrong for a 3–8 minute
explainer. It was not waved away — the format genuinely is not 20 seconds.
