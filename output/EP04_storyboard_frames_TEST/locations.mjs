// E03–E07 master layouts (world coordinates). One layout per location, reused by every shot there.
import { poly, rect, ell, pth, ln, wc, tree, bush, pot, rng, LIGHT, INK, extra } from './world.mjs';

let SID = 0;
function sky(x, y, w, h, light) {
  const L = LIGHT[light];
  const id = `sky${SID++}`;
  return `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${L.sky[0]}"/><stop offset="100%" stop-color="${L.sky[1]}"/></linearGradient></defs><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${id})"/>`;
}
const isDark = (l) => l === 'night' || l === 'dusk';

// ---------------------------------------------------------------- E03 residential street (side layout, 3800 wide)
export const STREET = { walkY: 845, curbY: 870, roadY: 900, w: 3800, miloHouse: 1, houses: [] };
const HOUSE_COL = ['#e8d8b8', '#d9c7a4', '#c9d3b8', '#e6c9a8', '#d6d0c0', '#e3d3b2'];
const ROOF_COL = ['#b06a52', '#8f6a5a', '#9b5f4c', '#7f6f62', '#b07a58', '#a45f4f'];
for (let i = 0; i < 6; i++) STREET.houses.push({ x0: 60 + i * 610, w: 500 + (i % 2) * 40, top: 470 + (i % 3) * 18, col: HOUSE_COL[i], roof: ROOF_COL[i] });

