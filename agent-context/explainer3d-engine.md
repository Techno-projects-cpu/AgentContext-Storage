# The 3D explainer engine

`engines/explainer3d/template.html` — one HTML file, CSS 3D transforms + GSAP,
**no WebGL**. It renders through the same HyperFrames pipeline as the brag engine,
so `tooling/render.sh` and the numeric QC gate apply unchanged.

Scaffold a new film: `tooling/new-film.sh my3d portrait 3d`

## The rule that cost the most renders

**CSS may define appearance and final state. It must never put a transform on an
element GSAP also animates.** GSAP parses the element's existing CSS transform as
its *baseline*, so a `translateY(112%)` in CSS becomes an offset added to every
value the timeline writes. Symptoms, all of which look like unrelated bugs:

- a masked line reveal finishes at 112% instead of 0 — the headline is parked
  outside its own mask and the frame looks empty;
- `translate(-50%,-50%)` centring vanishes, because GSAP overwrites the whole
  transform matrix — every plate hangs off the right edge;
- `top:50%; transform:translateY(-50%)` centring compounds with a `y` tween.

Fix: place everything from the timeline with `xPercent`/`yPercent`/`x`/`y`/`z` in
a `tl.set(..., 0)`, keep per-element geometry in `data-` attributes, and centre
with flexbox (`inset:0` + `display:flex`) rather than a transform. There is not a
single centring `translate` left in the engine.

Same reason the mask reveal sets its hidden state with `tl.set(..., 0)` rather
than a CSS class.

## On paper, three more traps

- **A `perspective` scene makes `overflow:hidden` stop clipping.** A scene with
  `perspective: 1400px` is a 3D rendering context, so a window inside it will not
  clip a transformed descendant — the drive rows spilled 500px down the frame.
  The chapter is flat 2D now and its layout fits the window by construction;
  never rely on clipping inside a perspective scene.
- **A faded-out scene leaves a ghost.** On the software GL stack, a scene at
  `opacity: 0` keeps painting a faint copy of itself — a soft grey smear across
  later chapters. `visibility: hidden` is set at the end of the crossfade, which
  is the only thing that removes it. Verified by measurement: background std in
  the smeared band went from 3.35 to 0.47.
- **Hairline outlines read as printing ghosts on light ground.** Rows at
  74–84px with a 1.2px stroke looked like faded ink. Solid translucent ink at
  16% is cleaner and survives encode.

## Three more, found by looking at frames

- **A mask must contain exactly one line.** "Websites built" wrapped to two lines
  inside a mask box sized for the wrapped content, so the second line was sliced
  through its middle and the frame read as a broken mask. Line breaks are explicit
  in the copy now.
- **A clip box cuts at its padding edge.** At `line-height: .9` the glyph box is
  taller than the line box, so a mask with no padding takes the descenders off
  p, y and g. `.m` carries `.10em`/`.26em` padding with matching negative margins,
  and the display line-height is `1.02`.
- **A z-push on 146px type leaves hairline seams** down the strokes, because the
  compositor re-rasterises the glyphs every frame. The hero drifts on `scale`
  instead of `z`: same movement, one clean raster. Large type never rides z.

## A safe area is a number, and the frame border has to obey it

`qc.py` treats the outer 6% as unsafe: at 1080 wide that is 32px each side. A
decorative 1px frame at `inset:50px` is *inside* the frame but outside the safe
area, so it failed `no_edge_cropping` at every timestamp on its own, pointing at
nothing. It sits at 62px now.

## Type floor is a proportion, not a pixel count

The gate measures ink-band height. A 30px absolute floor fails a *correct* 720p
encode of a 1080p master, because 34px of type becomes 22px. `qc.py` now scales
the floor by the render's short side (28px at 1080), with `--type-floor-abs` if
you really want a fixed number.

## Shape

The `FILM` object at the top is the whole edit. Chapters, each `kind`ed:

| kind | does |
|---|---|
| `hero` | type arrives from depth and orbits; used to open and close |
| `dive` | plates fall toward the lens, one per beat, each with `tag`/`line`/`note` |
| `tunnel` | a corridor of rings receding to a vanishing point, then `picks` punch through |

## What the renderer will not do

Everything animated must be a **transform or an opacity**. Animating `letterSpacing`
is a layout property and fails `gsap_non_transform_motion` outright. Animate `y` and
`opacity` instead.

## Five traps, all of them cost a render

1. **Never translate the world toward the camera to fake a dive.** It pushes the
   plates *behind* the viewer, where they magnify off-frame and then vanish.
   Animate each plate's own `z` and cap it around `+150`…`+260` with a simultaneous
   fade.
2. **`perspective: 900px` magnifies anything at `z > 0` violently.** Type that must
   hold its size stays at `z: 0`. Only the corridor and the rings travel.
3. **Keep the type out of the moving element.** The tunnel hero was once a child of
   `[data-world]`, the very element being pushed forward, so the headline rode the
   camera and inflated off-frame. The hero is now a **sibling** of the world.
4. **Don't animate `y` on something that already carries `translateY(-50%)`.** The
   offsets compound and every safe-area calculation is wrong by half the element.
5. **Give each plate a hold.** Arrive by 45% of its beat, hold to 78%, leave. If the
   exit starts before the entrance finishes there is no held frame anywhere, and
   two plates sit superimposed at partial opacity — which reads as a printing
   error, not as depth.

Stagger every layer in x *and* y as well as z. Plates aligned dead-centre in screen
space overlap into unreadable text and trip `content_overlap`.

## Cost

A 24 s 1080×1920 film renders in about **1 m 45 s** on the software GPU. The
`BeginFrame did not run` warning on every render is expected and not a defect.
