// Render EP004 frames as PNG.
//   node render_frames.mjs <from> <to> <outdir>      frames [from, to) at 24 fps
//   node render_frames.mjs --at 12.5 33.0 ... <outdir> single moments (seconds) for checking
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { miloDefs } from '../EP04_storyboard_frames_TEST/rig/milo.mjs';
import { worldDefs, W, H } from '../EP04_storyboard_frames_TEST/world.mjs';
import { frameAt } from './episode.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const FPS = 24;
const args = process.argv.slice(2);
const atMode = args[0] === '--at';
const out = args[args.length - 1];
mkdirSync(out, { recursive: true });
const font = pathToFileURL(join(here, '../EP04_storyboard_frames_TEST/rig/fonts/PatrickHand-latin.woff2')).href;
const shell = join(out, `_shell_${process.pid}.html`);
writeFileSync(shell, `<!doctype html><html><head><meta charset="utf-8"><style>@font-face{font-family:'Patrick Hand';src:url('${font}')}html,body{margin:0;background:#000}svg{display:block}</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${miloDefs()}${worldDefs()}</defs><g id="c"></g></svg></body></html>`);
const pw = require('playwright');
const browser = await pw.chromium.launch();
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
await pg.goto(pathToFileURL(shell).href);
await pg.evaluate(() => document.fonts.ready);
const BOIL = ['miloWobble', 'miloWobble1', 'miloWobble2', 'miloWobble3'];
async function one(t, file, idx) {
  // hand-drawn line boil: the character wobble filter changes every 3 frames
  const svg = frameAt(t).replaceAll('url(#miloWobble)', `url(#${BOIL[Math.floor(idx / 3) % 4]})`);
  await pg.evaluate((inner) => { document.getElementById('c').innerHTML = inner; }, svg);
  await pg.screenshot({ path: file });
}
if (atMode) {
  for (const a of args.slice(1, -1)) { await one(+a, join(out, `at_${a}.png`), Math.round(+a * FPS)); console.log('at', a); }
} else {
  const from = +args[0];
  const to = +args[1];
  const t0 = Date.now();
  for (let i = from; i < to; i++) {
    await one(i / FPS, join(out, `f${String(i).padStart(5, '0')}.png`), i);
    if ((i - from) % 200 === 0) console.log(`frames ${i}/${to} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  console.log('done', from, to, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
await browser.close();
