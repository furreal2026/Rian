// EP004 episode timeline: shot timing, per-shot animation (camera move + character action) and transitions.
// frameAt(t) returns the inner SVG of the frame at time t (seconds). Uses the storyboard modules as the art source.
import { drawMilo, pose, POSES, drawHand } from '../EP04_storyboard_frames_TEST/rig/milo.mjs';
import { walk, groundLock, reach } from '../EP04_storyboard_frames_TEST/rig/anim.mjs';
import * as Wd from '../EP04_storyboard_frames_TEST/world.mjs';
import * as L from '../EP04_storyboard_frames_TEST/locations.mjs';
import * as F from '../EP04_storyboard_frames_TEST/fx.mjs';
import * as V from '../EP04_storyboard_frames_TEST/views.mjs';
import * as S from '../EP04_storyboard_frames_TEST/shots.mjs';
import { PLAN } from '../EP04_storyboard_frames_TEST/plan.mjs';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const { W, H, finish } = Wd;
const M = (pz) => drawMilo(pose(pz));
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
const easeIn = (t) => t * t * t;
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const span = (t, a, b) => clamp((t - a) / (b - a));
const backOut = (t) => { const c = 1.7; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
// 4 decimals: camera scale must change every frame (2 decimals made zooms step in visible jumps)
const n = (v) => +(+v).toFixed(4);

// ---------------------------------------------------------------- timing (storyboard docx + 6 s intro after shot 06)
const full = JSON.parse(readFileSync(join(here, '../EP04_storyboard_frames_TEST/shots_full.json'), 'utf-8'));
const sec = (t) => { const [m, x] = t.split(':').map(Number); return m * 60 + x; };
export const OLD_TIMELINE = S.SHOTS.map((s) => {
  let a; let b;
  if (s.intro) { a = 60; b = 66; }
  else if (s.tc) { [a, b] = s.tc.split('–').map(sec); }
  else { [a, b] = full.find((m) => m.shot === s.n).tc.split('–').map(sec); if (s.n > 6) { a += 6; b += 6; } }
  return { id: String(s.n), shot: s, start: a, end: b };
});


// ---------------------------------------------------------------- tight cut (owner 2026-11-26): VO at 1.1x, cut soon after the narration ends
// Each shot keeps its old local action time at RATE (so actions stay in step with the 1.1x VO) and ends HOLD old-seconds after
// its last VO line (+ half its outgoing transition). Shots whose VO runs on into the next shot keep their whole length.
// MIN_OLD: shots with a visual beat after the narration keep at least this much old local time.
export const RATE = 1.1;
const HOLD = 0.35;
const MIN_OLD = { '02B': 2.9, '06A': 3.0, '22': 6.2, '23': 6.8, '31': 8.4, '40': 7.2, '41': 4.6 };
// VO cues on the old timeline: the expressive VO (vo_expr/, build_vo_expr.py place) when present, else the Kokoro VO
import { existsSync } from 'node:fs';
const EXPR = join(here, 'vo_expr/cues_old.json');
export const CUES = existsSync(EXPR) ? JSON.parse(readFileSync(EXPR, 'utf-8')).cues : JSON.parse(readFileSync(join(here, '../EP04_vo_am_puck_TEST/cues.json'), 'utf-8'));
const transD = (id) => parseTrans(id).d;
export const TIMELINE = (() => {
  let tnew = 0;
  return OLD_TIMELINE.map((e) => {
    const T = e.end - e.start;
    const inside = CUES.filter((c) => c.start < e.end && c.end > e.start);
    const runsOn = inside.some((c) => c.end > e.end + 1e-6);
    const voEnd = inside.length ? Math.min(T, Math.max(...inside.map((c) => c.end - e.start))) : 0;
    const keepOld = runsOn ? T : Math.min(T, Math.max(MIN_OLD[e.id] || 1.2, voEnd + HOLD));
    const dur = keepOld / RATE + (runsOn ? 0 : transD(e.id) / 2);
    const out = { ...e, oldStart: e.start, oldEnd: e.end, start: tnew, end: tnew + dur };
    tnew += dur;
    return out;
  });
})();
export const DURATION = TIMELINE[TIMELINE.length - 1].end;
/** new time of an old-timeline moment (used to place the VO lines) */
export function mapOld(t) {
  const e = TIMELINE.find((x) => t >= x.oldStart && t < x.oldEnd) || TIMELINE[TIMELINE.length - 1];
  return e.start + (t - e.oldStart) / RATE;
}
let U_NOW = null; // camera progress of the current shot in new time (0..1), so every camera move finishes smoothly inside the shorter shot
// ---------------------------------------------------------------- generic camera moves (one main move per shot)
const MOVE = {
  '1': { z: [1, 1.14] }, '02A': { z: [1, 1.08] }, '4': { x: [50, -50] }, '7': { z: [1, 1.06] }, '8': { z: [1, 1.05] }, '9': { z: [1, 1.08] },
  '14': { z: [1, 1.07] }, '17': { z: [1.08, 1] }, '18': { x: [60, -60] }, '19': { z: [1, 1.08] }, '20': { x: [-50, 50] }, '25': { z: [1, 1.04] },
  '29': { z: [1, 1.07] }, '32': { z: [1, 1.05] }, '33': { x: [-40, 40] }, '34': { z: [1, 1.07] }, '36': { z: [1, 1.06] }, '38': { z: [1, 1.07] },
  '39': { x: [40, -40] }, '40': { z: [1, 1.06] }, '41': { z: [1.04, 0.97] }, '16': { y: [-40, 40] }, '30': { y: [20, -20] },
};
function camAt(s, u, extra = {}) {
  const m = { ...(MOVE[String(s.n)] || {}), ...extra };
  const k = ease(U_NOW ?? u);
  const c = { x: W / 2, y: H / 2, z: 1, r: 0, ...(s.cam || {}) };
  return { ...c, x: c.x + (m.x ? lerp(m.x[0], m.x[1], k) / c.z : 0), y: c.y + (m.y ? lerp(m.y[0], m.y[1], k) / c.z : 0), z: c.z * (m.z ? lerp(m.z[0], m.z[1], k) : 1), r: c.r + (m.r ? lerp(m.r[0], m.r[1], k) : 0) };
}
/** frame assembly: world under a camera, screen overlays under an optional screen move, then grade/paper/vignette */
function compose(s, { cam, screen = null, bg, mid, fg, over, fin } = {}) {
  const c = cam || camAt(s, 0);
  const camT = `translate(${W / 2} ${H / 2}) rotate(${n(c.r)}) scale(${n(c.z)}) translate(${n(-c.x)} ${n(-c.y)})`;
  const bf = s.bgBlur ? `filter="url(#${s.bgBlur})"` : '';
  const ff = s.fgBlur ? `filter="url(#${s.fgBlur})"` : '';
  const body = `<rect width="${W}" height="${H}" fill="#efe3cc"/><g transform="${camT}"><g ${bf}>${bg ?? (s.bg ? s.bg() : '')}</g>${mid ?? (s.mid ? s.mid() : '')}<g ${ff}>${fg ?? (s.fg ? s.fg() : '')}</g></g>${over ?? (s.over ? s.over() : '')}`;
  const scr = screen ? `<g transform="translate(${W / 2} ${H / 2}) scale(${n(screen.z || 1)}) rotate(${n(screen.r || 0)}) translate(${n(-W / 2 + (screen.x || 0))} ${n(-H / 2 + (screen.y || 0))})">${body}</g>` : body;
  return scr + finish(s.light || 'day', fin || s.finish || {});
}
const screenMove = (s, u) => { const m = MOVE[String(s.n)] || {}; const k = ease(U_NOW ?? u); return { z: m.z ? lerp(m.z[0], m.z[1], k) : 1, x: m.x ? lerp(m.x[0], m.x[1], k) : 0, y: m.y ? lerp(m.y[0], m.y[1], k) : 0 }; };
const pop = (svg, cx, cy, k) => (k <= 0 ? '' : `<g transform="translate(${cx} ${cy}) scale(${n(Math.max(0.01, backOut(clamp(k))))}) translate(${-cx} ${-cy})">${svg}</g>`);
const walkPose = (ph, extra = {}) => groundLock({ view: 'side', facing: 1, ...walk(ph % 1), ...extra });

// ---------------------------------------------------------------- per-shot animation (t = local seconds, T = duration)
const A = {};
const R = S.R;
const MS = S.MS;
// SEQUENCE 1
A['02B'] = (s, t, T) => {
  const flicks = [0.25, 0.95, 1.55, 2.2, 2.75, 3.4, 3.95];
  let sc = 0.05; let vel = 0; let ty = 760;
  for (const f of flicks) {
    const uu = clamp((t - f - 0.05) / 0.55); sc += 0.11 * easeOut(uu); if (uu > 0 && uu < 1) vel = Math.max(vel, 3 * Math.pow(1 - uu, 2));
    if (t >= f && t < f + 0.6) ty = 760 - 200 * easeOut(clamp((t - f) / 0.22)) + 200 * easeOut(clamp((t - f - 0.25) / 0.3));
  }
  return compose(s, { over: `<g transform="translate(${n(Math.sin(t * 1.3) * 4)} 0)">${drawHand('ball', { x: 905, y: 815, scale: 400, deg: 170, stub: 3 })}${V.phoneScreen({ scroll: sc, blur: vel > 0.6, deg: -4, k: 0.62, cy: 420 })}${V.swipe(1185, ty, { scale: 400, arcs: ty < 750 })}</g>` });
};
A['3'] = (s, t, T) => {
  const u = t / T;
  const z = 1 + 0.08 * easeOut(u);
  const flicker = (t > 3.0 && t < 3.12) || (t > 3.3 && t < 3.36) ? 0 : 0.6;
  return compose(s, { over: `<g transform="translate(960 560) scale(${n(z)}) translate(-960 -560)">${drawHand('ball', { x: 890, y: 805, scale: 400, deg: 175, stub: 3 })}${V.phoneScreen({ scroll: 0.82, glitch: 0.15 + 0.85 * easeOut(u), deg: 16, cx: 1000, cy: 430, k: 0.62 })}${drawHand('ball', { x: 1200, y: 700, scale: 400, deg: 205, stub: 3, flip: -1 })}${F.particles(1000, 560, 500, Math.round(10 + 40 * u), 8)}</g><circle cx="1560" cy="140" r="300" fill="url(#warmGlow)" opacity="${flicker}" style="mix-blend-mode:screen"/>` });
};
A['4'] = (s, t, T) => {
  const u = t / T;
  const p = { view: 'side', facing: 1, x: 560, y: 2350, scale: 380, expr: 'netral', look: [0.6, 0.4], headTilt: -4, armR: { a1: 40, a2: 120 }, armL: { hide: true } };
  const over = M(p) + F.earphones(p, [2.2, -1.0], { glow: true }) + `<g opacity="0.85">${F.signalWaves(1150, 760, 30, 60 + 260 * easeOut(u), 6, { arc: [-150, -30], glow: 0.3 + 0.5 * u })}</g>` + F.particles(1100, 700, 300, Math.round(10 + 30 * u), 4) + Wd.phoneProp(1500, 980, 6, -20, '#c6b2ff', true);
  return compose(s, { screen: screenMove(s, u), over });
};
A['5'] = (s, t, T) => {
  const u = t / T;
  const jolt = span(t, 1.2, 1.45); // snap startle (anticipation then pop)
  const fly = span(t, 1.3, 2.4);
  const calm = jolt === 0;
  const fm = calm ? V.footMilo({ phone: true, earphones: true, expr: 'calm', look: [0, 0.45] }) : V.footMilo({ expr: 'kaget', look: [0.2, -0.6], headTilt: -6 * jolt, armL: { a1: lerp(-14, -70, easeOut(jolt)), a2: lerp(-8, -120, easeOut(jolt)) }, armR: { a1: lerp(14, 75, easeOut(jolt)), a2: lerp(8, 125, easeOut(jolt)) } });
  const ph = calm ? '' : Wd.phoneProp(lerp(960, 1240, easeOut(fly)), lerp(520, 300, easeOut(fly)) - 120 * Math.sin(Math.PI * fly), 3.2, lerp(0, 400, fly), '#c6b2ff', true);
  const waves = F.signalWaves(calm ? 960 : 1240, calm ? 520 : 330, 80, 120 + 1400 * easeOut(u), 10, { glow: 0.5 + 0.5 * u, sw: 8 }) + F.particles(1000, 450, 900, Math.round(30 + 60 * u), 2);
  const cam = camAt(s, u, { r: [0, -2] });
  return compose(s, { cam, bg: V.bedFootView('night', { curtain: 40 + 100 * u }), mid: fm.svg + V.footBlanket('night', 20) + ph, over: waves });
};
A['6'] = (s, t, T) => {
  const u = t / T;
  const drop = easeIn(span(t, 0.6, 2.6));
  const mid = V.footMilo({ expr: drop > 0.4 ? 'tidur' : 'netral', headTilt: 26 * drop, faceX: -0.06 * drop, armL: { a1: -8, a2: 6 }, armR: { a1: 10, a2: -4 } }).svg + V.footBlanket('night') + Wd.phoneProp(1150, 990, 2.6, 70, t < 3 ? '#8f86c8' : '#3b3f46', t < 3);
  return compose(s, { cam: camAt(s, u, { z: [1.0, 0.94] }), mid, fin: { dark: 0.2 + 0.5 * easeIn(U_NOW ?? u), vignette: 1.5 } });
};
A['06A'] = (s, t, T) => {
  const logo = backOut(clamp(t / 0.4));
  const title = span(t, 0.5, 1.2);
  let card = F.introCard();
  // reveal the title with a growing clip, pop the logo in
  card = card.replace(/<image /, `<g transform="translate(960 348) scale(${n(Math.max(0.01, logo))}) translate(-960 -348)"><image `).replace(/height="456"\/>/, 'height="456"/></g>');
  const clipW = n(1920 * title);
  card = `<defs><clipPath id="titleClip"><rect x="0" y="600" width="${clipW}" height="300"/></clipPath></defs>` + card.replace(/<text x="960" y="680"/, `<g clip-path="url(#titleClip)"><text x="960" y="680"`).replace(/<\/path>$|stroke-linecap="round"\/>$/, (m) => `${m}</g>`);
  const flash = '';
  return compose(s, { over: `<g transform="translate(960 540) scale(${n(1 + 0.03 * (t / T))}) translate(-960 -540)">${card}</g>${flash}` });
};
// SEQUENCE 2
A['7'] = (s, t, T) => {
  const up = easeOut(span(t, 0.2, 1.4));
  const { p } = V.leanBoard(MS, { lean: lerp(-16, -2, up), headTilt: 6, expr: t < 1.6 ? 'tidur' : 'ngantuk' });
  const q = t > 2.0 ? F.rubHead(p, 'R') : p;
  return compose(s, { cam: camAt(s, t / T), mid: M(q) + Wd.blanket('morning', 470, 960) + Wd.phoneProp(1600, 628, 1.6, 90, S.dimPhone) });
};
A['9'] = (s, t, T) => compose(s, { cam: camAt(s, t / T), mid: S.neighbour(), over: S.windowOverlay('morning', 980, 140, 820, 760) + pop(F.bubble(1440, 330, 120, ['plantWilt', 'hose'], { tail: [1330, 520] }), 1440, 330, span(t, 0.4, 0.75)) + M({ view: 'side', facing: 1, x: 560, y: 1820, scale: 270, expr: t < 0.5 ? 'netral' : 'penasaran', look: [0.7, -0.1], headTilt: -4, armR: { a1: 10, a2: 6 } }) });
A['10'] = (s, t, T) => {
  const on = (t > 1.6 && t < 2.6) || (t > 3.4 && t < 4.4);
  const p = on ? F.handsOnHead({ x: 960, y: 760, scale: 92, expr: 'kaget' }) : { x: 960, y: 760, scale: 92, expr: t > 4.4 ? 'bingung' : 'kaget' };
  const lines = on ? [0, 1, 2].map((k) => `<path d="M${560 - k * 60} ${320 - k * 40} Q${500 - k * 60} 440 ${560 - k * 60} ${560 + k * 40}" fill="none" stroke="#2b241e" stroke-width="4" opacity="${0.5 - k * 0.12}"/><path d="M${1360 + k * 60} ${320 - k * 40} Q${1420 + k * 60} 440 ${1360 + k * 60} ${560 + k * 40}" fill="none" stroke="#2b241e" stroke-width="4" opacity="${0.5 - k * 0.12}"/>`).join('') : '';
  return compose(s, { cam: camAt(s, t / T, { z: [1, 1.04] }), mid: M(p), over: lines });
};
A['11'] = (s, t, T) => {
  const a = 128 + 14 * Math.sin(t * 2 * Math.PI * 1.6);
  const nb = Wd.extra({ view: 'front', x: 1430, y: 848, scale: 58, armL: { a1: -a, a2: -a - 44, hand: 'ball' } }, { top: '#9fae84', bottom: '#6a5a50', acc: ['hat', 'apron'] });
  return compose(s, { cam: camAt(s, t / T, { x: [-30, 30] }), mid: nb + pop(F.bubble(1600, 430, 95, ['list', 'fern'], { tail: [1450, 560] }), 1600, 430, span(t, 1.0, 1.35)) });
};
// SEQUENCE 3
A['12'] = (s, t, T) => {
  const x = 1150 + 32 * t;
  const cam = { ...s.cam, x: 1350 + (x - 1300) * 0.85 };
  return compose(s, { cam, mid: M(walkPose(t * 1.05, { x, y: 852, scale: 50 })) + Wd.extra({ ...walkPose(t * 1.05 + 0.4), facing: -1, x: 2250 - 30 * t, y: 850, scale: 48 }, { top: '#b9867a', bottom: '#5b6070', acc: ['bag'], blur: 'b1' }) });
};
A['13'] = (s, t, T) => {
  const x = 1880 + 22 * t;
  const mid = Wd.extra({ view: 'side', facing: -1, x: 2300 - 18 * t, y: 852, scale: 50, armR: { a1: 8, a2: 24 } }, { top: '#c8a97a', bottom: '#4f5566', acc: ['tote'], bread: true, blur: 'b1' }) +
    Wd.extra({ ...walkPose(t * 1.05 + 0.3), x: 1660 + 20 * t, y: 850, scale: 48 }, { top: '#7d93ad', bottom: '#44505e', acc: ['cap'], blur: 'b2' }) + Wd.extra({ x: 2480, y: 848, scale: 47 }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['phone'], blur: 'b2' }) +
    M(walkPose(t * 1.05, { x, y: 856, scale: 52, expr: 'penasaran', look: [0.6, 0] })) +
    pop(F.bubble(2300 - 18 * t, 520, 52, ['bread']), 2300 - 18 * t, 520, span(t, 1.0, 1.3)) + pop(F.bubble(1680 + 20 * t, 540, 46, ['key']), 1680 + 20 * t, 540, span(t, 3.0, 3.3)) + pop(F.bubble(2490, 530, 46, ['lunch']), 2490, 530, span(t, 5.0, 5.3));
  return compose(s, { cam: { ...s.cam, x: 2020 + 15 * t }, mid });
};
A['15'] = (s, t, T) => compose(s, { cam: camAt(s, 0, { z: [1, 1] }) && { ...s.cam, z: s.cam.z * (1 + 0.06 * easeOut(span(t, 0, 0.35))) }, over: pop(F.bubble(1560, 270, 150, ['question', 'stain'], { tail: [1820, 470] }), 1560, 270, span(t, 0.6, 0.9)) });
A['16'] = (s, t, T) => {
  const sw = Math.floor(t / 1.4) % 2;
  let p = { x: 1930, y: 856, scale: 54, expr: 'bingung', look: [0, 1], headTilt: 10 };
  p = sw ? reach(reach(p, 'R', [-0.28, -2.75], 1), 'L', [0.15, -2.35], -1) : reach(reach(p, 'L', [0.28, -2.75], -1), 'R', [-0.15, -2.35], 1);
  return compose(s, { cam: camAt(s, t / T), mid: M({ ...p, armR: { ...p.armR, z: 'front' }, armL: { ...p.armL, z: 'front' } }) });
};
A['17'] = (s, t, T) => compose(s, { screen: screenMove(s, t / T) });
A['21'] = (s, t, T) => compose(s, { cam: { ...s.cam, y: s.cam.y + lerp(40, -30, ease(t / T)) }, mid: S.plazaCrowd() + M(walkPose(t * 1.05, { x: 1340 + 26 * t, y: 892, scale: 50 })) });
A['22'] = (s, t, T) => {
  const x = 1600 + 24 * t;
  const j = Math.sin(t * 7) * 3;
  const mid = S.plazaCrowd() + M(walkPose(t * 1.05, { x, y: 896, scale: 52, expr: 'penasaran', look: [0.5, -0.3] })) + pop(F.bubble(1460, 560, 46, ['plate']), 1460, 560, span(t, 1.5, 1.8)) + pop(F.bubble(1840, 540, 46, ['music']), 1840, 540, span(t, 3.5, 3.8)) + pop(F.bubble(1980, 600, 40, ['phone'], { op: 0.8 }), 1980, 600, span(t, 6.0, 6.3));
  return compose(s, { cam: { ...s.cam, x: 1650 + 22 * t, y: s.cam.y + j }, mid });
};
A['23'] = (s, t, T) => {
  const bs = [[620, 300, ['lock']], [800, 170, ['plate']], [1150, 160, ['phone']], [1330, 300, ['music']], [560, 520, ['list']], [1380, 560, ['briefcase']], [960, 120, ['clock']], [760, 700, ['bread']], [1200, 720, ['cash']], [420, 220, ['tab']], [1520, 200, ['book']]];
  let mid = bs.map(([x, y, i], k) => pop(F.bubble(x, y, 56 + (k % 3) * 10, i, { op: 0.92 - (k % 3) * 0.1 }), x, y, span(t, 0.3 + k * 0.7, 0.6 + k * 0.7))).join('');
  const w = [[560, 110, 'Did I lock the door?', 0, 0.9], [1180, 90, "What's for dinner?", 5, 2.4], [420, 640, 'call Mom…', -4, 3.9], [1330, 690, '♪ that song…', 4, 5.4]];
  mid += w.map(([x, y, txt, rot, at]) => (t > at ? F.words(x, y, txt, 34, { rot }) : '')).join('');
  return compose(s, { cam: camAt(s, t / T, { z: [1, 1.1] }), mid });
};
A['24'] = (s, t, T) => {
  const r = Wd.rng(7);
  let o = '';
  const k = Math.round(6 + 22 * (t / T));
  for (let i = 0; i < 28; i++) { const ic = ['tab', 'music', 'plate', 'lock', 'phone', 'clock', 'list', 'cash', 'bread', 'briefcase', 'book'][i % 11]; const x = 120 + r() * 1680; const y = 90 + r() * 760; const rr = 50 + r() * 50; const op = 0.55 + r() * 0.4; if (i < k) o += pop(F.bubble(x + Math.sin(t * 2 + i) * 10, y, rr, [ic], { op }), x, y, clamp((t / T * 22 + 6 - i) / 1.2)); }
  return compose(s, { cam: { ...s.cam, r: 2 * Math.sin(t * 1.4), z: s.cam.z * (1 + 0.05 * easeIn(t / T)) }, over: o + F.words(300, 980, 'tab 47', 34, { op: 0.6 }) });
};
A['26'] = (s, t, T) => {
  const stop = t > 4.4; // hands on head right after the line (tight cut)
  const fade = stop ? 0.1 : 0.35;
  const pre = Math.min(t, 4.4) / 4.4;
  const mid = F.bubble(1450 + Math.sin(t * 3) * 30, 470, 55, ['tab'], { op: fade }) + F.bubble(1860 - Math.sin(t * 3) * 30, 450, 55, ['music'], { op: fade }) + M(stop ? F.handsOnHead({ x: 1650, y: 896, scale: 56, expr: 'takut' }) : { x: 1650, y: 896, scale: 56, expr: 'takut' });
  return compose(s, { cam: { ...s.cam, x: s.cam.x + (stop ? 30 : lerp(-40, 30, pre)) }, mid, over: stop ? '' : F.bubble(250 + 60 * t, 320, 130, ['clock'], { op: 0.3, blur: 'b5' }) + F.bubble(1680 - 50 * t, 820, 140, ['lock'], { op: 0.3, blur: 'b5' }) });
};
A['27'] = (s, t, T) => compose(s, { cam: { ...s.cam, x: 2780 + 18 * t, z: s.cam.z * lerp(1, 0.94, t / T) }, mid: `<g filter="url(#b2)">${L.crowd('mid', { seed: 12, x0: 1600, x1: 2550 })}</g>` + M(walkPose(t * 0.8, { x: 2860 + 20 * t, y: 892, scale: 54, expr: 'netral', headTilt: 14, look: [0.3, 0.8] })) });
// SEQUENCE 5
A['28'] = (s, t, T) => compose(s, { cam: camAt(s, t / T, { z: [1, 1.06] }), mid: M(walkPose(t * 1.0, { x: 420 + 38 * t, y: 905, scale: 52, expr: 'penasaran', look: [0.6, 0] })) + L.cat(1380, 1080, 2.6, 'sit', -1) });
A['30'] = (s, t, T) => {
  const i = Math.floor(t / 0.8) % 3;
  const pairs = [['bowl', 'fish'], ['cushion', 'bowl'], ['door', 'fish']];
  return compose(s, { cam: camAt(s, t / T), over: F.bubble(1180, 230, 150, pairs[i]) + F.bubble(1580, 420, 110, pairs[(i + 1) % 3], { op: 0.9 }) });
};
A['31'] = (s, t, T) => {
  const down = easeOut(span(t, 6.0, 9.0));
  const target = [lerp(1.45, 0.9, down), lerp(-1.85, -1.1, down)];
  return compose(s, { cam: camAt(s, t / T, { z: [1, 0.96] }), mid: M(F.squat({ x: 820, y: 912, scale: 66, expr: 'netral', look: [0.7, 0] }, target)) + L.cat(1300 + 70 * t, 912, 1.2, t < 0.6 ? 'sit' : 'walk', 1) });
};
// SEQUENCE 6
A['35'] = (s, t, T) => {
  const fall = easeIn(span(t, 0.8, 1.4));
  const dy = -160 * (1 - fall);
  const items = Wd.wc([[1700, 1010, '#e09a4a'], [1760, 1030, '#e09a4a'], [1640, 1040, '#d9883e']].map(([x, y, c], k) => Wd.ell(x + k * 6 * (1 - fall), y + dy, 16, 15, c)).join('') + Wd.rect(1560, 1000 + dy, 70, 46, '#6f8fa8', { rx: 4 }) + Wd.rect(1800, 1040 + dy, 80, 18, '#c98f5c'));
  const mx = 1380 + (t > 1.6 ? 90 * easeOut(span(t, 1.6, 3.5)) : 0);
  const mid = Wd.extra({ view: 'side', facing: -1, x: 1880, y: 985, scale: 54, headTilt: 18, armR: { a1: -40, a2: -60 }, armL: { a1: -30, a2: -50 } }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['glasses'] }) + M(walkPose(t * 1.2, { x: mx, y: 990, scale: 58, expr: 'penasaran', look: [0.7, 0.4] }));
  return compose(s, { cam: { ...s.cam, x: s.cam.x + lerp(-40, 30, ease(t / T)) }, mid, fg: items });
};
A['36'] = (s, t, T) => {
  const k = easeOut(span(t, 1.0, 3.0));
  const book = [lerp(1640, 1745, k), lerp(985, 862, k)];
  const target = [lerp(0.8, 1.65, k), lerp(-0.3, -2.1, k)];
  return compose(s, { cam: camAt(s, t / T), mid: Wd.extra({ view: 'side', facing: -1, x: 1860, y: 985, scale: 54, headTilt: t > 3.4 ? 14 + 6 * Math.sin((t - 3.4) * 6) : 0, armR: { a1: -60, a2: -90 } }, { top: '#9a86a8', bottom: '#5f5a68', acc: ['glasses'] }) + M(F.squat({ x: 1600, y: 992, scale: 58, expr: t > 3 ? 'senang' : 'netral' }, target)) + Wd.wc(Wd.rect(book[0], book[1], 70, 46, '#6f8fa8', { rx: 4 })) });
};
// SEQUENCE 7
A['37'] = (s, t, T) => compose(s, { bg: V.street3d('dusk', { people: [{ z: 7 + 0.35 * t, svg: () => M({ ...V.placeAt(4.3, 7 + 0.35 * t), ...V.walkAway(t * 6) }) }] }) });
A['40'] = (s, t, T) => {
  const on = Math.floor(t * 2.2) % 3 !== 0 && t > 6;
  const bg = Wd.room('dusk') + Wd.phoneProp(1600, 628, 1.6, 90, on ? '#c6b2ff' : '#3b3f46', on) + (on ? `<g transform="translate(1600 628)">${F.signalWaves(0, 0, 8, 40, 3, { glow: 0.9, sw: 2 })}</g>` : '');
  return compose(s, { cam: camAt(s, t / T), bg });
};
A['41'] = (s, t, T) => compose(s, { cam: camAt(s, t / T), fin: { dark: 0.2 + 0.6 * easeIn(U_NOW ?? t / T), vignette: 1.6 } });

