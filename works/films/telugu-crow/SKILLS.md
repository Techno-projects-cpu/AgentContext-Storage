# What each skill contributes to this film

Cloned fresh each session into `/tmp/sk` (they are not vendored):
`Bangtutorial/bang-motion`, `Alchaincyf/huashu-art-motion`, `Alisa0808/vox-director`,
`Cloveric/claude-drawing-skill`, `Moh4696/cinematic-skill` (`/tmp/cs`).

| Skill | What it actually does in this film |
|---|---|
| **claude-drawing-skill** → `grainbook` (grainy picture book) | Paints the sets. `tools/plates.py` drives its numpy gouache engine: dry chalky brushes, paper tooth, no ink outlines. Four plates (`field`, `pot`, `quiz`, `end`) at 1380x3160 design px, plus `paper.jpg`, the print stock pressed over every frame in screen space. |
| **cinematic-skill** → `engine.py` / `engine2.py` | The renderer, camera, cards, sfx/mix chain. `engine2.Plates` blits the painted page inside the world transform so the camera moves through the painting; `engine2.press()` lays the paper on in screen space. |
| **bang-motion** → `references/kartun-panggung.md` | Set the grammar: one stage per beat, camera **inside** the stage at 1.08–2.02 (never wide), hard cuts between stages, a 96 px-shift-with-blur only where the place really changes, ≥10 moving things per stage, no caption blocks — which is why the stage made way for painted plates + the ambient layer. |
| **huashu-art-motion** → `09-视频动画语法.md` §三 | Rules 6–8 and 10: cuts on the breath between sentences, entry moves 0.6–1.5 s eased, **one** motivated move per shot, pull out after a push, never three pushes in a row. The shot list in `scene2.py` follows this literally. |
| **vox-director** → `references/beat-layer.md` §3 | "Camera move and element motion are separate axes; the energy comes from elements moving inside the frame." That is `tools/ambient.py`: heat shimmer on the horizon, dust motes, swaying tussocks of dry grass, steam off the warmed water. |

## Not used, and why

- **vox-director's own pipeline** needs an Atlas Cloud API key and generates collage *posters* — the
  wrong medium for a hand-drawn children's book, and there is no key in this sandbox.
- **bang-motion's HTML/GSAP starter** needs a browser to render; this container has no Chrome. Its
  *grammar* is used instead (see above).
