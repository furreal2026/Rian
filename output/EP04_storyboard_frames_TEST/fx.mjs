// Thought bubbles + icons, the mysterious signal, earphones, extra poses for this episode, and the intro card.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { drawMilo, miloParts, pose, STYLE, PROP } from './rig/milo.mjs';
import { reach, plant, groundLock } from './rig/anim.mjs';
import { poly, rect, ell, pth, ln, wc, INK, W, H } from './world.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const n = (v) => +(+v).toFixed(2);

// ---------------------------------------------------------------- thought bubbles (fantasy visualisation, 2D overlay)
export function bubble(cx, cy, r, icons = [], o = {}) {
  const op = o.op ?? 0.95;
  const blobs = [[0, 0, 1], [-0.62, 0.12, 0.62], [0.62, 0.1, 0.64], [-0.3, -0.45, 0.6], [0.32, -0.42, 0.62], [-0.05, 0.42, 0.62], [0.55, 0.42, 0.45], [-0.55, 0.42, 0.45]];
  const fill = o.fill || '#fbf6ec';
  let ink = '';
  let body = '';
  for (const [x, y, k] of blobs) {
    ink += `<circle cx="${n(cx + x * r)}" cy="${n(cy + y * r)}" r="${n(k * r * 0.62 + 3)}" fill="${INK}" opacity="0.85"/>`;
    body += `<circle cx="${n(cx + x * r)}" cy="${n(cy + y * r)}" r="${n(k * r * 0.62)}" fill="${fill}"/>`;
  }
  let tail = '';
  if (o.tail) {
    const [tx, ty] = o.tail;
    for (const [t, k] of [[0.55, 0.16], [0.75, 0.1], [0.9, 0.06]]) {
      const x = cx + (tx - cx) * t;
      const y = cy + r * 0.5 + (ty - cy - r * 0.5) * t;
      tail += `<circle cx="${n(x)}" cy="${n(y)}" r="${n(r * k + 2.5)}" fill="${INK}" opacity="0.85"/><circle cx="${n(x)}" cy="${n(y)}" r="${n(r * k)}" fill="${fill}"/>`;
    }
  }
  const k = icons.length;
  const ic = icons.map((name, i) => {
    const dx = k === 1 ? 0 : (i / (k - 1) - 0.5) * r * (k > 2 ? 1.25 : 0.95);
    const dy = k > 2 && i % 2 ? r * 0.18 : -r * 0.04;
    return icon(name, cx + dx, cy + dy, (r / 70) * (k > 2 ? 0.72 : k === 2 ? 0.85 : 1.1));
  }).join('');
  return `<g opacity="${op}" ${o.blur ? `filter="url(#${o.blur})"` : ''}>${wc(tail + ink + body)}${ic}</g>`;
}
/** speech-free "faint words" fragments for crowd noise */
export function words(x, y, txt, size = 30, o = {}) {
  return `<text x="${x}" y="${y}" font-family="Patrick Hand, sans-serif" font-size="${size}" fill="${o.col || INK}" opacity="${o.op ?? 0.75}" transform="rotate(${o.rot || 0} ${x} ${y})" ${o.blur ? `filter="url(#${o.blur})"` : ''}>${txt}</text>`;
}