export function street(light = 'morning', o = {}) {
  const S = STREET;
  const dark = isDark(light);
  let s = sky(-600, -400, 5000, 1300, light);
  if (light === 'night') s += `<circle cx="2200" cy="120" r="34" fill="#f4ecd0"/><circle cx="2200" cy="120" r="90" fill="#f4ecd0" opacity="0.12"/>`;
  if (light === 'dusk') s += `<circle cx="2900" cy="560" r="80" fill="#ffc88a" opacity="0.6"/>`;
  // far layer: distant roofs and trees
  const far = light === 'night' ? '#26304c' : light === 'dusk' ? '#6f6488' : '#a9bcc0';
  let fp = '';
  const r = rng(5);
  for (let x = -600; x < 4400; x += 170) fp += ell(x, 600 - r() * 40, 120 + r() * 50, 70 + r() * 30, far, { stroke: false });
  s += wc(fp + rect(-600, 590, 5000, 300, far, { stroke: false }), true);
  // trees between houses (behind fences)
  for (const x of [20, 600, 1230, 1840, 2470, 3080, 3700]) s += tree(x, 760, 1.05, dark ? (light === 'night' ? 'night' : 'dusk') : 'day', { seed: x });
  // houses
  let hs = '';
  S.houses.forEach((h, i) => {
    const base = 790;
    const wallTop = h.top;
    hs += rect(h.x0, wallTop, h.w, base - wallTop, h.col);
    hs += poly([[h.x0 - 40, wallTop + 4], [h.x0 + h.w / 2, wallTop - 150], [h.x0 + h.w + 40, wallTop + 4]], h.roof);
    hs += rect(h.x0 - 30, wallTop - 4, h.w + 60, 16, h.roof, { op: 0.9 });
    // windows + door
    const winC = dark ? '#f2c27a' : '#9fb6c8';
    const lit = (k) => (dark && (i + k) % 2 === 0) || (i === S.miloHouse && k === 0 && o.miloWindowLit);
    hs += rect(h.x0 + 50, wallTop + 70, 120, 110, lit(0) ? '#f6cf86' : winC, { op: 1 }) + ln(h.x0 + 110, wallTop + 70, h.x0 + 110, wallTop + 180, { sw: 5, stroke: '#efe6d2', so: 1 }) + rect(h.x0 + 44, wallTop + 180, 132, 10, '#efe6d2');
    hs += rect(h.x0 + h.w - 170, wallTop + 70, 120, 110, lit(1) ? '#f6cf86' : winC) + ln(h.x0 + h.w - 110, wallTop + 70, h.x0 + h.w - 110, wallTop + 180, { sw: 5, stroke: '#efe6d2', so: 1 });
    hs += rect(h.x0 + h.w / 2 - 45, base - 190, 90, 190, '#8e6a4c') + ell(h.x0 + h.w / 2 + 28, base - 95, 5, 5, INK, { stroke: false });
    hs += rect(h.x0 + h.w / 2 - 60, base - 205, 120, 12, h.roof);
    if (i === S.miloHouse && o.miloWindowLit) hs += `<circle cx="${h.x0 + 110}" cy="${wallTop + 125}" r="160" fill="url(#warmGlow)" opacity="0.5" style="mix-blend-mode:screen"/>`;
    // yard ground
    hs += rect(h.x0 - 60, base - 2, h.w + 120, 22, '#9c9a7a', { stroke: false, op: 0.6 });
  });
  s += wc(hs);
  // fences, gates, pots (iron bars on a low wall)
  let fc = '';
  for (let x = -600; x < 4400; x += 610) {
    fc += rect(x, 760, 470, 44, '#d9cdb5') + rect(x + 470, 680, 30, 124, '#cfc2a8');
    for (let b = x + 12; b < x + 470; b += 22) fc += ln(b, 760, b, 690, { sw: 3, stroke: '#3f3a36', so: 0.85 });
    fc += ln(x, 692, x + 470, 692, { sw: 4, stroke: '#3f3a36', so: 0.85 });
    // gate (open bars, different colour)
    fc += rect(x + 500, 690, 100, 114, 'none', { sw: 4, stroke: '#4a5560', so: 0.9 });
    for (let b = x + 512; b < x + 600; b += 18) fc += ln(b, 692, b, 802, { sw: 3, stroke: '#4a5560', so: 0.9 });
    fc += pot(x + 60, 805, 0.9) + pot(x + 420, 805, 0.8, '#7f9a5e', '#a8684a');
  }
  s += wc(fc);
  // power poles + sagging wires
  let pl = '';
  const poles = [380, 1500, 2620, 3740];
  for (const x of poles) pl += rect(x - 9, 170, 18, 690, '#8d8478') + rect(x - 70, 210, 140, 12, '#7a7166') + ell(x - 50, 204, 7, 9, '#cfc6b8') + ell(x + 50, 204, 7, 9, '#cfc6b8');
  for (let i = 0; i < poles.length - 1; i++) for (const [dy, sag] of [[0, 70], [12, 90], [-6, 55]]) pl += pth(`M${poles[i] - 50} ${208 + dy} Q${(poles[i] + poles[i + 1]) / 2} ${208 + dy + sag} ${poles[i + 1] - 50} ${208 + dy}`, 'none', { sw: 1.8, so: 0.8 });
  s += wc(pl);
  // warung (small shop) far right
  s += wc(rect(3420, 560, 340, 240, '#e2c89a') + rect(3440, 640, 300, 160, '#7e6a54') + pth(`M3400 560 L3780 560 L3760 610 L3420 610 Z`, '#c95f4f') + [0, 1, 2, 3, 4, 5].map((k) => rect(3420 + k * 60, 560, 30, 50, '#efe0c8', { stroke: false, op: 0.9 })).join('') + rect(3460, 660, 260, 8, '#b48a5a') + rect(3460, 710, 260, 8, '#b48a5a') + [0, 1, 2, 3, 4, 5, 6].map((k) => rect(3470 + k * 36, 680, 22, 30, ['#c9663f', '#e0b04e', '#6f8fa8'][k % 3], { sw: 1.4 })).join(''));
  // sidewalk, curb, gutter, road
  let gr = rect(-600, 800, 5000, S.curbY - 800, light === 'night' ? '#6b6a72' : '#d7cbb2', { stroke: false });
  for (let x = -600; x < 4400; x += 90) gr += ln(x, 800, x - 30, S.curbY, { so: 0.18, sw: 1.4 });
  gr += rect(-600, S.curbY, 5000, 12, '#bdb19a') + rect(-600, S.curbY + 12, 5000, 20, '#5d5850') ;
  for (let x = -600; x < 4400; x += 40) gr += ln(x, S.curbY + 14, x, S.curbY + 30, { so: 0.35, sw: 2 });
  gr += rect(-600, S.roadY, 5000, 500, light === 'night' ? '#3e3f48' : '#8c8a86', { stroke: false });
  for (let x = -560; x < 4400; x += 260) gr += rect(x, 1010, 130, 10, '#e8e2d2', { stroke: false, op: 0.7 });
  s += wc(gr);
  // parked motorbike
  s += motorbike(2280, 960, 1, light);
  // street lamps glow at dusk / night
  if (dark) for (const x of poles) s += `<circle cx="${x + 40}" cy="${250}" r="140" fill="url(#warmGlow)" opacity="0.45" style="mix-blend-mode:screen"/>` + ell(x + 40, 245, 14, 9, '#ffe2a8', { stroke: false });
  return s;
}
export function motorbike(x, y, s = 1, light = 'day') {
  const body = light === 'night' ? '#5b6b8a' : '#c45a48';
  return wc(`<circle cx="${x - 70 * s}" cy="${y}" r="${30 * s}" fill="#2f2f33" stroke="${INK}" stroke-width="2"/><circle cx="${x - 70 * s}" cy="${y}" r="${12 * s}" fill="#9a9a9e"/><circle cx="${x + 75 * s}" cy="${y}" r="${30 * s}" fill="#2f2f33" stroke="${INK}" stroke-width="2"/><circle cx="${x + 75 * s}" cy="${y}" r="${12 * s}" fill="#9a9a9e"/>` +
    pth(`M${x - 95 * s} ${y - 30 * s} Q${x - 60 * s} ${y - 80 * s} ${x - 5 * s} ${y - 60 * s} L${x + 40 * s} ${y - 40 * s} L${x + 60 * s} ${y - 95 * s} L${x + 80 * s} ${y - 95 * s} L${x + 90 * s} ${y - 30 * s} Z`, body) + rect(x - 90 * s, y - 82 * s, 85 * s, 16 * s, '#2f2f33', { rx: 6 }) + ln(x + 62 * s, y - 95 * s, x + 50 * s, y - 128 * s, { sw: 4 }) + ln(x + 38 * s, y - 128 * s, x + 66 * s, y - 128 * s, { sw: 5 }));
}

