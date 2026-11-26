// EP004 storyboard frames: painterly ink-and-watercolour world drawn in SVG.
// Every location is ONE master layout (world coordinates, 1 unit = 1 px of a 1920x1080 wide frame);
// a shot is a virtual camera on that master (centre, zoom, roll) plus a background blur for depth (2.5D).
// Milo comes from the approved rig (rig/milo.mjs). Extras ("figuran") use the same base body with no face.
import { drawMilo, miloParts, renderParts, pose } from './rig/milo.mjs';
import * as P from './rig/props.mjs';

export const W = 1920;
export const H = 1080;
export const INK = '#2b241e';
const n = (v) => +(+v).toFixed(2);

// ---------------------------------------------------------------- filters, grade, paper
export function worldDefs() {
  const blur = (id, s) => `<filter id="${id}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="${s}"/></filter>`;
  return `
<filter id="wc" x="-3%" y="-3%" width="106%" height="106%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.016" numOctaves="3" seed="4" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feGaussianBlur in="d" stdDeviation="0.55"/>
</filter>
<filter id="wcBig" x="-3%" y="-3%" width="106%" height="106%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.008" numOctaves="3" seed="9" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="16" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feGaussianBlur in="d" stdDeviation="1.2"/>
</filter>
${blur('b1', 1.2)}${blur('b2', 2.5)}${blur('b3', 4)}${blur('b5', 6)}${blur('b8', 9)}${blur('b12', 13)}
<filter id="glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="30"/></filter>
<filter id="glowS" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="9"/></filter>
<filter id="paper" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="11"/>
  <feColorMatrix type="matrix" values="0 0 0 0 0.42  0 0 0 0 0.35  0 0 0 0 0.27  0 0 0 0.55 -0.12"/>
</filter>
<filter id="bloom" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.0035" numOctaves="3" seed="23"/>
  <feColorMatrix type="matrix" values="0 0 0 0 0.45  0 0 0 0 0.36  0 0 0 0 0.28  0 0 0 0.6 -0.22"/>
</filter>
<radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="55%" stop-color="#1c140c" stop-opacity="0"/><stop offset="100%" stop-color="#1c140c" stop-opacity="0.55"/></radialGradient>
<radialGradient id="warmGlow"><stop offset="0%" stop-color="#ffd48a" stop-opacity="0.95"/><stop offset="100%" stop-color="#ffb860" stop-opacity="0"/></radialGradient>
<radialGradient id="screenGlow"><stop offset="0%" stop-color="#bfe0ff" stop-opacity="0.9"/><stop offset="100%" stop-color="#7fb2ff" stop-opacity="0"/></radialGradient>
<radialGradient id="sigGlow"><stop offset="0%" stop-color="#d9c6ff" stop-opacity="0.95"/><stop offset="45%" stop-color="#8f7cff" stop-opacity="0.45"/><stop offset="100%" stop-color="#5aa8ff" stop-opacity="0"/></radialGradient>
<linearGradient id="sunBeam" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fff2c6" stop-opacity="0.75"/><stop offset="100%" stop-color="#ffe0a0" stop-opacity="0.15"/></linearGradient>`;
}

/** colour grade + paper grain + vignette, drawn over the whole frame */
export function finish(light = 'day', { vignette = 1, dark = 0 } = {}) {
  const L = LIGHT[light];
  return `<rect width="${W}" height="${H}" fill="${L.tint}" opacity="${L.tintOp}" style="mix-blend-mode:multiply"/>
<rect width="${W}" height="${H}" filter="url(#bloom)" style="mix-blend-mode:multiply" opacity="0.7"/>
<rect width="${W}" height="${H}" filter="url(#paper)" style="mix-blend-mode:multiply" opacity="0.55"/>
<rect width="${W}" height="${H}" fill="url(#vig)" opacity="${vignette}"/>
${dark ? `<rect width="${W}" height="${H}" fill="#07060a" opacity="${dark}"/>` : ''}`;
}

