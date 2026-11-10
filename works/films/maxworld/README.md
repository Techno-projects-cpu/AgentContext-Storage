# Max World — localised ad films

Four 20-second ads for **Max World**, Indera Nagar, Khammam — CC cameras,
complete CCTV systems and laptop sales & service. One cut pattern, four graphic
languages.

> ⚠️ **Urdu has no voiceover yet.** Its clip stops before the phone number, so it
> is held back rather than shipped half-spoken. EN / TE / HI are fully voiced.

## Watch them

GitHub cannot stream an MP4 in the browser. Click a file, then press **Download**.

| # | Language | Vertical — post this | Square | Wide |
|---|---|---|---|---|
| 1 | **English** | [`03-maxworld-ad-en-vertical-1080p.mp4`](03-maxworld-ad-en-vertical-1080p.mp4) | [`03-maxworld-ad-en-square-1080.mp4`](03-maxworld-ad-en-square-1080.mp4) | [`03-maxworld-ad-en-wide-1920x1080.mp4`](03-maxworld-ad-en-wide-1920x1080.mp4) |
| 2 | **తెలుగు Telugu** | [`03-maxworld-ad-te-vertical-1080p.mp4`](03-maxworld-ad-te-vertical-1080p.mp4) | [`03-maxworld-ad-te-square-1080.mp4`](03-maxworld-ad-te-square-1080.mp4) | [`03-maxworld-ad-te-wide-1920x1080.mp4`](03-maxworld-ad-te-wide-1920x1080.mp4) |
| 3 | **हिन्दी Hindi** | [`03-maxworld-ad-hi-vertical-1080p.mp4`](03-maxworld-ad-hi-vertical-1080p.mp4) | [`03-maxworld-ad-hi-square-1080.mp4`](03-maxworld-ad-hi-square-1080.mp4) | [`03-maxworld-ad-hi-wide-1920x1080.mp4`](03-maxworld-ad-hi-wide-1920x1080.mp4) |
| 4 | **اردو Urdu** | [`03-maxworld-ad-ur-vertical-1080p.mp4`](03-maxworld-ad-ur-vertical-1080p.mp4) | [`03-maxworld-ad-ur-square-1080.mp4`](03-maxworld-ad-ur-square-1080.mp4) | [`03-maxworld-ad-ur-wide-1920x1080.mp4`](03-maxworld-ad-ur-wide-1920x1080.mp4) |

Posters — the CTA frame, use it as the video thumbnail:
[EN](03-maxworld-ad-en-poster.jpg) · [TE](03-maxworld-ad-te-poster.jpg) ·
[HI](03-maxworld-ad-hi-poster.jpg) · [UR](03-maxworld-ad-ur-poster.jpg)

Share copy, ready to paste:
[EN](share-copy.txt) · [TE](share-copy-te.txt) · [HI](share-copy-hi.txt) ·
[UR](share-copy-ur.txt)

## Which graphic language is which

The four deliberately do **not** share a look — only a skeleton (same timings,
same layout logic, same product photograph, same MW symbol).

| | ground | accent | ornament | display face |
|---|---|---|---|---|
| **EN** | `#0E0D0A` near-black | brand red `#E30613` | white viewfinder brackets, mono REC HUD | Space Grotesk |
| **TE** | `#17110A` charcoal-brown | marigold `#E3A624` | gold brackets + gold diamonds flanking the kicker, concentric gold arcs | Ramabhadra |
| **HI** | `#261010` deep maroon | saffron `#F5820B` | thick saffron corners, concentric diya-glow rings | Rozha One / Hind SemiBold |
| **UR** | `#0F1B13` deep green | antique gold `#CDB26B` | full double gold frame (book cover), mirrored right-aligned rows, Nastaliq | Noto Nastaliq Urdu |

The MW symbol is the shop's real one, from
`MaxWorld/public/logo/maxworld-symbol.svg` — red M, paper-white W — identical in
all four.

## The scripts are properly shaped — here is how

**This is a browser render, not an ImageMagick stamp pipeline.** HyperFrames in
headless Chrome laid out every frame, so **HarfBuzz** shaped every script:

- **Telugu** — Ramabhadra. Conjuncts and matras correct: `ల్యాప్టాప్` and
  `ఇన్స్టాల్` render as real clusters, not disconnected strokes.