// ---------------------------------------------------------------- E04 café / neighbourhood shop (1920 wide interior)
export const CAFE = { floorY: 905, counterTop: 715, counterFront: 860, counterX0: 760, counterX1: 1560 };
export function cafe(light = 'day', o = {}) {
  const C = CAFE;
  let s = rect(-300, -200, 2520, 1000, '#ecdcbf', { stroke: false });
  s += rect(-300, 560, 2520, 345, '#b88c62', { stroke: false }) + ln(-300, 560, 2220, 560, { sw: 3 });
  for (let x = -300; x < 2220; x += 60) s += ln(x, 566, x, 900, { so: 0.18, sw: 1.5 });
  s += poly([[-300, C.floorY], [2220, C.floorY], [2220, 1300], [-300, 1300]], '#c9b08e', { stroke: false });
  for (let i = 0; i < 26; i++) s += ln(-300 + i * 100, C.floorY, -500 + i * 140, 1300, { so: 0.15, sw: 1.4 });
  for (let k = 0; k < 6; k++) s += ln(-300, C.floorY + k * k * 12 + 10, 2220, C.floorY + k * k * 12 + 10, { so: 0.13, sw: 1.4 });
  // front window + glass door (left)
  s += sky(20, 170, 520, 520, light === 'afternoon' ? 'afternoon' : 'day') + tree(120, 760, 0.6, 'day') + rect(260, 470, 260, 220, '#e3c9a3', { op: 0.9 }) + poly([[240, 475], [390, 380], [540, 475]], '#b8735a');
  s += rect(20, 170, 520, 520, 'none', { sw: 14, stroke: '#6f5640', so: 1 }) + ln(280, 170, 280, 690, { sw: 9, stroke: '#6f5640', so: 1 });
  s += rect(560, 220, 150, 680, '#cfe0e8', { op: 0.55 }) + rect(560, 220, 150, 680, 'none', { sw: 10, stroke: '#6f5640', so: 1 }) + rect(680, 540, 10, 60, '#c9b48e');
  // menu board (generic: chalk lines, no words), shelves with jars and cups
  s += rect(860, 150, 420, 230, '#3f5148') + rect(860, 150, 420, 230, 'none', { sw: 10, stroke: '#8a6646', so: 1 });
  for (let k = 0; k < 5; k++) s += ln(900, 200 + k * 36, 1100 - (k % 2) * 50, 200 + k * 36, { stroke: '#e8e2d2', so: 0.75, sw: 3 }) + ln(1170, 200 + k * 36, 1240, 200 + k * 36, { stroke: '#e8e2d2', so: 0.75, sw: 3 });
  for (const y of [300, 420]) {
    s += rect(1340, y, 520, 14, '#8e6a4c');
    for (let k = 0; k < 9; k++) s += k % 3 === 0 ? rect(1355 + k * 56, y - 60, 40, 60, '#cfe0e8', { op: 0.85, rx: 6 }) + rect(1360 + k * 56, y - 34, 30, 30, ['#c98f5c', '#a26a4a', '#e0b04e'][k % 3], { stroke: false }) : rect(1360 + k * 56, y - 34, 34, 34, ['#efe6d6', '#c9d6dc', '#e8c9a8'][k % 3], { rx: 4, sw: 1.6 });
  }
  // pendant lamps
  for (const x of [930, 1180, 1430]) s += ln(x, -200, x, 120, { sw: 2 }) + pth(`M${x - 40} ${150} Q${x} ${100} ${x + 40} ${150} Z`, '#3f5148') + `<circle cx="${x}" cy="160" r="150" fill="url(#warmGlow)" opacity="0.38" style="mix-blend-mode:screen"/>`;
  // back counter + coffee machine
  s += rect(1300, 500, 560, 60, '#9a7450');
  s += rect(1420, 400, 170, 100, '#a9adb2', { rx: 8 }) + rect(1440, 420, 60, 40, '#3b3f46', { rx: 4 }) + ln(1540, 470, 1540, 498, { sw: 4 }) + ell(1555, 430, 10, 10, '#c9663f', { stroke: false });
  if (o.machineNoise) s += pth(`M1600 400 l30 -20 M1605 430 l40 0 M1600 460 l30 20`, 'none', { sw: 3, so: 0.9 }) + pth(`M1470 390 q-10 -30 6 -50 q14 -20 -2 -44`, 'none', { sw: 3, stroke: '#ffffff', so: 0.8 });
  return wc(s);
}
/** the counter + display case (drawn in front of the cashier) */
export function cafeCounter() {
  const C = CAFE;
  let s = rect(C.counterX0, C.counterTop, C.counterX1 - C.counterX0, C.counterFront - C.counterTop, '#8e6a4c') + rect(C.counterX0 - 10, C.counterTop - 14, C.counterX1 - C.counterX0 + 20, 18, '#6f5640');
  for (let x = C.counterX0 + 30; x < C.counterX1; x += 70) s += ln(x, C.counterTop + 10, x, C.counterFront, { so: 0.25, sw: 1.5 });
  // display case with pastries (left part)
  s += rect(C.counterX0 + 20, C.counterTop - 130, 330, 116, '#d9e8ee', { op: 0.6 }) + rect(C.counterX0 + 20, C.counterTop - 130, 330, 116, 'none');
  for (let k = 0; k < 6; k++) s += ell(C.counterX0 + 60 + k * 50, C.counterTop - 40, 20, 13, ['#d6a35e', '#c98f5c', '#e8c9a8'][k % 3]);
  for (let k = 0; k < 5; k++) s += ell(C.counterX0 + 80 + k * 55, C.counterTop - 92, 18, 12, ['#e0b04e', '#b46a55'][k % 2]);
  // register
  s += rect(1300, C.counterTop - 60, 110, 56, '#5a5f66', { rx: 6 }) + rect(1312, C.counterTop - 62, 50, 26, '#a9c8a6', { rx: 3 });
  s += rect(C.counterX0 - 20, C.counterFront, C.counterX1 - C.counterX0 + 40, 24, '#6f5640');
  return wc(s);
}
export function cafeTable(x, y, s = 1) {
  return wc(rect(x - 110 * s, y - 150 * s, 220 * s, 16 * s, '#a07a55') + rect(x - 10 * s, y - 134 * s, 20 * s, 130 * s, '#7d5e43') + rect(x - 60 * s, y - 6 * s, 120 * s, 10 * s, '#7d5e43') + ell(x - 40 * s, y - 168 * s, 18 * s, 10 * s, '#efe6d6') + rect(x + 20 * s, y - 190 * s, 26 * s, 34 * s, '#efe6d6', { rx: 4 }));
}
export function chair(x, y, s = 1, facing = 1) {
  const f = facing;
  return wc(rect(x - 50 * s, y - 120 * s, 100 * s, 14 * s, '#8e6a4c') + rect(x - 45 * s, y - 106 * s, 10 * s, 106 * s, '#6d523a') + rect(x + 35 * s, y - 106 * s, 10 * s, 106 * s, '#6d523a') + rect(x - f * 50 * s - (f > 0 ? 0 : -10 * s), y - 240 * s, 10 * s, 130 * s, '#6d523a') + rect(x - f * 50 * s - (f > 0 ? 0 : 60 * s), y - 240 * s, 70 * s, 40 * s, '#8e6a4c', { rx: 6 }));
}

