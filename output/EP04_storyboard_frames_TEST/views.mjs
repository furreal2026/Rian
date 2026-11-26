// Extra camera angles for EP004 (owner request 2026-11-26: varied 3D/2D angles, strong transitions, no lying flat):
//   bedFootView  - E01 seen from the foot of the bed: Milo sits with his back against the wooden headboard
//   phoneScreen  - the phone filling the frame, feed scrolling (motion streaks, thumb swipe)
//   streetPerspective - E03 in one-point perspective (rear tracking / locked-off wide)
//   crowdTop     - E05 from straight above (bird's-eye), heads and shoulders, thought bubbles rising
import { drawMilo, miloParts, pose, drawHand, STYLE } from './rig/milo.mjs';
import { reach, reachDown } from './rig/anim.mjs';
import { poly, rect, ell, pth, ln, wc, tree, pot, rng, LIGHT, INK, W, H, extra } from './world.mjs';
import { motorbike } from './locations.mjs';

const n = (v) => +(+v).toFixed(2);
export const M = (pz) => drawMilo(pose(pz));

// ---------------------------------------------------------------- Milo against the headboard (side view, E01 master)
/** sitting on the mattress, back resting on the wooden headboard (E01 master: board at x 270..316) */
export function leanBoard(scale = 70, o = {}) {
  const lean = o.lean ?? -16;
  let p = { view: 'side', facing: 1, x: 0, y: 688, scale, hip: [0, 1.56], lean, headTilt: o.headTilt ?? 10, expr: o.expr || 'calm', look: o.look || [0.5, 0.2],
    legR: { a1: 88, a2: 90, foot: -88 }, legL: { a1: 86, a2: 89, foot: -88 }, armR: o.armR || { a1: 40, a2: 80 }, armL: o.armL || { a1: 30, a2: 70, z: 'back' } };
  // place him so the back of the torso (at shoulder height) touches the board's front face
  const { joints } = miloParts(pose(p));
  const backAtShoulder = joints.shL[0] - 0.36; // torso half-depth behind the shoulder line
  p.x = 316 + 6 - backAtShoulder * scale;
  if (o.phone) {
    const hc = miloParts(pose(p)).joints.headC;
    const t = o.phoneAt || [hc[0] + 1.3, hc[1] + 0.9];
    p = reach(p, 'R', t, -1);
    p = reach(p, 'L', [t[0] - 0.02, t[1] + 0.12], -1);
    p.armL = { ...p.armL, z: 'back' };
    return { p, phone: t };
  }
  return { p };
}