export function icon(name, x, y, s = 1) {
  const S = (v) => v * s;
  const X = (v) => n(x + S(v));
  const Y = (v) => n(y + S(v));
  const o = { sw: 2.4 * Math.max(0.6, s) };
  switch (name) {
    case 'plantWilt': return poly([[X(-18), Y(10)], [X(18), Y(10)], [X(13), Y(38)], [X(-13), Y(38)]], '#b8714f', o) + pth(`M${X(0)} ${Y(10)} Q${X(2)} ${Y(-20)} ${X(20)} ${Y(-24)} Q${X(30)} ${Y(-20)} ${X(28)} ${Y(-8)}`, 'none', { ...o, stroke: '#6f7a3a' }) + ell(X(26), Y(-6), S(9), S(5), '#a7a35a', o) + pth(`M${X(-2)} ${Y(4)} Q${X(-20)} ${Y(-6)} ${X(-24)} ${Y(8)}`, 'none', { ...o, stroke: '#6f7a3a' }) + ell(X(-24), Y(10), S(8), S(5), '#a7a35a', o);
    case 'hose': return pth(`M${X(-34)} ${Y(20)} Q${X(-20)} ${Y(-20)} ${X(10)} ${Y(-6)} Q${X(30)} ${Y(4)} ${X(30)} ${Y(-16)}`, 'none', { sw: 9 * s, stroke: '#5f8a5a', so: 1 }) + [[-6, -4], [8, 0], [-18, 4]].map(([a, b]) => pth(`M${X(a)} ${Y(b)} q${S(3)} ${S(10)} ${S(0)} ${S(16)}`, 'none', { ...o, stroke: '#7fb2dd' })).join('') + ell(X(-4), Y(30), S(14), S(4), '#9fc7e6', { stroke: false, op: 0.8 });
    case 'list': return rect(X(-22), Y(-30), S(44), S(60), '#f3efe4', o) + [0, 1, 2, 3].map((k) => ln(X(-12), Y(-16 + k * 13), X(14), Y(-16 + k * 13), { sw: 2 * s })).join('') + [0, 1, 2, 3].map((k) => `<circle cx="${X(-16)}" cy="${Y(-16 + k * 13)}" r="${S(2)}" fill="${INK}"/>`).join('');
    case 'fern': return pth(`M${X(0)} ${Y(34)} Q${X(4)} ${Y(0)} ${X(-6)} ${Y(-30)}`, 'none', { ...o, stroke: '#5f7a3a' }) + [-20, -8, 4, 16].map((v, k) => ell(X(k % 2 ? 10 : -10), Y(v), S(10), S(5), '#8fa15a', { sw: 1.6 * s })).join('');
    case 'bread': return pth(`M${X(-30)} ${Y(10)} Q${X(-34)} ${Y(-20)} ${X(0)} ${Y(-22)} Q${X(34)} ${Y(-20)} ${X(30)} ${Y(10)} Z`, '#d6a35e', o) + [-12, 0, 12].map((v) => ln(X(v - 4), Y(-14), X(v + 4), Y(-4), { sw: 2 * s })).join('');
    case 'key': return `<circle cx="${X(-16)}" cy="${Y(0)}" r="${S(12)}" fill="#e0b04e" stroke="${INK}" stroke-width="${o.sw}"/><circle cx="${X(-16)}" cy="${Y(0)}" r="${S(4)}" fill="#fbf6ec"/>` + rect(X(-4), Y(-4), S(36), S(8), '#e0b04e', o) + rect(X(20), Y(4), S(6), S(10), '#e0b04e', o) + words(X(8), Y(-14), '?', 22 * s, { op: 0.9 });
    case 'clock': return `<circle cx="${X(0)}" cy="${Y(0)}" r="${S(26)}" fill="#f3efe4" stroke="${INK}" stroke-width="${o.sw}"/>` + ln(X(0), Y(0), X(0), Y(-16), o) + ln(X(0), Y(0), X(12), Y(6), o);
    case 'lunch': return ell(X(0), Y(10), S(32), S(10), '#efe6d6', o) + pth(`M${X(-30)} ${Y(8)} Q${X(0)} ${Y(-36)} ${X(30)} ${Y(8)} Z`, '#e0b04e', o) + pth(`M${X(-8)} ${Y(-26)} q${S(-6)} ${S(-10)} 0 ${S(-18)} M${X(8)} ${Y(-26)} q${S(-6)} ${S(-10)} 0 ${S(-18)}`, 'none', { sw: 2 * s, so: 0.6 });
    case 'question': return words(X(-14), Y(22), '?', 70 * s, { op: 0.95 });
    case 'stain': return pth(`M${X(-26)} ${Y(-20)} L${X(-10)} ${Y(-30)} Q${X(0)} ${Y(-22)} ${X(10)} ${Y(-30)} L${X(26)} ${Y(-20)} L${X(20)} ${Y(-6)} L${X(14)} ${Y(-10)} L${X(14)} ${Y(30)} L${X(-14)} ${Y(30)} L${X(-14)} ${Y(-10)} L${X(-20)} ${Y(-6)} Z`, '#e8e2d2', o) + ell(X(4), Y(8), S(8), S(6), '#8a6a44', { stroke: false, op: 0.8 });
    case 'queue': return [-24, 0, 24].map((v) => `<circle cx="${X(v)}" cy="${Y(-14)}" r="${S(8)}" fill="#f3efe4" stroke="${INK}" stroke-width="${o.sw * 0.8}"/>` + rect(X(v - 7), Y(-6), S(14), S(26), '#8796a8', { sw: o.sw * 0.8, rx: 3 })).join('') + ln(X(-36), Y(26), X(36), Y(26), { sw: 2 * s });
    case 'machine': return rect(X(-24), Y(-28), S(48), S(52), '#a9adb2', { ...o, rx: 5 }) + rect(X(-14), Y(-18), S(28), S(16), '#3b3f46', { stroke: false }) + pth(`M${X(30)} ${Y(-24)} l${S(10)} ${S(-8)} M${X(32)} ${Y(-8)} l${S(14)} 0 M${X(30)} ${Y(8)} l${S(10)} ${S(8)}`, 'none', o) + words(X(-6), Y(-34), '!', 28 * s, { op: 0.9 });
    case 'laptop': return rect(X(-24), Y(-22), S(48), S(32), '#5a5f66', o) + rect(X(-19), Y(-18), S(38), S(24), '#a9c8e6', { stroke: false }) + poly([[X(-32), Y(10)], [X(32), Y(10)], [X(26), Y(18)], [X(-26), Y(18)]], '#7d8288', o);
    case 'book': return rect(X(-26), Y(-20), S(52), S(38), '#c98f5c', o) + ln(X(0), Y(-20), X(0), Y(18), o) + rect(X(-20), Y(-16), S(17), S(30), '#f3ead8', { stroke: false }) + rect(X(3), Y(-16), S(17), S(30), '#f3ead8', { stroke: false });
    case 'music': return pth(`M${X(-12)} ${Y(18)} L${X(-12)} ${Y(-22)} L${X(16)} ${Y(-28)} L${X(16)} ${Y(12)}`, 'none', o) + ell(X(-18), Y(20), S(8), S(6), INK, { stroke: false }) + ell(X(10), Y(14), S(8), S(6), INK, { stroke: false });
    case 'lock': return rect(X(-18), Y(-4), S(36), S(30), '#e0b04e', { ...o, rx: 4 }) + pth(`M${X(-11)} ${Y(-4)} L${X(-11)} ${Y(-16)} Q${X(0)} ${Y(-32)} ${X(11)} ${Y(-16)} L${X(11)} ${Y(-4)}`, 'none', o) + words(X(22), Y(-12), '?', 26 * s, { op: 0.9 });
    case 'plate': return ell(X(0), Y(8), S(34), S(12), '#efe6d6', o) + ell(X(0), Y(4), S(20), S(7), '#c98f5c', o);
    case 'phone': return rect(X(-14), Y(-26), S(28), S(52), '#2f333a', { ...o, rx: 5 }) + rect(X(-10), Y(-20), S(20), S(38), '#a9c8e6', { stroke: false }) + pth(`M${X(20)} ${Y(-16)} q${S(8)} ${S(6)} 0 ${S(14)} M${X(26)} ${Y(-22)} q${S(14)} ${S(12)} 0 ${S(26)}`, 'none', { sw: 2 * s });
    case 'fish': return pth(`M${X(-26)} ${Y(0)} Q${X(0)} ${Y(-22)} ${X(18)} ${Y(0)} Q${X(0)} ${Y(22)} ${X(-26)} ${Y(0)} Z`, '#8fb0c8', o) + poly([[X(16), Y(0)], [X(32), Y(-12)], [X(32), Y(12)]], '#8fb0c8', o) + `<circle cx="${X(-14)}" cy="${Y(-3)}" r="${S(2.5)}" fill="${INK}"/>`;
    case 'bowl': return pth(`M${X(-30)} ${Y(-4)} L${X(30)} ${Y(-4)} L${X(22)} ${Y(18)} L${X(-22)} ${Y(18)} Z`, '#6f8fa8', o) + ell(X(0), Y(-6), S(26), S(7), '#b98b55', o);
    case 'cushion': return pth(`M${X(-32)} ${Y(10)} Q${X(-34)} ${Y(-14)} ${X(0)} ${Y(-14)} Q${X(34)} ${Y(-14)} ${X(32)} ${Y(10)} Q${X(0)} ${Y(22)} ${X(-32)} ${Y(10)} Z`, '#c98f6f', o) + pth(`M${X(-6)} ${Y(-22)} q${S(-5)} ${S(-8)} 0 ${S(-16)} M${X(8)} ${Y(-22)} q${S(-5)} ${S(-8)} 0 ${S(-16)}`, 'none', { sw: 2 * s, stroke: '#e0904e' });
    case 'door': return rect(X(-18), Y(-32), S(36), S(64), '#8e6a4c', o) + `<circle cx="${X(10)}" cy="${Y(2)}" r="${S(3)}" fill="${INK}"/>` + pth(`M${X(24)} ${Y(-20)} l${S(14)} ${S(-6)} M${X(24)} ${Y(0)} l${S(16)} 0`, 'none', o);
    case 'briefcase': return rect(X(-28), Y(-14), S(56), S(36), '#8a6a44', { ...o, rx: 4 }) + rect(X(-10), Y(-24), S(20), S(10), 'none', o);
    case 'zz': return words(X(-24), Y(14), 'z', 34 * s, { op: 0.9 }) + words(X(0), Y(-4), 'Z', 40 * s, { op: 0.9 });
    case 'heart': return pth(`M${X(0)} ${Y(20)} C${X(-34)} ${Y(-4)} ${X(-18)} ${Y(-30)} ${X(0)} ${Y(-12)} C${X(18)} ${Y(-30)} ${X(34)} ${Y(-4)} ${X(0)} ${Y(20)} Z`, '#d9776a', o);
    case 'smile': return `<circle cx="${X(0)}" cy="${Y(0)}" r="${S(24)}" fill="#f3d27a" stroke="${INK}" stroke-width="${o.sw}"/>` + pth(`M${X(-12)} ${Y(4)} Q${X(0)} ${Y(16)} ${X(12)} ${Y(4)}`, 'none', o) + `<circle cx="${X(-8)}" cy="${Y(-6)}" r="${S(2.5)}" fill="${INK}"/><circle cx="${X(8)}" cy="${Y(-6)}" r="${S(2.5)}" fill="${INK}"/>`;
    case 'rain': return ell(X(0), Y(-8), S(28), S(14), '#9aa7b8', o) + [-14, 0, 14].map((v) => ln(X(v), Y(10), X(v - 4), Y(24), { sw: 2 * s, stroke: '#7fb2dd' })).join('');
    case 'photo': return rect(X(-26), Y(-20), S(52), S(40), '#f3efe4', o) + poly([[X(-20), Y(14)], [X(-4), Y(-6)], [X(8), Y(6)], [X(14), Y(0)], [X(20), Y(14)]], '#8fa16a', { sw: 1.5 * s });
    case 'spiral': return pth(`M${X(0)} ${Y(0)} m${S(-4)} 0 a${S(4)} ${S(4)} 0 1 1 ${S(8)} 0 a${S(9)} ${S(9)} 0 1 1 ${S(-18)} 0 a${S(14)} ${S(14)} 0 1 1 ${S(28)} 0 a${S(19)} ${S(19)} 0 1 1 ${S(-38)} 0`, 'none', o);
    case 'tab': return rect(X(-30), Y(-20), S(60), S(40), '#f3efe4', { ...o, rx: 4 }) + rect(X(-30), Y(-20), S(60), S(10), '#c9d6dc', { ...o, rx: 4 }) + pth(`M${X(-8)} ${Y(4)} l${S(6)} ${S(-6)} l${S(6)} ${S(6)} l${S(6)} ${S(-6)}`, 'none', { sw: 2 * s });
    case 'cash': return rect(X(-28), Y(-16), S(56), S(32), '#9fbf8a', o) + `<circle cx="${X(0)}" cy="${Y(0)}" r="${S(8)}" fill="none" stroke="${INK}" stroke-width="${2 * s}"/>`;
    default: return '';
  }
}

