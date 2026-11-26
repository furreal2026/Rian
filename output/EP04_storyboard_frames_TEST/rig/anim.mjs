// Animation helpers for the Milo rig: easing, pose blending and the walk / run cycles.
// Poses here are plain objects for pose() in milo.mjs; nothing in this file draws.
import { pose, miloParts, PROP } from './milo.mjs';

export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2); // in-out cubic
export const easeOut = (t) => 1 - Math.pow(1 - t, 3);
export const easeIn = (t) => t * t * t;
/** 0..1 progress of time t through [a, b] */
export const span = (t, a, b) => clamp((t - a) / (b - a));
/** a spring-like settle: overshoots once and comes to rest at 1 */
export const backOut = (t) => {
  const c = 1.9;
  return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2);
};

/** Blend two poses: numbers and number arrays interpolate, everything else switches at t = 0.5. */
export function mix(a, b, t) {
  if (t <= 0) return a;
  if (t >= 1) return b;
  const out = {};
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) {
    const x = a[k];
    const y = b[k];
    if (typeof x === 'number' && typeof y === 'number') out[k] = lerp(x, y, t);
    else if (Array.isArray(x) && Array.isArray(y) && typeof x[0] === 'number') out[k] = x.map((v, i) => lerp(v, y[i], t));
    else if (x && y && typeof x === 'object' && typeof y === 'object' && !Array.isArray(x)) out[k] = mix(x, y, t);
    else out[k] = t < 0.5 ? (x ?? y) : (y ?? x);
  }
  return out;
}

const TAU = Math.PI * 2;

/**
 * Periodic smooth curve through keyframes: [[percent of the cycle, value], ...] (0..100, wraps).
 * Catmull-Rom between keys, so joint angles move smoothly and loop without a seam.
 */
export function cyc(keys, phase) {
  const x = (((phase % 1) + 1) % 1) * 100;
  const n = keys.length;
  let i = n - 1;
  for (let k = 0; k < n; k++) if (keys[k][0] <= x) i = k;
  const at = (k) => {
    const j = ((k % n) + n) % n;
    const wrap = Math.floor(k / n) * 100;
    return [keys[j][0] + wrap, keys[j][1]];
  };
  const p0 = at(i - 1);
  const p1 = at(i);
  const p2 = at(i + 1);
  const p3 = at(i + 2);
  const t = (x - p1[0]) / (p2[0] - p1[0] || 1);
  const m1 = ((p2[1] - p0[1]) / (p2[0] - p0[0])) * (p2[0] - p1[0]);
  const m2 = ((p3[1] - p1[1]) / (p3[0] - p1[0])) * (p2[0] - p1[0]);
  const t2 = t * t;
  const t3 = t2 * t;
  return (2 * t3 - 3 * t2 + 1) * p1[1] + (t3 - 2 * t2 + t) * m1 + (-2 * t3 + 3 * t2) * p2[1] + (t3 - t2) * m2;
}

// ---------- human gait data ----------
// Sagittal joint angles over one gait cycle of the right leg, 0 % = heel strike.
// Walking: normal adult gait at self-selected speed (hip about +30 flexion to -10 extension, stance knee
// flexion about 15, swing knee flexion about 60-65, ankle about 10 dorsi to 20 plantar at toe-off).
// Sources: clinical normal-gait references (Perry / Winter style curves, Univ. of Missouri "Normal Gait").
const WALK = {
  hip: [[0, 30], [10, 27], [30, 8], [50, -10], [60, -2], [75, 24], [87, 33], [100, 30]],
  knee: [[0, 4], [15, 17], [40, 4], [55, 22], [62, 40], [73, 62], [85, 30], [96, 3], [100, 4]],
  ankle: [[0, 0], [8, -6], [30, 6], [48, 10], [62, -18], [72, 0], [85, 2], [100, 0]], // + dorsiflexion
  shoulder: [[0, -16], [50, 16], [100, -16]], // arm swings opposite its own-side leg
  elbow: [[0, 12], [50, 30], [100, 12]], // more bent as the arm swings forward
};
// Running: stance about 0-40 %, flight 40-50 %, then the other leg. Hip flexion peaks about 55-60 in
// swing, the knee folds to about 100 in swing, foot strike with hip about 40 and knee about 25.
// Sources: running-gait chapter (Taylor & Francis), runner kinematics studies (PMC).
const RUN = {
  // measured values pushed about 20 % for a readable cartoon run (animators exaggerate the extremes)
  hip: [[0, 44], [20, 18], [40, -18], [55, 6], [75, 56], [88, 70], [100, 44]],
  knee: [[0, 26], [15, 44], [40, 18], [55, 70], [70, 120], [85, 84], [95, 34], [100, 26]],
  ankle: [[0, 4], [15, 18], [40, -26], [60, 0], [85, 6], [100, 4]],
  shoulder: [[0, -44], [50, 44], [100, -44]],
  elbow: [[0, 78], [50, 100], [100, 78]],
};

function gaitPose(D, phase, lean) {
  const leg = (ph) => {
    const hip = cyc(D.hip, ph);
    const knee = cyc(D.knee, ph);
    const ankle = cyc(D.ankle, ph);
    const a1 = hip - lean; // hip flexion is measured from the leaning trunk
    const a2 = a1 - knee; // the knee folds the shin back
    return { a1, a2, foot: -a2 - ankle };
  };
  const arm = (ph) => {
    const sh = cyc(D.shoulder, ph);
    return { a1: sh, a2: sh + cyc(D.elbow, ph) };
  };
  return {
    legR: leg(phase), // near leg
    legL: leg(phase + 0.5), // far leg, half a cycle later
    armR: arm(phase), // near arm swings back while the near leg is forward
    armL: arm(phase + 0.5),
  };
}

