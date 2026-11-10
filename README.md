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

### 02 — Zero-vast 3D explainer · 24.0 s, vertical

The same brand, explained in depth: type arrives out of the dark, the camera
falls through a stack of plates, then a corridor of rings. Four chapters.

| Watch | File | Size |
|---|---|---|
| 📱 **Start with this** | [`02-zero-vast-3d-explainer-vertical-720p.mp4`](works/films/zero-vast/02-zero-vast-3d-explainer-vertical-720p.mp4) | 0.9 MB |
| 🎞 Master | [`02-zero-vast-3d-explainer-vertical-1080p.mp4`](works/films/zero-vast/02-zero-vast-3d-explainer-vertical-1080p.mp4) | 1.9 MB |

> **Honest caveat:** nobody has sat and watched these end to end. The gate that
> ships them is numeric — it proves the frames are not cropped, not silent, not
> illegible and not frozen. It cannot tell you the edit is good.

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