// ---------------------------------------------------------------- mysterious signal (fantasy, 2D overlay)
export function signalWaves(cx, cy, r0, r1, k = 6, o = {}) {
  let s = `<circle cx="${cx}" cy="${cy}" r="${r0 * 1.6}" fill="url(#sigGlow)" opacity="${o.glow ?? 0.8}" style="mix-blend-mode:screen"/>`;
  for (let i = 0; i < k; i++) {
    const r = r0 + ((r1 - r0) * i) / (k - 1);
    const a0 = o.arc ? o.arc[0] : -180;
    const a1 = o.arc ? o.arc[1] : 180;
    const p = (a) => [cx + r * Math.cos((a * Math.PI) / 180), cy + r * Math.sin((a * Math.PI) / 180) * (o.squash ?? 1)];
    const [x0, y0] = p(a0);
    const [x1, y1] = p(a1 - 0.01);
    const large = a1 - a0 > 180 ? 1 : 0;
    const col = i % 2 ? '#9fd0ff' : '#c6b2ff';
    s += `<path d="M${n(x0)} ${n(y0)} A${n(r)} ${n(r * (o.squash ?? 1))} 0 ${large} 1 ${n(x1)} ${n(y1)}" fill="none" stroke="${col}" stroke-width="${o.sw ?? 5}" opacity="${(1 - i / k) * 0.9}" filter="url(#glowS)" style="mix-blend-mode:screen"/>`;
    s += `<path d="M${n(x0)} ${n(y0)} A${n(r)} ${n(r * (o.squash ?? 1))} 0 ${large} 1 ${n(x1)} ${n(y1)}" fill="none" stroke="#f1ecff" stroke-width="${(o.sw ?? 5) * 0.35}" opacity="${(1 - i / k) * 0.85}" stroke-dasharray="${o.dash || 'none'}"/>`;
  }
  return s;
}
export function particles(cx, cy, r, k = 40, seed = 3) {
  let s = 0;
  let out = '';
  const rnd = () => ((s = (s * 9301 + 49297 + seed * 7) % 233280) / 233280);
  for (let i = 0; i < k; i++) {
    const a = rnd() * Math.PI * 2;
    const d = r * (0.2 + rnd());
    out += `<circle cx="${n(cx + Math.cos(a) * d)}" cy="${n(cy + Math.sin(a) * d * 0.7)}" r="${n(1.5 + rnd() * 4)}" fill="#e6dcff" opacity="${n(0.3 + rnd() * 0.6)}" style="mix-blend-mode:screen"/>`;
  }
  return out;
}

