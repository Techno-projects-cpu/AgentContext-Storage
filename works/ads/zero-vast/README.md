# ZeroVast / NEZAAD — claude-ads run

Ads for **zero-vast.vercel.app**, produced with the
[`AgriciDaniel/claude-ads`](https://github.com/AgriciDaniel/claude-ads) skill
(MIT) on 2026-11-09.

Run `zv-2026-11-09-01`. Everything here is either lifted from the site's source
or marked as an unapproved inference.

---

## 🖼 The creatives

**[Contact sheet — all 8 boards](creative/png/contact-sheet.png)** (shipped ink set)
· [paper alternate](creative/png/paper/contact-sheet.png)

| # | Board | Size | File |
|---|---|---|---|
| 1 | speed · feed | 1080×1080 | [`creative/png/speed-feed-1x1.png`](creative/png/speed-feed-1x1.png) |
| 2 | speed · feed 4:5 | 1080×1350 | [`creative/png/speed-feed-4x5.png`](creative/png/speed-feed-4x5.png) |
| 3 | speed · story 9:16 | 1080×1920 | [`creative/png/speed-story-9x16.png`](creative/png/speed-story-9x16.png) |
| 4 | speed · landscape | 1200×628 | [`creative/png/speed-wide-1.91x1.png`](creative/png/speed-wide-1.91x1.png) |
| 5 | ownership · feed | 1080×1080 | [`creative/png/ownership-feed-1x1.png`](creative/png/ownership-feed-1x1.png) |
| 6 | ownership · landscape | 1200×628 | [`creative/png/ownership-wide-1.91x1.png`](creative/png/ownership-wide-1.91x1.png) |
| 7 | limits · feed | 1080×1080 | [`creative/png/limits-feed-1x1.png`](creative/png/limits-feed-1x1.png) |
| 8 | limits · feed 4:5 | 1080×1350 | [`creative/png/limits-4x5.png`](creative/png/limits-4x5.png) |

Copy for every placement, with measured character counts:
**[`creative/copy-deck.md`](creative/copy-deck.md)**

---

## What claude-ads actually did here

claude-ads is a **paid-media analysis skill for Claude Code**, not a video
generator. Its own contract is explicit: *"No skill renders video: video work
ends at concepts and briefs in `ads-create`."* So this run used it the way it is
built to be used — and the last step (rendering pixels) is mine.

| stage | claude-ads part | what it produced |
|---|---|---|
| brand | `skills/ads-dna` → `brand-profile` contract | [`brand/brand-profile.json`](brand/brand-profile.json) — observations vs inferences, each with approval state |
| concepts | `skills/ads-create` | three materially distinct strategic concepts, not three rewrites |
| copy | `ads-create` + `ads/references/copy-frameworks.md` | per-placement copy deck, every claim traceable to a page |
| landing | `skills/ads-landing` message-match | [`landing/landing_check.py`](landing/landing_check.py), all three concepts PASS |
| validation | `claude_ads_core.contracts` | both artifacts validated by the **upstream** validator before writing |

The validator is real, and I checked it rather than trusting it: removing a
required field, using a bogus platform name, dropping a `cta`, or adding an
unknown property each produce a rejection.

## The three concepts

| id | insight | hook | platforms |
|---|---|---|---|
| `h1-speed` | a slow page loses the visitor silently, so the owner never hears the complaint | "Your site is too slow. They leave." | Google, Meta, YouTube, LinkedIn |
| `h2-ownership` | the real objection behind "I'll think about it" is lock-in | "Can you edit your own site? You should." | Google, Meta, LinkedIn |
| `h3-limit` | everyone promises everything; stating limits is the cheapest way to be believed | "Four things I won't do." | Google, Reddit, X, LinkedIn |

Each carries an experiment hypothesis, so they are testable against each other
rather than being three guesses.

## Design

The **ink** set shipped here borrows the live site's own tokens —
`#070707` ground, paper-white type, mono labels, hairline rules, one accent — and
its signature: the display line that drops to outlined type. A click from these
ads lands on a near-black page with outlined display type, so the ad does not
change visual world on click.

The **paper** alternate (`png/paper/`) uses the approved zero-vast film language
(warm paper `#f4f2ec`, ink, blue accent) — consistent with films 01/02 instead of
with the site.

## What is measured, and what is not

Every board is gated at render time, and a board that fails does not ship:

- **fonts loaded** — `document.fonts.check()` for all three families; a silent
  fallback is a failure, not a creative
- **no edge overflow** — nothing may extend past the artboard
- **no block collisions** — header vs kicker, CTA vs URL. This caught two real
  bugs (brand rendering ink-on-ink on the dark board, and a CTA running into the
  URL) that eyeballing had missed.
- final run: **16 boards, 0 collisions, 0 overflow, 0 font fallbacks**

**Not measured, and not claimed:**

- No Core Web Vitals, no mobile rendering, no redirects on the live page:
  `zero-vast.vercel.app` is **unreachable from this sandbox** (`000`), and
  claude-ads' guarded fetcher refuses without an egress attestation. Those checks
  are recorded as **unknown**. Page content was read from the repository that
  deploys to that URL.
- No ad account, budget, or analytics data was supplied, so **no performance
  claim is possible** — the experiment hypotheses are untested by definition.
- **Nobody has looked at these ads in a real placement.** They are correct
  boards, not proven creative. `human_review` is `pending` in the brief, as the
  contract requires.

## Nothing invented

The site publishes **no prices, no testimonials, no client counts, no portfolio
names**. So none appear. Every claim in the copy deck maps to a line on
`index.html` or `capabilities.html`, and `landing_check.py` proves it:

| claim | found on |
|---|---|
| hand-written, vanilla JS | index.html |
| Core Web Vitals budgets | index.html |
| WCAG 2.2 | index.html |
| repository / source code at handover | index.html |
| hosting registered in your name, no markup | capabilities.html |
| three revision rounds | capabilities.html |

## Rebuild

```bash
cd creative && node render_creatives.js          # 16 boards in ~17 s
cd landing  && python3 landing_check.py --site /home/user/ZeroVast \
                 --brief ../creative/creative-brief.json
python3 build_artifacts.py --claude-ads <claude-ads checkout> \
        --site <ZeroVast checkout> --out .
```

Rendering needs `puppeteer-core` (`/home/user/.local/hf/node_modules`). Note:
`chrome --headless --screenshot` **hangs indefinitely** in this sandbox, even on
a `data:` URL; puppeteer-core against the same binary renders in under a second.

## Next, if the owner wants them

1. Approve or reject the brand **inferences** (`brand/brand-profile.json` —
   audience, voice, price sensitivity are all `pending`).
2. Pick ink or paper for the shipped set.
3. Supply the destination URLs: the site is four pages, and `h3-limit` points at
   `capabilities.html`; confirm that is where a "read the limits" click should land.
4. Any pixel spec the platforms require must come from their current official
   documentation — claude-ads deliberately freezes no character limits or
   dimensions, and I have not invented any.
