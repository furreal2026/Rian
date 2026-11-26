// Milo v2: reusable character rig, drawn entirely in code (SVG strings, no dependencies).
//
// Units: 1 = Milo's head radius. Origin = the ground point between his feet. y points down (SVG).
// A figure is a list of "parts" in z-order. Every part is filled in skin colour with a bold ink outline;
// where a part lies over an earlier part, only that overlap gets an inner outline, so the whole body
// reads as one clean, seamless silhouette (as in the reference sheet) while limbs in front still show.
//
// Public API:
//   miloDefs()                      shared <defs> (filters) - put once per SVG
//   drawMilo(pose)                  one Milo, returns an SVG <g> string
//   drawHand(kind, opts)            a single hand on a wrist stub (for gesture sheets)
//   pose(overrides)                 a full pose from the neutral one
//   POSES, EXPR, HANDS              presets
//   STYLE, PROP                     colours and proportions (change here, never per scene)

export const STYLE = {
  ink: '#1e1914',
  skin: '#f8eedd',
  shade: '#c9ab84', // edge shading and the cast shadow under the head
  line: 0.044, // ink width in head radii
  wobble: 1.6, // hand-drawn wobble in screen px
};

export const PROP = {
  headY: -4.43, // head centre
  neckY: -3.45, // head rotates about this point
  shoulderX: 0.36,
  shoulderY: -2.95,
  hipY: -1.8,
  hipX: 0.275,
  armW: 0.35,
  upperArm: 0.72, // human-like: hanging hands reach mid-thigh, as in the motion guide
  foreArm: 0.66,
  legW: 0.44,
  thigh: 0.8,
  shin: 0.78,
  footW: 0.31,
  hand: 0.5, // palm width in head radii
};

// ---------- tiny geometry ----------
const f = (n) => (Math.abs(n) < 1e-9 ? '0' : n.toFixed(4).replace(/\.?0+$/, ''));
const pt = (p) => `${f(p[0])} ${f(p[1])}`;
const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const mul = (a, k) => [a[0] * k, a[1] * k];
const rad = (d) => (d * Math.PI) / 180;
/** direction for an angle in degrees: 0 = straight down, 90 = screen right, 180 = up, -90 = screen left */
const dir = (deg) => [Math.sin(rad(deg)), Math.cos(rad(deg))];
const rot = (p, deg, c = [0, 0]) => {
  const a = rad(deg);
  const x = p[0] - c[0];
  const y = p[1] - c[1];
  return [c[0] + x * Math.cos(a) - y * Math.sin(a), c[1] + x * Math.sin(a) + y * Math.cos(a)];
};

/** closed smooth path through points (Catmull-Rom as cubic Beziers) */
export function smooth(pts, closed = true) {
  const n = pts.length;
  let d = `M${pt(pts[0])}`;
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = pts[(i - 1 + n) % n];
    const p1 = pts[i];
    const p2 = pts[(i + 1) % n];
    const p3 = pts[(i + 2) % n];
    const a = closed || i > 0 ? p0 : p1;
    const b = closed || i < n - 2 ? p3 : p2;
    const c1 = add(p1, mul(sub(p2, a), 1 / 6));
    const c2 = sub(p2, mul(sub(b, p1), 1 / 6));
    d += ` C${pt(c1)} ${pt(c2)} ${pt(p2)}`;
  }
  return closed ? d + 'Z' : d;
}
const circle = (c, r) => `M${f(c[0] - r)} ${f(c[1])}a${f(r)} ${f(r)} 0 1 0 ${f(2 * r)} 0a${f(r)} ${f(r)} 0 1 0 ${f(-2 * r)} 0Z`;
const ellipse = (c, rx, ry) => `M${f(c[0] - rx)} ${f(c[1])}a${f(rx)} ${f(ry)} 0 1 0 ${f(2 * rx)} 0a${f(rx)} ${f(ry)} 0 1 0 ${f(-2 * rx)} 0Z`;
/** a bent limb as one smooth curve: the joint is the curve's control point (no elbow corner) */
function limbCurve(a, j, b, k = 0.9) {
  const m = mul(add(a, b), 0.5);
  const c = add(m, mul(sub(j, m), 2 * k));
  return `M${pt(a)} Q${pt(c)} ${pt(b)}`;
}
const line = (a, b) => `M${pt(a)} L${pt(b)}`;
/**
 * A bent limb with a readable joint: two straight bones meeting in a small rounded corner at the joint.
 * The corner radius grows with the bend, so a nearly straight arm stays straight and a sharp bend
 * shows a clear elbow instead of a noodle-like arc.
 */
function limbJoint(a, j, b, r = 0.16) {
  const len = (v) => Math.hypot(v[0], v[1]);
  const u1 = sub(j, a);
  const u2 = sub(b, j);
  const l1 = len(u1);
  const l2 = len(u2);
  if (l1 < 1e-6 || l2 < 1e-6) return line(a, b);
  const cos = (u1[0] * u2[0] + u1[1] * u2[1]) / (l1 * l2);
  const bend = Math.acos(Math.max(-1, Math.min(1, cos))); // 0 = straight
  const rr = Math.min(r * Math.min(1, bend / 1.2), l1 * 0.45, l2 * 0.45);
  const p1 = sub(j, mul(u1, rr / l1));
  const p2 = add(j, mul(u2, rr / l2));
  return `M${pt(a)} L${pt(p1)} Q${pt(j)} ${pt(p2)} L${pt(b)}`;
}