// ---------------------------------------------------------------- earphones (figure space of a pose, side view)
export function earphones(p, to, o = {}) {
  const { headC } = miloParts(pose(p));
  const bud = [headC[0] - 0.42, headC[1] + 0.22];
  const cable = `M${bud[0]} ${bud[1] + 0.1} Q${bud[0] - 0.2} ${bud[1] + 1.4} ${to[0] - 0.2} ${to[1] + 0.3}`;
  const glow = o.glow ? `<path d="${cable}" fill="none" stroke="#c6b2ff" stroke-width="0.22" opacity="0.8" filter="url(#glowS)"/>` : '';
  const inner = `${glow}<path d="${cable}" fill="none" stroke="#f3efe4" stroke-width="0.07"/><path d="${cable}" fill="none" stroke="${INK}" stroke-width="0.02" opacity="0.6"/><ellipse cx="${bud[0]}" cy="${bud[1]}" rx="0.13" ry="0.16" fill="#f3efe4" stroke="${INK}" stroke-width="0.04"/>`;
  const flip = p.view === 'side' && p.facing === -1 ? -1 : 1;
  return `<g transform="translate(${n(p.x)} ${n(p.y)}) rotate(${p.rot || 0}) scale(${n(p.scale * flip)} ${n(p.scale)})">${inner}</g>`;
}

