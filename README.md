# 👉 START HERE

This repo holds brand videos, the engines that make them, and the notes an agent
needs to pick the work back up.

---

## 🎬 Watch the videos

**Newest first.** Click a file, then press **Download** — GitHub will not stream an
MP4 in the browser.

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

**Vertical 1080×1920 is the one to post. Square and wide use a blurred fill, not
a crop.**

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

---

## 📁 What is in here

```
works/          ← the things you actually look at: videos, slides, images
   films/       ← finished videos, named like 01-<brand>-<type>-<format>
agent-context/  ← notes for the next agent (and you)
engines/        ← the video engines: brag (and whatever comes next)
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