// ---------- parts renderer ----------
let UID = 0;

/** Filters shared by every Milo on a page. */
export function miloDefs(wobble = STYLE.wobble) {
  const wob = (id, seed) => `<filter id="${id}" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="2" seed="${seed}" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="${wobble * 2}" xChannelSelector="R" yChannelSelector="G"/>
</filter>`;
  // miloWobble is the still look; miloWobble1..3 are alternative seeds for line boil in animation
  return `${wob('miloWobble', 7)}${wob('miloWobble1', 21)}${wob('miloWobble2', 34)}${wob('miloWobble3', 55)}
<filter id="miloEdge" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">
  <feGaussianBlur in="SourceAlpha" stdDeviation="0.28" result="b"/>
  <feOffset in="b" dx="-0.1" dy="-0.13" result="o"/>
  <feComposite in="SourceAlpha" in2="o" operator="out" result="e1"/>
  <feComponentTransfer in="e1" result="edge"><feFuncA type="linear" slope="0.32"/></feComponentTransfer>
  <feGaussianBlur in="edge" stdDeviation="0.13" result="e2"/>
  <feComposite in="e2" in2="SourceAlpha" operator="in" result="edgeS"/>
  <feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="3" seed="3" result="t"/>
  <feColorMatrix in="t" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.12 -0.03" result="tA"/>
  <feComposite in="tA" in2="SourceAlpha" operator="in" result="tex"/>
  <feMerge result="m"><feMergeNode in="edgeS"/><feMergeNode in="tex"/></feMerge>
  <feFlood flood-color="${STYLE.shade}"/>
  <feComposite in2="m" operator="in"/>
</filter>
<filter id="miloSoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="0.09"/></filter>`;
}

/**
 * parts: [{ tf, k, shapes:[d], tubes:[{d,w}], seams:[[x,y,r]], pre, detail, ring }]
 *  tf: SVG transform from the part's own space to figure space; k: its scale (keeps ink width constant)
 *  seams: circles (part space) where the part grows out of the one below it: no inner outline there
 *  pre: SVG in figure space drawn under the part but only over the parts below it (cast shadows)
 */
export function renderParts(parts, { t = STYLE.line, ink = STYLE.ink, skin = STYLE.skin } = {}) {
  const u = `milo${UID++}_`;
  const inkOf = (p) => {
    const k = p.k || 1;
    let s = '';
    for (const d of p.shapes || []) s += `<path d="${d}" fill="${ink}" stroke="${ink}" stroke-width="${f((2 * t) / k)}" stroke-linejoin="round"/>`;
    for (const tb of p.tubes || []) s += `<path d="${tb.d}" fill="none" stroke="${ink}" stroke-width="${f(tb.w + (2 * t) / k)}" stroke-linecap="round" stroke-linejoin="round"/>`;
    return s;
  };
  const geoOf = (p, col) => {
    let s = '';
    for (const d of p.shapes || []) s += `<path d="${d}" fill="${col}"/>`;
    for (const tb of p.tubes || []) s += `<path d="${tb.d}" fill="none" stroke="${col}" stroke-width="${f(tb.w)}" stroke-linecap="round" stroke-linejoin="round"/>`;
    return s;
  };
  const g = (tf, inner) => (tf ? `<g transform="${tf}">${inner}</g>` : inner);
  let defs = '';
  parts.forEach((p, i) => {
    defs += `<g id="${u}g${i}">${g(p.tf, geoOf(p, '#fff'))}</g>`;
  });
  let out = '';
  // 1. the outer silhouette: every part's ink, all together
  out += parts.map((p) => g(p.tf, inkOf(p))).join('');
  // 2. parts in order: inner outline (only over earlier parts), then the fill, then details
  parts.forEach((p, i) => {
    if (i > 0) {
      let m = `<rect x="-60" y="-60" width="120" height="120" fill="#000"/>`;
      for (let j = 0; j < i; j++) m += `<use href="#${u}g${j}"/>`;
      m += g(p.tf, (p.seams || []).map((s) => `<path d="${circle([s[0], s[1]], s[2])}" fill="#000"/>`).join(''));
      defs += `<mask id="${u}m${i}" maskUnits="userSpaceOnUse" x="-60" y="-60" width="120" height="120">${m}</mask>`;
      if (p.pre) out += `<g mask="url(#${u}m${i})">${p.pre}</g>`;
      if (p.ring !== false) out += `<g mask="url(#${u}m${i})">${g(p.tf, inkOf(p))}</g>`;
    }
    out += g(p.tf, geoOf(p, p.fill || skin));
    if (p.detail) out += g(p.tf, p.detail);
  });
  // 3. soft watercolour shading along the outer edge, multiplied over everything
  out += `<g filter="url(#miloEdge)" style="mix-blend-mode:multiply" opacity="0.7">${parts.map((p) => g(p.tf, geoOf(p, skin))).join('')}</g>`;
  // details drawn again on top of the shading so eyes stay crisp black
  parts.forEach((p) => {
    if (p.detail) out += g(p.tf, p.detail);
  });
  return `<defs>${defs}</defs>${out}`;
}

