# Demo render — what the clips will look like

**These are not GTA clips.** The footage is [Big Buck Bunny](https://peach.blender.org/)
(Blender Foundation, CC-BY 3.0), used as a stand-in because this sandbox cannot reach
YouTube, so the real source has not been through the pipeline yet.

What *is* real: everything else. `shorts/demo-360.mp4` was rendered by **SupaClip's own
renderer** (`stitch render`, EDL built by `../speed-gta6/tools/supaclip_render.py` from
`candidates.json`), at 1080×1920, with the `yellow_punch` on-screen text style this pack uses,
then scaled down to 360×640 so it is cheap to commit and quick to watch.

Watch it to see the output shape. When the real source arrives, the same pipeline writes
`../gta6-launch/shorts/clip-01..05.mp4` at full 1080×1920 with the boss's credit burned in —
those will be the actual clips.

| | |
|---|---|
| renderer | `uditdc/supaclip` → `stitch render` |
| output | 1080×1920, 30 fps, `yellow_punch` OST, no voiceover |
| footage | Big Buck Bunny, CC-BY 3.0 (placeholder) |
| real clips | `../gta6-launch/shorts/` once a source file exists |
