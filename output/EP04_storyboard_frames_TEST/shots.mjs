// EP004 shot compositions. Each shot: a location master (world.mjs), a camera on it, Milo + extras, overlays.
import { drawMilo, miloParts, pose, POSES } from './rig/milo.mjs';
import { reach, reachDown, plant, groundLock, walk } from './rig/anim.mjs';
import * as P from './rig/props.mjs';
import * as Wd from './world.mjs';
const { W, H, finish } = Wd;

const n = (v) => +(+v).toFixed(2);
export const M = (pz) => drawMilo(pose(pz));
const prop = (pz, inner) => P.propLayer(pz, inner);

// ---------------------------------------------------------------- frame assembly
/** s: { light, cam:{x,y,z,r}, bg(), mid(), fg(), over(), bgBlur, fgBlur, finish:{} } — bg/mid/fg in world coords */
export function frame(s) {
  const c = { x: W / 2, y: H / 2, z: 1, r: 0, ...(s.cam || {}) };
  const camT = `translate(${W / 2} ${H / 2}) rotate(${c.r}) scale(${c.z}) translate(${-c.x} ${-c.y})`;
  const bf = s.bgBlur ? `filter="url(#${s.bgBlur})"` : '';
  const ff = s.fgBlur ? `filter="url(#${s.fgBlur})"` : '';
  return `<rect width="${W}" height="${H}" fill="#efe3cc"/>
<g transform="${camT}"><g ${bf}>${s.bg ? s.bg() : ''}</g>${s.mid ? s.mid() : ''}<g ${ff}>${s.fg ? s.fg() : ''}</g></g>
${s.over ? s.over() : ''}${finish(s.light || 'day', s.finish || {})}`;
}

// ---------------------------------------------------------------- Milo poses for this episode
/** reclined on the bed, legs forward, phone held up in front of the face (side view, facing right) */
export function recline(x, y, scale, o = {}) {
  let p = { view: 'side', facing: 1, x, y, scale, hip: [0, 1.56], lean: o.lean ?? -34, headTilt: o.headTilt ?? 4, expr: o.expr || 'calm', look: o.look || [0.5, 0.25],
    legR: { a1: 88, a2: 90, foot: -88 }, legL: { a1: 86, a2: 89, foot: -88 } };
  const { joints } = miloParts(pose(p));
  const hc = joints.headC;
  const t = o.phoneAt || [hc[0] + 1.35, hc[1] + 0.75];
  p = reach(p, 'R', t, -1);
  p = reach(p, 'L', [t[0] - 0.02, t[1] + 0.12], -1);
  p.armL = { ...p.armL, z: 'back' };
  return { p, phone: t, hc };
}
/** the phone in figure space, seen nearly edge-on in Milo's hands */
export function heldPhone(p, t, { glow = true, screen = '#a9c8e6', deg = -62 } = {}) {
  const ph = `<g transform="translate(${t[0] + 0.05} ${t[1] - 0.25}) rotate(${deg})"><rect x="-0.17" y="-0.32" width="0.34" height="0.64" rx="0.06" fill="#2f333a" stroke="#1e1914" stroke-width="0.04"/><rect x="-0.13" y="-0.27" width="0.26" height="0.52" rx="0.03" fill="${screen}"/></g>`;
  return (glow ? `<g transform="translate(${n(p.x)} ${n(p.y)}) scale(${p.scale})"><circle cx="${t[0] - 0.3}" cy="${t[1] - 0.6}" r="1.6" fill="url(#screenGlow)" opacity="0.55" style="mix-blend-mode:screen"/></g>` : '') + prop(p, ph);
}

// ---------------------------------------------------------------- shared pieces
import * as L from './locations.mjs';
import * as F from './fx.mjs';
import { drawHand } from './rig/milo.mjs';
import * as V from './views.mjs';
const R = Wd.ROOM;
const MS = 70; // Milo scale in the room master
const WALK = POSES.berjalan;
const dimPhone = '#3b3f46';
const wallCol = (l) => Wd.LIGHT[l].wall;

