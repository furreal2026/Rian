// Props for Milo, drawn in the same ink-and-watercolour style. Every prop is authored in Milo's own figure
// space (1 = head radius, ground at y = 0, facing right), so it can be placed from his joints
// (miloParts(...).joints) and is mirrored / rotated together with him by propLayer().
import { pose, STYLE } from './milo.mjs';

const INK = STYLE.ink;
const LW = 0.05; // prop outline width (head radii)
const f = (n) => +n.toFixed(4);
const P = (pt) => `${f(pt[0])} ${f(pt[1])}`;

export const WOOD = '#b98b55';
export const WOOD_DARK = '#8a6a44';
export const CARD = '#cfa86f';
export const CARD_LIGHT = '#e0c493';
export const METAL = '#a9adb2';
export const DARK = '#3b3f46';

/** Wrap prop SVG (authored in figure space) with the same transform as drawMilo for this pose. */
export function propLayer(pz, inner) {
  const p = pose(pz);
  const flip = p.view === 'side' && p.facing === -1 ? -1 : 1;
  const rot = p.rot ? ` rotate(${f(p.rot)})` : '';
  return `<g transform="translate(${f(p.x)} ${f(p.y)})"><g filter="url(#${p.wobbleId || 'miloWobble'})"><g transform="${rot.trim()} scale(${f(p.scale * flip)} ${f(p.scale)})" stroke-linejoin="round" stroke-linecap="round">${inner}</g></g></g>`;
}

const rect = (x, y, w, h, fill, rx = 0.05) =>
  `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" rx="${rx}" fill="${fill}" stroke="${INK}" stroke-width="${LW}"/>`;
const ln = (a, b, w = LW, col = INK) => `<path d="M${P(a)} L${P(b)}" stroke="${col}" stroke-width="${w}" fill="none"/>`;
/** a round rod with an ink outline (sticks, handles, rope) */
export const rod = (a, b, w = 0.13, fill = WOOD_DARK) => ln(a, b, w + 2 * LW) + ln(a, b, w, fill);
const shade = (x, y, w, h) => `<rect x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(h)}" fill="#000" opacity="0.08"/>`;

/** cardboard box: top-left corner, width, height */
export function box(x, y, w = 1.1, h = 0.95) {
  return (
    rect(x, y, w, h, CARD, 0.04) +
    shade(x + w * 0.72, y + 0.03, w * 0.26, h - 0.06) +
    ln([x + 0.02, y + h * 0.2], [x + w - 0.02, y + h * 0.2], 0.035) +
    `<rect x="${f(x + w * 0.44)}" y="${f(y)}" width="${f(w * 0.12)}" height="${f(h * 0.2)}" fill="${CARD_LIGHT}" stroke="${INK}" stroke-width="0.03"/>`
  );
}

/** wooden crate with an X brace */
export function crate(x, y, w = 1.4, h = 1.3) {
  const i = 0.12;
  return (
    rect(x, y, w, h, WOOD, 0.03) +
    `<rect x="${f(x + i)}" y="${f(y + i)}" width="${f(w - 2 * i)}" height="${f(h - 2 * i)}" fill="none" stroke="${INK}" stroke-width="0.035"/>` +
    ln([x + i, y + i], [x + w - i, y + h - i], 0.1, WOOD_DARK) +
    ln([x + w - i, y + i], [x + i, y + h - i], 0.1, WOOD_DARK) +
    shade(x + w * 0.75, y, w * 0.25, h)
  );
}

/** handbag hanging from a hand point: body below the hand */
export function bag(hand, w = 0.8, h = 0.62) {
  const [hx, hy] = hand;
  const top = hy + 0.32;
  const body = `<path d="M${P([hx - w / 2 + 0.06, top])} L${P([hx + w / 2 - 0.06, top])} L${P([hx + w / 2, top + h])} L${P([hx - w / 2, top + h])}Z" fill="${WOOD}" stroke="${INK}" stroke-width="${LW}"/>`;
  const handle = `<path d="M${P([hx - w / 4, top])} Q${P([hx, hy - 0.22])} ${P([hx + w / 4, top])}" fill="none" stroke="${INK}" stroke-width="0.1"/>`;
  return handle + body + ln([hx - w / 2 + 0.1, top + 0.18], [hx + w / 2 - 0.1, top + 0.18], 0.035);
}