// ---------------------------------------------------------------- E01 from the foot of the bed
export function bedFootView(light = 'night', o = {}) {
  const L = LIGHT[light];
  const night = light === 'night';
  let s = rect(-200, -200, 2320, 1500, L.wall2, { stroke: false });
  // back wall with the window on the right (the same window as the wide master), corner at x 1480
  s += poly([[1480, -200], [2200, -200], [2200, 1300], [1480, 1300]], L.wall, { stroke: false }) + ln(1480, -200, 1480, 1300, { so: 0.35 });
  const sk = night ? ['#1b2442', '#34446c'] : light === 'dusk' ? ['#4f4f7e', '#e9a477'] : ['#a9cbe2', '#f2e2c0'];
  s += `<defs><linearGradient id="fvSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${sk[0]}"/><stop offset="100%" stop-color="${sk[1]}"/></linearGradient></defs>`;
  s += poly([[1600, 180], [1920, 150], [1920, 640], [1600, 600]], 'url(#fvSky)');
  if (night) s += `<circle cx="1780" cy="260" r="24" fill="#f4ecd0"/>`;
  s += poly([[1600, 180], [1920, 150], [1920, 640], [1600, 600]], 'none', { sw: 16, stroke: '#e9e0cf', so: 1 }) + ln(1760, 166, 1760, 620, { sw: 10, stroke: '#e9e0cf', so: 1 });
  const cur = night ? '#5c6b90' : '#8aa0c4';
  const sway = o.curtain || 0;
  s += pth(`M1540 120 L1650 110 Q${1620 + sway} 400 ${1680 + sway * 1.5} 700 L1530 710 Z`, cur);
  // wardrobe on the left wall, in perspective
  s += poly([[-40, 220], [250, 270], [250, 880], [-40, 960]], '#a98261') + ln(110, 250, 110, 920, { sw: 2 }) + ell(95, 560, 6, 6, INK, { stroke: false });
  // floor
  s += poly([[-200, 900], [2200, 860], [2200, 1300], [-200, 1300]], L.floor, { stroke: false });
  // headboard (wide wooden board, centre), mattress in perspective toward the camera
  s += pth(`M540 820 L540 420 Q960 330 1380 420 L1380 820 Z`, '#8e6a4c') + pth(`M580 800 L580 450 Q960 375 1340 450 L1340 800`, 'none', { so: 0.3 });
  for (let k = 0; k < 5; k++) s += ln(620 + k * 170, 445 - (k === 2 ? 16 : 8), 620 + k * 170, 800, { so: 0.18 });
  s += poly([[560, 790], [1360, 790], [1700, 1300], [220, 1300]], '#f0e8d8');
  s += poly([[560, 790], [1360, 790], [1380, 830], [540, 830]], '#ded3bf', { so: 0.4 });
  // pillow lying flat at the side (his back rests on the wood, not on the pillow)
  s += ell(700, 820, 120, 34, '#f6f1e6');
  if (night) s += poly([[1480, 640], [1600, 600], [1700, 1300], [1300, 1300]], '#7b8fc4', { stroke: false, op: 0.12 });
  else s += poly([[1480, 640], [1600, 600], [1800, 1300], [1250, 1300]], L.sun || '#fff', { stroke: false, op: 0.25 });
  return wc(s);
}
/** blanket over Milo's legs, from the hips toward the camera (front view, foot of the bed) */
export function footBlanket(light = 'night', mound = 0) {
  const c = night(light) ? '#5d6f98' : '#7f98c2';
  return wc(pth(`M640 ${880 - mound} Q960 ${820 - mound} 1280 ${880 - mound} L1660 1320 L260 1320 Z`, c) + pth(`M760 ${960 - mound} Q900 ${1010 - mound} 1040 ${980 - mound} M1100 ${1080} Q1250 ${1040} 1380 ${1100}`, 'none', { so: 0.35 }) + ell(830, 1000 - mound, 120, 50, c, { so: 0.3 }) + ell(1090, 1000 - mound, 120, 50, c, { so: 0.3 }));
}
const night = (l) => l === 'night';
/** Milo against the headboard, front view: legs under the blanket, phone held up in both hands */
export function footMilo(o = {}) {
  const scale = o.scale || 120;
  const hipY = 820; // where his seat meets the mattress, just in front of the board
  let p = { x: o.x ?? 960, y: hipY + 1.8 * scale, scale, expr: o.expr || 'calm', look: o.look || [0, 0.35], headTilt: o.headTilt || 0, faceX: o.faceX || 0,
    legL: { hide: true }, legR: { hide: true }, shadow: false, armL: o.armL || { a1: -14, a2: -8 }, armR: o.armR || { a1: 14, a2: 8 } };
  let phoneAt = null;
  if (o.phone) {
    phoneAt = o.phoneAt || [0, -3.05];
    p = reachDown(p, 'R', [phoneAt[0] + 0.16, phoneAt[1] + 0.12], 16);
    p = reachDown(p, 'L', [phoneAt[0] - 0.16, phoneAt[1] + 0.12], -16);
    p.armR = { ...p.armR, z: 'front' };
    p.armL = { ...p.armL, z: 'front' };
  }
  if (o.pose) p = o.pose(p);
  let s = drawMilo(pose(p));
  const tf = (inner) => `<g transform="translate(${n(p.x)} ${n(p.y)}) scale(${scale})">${inner}</g>`;
  const head = miloParts(pose(p)).joints.headC;
  if (o.earphones) {
    // two white cables from the sides of the head down to the phone
    const to = phoneAt || [0, -2.6];
    const c = (sx) => `M${head[0] + sx * 0.98} ${head[1] + 0.25} Q${head[0] + sx * 0.9} ${head[1] + 1.4} ${to[0] + sx * 0.05} ${to[1] + 0.3}`;
    s += tf(`<path d="${c(-1)}" fill="none" stroke="#f3efe4" stroke-width="0.06"/><path d="${c(1)}" fill="none" stroke="#f3efe4" stroke-width="0.06"/><ellipse cx="${head[0] - 0.98}" cy="${head[1] + 0.25}" rx="0.12" ry="0.15" fill="#f3efe4" stroke="${INK}" stroke-width="0.035"/><ellipse cx="${head[0] + 0.98}" cy="${head[1] + 0.25}" rx="0.12" ry="0.15" fill="#f3efe4" stroke="${INK}" stroke-width="0.035"/>`);
  }
  if (phoneAt) {
    const scr = o.screen || '#a9c8e6';
    s += tf(`<g transform="translate(${phoneAt[0]} ${phoneAt[1]}) rotate(${o.phoneDeg || 0})"><rect x="-0.3" y="-0.48" width="0.6" height="0.96" rx="0.08" fill="#2f333a" stroke="${INK}" stroke-width="0.04"/><circle cx="0.16" cy="-0.36" r="0.05" fill="#5a5f66"/></g>`);
    if (o.glow !== false) s += tf(`<ellipse cx="${head[0]}" cy="${head[1] + 0.25}" rx="1.1" ry="0.9" fill="${o.glowCol || '#bfe0ff'}" opacity="0.28" style="mix-blend-mode:screen"/><circle cx="${phoneAt[0]}" cy="${phoneAt[1] - 0.6}" r="1.4" fill="url(#screenGlow)" opacity="0.45" style="mix-blend-mode:screen"/>`);
  }
  return { svg: s, p, head, phoneAt };
}