// ---------------------------------------------------------------- E05 crowded public area (3400 wide)
export const PLAZA = { walkY: 860, roadY: 905, w: 3400 };
export function plaza(light = 'day') {
  let s = sky(-600, -400, 4600, 1300, light);
  // building blocks with shops (awnings, blank signboards)
  const cols = ['#e3d3b2', '#d4c3a6', '#cdd5c4', '#e6cfae', '#d9cdbb', '#e0c9a8', '#cbd0c6'];
  let b = '';
  for (let i = 0; i < 9; i++) {
    const x = -500 + i * 470;
    const top = 120 + (i % 3) * 60;
    b += rect(x, top, 450, 700 - top + 90, cols[i % cols.length]);
    for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) b += rect(x + 40 + c * 130, top + 40 + r * 110, 90, 70, '#9fb6c8', { op: 0.9 });
    b += pth(`M${x + 10} 620 L${x + 440} 620 L${x + 420} 680 L${x + 30} 680 Z`, ['#c95f4f', '#5f8a8b', '#d9a14e', '#7a6aa0'][i % 4]);
    for (let k = 0; k < 7; k++) b += rect(x + 30 + k * 56, 620, 28, 60, '#efe0c8', { stroke: false, op: 0.7 });
    b += rect(x + 90, 560, 270, 50, '#f3ead8') + ln(x + 120, 585, x + 330, 585, { so: 0.35, sw: 6 }); // blank signboard
    b += rect(x + 40, 690, 370, 120, '#6f6a62', { op: 0.85 }) + rect(x + 60, 700, 150, 110, '#c9dbe2', { op: 0.6 });
  }
  s += wc(b);
  for (const x of [-200, 500, 1250, 1950, 2700, 3400]) s += tree(x, 850, 0.95, 'day', { seed: x + 3 });
  // sidewalk, bus shelter, bench, signpost
  let g = rect(-600, 810, 4600, PLAZA.roadY - 810, '#d9cdb5', { stroke: false });
  for (let x = -600; x < 4000; x += 80) g += ln(x, 810, x - 20, PLAZA.roadY, { so: 0.15, sw: 1.3 });
  g += rect(-600, PLAZA.roadY - 10, 4600, 12, '#bdb19a') + rect(-600, PLAZA.roadY, 4600, 600, '#8f8d8a', { stroke: false });
  // zebra crossing (foreground, x 600..1500)
  for (let k = 0; k < 9; k++) g += rect(620 + k * 100, 960, 60, 400, '#efe9dc', { stroke: false, op: 0.9 });
  s += wc(g);
  s += wc(rect(2500, 560, 420, 20, '#5f6b74') + rect(2510, 580, 10, 270, '#5f6b74') + rect(2900, 580, 10, 270, '#5f6b74') + rect(2520, 600, 380, 200, '#cfe0e8', { op: 0.35 }) + rect(2560, 780, 300, 16, '#8e6a4c'));
  s += wc(rect(1660, 470, 12, 390, '#5f6b74') + rect(1600, 470, 140, 70, '#e9e2d0') + ln(1620, 505, 1720, 505, { so: 0.35, sw: 6 }) + rect(1950, 520, 14, 340, '#4a4e55') + rect(1932, 470, 50, 120, '#3b3f46', { rx: 8 }) + ell(1957, 495, 12, 12, '#c9663f', { stroke: false }) + ell(1957, 530, 12, 12, '#e0b04e', { stroke: false, op: 0.5 }) + ell(1957, 565, 12, 12, '#7aa36a', { stroke: false, op: 0.5 }));
  // cars on the road
  s += car(300, 1000, 1, '#7f98b0') + car(2600, 1010, 1.05, '#c9a15e');
  return s;
}
export function car(x, y, s = 1, col = '#7f98b0') {
  return wc(pth(`M${x - 170 * s} ${y} L${x - 170 * s} ${y - 60 * s} Q${x - 160 * s} ${y - 80 * s} ${x - 110 * s} ${y - 85 * s} L${x - 70 * s} ${y - 140 * s} L${x + 80 * s} ${y - 140 * s} L${x + 130 * s} ${y - 85 * s} Q${x + 175 * s} ${y - 80 * s} ${x + 175 * s} ${y - 50 * s} L${x + 175 * s} ${y} Z`, col) + poly([[x - 60 * s, y - 130 * s], [x + 5 * s, y - 130 * s], [x + 5 * s, y - 88 * s], [x - 95 * s, y - 88 * s]], '#cfe0e8') + poly([[x + 20 * s, y - 130 * s], [x + 75 * s, y - 130 * s], [x + 115 * s, y - 88 * s], [x + 20 * s, y - 88 * s]], '#cfe0e8') + `<circle cx="${x - 100 * s}" cy="${y}" r="${30 * s}" fill="#2f2f33" stroke="${INK}" stroke-width="2"/><circle cx="${x + 110 * s}" cy="${y}" r="${30 * s}" fill="#2f2f33" stroke="${INK}" stroke-width="2"/>`);
}
/** crowd of extras in depth bands; returns SVG (seeded so every shot of the plaza shows the same crowd) */
export function crowd(band, { x0 = -300, x1 = 3600, seed = 1, skip = [] } = {}) {
  const r = rng(seed);
  const cfg = { far: { y: 840, sc: 30, step: 95, blur: 'b3', op: 0.9 }, mid: { y: 885, sc: 46, step: 150, blur: 'b2', op: 1 }, near: { y: 1075, sc: 92, step: 330, blur: 'b8', op: 1 } }[band];
  const tops = ['#7d93ad', '#b9867a', '#8a9a72', '#c8a97a', '#9a86a8', '#6f7f8f', '#c98f6f', '#a8a08a'];
  const bots = ['#4f5566', '#5b6070', '#6a5a50', '#44505e', '#5f5a68'];
  const accs = [['bag'], ['cap'], ['glasses'], ['tote'], ['id'], [], ['umbrella'], ['phone'], ['hat']];
  let s = '';
  for (let x = x0; x < x1; x += cfg.step * (0.7 + r() * 0.6)) {
    if (skip.some(([a, b]) => x > a && x < b)) continue;
    const walking = r() > 0.4;
    const facing = r() > 0.5 ? 1 : -1;
    const pz = walking ? { view: 'side', facing, lean: 4, legR: { a1: 20, a2: 6 }, legL: { a1: -18, a2: -36, foot: 26 }, armR: { a1: -22, a2: -6 }, armL: { a1: 22, a2: 46 }, hip: [0, 0.07] } : {};
    const a = accs[Math.floor(r() * accs.length)];
    s += extra({ ...pz, x, y: cfg.y + (r() - 0.5) * 18, scale: cfg.sc * (0.92 + r() * 0.16), armR: a[0] === 'umbrella' || a[0] === 'phone' ? { a1: 20, a2: 150 } : pz.armR }, { top: tops[Math.floor(r() * tops.length)], bottom: bots[Math.floor(r() * bots.length)], acc: a, blur: cfg.blur, op: cfg.op });
  }
  return s;
}