function shotFrame(entry, t) {
  const s = entry.shot;
  const T = entry.oldEnd - entry.oldStart;               // old length: the per-shot action code is written in old local seconds
  const tn = clamp(t - entry.start, 0, entry.end - entry.start);
  const lt = clamp(tn * RATE, 0, T);
  U_NOW = tn / (entry.end - entry.start);
  const f = A[entry.id];
  let out;
  if (f) out = f(s, lt, T);
  else out = s.cam ? compose(s, { cam: camAt(s, lt / T) }) : compose(s, { screen: screenMove(s, lt / T) });
  U_NOW = null;
  return out;
}

// ---------------------------------------------------------------- transitions (from plan.mjs, around each cut)
function parseTrans(id) {
  const out = (PLAN[id]?.out || 'CUT').toUpperCase();
  const d = +(out.match(/\(([\d.]+) S\)/)?.[1] || 0);
  let type = 'cut';
  if (/WHIP/.test(out)) type = 'whip';
  else if (/PUSH-THROUGH|SNAP ZOOM|CRASH ZOOM \(|CRASH ZOOM KE|RACK FOCUS|CRANE UP/.test(out)) type = 'zoom';
  else if (/CRASH ZOOM OUT/.test(out)) type = 'zoomout';
  else if (/SMASH CUT/.test(out)) type = /SUNYI/.test(out) ? 'cut' : /HITAM/.test(out) ? 'black' : 'smash';
  else if (/LEAF WIPE|OBJECT WIPE/.test(out)) type = /LEAF/.test(out) ? 'leaf' : 'object';
  else if (/TILT DOWN/.test(out)) type = 'tilt';
  return { type, d: type === 'cut' ? 0 : type === 'black' ? 0.5 : Math.max(d || 0.3, 0.2) };
}
const blurX = (px) => `<filter id="mbX${px}" x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur stdDeviation="${px} 0"/></filter>`;
const blurY = (px) => `<filter id="mbY${px}" x="-5%" y="-20%" width="110%" height="140%"><feGaussianBlur stdDeviation="0 ${px}"/></filter>`;
const blurR = (px) => `<filter id="mbR${px}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${px}"/></filter>`;

export function frameAt(t) {
  const i = TIMELINE.findIndex((e) => t >= e.start && t < e.end);
  const k = i < 0 ? TIMELINE.length - 1 : i;
  const cur = TIMELINE[k];
  // transition window: last d/2 of the outgoing shot and first d/2 of the incoming one
  const prev = TIMELINE[k - 1];
  const next = TIMELINE[k + 1];
  let a = null; let b = null; let p = 0; let type = 'cut';
  if (next) { const tr = parseTrans(cur.id); if (tr.d && t > cur.end - tr.d / 2) { a = cur; b = next; p = (t - (cur.end - tr.d / 2)) / tr.d; type = tr.type; } }
  if (!a && prev) { const tr = parseTrans(prev.id); if (tr.d && t < cur.start + tr.d / 2) { a = prev; b = cur; p = (t - (cur.start - tr.d / 2)) / tr.d; type = tr.type; } }
  if (!a) return shotFrame(cur, t);
  const FA = shotFrame(a, Math.min(t, a.end - 1e-3));
  const FB = shotFrame(b, Math.max(t, b.start));
  const q = clamp(p);
  const showA = q < 0.5;
  const amt = showA ? q * 2 : (1 - q) * 2; // 0 at the edges, 1 at the cut
  switch (type) {
    case 'whip': { const px = Math.round(10 + 70 * amt); const dir = showA ? -1 : 1; const off = showA ? -q * 2 * 900 : (1 - q) * 2 * 900; return `<defs>${blurX(px)}</defs><g filter="url(#mbX${px})" transform="translate(${n(showA ? off : off * dir * -1)} 0)">${showA ? FA : FB}</g>`; }
    case 'zoom': { const px = Math.round(2 + 22 * amt); const z = showA ? 1 + 0.9 * easeIn(q * 2) : 1 + 0.35 * (1 - easeOut((q - 0.5) * 2)); return `<defs>${blurR(px)}</defs><g filter="url(#mbR${px})" transform="translate(960 540) scale(${n(z)}) translate(-960 -540)">${showA ? FA : FB}</g>`; }
    case 'zoomout': { const px = Math.round(2 + 18 * amt); const z = showA ? 1 - 0.35 * easeIn(q * 2) : 1.25 - 0.25 * easeOut((q - 0.5) * 2); return `<defs>${blurR(px)}</defs><g filter="url(#mbR${px})" transform="translate(960 540) scale(${n(z)}) translate(-960 -540)">${showA ? FA : FB}</g>`; }
    case 'tilt': { const px = Math.round(8 + 50 * amt); const off = showA ? -q * 2 * 700 : (1 - q) * 2 * 700; return `<defs>${blurY(px)}</defs><g filter="url(#mbY${px})" transform="translate(0 ${n(off)})">${showA ? FA : FB}</g>`; }
    case 'smash': return showA ? FA + (q > 0.35 ? `<rect width="${W}" height="${H}" fill="#fbf6ec" opacity="${n((q - 0.35) / 0.15)}"/>` : '') : FB + `<rect width="${W}" height="${H}" fill="#fbf6ec" opacity="${n(clamp(1 - (q - 0.5) / 0.25))}"/>`;
    case 'black': return showA ? FA + `<rect width="${W}" height="${H}" fill="#05050a" opacity="${n(clamp(q * 3))}"/>` : FB + `<rect width="${W}" height="${H}" fill="#05050a" opacity="${n(clamp((1 - q) * 2))}"/>`;
    case 'leaf': case 'object': {
      const x = lerp(-900, 2800, q);
      const shape = type === 'leaf'
        ? `<g transform="translate(${n(x)} 540) rotate(${n(-30 + 60 * q)})"><ellipse cx="0" cy="0" rx="1100" ry="640" fill="#6f8f58"/><ellipse cx="0" cy="0" rx="1100" ry="640" fill="none" stroke="#2b241e" stroke-width="10" opacity="0.7"/><path d="M-1050 0 Q0 -60 1050 0" stroke="#4d6a3c" stroke-width="22" fill="none"/></g>`
        : `<g transform="translate(${n(x)} 0)"><ellipse cx="0" cy="560" rx="760" ry="900" fill="#7d93ad"/><circle cx="0" cy="-120" r="520" fill="#f3ead8"/></g>`;
      const cover = `<g filter="url(#b8)">${shape}</g>`;
      return `${showA ? FA : FB}${cover}`;
    }
    default: return showA ? FA : FB;
  }
}