/** room wall with a window opening (screen space), curtains and sill — for shots looking out of Milo's window */
function windowOverlay(light, x0, y0, w, h, o = {}) {
  const wall = wallCol(light);
  let s = `<path d="M0 0 H${W} V${H} H0 Z M${x0} ${y0} V${y0 + h} H${x0 + w} V${y0} Z" fill="${wall}" fill-rule="evenodd"/>`;
  s += Wd.rect(x0 - 22, y0 - 22, w + 44, h + 44, 'none', { sw: 22, stroke: '#e9e0cf', so: 1 }) + Wd.rect(x0 - 22, y0 - 22, w + 44, h + 44, 'none', { sw: 2.4 });
  s += Wd.ln(x0 + w / 2, y0, x0 + w / 2, y0 + h, { sw: 14, stroke: '#e9e0cf', so: 1 }) + Wd.rect(x0 - 60, y0 + h + 14, w + 120, 30, '#e9e0cf');
  const cur = light === 'night' ? '#5c6b90' : '#8aa0c4';
  s += Wd.pth(`M${x0 - 160} ${y0 - 60} L${x0 + 70} ${y0 - 60} Q${x0 + 40} ${y0 + h * 0.5} ${x0 + 90} ${y0 + h + 80} L${x0 - 160} ${y0 + h + 80} Z`, cur);
  s += Wd.pth(`M${x0 + w + 160} ${y0 - 60} L${x0 + w - 70} ${y0 - 60} Q${x0 + w - 40} ${y0 + h * 0.5} ${x0 + w - 90} ${y0 + h + 80} L${x0 + w + 160} ${y0 + h + 80} Z`, cur);
  return `<g ${o.blur ? `filter="url(#${o.blur})"` : ''}>${Wd.wc(s)}</g>`;
}
const neighbour = (pz = {}, o = {}) => Wd.extra({ view: 'side', facing: -1, x: 1430, y: 848, scale: 58, armR: { a1: -70, a2: -95 }, ...pz }, { top: '#9fae84', bottom: '#6a5a50', acc: ['hat', 'apron', 'can'], ...o });
const neighbourWave = () => Wd.extra(F.wave({ view: 'front', x: 1430, y: 848, scale: 58 }, 'L'), { top: '#9fae84', bottom: '#6a5a50', acc: ['hat', 'apron'] });
/** Milo seen from behind, large, as an over-the-shoulder foreground (screen space) */
const otsMilo = (x, y, scale, blur = 'b3', o = {}) => `<g filter="url(#${blur})">${M({ view: 'back', x, y, scale, armR: { a1: 10, a2: 6 }, armL: { a1: -10, a2: -6 }, ...o })}</g>`;
const cafeCashier = (o = {}) => Wd.extra({ x: 1180, y: 880, scale: 74, armR: { a1: 30, a2: 70 }, armL: { a1: -30, a2: -70 }, ...o }, { top: '#efe6d6', bottom: '#5b6070', acc: ['apron', 'id'], apron: '#7d5e43' });
const plazaCrowd = (o = {}) => L.crowd('far', { seed: 11 }) + L.crowd('mid', { seed: 12, ...o });
const parkExtras = () =>
  Wd.extra({ x: 2150, y: 900, scale: 44, hip: [0, 0.62], legL: { a1: -8, a2: -8 }, legR: { a1: 8, a2: 8 } }, { top: '#9a86a8', bottom: '#5f5a68', blur: 'b2', acc: ['glasses'] }) +
  Wd.extra({ ...WALK, x: 1750, y: 960, scale: 46 }, { top: '#7d93ad', bottom: '#4f5566', acc: ['bag'], blur: 'b2' }) +
  Wd.extra({ view: 'side', facing: 1, x: 420, y: 950, scale: 46, armR: { a1: 50, a2: 110, hand: 'explain' } }, { top: '#c98f6f', bottom: '#44505e', blur: 'b2' }) +
  Wd.extra({ view: 'side', facing: -1, x: 560, y: 950, scale: 46 }, { top: '#8a9a72', bottom: '#5b6070', acc: ['tote'], blur: 'b2' });