// ---------------------------------------------------------------- E06 neighbourhood park (2400 wide)
export const PARK = { groundY: 880, benchX: 1200, benchSeat: 770 };
export function park(light = 'afternoon') {
  let s = sky(-600, -400, 3600, 1300, light);
  s += wc(rect(-600, 600, 3600, 300, '#9db08a', { stroke: false }) + ell(400, 640, 700, 90, '#a8ba92', { stroke: false }) + ell(1900, 650, 800, 100, '#a3b68d', { stroke: false }), true);
  // low fence at the back
  let f = '';
  for (let x = -600; x < 3000; x += 70) f += rect(x, 690, 14, 70, '#e6dcc6', { sw: 1.4 });
  f += rect(-600, 705, 3600, 10, '#e6dcc6', { sw: 1.4 }) + rect(-600, 735, 3600, 10, '#e6dcc6', { sw: 1.4 });
  s += wc(f);
  for (const [x, sc] of [[-150, 1.3], [520, 1.15], [1820, 1.25], [2500, 1.1]]) s += tree(x, 770, sc, 'day', { seed: x + 11, leaf: '#7f9a62', leaf2: '#65804f' });
  s += bush(160, 790, 1.2) + bush(980, 780, 0.9) + bush(1560, 790, 1.1) + bush(2250, 790, 1.2);
  // grass + paving path
  s += wc(rect(-600, 760, 3600, 700, '#a6b98c', { stroke: false }) + pth(`M-600 980 Q600 860 1200 900 Q1800 940 3000 860 L3000 1000 Q1800 1080 1200 1040 Q600 1000 -600 1120 Z`, '#d8c9a6'), true);
  // bench (centre), second bench, lamp, bin
  s += bench(PARK.benchX, 880, 0.72) + bench(2150, 900, 0.62) + wc(rect(1590, 380, 12, 500, '#4a4e55') + pth(`M1570 380 L1620 380 L1610 340 L1580 340 Z`, '#4a4e55') + rect(1440, 800, 70, 90, '#6f7f6a', { rx: 6 }) + rect(1434, 792, 82, 14, '#5d6b58'));
  return s;
}
export function bench(x, y, s = 1) {
  return wc(rect(x - 230 * s, y - 112 * s, 460 * s, 20 * s, '#a07a55') + rect(x - 230 * s, y - 200 * s, 460 * s, 18 * s, '#a07a55') + rect(x - 230 * s, y - 168 * s, 460 * s, 18 * s, '#a07a55') + rect(x - 210 * s, y - 210 * s, 14 * s, 210 * s, '#4a4e55') + rect(x + 196 * s, y - 210 * s, 14 * s, 210 * s, '#4a4e55'));
}

