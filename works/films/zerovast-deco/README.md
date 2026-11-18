# ZERO VAST — "Deco" (no voiceover)

23 s, 1080×1920, 30 fps. A 1930s airbrushed **night poster**: sunburst, moon, stepped skyline, water,
gilt ornamental lettering. Nothing in it has an outline — every surface is sprayed through a frisket.

| | |
|---|---|
| Style | `claude-drawing-skill` artdeco engine (`ArtDeco.sky/burst/moon/searchlight/tower/crown/clock/water/lettering/caption/border/finish`) |
| Artwork | `tools/plates_deco.py` → one 1080×1920 poster in seven stages (sky, burst, far city, near city, water, jetty, lettering) |
| Motion | the poster paints itself in 2.3 s, then the camera walks through the finished picture at eight scales |
| Type | the poster's own voice: tracked gold caps on gilt rules (the engine's `lettering`/`caption`) |
| Track | `audio/score.wav` — 88 bpm, hits on every cut |
| Mix | `audio/mix.m4a` — music + sfx, −15 LUFS |

Rebuild:

```bash
export CF_ENGINE=/tmp/cs/cinematic-skill/skills/cinematic-film/scripts
/tmp/py tools/plates_deco.py --out assets/plates    # ~25 s
SCENE=scene.py /tmp/py tools/render2.py --project . --cues
/tmp/py $CF_ENGINE/build_sfx.py --project .
/tmp/py ../_shared/eng/mix_novo.py --project .
SCENE=scene.py /tmp/py tools/render2.py --project . --size 1080x1920 --audio audio/mix.m4a \
    --out out/final.mp4 --workers 2                  # ~95 s
```

Every claim is from zero-vast.vercel.app: hand-written, no framework, no lock-in, no page-builder
payload, built to perform, Khammam Telangana, one point of contact, address printed on the poster.

## What this one taught

* **Stages must not leave bare paper.** The sky stage without the water left a pale band for the
  first second; painting the water's base tone dark in the sky stage fixed the opening.
* **Two adjacent plates meet at a horizon.** Sky's last stop and water's first stop have to be the
  same value or the horizon is a bright line that looks like a rendering bug, not a sea.
* Airbrush stages composite beautifully with a bloom and no wipe: at 30 fps five stages in 2.3 s
  read as painting, not as a slideshow.