// ---------------------------------------------------------------- the phone screen filling the frame
/** scroll: 0..1 feed offset; blur: motion streaks while scrolling; glitch: 0..1 signal corruption */
export function phoneScreen(o = {}) {
  const scroll = o.scroll ?? 0.35;
  const glitch = o.glitch ?? 0;
  const cx = o.cx ?? 960;
  const cy = o.cy ?? 560;
  const deg = o.deg ?? -6;
  const sw = 560;
  const shh = 980;
  const cards = ['#8fb0c8', '#d6a35e', '#9fbf8a', '#c98f6f', '#a99ac9', '#e0b04e', '#7fa7a2', '#c9a37a'];
  let feed = '';
  const step = 250;
  const off = -((scroll * step * 8) % (step * 8));
  for (let k = -1; k < 12; k++) {
    const y = -shh / 2 + 20 + k * step + off;
    const c = cards[((k % 8) + 8) % 8];
    feed += `<rect x="${-sw / 2 + 26}" y="${y}" width="${sw - 52}" height="180" rx="16" fill="${c}"/>`;
    feed += k % 3 === 1 ? catThumb(-sw / 2 + 26, y, sw - 52, 180) : `<polygon points="${-24},${y + 62} ${30},${y + 90} ${-24},${y + 118}" fill="#fbf6ec" opacity="0.85"/>`;
    feed += `<circle cx="${-sw / 2 + 50}" cy="${y + 206}" r="14" fill="#e9e2d0"/><rect x="${-sw / 2 + 76}" y="${y + 198}" width="${180 + (k % 4) * 30}" height="14" rx="7" fill="#e9e2d0" opacity="0.8"/>`;
  }
  const streak = o.blur ? `<g opacity="0.55">${[0, 1, 2, 3, 4, 5, 6].map((k) => `<rect x="${-sw / 2 + 40 + k * 70}" y="${-shh / 2}" width="${8 + (k % 3) * 6}" height="${shh}" fill="#fbf6ec" opacity="${0.15 + (k % 2) * 0.1}"/>`).join('')}</g>` : '';
  let gl = '';
  if (glitch > 0) {
    const r = rng(9);
    for (let k = 0; k < 16 * glitch; k++) gl += `<rect x="${-sw / 2}" y="${-shh / 2 + r() * shh}" width="${sw}" height="${6 + r() * 26}" fill="${r() > 0.5 ? '#c6b2ff' : '#9fd0ff'}" opacity="${0.4 + r() * 0.5}" transform="translate(${(r() - 0.5) * 60 * glitch} 0)"/>`;
    gl += `<circle cx="0" cy="0" r="${200 * glitch}" fill="url(#sigGlow)" opacity="${0.9 * glitch}" style="mix-blend-mode:screen"/>`;
  }
  const clip = `<clipPath id="scrClip"><rect x="${-sw / 2}" y="${-shh / 2}" width="${sw}" height="${shh}" rx="26"/></clipPath>`;
  const k = o.k ?? 1;
  let s = `<defs>${clip}</defs><g transform="translate(${cx} ${cy}) rotate(${deg}) scale(${k})">`;
  s += `<rect x="${-sw / 2 - 34}" y="${-shh / 2 - 60}" width="${sw + 68}" height="${shh + 120}" rx="70" fill="#2f333a" stroke="${INK}" stroke-width="8"/>`;
  s += `<g clip-path="url(#scrClip)"><rect x="${-sw / 2}" y="${-shh / 2}" width="${sw}" height="${shh}" fill="#1d2233"/>${feed}${streak}${gl}</g>`;
  s += `<rect x="-60" y="${-shh / 2 - 40}" width="120" height="16" rx="8" fill="#1d2233"/>`;
  // scroll bar
  s += `<rect x="${sw / 2 - 14}" y="${-shh / 2 + 30 + scroll * (shh - 220)}" width="7" height="150" rx="4" fill="#fbf6ec" opacity="0.6"/>`;
  s += `</g>`;
  return s;
}
function catThumb(x, y, w, h) {
  const cx = x + w / 2;
  const cy = y + h / 2 + 20;
  return `<ellipse cx="${cx}" cy="${cy + 20}" rx="70" ry="40" fill="#d39a5c"/><circle cx="${cx + 50}" cy="${cy - 20}" r="34" fill="#d39a5c"/><polygon points="${cx + 26},${cy - 44} ${cx + 32},${cy - 76} ${cx + 48},${cy - 50}" fill="#d39a5c"/><polygon points="${cx + 56},${cy - 52} ${cx + 74},${cy - 78} ${cx + 78},${cy - 42}" fill="#d39a5c"/>`;
}
/** Milo's round thumb-hand swiping up across the screen, with motion arcs */
export function swipe(x, y, o = {}) {
  const a = (o.scale || 150) / 150;
  const arcs = o.arcs !== false ? [0, 1, 2].map((k) => `<path d="M${x + 40 * a} ${y + (60 + k * 26) * a} Q${x + 70 * a} ${y - 60 * a} ${x + 30 * a} ${y - (190 + k * 20) * a}" fill="none" stroke="#fbf6ec" stroke-width="${(6 - k * 1.6) * a}" opacity="${0.75 - k * 0.2}" stroke-linecap="round"/>`).join('') + `<path d="M${x + 22 * a} ${y - 210 * a} l${14 * a} ${-24 * a} l${14 * a} ${24 * a}" fill="none" stroke="#fbf6ec" stroke-width="${5 * a}" opacity="0.75" stroke-linecap="round"/>` : '';
  return arcs + drawHand('ball', { x, y, scale: o.scale || 150, deg: o.deg ?? 200, stub: 3.4, flip: -1 });
}

