#!/usr/bin/env node
/**
 * Render every ZeroVast static creative to PNG with puppeteer-core.
 *
 *   node render_creatives.js
 *
 * Why puppeteer and not `chrome --screenshot`: the bare flag hangs indefinitely
 * in this sandbox (even on a data: URL), while puppeteer-core against the same
 * binary returns in under a second. No virtual-time trickery, explicit waits.
 *
 * Determinism: fixed viewport, deviceScaleFactor 1, fonts self-hosted, and a
 * hard gate that the page reported window.__ready (fonts resolved) before the
 * shutter. A board that renders with fallback fonts is a failure, not a creative.
 */
const path = require('path');
const fs = require('fs');
const puppeteer = require('/home/user/.local/hf/node_modules/puppeteer-core');

const HERE = __dirname;
/* Two themes. `ink` is the shipped set: it uses the live site's own tokens and its
   outlined-display signature, so the click-through does not change visual world.
   `paper` is the alternate, matching the approved zero-vast film language. */
const THEMES = ['ink', 'paper'];
const outFor = (t) => path.join(HERE, 'png', t === 'ink' ? '' : 'paper');

// id, w, h — mirrors BOARDS in the brief
const BOARDS = [
  ['speed-feed-1x1', 1080, 1080],
  ['speed-feed-4x5', 1080, 1350],
  ['speed-story-9x16', 1080, 1920],
  ['speed-wide-1.91x1', 1200, 628],
  ['ownership-feed-1x1', 1080, 1080],
  ['ownership-wide-1.91x1', 1200, 628],
  ['limits-feed-1x1', 1080, 1080],
  ['limits-4x5', 1080, 1350],
];

(async () => {
  for (const t of THEMES) fs.mkdirSync(outFor(t), { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: '/home/user/.local/bin/chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--font-render-hinting=none'],
    protocolTimeout: 120000,
  });
  const manifest = [];
  let failed = 0;

  for (const THEME of THEMES)
  for (const [id, w, h] of BOARDS) {
    const page = await browser.newPage();
    await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
    const url = `file://${HERE}/creative.html?id=${id}&w=${w}&h=${h}&theme=${THEME}`;
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.waitForFunction('window.__ready === true', { timeout: 20000 });

    const audit = await page.evaluate(() => {
      const h1 = document.querySelector('h1');
      const r = h1.getBoundingClientRect();
      const cs = getComputedStyle(h1);
      const fam = cs.fontFamily;
      // overflow check: nothing may spill outside the artboard
      const art = document.getElementById('art').getBoundingClientRect();
      // edge spill
      const spill = [...document.querySelectorAll('.mid *, .bottom *')]
        .map(el => el.getBoundingClientRect())
        .filter(b => b.bottom > art.bottom - 4 || b.right > art.right - 4)
        .length;
      // sibling collision: any two blocks on different rows must not overlap
      // vertically, and the header must not overlap the kicker. This is what the
      // first pass missed — brand over kicker, CTA over the URL.
      const boxes = (sel) => [...document.querySelectorAll(sel)].map(e => e.getBoundingClientRect());
      const overlap = (a, b) => a.left < b.right - 2 && b.left < a.right - 2 &&
                                a.top < b.bottom - 2 && b.top < a.bottom - 2;
      const top = document.querySelector('.top').getBoundingClientRect();
      const kick = document.querySelector('.kicker').getBoundingClientRect();
      const collide =
        (overlap(top, kick) ? 1 : 0) +
        (boxes('.bottom .cta').some(a => boxes('.bottom .url').some(b => overlap(a, b))) ? 1 : 0);
      return {
        font: fam,
        h1px: Math.round(parseFloat(cs.fontSize)),
        fits: r.width <= art.width && r.height <= art.height,
        spill,
        // is the display face actually loaded, or did it silently fall back?
        collide,
        loaded: document.fonts.check(`700 100px "Display"`) &&
                document.fonts.check(`400 40px "Text"`) &&
                document.fonts.check(`500 26px "Mono"`),
      };
    });

    if (!audit.loaded || !audit.fits || audit.spill > 0 || audit.collide > 0) {
      console.error(`  FAIL ${id}: ${JSON.stringify(audit)}`);
      failed++;
    }
    const dest = path.join(outFor(THEME), `${id}.png`);
    await page.screenshot({ path: dest });
    const bytes = fs.statSync(dest).size;
    manifest.push({ id, theme: THEME, w, h, bytes, ...audit });
    console.log(`  ${(THEME + ' ' + id).padEnd(30)} ${w}x${h}  ${(bytes / 1024).toFixed(1)} KB  ${audit.loaded ? 'fonts ok' : 'FONT FALLBACK'}`);
    await page.close();
  }

  await browser.close();
  fs.writeFileSync(path.join(HERE, 'png', 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  if (failed) { console.error(`${failed} board(s) failed`); process.exit(1); }
  console.log('all boards rendered');
})();