/** Human walk, facing screen right (side view). phase: 0..1 = one full cycle (two steps). */
export function walk(phase) {
  const lean = 3;
  const th = phase * TAU;
  return {
    ...gaitPose(WALK, phase, lean),
    lean: lean + 1.2 * Math.cos(2 * th), // a touch more lean at each heel strike
    headTilt: -lean * 0.5 + 1 * Math.sin(2 * th),
  };
}

/** Human run, facing screen right. phase: 0..1 = one full cycle (two strides). */
export function run(phase) {
  const lean = 13;
  const th = phase * TAU;
  // airborne in each flight phase (about 40-50 % and 90-100 % of the cycle)
  const flight = (ph) => Math.max(0, Math.sin(((((ph % 0.5) + 0.5) % 0.5) - 0.38) / 0.17 * Math.PI));
  return {
    ...gaitPose(RUN, phase, lean),
    lean: lean + 1.5 * Math.cos(2 * th),
    headTilt: -lean * 0.4,
    lift: 0.3 * (phase % 0.5 > 0.38 ? flight(phase) : 0),
  };
}

let groundRef = null;
/** Moves the hips so Milo's lowest point (a foot, or a knee when he kneels or sits) touches the ground. */
export function groundLock(pz) {
  if (groundRef === null) groundRef = miloParts(pose({ legL: { a1: 0, a2: 0 }, legR: { a1: 0, a2: 0 } })).low;
  const p = { ...pz, hip: [...(pz.hip || [0, 0])] };
  const g = miloParts(pose(p)).low;
  p.hip[1] += groundRef - g - (pz.lift || 0);
  return p;
}

/** Where a point of Milo's own (unscaled) drawing lands in world units, for a pose with rot/facing. */
export function toWorld(pz, q) {
  const p = pose(pz);
  const flip = p.view === 'side' && p.facing === -1 ? -1 : 1;
  const x = q[0] * flip;
  const y = q[1];
  const a = ((p.rot || 0) * Math.PI) / 180;
  return [x * Math.cos(a) - y * Math.sin(a), x * Math.sin(a) + y * Math.cos(a)];
}

// ---------- inverse kinematics ----------
const deg = (r) => (r * 180) / Math.PI;
/** Two-bone IK: angles (this rig's convention: 0 = down, 90 = screen right) placing the tip at target. */
function ik(root, target, l1, l2, bend) {
  const dx = target[0] - root[0];
  const dy = target[1] - root[1];
  const d = Math.min(Math.hypot(dx, dy), l1 + l2 - 1e-4);
  const th = deg(Math.atan2(dx, dy));
  const al = deg(Math.acos(Math.max(-1, Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)))));
  const a1 = th + bend * al;
  const e = [root[0] + l1 * Math.sin((a1 * Math.PI) / 180), root[1] + l1 * Math.cos((a1 * Math.PI) / 180)];
  const a2 = deg(Math.atan2(target[0] - e[0], target[1] - e[1]));
  return { a1, a2 };
}

/**
 * Put Milo's wrist on a target point (figure space, head radii, before facing/rot), like a hand reaching for
 * a handle. side: 'L' | 'R'. bend: -1 folds the elbow the human way in side view (facing right); in front
 * view pass +1 or -1 to choose the elbow side. Returns the pose with that arm set (other arm fields kept).
 */
export function reach(pz, side, target, bend = -1) {
  const p = pose(pz);
  const { joints } = miloParts(p);
  const root = side === 'L' ? joints.shL : joints.shR;
  const key = side === 'L' ? 'armL' : 'armR';
  const k = pz[key]?.len ?? 1;
  const { a1, a2 } = ik(root, target, PROP.upperArm * k, PROP.foreArm * k, bend);
  return { ...pz, [key]: { ...(pz[key] || {}), a1: a1 - p.lean, a2: a2 - p.lean } };
}

/** Put an ankle on a target point (a planted foot). bend: +1 folds the knee the human way (facing right). */
export function plant(pz, side, target, bend = 1) {
  const p = pose(pz);
  const { joints } = miloParts(p);
  const root = side === 'L' ? joints.hipL : joints.hipR;
  const { a1, a2 } = ik(root, target, PROP.thigh, PROP.shin, bend);
  const key = side === 'L' ? 'legL' : 'legR';
  return { ...pz, [key]: { ...(pz[key] || {}), a1, a2, foot: pz[key]?.foot ?? -a2 } };
}

/**
 * Elbow-down reach (a relaxed shoulder): the upper arm hangs at a fixed angle a1 (pose convention) and the
 * forearm points at the target. In front view a forearm coming toward the camera is foreshortened
 * (fore = distance / forearm length), which is how a book or phone held in front is drawn.
 */
export function reachDown(pz, side, target, a1) {
  const p = pose(pz);
  const { joints } = miloParts(p);
  const root = side === 'L' ? joints.shL : joints.shR;
  const key = side === 'L' ? 'armL' : 'armR';
  const k = pz[key]?.len ?? 1;
  const rad = ((a1 + p.lean) * Math.PI) / 180;
  const e = [root[0] + PROP.upperArm * k * Math.sin(rad), root[1] + PROP.upperArm * k * Math.cos(rad)];
  const dx = target[0] - e[0];
  const dy = target[1] - e[1];
  const a2 = (Math.atan2(dx, dy) * 180) / Math.PI - p.lean;
  const fore = Math.max(0.3, Math.min(1, Math.hypot(dx, dy) / (PROP.foreArm * k)));
  return { ...pz, [key]: { ...(pz[key] || {}), a1, a2, fore, limit: false } };
}