// ---------------------------------------------------------------- poses for this episode
export const SLEEP = {
  view: 'side', facing: -1, eyes: 2, faceX: 0.08, expr: 'tidur', rot: -86, lean: 12, headTilt: -80, shadow: false,
  legR: { a1: 6, a2: 2, foot: 0 }, legL: { a1: 2, a2: -2, foot: 0 },
  armR: { a1: 132, a2: 168, z: 'front' }, armL: { a1: 140, a2: 172, z: 'body' },
};
/** both round hands pressed to the sides of the head (Milo has no ears) */
export function handsOnHead(pz) {
  let p = pose(pz);
  const { joints } = miloParts(p);
  const h = joints.headC;
  p = reach(pz, 'R', [h[0] + 1.0, h[1] + 0.35], 1);
  p = reach(p, 'L', [h[0] - 1.0, h[1] + 0.35], -1);
  return { ...p, armR: { ...p.armR, z: 'front' }, armL: { ...p.armL, z: 'front' } };
}
/** one hand rubbing the side of the head (just woke up) */
export function rubHead(pz, side = 'R') {
  const p = pose(pz);
  const { joints } = miloParts(p);
  const h = joints.headC;
  const q = reach(pz, side, [h[0] + (side === 'R' ? 0.95 : -0.95), h[1] - 0.15], side === 'R' ? 1 : -1);
  const k = side === 'R' ? 'armR' : 'armL';
  return { ...q, [k]: { ...q[k], z: 'front' } };
}
/** hand under the chin (thinking) */
export function chinHand(pz) {
  const p = pose(pz);
  const { joints } = miloParts(p);
  const h = joints.headC;
  const side = p.view === 'side';
  const q = reach(pz, 'R', side ? [h[0] + 0.62, h[1] + 1.12] : [h[0] + 0.25, h[1] + 1.15], side ? -1 : 1);
  const a = { ...q.armR };
  while (a.a2 - a.a1 < -180) a.a2 += 360; // IK returns the same direction as -177 instead of 183: unwrap so the elbow limit reads it right
  while (a.a2 - a.a1 > 180) a.a2 -= 360;
  return { ...q, armR: { ...a, z: 'front', hand: 'ball' } };
}
export function wave(pz, side = 'R') {
  const k = side === 'R' ? 'armR' : 'armL';
  const s = side === 'R' ? 1 : -1;
  return { ...pz, [k]: { a1: s * 128, a2: s * 172, hand: 'ball' } };
}
/** squat facing right (side view), one hand reaching out to a target (figure space) */
export function squat(pz, reachTo) {
  let p = plant(plant({ view: 'side', facing: 1, hip: [-0.3, 0.95], lean: 22, headTilt: 6, ...pz }, 'R', [0.32, -0.22]), 'L', [0.05, -0.22]);
  if (reachTo) p = reach(p, 'R', reachTo, -1);
  else p = { ...p, armR: { a1: 30, a2: 70 }, armL: { a1: 20, a2: 60 } };
  return p;
}
/** sitting on a bench or bed edge, seen from the front: thighs foreshortened (hidden), shins drawn to the ground */
export function frontSit(x, groundY, seatY, scale, o = {}) {
  const hipY = -(groundY - seatY) / scale; // seat height in head radii above the ground
  const dy = PROP.hipY - hipY + 0.12;
  const pz = { x, y: groundY, scale, hip: [0, -dy], expr: o.expr || 'calm', legL: { hide: true }, legR: { hide: true }, armL: o.armL || { a1: -12, a2: 10 }, armR: o.armR || { a1: 12, a2: -10 }, headTilt: o.headTilt || 0, look: o.look || [0, 0], faceX: o.faceX || 0, shadow: false };
  const p = o.pose ? o.pose(pz) : pz;
  const t = STYLE.line;
  const w = PROP.legW;
  const shin = (sx) => {
    const top = [sx, hipY - 0.02];
    const bot = [sx * 1.15, -0.22];
    const toe = [bot[0] + (sx < 0 ? -0.28 : 0.28), -0.14];
    const d = `M${top[0]} ${top[1]} L${bot[0]} ${bot[1]}`;
    const f = `M${bot[0]} ${bot[1]} L${toe[0]} ${toe[1]}`;
    return `<path d="${d}" stroke="${STYLE.ink}" stroke-width="${w + 2 * t}" stroke-linecap="round"/><path d="${f}" stroke="${STYLE.ink}" stroke-width="${PROP.footW + 2 * t}" stroke-linecap="round"/><path d="${d}" stroke="${STYLE.skin}" stroke-width="${w}" stroke-linecap="round"/><path d="${f}" stroke="${STYLE.skin}" stroke-width="${PROP.footW}" stroke-linecap="round"/>`;
  };
  const legs = `<g transform="translate(${n(x)} ${n(groundY)})"><g filter="url(#miloWobble)"><g transform="scale(${scale})"><ellipse cx="0" cy="0.02" rx="0.95" ry="0.12" fill="#6e5a44" opacity="0.35"/>${shin(-0.22)}${shin(0.22)}</g></g></g>`;
  return legs + drawMilo(pose(p));
}

