# supaclip (skill)

Vendored from **[uditdc/supaclip](https://github.com/uditdc/supaclip)** (MIT) — "turn long gameplay
recordings into short-form videos, with Claude as the editor". Three skills:

| skill | does |
|---|---|
| `stitch-director/SKILL.md` | catalog search → validate EDL → render, the hands-free flow |
| `movie-clips/SKILL.md` | clip-extraction flow |
| `movie-recap/SKILL.md` | recap/recut flow |

SupaClip itself is a Python package whose CLI ships four entry points:
`extract` (VLM analysis → clips + manifest), `catalog` (SQLite/FTS5 library), `stitch render`
(EDL → mp4, 1080×1920, OST styles, transitions, optional TTS), `supaclip-mcp`.

## Install the engine

```bash
git clone https://github.com/uditdc/supaclip && cd supaclip
python -m venv .venv && . .venv/bin/activate
pip install -e .
```

`stitch render` needs only ffmpeg — no model, no API key, no network. Only `extract` (the VLM
moment-finder) wants Ollama or a hosted key; `LLM_PROVIDER=gemini` with `GOOGLE_API_KEY` is the
shortest path if you have a key.

## How this repo uses it

`works/clips/{gta6-launch,speed-gta6}/tools/supaclip_render.py` writes a catalog directly from a
moment sheet (skipping the VLM), then hands an EDL to SupaClip's own renderer. That path is
verified: it rendered a 15 s 1080×1920 clip with the `yellow_punch` OST style and no voiceover.

Voiceover is optional in this repo by standing instruction: the EDLs are built with `"audio": []`
and on-screen text only.

Verified working on 2026-11-19 against `main` of the upstream repo.