// ---------------------------------------------------------------- the 41 shots + intro
export const SHOTS = [
  // ===== SEQUENCE 1 — THE SIGNAL
  { n: 1, light: 'night', finish: { vignette: 1.2 },
    over: () => { const { p, phone } = V.leanBoard(MS, { phone: true, expr: 'calm', look: [0.5, 0.3] }); const inside = `<g transform="translate(960 470) scale(-1.22 1.22) translate(-505 -540)">${Wd.room('night', { noPillow: true })}${M(p)}${heldPhone(p, phone)}${Wd.blanket('night', 470, 960)}</g>`; return V.yardWindow(inside); } },
  { n: '02A', base: 2, tc: '00:10–00:15', light: 'night', cam: { x: 960, y: 560, z: 1.0 }, bg: () => V.bedFootView('night'),
    mid: () => V.footMilo({ phone: true, earphones: true, expr: 'calm', look: [0, 0.45] }).svg + V.footBlanket('night'),
    fg: () => Wd.wc(Wd.pth(`M-100 1150 Q300 980 700 1100 L700 1300 L-100 1300 Z`, '#5d6f98') + Wd.pth(`M1300 1120 Q1700 980 2100 1060 L2100 1300 L1300 1300 Z`, '#5d6f98')), fgBlur: 'b8' },
  { n: '02B', base: 2, tc: '00:15–00:20', light: 'night', bg: () => `<g transform="translate(960 540) scale(3) translate(-700 -470)" filter="url(#b12)">${Wd.room('night')}</g>`,
    over: () => drawHand('ball', { x: 905, y: 815, scale: 400, deg: 170, stub: 3 }) + V.phoneScreen({ scroll: 0.42, blur: true, deg: -4, k: 0.62, cy: 420 }) + V.swipe(1185, 690, { scale: 400 }) },
  { n: 3, light: 'night', bg: () => `<g transform="translate(960 540) scale(3.4) translate(-720 -420)" filter="url(#b12)">${Wd.room('night')}</g>`,
    over: () => drawHand('ball', { x: 890, y: 805, scale: 400, deg: 175, stub: 3 }) + V.phoneScreen({ scroll: 0.5, glitch: 0.85, deg: 16, cx: 1000, cy: 430, k: 0.62 }) + drawHand('ball', { x: 1200, y: 700, scale: 400, deg: 205, stub: 3, flip: -1 }) + `<circle cx="1560" cy="140" r="300" fill="url(#warmGlow)" opacity="0.6" style="mix-blend-mode:screen"/>` + F.particles(1000, 560, 500, 40, 8) },
  { n: 4, light: 'night', bg: () => `<g transform="translate(960 540) scale(3) translate(-1100 -500)" filter="url(#b12)">${Wd.room('night')}</g>`,
    over: () => {
      const p = { view: 'side', facing: 1, x: 560, y: 2350, scale: 380, expr: 'netral', look: [0.6, 0.4], headTilt: -4, armR: { a1: 40, a2: 120 }, armL: { hide: true } };
      return M(p) + F.earphones(p, [2.2, -1.0], { glow: true }) + `<g opacity="0.85">${F.signalWaves(1150, 760, 30, 260, 6, { arc: [-150, -30], glow: 0.5 })}</g>` + F.particles(1100, 700, 300, 30, 4) + Wd.phoneProp(1500, 980, 6, -20, '#c6b2ff', true);
    } },
  { n: 5, light: 'night', cam: { x: 960, y: 470, z: 1.12, r: -8 }, bg: () => V.bedFootView('night', { curtain: 120 }),
    mid: () => V.footMilo({ expr: 'kaget', look: [0.2, -0.6], headTilt: -6, armL: { a1: -70, a2: -120 }, armR: { a1: 75, a2: 125 }, earphones: false }).svg + V.footBlanket('night', 20) + Wd.phoneProp(1240, 300, 3.2, 40, '#c6b2ff', true) + `<path d="M1160 520 Q1200 400 1230 340" fill="none" stroke="#fbf6ec" stroke-width="5" opacity="0.6"/>`,
    over: () => F.signalWaves(1240, 330, 80, 1500, 10, { glow: 1, sw: 8 }) + F.particles(1000, 450, 900, 90, 2) },
  { n: 6, light: 'night', cam: { x: 960, y: 600, z: 1.35, r: 4 }, finish: { dark: 0.42, vignette: 1.5 }, bg: () => V.bedFootView('night'),
    mid: () => V.footMilo({ expr: 'tidur', headTilt: 26, faceX: -0.06, armL: { a1: -8, a2: 6 }, armR: { a1: 10, a2: -4 } }).svg + V.footBlanket('night') + Wd.phoneProp(1150, 990, 2.6, 70, '#3b3f46') },
  { n: '06A', intro: true, light: 'night', finish: { vignette: 0.6 }, over: () => F.introCard() },

  // ===== SEQUENCE 2 — THE FIRST THOUGHT
  { n: 7, light: 'morning', cam: { x: 930, y: 560, z: 1.06 }, bg: () => Wd.room('morning', { noPillow: true }),
    mid: () => { const { p } = V.leanBoard(MS, { lean: -2, headTilt: 6, expr: 'ngantuk' }); return M(F.rubHead(p, 'R')) + Wd.blanket('morning', 470, 960) + Wd.phoneProp(1600, 628, 1.6, 90, dimPhone); } },
  { n: 8, light: 'morning', cam: { x: 1500, y: 640, z: 1.25 }, bgBlur: 'b1', bg: () => L.street('morning'), mid: () => neighbour(),
    over: () => windowOverlay('morning', 300, 110, 1300, 800) + otsMilo(420, 1900, 300, 'b5') },
  { n: 9, light: 'morning', cam: { x: 1420, y: 700, z: 0.95 }, bgBlur: 'b2', bg: () => L.street('morning'),
    mid: () => neighbour(),
    over: () => windowOverlay('morning', 980, 140, 820, 760) + F.bubble(1440, 330, 120, ['plantWilt', 'hose'], { tail: [1330, 520] }) + M({ view: 'side', facing: 1, x: 560, y: 1820, scale: 270, expr: 'penasaran', look: [0.7, -0.1], headTilt: -4, armR: { a1: 10, a2: 6 } }) },
  { n: 10, light: 'morning', cam: { x: 960, y: 420, z: 2.3 }, bgBlur: 'b5', bg: () => Wd.room('morning'),
    mid: () => M(F.handsOnHead({ x: 960, y: 760, scale: 92, expr: 'kaget' })),
    over: () => [0, 1, 2].map((k) => `<path d="M${560 - k * 60} ${320 - k * 40} Q${500 - k * 60} ${440} ${560 - k * 60} ${560 + k * 40}" fill="none" stroke="#2b241e" stroke-width="4" opacity="${0.5 - k * 0.12}"/><path d="M${1360 + k * 60} ${320 - k * 40} Q${1420 + k * 60} ${440} ${1360 + k * 60} ${560 + k * 40}" fill="none" stroke="#2b241e" stroke-width="4" opacity="${0.5 - k * 0.12}"/>`).join('') },
  { n: 11, light: 'morning', cam: { x: 1460, y: 650, z: 1.4 }, bgBlur: 'b1', bg: () => L.street('morning'),
    mid: () => neighbourWave() + F.bubble(1600, 430, 95, ['list', 'fern'], { tail: [1450, 560] }),
    over: () => windowOverlay('morning', 300, 110, 1300, 800) + otsMilo(380, 1950, 310, 'b5') },

  // ===== SEQUENCE 3 — SOCIAL STATIC
  { n: 12, light: 'morning', cam: { x: 1500, y: 610, z: 1.0 }, bg: () => L.street('morning'),
    mid: () => M({ ...WALK, x: 1300, y: 852, scale: 50 }) + Wd.extra({ ...WALK, facing: -1, x: 2150, y: 850, scale: 48 }, { top: '#b9867a', bottom: '#5b6070', acc: ['bag'], blur: 'b1' }),
    fg: () => Wd.pot(700, 1120, 3.4) + Wd.pot(2350, 1140, 3.0, '#7f9a5e', '#a8684a'), fgBlur: 'b8' },
  { n: 13, light: 'morning', cam: { x: 2020, y: 690, z: 1.55 }, bg: () => L.street('morning'),
    mid: () => Wd.extra({ view: 'side', facing: -1, x: 2260, y: 852, scale: 50, armR: { a1: 8, a2: 24 } }, { top: '#c8a97a', bottom: '#4f5566', acc: ['tote'], bread: true, blur: 'b1' }) +
      Wd.extra({ ...WALK, x: 1680, y: 850, scale: 48 }, { top: '#7d93ad', bottom: '#44505e', acc: ['cap'], blur: 'b2' }) + Wd.extra({ x: 2480, y: 848, scale: 47 }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['phone'], blur: 'b2' }) +
      M({ ...WALK, x: 1980, y: 856, scale: 52, expr: 'penasaran', look: [0.6, 0] }) +
      F.bubble(2280, 520, 52, ['bread']) + F.bubble(1700, 540, 46, ['key']) + F.bubble(2490, 530, 46, ['lunch']) },
  { n: 14, light: 'morning', cam: { x: 2020, y: 680, z: 2.0 }, bgBlur: 'b2', bg: () => L.street('morning'),
    mid: () => Wd.extra({ view: 'side', facing: -1, x: 2150, y: 852, scale: 52, headTilt: 6, armR: { a1: -8, a2: -14 } }, { top: '#b97a6a', bottom: '#5f5a68', acc: ['bag'], bag: '#7d5e43', blur: 'b1' }) +
      M({ view: 'side', facing: 1, x: 1900, y: 856, scale: 54, expr: 'senang', headTilt: -4, armR: { a1: 6, a2: 4 } }) },
  { n: 15, light: 'morning', cam: { x: 1930, y: 610, z: 3.4, r: 4 }, bgBlur: 'b5', bg: () => L.street('morning'),
    mid: () => Wd.extra({ view: 'side', facing: -1, x: 2150, y: 852, scale: 52 }, { top: '#b97a6a', bottom: '#5f5a68', acc: ['bag'], blur: 'b5' }) + M({ ...WALK, x: 1900, y: 856, scale: 54, expr: 'kaget', look: [0.5, -0.2] }),
    over: () => F.bubble(1560, 270, 150, ['question', 'stain'], { tail: [1820, 470] }) },
  { n: 16, light: 'morning', cam: { x: 1930, y: 690, z: 2.2 }, bgBlur: 'b3', finish: { vignette: 1.5 }, bg: () => L.street('morning'),
    mid: () => { let p = { x: 1930, y: 856, scale: 54, expr: 'bingung', look: [0, 1], headTilt: 10 }; p = reach(p, 'R', [-0.28, -2.75], 1); p = reach(p, 'L', [0.15, -2.35], -1); return M({ ...p, armR: { ...p.armR, z: 'front' }, armL: { ...p.armL, z: 'front' } }); } },
  { n: 17, light: 'morning', bg: () => V.street3d('morning', { people: [
      { z: 6.5, svg: () => M({ ...V.placeAt(-4.3, 6.5), view: 'front', expr: 'netral', look: [0.3, 0], legL: { a1: -6, a2: 4 }, legR: { a1: 8, a2: 2 }, armL: { a1: -24, a2: -16 }, armR: { a1: 10, a2: 6 } }) },
      { z: 13, svg: () => Wd.extra({ ...V.placeAt(-4.6, 13, 1.5), armR: { a1: 20, a2: 150 } }, { top: '#8a9a72', bottom: '#4f5566', acc: ['phone'], blur: 'b1' }) },
      { z: 11, svg: () => Wd.extra({ ...V.placeAt(4.4, 11, 1.5), view: 'side', facing: 1, armR: { a1: 8, a2: 24 } }, { top: '#c98f6f', bottom: '#5b6070', acc: ['tote'], bread: true, blur: 'b1' }) },
      { z: 19, svg: () => Wd.extra({ ...V.placeAt(5.2, 19, 1.5), view: 'side', facing: 1, armR: { a1: 60, a2: 80 } }, { top: '#7d93ad', bottom: '#44505e', acc: ['bag'], blur: 'b1' }) },
      { z: 27, svg: () => Wd.extra({ ...V.placeAt(-4.2, 27, 1.5), ...WALK, facing: -1 }, { top: '#9a86a8', bottom: '#5f5a68', blur: 'b2' }) },
    ] }) },
  { n: 18, light: 'morning', cam: { x: 2680, y: 640, z: 1.45 }, bg: () => L.street('morning'),
    mid: () => Wd.extra({ view: 'side', facing: 1, x: 2660, y: 850, scale: 50, armR: { a1: 50, a2: 110, hand: 'explain' } }, { top: '#c8a97a', bottom: '#4f5566', acc: ['tote'], blur: 'b1' }) +
      Wd.extra({ view: 'side', facing: -1, x: 2850, y: 850, scale: 50, headTilt: 6 }, { top: '#7d93ad', bottom: '#5b6070', acc: ['glasses'], blur: 'b1' }) +
      F.bubble(2620, 480, 58, ['smile']) + F.bubble(2620, 340, 50, ['clock', 'zz'], { op: 0.75 }) + F.bubble(2890, 480, 58, ['heart']) + F.bubble(2890, 340, 50, ['briefcase'], { op: 0.75 }) +
      M({ ...WALK, x: 2470, y: 860, scale: 58, expr: 'penasaran', look: [0.7, -0.3] }) },
  { n: 19, light: 'day', cam: { x: 1010, y: 600, z: 1.05 }, bg: () => L.cafe('day'),
    mid: () => cafeCashier() + L.cafeCounter() + Wd.extra({ view: 'back', x: 1180, y: 920, scale: 62 }, { top: '#7d93ad', bottom: '#44505e', acc: ['bag'] }) + Wd.extra({ view: 'back', x: 1090, y: 975, scale: 68 }, { top: '#9a86a8', bottom: '#5f5a68' }) + M({ view: 'back', x: 980, y: 1035, scale: 74 }),
    fg: () => L.chair(330, 1180, 1.7) + L.cafeTable(560, 1180, 1.6) + Wd.pot(1720, 1200, 3.4), fgBlur: 'b8' },
  { n: 20, light: 'day', cam: { x: 1150, y: 560, z: 1.55 }, bgBlur: 'b1', bg: () => L.cafe('day', { machineNoise: true }),
    mid: () => cafeCashier() + L.cafeCounter() + F.bubble(1180, 230, 95, ['queue', 'machine'], { tail: [1180, 420] }) + Wd.extra({ view: 'side', facing: 1, x: 1520, y: 980, scale: 70, hip: [0, 0.8], legL: { a1: 60, a2: 20 }, legR: { a1: 70, a2: 20 } }, { top: '#8a9a72', bottom: '#5b6070', blur: 'b2' }) + F.bubble(1600, 520, 60, ['laptop', 'book', 'music'], { op: 0.9 }),
    over: () => otsMilo(300, 1950, 330, 'b5') },

  // ===== SEQUENCE 4 — TOO MANY MINDS
  { n: 21, light: 'day', cam: { x: 1500, y: 600, z: 0.95 }, bg: () => L.plaza('day'), mid: () => plazaCrowd() + M({ ...WALK, x: 1420, y: 892, scale: 50 }) },
  { n: 22, light: 'day', cam: { x: 1650, y: 690, z: 1.65, r: -1 }, bg: () => L.plaza('day'),
    mid: () => plazaCrowd() + M({ ...WALK, x: 1640, y: 896, scale: 52, expr: 'penasaran', look: [0.5, -0.3] }) + F.bubble(1460, 560, 46, ['plate']) + F.bubble(1840, 540, 46, ['music']) + F.bubble(1980, 600, 40, ['phone'], { op: 0.8 }),
    fg: () => L.crowd('near', { seed: 31, x0: 1150, x1: 2200 }) },
  { n: 23, light: 'day', cam: { x: 960, y: 480, z: 1.05, r: 0 }, bg: () => V.crowdTop(),
    mid: () => [[620, 300, ['lock']], [800, 170, ['plate']], [1150, 160, ['phone']], [1330, 300, ['music']], [560, 520, ['list']], [1380, 560, ['briefcase']], [960, 120, ['clock']], [760, 700, ['bread']], [1200, 720, ['cash']], [420, 220, ['tab']], [1520, 200, ['book']]].map(([x, y, i], k) => F.bubble(x, y, 56 + (k % 3) * 10, i, { op: 0.92 - (k % 3) * 0.1 })).join('') +
      F.words(560, 110, 'Did I lock the door?', 34) + F.words(1180, 90, "What's for dinner?", 34, { rot: 5 }) + F.words(420, 640, 'call Mom…', 30, { rot: -4 }) + F.words(1330, 690, '♪ that song…', 30, { rot: 4 }) },
  { n: 24, light: 'day', cam: { x: 1650, y: 560, z: 2.3, r: 2 }, bgBlur: 'b5', bg: () => L.plaza('day') + plazaCrowd(),
    over: () => { let s = ''; const r = Wd.rng(7); for (let k = 0; k < 26; k++) { const ic = ['tab', 'music', 'plate', 'lock', 'phone', 'clock', 'list', 'cash', 'bread', 'briefcase', 'book'][k % 11]; s += F.bubble(120 + r() * 1680, 90 + r() * 760, 50 + r() * 50, [ic], { op: 0.55 + r() * 0.4 }); } return s + F.words(300, 980, 'tab 47', 34, { op: 0.6 }); } },
  { n: 25, light: 'day', cam: { x: 1520, y: 640, z: 6.2 }, bgBlur: 'b12', finish: { vignette: 1.8 }, bg: () => L.plaza('day') + plazaCrowd(),
    mid: () => M({ x: 1520, y: 870, scale: 52, expr: 'takut', look: [0.8, -0.1], faceX: 0.1 }) },
  { n: 26, light: 'day', cam: { x: 1650, y: 610, z: 2.4 }, bgBlur: 'b5', bg: () => L.plaza('day') + plazaCrowd(),
    mid: () => F.bubble(1450, 470, 55, ['tab'], { op: 0.35 }) + F.bubble(1860, 450, 55, ['music'], { op: 0.35 }) + M(F.handsOnHead({ x: 1650, y: 896, scale: 56, expr: 'takut' })),
    over: () => F.bubble(250, 320, 130, ['clock'], { op: 0.3, blur: 'b5' }) + F.bubble(1680, 820, 140, ['lock'], { op: 0.3, blur: 'b5' }) },
  { n: 27, light: 'day', cam: { x: 2800, y: 640, z: 1.35 }, bg: () => L.plaza('day'),
    mid: () => `<g filter="url(#b2)">${L.crowd('mid', { seed: 12, x0: 1600, x1: 2550 })}</g>` + M({ ...WALK, x: 2900, y: 892, scale: 54, expr: 'netral', headTilt: 14, look: [0.3, 0.8] }) },

  // ===== SEQUENCE 5 — THE CAT
  { n: 28, light: 'afternoon', cam: { x: 960, y: 760, z: 1.0 }, bg: () => L.yard('afternoon'),
    mid: () => M({ ...WALK, x: 620, y: 905, scale: 52, expr: 'penasaran', look: [0.6, 0] }) + L.cat(1380, 1080, 2.6, 'sit', -1),
    fg: () => Wd.wc([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((k) => Wd.pth(`M${-40 + k * 180} 1300 l18 -120 l14 110 l22 -90 l8 100`, '#7d9a62', { so: 0.5 })).join('')), fgBlur: 'b5' },
  { n: 29, light: 'afternoon', cam: { x: 1010, y: 780, z: 1.8 }, bg: () => L.yard('afternoon'),
    mid: () => M(F.squat({ x: 880, y: 912, scale: 66, expr: 'penasaran', look: [0.7, 0.2] })) + L.cat(1130, 905, 1.25, 'sit', -1, { lookAway: true }),
    fg: () => Wd.wc(Wd.ell(1260, 1010, 90, 26, '#6f8fa8') + Wd.ell(1260, 1004, 70, 14, '#b98b55')), fgBlur: 'b3' },
  { n: 30, light: 'afternoon', cam: { x: 1120, y: 720, z: 2.6 }, bgBlur: 'b5', bg: () => L.yard('afternoon'),
    mid: () => L.cat(1120, 905, 1.25, 'sit', -1, { lookAway: true }),
    over: () => F.bubble(1180, 230, 150, ['bowl', 'fish']) + F.bubble(1580, 420, 110, ['cushion', 'door'], { op: 0.9 }) },
  { n: 31, light: 'afternoon', cam: { x: 1080, y: 740, z: 1.3 }, bg: () => L.yard('afternoon'),
    mid: () => M(F.squat({ x: 820, y: 912, scale: 66, expr: 'netral', look: [0.7, 0] }, [1.45, -1.85])) + L.cat(1460, 912, 1.2, 'walk', 1) },

  // ===== SEQUENCE 6 — WHAT THOUGHTS REALLY MEAN
  { n: 32, light: 'afternoon', cam: { x: 1200, y: 640, z: 1.05 }, bg: () => L.park('afternoon'),
    mid: () => M(F.sideSit(1150, 880, 80, { expr: 'netral', look: [0.2, 0.3], headTilt: 6 })),
    fg: () => Wd.bush(250, 1200, 2.6) + Wd.bush(2150, 1210, 2.4), fgBlur: 'b8' },
  { n: 33, light: 'afternoon', cam: { x: 1250, y: 650, z: 1.1 }, bgBlur: 'b1', bg: () => L.park('afternoon'), mid: () => parkExtras(),
    over: () => `<g filter="url(#b3)">${F.frontSit(560, 1500, 1150, 260, { pose: (p) => ({ ...p, view: 'back' }) })}</g>` },
  { n: 34, light: 'afternoon', cam: { x: 1150, y: 600, z: 1.95 }, bg: () => L.park('afternoon'),
    mid: () => Wd.extra({ view: 'side', facing: 1, x: 760, y: 950, scale: 46 }, { top: '#c98f6f', bottom: '#44505e', blur: 'b2', acc: ['tote'] }) + F.bubble(800, 520, 70, ['photo', 'question', 'rain'], { op: 0.85 }) + F.bubble(960, 400, 56, ['smile', 'spiral'], { op: 0.7 }) +
      M(F.sideSit(1150, 880, 80, { expr: 'penasaran', pose: F.chinHand, look: [0.5, -0.3] })) },
  { n: 35, light: 'afternoon', cam: { x: 1700, y: 760, z: 1.45 }, bg: () => L.park('afternoon'),
    mid: () => Wd.extra({ view: 'side', facing: -1, x: 1880, y: 985, scale: 54, headTilt: 18, armR: { a1: -40, a2: -60 }, armL: { a1: -30, a2: -50 } }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['glasses'] }) +
      M({ ...WALK, x: 1450, y: 990, scale: 58, expr: 'penasaran', look: [0.7, 0.4] }),
    fg: () => Wd.wc([[1700, 1010, '#e09a4a'], [1760, 1030, '#e09a4a'], [1640, 1040, '#d9883e']].map(([x, y, c]) => Wd.ell(x, y, 16, 15, c)).join('') + Wd.rect(1560, 1000, 70, 46, '#6f8fa8', { rx: 4 }) + Wd.rect(1800, 1040, 80, 18, '#c98f5c')) },
  { n: 36, light: 'afternoon', cam: { x: 1700, y: 760, z: 1.9 }, bgBlur: 'b3', bg: () => L.park('afternoon'),
    mid: () => Wd.extra({ view: 'side', facing: -1, x: 1860, y: 985, scale: 54, headTilt: 14, armR: { a1: -60, a2: -90 } }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['glasses'] }) +
      M(F.squat({ x: 1600, y: 992, scale: 58, expr: 'senang' }, [1.65, -2.1])) + Wd.wc(Wd.rect(1745, 862, 70, 46, '#6f8fa8', { rx: 4 })) },

  // ===== SEQUENCE 7 — THE POWER IS STILL THERE
  { n: 37, light: 'dusk', bg: () => V.street3d('dusk', { people: [
      { z: 7, svg: () => M({ ...V.placeAt(4.3, 7), ...V.walkAway(0.9) }) },
    ] }) },
  { n: 38, light: 'dusk', cam: { x: 990, y: 600, z: 1.05 }, bg: () => Wd.room('dusk'),
    mid: () => M(F.sideSit(820, 790, 92, { expr: 'netral', look: [0.6, 0.2] })) + Wd.phoneProp(1600, 628, 1.6, 90, dimPhone) },
  { n: 39, light: 'dusk', cam: { x: 930, y: 700, z: 1.05 }, bgBlur: 'b2', bg: () => L.yard('dusk') + L.cat(1110, 905, 1.0, 'sit', -1),
    mid: () => F.bubble(1180, 600, 60, ['bowl'], { tail: [1120, 740] }),
    over: () => windowOverlay('dusk', 980, 160, 820, 720) + M({ view: 'side', facing: 1, x: 540, y: 1650, scale: 200, expr: 'penasaran', look: [0.8, 0], headTilt: -6, armR: { a1: 10, a2: 6 } }) },
  { n: 40, light: 'dusk', cam: { x: 1350, y: 520, z: 2.2 }, bgBlur: 'b8', bg: () => Wd.room('dusk') + Wd.phoneProp(1600, 628, 1.6, 90, '#c6b2ff', true) + `<g transform="translate(1600 628)">${F.signalWaves(0, 0, 8, 40, 3, { glow: 0.9, sw: 2 })}</g>`,
    mid: () => M({ x: 1080, y: 860, scale: 82, expr: 'netral', look: [0.8, -0.1], faceX: 0.1 }) },
  { n: 41, light: 'night', cam: { x: 930, y: 560, z: 1.06 }, finish: { dark: 0.3, vignette: 1.6 }, bg: () => Wd.room('night', { lampOff: true, noPillow: true }),
    mid: () => { const { p } = V.leanBoard(MS, { lean: -16, headTilt: -10, expr: 'netral', look: [0.2, -1], armR: { a1: 20, a2: 60 } }); return M(p) + Wd.blanket('night', 470, 960) + Wd.phoneProp(1600, 628, 1.6, 90, '#c6b2ff', true) + `<g transform="translate(1600 628)">${F.signalWaves(0, 0, 10, 80, 4, { glow: 1, sw: 3 })}</g>`; } },
];

export const TESTS = {};
