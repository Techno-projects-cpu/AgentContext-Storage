# 👉 START HERE

This repo holds brand videos, the engines that make them, and the notes an agent
needs to pick the work back up.

---

## 🎬 Watch the videos

**Newest first.** Click a file, then press **Download** — GitHub will not stream an
MP4 in the browser.

### 00a — SR-71 · vertical 3D short · **the newest thing here**

A sample built to a real YouTube channel's format: [**Influx
Picture**](https://youtube.com/@influxpicture), who do one counter-intuitive
mechanical fact per vertical Short over a schematic 3D model. Short version of
what I learned: **the title is the paradox, the first two seconds state the
contradiction, one mechanism per video, a schematic (not photoreal) 3D model
carries it, labels name the parts, and the close is a quotable sentence.** The
channel declares its own stack in its descriptions — schematic animation, library
sound effects, and sources listed per video.

| Watch | File | Length |
|---|---|---|
| ▶ **The City That Reversed Its River** · Chicago, 1900 | [`preview_540.mp4`](works/films/chicago-river/preview_540.mp4) | 1:24 |
| ▶ **SR-71 · "It leaked fuel. On purpose."** | [`01-sr71-leaked-fuel-vertical-1080x1920.mp4`](works/films/influx-sample/01-sr71-leaked-fuel-vertical-1080x1920.mp4) · [poster](works/films/influx-sample/01-sr71-leaked-fuel-poster.jpg) | 51.0 s |

Beats: fuel raining off the belly → every joint open and cold → macro on two
titanium panels, the gap between them opening onto the inside of the tank → the
airframe's edges going ember at Mach 3 → **the same two panels closing in real
geometry** while the glowing edge is swallowed → TEB ignition, green plumes →
**"It didn't leak. It leaked because it grew."** 1080×1920, 24 fps, AAC.

Rebuilt once after review, because the first cut asserted the sealing mechanism
instead of showing it: the seam gaps were static geometry, and the hull read as
low-poly. Both are now real — the panel gap is a mesh parameter that animates,
and the renderer does crease-aware smooth normals with Gouraud interpolation.

The 3D is **real 3D, rasterised on the CPU**: there is no WebGL in this sandbox,
so [`engines/sr71-3d/`](engines/sr71-3d/) is a NumPy renderer — z-buffer, crease-aware
smooth normals, three-light rig, environment reflections, rim heat, bloom, tone
map — plus a PIL type layer
and a synthesized sound bed. Channel analysis and the full production notes:
[`works/films/influx-sample/README.md`](works/films/influx-sample/README.md).

**v1 vs v2:** [`01-sr71-v1-vs-v2.jpg`](works/films/influx-sample/01-sr71-v1-vs-v2.jpg)
puts the first cut next to the rebuild at the same beats.

> **Honest caveat:** the model is schematic and not to scale, which the channel
> says about its own models too — it is not a Lockheed drawing. Nobody has
> watched this end to end; it was checked frame by frame at every beat and
> measured numerically.

### 00aa — Tools worth knowing: `cinematic-skill`

Found and **run** here, not just linked: [**Moh4696/cinematic-skill**](https://github.com/Moh4696/cinematic-skill)
(509★, MIT, by exploraX) builds narrated films entirely from code — one
continuous camera over one designed world of photos, maps and cards, with every
stamp and counter landing on the narrator's spoken word. It is the packaged
version of what the SR-71 short does by hand, plus the sound, captions and SRT
that were manual there.

It works in this container even though there is no `libEGL`/`libGL` and no
ffprobe: Skia's GL symbols are stubbed, ffmpeg comes from `imageio-ffmpeg` and
ffprobe from npm's `ffprobe-static`. A 28.6 s 720×1280 draft rendered in 117 s.
Notes and caveats: [`skills/cinematic-skill/README.md`](skills/cinematic-skill/README.md).

### The City That Reversed Its River (80 s documentary)

Chicago dumped its sewage into the river, and the river ran into the lake the city drank from — so
Chicago cut a canal 28 miles west and made the river run the other way. Made with the
[`cinematic-skill`](skills/cinematic-skill/README.md) engine (one camera, one board, every hit on a
spoken word), on a printed map sheet built from local Natural Earth data: the lake, the canal, the
eight-foot divide, the dam broken by hand at dawn on 2 January 1900, *Missouri v. Illinois* in 1906,
and the electric carp barriers that stand in the same channel today.

82 s, 720×1280, 21 lines, 47 synthesised sound cues, mastered to −15 LUFS. The full project —
script with per-line sources, beat table, scene, and the two map builders — is in
[`works/films/chicago-river/`](works/films/chicago-river/README.md).

### 00b — ZeroVast × HyperFrames · three films, 1080p

Three films about **zero-vast.vercel.app**, each written as an HTML composition
and rendered with [HyperFrames](https://github.com/heygen-com/hyperframes); the
edit follows the [Brag](https://github.com/latent-spaces/brag) skill's laws
(15–25 s, hook first, show the real thing, no generic SaaS language, fast in then
hold). Between them they cover the whole camera kit: pushes, trucks, tilts, rack
focus, pull-backs, a 3D deck, parallax and type motion.

| # | Film | Length | Poster |
|---|---|---|---|
| 1 | [**Site tour** — `01-hyperframes-site-tour-1080p.mp4`](works/films/zerovast-hf/01-hyperframes-site-tour-1080p.mp4) | 25 s | [still](works/films/zerovast-hf/01-hyperframes-site-tour-1080p-poster.jpg) |
| 2 | [**Camera moves** — `02-hyperframes-camera-moves-1080p.mp4`](works/films/zerovast-hf/02-hyperframes-camera-moves-1080p.mp4) | 22 s | [still](works/films/zerovast-hf/02-hyperframes-camera-moves-1080p-poster.jpg) |
| 3 | [**Kinetic type** — `03-hyperframes-kinetic-type-1080p.mp4`](works/films/zerovast-hf/03-hyperframes-kinetic-type-1080p.mp4) | 20 s | [still](works/films/zerovast-hf/03-hyperframes-kinetic-type-1080p-poster.jpg) |

All three: 1920×1080 @ 30 fps, AAC audio, −16.0 to −16.2 LUFS, peaks under
−1 dBTP, no dead frames beyond the tail fades, and a green HyperFrames gate
(lint, runtime, layout, motion, contrast) at 0 errors, 0 warnings. Sources, measurements and the defects
found along the way: [`works/films/zerovast-hf/README.md`](works/films/zerovast-hf/README.md).

> **Honest caveat:** nobody has watched these end to end. The checks are numeric
> and still-frame; they prove the films are not cropped, silent, illegible or
> frozen. They cannot tell you the edit is good.

### 01 — Zero-vast brag film · 24.9 s, vertical

Type-led brand film: one claim per shot, camera pushes, captions and narration
carry different words.

| Watch | File | Size |
|---|---|---|
| 📱 **Start with this** | [`01-zero-vast-brag-vertical-720p.mp4`](works/films/zero-vast/01-zero-vast-brag-vertical-720p.mp4) | 1.4 MB |
| 🎞 Master | [`01-zero-vast-brag-vertical-1080p.mp4`](works/films/zero-vast/01-zero-vast-brag-vertical-1080p.mp4) | 12 MB |

### 02 — Zero-vast 3D explainer · 24.9 s, vertical

The same brand explained in motion, on paper: warm off-white ground, near-black
ink, a printed blue and a deep forest green. Five chapters — headline, a helix of
white cards for the stack, a throat of rules racing past the performance numbers,
a title-sequence window for the four steps, and a close. Very few elements per
frame and a great deal of empty paper; no stock footage, no shaders.

| Watch | File | Size |
|---|---|---|
| 📱 **Start with this** | [`02-zero-vast-3d-explainer-vertical-720p.mp4`](works/films/zero-vast/02-zero-vast-3d-explainer-vertical-720p.mp4) | 1.4 MB |
| 🎞 Master | [`02-zero-vast-3d-explainer-vertical-1080p.mp4`](works/films/zero-vast/02-zero-vast-3d-explainer-vertical-1080p.mp4) | 3.2 MB |

### 03 — Max World localised ads · 20 s, vertical ×4

Four ads for Max World (CC cameras, systems, laptops — Indera Nagar, Khammam),
one cut pattern, four graphic languages. Telugu, Hindi and Urdu are shaped by a
real browser (HarfBuzz), so the Nastaliq and the Telugu conjuncts are correct.

A voiceover in each language, over a 110 BPM bed. **Vertical 1080×1920 is the
one to post. Square and wide use a blurred fill, not a crop.**

> ⚠️ **Urdu is not finished.** `03-maxworld-ad-ur-*` currently has music and SFX
> but **no voice** — the Urdu narration clip stops before the phone number, so it
> was held back rather than shipped half-spoken. English, Telugu and Hindi all
> have their voiceovers.

| Language | Post this | Square | Wide |
|---|---|---|---|
| **English** | [`03-maxworld-ad-en-vertical-1080p.mp4`](works/films/maxworld/03-maxworld-ad-en-vertical-1080p.mp4) | [square](works/films/maxworld/03-maxworld-ad-en-square-1080.mp4) | [wide](works/films/maxworld/03-maxworld-ad-en-wide-1920x1080.mp4) |
| **తెలుగు Telugu** | [`03-maxworld-ad-te-vertical-1080p.mp4`](works/films/maxworld/03-maxworld-ad-te-vertical-1080p.mp4) | [square](works/films/maxworld/03-maxworld-ad-te-square-1080.mp4) | [wide](works/films/maxworld/03-maxworld-ad-te-wide-1920x1080.mp4) |
| **हिन्दी Hindi** | [`03-maxworld-ad-hi-vertical-1080p.mp4`](works/films/maxworld/03-maxworld-ad-hi-vertical-1080p.mp4) | [square](works/films/maxworld/03-maxworld-ad-hi-square-1080.mp4) | [wide](works/films/maxworld/03-maxworld-ad-hi-wide-1920x1080.mp4) |
| **اردو Urdu** | [`03-maxworld-ad-ur-vertical-1080p.mp4`](works/films/maxworld/03-maxworld-ad-ur-vertical-1080p.mp4) | [square](works/films/maxworld/03-maxworld-ad-ur-square-1080.mp4) | [wide](works/films/maxworld/03-maxworld-ad-ur-wide-1920x1080.mp4) |

Posters: [EN](works/films/maxworld/03-maxworld-ad-en-poster.jpg) ·
[TE](works/films/maxworld/03-maxworld-ad-te-poster.jpg) ·
[HI](works/films/maxworld/03-maxworld-ad-hi-poster.jpg) ·
[UR](works/films/maxworld/03-maxworld-ad-ur-poster.jpg)
· Share copy: [EN](works/films/maxworld/share-copy.txt) ·
[TE](works/films/maxworld/share-copy-te.txt) ·
[HI](works/films/maxworld/share-copy-hi.txt) ·
[UR](works/films/maxworld/share-copy-ur.txt)

More: [`works/films/maxworld/README.md`](works/films/maxworld/README.md) — a
copy of the docs that ship with the MaxWorld repo.

> **Honest caveat:** nobody has sat and watched these end to end. For films 01 and
> 02 the gate that ships them is numeric — it proves the frames are not cropped,
> not silent, not illegible and not frozen. It cannot tell you the edit is good.
> For the Max World ads, each was checked by reading stills at 1.17 / 5.0 / 8.3 /
> 12.3 / 18.3 / 19.9 s in all four languages; the mix measures −17.3 dB RMS and no
> silent gaps. That is still not the same thing as watching them.

### 04 — ZeroVast ad set · static, 8 boards × 2 themes

Ads for **zero-vast.vercel.app**, produced with the
[claude-ads](https://github.com/AgriciDaniel/claude-ads) skill — brand profile,
three testable concepts, per-placement copy and a landing message-match check,
all validated against claude-ads' own JSON contracts.

**[Contact sheet →](works/ads/zero-vast/creative/png/contact-sheet.png)** ·
[full run notes](works/ads/zero-vast/README.md) ·
[copy deck](works/ads/zero-vast/creative/copy-deck.md)

| Board | Size |
|---|---|
| [speed · feed](works/ads/zero-vast/creative/png/speed-feed-1x1.png) | 1080×1080 |
| [speed · 4:5](works/ads/zero-vast/creative/png/speed-feed-4x5.png) | 1080×1350 |
| [speed · story](works/ads/zero-vast/creative/png/speed-story-9x16.png) | 1080×1920 |
| [speed · landscape](works/ads/zero-vast/creative/png/speed-wide-1.91x1.png) | 1200×628 |
| [ownership · feed](works/ads/zero-vast/creative/png/ownership-feed-1x1.png) | 1080×1080 |
| [ownership · landscape](works/ads/zero-vast/creative/png/ownership-wide-1.91x1.png) | 1200×628 |
| [limits · feed](works/ads/zero-vast/creative/png/limits-feed-1x1.png) | 1080×1080 |
| [limits · 4:5](works/ads/zero-vast/creative/png/limits-4x5.png) | 1080×1350 |

Two themes: **ink** (shown, uses the live site's own colours and its outlined
display type) and **paper** (`png/paper/`, the film language).

> **Honest caveat:** these are correct boards, not proven creative. Zero boards
> have been seen in a real placement, the site's live Core Web Vitals could not be
> measured from this sandbox, and no ad account data was supplied — so there is no
> performance claim anywhere in this set.

---

## 📁 What is in here

```
works/          ← the things you actually look at: videos, slides, images
   films/       ← finished videos, named like 01-<brand>-<type>-<format>
agent-context/  ← notes for the next agent (and you)
engines/        ← the video engines: brag, hyperframes, sr71-3d (and whatever
                   comes next)
tooling/        ← the plumbing: bootstrap, render, QC. You never need to read this.
```

### `works/` — your output
Everything watchable. Named by number, brand, kind and format so the name tells you
what it is: `01-zero-vast-brag-vertical-720p.mp4`.

### `agent-context/` — the brief
- [`HANDOFF.md`](agent-context/HANDOFF.md) — who you are, how the box works, the traps
- [`BRAG-PROMPT.md`](agent-context/BRAG-PROMPT.md) — the reusable authoring prompt
- [`zero-vast-film-notes.md`](agent-context/zero-vast-film-notes.md) — what the current film is
- [`explainer3d-engine.md`](agent-context/explainer3d-engine.md) — how the 3D engine works and the traps it taught us

### `engines/` — the machines
- **`brag/`** — the short brand-film engine (HyperFrames + GSAP, portrait-first).
  `template.html` is the engine, `film-zero-vast.html` is the current film.
- **`explainer3d/`** — the 3D explainer engine. CSS 3D transforms only, no WebGL:
  chapters are `hero` (orbiting type), `dive` (plates falling toward the lens) and
  `tunnel` (rings receding to a vanishing point). `template.html` holds the engine
  and a complete 4-chapter demo in its `FILM` object.

### `tooling/` — the plumbing
Rebuild the toolchain, render, and the numeric QC gate. Read only if something breaks.

---

## Making a new video

```bash
bash tooling/bootstrap.sh
source ~/.local/env.sh

tooling/new-film.sh myfilm portrait     # scaffold from the brag engine
tooling/new-film.sh my3d  portrait 3d   # scaffold from the 3D engine
#   edit the FILM object at the top of myfilm/index.html
tooling/render.sh myfilm                # render + QC gate (fails loudly)
```

---

## Honest status

The QC gate proves a film is **not silent, not cropped, not illegible, not flashing
black and not static**. It cannot prove it is *good*. Nobody has watched these with
eyes, or heard the voiceover.