// ---------- hands ----------
// Hand space: wrist at (0,0), fingers point to +y, thumb on the +x side, 1 = palm width.
const FW = 0.22; // finger width
const fingerTube = (base, deg, len, w = FW) => ({ d: line(base, add(base, mul(dir(deg), len))), w });
function handParts(kind, opt = {}) {
  const P = [];
  const palmRound = smooth([[-0.36, 0], [-0.5, 0.3], [-0.5, 0.72], [-0.3, 0.92], [0.3, 0.92], [0.5, 0.72], [0.5, 0.3], [0.36, 0]]);
  // curled fingers seen from the knuckle side: short rounded capsules in a row
  const knuckles = (xs, y, r = 0.16) => xs.forEach((x) => P.push({ tubes: [{ d: line([x, y - 0.36], [x, y]), w: r * 1.55 }], seams: [[x, y - 0.36, r * 0.95]] }));
  const curledThumb = () => P.push({ tubes: [{ d: smooth([[0.5, 0.2], [0.4, 0.46], [0.02, 0.56]], false), w: 0.27 }], seams: [[0.5, 0.2, 0.16]] });
  switch (kind) {
    case 'ball': {
      // the default hand: a perfect circle, fully outlined (also where it sits over the wrist)
      P.push({ round: true, shapes: [circle([0, 0.5], 0.55)] });
      break;
    }
    case 'grip': {
      // a fist closed around a wooden stick (the stick runs across the fingers, passing behind the fist):
      // the fist is one clean shape with knuckle scallops on its edge and a soft shadow on the lower side,
      // with no inner finger lines and no thumb
      const [s0, s1] = opt.stick || [-0.95, 1.15]; // stick ends along the hand's x axis (+x is the top when the fingers point right)
      P.push({ round: true, shapes: [], tubes: [{ d: line([s0, 0.66], [s1, 0.66]), w: 0.22 }], fill: '#8a7560' });
      P.push({
        base: true,
        shapes: [
          smooth([[-0.3, -0.04], [-0.38, 0.12], [-0.52, 0.3], [-0.56, 0.62], [-0.44, 0.94], [0.44, 0.96], [0.56, 0.64], [0.5, 0.3], [0.38, 0.12], [0.3, -0.04]]),
        ],
        detail: [
          `<path d="M-0.56 0.62 C-0.36 0.8 0.3 0.84 0.55 0.6" fill="none" stroke="${STYLE.shade}" stroke-width="0.09" stroke-linecap="round" opacity="0.4"/>`,
          `<path d="M-0.44 0.94 Q0 1.0 0.44 0.96" fill="none" stroke="${STYLE.shade}" stroke-width="0.08" stroke-linecap="round" opacity="0.5"/>`,
        ].join(''),
      });
      break;
    }
    case 'mitt': {
      // relaxed hanging hand: a round mitten, the thumb drawn as a hooked crease on the inner side
      P.push({ base: true, shapes: [smooth([[-0.3, 0], [-0.5, 0.3], [-0.56, 0.72], [-0.38, 1.04], [-0.02, 1.13], [0.3, 1.02], [0.46, 0.76], [0.42, 0.42], [0.31, 0]])] });
      P.push({ ring: false, detail: `<path d="M0.2 0.5 C0.11 0.72 0.13 0.95 0.38 0.99" stroke-width="0.09"/>` });
      break;
    }
    case 'fist': {
      P.push({ base: true, shapes: [palmRound] });
      knuckles([-0.36, -0.12, 0.12, 0.36], 0.9);
      curledThumb();
      break;
    }
    case 'open': {
      P.push({ base: true, shapes: [ellipse([0, 0.46], 0.5, 0.48)] });
      const fingers = [
        [[-0.33, 0.62], -20, 0.68],
        [[-0.11, 0.7], -6, 0.86],
        [[0.11, 0.7], 6, 0.88],
        [[0.31, 0.64], 18, 0.76],
      ];
      for (const [b, a, l] of fingers) P.push({ tubes: [fingerTube(b, a, l)], seams: [[b[0], b[1], 0.12]] });
      P.push({ tubes: [fingerTube([0.34, 0.34], 48, 0.55, 0.25)], seams: [[0.34, 0.34, 0.14]] });
      break;
    }
    case 'point': {
      // the round hand with the index finger out. As in classic cartoon pointing hands, the finger leaves
      // from the top edge of the fist, not its middle: its top line runs on from the ball's outline in one
      // stroke (same part, so no seam), it tapers a little to a round tip, and the only inner line is the
      // small fold where its underside meets the ball.
      const finger = 'M0.555 0.42 C0.56 0.9 0.55 1.35 0.54 1.68 Q0.535 1.87 0.39 1.87 Q0.25 1.87 0.25 1.69 L0.25 0.7 Z';
      P.push({ round: true, shapes: [circle([0, 0.5], 0.55), finger] });
      P.push({ ring: false, detail: `<path d="M0.25 0.99 Q0.17 0.86 0.04 0.84" stroke-width="0.075"/>` });
      break;
    }
    case 'thumb': {
      // fist seen from the side, thumb along +y (rotate the hand to point it up or down)
      P.push({ base: true, shapes: [smooth([[-0.4, 0], [-0.46, 0.4], [-0.42, 0.88], [0.1, 0.96], [0.5, 0.86], [0.52, 0.4], [0.42, 0]])] });
      for (const y of [0.16, 0.38, 0.6, 0.8]) P.push({ tubes: [{ d: line([0.12, y], [0.5, y]), w: 0.23 }], seams: [[0.08, y, 0.11]] });
      P.push({ tubes: [fingerTube([-0.24, 0.62], -4, 0.72, 0.27)], seams: [[-0.24, 0.62, 0.15]] });
      break;
    }
    case 'ok': {
      P.push({ base: true, shapes: [ellipse([0, 0.46], 0.5, 0.48)] });
      const fingers = [
        [[-0.33, 0.62], -16, 0.66],
        [[-0.11, 0.7], -5, 0.84],
        [[0.11, 0.7], 6, 0.82],
      ];
      for (const [b, a, l] of fingers) P.push({ tubes: [fingerTube(b, a, l)], seams: [[b[0], b[1], 0.12]] });
      // index + thumb ring
      P.push({ tubes: [{ d: circle([0.42, 0.92], 0.25), w: 0.16 }], seams: [[0.32, 0.66, 0.12]] });
      break;
    }
    case 'peace': {
      P.push({ base: true, shapes: [palmRound] });
      knuckles([-0.34, -0.1], 0.86, 0.15);
      P.push({ tubes: [fingerTube([0.07, 0.66], -9, 0.92)], seams: [[0.07, 0.66, 0.12]] });
      P.push({ tubes: [fingerTube([0.3, 0.66], 12, 0.88)], seams: [[0.3, 0.66, 0.12]] });
      curledThumb();
      break;
    }
    case 'explain':
    case 'flat': {
      // fingers together, palm open (a talking / presenting hand)
      P.push({ base: true, shapes: [smooth([[-0.34, 0], [-0.5, 0.35], [-0.5, 0.95], [-0.38, 1.3], [-0.12, 1.42], [0.12, 1.36], [0.3, 1.1], [0.42, 0.6], [0.36, 0]])] });
      P.push({ tubes: [fingerTube([0.3, 0.36], 34, 0.42, 0.25)], seams: [[0.3, 0.36, 0.14]] });
      P.push({ ring: false, detail: `<path d="${line([-0.22, 1.36], [-0.2, 0.98])} ${line([0.04, 1.4], [0.02, 1.02])}" stroke-width="0.06"/>` });
      break;
    }
    default:
      throw new Error(`unknown hand: ${kind}`);
  }
  return P;
}
export const HANDS = ['ball', 'grip', 'point', 'explain', 'open', 'thumb', 'ok', 'peace', 'fist', 'mitt'];

