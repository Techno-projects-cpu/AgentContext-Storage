# Influx Picture — how the channel is built, and what I copied

Analysis of **[@influxpicture](https://youtube.com/@influxpicture)** (3.85K subs,
13 short-form videos at the time of writing), then a sample film made in this
repo with the same grammar. Everything here is from the channel's public pages,
its own video descriptions and the published facts the videos cite.

## 1 · What the channel actually is

Not a film studio account. It is a **one-idea-per-video military-technology
explainer channel**, entirely in vertical Shorts:

| Video | Views |
|---|---|
| Why the F-47 Has No Tail | 2.9 M |
| This Fighter Jet Got a Laser on it? | 533 K |
| Hitler's Plywood Stealth Bomber | 485 K |
| This Nazi Fighter Had to Land Backwards | 445 K |
| Why Fighter Jets Turn Sideways After Firing a Missile | 423 K |
| The Navy's $20 Billion Fighter Nobody Can See | 212 K |

The niche is precise: **machines, weapons and buildings, told through one
counter-intuitive mechanical fact.** Not history, not news — *"the one strange
detail most people never noticed"*, which is the channel's own bio line. That is
the entire editorial thesis and it is worth stealing.

## 2 · The format, reconstructed

From the video pages, their descriptions and the way the titles are written:

1. **Title = the paradox, not the subject.** "Why the F-47 **Has No Tail**",
   "**Couldn't Steer**", "**Made of Plywood**", "**Aimed With His Feet**". Every
   title is a contradiction a viewer cannot resolve without watching.
2. **The first two seconds state the contradiction**, usually over a 3D model
   already in motion. No logo, no intro, no "in this video".
3. **One mechanism per video.** The F-47 short explains *only* why removing the
   tail works (fly-by-wire, split drag rudders, differential thrust) and states
   plainly what is **not** public: *"The Air Force has not said how the F-47 does
   it."*
4. **A schematic 3D model carries the whole video** — an aircraft, a section
   through a hull, a part moving. It is deliberately *not* photoreal. Their own
   description says: *"The model is an artist's concept… The animation is
   schematic and not to scale."*
5. **Labels name the mechanism.** Numbered steps, short mono annotations pinned
   to the part they describe. The type is a caption system, not decoration.
6. **The close is a sentence you could quote.** Not a CTA.

## 3 · The production stack, as declared by the channel

This is the useful part. Their video descriptions state, in the channel's own
words:

> "The animation is schematic and not to scale. **Sound effects: ElevenLabs
> Sound Effects library.** Sources: Wikipedia… Air & Space Forces Magazine… The
> War Zone… MDPI Aerospace…"

So: a **schematic 3D animation** (however it is authored), **library sound
effects**, and a **sourced script with the sources listed in the description**.
The 3D is not a game engine cutscene — the geometry is simple, flat-shaded,
faceted, lit with a couple of coloured lights, and the camera does the work. That
is reproducible here without a GPU, which is exactly what the sample film does.

## 4 · What I judged to be the real craft

- **Silhouette first.** Every model reads instantly as one shape on black.
- **Colour is a lighting decision, not a palette.** Cold blue for "normal",
  ember orange for "hot", green for "ignition". One hue per beat.
- **The camera is always moving, and always for a reason** — push to a part,
  orbit to show depth, pull back to reveal scale.
- **Type is mono + one display face**, huge, bottom-heavy, safe for Shorts UI.
- **Honest disclaimers.** Their model is openly an artist's concept. That is a
  credibility device, not a weakness.

## 5 · The sample film made here

`sr71-final.mp4` — **51 s**, 1080×1920, 24 fps, on **why the SR-71 Blackbird
leaked fuel on the ground**. Same grammar: paradox hook, cold state → hot state →
mechanism → quotable close.

| # | Beat | Time | What is on screen |
|---|---|---|---|
| — | Hook | 0 – 5.0 s | Rain of fuel under the belly, pulls back to the whole aircraft: **THE SR-71 LEAKED FUEL.** |
| 01 | Built loose | 5.0 – 11.0 s | Cold airframe, every panel joint open and glowing blue: **BUILT LOOSE.** |
| 02 | Skin = tank | 11.0 – 16.8 s | Macro on two titanium panels. The gap between them opens onto the inside of the tank — there was no rubber bladder: **THE SKIN IS THE TANK.** |
| 03 | The heat | 16.8 – 23.2 s | Ember light, heat haze; the airframe's edges go hot: **THE METAL GROWS.** |
| 04 | Seals | 23.2 – 30.2 s | The same two panels, closing in real geometry over six seconds, a glowing edge swallowed as they meet: **IT SEALS ITSELF.** |
| 05 | JP-7 | 30.2 – 36.0 s | The seams shut on the aircraft in flight, no drips: **COOLANT FIRST.** |
| 06 | TEB | 36.0 – 41.5 s | Green plumes off both exhausts: **IT BURNS GREEN.** |
| 07 | Close | 41.5 – 51.0 s | Slow orbit, clean silhouette: **IT DIDN'T LEAK.** / it leaked because it grew. |