export const LIGHT = {
  night: { sky: ['#1b2442', '#34446c'], wall: '#4a5270', wall2: '#3c4462', floor: '#5a5064', floor2: '#463f52', tint: '#2a3358', tintOp: 0.32, sun: null },
  morning: { sky: ['#a9cbe2', '#f2e2c0'], wall: '#eadbc0', wall2: '#dfcba8', floor: '#c9a47b', floor2: '#b88f66', tint: '#ffd795', tintOp: 0.07, sun: '#fff1c4' },
  day: { sky: ['#9fc4dd', '#e8e0c8'], wall: '#e9dcc3', wall2: '#dccaa8', floor: '#c8a57d', floor2: '#b79068', tint: '#f6e0b0', tintOp: 0.05, sun: '#fff4d2' },
  afternoon: { sky: ['#a4c0d4', '#f1d2a2'], wall: '#e6cfaa', wall2: '#d8bb92', floor: '#c49b6e', floor2: '#ad845c', tint: '#f3b06a', tintOp: 0.13, sun: '#ffd99a' },
  dusk: { sky: ['#4f4f7e', '#e9a477'], wall: '#b88f86', wall2: '#9f7a76', floor: '#8f6f6c', floor2: '#77595a', tint: '#6d4f86', tintOp: 0.2, sun: '#ffb27a' },
  dim: { sky: ['#6a6e8a', '#d9a982'], wall: '#9b8a86', wall2: '#887775', floor: '#7d6a66', floor2: '#695855', tint: '#4b3f62', tintOp: 0.25, sun: '#ffb27a' },
};

// ---------------------------------------------------------------- shape helpers (watercolour fill + soft ink)
const stroke = (o) => (o.stroke === false ? '' : ` stroke="${o.stroke || INK}" stroke-width="${o.sw ?? 2.2}" stroke-opacity="${o.so ?? 0.72}" stroke-linejoin="round" stroke-linecap="round"`);
const opa = (o) => (o.op != null ? ` opacity="${o.op}"` : '');
export const poly = (pts, fill, o = {}) => `<path d="M${pts.map((p) => `${n(p[0])} ${n(p[1])}`).join(' L')}Z" fill="${fill}"${stroke(o)}${opa(o)}/>`;
export const rect = (x, y, w, h, fill, o = {}) => `<rect x="${n(x)}" y="${n(y)}" width="${n(w)}" height="${n(h)}" rx="${o.rx || 0}" fill="${fill}"${stroke(o)}${opa(o)}/>`;
export const ell = (cx, cy, rx, ry, fill, o = {}) => `<ellipse cx="${n(cx)}" cy="${n(cy)}" rx="${n(rx)}" ry="${n(ry)}" fill="${fill}"${stroke(o)}${opa(o)}/>`;
export const pth = (d, fill = 'none', o = {}) => `<path d="${d}" fill="${fill}"${stroke(o)}${opa(o)}/>`;
export const ln = (x1, y1, x2, y2, o = {}) => `<path d="M${n(x1)} ${n(y1)} L${n(x2)} ${n(y2)}" fill="none"${stroke({ sw: 2.2, ...o })}${opa(o)}/>`;
export const g = (inner, attrs = '') => `<g ${attrs}>${inner}</g>`;
export const wc = (inner, big = false) => `<g filter="url(#${big ? 'wcBig' : 'wc'})">${inner}</g>`;
const lerp = (a, b, t) => a + (b - a) * t;
// deterministic pseudo-random
export function rng(seed = 1) {
  let s = seed >>> 0;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}
function skyRect(x, y, w, h, light, id) {
  const L = LIGHT[light];
  return `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${L.sky[0]}"/><stop offset="100%" stop-color="${L.sky[1]}"/></linearGradient></defs><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${id})"/>`;
}
let GID = 0;
const uid = (p) => `${p}${GID++}`;