// ---------------------------------------------------------------- E03 in one-point perspective
export const VP = [960, 560];
export function streetPerspective(light = 'dusk', o = {}) {
  const dark = light === 'dusk' || light === 'night';
  const L = LIGHT[light];
  const [vx, vy] = VP;
  const sk = light === 'dusk' ? ['#4f4f7e', '#e9a477'] : L.sky;
  let s = `<defs><linearGradient id="spSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${sk[0]}"/><stop offset="100%" stop-color="${sk[1]}"/></linearGradient></defs><rect x="-200" y="-200" width="2320" height="${vy + 260}" fill="url(#spSky)"/>`;
  if (light === 'dusk') s += `<circle cx="${vx + 40}" cy="${vy - 30}" r="70" fill="#ffc88a" opacity="0.7"/>`;
  // far trees at the vanishing point
  s += wc(ell(vx - 120, vy - 20, 140, 60, dark ? '#5f5a78' : '#a9bcc0', { stroke: false }) + ell(vx + 140, vy - 16, 150, 58, dark ? '#5f5a78' : '#a9bcc0', { stroke: false }), true);
  // ground planes: road, gutters, sidewalks (converging)
  const toVP = (x, y, t) => [x + (vx - x) * t, y + (vy - y) * t];
  s += poly([[-200, 1300], [2120, 1300], [vx + 8, vy], [vx - 8, vy]], dark ? '#5e5a66' : '#8c8a86', { stroke: false });
  s += poly([[-900, 1300], [-200, 1300], [vx - 8, vy], [vx - 30, vy]], dark ? '#8a7f86' : '#d7cbb2', { stroke: false }) + poly([[2120, 1300], [2820, 1300], [vx + 30, vy], [vx + 8, vy]], dark ? '#8a7f86' : '#d7cbb2', { stroke: false });
  s += ln(-200, 1300, vx - 8, vy, { sw: 3, so: 0.5 }) + ln(2120, 1300, vx + 8, vy, { sw: 3, so: 0.5 });
  for (let t = 0.05; t < 0.95; t += 0.1) { const a = toVP(960, 1300, t); const b = toVP(960, 1300, t + 0.04); s += ln(a[0], a[1], b[0], b[1], { sw: 10 * (1 - t), stroke: '#e8e2d2', so: 0.7 }); }
  // house facades on both sides, receding
  const cols = ['#e8d8b8', '#c9d3b8', '#e6c9a8', '#d6d0c0', '#e3d3b2', '#d9c7a4'];
  for (const side of [-1, 1]) {
    for (let i = 5; i >= 0; i--) {
      const t0 = 0.08 + i * 0.15;
      const t1 = t0 + 0.12;
      const baseX = side < 0 ? -700 : 2620;
      const near = toVP(baseX, 1180, t0);
      const far = toVP(baseX, 1180, t1);
      const hNear = 520 * (1 - t0);
      const hFar = 520 * (1 - t1);
      const wall = [[near[0], near[1]], [far[0], far[1]], [far[0], far[1] - hFar], [near[0], near[1] - hNear]];
      s += wc(poly(wall, cols[i % cols.length]));
      // roof edge
      s += wc(poly([[near[0], near[1] - hNear], [far[0], far[1] - hFar], [far[0] + side * -20 * (1 - t1), far[1] - hFar * 1.25], [near[0] + side * -40 * (1 - t0), near[1] - hNear * 1.25]], ['#b06a52', '#9b5f4c', '#8f6a5a'][i % 3]));
      // window (lit at dusk)
      const wx = (k) => near[0] + (far[0] - near[0]) * k;
      const wy = (k, h) => near[1] + (far[1] - near[1]) * k - h;
      const wh = (k) => hNear + (hFar - hNear) * k;
      s += poly([[wx(0.25), wy(0.25, wh(0.25) * 0.75)], [wx(0.6), wy(0.6, wh(0.6) * 0.75)], [wx(0.6), wy(0.6, wh(0.6) * 0.45)], [wx(0.25), wy(0.25, wh(0.25) * 0.45)]], dark && i % 2 === 0 ? '#f6cf86' : '#9fb6c8', { sw: 1.6 });
      // fence along the sidewalk edge
      const fn = toVP(side < 0 ? -260 : 2180, 1260, t0);
      const ff = toVP(side < 0 ? -260 : 2180, 1260, t1);
      const fh = (t) => 150 * (1 - t);
      s += wc(poly([[fn[0], fn[1]], [ff[0], ff[1]], [ff[0], ff[1] - fh(t1) * 0.35], [fn[0], fn[1] - fh(t0) * 0.35]], '#d9cdb5', { sw: 1.4 }));
      for (let b = 0; b <= 8; b++) { const q = b / 8; const x = fn[0] + (ff[0] - fn[0]) * q; const y = fn[1] + (ff[1] - fn[1]) * q; const hh = fh(t0 + (t1 - t0) * q); s += ln(x, y - hh * 0.35, x, y - hh, { sw: 2 * (1 - t0), stroke: '#3f3a36', so: 0.8 }); }
    }
    // power poles + wires
    let prev = null;
    for (let i = 0; i < 5; i++) {
      const t = 0.02 + i * 0.2;
      const b = toVP(side < 0 ? -120 : 2040, 1290, t);
      const h = 900 * (1 - t);
      s += ln(b[0], b[1], b[0], b[1] - h, { sw: 16 * (1 - t), stroke: '#8d8478', so: 1 });
      const top = [b[0], b[1] - h * 0.92];
      if (prev) s += pth(`M${prev[0]} ${prev[1]} Q${(prev[0] + top[0]) / 2} ${(prev[1] + top[1]) / 2 + 40 * (1 - t)} ${top[0]} ${top[1]}`, 'none', { sw: 1.8, so: 0.8 });
      if (dark) s += `<circle cx="${b[0] - side * 30 * (1 - t)}" cy="${b[1] - h * 0.86}" r="${110 * (1 - t)}" fill="url(#warmGlow)" opacity="0.5" style="mix-blend-mode:screen"/>`;
      prev = top;
    }
  }
  // trees and a parked motorbike near the camera
  s += tree(-60, 1240, 1.6, dark ? 'dusk' : 'day', { seed: 5 }) + tree(1990, 1250, 1.5, dark ? 'dusk' : 'day', { seed: 9 });
  if (o.bike !== false) s += motorbike(1560, 1050, 1.3, light);
  s += pot(300, 1180, 1.6) + pot(1660, 1160, 1.4, '#7f9a5e', '#a8684a');
  return s;
}
/** depth scale for a figure standing at screen y in the perspective street */
export const depthScale = (y, base = 92) => base * ((y - VP[1]) / (1300 - VP[1]));
/** walking away from the camera (back view): legs and arms alternate a little */
export const walkAway = (ph = 0) => ({ view: 'back', legL: { a1: -3 + 9 * Math.sin(ph), a2: -3 + 14 * Math.max(0, Math.sin(ph)) }, legR: { a1: 3 - 9 * Math.sin(ph), a2: 3 + 14 * Math.max(0, -Math.sin(ph)) }, armL: { a1: -16 - 8 * Math.sin(ph), a2: -10 }, armR: { a1: 16 - 8 * Math.sin(ph), a2: 10 } });

