# Films

Every finished video, named `<number>-<brand>-<kind>-<format>` so the filename
tells you what you're about to download.

| file | what |
|---|---|
| [`zero-vast/01-zero-vast-brag-vertical-720p.mp4`](zero-vast/01-zero-vast-brag-vertical-720p.mp4) | 24.9 s brag film, 720×1280, 1.4 MB — start here |
| [`zero-vast/01-zero-vast-brag-vertical-1080p.mp4`](zero-vast/01-zero-vast-brag-vertical-1080p.mp4) | same film, 1080×1920 master, 12 MB |
| [`zero-vast/02-zero-vast-3d-explainer-vertical-720p.mp4`](zero-vast/02-zero-vast-3d-explainer-vertical-720p.mp4) | 24.0 s 3D explainer, 720×1280, 0.9 MB |
| [`zero-vast/02-zero-vast-3d-explainer-vertical-1080p.mp4`](zero-vast/02-zero-vast-3d-explainer-vertical-1080p.mp4) | same film, 1080×1920 master, 1.9 MB |

Engines: `engines/brag/` makes the brag film, `engines/explainer3d/` makes the 3D
one. Neither engine produces both.

GitHub's web player will not stream an MP4 from a repo: use the **Download** button
on the file page, or append `?raw=true` to the file URL.

Files are committed directly rather than through LFS — this account has no LFS
budget. A 24-second 1080p film is 2 MB from these engines; that's cheap enough to
keep in the repo so the videos are always one click away.