// ---------------------------------------------------------------- shared props
export function tree(x, groundY, s = 1, light = 'day', o = {}) {
  const r = rng(o.seed || Math.round(x));
  const leaf = o.leaf || (light === 'night' ? '#2f4a4a' : light === 'dusk' ? '#4f5a52' : '#7d9a66');
  const leaf2 = o.leaf2 || (light === 'night' ? '#253c3e' : light === 'dusk' ? '#3f4a46' : '#62804f');
  let blobs = '';
  for (let i = 0; i < 9; i++) {
    const a = (i / 9) * Math.PI * 2;
    blobs += ell(x + Math.cos(a) * 95 * s * (0.6 + r() * 0.5), groundY - 330 * s + Math.sin(a) * 70 * s, (70 + r() * 40) * s, (60 + r() * 30) * s, i % 2 ? leaf : leaf2, { so: 0.35 });
  }
  return wc(poly([[x - 14 * s, groundY], [x - 9 * s, groundY - 260 * s], [x + 9 * s, groundY - 260 * s], [x + 16 * s, groundY]], '#7a5a3f', { so: 0.6 }) + blobs + ell(x, groundY - 340 * s, 105 * s, 90 * s, leaf, { so: 0.3, op: 0.85 }));
}
export function bush(x, y, s = 1, col = '#738f5c') {
  return wc(ell(x - 40 * s, y - 30 * s, 55 * s, 40 * s, col, { so: 0.4 }) + ell(x + 30 * s, y - 34 * s, 60 * s, 45 * s, col, { so: 0.4 }) + ell(x, y - 55 * s, 50 * s, 40 * s, '#86a26b', { so: 0.4 }));
}
export function pot(x, y, s = 1, plant = '#6f8f58', col = '#b8714f') {
  return wc(poly([[x - 26 * s, y - 48 * s], [x + 26 * s, y - 48 * s], [x + 19 * s, y], [x - 19 * s, y]], col) + ell(x - 12 * s, y - 70 * s, 18 * s, 28 * s, plant, { so: 0.5 }) + ell(x + 12 * s, y - 74 * s, 17 * s, 30 * s, plant, { so: 0.5 }) + ell(x, y - 88 * s, 14 * s, 26 * s, '#83a368', { so: 0.5 }));
}
export function phoneProp(x, y, s = 1, deg = 0, screen = '#86a9c9', glow = false) {
  return `${glow ? `<circle cx="${x}" cy="${y}" r="${70 * s}" fill="url(#screenGlow)" opacity="0.7"/>` : ''}<g transform="translate(${n(x)} ${n(y)}) rotate(${deg})">${rect(-11 * s, -19 * s, 22 * s, 38 * s, '#2f333a', { rx: 4 * s, sw: 1.6 })}${rect(-8.5 * s, -15.5 * s, 17 * s, 29 * s, screen, { rx: 2 * s, stroke: false })}</g>`;
}