/** hand parts placed at a wrist: deg = direction the fingers point, flip = -1 mirrors (thumb to -x) */
function placeHand(kind, wrist, deg, flip, size, t, opt = {}) {
  const tf = `translate(${pt(wrist)}) rotate(${f(-deg)}) scale(${f(size * flip)} ${f(size)})`;
  return handParts(kind, opt).map((p) => ({
    ...p,
    tf,
    k: size,
    detail: p.detail ? `<g fill="none" stroke="${STYLE.ink}" stroke-linecap="round">${p.detail}</g>` : undefined,
    shapes: p.shapes,
    tubes: p.tubes,
    seams: p.round ? [] : p.base ? [[0, -0.05, 0.34]] : p.seams, // the palm grows out of the forearm without a wrist line
  }));
}

// ---------- face ----------
export const EXPR = {
  calm: { brows: { dy: -0.42, ang: -10, curve: 0.1, len: 0.38 } },
  netral: { brows: { dy: -0.09, ang: 0, curve: 0, len: 0.42, th: 0.1 } },
  senang: { eyes: 'happy', brows: null },
  antusias: { brows: { dy: -0.33, ang: 26, curve: 0, len: 0.38 }, browsR: { dy: -0.36, ang: 40, curve: 0, len: 0.34 }, extra: ['emph'] },
  penasaran: { brows: { dy: -0.32, ang: 10, curve: 0.06, len: 0.4 }, browsR: { dy: -0.34, ang: 32, curve: 0, len: 0.34 }, extra: ['?'] },
  kaget: { brows: { dy: -0.5, ang: -16, curve: 0.12, len: 0.34 }, extra: ['shock'] },
  takut: { brows: { dy: -0.42, ang: -24, curve: 0.07, len: 0.36 }, extra: ['sweat'] },
  kesal: { eyes: 'small', brows: { dy: -0.2, ang: 32, curve: -0.02, len: 0.46 }, extra: ['vein'] },
  bingung: { brows: { dy: -0.11, ang: 3, curve: 0, len: 0.4, th: 0.08 }, browsR: { dy: -0.16, ang: -8, curve: 0, len: 0.36, th: 0.08 }, extra: ['??'] },
  jelaskan: { brows: { dy: -0.32, ang: 16, curve: 0.02, len: 0.34 }, browsR: { dy: -0.36, ang: 6, curve: 0.05, len: 0.32 } },
  tunjuk: { brows: { dy: -0.3, ang: 30, curve: 0, len: 0.38 } },
  tidur: { eyes: 'sleep', brows: null },
  fokus: { brows: { dy: -0.3, ang: 14, curve: 0.02, len: 0.34 } }, // reading: brows slightly in; set look: [0, 1] to lower the eyes
  ngantuk: { brows: { dy: -0.3, ang: -6, curve: 0.04, len: 0.32 } },
  bicara: { brows: { dy: -0.3, ang: 22, curve: 0, len: 0.34 }, browsR: { dy: -0.4, ang: -12, curve: 0.08, len: 0.32 }, extra: ['emph'] },
};