/** backpack on the back: from the shoulder point, behind the torso (side view, facing right) */
export function backpack(shoulder, w = 0.62, h = 1.05) {
  const x = shoulder[0] - 0.42 - w;
  const y = shoulder[1] - 0.05;
  return (
    rect(x, y, w, h, '#9a7548', 0.22) +
    rect(x - 0.08, y + h * 0.45, w * 0.55, h * 0.42, '#86643c', 0.12) +
    `<path d="M${P([x + w - 0.05, y + 0.12])} Q${P([shoulder[0] + 0.1, y - 0.05])} ${P([shoulder[0] + 0.12, y + 0.6])}" fill="none" stroke="${INK}" stroke-width="0.09"/>`
  );
}

/** shovel: handle from a to b, blade at b */
export function shovel(a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const L = Math.hypot(dx, dy);
  const ux = dx / L;
  const uy = dy / L;
  const nx = -uy;
  const ny = ux;
  const c = [b[0] + ux * 0.32, b[1] + uy * 0.32];
  const blade = `<path d="M${P([b[0] + nx * 0.24, b[1] + ny * 0.24])} L${P([b[0] - nx * 0.24, b[1] - ny * 0.24])} Q${P([c[0] - nx * 0.22 + ux * 0.2, c[1] - ny * 0.22 + uy * 0.2])} ${P([c[0] + ux * 0.18, c[1] + uy * 0.18])} Q${P([c[0] + nx * 0.22 + ux * 0.2, c[1] + ny * 0.22 + uy * 0.2])} ${P([b[0] + nx * 0.24, b[1] + ny * 0.24])}Z" fill="${METAL}" stroke="${INK}" stroke-width="${LW}"/>`;
  return rod(a, b, 0.11) + blade;
}

/** hammer: handle from a (grip end) to b, head across b */
export function hammer(a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const L = Math.hypot(dx, dy);
  const nx = -dy / L;
  const ny = dx / L;
  const h1 = [b[0] + nx * 0.28, b[1] + ny * 0.28];
  const h2 = [b[0] - nx * 0.2, b[1] - ny * 0.2];
  return rod(a, b, 0.11) + ln(h1, h2, 0.24 + 2 * LW) + ln(h1, h2, 0.24, METAL);
}

/** flashlight from a (tail) to b (lens), with a beam */
export function flashlight(a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const L = Math.hypot(dx, dy);
  const ux = dx / L;
  const uy = dy / L;
  const nx = -uy;
  const ny = ux;
  const beam = [0.3, 0.55, 0.8]
    .map((s, i) => ln([b[0] + ux * 0.15 + nx * (i - 1) * 0.1, b[1] + uy * 0.15 + ny * (i - 1) * 0.1], [b[0] + ux * (0.15 + s) + nx * (i - 1) * 0.3, b[1] + uy * (0.15 + s) + ny * (i - 1) * 0.3], 0.05, '#d99a3a'))
    .join('');
  return ln(a, b, 0.2 + 2 * LW) + ln(a, b, 0.2, DARK) + ln([b[0] - ux * 0.08, b[1] - uy * 0.08], b, 0.3, '#e8d9a8') + beam;
}