// ---------------------------------------------------------------- E07 house yard with a cat (1920 wide)
export const YARD = { groundY: 900, bowl: [1180, 905], porchX: 1300 };
export function yard(light = 'afternoon') {
  let s = sky(-400, -300, 2700, 1100, light);
  // neighbour wall + fence at the back
  s += wc(rect(-400, 520, 2700, 300, '#d8ccb2') + [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map((k) => ln(-400 + k * 200, 520, -400 + k * 200, 820, { so: 0.2 })).join(''));
  s += tree(200, 700, 0.9, 'day', { seed: 77 }) + tree(820, 690, 0.75, 'day', { seed: 78 });
  let f = '';
  for (let x = -400; x < 1300; x += 26) f += ln(x, 820, x, 700, { sw: 3, stroke: '#3f3a36', so: 0.8 });
  f += ln(-400, 708, 1300, 708, { sw: 4, stroke: '#3f3a36' }) + rect(-400, 800, 1700, 30, '#cfc2a8');
  s += wc(f);
  // grass
  s += wc(rect(-400, 820, 2700, 500, '#9fb487', { stroke: false }) + [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19].map((k) => pth(`M${-300 + k * 90} 1010 l6 -24 l6 22 l8 -18 l4 20`, 'none', { stroke: '#5f7a4c', so: 0.6, sw: 2 })).join(''), true);
  // house corner + porch (teras) on the right
  s += wc(rect(1300, 260, 1000, 600, '#e8dcc2') + poly([[1260, 270], [1800, 120], [2340, 270]], '#9b5f4c') + rect(1460, 470, 200, 390, '#8e6a4c') + rect(1760, 430, 260, 220, '#9fb6c8') + ln(1890, 430, 1890, 650, { sw: 6, stroke: '#efe6d2', so: 1 }) + rect(1240, 860, 1100, 50, '#c9b8a0') + [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((k) => ln(1240 + k * 100, 860, 1240 + k * 100, 910, { so: 0.25 })).join('') + rect(1470, 848, 180, 18, '#b0635a', { rx: 4 }));
  s += pot(1330, 862, 1.2) + pot(2080, 862, 1.1, '#7f9a5e', '#a8684a') + pot(160, 905, 1.3);
  // cat bowl
  s += wc(ell(YARD.bowl[0], YARD.bowl[1], 46, 14, '#6f8fa8') + pth(`M${YARD.bowl[0] - 46} ${YARD.bowl[1]} L${YARD.bowl[0] - 36} ${YARD.bowl[1] + 22} L${YARD.bowl[0] + 36} ${YARD.bowl[1] + 22} L${YARD.bowl[0] + 46} ${YARD.bowl[1]} Z`, '#6f8fa8') + ell(YARD.bowl[0], YARD.bowl[1] - 2, 36, 8, '#b98b55', { stroke: false }));
  return s;
}

// ---------------------------------------------------------------- the cat (behaviour, not text)
export function cat(x, y, s = 1, mode = 'sit', facing = 1, o = {}) {
  const f = facing;
  const C = o.col || '#d39a5c';
  const D = '#a8703f';
  const X = (v) => x + v * s * f;
  const Y = (v) => y + v * s;
  let k = '';
  if (mode === 'sit') {
    k += pth(`M${X(-40)} ${Y(0)} Q${X(-60)} ${Y(-70)} ${X(-20)} ${Y(-110)} L${X(30)} ${Y(-110)} Q${X(50)} ${Y(-60)} ${X(40)} ${Y(0)} Z`, C);
    k += pth(`M${X(-40)} ${Y(-6)} Q${X(-110)} ${Y(-10)} ${X(-100)} ${Y(-60)}`, 'none', { sw: 14 * s, stroke: INK, so: 1 }) + pth(`M${X(-40)} ${Y(-6)} Q${X(-110)} ${Y(-10)} ${X(-100)} ${Y(-60)}`, 'none', { sw: 9 * s, stroke: C, so: 1 });
    k += ell(X(5), Y(-140), 42 * s, 38 * s, C) + poly([[X(-30), Y(-160)], [X(-24), Y(-200)], [X(-4), Y(-170)]], C) + poly([[X(14), Y(-172)], [X(34), Y(-200)], [X(40), Y(-158)]], C);
    for (const dy of [-60, -80]) k += pth(`M${X(-35)} ${Y(dy)} q20 -6 30 4`, 'none', { stroke: D, sw: 4 * s, so: 0.9 });
    const lx = o.lookAway ? 18 : 10;
    k += ell(X(lx - 12), Y(-142), 4 * s, 6 * s, INK, { stroke: false }) + ell(X(lx + 14), Y(-142), 4 * s, 6 * s, INK, { stroke: false }) + ell(X(lx + 1), Y(-128), 5 * s, 3.5 * s, '#b0635a', { stroke: false });
    k += ln(X(-10), Y(0), X(-8), Y(-40), { sw: 2 * s }) + ln(X(20), Y(0), X(18), Y(-40), { sw: 2 * s });
  } else {
    // walking away, side view
    k += pth(`M${X(-80)} ${Y(-70)} Q${X(0)} ${Y(-95)} ${X(70)} ${Y(-72)} Q${X(85)} ${Y(-40)} ${X(60)} ${Y(-38)} L${X(-70)} ${Y(-38)} Q${X(-95)} ${Y(-48)} ${X(-80)} ${Y(-70)} Z`, C);
    for (const [a, b] of [[-60, -50], [-40, -30], [40, 50], [58, 66]]) k += ln(X(a), Y(-42), X(b), Y(0), { sw: 9 * s, stroke: INK, so: 1 }) + ln(X(a), Y(-42), X(b), Y(0), { sw: 5 * s, stroke: C, so: 1 });
    k += pth(`M${X(-80)} ${Y(-68)} Q${X(-130)} ${Y(-110)} ${X(-110)} ${Y(-160)}`, 'none', { sw: 13 * s, stroke: INK, so: 1 }) + pth(`M${X(-80)} ${Y(-68)} Q${X(-130)} ${Y(-110)} ${X(-110)} ${Y(-160)}`, 'none', { sw: 8 * s, stroke: C, so: 1 });
    k += ell(X(92), Y(-92), 34 * s, 30 * s, C) + poly([[X(78), Y(-116)], [X(82), Y(-146)], [X(98), Y(-120)]], C) + poly([[X(100), Y(-120)], [X(118), Y(-146)], [X(120), Y(-108)]], C) + ell(X(110), Y(-94), 3.5 * s, 5 * s, INK, { stroke: false });
    for (const dx of [-30, 0, 30]) k += pth(`M${X(dx)} ${Y(-88)} q6 14 0 26`, 'none', { stroke: D, sw: 4 * s, so: 0.9 });
  }
  const shadow = ell(x, y + 2, 70 * s, 9 * s, '#6e5a44', { stroke: false, op: 0.3 });
  return shadow + wc(k);
}