// ---------------------------------------------------------------- E01 / E02: Milo's room (one master layout)
export const ROOM = { floorY: 760, bedTop: 688, bedFront: 800, bedX0: 300, bedX1: 960, deskTop: 640, deskX0: 1380, deskX1: 1840, phoneDesk: [1600, 628], lamp: [1470, 640], win: [960, 200, 330, 360] };
export function room(light = 'night', o = {}) {
  const L = LIGHT[light];
  const R = ROOM;
  const night = light === 'night';
  const [wx, wy, ww, wh] = R.win;
  let s = '';
  // wall + floor
  s += rect(-400, -200, 2720, R.floorY + 200, L.wall, { stroke: false });
  s += rect(-400, 0, 2720, 90, L.wall2, { stroke: false, op: 0.5 });
  s += poly([[-400, R.floorY], [2320, R.floorY], [2320, 1300], [-400, 1300]], L.floor, { stroke: false });
  for (let i = 0; i < 9; i++) s += ln(-400, R.floorY + 30 + i * i * 9, 2320, R.floorY + 30 + i * i * 9, { so: 0.12, sw: 1.5 });
  s += rect(-400, R.floorY - 14, 2720, 14, L.wall2, { so: 0.4 });
  // window: sky, neighbourhood outside, frame, curtains
  s += skyRect(wx, wy, ww, wh, light, uid('rsky'));
  if (night) {
    s += `<circle cx="${wx + 250}" cy="${wy + 70}" r="26" fill="#f4ecd0" opacity="0.95"/><circle cx="${wx + 250}" cy="${wy + 70}" r="60" fill="#f4ecd0" opacity="0.15"/>`;
    s += poly([[wx, wy + 270], [wx + 60, wy + 230], [wx + 120, wy + 262], [wx + 190, wy + 220], [wx + 260, wy + 255], [wx + ww, wy + 235], [wx + ww, wy + wh], [wx, wy + wh]], '#1e2740', { stroke: false });
    s += rect(wx + 70, wy + 280, 14, 12, '#f2c27a', { stroke: false }) + rect(wx + 210, wy + 268, 12, 12, '#f2c27a', { stroke: false, op: 0.8 });
  } else {
    s += tree(wx + 70, wy + wh + 40, 0.55, light) + poly([[wx + 150, wy + wh], [wx + 150, wy + 210], [wx + 230, wy + 160], [wx + 310, wy + 210], [wx + 310, wy + wh]], '#e3c9a3') + poly([[wx + 140, wy + 215], [wx + 230, wy + 150], [wx + 320, wy + 215]], '#b8735a');
    s += rect(wx + 200, wy + 250, 40, 40, '#9fb6c8');
  }
  s += rect(wx - 14, wy - 14, ww + 28, wh + 28, 'none', { sw: 14, stroke: '#e9e0cf', so: 1 }) + rect(wx - 14, wy - 14, ww + 28, wh + 28, 'none', { sw: 2.2 });
  s += ln(wx + ww / 2, wy, wx + ww / 2, wy + wh, { sw: 9, stroke: '#e9e0cf', so: 1 }) + ln(wx, wy + wh / 2, wx + ww, wy + wh / 2, { sw: 9, stroke: '#e9e0cf', so: 1 });
  s += rect(wx - 40, wy + wh + 8, ww + 80, 18, '#e9e0cf');
  const cur = night ? '#5c6b90' : '#8aa0c4';
  const sway = o.curtain || 0;
  s += pth(`M${wx - 70} ${wy - 40} L${wx + 60} ${wy - 40} Q${wx + 40 + sway} ${wy + 200} ${wx + 70 + sway * 1.6} ${wy + wh + 60} L${wx - 80} ${wy + wh + 60} Z`, cur);
  s += pth(`M${wx + ww + 70} ${wy - 40} L${wx + ww - 60} ${wy - 40} Q${wx + ww - 40 + sway} ${wy + 200} ${wx + ww - 70 + sway * 1.6} ${wy + wh + 60} L${wx + ww + 80} ${wy + wh + 60} Z`, cur);
  s += ln(wx - 90, wy - 44, wx + ww + 90, wy - 44, { sw: 6 });
  // wall frames + shelf with books above the desk
  s += rect(560, 300, 140, 110, '#e8dcc6') + rect(575, 315, 110, 80, night ? '#6f7f8f' : '#a9c1b4', { so: 0.4 });
  s += rect(1430, 410, 360, 16, '#9b7652');
  const bk = ['#b46a55', '#6f8fa8', '#d1a65e', '#7b9a6a', '#a77a9c', '#c98f5c'];
  for (let i = 0; i < 9; i++) s += rect(1450 + i * 28, 410 - (60 + (i % 3) * 12), 22, 60 + (i % 3) * 12, bk[i % bk.length], { sw: 1.6 });
  // wardrobe (left)
  s += rect(40, 250, 300, 530, '#a98261') + ln(190, 270, 190, 760, { sw: 2 }) + ell(175, 520, 6, 6, INK, { stroke: false }) + ell(205, 520, 6, 6, INK, { stroke: false }) + rect(30, 236, 320, 22, '#946f50');
  s += rect(70, 200, 90, 36, '#c9b48e') + rect(190, 210, 70, 26, '#b4917a');
  // bed
  s += rect(R.bedX0 - 30, 470, 46, R.bedFront - 470, '#8e6a4c', { rx: 8 });
  s += rect(R.bedX0, R.bedTop, R.bedX1 - R.bedX0, R.bedFront - R.bedTop, '#f0e8d8');
  s += rect(R.bedX0, R.bedTop + 22, R.bedX1 - R.bedX0, R.bedFront - R.bedTop - 22, '#9b7a5b', { op: 0.25, stroke: false });
  s += rect(R.bedX0 - 6, R.bedFront, R.bedX1 - R.bedX0 + 12, 30, '#8e6a4c');
  s += rect(R.bedX1 - 18, R.bedTop - 40, 30, R.bedFront - R.bedTop + 70, '#8e6a4c', { rx: 6 });
  if (!o.noPillow) s += ell(R.bedX0 + 95, R.bedTop - 26, 95, 36, '#f6f1e6');
  // desk, chair, lamp, books
  s += rect(R.deskX0, R.deskTop, R.deskX1 - R.deskX0, 22, '#a07a55') + rect(R.deskX0 + 20, R.deskTop + 22, 20, 210, '#8a6646') + rect(R.deskX1 - 40, R.deskTop + 22, 20, 210, '#8a6646') + rect(R.deskX1 - 190, R.deskTop + 22, 150, 90, '#9a7450');
  s += rect(1715, R.deskTop - 34, 90, 16, '#6f8fa8', { sw: 1.6 }) + rect(1722, R.deskTop - 18, 80, 18, '#c98f5c', { sw: 1.6 });
  s += rect(1530, 700, 150, 18, '#7d5e43') + rect(1540, 560, 14, 150, '#7d5e43') + rect(1540, 556, 130, 30, '#8e6a4c', { rx: 6 }) + rect(1545, 718, 12, 140, '#6d523a') + rect(1655, 718, 12, 140, '#6d523a');
  const [lx, ly] = R.lamp;
  s += rect(lx - 32, ly - 10, 64, 10, '#3f4650') + ln(lx, ly - 10, lx + 26, ly - 110, { sw: 6, stroke: '#3f4650', so: 1 }) + poly([[lx + 2, ly - 112], [lx + 70, ly - 140], [lx + 60, ly - 92], [lx + 20, ly - 90]], night ? '#f0cf8c' : '#d9c39a');
  // rug
  s += ell(1180, 930, 260, 60, night ? '#7a6175' : '#c98f6f', { op: 0.85 });
  // light
  if (night) {
    s += `<circle cx="${lx + 50}" cy="${ly - 60}" r="360" fill="url(#warmGlow)" opacity="${o.lampOff ? 0 : 0.55}" style="mix-blend-mode:screen"/>`;
    s += poly([[wx - 20, R.floorY + 10], [wx + ww + 20, R.floorY + 10], [wx + ww + 160, 1080], [wx - 120, 1080]], '#7b8fc4', { stroke: false, op: 0.18 });
  } else if (L.sun) {
    s += poly([[wx, wy + wh + 20], [wx + ww, wy + wh + 20], [wx + ww - 120, R.floorY + 260], [wx - 420, R.floorY + 260]], 'url(#sunBeam)', { stroke: false, op: light === 'dusk' ? 0.35 : 0.65 });
    s += poly([[wx - 30, R.bedTop + 4], [wx + 20, R.bedTop + 4], [wx - 200, R.bedFront], [wx - 310, R.bedFront]], L.sun, { stroke: false, op: 0.45 });
  }
  return wc(s);
}
/** blanket over the bed (drawn in front of Milo's legs) */
export function blanket(light = 'night', x0 = 560, x1 = 960, top = ROOM.bedTop - 10) {
  const c = light === 'night' ? '#5d6f98' : '#7f98c2';
  return wc(pth(`M${x0} ${top + 30} Q${(x0 + x1) / 2} ${top - 18} ${x1 + 10} ${top + 8} L${x1 + 14} ${ROOM.bedFront + 12} L${x0 - 30} ${ROOM.bedFront + 12} Q${x0 - 50} ${top + 70} ${x0} ${top + 30} Z`, c) + pth(`M${x0 + 60} ${top + 40} Q${x0 + 160} ${top + 70} ${x0 + 240} ${top + 50}`, 'none', { so: 0.35 }));
}