/** bucket hanging from a hand point */
export function bucket(hand, w = 0.75, h = 0.7) {
  const [hx, hy] = hand;
  const top = hy + 0.38;
  return (
    `<path d="M${P([hx - w / 2, top])} Q${P([hx, hy - 0.25])} ${P([hx + w / 2, top])}" fill="none" stroke="${INK}" stroke-width="0.06"/>` +
    `<path d="M${P([hx - w / 2, top])} L${P([hx + w / 2, top])} L${P([hx + w / 2 - 0.1, top + h])} L${P([hx - w / 2 + 0.1, top + h])}Z" fill="${METAL}" stroke="${INK}" stroke-width="${LW}"/>` +
    `<ellipse cx="${f(hx)}" cy="${f(top)}" rx="${f(w / 2)}" ry="0.08" fill="#c8ccd0" stroke="${INK}" stroke-width="0.04"/>`
  );
}

/** wooden plank: centre, length, thickness */
export function plank(cx, cy, len = 3, th = 0.32) {
  const x = cx - len / 2;
  const y = cy - th / 2;
  return rect(x, y, len, th, WOOD, 0.04) + ln([x + 0.3, y + th * 0.4], [x + len * 0.45, y + th * 0.4], 0.025, WOOD_DARK) + ln([x + len * 0.55, y + th * 0.65], [x + len - 0.3, y + th * 0.65], 0.025, WOOD_DARK);
}

/** phone held at a point, rotated by deg */
export function phone(c, deg = 0, w = 0.36, h = 0.6) {
  return `<g transform="translate(${P(c)}) rotate(${deg})">${rect(-w / 2, -h / 2, w, h, DARK, 0.07)}<rect x="${f(-w / 2 + 0.05)}" y="${f(-h / 2 + 0.06)}" width="${f(w - 0.1)}" height="${f(h - 0.14)}" rx="0.03" fill="#7f9db3"/></g>`;
}

/** cup with a straw, centred at c */
export function cup(c, w = 0.38, h = 0.5) {
  const [x, y] = c;
  return ln([x + 0.06, y - h / 2], [x + 0.16, y - h / 2 - 0.28], 0.05, '#d9603b') + `<path d="M${P([x - w / 2, y - h / 2])} L${P([x + w / 2, y - h / 2])} L${P([x + w / 2 - 0.05, y + h / 2])} L${P([x - w / 2 + 0.05, y + h / 2])}Z" fill="#efe6d6" stroke="${INK}" stroke-width="${LW}"/>`;
}

/** open book facing the viewer, centred at c */
export function book(c, w = 1.4, h = 0.9) {
  const [x, y] = c;
  const page = (s) => `<path d="M${P([x, y - h / 2 + 0.05])} Q${P([x + s * w * 0.25, y - h / 2 - 0.06])} ${P([x + s * w / 2, y - h / 2])} L${P([x + s * w / 2, y + h / 2])} Q${P([x + s * w * 0.25, y + h / 2 - 0.06])} ${P([x, y + h / 2])}Z" fill="#f3ead8" stroke="${INK}" stroke-width="${LW}"/>`;
  const lines = [-1, 1].map((s) => [0.25, 0.42, 0.59].map((k) => ln([x + s * 0.12, y - h / 2 + k * h], [x + s * w * 0.4, y - h / 2 + k * h], 0.025, '#b9a283')).join('')).join('');
  return rect(x - w / 2 - 0.05, y - h / 2 - 0.02, w + 0.1, h + 0.1, WOOD, 0.04) + page(-1) + page(1) + lines;
}

/** a small round object (apple, ball) */
export const ball = (c, r = 0.16, fill = '#c9663f') => `<circle cx="${f(c[0])}" cy="${f(c[1])}" r="${r}" fill="${fill}" stroke="${INK}" stroke-width="${LW}"/>`;

/** desk top line with a sheet of paper, for writing */
export function desk(x0, x1, y) {
  return rect(x0, y, x1 - x0, 0.14, WOOD, 0.03) + `<path d="M${P([x0 + 0.5, y - 0.02])} L${P([x1 - 0.5, y - 0.02])}" stroke="#f3ead8" stroke-width="0.05"/>`;
}