### v2 — what the first cut got wrong

The first version (48.5 s) was shipped, then re-reviewed frame by frame, and two
things were wrong underneath the paint:

1. **The mechanism was faked.** The "it seals itself" beat used a static seam
   mesh: `build_parts` hardcoded `seams = 0.0` in both the cold and hot branches,
   so the gaps never actually closed. The beat asserted a mechanism it did not
   show. It now closes real geometry: the panel gap is a parameter of the plate
   mesh and animates from 0.44 to 0.012 over the beat, with a glowing edge that
   gets covered as the joint shuts.
2. **The hull was visibly low-poly** — eight flat sections per ring, hard facet
   edges, so the aircraft read as a 2004 viewport. The renderer now does
   crease-aware smoothing: per-corner normals averaged across faces, kept hard
   where the angle exceeds 42°, with Gouraud interpolation across every triangle.
   The fuselage is resampled from 15 stations to ~45 with Catmull-Rom, so there
   are no facets along its length. Wing leading edges and box corners stay sharp.

Also fixed: the skin expansion is now real geometry (the skin lifts off the frame
along its own normal, and every seam hoop rides the expanded surface); the frame
is solved from the subject's projected width instead of a bounding sphere (the
first cut was zoomed so far that parts of the aircraft left the frame); the
macro beats are framed on measured projections rather than guesses; the camera
has a continuous slow sweep so no beat measures as a frozen frame; hot skin stays
black and only its *edges* go ember, instead of the whole hull turning pink.

### How it is made

No WebGL is available in this container (ANGLE/SwiftShader cannot initialise),
so `zv3d/engine.py` is a **software 3D renderer written for this**: perspective
projection, z-buffer triangle rasterisation in NumPy, crease-aware smooth normals
with Gouraud interpolation, a three-light rig (warm key, cool rim, ember fill),
a fake studio environment so metal reflects something, a rim-emission term for
hot edges, bloom, ACES-ish tone map, vignette and per-frame grain. The aircraft
is ~30 parts in `zv3d/model.py` — a resampled superellipse hull, seam hoops and
spine seams generated *on* that hull, nacelles, canted tails, delta wing, canopy.
Type, HUD and leader-line labels are PIL layers (`zv3d/overlay.py`); the edit,
copy, camera and mechanism are `zv3d/shots.py`.

Every frame is a pure function of time — no clock, no unseeded RNG — so any frame
can be re-rendered on its own, and a held shot is precomputed rather than
re-fitted per frame (a camera that keeps fitting a shrinking object drifts
backwards and gives the reveal away):

```
python3 zv3d/render.py --still 27.0 --w 540 --h 960 --ss 1   # one frame
python3 zv3d/render.py --w 540 --h 960 --ss 1 --fps 12 --out prev.mp4  # preview
python3 zv3d/render.py --ss 2 --out film.mp4                  # the master
```

Measured: 1080×1920 at `--ss 2` is ~3.3 s/frame (1,224 frames ≈ 67 min); the
540×960 preview is ~2.0 s/frame. Audio is `zv3d/audio.py` — a synthesised bed
with a low hit on every cut, a riser into the hot beat and a bell on the green
flash. **No sound library, no ElevenLabs, no Blender, no GPU.**

### Facts used, and where they come from

Stated by the sources cited below, not invented:

- Airframe ~93% titanium; at Mach 3.2 the skin runs roughly 460–620 °F, with hot
  spots above 1,000 °F.
- The wing skin *was* the tank wall — "wet wing" tanks, no rubber bladder — and
  panels were fitted loose **because** the airframe expands several inches hot;
  a tightly-fitted cold airframe would buckle.
- The leak is the consequence of that fit, not a design goal: JP-7 seeped from
  the cold joints on the ground and the seams closed at speed.
- JP-7's flash point is around 140 °F; it was so hard to ignite that TEB
  (triethylborane) was injected to start the engines and light the afterburners,
  producing a green flash.
- The post-takeoff refuelling was about inerting the tanks with nitrogen for
  Mach >2.6, **not** about replacing leaked fuel — a myth this film avoids.

Sources: Wikipedia (Lockheed SR-71 Blackbird), 19FortyFive, Simple Flying,
The War Zone / Air & Space Forces Magazine, NASA historian Peter Merlin via
secondary reporting.

> **Honest caveat:** the model is schematic and not to scale, exactly as the
> channel disclaims about its own. It is not a Lockheed drawing and should not be
> read as one. I have not watched the finished render end to end; it was checked
> by inspecting frames at every beat, by a frame-difference pass that flags
> frozen frames, and by measuring the file.