function brow(c, b, mirror) {
  // a tapered stroke from the outer end to the inner end; ang > 0 drops the inner end (angry), < 0 lifts it (worried)
  const s = mirror ? -1 : 1;
  const half = b.len / 2;
  const a = rad(b.ang);
  const ux = Math.cos(a) * s;
  const uy = Math.sin(a);
  const p0 = [c[0] - ux * half, c[1] - uy * half];
  const p1 = [c[0] + ux * half, c[1] + uy * half];
  const n = [uy * s, -Math.abs(ux)]; // normal pointing up
  const th = b.th ?? 0.06;
  const m = mul(add(p0, p1), 0.5);
  const cu = add(m, mul(n, 2 * (b.curve + th / 2)));
  const cd = add(m, mul(n, 2 * (b.curve - th / 2)));
  // one soft stroke with round ends: the brow arcs through its control point
  const mid = add(m, mul(n, 2 * b.curve));
  return `<path d="M${pt(p0)} Q${pt(mid)} ${pt(p1)}" fill="none" stroke="${STYLE.ink}" stroke-width="${f(th * 1.15)}" stroke-linecap="round"/>`;
}

function face(expr, { eyes = 2, faceX = 0, look = [0, 0], blink = 0 } = {}) {
  const e = typeof expr === 'string' ? EXPR[expr] : expr;
  const ink = STYLE.ink;
  let s = '';
  const eyeY = 0.06 + (e.eyes === 'small' ? 0.08 : 0);
  const centres = eyes === 2 ? [[-0.34 + faceX, eyeY], [0.34 + faceX, eyeY]] : [[faceX, eyeY]];
  centres.forEach((c, i) => {
    const ec = add(c, mul(look, 0.08));
    if (e.eyes === 'sleep') {
      // closed, relaxed eyes: a soft downward arc
      s += `<path d="M${pt(add(ec, [-0.16, -0.03]))} Q${pt(add(ec, [0, 0.13]))} ${pt(add(ec, [0.16, -0.03]))}" fill="none" stroke="${ink}" stroke-width="0.07" stroke-linecap="round"/>`;
    } else if (e.eyes === 'happy') {
      s += `<path d="M${pt(add(ec, [-0.14, 0.05]))} Q${pt(add(ec, [0, -0.2]))} ${pt(add(ec, [0.14, 0.05]))}" fill="none" stroke="${ink}" stroke-width="0.07" stroke-linecap="round"/>`;
    } else {
      const rx = (e.eyes === 'small' ? 0.08 : 0.093) * (eyes === 1 ? 0.92 : 1);
      const ry = (e.eyes === 'small' ? 0.135 : 0.17) * (1 - blink * 0.92);
      s += `<path d="${ellipse(ec, rx, ry)}" fill="${ink}"/>`;
    }
    const b = i === 1 && e.browsR ? e.browsR : e.brows;
    if (b) s += brow([c[0], c[1] + b.dy], b, eyes === 2 && i === 1);
  });
  for (const x of e.extra || []) s += extra(x);
  return s;
}

function extra(kind) {
  const ink = STYLE.ink;
  const st = `fill="none" stroke="${ink}" stroke-width="0.07" stroke-linecap="round"`;
  const font = `font-family="Patrick Hand, Comic Sans MS, sans-serif" fill="${ink}"`;
  switch (kind) {
    case '?':
      return `<text x="1.02" y="-0.9" font-size="0.78" ${font}>?</text>`;
    case '??':
      return `<text x="0.95" y="-0.85" font-size="0.72" ${font} letter-spacing="-0.08">??</text>`;
    case 'shock':
      return `<path d="${line([-1.18, -0.78], [-1.42, -1.02])} ${line([-1.26, -0.52], [-1.62, -0.66])} ${line([-0.95, -1.05], [-1.05, -1.36])}" ${st}/>`;
    case 'emph':
      return `<path d="${line([1.06, -0.82], [1.28, -1.1])} ${line([1.2, -0.55], [1.5, -0.68])} ${line([1.26, -0.22], [1.56, -0.22])}" ${st}/>`;
    case 'vein': {
      const c = [1.05, -0.98];
      const arc = (a) => {
        const p = rot([0.06, -0.24], a);
        const q = rot([0.24, -0.06], a);
        return `M${pt(add(c, p))} Q${pt(add(c, rot([0.07, -0.07], a)))} ${pt(add(c, q))}`;
      };
      return `<path d="${arc(0)} ${arc(90)} ${arc(180)} ${arc(270)}" ${st}/>`;
    }
    case 'sweat': {
      const drop = (c, sc) => {
        const d = `M${pt(add(c, [0, -0.07 * sc]))} Q${pt(add(c, [0.06 * sc, 0.02 * sc]))} ${pt(add(c, [0, 0.06 * sc]))} Q${pt(add(c, [-0.06 * sc, 0.02 * sc]))} ${pt(add(c, [0, -0.07 * sc]))}Z`;
        return `<path d="${d}" fill="#fff" stroke="${ink}" stroke-width="0.035"/>`;
      };
      return [[-0.8, 0.0, 1], [-0.86, 0.2, 0.8], [-0.72, 0.36, 1.2], [0.82, -0.05, 0.9], [0.76, 0.3, 1.2], [0.86, 0.16, 0.7]].map(([x, y, sc]) => drop([x, y], sc)).join('');
    }
    default:
      return '';
  }
}

