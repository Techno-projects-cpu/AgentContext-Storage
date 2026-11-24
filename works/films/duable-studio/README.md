# Duable — the studio film

`05-duable-studio-1080x1920.mp4` · 24.8 s · 1080×1920 · 30 fps · H.264 + AAC ·
score + narration, mastered to −14 LUFS.

`05-duable-studio-1080x1920-music-only.mp4` — same picture and score, no voice.

---

## The story

It is not a list of services. It is the shape of a conversation, told in the
order a client actually thinks:

| # | time | beat | what the voice says |
|---|---|---|---|
| 1 | 0.0–2.8 | **A sentence** — a full stop alone, then *"I need a thing made."* | *I need a thing made.* |
| 2 | 2.8–6.6 | **A service** — "YOU SAY" above a rule, "WE HAVE *Paid advertising. One of twenty-four.*" below | *Every service here starts with a sentence like that.* |
| 3 | 6.6–9.9 | **The catalogue** — 3D stacks rise into place: 8 / 4 / 5 / 7 plates | *Twenty-four services. Four categories.* |
| 4 | 9.9–13.6 | **One of them is yours** — the camera holds still and one plate lifts out of its stack and hangs there | *One of them is yours.* |
| 5 | 13.6–17.2 | **The answer, unpacked** — "THEY SAID" / "DUABLE SAYS", the real ask mapped to the real names | *They said: make the story and visuals feel connected.* |
| 6 | 17.2–20.8 | **Four ways in** — the four chapters with the site's own headlines and counts | *Design. Automate. Edit. Position.* |
| 7 | 20.8–24.8 | **The answer, incoming** — the plate comes back, the mark, the line | *Duable. A studio with a service for that.* |

The bookend: beat 1 opens on the *end* of a sentence, beat 7 answers it. The same
full stop appears in both. Beat 3 is a catalogue of twenty-four; beat 4 is a
catalogue of one. That is the whole argument of the film.

The running head (`DUABLE · 01 / 07`) is the only element that never changes, so
seven beats read as one film.

## Three engines, one pipeline

| engine | what it contributes |
|---|---|
| `engines/sr71-3d` — NumPy software rasteriser | the plates: 24 of them, the lift, the payoff |
| `works/films/_shared/eng` — skia canvas | all the type: real glyph shaping, masks, rules, arcs |
| `engines/brag` + `agent-context/BRAG-PROMPT.md` | the grammar: craft floor and shot discipline, enforced in code (30 px type, 0.45 s expo, frame 0 inked, pure `f(t)`) |

## The score (`score.py`)

Synthesised from partials, no samples: felted piano (six partials decaying at
their own rates), inharmonic celesta, filtered pad, lowpassed bass, soft felt
thump, into a synthetic convolution plate. The harmony turns **on the cuts** —
Am9 → Fmaj7 → G7 → Em7 → Cmaj7 → Dm7 → Am(add9) — so it opens unresolved and
closes on the chord it started on, which is the film's bookend in music.

Measured: 17 % bass, 50 % mid, centroid ~543 Hz, stereo side/mid 0.24 —
deliberately narrow, because a phone speaker folds to mono.

## What was actually hard

1. **The bevel was broken, and had been for every render.** `box()` built its inner
   shell as `core + core*2*bevel`, which scales from the ORIGIN rather than
   offsetting along each face — on a thin slab that spawns a floating copy of the
   plate. The hero plate kept reading as "a green card with a flap". The bridge
   quads also connected to vertex `+4` (the opposite face) instead of `+8`.
2. **A frame solved by projected width leaves the subject in a mostly empty
   canvas.** The stacks occupied the top third of an 820×760 render. Cropping per
   frame is not an option (the bbox changes as the subject turns, so the crop
   rescales every frame and the object pumps). Fix: measure the bbox at the
   extremes of the shot, take the union, use ONE window for every frame.
3. **Frame 0 is the thumbnail.** The cold open was designed to start on a full
   stop, and `span(t, 0.02, 0.5)` is exactly 0 at t=0 — so the first frame was a
   blank page. QC caught it at 0.19 % ink. The sentence now starts ON frame 0.
4. **Pitch vs yaw.** Rotating a plate about X rolls a wafer over and it disappears
   (a plate is 0.13 thick against a 0.52 face). Turning it about **Y** swings the
   broad face into view. The lift yaws; it does not pitch.
5. **A 25.4 s cut is over a 25 s gate** — and a 24.8 s film loses its last line
   unless every entrance is 0.2 s earlier. Both had to move together.

## Facts

Chapter kickers and headlines are the site's own category pages, verbatim.
Counts 8 / 4 / 5 / 7, the 24 service names in the site's order. No prices, no
client counts, no testimonials — spoken or written.

## Build

```bash
PYTHON=python3 bash tools/skia_stubs.sh /tmp/gl     # CPU skia still links libEGL/libGL
cd source
LD_LIBRARY_PATH=/tmp/gl python3 film.py --still 11.6
LD_LIBRARY_PATH=/tmp/gl python3 film.py \
    --out ../05-duable-studio-1080x1920.mp4 \
    --clean-out ../05-duable-studio-1080x1920-music-only.mp4
python3 score.py --out /tmp/score.wav    # music alone
python3 mix.py   --out /tmp/mix.wav      # score + voice, mastered
```

## QC

`tooling/qc.py --safe 0.90` → **10/10** on both cuts, motion in 13/13 sampled
intervals, `audio_has_voice` true on the narrated cut (0.47) and false on the
music-only one (0.31).