// ---------------------------------------------------------------- E05 from straight above
/** a person from above: shoulders (clothes colour) and the round head */
export function topPerson(x, y, s = 1, col = '#7d93ad', o = {}) {
  const r = rng(Math.round(x * 7 + y));
  const ang = o.ang ?? r() * 360;
  return `<g transform="translate(${n(x)} ${n(y)}) rotate(${n(ang)})" ${o.blur ? `filter="url(#${o.blur})"` : ''}><ellipse cx="0" cy="${4 * s}" rx="${46 * s}" ry="${22 * s}" fill="#6e5a44" opacity="0.25"/><ellipse cx="0" cy="0" rx="${42 * s}" ry="${19 * s}" fill="${col}" stroke="${INK}" stroke-width="${2.2 * s}"/><circle cx="0" cy="${-2 * s}" r="${20 * s}" fill="${o.head || STYLE.skin}" stroke="${INK}" stroke-width="${2.4 * s}"/>${o.cap ? `<circle cx="0" cy="${-2 * s}" r="${15 * s}" fill="${o.cap}" stroke="${INK}" stroke-width="${2 * s}"/>` : ''}${o.umbrella ? `<circle cx="${10 * s}" cy="${-8 * s}" r="${48 * s}" fill="${o.umbrella}" stroke="${INK}" stroke-width="${2 * s}" opacity="0.92"/>` : ''}</g>`;
}
export function crowdTop(o = {}) {
  let s = rect(-200, -200, 2320, 1500, '#d9cdb5', { stroke: false });
  for (let x = -200; x < 2200; x += 90) s += ln(x, -200, x, 1300, { so: 0.12, sw: 1.4 });
  for (let y = -200; y < 1300; y += 90) s += ln(-200, y, 2200, y, { so: 0.12, sw: 1.4 });
  // road + zebra crossing along the bottom
  s += rect(-200, 860, 2320, 500, '#8f8d8a', { stroke: false });
  for (let k = 0; k < 12; k++) s += rect(220 + k * 130, 880, 70, 300, '#efe9dc', { stroke: false, op: 0.9 });
  s += rect(-200, 846, 2320, 16, '#bdb19a');
  // tree canopies + a bus shelter roof from above
  s += wc(ell(150, 120, 170, 150, '#7d9a66') + ell(1800, 160, 180, 150, '#7d9a66') + ell(1700, 760, 150, 120, '#62804f'), true);
  s += wc(rect(260, 620, 380, 120, '#5f6b74', { rx: 6 }));
  const tops = ['#7d93ad', '#b9867a', '#8a9a72', '#c8a97a', '#9a86a8', '#6f7f8f', '#c98f6f', '#a8a08a'];
  const r = rng(o.seed || 4);
  let ppl = '';
  for (let k = 0; k < 70; k++) {
    const x = -100 + r() * 2120;
    const y = -80 + r() * 900;
    if (Math.hypot(x - 960, y - 470) < 150) continue;
    ppl += topPerson(x, y, 0.95 + r() * 0.2, tops[k % tops.length], { cap: r() > 0.85 ? '#c2874f' : null, umbrella: r() > 0.92 ? '#8aa0c4' : null });
  }
  s += ppl;
  // Milo from above: cream shoulders (no clothes), the same round head
  s += topPerson(960, 470, 1.25, STYLE.skin, { ang: 0 });
  return s;
}