// ---------- body ----------
// torso outlines relative to the hip centre, front and profile (profile faces +x)
const TORSO_FRONT = [[0.25, -1.9], [0.27, -1.58], [0.4, -1.32], [0.5, -1.08], [0.53, -0.7], [0.53, -0.3], [0.5, 0.0], [0.36, 0.1], [0.14, 0.13], [0, 0.13]];
const TORSO_SIDE = [[0.17, -1.9], [0.19, -1.56], [0.32, -1.22], [0.37, -0.75], [0.36, -0.3], [0.3, 0.04], [0.1, 0.16], [-0.16, 0.16], [-0.33, 0.02], [-0.36, -0.45], [-0.34, -0.95], [-0.27, -1.32], [-0.17, -1.58], [-0.15, -1.9]];
function frontTorso() {
  const right = TORSO_FRONT;
  const left = TORSO_FRONT.slice(0, -1).reverse().map(([x, y]) => [-x, y]);
  return [...right, ...left];
}

export const NEUTRAL = {
  x: 0,
  y: 0,
  scale: 100,
  view: 'front', // 'front' | 'side' | 'back'
  facing: 1, // side view: 1 faces screen right, -1 screen left
  lean: 0, // torso tilt around the hips, degrees (+ = clockwise, i.e. forward when facing right)
  hip: [0, 0], // hip offset (sitting, jumping)
  headTilt: 0,
  expr: 'calm',
  faceX: 0, // slide the face toward the side Milo looks to (-0.15..0.15)
  look: [0, 0],
  blink: 0,
  // arms and legs are named by screen side in front/back view, near/far in side view
  armL: { a1: -20, a2: -13, hand: 'ball', z: 'body' },
  armR: { a1: 20, a2: 13, hand: 'ball', z: 'body' },
  legL: { a1: -2.7, a2: -2.7, foot: 0 },
  legR: { a1: 2.7, a2: 2.7, foot: 0 },
  shadow: true,
  line: STYLE.line,
};

export function pose(o = {}) {
  const p = { ...NEUTRAL, ...o };
  for (const k of ['armL', 'armR', 'legL', 'legR']) p[k] = { ...NEUTRAL[k], ...(o[k] || {}) };
  return p;
}

// Human joint ranges (motion guide, "Referensi Sudut"): elbow and knee bend 0..150 degrees, one way only.
// In side view (facing right) an elbow folds forward (a2 >= a1) and a knee folds backward (a2 <= a1).
export const LIMITS = { elbow: [0, 150], knee: [0, 150], head: [-45, 45] };
const clampTo = (x, [lo, hi]) => Math.min(hi, Math.max(lo, x));

function buildArm(side, a, root, lean, t, view) {
  const r = PROP;
  const a2 = view === 'side' && a.limit !== false ? a.a1 + clampTo(a.a2 - a.a1, LIMITS.elbow) : a.a2;
  const k = a.len ?? 1; // arm stretch (1 = human length); only for cartoon moments such as a load held overhead
  const elbow = add(root, mul(dir(a.a1 + lean), r.upperArm * k));
  // fore < 1 foreshortens the forearm when it points toward the camera (front view, hands held up in front)
  const wrist = add(elbow, mul(dir(a2 + lean), r.foreArm * k * (a.fore ?? 1)));
  const arm = { tubes: [{ d: limbJoint(root, elbow, wrist), w: r.armW }], seams: [[root[0], root[1], r.armW * 0.8]] };
  const handDeg = a.handDeg ?? a2 + lean;
  const flip = a.flip ?? (side === 'L' ? 1 : -1);
  const hs = (a.handSize ?? 1) * r.hand;
  const hand = placeHand(a.hand, add(wrist, mul(dir(handDeg), -0.04)), handDeg, flip, hs, t, { stick: a.stick });
  const out = [arm, ...hand.map((q) => ({ ...q, htag: `hand${side}` }))].map((q) => ({ ...q, tag: `arm${side}` }));
  // where the hand is, for props held in it: the palm centre and the direction the fingers point
  out.joint = { elbow, wrist, hand: add(wrist, mul(dir(handDeg), 0.46 * hs)), handDeg };
  return out;
}

function buildLeg(side, l, hip, lean, view, t) {
  const r = PROP;
  const a2 = view === 'side' && l.limit !== false ? l.a1 - clampTo(l.a1 - l.a2, LIMITS.knee) : l.a2;
  const knee = add(hip, mul(dir(l.a1), r.thigh));
  const ankle = add(knee, mul(dir(a2), r.shin));
  const leg = { tubes: [{ d: limbJoint(hip, knee, ankle, 0.24), w: r.legW }], seams: [[hip[0], hip[1], r.legW * 0.7]] };
  let shin = null;
  if (l.split) {
    // thigh and shin as separate parts, so a shin crossing in front of its thigh keeps its outline
    leg.tubes = [{ d: line(hip, knee), w: r.legW }];
    shin = { tubes: [{ d: line(knee, ankle), w: r.legW * 0.96 }], seams: [[knee[0], knee[1], r.legW * 0.62]] };
  }
  // foot: front view = a rounded nub pointing out; side view = a long shoe pointing forward
  const out = side === 'L' ? -1 : 1;
  let heel;
  let toe;
  if (view === 'side') {
    heel = add(ankle, rot([-0.08, 0.06], l.foot));
    toe = add(ankle, rot([0.36, 0.06], l.foot));
  } else {
    heel = add(ankle, rot([-0.05 * out, 0.07], l.foot * out));
    toe = add(ankle, rot([0.3 * out, 0.08], l.foot * out));
  }
  (shin || leg).tubes.push({ d: line(heel, toe), w: r.footW });
  return { leg, shin, ankle, knee };
}

