# Vendored agent skills

Cloned from GitHub and kept here so a session can use them without network access. Showcase videos
and example renders were stripped (they were ~500 MB of binaries); the docs, references, scripts and
code are complete.

| skill | source | what it is |
|---|---|---|
| `bang-motion` | Bangtutorial/bang-motion | cinematic motion graphics in HTML + CSS + GSAP (+ Three.js); promo/openers/kinetic type, and how to render the result to MP4 |
| `vox-director` | Alisa0808/vox-director | one topic -> finished Vox-style paper-collage explainer (script, collage keyframes, VO, music, captions) |
| `huashu-art-motion` | Alchaincyf/huashu-art-motion | art/video animation: 36 realised styles, 16 transferable recipes, 9 explainer grammar, parameterised clip renderer |
| `claude-drawing-skill` | Cloveric/claude-drawing-skill | 83 styles of procedural painting in pure numpy + Pillow — no image model, deterministic, animatable stage by stage |
| `find-skills` | su-ron/find-skills | discovery: how to search and install skills from the open agent-skills ecosystem (`npx skills find/add`) |
| `cinematic-skill` | Moh4696/cinematic-skill | the engine this repo's films are built on (see its own README) |

`.claude/skills/` symlinks to these so a coding agent picks them up.

Each skill's own `SKILL.md` is the entry point.
