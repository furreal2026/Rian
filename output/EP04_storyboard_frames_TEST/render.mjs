// Render EP004 storyboard frames.
//   node render.mjs                 all shots -> frames/shot_01.png … shot_41.png, then contact sheets in sheets/
//   node render.mjs 1 2 15          only these shots
//   node render.mjs --sheets        contact sheets only (from existing frames)
//   node render.mjs --test name     a test composition from shots.mjs TESTS -> _test/name.png
import { createRequire } from 'node:module';
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { miloDefs } from './rig/milo.mjs';
import { worldDefs, W, H } from './world.mjs';
import { SHOTS, TESTS, frame } from './shots.mjs';
import { PLAN } from './plan.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const pw = require('playwright');
const font = pathToFileURL(join(here, 'rig/fonts/PatrickHand-latin.woff2')).href;
const page = (inner) => `<!doctype html><html><head><meta charset="utf-8"><style>@font-face{font-family:'Patrick Hand';src:url('${font}')}html,body{margin:0;background:#efe3cc}svg{display:block}</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>${miloDefs()}${worldDefs()}</defs>${inner}</svg></body></html>`;

const args = process.argv.slice(2);
for (const d of ['frames', 'sheets', '_test', '_html']) mkdirSync(join(here, d), { recursive: true });
const browser = await pw.chromium.launch();
const pg = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
async function shoot(inner, out) {
  const file = join(here, '_html', out.split('/').pop().replace(/\.png$/, '.html'));
  writeFileSync(file, page(inner));
  await pg.goto(pathToFileURL(file).href);
  await pg.evaluate(() => document.fonts.ready);
  await pg.screenshot({ path: out });
}

if (args[0] === '--test') {
  for (const name of args.slice(1)) {
    await shoot(TESTS[name](), join(here, '_test', `${name}.png`));
    console.log('test', name);
  }
} else if (args[0] !== '--sheets') {
  const pick = (x) => !args.length || args.some((a) => a.toUpperCase() === String(x.n).toUpperCase() || (Number(a) && Number(a) === x.n));
  for (const s of SHOTS.filter(pick)) {
    const out = join(here, 'frames', `shot_${String(s.n).padStart(2, '0')}.png`);
    await shoot(frame(s), out);
    console.log('shot', s.n);
  }
}

if (!args.length || args[0] === '--sheets') {
  // contact sheets: 6 frames per page (2 x 3), each with shot number, timecode, narration and camera note
  const full = JSON.parse(readFileSync(join(here, 'shots_full.json'), 'utf-8'));
  // timecodes after the 6 s intro (inserted after shot 06) move 6 s later
  const sec = (t) => { const [m, x] = t.split(':').map(Number); return m * 60 + x; };
  const fmt = (v) => `${String(Math.floor(v / 60)).padStart(2, '0')}:${String(v % 60).padStart(2, '0')}`;
  const shift = (m) => (m.shot > 6 ? { ...m, tc: m.tc.split('–').map((t) => fmt(sec(t) + 6)).join('–') } : m);
  const meta = SHOTS.map((s) => s.intro
    ? { shot: s.n, tc: '01:00–01:06 (+6 s, new)', narration: '(no narration) Title card: CURIOUS MIND logo, EPISODE 004, What If You Could Read Everyone\'s Mind?', camera: '3D CAMERA: Intro card after Milo faints (owner request 2026-11-26). Signal waves + particles behind the logo. 2D LAYOUT: logo and title composited 2D.' }
    : { ...shift(full.find((m) => m.shot === (s.base || s.n))), ...(s.tc ? { tc: s.tc } : {}), shot: s.n });
  const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const cam = (t) => esc(t.replace(/^3D CAMERA:\s*/, '').split('2D LAYOUT:')[0].trim());
  const per = 6;
  const sp = await browser.newPage({ viewport: { width: 2000, height: 2400 }, deviceScaleFactor: 1 });
  for (let i = 0; i < meta.length; i += per) {
    const cells = meta.slice(i, i + per).map((m) => {
      const img = join(here, 'frames', `shot_${String(m.shot).padStart(2, '0')}.png`);
      const src = existsSync(img) ? pathToFileURL(img).href : '';
      return `<div class="c"><div class="h"><b>${String(m.shot) === '06A' ? 'INTRO' : 'SHOT ' + String(m.shot).padStart(2, '0')}</b><span>${m.tc}</span></div><img src="${src}"><p class="n">“${esc(m.narration)}”</p><p class="k">${cam(m.camera)}</p>${PLAN[String(m.shot)] ? `<p class="t"><b>Tempo:</b> ${esc(PLAN[String(m.shot)].tempo)}<br><b>Transisi keluar →</b> ${esc(PLAN[String(m.shot)].out)}</p>` : ''}</div>`;
    }).join('');
    const pageNo = i / per + 1;
    const html = `<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Patrick Hand';src:url('${font}')}
body{margin:0;background:#f3ead8;font-family:'Patrick Hand',sans-serif;color:#2b241e}
.top{display:flex;justify-content:space-between;align-items:baseline;padding:26px 40px 6px}
.top h1{font-size:44px;margin:0;color:#24375e}.top span{font-size:26px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:26px;padding:16px 40px 40px}
.c{background:#fbf6ec;border:2px solid #cdbb9a;border-radius:10px;padding:14px}
.h{display:flex;justify-content:space-between;font-size:30px;margin-bottom:8px}.h b{color:#24375e}
img{width:100%;display:block;border-radius:6px;border:1px solid #b9a483}
.n{font-size:23px;margin:10px 0 4px;line-height:1.2}.k{font-size:19px;margin:0;color:#6b5a45;line-height:1.2}.t{font-size:20px;margin:8px 0 0;padding:6px 10px;background:#efe3c8;border-radius:6px;line-height:1.25;color:#3d3022}.t b{color:#8a3f2a}
.foot{padding:0 40px 24px;font-size:20px;color:#6b5a45}
</style></head><body><div class="top"><h1>Curious Mind — EP004 · What If You Could Read Everyone's Mind?</h1><span>Storyboard v2 · page ${pageNo}/${Math.ceil(meta.length / per)}</span></div>
<div class="grid">${cells}</div><div class="foot">TEST storyboard frames for approval of blocking and framing. Milo from the approved v2 rig (curious-mind 203bfc9); environments are code-drawn sketches, not final plates.</div></body></html>`;
    const f = join(here, '_html', `sheet_${pageNo}.html`);
    writeFileSync(f, html);
    await sp.goto(pathToFileURL(f).href);
    await sp.evaluate(() => document.fonts.ready);
    await sp.waitForLoadState('networkidle');
    const h = await sp.evaluate(() => document.body.scrollHeight);
    await sp.setViewportSize({ width: 2000, height: h });
    await sp.screenshot({ path: join(here, 'sheets', `ep04_storyboard_page_${String(pageNo).padStart(2, '0')}.png`) });
    console.log('sheet', pageNo);
  }
}
await browser.close();
