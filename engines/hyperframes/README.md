# HyperFrames as a video engine

Three ZeroVast films in [`works/films/zerovast-hf/`](../../works/films/zerovast-hf)
were made with [HyperFrames](https://github.com/heygen-com/hyperframes) instead of
a timeline editor. The composition is a single HTML file; the MP4 is a render of
it. This file records what that costs and what it buys, so the next film starts
here instead of rediscovering it.

## The deal

```
npx hyperframes init <dir> --skip-skills   # scaffold (don't copy another film)
# write index.html — one paused GSAP timeline, registered on window.__timelines
npx hyperframes check                      # lint, runtime, layout, motion, contrast
npx hyperframes snapshot --at 2,9,14 -o /tmp/x   # stills, plus a contact sheet
npx hyperframes render -w 1 --low-memory-mode -o film.mp4
```

## Contract (violate any of these and it renders blank or black)

- Root element carries `data-composition-id`, `data-start`, `data-duration`,
  `data-width`, `data-height`.
- One paused timeline, registered as `window.__timelines["main"]`, then
  `tl.seek(0)`. `window.__timelines` does not exist until the runtime provides it —
  if you probe the file directly in a browser, define it first.
- No `Date.now`, unseeded `Math.random`, timers or network calls. Every value must
  be reproducible at any seek time.
- Never tween `display`, `visibility` or `autoAlpha` on `.clip`.
- No CSS `transform` on anything GSAP transforms — it will be overwritten and the
  first frame jumps.
- Asset paths relative (`assets/...`); every `<audio>` needs an `id` plus
  `data-start` and `data-volume`.

## Traps that actually cost time

1. **A real photograph behind display type is unusable.** The site's own headline
   reads through scrims and crops. Put type on flat ground, and show the page in a
   separate scene.
2. **`nth-of-type` on a lone child matches the first line, always.** Wrapping each
   line in its own `<span class="ln">` means `.w:nth-of-type(2)` matches nothing —
   and GSAP's "target not found" is a *warning*, so `runtime` still reports ok.
   Read the warning count, not just the error count.
3. **A near-black page makes camera moves invisible.** Screen-grabs of a dark site
   measure 7–27/255; a truck across that looks frozen. Grade the plate
   (`filter:brightness(1.8–2.2)`) and let a caption scrim carry legibility.
4. **Opaque planes in front of text fire `text_occluded`.** Spread the deck; don't
   just raise a z-index.
5. **A scene that never exits reports every later scene as `content_overlap`.**
6. **Layout gates are literal:** absolutely-positioned rows with no `top` stack at
   zero; an `<em>` after a `<br>` can collapse onto the previous line box.
7. **Two renders on one machine silently stall** — they fight over the same Vite
   port, sit at ~0.5 % CPU forever. `pkill -9 -f "hyperframes render"` between
   renders, and use `-w 1` in a sandbox.
8. **Retiming by string replace is unsafe.** `}}, {t});` patterns collide and emit
   broken JS. Retime by script and verify with a `node -e` parse of the
   `<script>` body.

## Measuring the result

Numbers that are worth reporting, all on the delivered MP4:

- duration, resolution, frame rate, audio stream (`ffprobe`)
- loudness and true peak (`loudnorm=I=-18:TP=-1.5:print_format=json`) — target
  roughly −16 LUFS for web
- dead frames: `tblend=all_mode=difference,format=gray,signalstats` sampled every
  30 frames; anything under ~0.15 AVG that is not a deliberate tail fade is a bug
- `silencedetect` for gaps in the audio

A green gate plus those numbers proves a film is not broken. It does not prove it
is good.