// ---------------------------------------------------------------- Shot 01: from Milo's front yard, close to his window
/** the room seen from outside through the window glass (mirrored: we look in from the yard side) */
export function yardWindow(roomSvg, o = {}) {
  const wx = o.wx ?? 520;
  const wy = o.wy ?? 170;
  const ww = o.ww ?? 880;
  const wh = o.wh ?? 640;
  const facade = '#9a8c78'; // house wall at night (house 1 colour, darkened)
  let s = '';
  // night sky strip + roof eave at the top
  s += `<rect x="0" y="0" width="${W}" height="${H}" fill="#202a46"/>`;
  s += wc(rect(-50, 40, W + 100, H, facade) + poly([[-80, 60], [W + 80, 60], [W + 80, -20], [-80, -20]], '#5e4038') + rect(-80, 52, W + 160, 20, '#4e352f'));
  for (let k = 0; k < 14; k++) s += ln(-50, 110 + k * 70, W + 50, 110 + k * 70, { so: 0.08, sw: 1.5 });
  s += `<ellipse cx="${wx + ww / 2}" cy="${wy + wh / 2}" rx="${ww * 0.85}" ry="${wh * 0.85}" fill="url(#warmGlow)" opacity="0.22" style="mix-blend-mode:screen"/>`;
  // the room inside, clipped to the opening
  s += `<defs><clipPath id="ywClip"><rect x="${wx}" y="${wy}" width="${ww}" height="${wh}"/></clipPath><linearGradient id="ywGlass" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#b9cbe6" stop-opacity="0.5"/><stop offset="55%" stop-color="#6f86b0" stop-opacity="0.3"/><stop offset="100%" stop-color="#2a3558" stop-opacity="0.5"/></linearGradient></defs>`;
  s += `<g clip-path="url(#ywClip)"><g filter="url(#b3)">${roomSvg}</g>`;
  // glass: tint, reflections of the yard tree and the moon, diagonal glare, light condensation at the bottom
  s += `<rect x="${wx}" y="${wy}" width="${ww}" height="${wh}" fill="url(#ywGlass)"/>`;
  s += `<g opacity="0.38" filter="url(#b5)">${ell(wx + 140, wy + 120, 170, 120, '#1c2a2a', { stroke: false })}${ell(wx + 60, wy + 260, 120, 140, '#1c2a2a', { stroke: false })}<circle cx="${wx + ww - 160}" cy="${wy + 90}" r="34" fill="#f4ecd0"/></g>`;
  s += [0, 1, 2].map((k) => `<path d="M${wx + 120 + k * 260} ${wy + wh} L${wx + 320 + k * 260} ${wy}" stroke="#ffffff" stroke-width="${70 - k * 18}" opacity="${0.12 + (k === 1 ? 0.07 : 0)}" filter="url(#b8)"/>`).join('');
  s += `<rect x="${wx}" y="${wy + wh - 120}" width="${ww}" height="120" fill="#dfe8f2" opacity="0.12" filter="url(#b8)"/>`;
  const r = rng(21);
  for (let k = 0; k < 70; k++) s += `<circle cx="${n(wx + r() * ww)}" cy="${n(wy + wh - r() * 150)}" r="${n(1.5 + r() * 3.5)}" fill="#eef3fa" opacity="${n(0.15 + r() * 0.3)}"/>`;
  s += `</g>`;
  // window frame (wood), mullions, sill, warm light spilling out
  const fr = '#e3d8c3';
  s += wc(rect(wx - 30, wy - 30, ww + 60, wh + 60, 'none', { sw: 34, stroke: fr, so: 1 }) + rect(wx - 30, wy - 30, ww + 60, wh + 60, 'none', { sw: 2.4 }) + rect(wx - 47, wy - 47, ww + 94, wh + 94, 'none', { sw: 2, so: 0.5 }));
  s += wc(ln(wx + ww / 2, wy, wx + ww / 2, wy + wh, { sw: 20, stroke: fr, so: 1 }) + ln(wx, wy + wh * 0.36, wx + ww, wy + wh * 0.36, { sw: 14, stroke: fr, so: 1 }));
  s += wc(rect(wx - 90, wy + wh + 30, ww + 180, 34, '#cfc2a8') + rect(wx - 70, wy + wh + 64, ww + 140, 14, '#a99c84', { op: 0.8 }));
  s += `<ellipse cx="${wx + ww / 2}" cy="${wy + wh + 200}" rx="${ww * 0.75}" ry="220" fill="url(#warmGlow)" opacity="0.35" style="mix-blend-mode:screen"/>`;
  // front yard foreground: plants and a pot, out of focus
  s += `<g filter="url(#b8)">${pot(260, 1180, 3.2)}${pot(1700, 1200, 3.0, '#7f9a5e', '#a8684a')}${wc(ell(980, 1170, 520, 120, '#33473f', { stroke: false }) + ell(620, 1120, 260, 120, '#3c5446', { stroke: false }) + ell(1360, 1130, 280, 120, '#3c5446', { stroke: false }))}</g>`;
  return s;
}

