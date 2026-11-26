// Motion test (not an episode render): shot 02B phone scroll -> cut on action -> shot 03 glitch.
//   node motion_scroll.mjs   -> motion/ep04_motiontest_02B_03_scroll.mp4 (1920x1080, 24 fps, 6.5 s)
// Fast flicks (thumb up in 0.22 s, ease-out), feed momentum 0.55 s with motion streaks, then the glitch builds.
import { createRequire } from 'node:module';
import { mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { miloDefs, drawHand } from './rig/milo.mjs';
import { worldDefs, W, H, room } from './world.mjs';
import { frame } from './shots.mjs';
import * as V from './views.mjs';
import * as F from './fx.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const FPS = 24;
const DUR = 6.5;
const CUT = 4.6; // cut on action: the last flick stops, the screen blinks
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const flicks = [0.25, 0.95, 1.55, 2.2, 2.75, 3.4, 3.95];

function scrollAt(t) {
  let s = 0.05;
  let vel = 0;
  for (const f of flicks) {
    const u = clamp((t - f - 0.05) / 0.55);
    s += 0.11 * easeOut(u);
    if (u > 0 && u < 1) vel = Math.max(vel, 3 * Math.pow(1 - u, 2));
  }
  return { s, vel };
}
function thumbAt(t) {
  let y = 760;
  for (const f of flicks) {
    const up = clamp((t - f) / 0.22);
    const back = clamp((t - f - 0.25) / 0.3);
    if (t >= f && t < f + 0.6) y = 760 - 200 * easeOut(up) + 200 * easeOut(back);
  }
  return y;
}
const bg02 = `<g transform="translate(960 540) scale(3) translate(-700 -470)" filter="url(#b12)">${room('night')}</g>`;
const bg03 = `<g transform="translate(960 540) scale(3.4) translate(-720 -420)" filter="url(#b12)">${room('night')}</g>`;
function svgAt(t) {
  if (t < CUT) {
    const { s, vel } = scrollAt(t);
    const ty = thumbAt(t);
    const moving = ty < 750;
    const drift = Math.sin(t * 1.3) * 4;
    return frame({ light: 'night', bg: () => bg02, over: () => `<g transform="translate(${drift} 0)">${drawHand('ball', { x: 905, y: 815, scale: 400, deg: 170, stub: 3 })}${V.phoneScreen({ scroll: s, blur: vel > 0.6, deg: -4, k: 0.62, cy: 420 })}${V.swipe(1185, ty, { scale: 400, arcs: moving })}</g>` });
  }
  const u = clamp((t - CUT) / (DUR - CUT));
  const z = 1 + 0.08 * easeOut(u);
  const flicker = t > 5.55 && t < 5.65 ? 0.0 : 0.6;
  const blink = t - CUT < 0.08 ? `<rect width="${W}" height="${H}" fill="#e6dcff" opacity="0.6"/>` : '';
  return frame({ light: 'night', bg: () => bg03, over: () => `<g transform="translate(960 560) scale(${z}) translate(-960 -560)">${drawHand('ball', { x: 890, y: 805, scale: 400, deg: 175, stub: 3 })}${V.phoneScreen({ scroll: scrollAt(CUT).s, glitch: 0.25 + 0.75 * easeOut(u), deg: 16, cx: 1000, cy: 430, k: 0.62 })}${drawHand('ball', { x: 1200, y: 700, scale: 400, deg: 205, stub: 3, flip: -1 })}${F.particles(1000, 560, 500, Math.round(10 + 40 * u), 8)}</g><circle cx="1560" cy="140" r="300" fill="url(#warmGlow)" opacity="${flicker}" style="mix-blend-mode:screen"/>${blink}` });
}

const font = pathToFileURL(join(here, 'rig/fonts/PatrickHand-latin.woff2')).href;
const out = join(here, 'motion');
const tmp = join(out, '_frames');
rmSync(tmp, { recursive: true, force: true });
mkdirSync(tmp, { recursive: true });
const pw = require('playwright');
const browser = await pw.chromium.launch();
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
const shell = join(tmp, 'shell.html');
writeFileSync(shell, `<!doctype html><html><head><meta charset="utf-8"><style>@font-face{font-family:'Patrick Hand';src:url('${font}')}html,body{margin:0;background:#000}svg{display:block}</style></head><body><svg id="s" xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${miloDefs()}${worldDefs()}</defs><g id="c"></g></svg></body></html>`);
await pg.goto(pathToFileURL(shell).href);
await pg.evaluate(() => document.fonts.ready);
const N = Math.round(DUR * FPS);
for (let i = 0; i < N; i++) {
  await pg.evaluate((inner) => { document.getElementById('c').innerHTML = inner; }, svgAt(i / FPS));
  await pg.screenshot({ path: join(tmp, `f${String(i).padStart(4, '0')}.png`) });
}
await browser.close();
const mp4 = join(out, 'ep04_motiontest_02B_03_scroll.mp4');
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', String(FPS), '-i', join(tmp, 'f%04d.png'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-movflags', '+faststart', mp4]);
console.log(mp4, N, 'frames');
