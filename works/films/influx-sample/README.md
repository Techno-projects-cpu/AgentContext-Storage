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

`01-sr71-leaked-fuel-vertical-1080x1920.mp4` — 48.5 s, vertical, on **why the SR-71 Blackbird leaked
fuel on the ground**. Same grammar: paradox title, cold state → hot state →
mechanism → quotable close.

| Beat | Time | What is on screen |
|---|---|---|
| Hook | 0 – 4.5 s | Cold, wet close-up under the belly; the type lands: **THE SR-71 LEAKED FUEL.** |
| 01 Cold | 4.5 – 13 s | Pan along the airframe; panel gaps named; drips fall from the belly |
| 02 Hot | 13 – 24.5 s | Ember lighting, heat haze; the metal grows, then **IT SEALS ITSELF** |
| 03 Fuel | 24.5 – 32 s | Macro on two titanium panels; the gap between them is the subject |
| 04 Ignition | 32 – 40.4 s | TEB injector; the frame goes green |
| Close | 40.4 – 48.5 s | Slow orbit; **IT DIDN'T LEAK. IT LEAKED BECAUSE IT GREW.** |

### How it is made

No WebGL is available in this container (ANGLE/SwiftShader cannot initialise),
so `zv3d/engine.py` is a **software 3D renderer written for this**: perspective
projection, z-buffer triangle rasterisation in NumPy, per-face shading with a
three-light rig (warm key, cool rim, ember fill), a fake studio environment so
metal reflects something, bloom, ACES-ish tone map, vignette and grain. The
aircraft is ~40 primitives in `zv3d/model.py`. Type, HUD and labels are PIL
layers (`zv3d/overlay.py`); the edit and copy are `zv3d/shots.py`.

Every frame is a pure function of time — no clock, no unseeded RNG — so any frame
can be re-rendered on its own:

```
cd engines/sr71-3d
python3 render.py --still 12.4 --w 540 --h 960 --ss 1   # one frame
python3 render.py --out film.mp4 --ss 2                 # the master (71 min at 1080x1920)
python3 audio.py --dur 48.5 --out /tmp/bed.wav          # the sound bed
```

Measured on the delivered file: 48.500 s, 1080x1920, H.264 + AAC, −16.9 LUFS,
−1.3 dBTP true peak, no dead frames sampled every 30 frames.

### Facts used, and where they come from

Stated by the sources cited in the section below, not invented:

- Airframe ~93% titanium; at Mach 3.2 skin runs roughly 460–620 °F, with hot
  spots above 1,000 °F.
- Panels were fitted loose **because** the airframe expands several inches when
  hot; a tightly-fitted cold airframe would buckle.
- The leak is a consequence of that fit, not a design goal in itself — the tanks
  sealed once the skin expanded.
- JP-7 has a flash point around 140 °F; it was so hard to ignite that TEB
  (triethylborane) was injected to start the engines and light the afterburners,
  producing a green flash.
- Pilots have said the post-takeoff refuelling was about inerting the tanks with
  nitrogen for Mach >2.6, not about the leak volume.

Sources: Wikipedia (Lockheed SR-71 Blackbird), 19FortyFive, Simple Flying,
The War Zone / Air & Space Forces Magazine, NASA historian Peter Merlin via
secondary reporting.

> **Honest caveat:** the model is schematic and not to scale, exactly as the
> channel disclaims about its own. It is not a Lockheed drawing and should not be
> read as one. I have not watched the finished render end to end; it was checked
> by inspecting frames at every beat and by measuring the file.