/** camera held in front of the face (front view), centred at c */
export function camera(c, w = 0.8, h = 0.52) {
  const [x, y] = c;
  return rect(x - w / 2, y - h / 2, w, h, DARK, 0.08) + rect(x - 0.18, y - h / 2 - 0.12, 0.3, 0.14, DARK, 0.03) + `<circle cx="${f(x)}" cy="${f(y + 0.02)}" r="0.19" fill="#7f9db3" stroke="${INK}" stroke-width="${LW}"/>`;
}

/** keyboard on a table (front view), centred at c */
export function keyboard(c, w = 2.2, h = 0.34) {
  const [x, y] = c;
  let keys = '';
  for (let i = 0; i < 9; i++) keys += `<rect x="${f(x - w / 2 + 0.12 + i * 0.22)}" y="${f(y - h / 2 + 0.07)}" width="0.16" height="0.1" rx="0.02" fill="#d6d9dc"/>`;
  return rect(x - w / 2, y - h / 2, w, h, '#8c9197', 0.05) + keys + rect(x - 1.7, y + h / 2, 3.4, 0.14, WOOD, 0.03);
}

/** handlebar seen from the front, centred at c */
export function handlebar(c, w = 2.4) {
  const [x, y] = c;
  return rod([x - w / 2, y - 0.12], [x + w / 2, y - 0.12], 0.12, DARK) + rod([x, y - 0.1], [x, y + 0.8], 0.16, DARK) + rod([x - w / 2 - 0.05, y - 0.12], [x - w / 2 + 0.25, y - 0.12], 0.2, '#555a62') + rod([x + w / 2 - 0.25, y - 0.12], [x + w / 2 + 0.05, y - 0.12], 0.2, '#555a62');
}

/** rope from a to b with a little sag */
export function rope(a, b, sag = 0.15) {
  const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + sag];
  const d = `M${P(a)} Q${P(m)} ${P(b)}`;
  return `<path d="${d}" fill="none" stroke="${INK}" stroke-width="${0.1 + 2 * LW}"/><path d="${d}" fill="none" stroke="#a8844f" stroke-width="0.1"/>`;
}

/** a book seen from the side, held open toward the reader: c = the hand at its lower edge, tilt in degrees */
export function bookSide(c, tilt = 35, len = 1.0) {
  const [x, y] = c;
  return `<g transform="translate(${P([x, y])}) rotate(${tilt})">` +
    // an open book seen edge-on: the cover, and the page block fanning open toward the reader
    `<path d="M-0.04 0 L-0.04 ${f(-len)} L0.2 ${f(-len * 0.97)} L0.2 ${f(-len * 0.03)}Z" fill="${WOOD}" stroke="${INK}" stroke-width="${LW}"/>` +
    `<path d="M-0.04 ${f(-0.05)} Q-0.28 ${f(-len * 0.5)} -0.04 ${f(-len + 0.05)}" fill="#f3ead8" stroke="${INK}" stroke-width="${LW}"/>` +
    `</g>`;
}

/** a chair in side view (facing right): seat top at seatY, seat from x0 to x1, backrest at x0 */
export function chair(x0, x1, seatY, backTop = -2.7) {
  return rod([x0 + 0.06, seatY], [x0 + 0.06, 0], 0.1, WOOD_DARK) + rod([x1 - 0.06, seatY], [x1 - 0.06, 0], 0.1, WOOD_DARK) +
    rod([x0 - 0.02, seatY], [x0 - 0.12, backTop], 0.12, WOOD_DARK) + rect(x0, seatY, x1 - x0, 0.12, WOOD, 0.03);
}

/** a table in side view: top surface at topY from x0 to x1 */
export function table(x0, x1, topY) {
  return rect(x0, topY, x1 - x0, 0.14, WOOD, 0.03) + rod([x0 + 0.15, topY + 0.14], [x0 + 0.15, 0], 0.12, WOOD_DARK) + rod([x1 - 0.15, topY + 0.14], [x1 - 0.15, 0], 0.12, WOOD_DARK);
}