// ---------------------------------------------------------------- E03 as a real one-point perspective scene (box houses)
// World units in metres: x across (road centre 0, + right), y up, z away from the camera.
export const P3 = { f: 950, h: 1.55, vx: 960, vy: 520 };
export const proj = (x, y, z) => [P3.vx + (P3.f * x) / z, P3.vy + (P3.f * (P3.h - y)) / z];
const pp = (pts) => pts.map(([x, y, z]) => proj(x, y, z));
/** pixels per metre at depth z (to size Milo and extras) */
export const pxPerM = (z) => P3.f / z;
/** Milo / an extra standing at (x, z): returns {x, y, scale} for drawMilo (height in metres) */
export function placeAt(x, z, heightM = 1.25) {
  const [sx, sy] = proj(x, 0, z);
  return { x: sx, y: sy, scale: (heightM * pxPerM(z)) / 5.43 };
}
function boxHouse(side, x0, x1, z0, z1, wallH, roofH, col, roofCol, light, i) {
  const dark = light === 'dusk' || light === 'night';
  const s = side; // -1 left of the road, +1 right
  const near = s > 0 ? x0 : -x0; // street-facing wall plane
  const far = s > 0 ? x1 : -x1;
  const mid = (near + far) / 2;
  let g = '';
  const shade = (hex, k) => { const c = parseInt(hex.slice(1), 16); const f = (v) => Math.round(v * k).toString(16).padStart(2, '0'); return `#${f((c >> 16) & 255)}${f((c >> 8) & 255)}${f(c & 255)}`; };
  // street-facing side wall (receding) — the lit face
  g += poly(pp([[near, 0, z0], [near, 0, z1], [near, wallH, z1], [near, wallH, z0]]), col);
  // near end wall (frontal, faces the camera) — slightly darker so the corner reads
  g += poly(pp([[near, 0, z0], [far, 0, z0], [far, wallH, z0], [near, wallH, z0]]), shade(col, 0.86));
  // gable triangle on the end wall
  g += poly(pp([[near, wallH, z0], [far, wallH, z0], [mid, wallH + roofH, z0]]), shade(col, 0.8));
  // roof plane facing the street (from the eave to the ridge), with overhang at the front
  g += poly(pp([[near - s * 0.35, wallH - 0.15, z0 - 0.4], [near - s * 0.35, wallH - 0.15, z1 + 0.2], [mid, wallH + roofH, z1 + 0.2], [mid, wallH + roofH, z0 - 0.4]]), roofCol);
  // roof edge (fascia) along the gable, gives the corner thickness
  g += pth(`M${pp([[near - s * 0.35, wallH - 0.15, z0 - 0.4]])[0].join(' ')} L${pp([[mid, wallH + roofH, z0 - 0.4]])[0].join(' ')} L${pp([[far + s * 0.35, wallH - 0.15, z0 - 0.4]])[0].join(' ')}`, 'none', { sw: 5, stroke: shade(roofCol, 0.7), so: 1 });
  // corner line
  g += pth(`M${proj(near, 0, z0).join(' ')} L${proj(near, wallH, z0).join(' ')}`, 'none', { sw: 2.4 });
  // windows + door on the street-facing wall
  const win = (za, zb, ya, yb, lit) => poly(pp([[near, ya, za], [near, ya, zb], [near, yb, zb], [near, yb, za]]), lit ? '#f6cf86' : '#9fb6c8', { sw: 1.8 });
  const L = z1 - z0;
  g += win(z0 + L * 0.12, z0 + L * 0.32, 1.0, 2.1, dark && i % 2 === 0) + win(z0 + L * 0.68, z0 + L * 0.88, 1.0, 2.1, dark && i % 2 === 1);
  g += poly(pp([[near, 0, z0 + L * 0.44], [near, 0, z0 + L * 0.56], [near, 2.1, z0 + L * 0.56], [near, 2.1, z0 + L * 0.44]]), '#8e6a4c', { sw: 1.8 });
  // a window on the end wall
  const ex = (k) => near + (far - near) * k;
  g += poly(pp([[ex(0.35), 1.1, z0], [ex(0.65), 1.1, z0], [ex(0.65), 2.0, z0], [ex(0.35), 2.0, z0]]), dark && i % 3 === 0 ? '#f6cf86' : '#9fb6c8', { sw: 1.6 });
  return wc(g);
}
function fence3(side, z0, z1, gate = null) {
  const x = side * 5.8;
  let g = poly(pp([[x, 0, z0], [x, 0, z1], [x, 0.45, z1], [x, 0.45, z0]]), '#d9cdb5', { sw: 1.4 });
  g += pth(`M${proj(x, 1.15, z0).join(' ')} L${proj(x, 1.15, z1).join(' ')}`, 'none', { sw: 3, stroke: '#3f3a36', so: 0.85 });
  for (let z = z0; z <= z1; z += 0.35) {
    if (gate && z > gate[0] && z < gate[1]) continue;
    g += pth(`M${proj(x, 0.45, z).join(' ')} L${proj(x, 1.15, z).join(' ')}`, 'none', { sw: Math.max(0.8, 26 / z), stroke: '#3f3a36', so: 0.8 });
  }
  // brick posts at both ends
  for (const z of [z0, z1]) g += poly(pp([[x - side * 0.15, 0, z], [x + side * 0.15, 0, z], [x + side * 0.15, 1.35, z], [x - side * 0.15, 1.35, z]]), '#cfc2a8', { sw: 1.4 });
  return wc(g);
}
export function street3d(light = 'morning', o = {}) {
  const dark = light === 'dusk' || light === 'night';
  const L = LIGHT[light];
  const sk = light === 'dusk' ? ['#4f4f7e', '#e9a477'] : L.sky;
  const [vx, vy] = [P3.vx, P3.vy];
  let s = `<defs><linearGradient id="s3Sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${sk[0]}"/><stop offset="100%" stop-color="${sk[1]}"/></linearGradient></defs><rect x="-200" y="-200" width="2320" height="${vy + 300}" fill="url(#s3Sky)"/>`;
  if (light === 'dusk') s += `<circle cx="${vx + 30}" cy="${vy - 40}" r="60" fill="#ffc88a" opacity="0.7"/>`;
  s += wc(ell(vx - 160, vy - 18, 220, 60, dark ? '#5f5a78' : '#a9bcc0', { stroke: false }) + ell(vx + 180, vy - 14, 220, 56, dark ? '#5f5a78' : '#a9bcc0', { stroke: false }), true);
  // ground: verge, sidewalks, curbs, road (planes to the horizon)
  const Z0 = 2.2;
  const Z1 = 400;
  const band = (xa, xb, col) => poly(pp([[xa, 0, Z0], [xb, 0, Z0], [xb, 0, Z1], [xa, 0, Z1]]), col, { stroke: false });
  s += band(-60, -5.8, dark ? '#6f6a5a' : '#9c9a7a') + band(5.8, 60, dark ? '#6f6a5a' : '#9c9a7a');
  s += band(-5.8, -3.1, dark ? '#8a7f86' : '#d7cbb2') + band(3.1, 5.8, dark ? '#8a7f86' : '#d7cbb2');
  s += band(-3.1, -2.95, '#bdb19a') + band(2.95, 3.1, '#bdb19a');
  s += band(-2.95, 2.95, dark ? '#5e5a66' : '#8c8a86');
  for (let z = 3; z < 80; z += 1.2) for (const x of [-5.8, 5.8, -3.1, 3.1]) s += '';
  // sidewalk paving joints
  let pv = '';
  for (let z = 3; z < 90; z *= 1.12) for (const sd of [-1, 1]) pv += pth(`M${proj(sd * 3.1, 0, z).join(' ')} L${proj(sd * 5.8, 0, z).join(' ')}`, 'none', { sw: 1.2, so: 0.18 });
  s += pv;
  // gutter line + centre dashes
  for (const sd of [-1, 1]) s += pth(`M${proj(sd * 2.95, 0, Z0).join(' ')} L${proj(sd * 2.95, 0, Z1).join(' ')}`, 'none', { sw: 3, so: 0.5 });
  for (let z = 3; z < 120; z += 6) s += poly(pp([[-0.08, 0, z], [0.08, 0, z], [0.08, 0, z + 3], [-0.08, 0, z + 3]]), '#e8e2d2', { stroke: false, op: 0.75 });
  // objects, far to near
  const items = []; // roadside structures (houses, fences, trees, pots): drawn first, far to near
  const front = []; // things on the sidewalk / road (poles, people, bike): drawn after, far to near
  const cols = ['#e8d8b8', '#c9d3b8', '#e6c9a8', '#d6d0c0', '#e3d3b2', '#d9c7a4', '#cdd5c4'];
  const roofs = ['#b06a52', '#9b5f4c', '#8f6a5a', '#a45f4f', '#7f6f62'];
  let i = 0;
  for (const sd of [-1, 1]) {
    for (let z0 = 8 + (sd > 0 ? 3 : 0); z0 < 80; z0 += 10.5) {
      const d = 7;
      const w = 7.5 + ((i * 7) % 3);
      const k = i++;
      items.push({ z: z0, svg: () => boxHouse(sd, 7.5, 7.5 + w, z0, z0 + d, 3.1, 2.1, cols[k % cols.length], roofs[k % roofs.length], light, k) });
      items.push({ z: z0 - 0.3, svg: () => fence3(sd, z0 - 1.2, z0 + d + 0.6, [z0 + d * 0.4, z0 + d * 0.62]) });
      // tree in the gap between houses
      const tz = z0 + d + 1.8;
      if (k % 2 === 0) items.push({ z: tz, svg: () => { const [tx, ty] = proj(sd * 7.2, 0, tz); return tree(tx, ty, 1.35 * pxPerM(tz) / 95, dark ? 'dusk' : 'day', { seed: k * 13 + 5 }); } });
      items.push({ z: z0 + 2.5, svg: () => { const [px, py] = proj(sd * 5.4, 0, z0 + 2.5); return pot(px, py, 0.9 * pxPerM(z0 + 2.5) / 95); } });
    }
    // power poles
    for (let z = 6 + (sd > 0 ? 6 : 0); z < 90; z += 12) {
      front.push({ z, svg: () => { const b = proj(sd * 5.35, 0, z); const t = proj(sd * 5.35, 8, z); const arm = [proj(sd * 5.35 - 0.9, 7.6, z), proj(sd * 5.35 + 0.9, 7.6, z)]; let g = pth(`M${b.join(' ')} L${t.join(' ')}`, 'none', { sw: Math.max(1.5, 0.28 * pxPerM(z)), stroke: '#8d8478', so: 1 }) + pth(`M${arm[0].join(' ')} L${arm[1].join(' ')}`, 'none', { sw: Math.max(1, 0.16 * pxPerM(z)), stroke: '#7a7166', so: 1 }); const nz = z + 12; const a = proj(sd * 5.35, 7.6, z); const c = proj(sd * 5.35, 7.6, nz); g += pth(`M${a.join(' ')} Q${(a[0] + c[0]) / 2} ${(a[1] + c[1]) / 2 + 0.5 * pxPerM(z)} ${c.join(' ')}`, 'none', { sw: 1.6, so: 0.8 }); if (dark) g += `<circle cx="${n(t[0] - sd * 0.6 * pxPerM(z))}" cy="${n(arm[0][1] + 0.4 * pxPerM(z))}" r="${n(2.8 * pxPerM(z))}" fill="url(#warmGlow)" opacity="0.5" style="mix-blend-mode:screen"/>`; return wc(g); } });
    }
  }
  if (o.bike) front.push({ z: 9, svg: () => { const [bx, by] = proj(2.4, 0, 9); return motorbike(bx, by, 1.15 * pxPerM(9) / 95 * 1.6, light); } });
  for (const it of items.sort((a, b) => b.z - a.z)) s += it.svg();
  for (const it of [...front, ...(o.people || [])].sort((a, b) => b.z - a.z)) s += it.svg();
  return s;
}