- **Hindi** — Rozha One display, Hind body.
- **Urdu** — **Noto Nastaliq Urdu**, RTL, correctly shaped. The plan allowed a
  Noto Naskh Arabic fallback if Nastaliq would not rasterise; **it was not
  needed** and is not in the build.

Latin text (the phone number, `CAM 01 — KHAMMAM`, `REC · LIVE VIEW`) is always in
a Latin face. No ZWNJ (U+200C) exists anywhere in the copy.

## Timeline (identical in all four)

| time | scene |
|---|---|
| 0.00 – 3.27 | Hook — three headline beats at 0.5 / 0.9 / 1.3 s |
| 3.27 – 8.74 | Lockup + payoff; brand chips drop at 4.91 / 5.34 / 6.00 / 6.56 |
| 8.74 – 13.11 | Three rows staggered at 9.29 / 10.37 / 11.46 |
| 13.11 – 20.00 | CTA — phone number punches in at 17.47 |

A 0.18 s background dip at each cut, so no two layouts cross-fade into a double
exposure. The music is 110 BPM, so every cut lands on a beat.

## Audio

- **Narration** per language (`src/vo/vo-<lang>.mp3`), entering at 0.45 s. It
  complements the captions rather than reading them aloud — it never repeats the
  on-screen line word for word.
- Music *happy-beats-business-moves-vol-12* (ende-dot-app, 110 BPM), fade in
  0–0.5 s, fade out 18.6–20.0 s, **sidechain-ducked under the voice**.
- SFX: `drop_001` at 4.91 / 5.34 / 6.00 / 6.56 (the chip drops), `bong_001` at
  8.74, `impactSoft_medium_001` at 17.47.
- The bed is `loudnorm`'d on its own; the voice is summed on top and the result is
  **limited, not normalised** — a final loudnorm would renormalise the sum and
  undo the balance.
- Measured: voice **4.6–7.9 dB above the music** in the 300–3000 Hz speech band
  across the whole film; −18.9 / −18.3 / −18.4 LUFS; true peak −4.0 / −3.9 /
  −3.4 dBFS. No silent gap.

## Encode

`libx264 -crf 20 -preset slow -pix_fmt yuv420p -movflags +faststart`, AAC 192 kbps,
30 fps, 20.01 s. Square and wide are derived from the vertical master with a
**blurred fill** — the frame scaled to fill and blurred for the background, then
the untouched vertical laid on top full-height and centred — so nothing is ever
cropped for the platform.

## Facts used

Name, address (Indera Nagar, near Ek Minar Masjid, Khammam, Telangana), hours
(daily 10 AM – 8 PM), phone 76619 72758, CP Plus / Hikvision / Dahua / Prama, free
site survey, laptop sales & service. All of it lives in `lib/site.ts` in the
MaxWorld repo.

**No prices, no client counts, no testimonials, no invented stats.** The shop
publishes none, so the ads claim none.

## Fonts (all OFL 1.1, from github.com/google/fonts)

Ramabhadra · Rozha One · Hind (Regular + SemiBold) · Noto Nastaliq Urdu ·
Space Grotesk — the TTFs travel in [`src/assets/fonts/`](src/assets/fonts).

## Rebuilding

```bash
cd src && bash build.sh en te hi ur
```

To change only the sound of an approved picture, `src/remix.sh` swaps the audio
and copies the video stream — no re-render, no re-encode:

```bash
cd src && bash remix.sh en ../03-maxworld-ad-en-vertical-1080p.mp4 /tmp/out.mp4
```

[`src/index.html`](src/index.html) is the whole composition — one file, four
languages, selected by `?lang=`. [`src/build.sh`](src/build.sh) renders each
language, authors the audio mix, encodes the vertical master, derives the square
and wide variants and pulls the poster. Frame scratch stays in `/tmp`, out of git.

## Honesty

Checked by reading stills at 1.17 / 5.0 / 8.3 / 12.3 / 18.3 / 19.9 s in all four
languages: shaping, line collisions, overlaps, tofu boxes. **They have not been
watched end to end by a human**, so nothing here should be read as "the pacing
feels right" — only as "the frames are correct."