/** Builds Milo's parts for a pose (figure space). */
export function miloParts(pz) {
  const p = pose(pz);
  const r = PROP;
  const t = p.line;
  const side = p.view === 'side';
  const hipC = add([0, r.hipY], p.hip);
  const torsoPts = (side ? TORSO_SIDE : frontTorso()).map((q) => rot(add(hipC, q), p.lean, hipC));
  const torso = { shapes: [smooth(torsoPts)] };
  const sh = (x) => rot(add(hipC, [x, r.shoulderY - r.hipY]), p.lean, hipC);
  const neck = rot(add(hipC, [side ? 0.02 : 0, r.neckY - r.hipY]), p.lean, hipC);
  const headC = add(neck, rot([side ? 0.06 : 0, r.headY - r.neckY], p.headTilt + p.lean * 0.5));

  // shoulders and hips
  const shL = side ? sh(0.0) : sh(-r.shoulderX);
  const shR = side ? sh(0.02) : sh(r.shoulderX);
  const hipL = side ? add(hipC, [0.0, 0]) : add(hipC, [-r.hipX, 0.02]);
  const hipR = side ? add(hipC, [0.0, 0]) : add(hipC, [r.hipX, 0.02]);

  const legL = buildLeg('L', p.legL, hipL, p.lean, p.view, t);
  const legR = buildLeg('R', p.legR, hipR, p.lean, p.view, t);
  const armL = buildArm('L', p.armL, shL, p.lean, t, p.view);
  const armR = buildArm('R', p.armR, shR, p.lean, t, p.view);

  // head
  const headTf = `translate(${pt(headC)}) rotate(${f(p.headTilt + p.lean * 0.5)})`;
  const back = p.view === 'back';
  const eyes = p.eyes ?? (side ? 1 : 2);
  const faceSvg = back ? '' : face(p.expr, { eyes, faceX: side && eyes === 1 ? 0.58 : p.faceX, look: p.look, blink: p.blink });
  const head = {
    tf: headTf,
    shapes: [circle([0, 0], 1)],
    pre: `<path d="${ellipse(add(headC, [0.06, 1.0]), 0.5, 0.2)}" fill="${STYLE.shade}" opacity="0.75" filter="url(#miloSoft)"/>`,
    detail: faceSvg,
  };

  // z order
  const parts = [];
  // from behind, Milo's hands always come forward of the body: the arms are drawn in front of the torso
  const zArm = (a, arm, z) => {
    const eff = p.view === 'back' && a.z === 'body' ? 'front' : a.z;
    return eff === z && !a.hide ? arm : [];
  };
  if (side) {
    // L = far side, R = near side
    parts.push(...zArm(p.armL, armL, 'back'), ...zArm(p.armL, armL, 'body'));
    if (!p.legL.hide) parts.push(legL.leg, ...(legL.shin ? [legL.shin] : []));
    parts.push(torso);
    parts.push(legR.leg);
    if (legR.shin) parts.push(legR.shin);
    parts.push(...zArm(p.armR, armR, 'back'), ...zArm(p.armR, armR, 'body'));
  } else {
    parts.push(...zArm(p.armL, armL, 'back'), ...zArm(p.armR, armR, 'back'));
    parts.push(torso, legL.leg, legR.leg);
    if (legL.shin) parts.push(legR.shin, legL.shin);
    parts.push(...zArm(p.armL, armL, 'body'), ...zArm(p.armR, armR, 'body'));
  }
  parts.push(head);
  parts.push(...zArm(p.armL, armL, 'front'), ...zArm(p.armR, armR, 'front'));
  // joints for scene code: ground contact, props, camera framing
  const legs = [p.legL.hide ? null : legL, legR].filter(Boolean);
  const low = Math.max(...legs.map((l) => Math.max(l.ankle[1] + 0.23, l.knee[1] + r.legW / 2)));
  return { parts, p, headC, ground: Math.max(legL.ankle[1], legR.ankle[1]), low, joints: { headC, kneeL: legL.knee, kneeR: legR.knee, ankleL: legL.ankle, ankleR: legR.ankle, shL, shR, hipL, hipR, handL: armL.joint.hand, handR: armR.joint.hand, wristL: armL.joint.wrist, wristR: armR.joint.wrist, elbowL: armL.joint.elbow, elbowR: armR.joint.elbow } };
}