// ---------------------------------------------------------------- extras: same base body, no face, clothes + accessories
const lighten = (hex, k) => {
  const c = parseInt(hex.slice(1), 16);
  const ch = (v) => Math.round(lerp(v, 255, k));
  return `#${[(c >> 16) & 255, (c >> 8) & 255, c & 255].map((v) => ch(v).toString(16).padStart(2, '0')).join('')}`;
};
export function extra(pz, o = {}) {
  const p = pose(pz);
  const built = miloParts(p);
  const top = o.top || '#8796a8';
  const bottom = o.bottom || '#5b6070';
  const sleeves = o.sleeves !== false;
  for (const q of built.parts) {
    if (q.detail !== undefined && q.tf) q.detail = ''; // head: no face
    else if (q.htag) continue; // hands stay bare
    else if (q.tag) { if (sleeves) q.fill = top; }
    else if (q.shapes && !q.tf) q.fill = top; // torso
    else if (q.tubes && !q.tf) q.fill = bottom; // legs
  }
  const flip = p.view === 'side' && p.facing === -1 ? -1 : 1;
  const J = built.joints;
  const acc = (o.acc || []).map((a) => accessory(a, J, built.p, o)).join('');
  const shadow = `<ellipse cx="0" cy="0.02" rx="1.05" ry="0.13" fill="#6e5a44" opacity="0.35"/>`;
  const body = `<g transform="translate(${n(p.x)} ${n(p.y)})"><g filter="url(#miloWobble)"><g transform="scale(${n(p.scale * flip)} ${n(p.scale)})">${p.shadow === false ? '' : shadow}${renderParts(built.parts)}${acc}</g></g></g>`;
  const blur = o.blur ? `filter="url(#${o.blur})"` : '';
  return `<g ${blur} opacity="${o.op ?? 1}">${body}</g>`;
}
function accessory(kind, J, p, o) {
  const h = J.headC;
  const k = INK;
  const lw = 0.05;
  const side = p.view === 'side';
  switch (kind) {
    case 'cap': return `<path d="M${h[0] - 0.95} ${h[1] - 0.25} Q${h[0]} ${h[1] - 1.45} ${h[0] + 0.95} ${h[1] - 0.25} Z" fill="${o.cap || '#c2874f'}" stroke="${k}" stroke-width="${lw}"/><path d="M${h[0] + (side ? 0.6 : 0.3)} ${h[1] - 0.3} L${h[0] + (side ? 1.55 : 1.2)} ${h[1] - 0.2}" stroke="${o.cap || '#c2874f'}" stroke-width="0.18" stroke-linecap="round"/>`;
    case 'hat': return `<ellipse cx="${h[0]}" cy="${h[1] - 0.55}" rx="1.35" ry="0.22" fill="${o.hat || '#d8c08a'}" stroke="${k}" stroke-width="${lw}"/><path d="M${h[0] - 0.7} ${h[1] - 0.6} Q${h[0]} ${h[1] - 1.5} ${h[0] + 0.7} ${h[1] - 0.6} Z" fill="${o.hat || '#d8c08a'}" stroke="${k}" stroke-width="${lw}"/>`;
    case 'glasses': return side ? `<circle cx="${h[0] + 0.6}" cy="${h[1] + 0.05}" r="0.2" fill="none" stroke="${k}" stroke-width="0.06"/>` : `<circle cx="${h[0] - 0.34}" cy="${h[1] + 0.05}" r="0.22" fill="none" stroke="${k}" stroke-width="0.06"/><circle cx="${h[0] + 0.34}" cy="${h[1] + 0.05}" r="0.22" fill="none" stroke="${k}" stroke-width="0.06"/><path d="M${h[0] - 0.12} ${h[1] + 0.03} L${h[0] + 0.12} ${h[1] + 0.03}" stroke="${k}" stroke-width="0.05"/>`;
    case 'apron': {
      const a = J.shL; const b = J.shR; const cy = (J.hipL[1] + J.hipR[1]) / 2;
      const cx = (a[0] + b[0]) / 2;
      return `<path d="M${cx - 0.3} ${a[1] + 0.25} L${cx + 0.3} ${a[1] + 0.25} L${cx + 0.45} ${cy + 0.55} L${cx - 0.45} ${cy + 0.55} Z" fill="${o.apron || '#c9a77a'}" stroke="${k}" stroke-width="${lw}"/>`;
    }
    case 'id': { const c = [(J.shL[0] + J.shR[0]) / 2 + (side ? 0.2 : 0.12), J.shL[1] + 0.75]; return `<path d="M${c[0] - 0.18} ${J.shL[1] + 0.05} L${c[0]} ${c[1] - 0.18} L${c[0] + 0.18} ${J.shL[1] + 0.05}" fill="none" stroke="#3d5a8a" stroke-width="0.04"/><rect x="${c[0] - 0.13}" y="${c[1] - 0.17}" width="0.26" height="0.34" rx="0.03" fill="#f3efe4" stroke="${k}" stroke-width="0.035"/>`; }
    case 'bag': { const hp = side ? J.hipR : J.hipR; return `<path d="M${J.shL[0]} ${J.shL[1]} L${hp[0] + 0.25} ${hp[1] - 0.1}" stroke="#6a4a36" stroke-width="0.07"/><rect x="${hp[0] + 0.05}" y="${hp[1] - 0.2}" width="0.6" height="0.5" rx="0.07" fill="${o.bag || '#9a6a48'}" stroke="${k}" stroke-width="${lw}"/>`; }
    case 'tote': { const w = J.wristR; return `<path d="M${w[0] - 0.12} ${w[1] + 0.1} Q${w[0]} ${w[1] - 0.15} ${w[0] + 0.12} ${w[1] + 0.1}" fill="none" stroke="${k}" stroke-width="0.05"/><path d="M${w[0] - 0.32} ${w[1] + 0.12} L${w[0] + 0.32} ${w[1] + 0.12} L${w[0] + 0.26} ${w[1] + 0.8} L${w[0] - 0.26} ${w[1] + 0.8} Z" fill="${o.bag || '#e2d3b0'}" stroke="${k}" stroke-width="${lw}"/>${o.bread ? `<ellipse cx="${w[0] + 0.05}" cy="${w[1] + 0.12}" rx="0.12" ry="0.32" transform="rotate(20 ${w[0]} ${w[1]})" fill="#d6a35e" stroke="${k}" stroke-width="0.035"/>` : ''}`; }
    case 'umbrella': { const w = J.wristR; return `<path d="M${w[0]} ${w[1]} L${w[0]} ${w[1] - 2.4}" stroke="${k}" stroke-width="0.06"/><path d="M${w[0] - 1.3} ${w[1] - 2.2} Q${w[0]} ${w[1] - 3.4} ${w[0] + 1.3} ${w[1] - 2.2} Z" fill="${o.umb || '#8aa0c4'}" stroke="${k}" stroke-width="${lw}"/>`; }
    case 'phone': { const w = J.handR; return `<rect x="${w[0] - 0.12}" y="${w[1] - 0.22}" width="0.24" height="0.4" rx="0.04" fill="#2f333a" stroke="${k}" stroke-width="0.03"/>`; }
    case 'hose': { const w = J.handR; return `<path d="M${w[0]} ${w[1]} Q${w[0] + 0.6} ${w[1] + 0.1} ${w[0] + 0.85} ${w[1] - 0.2}" fill="none" stroke="#5f8a5a" stroke-width="0.12" stroke-linecap="round"/><path d="M${w[0] + 0.9} ${w[1] - 0.15} q0.4 0.3 0.5 1.0 M${w[0] + 0.95} ${w[1] - 0.1} q0.3 0.4 0.25 1.1" fill="none" stroke="#9fc7e6" stroke-width="0.05" stroke-linecap="round"/>`; }
    case 'can': { const w = J.handR; return `<path d="M${w[0] - 0.1} ${w[1] - 0.25} L${w[0] + 0.45} ${w[1] - 0.25} L${w[0] + 0.4} ${w[1] + 0.25} L${w[0] - 0.05} ${w[1] + 0.25} Z" fill="#7f9db0" stroke="${k}" stroke-width="${lw}"/><path d="M${w[0] + 0.42} ${w[1] - 0.1} L${w[0] + 0.85} ${w[1] - 0.4}" stroke="#7f9db0" stroke-width="0.1"/><path d="M${w[0] + 0.88} ${w[1] - 0.38} q0.15 0.35 0.05 0.9 M${w[0] + 0.92} ${w[1] - 0.36} q0.3 0.3 0.3 0.85" fill="none" stroke="#9fc7e6" stroke-width="0.04"/>`; }
    default: return '';
  }
}
