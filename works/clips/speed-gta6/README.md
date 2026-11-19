# IShowSpeed · GTA 6 launch clips

**Open `START-HERE.html` first.** It is the walkthrough, written to be read in a browser rather
than a terminal.

The stream: **🔴PLAYING GTA 6 EARLY ACCESS GAMEPLAY GET IN HERE!** — IShowSpeed, started
**Wed 18 Nov 2026, 9:00 pm ET** (2:00 am UTC, 7:30 am IST on the 19th), simulcast on YouTube and
Twitch. It was still live at ~26k concurrent when this pack was written, so the VOD does not exist
yet: everything here is built to work the moment it does.

## Why you are the one pressing the button

This sandbox reaches GitHub, PyPI and npm and nothing else. YouTube, Twitch and SupaClip all fail at
the handshake — tested, not assumed. The downloader sites fail too (savefrom discontinued in the US,
ssyoutube 502), the GitHub-runner route is closed (Actions off on this repo), and free file hosting
won't take a 30 GB VOD.

What that leaves is the useful split: **SupaClip runs in your browser**, where nothing is blocked,
and it does the AI moment-finding. Everything SupaClip cannot know lives in this folder — the
credit burned into the frames, the moment brief, the captions, the 60-second cap.

## Two ways to finish

**A. SupaClip (AI, no editing skill needed).** Open [supaclip.ai](https://supaclip.ai), new project,
paste the VOD URL, choose the **stream** video type so it frames facecam over gameplay, keep only
moments from `candidates.json → targets`, trim to ≤40 s, export. Then:

```bash
tools/burn_credit.sh ~/Downloads/supaclip/*.mp4     # stamps CLIP: IShowSpeed into every frame
```

Free tier is 30 AI minutes a month and 720p export, no watermark. Pro is 1080p.

**B. This pack (ffmpeg only, no quota).** Say when you saw the moment:

```bash
python3 tools/set_moment.py 01 4823.5 4851.0 \
  --hook "First frame of GTA 6" \
  --title "IShowSpeed sees GTA 6 for the first time"
FR=60 ./capture.sh speed-vod.mp4 01       # → shorts/clip-01.mp4
python3 tools/check.py                    # refuses to pass a bad clip
```

`./capture.sh speed-vod.mp4 all` cuts every recorded moment. `tools/set_moment.py --list` shows what
is filled in. `./build.sh speed-vod.mp4` adds burned-in word-by-word captions once a transcript
exists (that is the vendored `video-to-shorts-skill`, the same one the boss pack uses).

`cut.sh` still works too: it vendors yt-dlp into `./vendor` and downloads, if you would rather have
the file than point at it.

## The five moments worth having

| Moment | What to catch | Why it travels |
|---|---|---|
| First reaction | the 30 s after he gets control: face, then gameplay | the most-clipped moment of any launch stream |
| Police stop rage | first wanted level, him blaming the car | cop chases are his most reliable content |
| Car-theft fail | phone out, locked car, alarm | GTA 6 gates nice cars; he finds out loudly |
| Leonida at night | Vice City skyline, ideally a storm | visual payoff travels beyond his audience |
| The gator | anything that bites him | needs zero context, works at 15 s |

Rules that matter more than the list: **start on the shout, not before it**, keep clips **≤40 s**
(60 absolute — that is where Content ID lives), and **keep `Clip: @IShowSpeed` in the caption** on
top of the burned-in credit.

## Files

| file | what it is |
|---|---|
| `START-HERE.html` | the walkthrough, in plain language, linkable |
| `candidates.json` | moment brief, per-clip hooks/titles/captions, `capture.final` seconds, and the rules |
| `capture.sh` | ffmpeg-only vertical cut, credit burned in, `REFRAME=fit` by default |
| `build.sh` | the skill's pipeline: transcribe → snap → render → captions → credit → review |
| `cut.sh` | download (vendoring yt-dlp) then build |
| `tools/set_moment.py` | record seconds for a moment, the fast path |
| `tools/check.py` | pre-flight: placeholders, length, dimensions, credit |
| `tools/burn_credit.sh` | stamp the credit into any finished clip, idempotently |
| `tools/credit_overlay.py` | renders the credit pill (already rendered: `assets/credit.png`) |
| `tools/to_clips.py`, `tools/review.py` | sentence→word-timing snap, and the review page |

## Verified here, so you are not debugging guesses

- `capture.sh` rendered a real **1080×1920, 60 fps, 11 s** clip from a 16:9 source with the whole
  frame preserved over a blurred fill, and `CLIP: IShowSpeed` visibly burned in.
- `set_moment.py` → `capture.sh` → `check.py` ran as one chain; `check.py` correctly failed the run
  while a caption line was still a placeholder, which is the point of it.
- The credit burn is idempotent (container marker), and was verified on a decoded frame in the boss
  pack with the same tool.
- The caption engine and the timing matcher were proven in `works/clips/gta6-launch/_verify/`.

## The credit position, unchanged

Burn it in, put it in the caption, and keep the clips short. This is somebody else's stream: the
credit is the floor, not the favour. If these go on a brand or monetised account, ask Speed's team
first — a one-paragraph message beats a strike. Nothing in this pack posts anything by itself.