export function drawMilo(pz = {}) {
  // three-quarter view: the front build turned a little toward `facing`: the face slides that way, the body
  // narrows, and the figure keeps its own wobble and shadow
  if (pz.view === 'three') {
    const k = pz.facing ?? 1;
    const q = pose({ ...pz, view: 'front', faceX: (pz.faceX ?? 0) + k * 0.26 });
    const { parts: tp } = miloParts(q);
    const inner = renderParts(tp, { t: q.line });
    const sh = q.shadow ? `<path d="${ellipse([0, 0.02], 1.05, 0.13)}" fill="#6e5a44" opacity="0.42" filter="url(#miloSoft)"/>` : '';
    return `<g transform="translate(${f(q.x)} ${f(q.y)})" opacity="${q.opacity ?? 1}"><g filter="url(#${q.wobbleId || 'miloWobble'})"><g transform="scale(${f(q.scale)} ${f(q.scale)})">${sh}<g transform="translate(${f(k * 0.06)} 0) scale(0.8 1)">${inner}</g></g></g></g>`;
  }
  const built = miloParts(pz);
  const p = built.p;
  // only: draw just one arm (e.g. 'armR') again on top of a prop, so a hand holding a box stays in front
  // only: 'armR' redraws the whole arm, 'handR' just the hand (a book held in front of the upper arms)
  const parts = pz.only ? built.parts.filter((q) => q.tag === pz.only || q.htag === pz.only) : built.parts;
  if (pz.only) p.shadow = false;
  const flip = p.view === 'side' && p.facing === -1 ? -1 : 1;
  const shadow = p.shadow
    ? `<path d="${ellipse([0, 0.02], 1.05, 0.13)}" fill="#6e5a44" opacity="0.42" filter="url(#miloSoft)"/>`
    : '';
  // the wobble filter sits in a group that moves with Milo, so the hand-drawn wobble travels with him
  // instead of the lines swimming through a fixed noise field
  const rot = p.rot ? ` rotate(${f(p.rot)})` : '';
  const sq = p.squash ? ` scale(${f(1 + p.squash * 0.5)} ${f(1 - p.squash)})` : '';
  return `<g transform="translate(${f(p.x)} ${f(p.y)})" opacity="${p.opacity ?? 1}"><g filter="url(#${p.wobbleId || 'miloWobble'})"><g transform="${rot.trim()}${sq} scale(${f(p.scale * flip)} ${f(p.scale)})">${shadow}${renderParts(parts, { t: p.line })}</g></g></g>`;
}

/** One hand on a short wrist stub, fingers pointing `deg` (180 = up). */
export function drawHand(kind, { x = 0, y = 0, scale = 100, deg = 180, flip = 1, stub = 0.9, stubDeg, size = 1.4, wrist: ww = 0.3, line = STYLE.line } = {}) {
  const wrist = [0, 0];
  const back = add(wrist, mul(dir(stubDeg ?? deg), -stub));
  const arm = { tubes: [{ d: line_(back, wrist), w: ww }] };
  const hand = placeHand(kind, wrist, deg, flip, PROP.hand * size, line);
  const parts = stub > 0 ? [arm, ...hand] : hand;
  return `<g filter="url(#miloWobble)"><g transform="translate(${f(x)} ${f(y)}) scale(${f(scale)})">${renderParts(parts, { t: line })}</g></g>`;
}
const line_ = line;

// ---------- pose presets (from the v2.1 reference sheet) ----------
const calm = 'calm';
export const POSES = {
  front: {},
  side: { view: 'side', facing: -1, armR: { a1: 6, a2: 2 }, armL: { hide: true }, legL: { hide: true }, legR: { a1: 0, a2: 0 }, headTilt: -3 },
  back: { view: 'back' },
  berdiri: { expr: calm },
  berjalan: {
    view: 'side', facing: 1, lean: 4, expr: calm,
    legR: { a1: 24, a2: 8, foot: 0 },
    legL: { a1: -22, a2: -42, foot: 30 },
    armR: { a1: -26, a2: -6 },
    armL: { a1: 26, a2: 52 },
    hip: [0, 0.07],
  },
  berlari: {
    view: 'side', facing: 1, lean: 16, expr: calm,
    legR: { a1: 62, a2: 2, foot: -6 },
    legL: { a1: -42, a2: -98, foot: 70 },
    armR: { a1: 34, a2: 102 },
    armL: { a1: -48, a2: -88 },
    hip: [0, 0.02],
  },
  duduk: {
    hip: [0, 1.36], expr: calm,
    legL: { a1: -74, a2: 78, foot: -30, split: true },
    legR: { a1: 74, a2: -78, foot: -30, split: true },
    armL: { a1: -26, a2: -20 },
    armR: { a1: 26, a2: 20 },
  },
  menjelaskan: {
    expr: 'jelaskan', faceX: 0.08,
    armR: { a1: 50, a2: 118, hand: 'explain', handDeg: 104, flip: 1 },
  },
  menunjuk: {
    expr: 'tunjuk', faceX: 0.12,
    armR: { a1: 82, a2: 88, hand: 'point', handDeg: 90, flip: 1 },
  },
};
// raising the stick: elbow out at shoulder height, forearm up, the grip hand holds a long stick upright
POSES.angkatStick = {
  view: 'front', expr: 'kesal',
  // upper arm out level with the shoulder, a clear elbow, forearm straight up, the stick held upright
  armR: { a1: 88, a2: 178, hand: 'grip', handDeg: 90, flip: 1, stick: [-1.5, 2.7] },
  armL: { a1: -12, a2: -8, hand: 'ball' },
};
// older names
POSES.berbicara = POSES.menjelaskan;