// ---------------------------------------------------------------- intro card (after Milo faints): title + Curious Mind logo
const LOGO = `data:image/png;base64,${readFileSync(join(here, '../../episodes/EP04_WHAT_IF_BISA_MENDENGAR_PIKIRAN/source/curious_mind_logo.png')).toString('base64')}`;
export function introCard() {
  let s = `<defs><radialGradient id="introBg" cx="50%" cy="45%" r="75%"><stop offset="0%" stop-color="#3b3f73"/><stop offset="60%" stop-color="#252a4d"/><stop offset="100%" stop-color="#141729"/></radialGradient></defs><rect width="${W}" height="${H}" fill="url(#introBg)"/>`;
  s += signalWaves(W / 2, 470, 150, 820, 9, { glow: 0.55, sw: 4 });
  s += particles(W / 2, 470, 760, 90, 5);
  s += `<rect x="${W / 2 - 560}" y="150" width="1120" height="560" rx="40" fill="#fbf6ec" opacity="0.06"/>`;
  s += `<image href="${LOGO}" x="${W / 2 - 520}" y="120" width="1040" height="456"/>`;
  s += `<text x="${W / 2}" y="680" text-anchor="middle" font-family="Patrick Hand, sans-serif" font-size="44" fill="#f2c94c" letter-spacing="6">EPISODE 004</text>`;
  s += `<text x="${W / 2}" y="790" text-anchor="middle" font-family="Patrick Hand, sans-serif" font-size="96" fill="#fbf6ec" stroke="#141729" stroke-width="10" paint-order="stroke">What If You Could Read Everyone's Mind?</text>`;
  s += `<path d="M${W / 2 - 430} 830 Q${W / 2} 850 ${W / 2 + 430} 830" fill="none" stroke="#f2c94c" stroke-width="9" stroke-linecap="round"/>`;
  return s;
}

/** sitting on a bench or bed edge, side view facing right: thighs level, shins down, hands resting on the thighs */
export function sideSit(x, groundY, scale, o = {}) {
  let p = { view: 'side', facing: o.facing ?? 1, x, y: groundY, scale, hip: [0, 0.8], lean: o.lean ?? -2, headTilt: o.headTilt ?? 0, expr: o.expr || 'calm', look: o.look || [0, 0],
    legR: { a1: 90, a2: 0, foot: 0 }, legL: { a1: 86, a2: -3, foot: 0 }, shadow: false };
  p = reach(p, 'R', [0.55, -0.98], -1);
  p = reach(p, 'L', [0.45, -1.02], -1);
  return o.pose ? o.pose(p) : p;
}
