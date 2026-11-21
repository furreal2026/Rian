// Curious Mind stick-figure rig (A4 Cozy Storytelling drawing grammar, code-drawn):
// white filled round head, slim white tapered torso, dark single-stroke limbs,
// small dark rounded hands and feet, simple facial marks. Identity lives in the
// rig JSON; poses and expressions are data. Nothing here invents a new design.
import { deg, lerp, ease, stepKey, sampleKeys, hashSeed, clamp } from './util.mjs';

const LIMB_PARAMS = ['lean', 'head_tilt', 'l_sh', 'l_el', 'r_sh', 'r_el', 'l_hip', 'l_knee', 'r_hip', 'r_knee', 'lift', 'squash'];

export function resolvePose(lib, name) {
  const base = lib.poses.stand;
  const p = lib.poses[name];
  if (!p) throw new Error(`Unknown pose "${name}". Known: ${Object.keys(lib.poses).join(', ')}`);
  return { ...base, ...p };
}
export function resolveExpression(lib, name) {
  const base = lib.expressions.neutral;
  const e = lib.expressions[name];
  if (!e) throw new Error(`Unknown expression "${name}". Known: ${Object.keys(lib.expressions).join(', ')}`);
  return { ...base, ...e, extras: e.extras || [] };
}

function blendPose(a, b, u) {
  const out = { ...b };
  for (const k of LIMB_PARAMS) out[k] = lerp(a[k] ?? 0, b[k] ?? 0, u);
  out.anchor = u < 0.5 ? a.anchor : b.anchor;
  out.behind = u < 0.5 ? a.behind : b.behind;
  return out;
}

/** Pose at time t from a pose track [{t, pose, blend?, ease?}]. */
export function poseAt(lib, track, t) {
  if (!track?.length) return resolvePose(lib, 'stand');
  const { key, since, prev } = stepKey(track, t);
  const target = resolvePose(lib, key.pose);
  const blend = key.blend ?? 0.22;
  if (!prev || since >= blend || t < key.t) return target;
  const from = poseAt(lib, track.slice(0, track.indexOf(key)), key.t - 1e-6);
  return blendPose(from, target, ease(key.ease || 'easeOutCubic', since / blend));
}

/** Apply procedural actions (walk/run/idle/bounce/nod/shake/nervous) on top of a pose. */
export function applyAction(pose, action, { t, distance = 0, scale = 1, seed = 0, rig }) {
  const p = { ...pose };
  const name = action?.action || 'idle';
  const amt = action?.amount ?? 1;
  const breathe = Math.sin(t * Math.PI * 2 * 0.28 + seed * 6);
  if (name === 'walk' || name === 'run' || name === 'walk_in_place') {
    const run = name === 'run';
    const stride = (run ? 190 : rig.walk?.stride ?? 128) * scale;
    const phase = name === 'walk_in_place' ? t * (run ? 2.6 : 1.7) * Math.PI * 2 : (distance / stride) * Math.PI;
    const swing = (run ? 38 : 24) * amt, armSwing = (run ? 42 : 20) * amt;
    const s = Math.sin(phase);
    p.l_hip = (p.l_hip ?? 0) + s * swing;
    p.r_hip = (p.r_hip ?? 0) - s * swing;
    p.l_knee = (p.l_knee ?? 0) - Math.max(0, -Math.cos(phase)) * (run ? 55 : 28) * amt;
    p.r_knee = (p.r_knee ?? 0) - Math.max(0, Math.cos(phase)) * (run ? 55 : 28) * amt;
    if (!action.keep_arms) {
      p.l_sh = (p.l_sh ?? 0) - s * armSwing;
      p.r_sh = (p.r_sh ?? 0) + s * armSwing;
      if (run) { p.l_el = (p.l_el ?? 0) - 70; p.r_el = (p.r_el ?? 0) + 70; }
    }
    p.lean = (p.lean ?? 0) + (run ? 9 : 3) * amt;
    p.lift = (p.lift ?? 0) + Math.abs(Math.cos(phase)) * (run ? 10 : 5) * amt;
  } else if (name === 'wave') {
    p.r_el = (p.r_el ?? 0) + Math.sin(t * Math.PI * 2 * (action.speed || 2.6)) * 24 * amt;
  } else if (name === 'gesture') {
    // Small talking-hands motion for on-screen explanations.
    p.r_el = (p.r_el ?? 0) + Math.sin(t * Math.PI * 2 * 1.3 + seed) * 14 * amt;
    p.r_sh = (p.r_sh ?? 0) + Math.sin(t * Math.PI * 2 * 0.9) * 6 * amt;
  } else if (name === 'bounce') {
    p.lift = (p.lift ?? 0) + Math.abs(Math.sin(t * Math.PI * 2 * (action.speed || 1.8))) * 30 * amt;
  } else if (name === 'nod') {
    p.head_tilt = (p.head_tilt ?? 0) + Math.sin(t * Math.PI * 2 * 2) * 0; // tilt is lateral; nod uses squash
    p.nod = Math.sin(t * Math.PI * 2 * (action.speed || 2.2)) * 6 * amt;
  } else if (name === 'shake_head') {
    p.head_tilt = (p.head_tilt ?? 0) + Math.sin(t * Math.PI * 2 * (action.speed || 2.6)) * 9 * amt;
  } else if (name === 'nervous') {
    p.lean = (p.lean ?? 0) + Math.sin(t * 37 + seed) * 1.2 * amt;
    p.l_el = (p.l_el ?? 0) + Math.sin(t * 29) * 4 * amt;
    p.r_el = (p.r_el ?? 0) + Math.sin(t * 31) * 4 * amt;
  }
  if (name !== 'freeze') {
    // Gentle life: breathing and a tiny arm drift so holds never look frozen.
    p.squash = (p.squash ?? 0) + breathe * 0.012;
    p.l_sh = (p.l_sh ?? 0) - breathe * 1.4;
    p.r_sh = (p.r_sh ?? 0) + breathe * 1.4;
  }
  return p;
}

const dir = a => [Math.sin(deg(a)), Math.cos(deg(a))];

/** Forward kinematics in actor-local units (origin = ground under hip, y down). */
export function solve(rig, pose) {
  const L = rig.leg, A = rig.arm, T = rig.torso;
  const leg = (hip, knee, sx) => {
    const k = [sx + dir(hip)[0] * L.upper, dir(hip)[1] * L.upper];
    const fa = hip + knee;
    const f = [k[0] + dir(fa)[0] * L.lower, k[1] + dir(fa)[1] * L.lower];
    return { knee: k, foot: f, footAngle: fa };
  };
  const ll = leg(pose.l_hip, pose.l_knee, -L.hip_spread);
  const rl = leg(pose.r_hip, pose.r_knee, L.hip_spread);
  // Hip height: feet anchor puts the lowest foot on the ground; hip anchor puts hip at origin.
  const lowest = Math.max(ll.foot[1], rl.foot[1]);
  const hipY = (pose.anchor === 'hip' ? 0 : -lowest) - (pose.lift || 0);
  const off = ([x, y]) => [x, y + hipY];
  const lean = deg(pose.lean || 0);
  const up = [Math.sin(lean), -Math.cos(lean)];
  const squash = 1 + (pose.squash || 0);
  const tl = T.length * squash;
  const neck = [up[0] * tl, hipY + up[1] * tl];
  const sh = (side) => {
    const d = T.length * squash - A.shoulder_drop;
    const half = lerp(T.bottom_w, T.top_w, d / T.length) / 2 - A.shoulder_inset;
    const perp = [Math.cos(lean), Math.sin(lean)];
    return [up[0] * d + perp[0] * half * side, hipY + up[1] * d + perp[1] * half * side];
  };
  const arm = (shoulder, s, e, side) => {
    const ua = s + (pose.lean || 0);
    const el = [shoulder[0] + dir(ua)[0] * A.upper, shoulder[1] + dir(ua)[1] * A.upper];
    const fa = ua + e;
    const hand = [el[0] + dir(fa)[0] * A.lower, el[1] + dir(fa)[1] * A.lower];
    return { shoulder, elbow: el, hand, angle: fa, side };
  };
  const lsh = sh(-1), rsh = sh(1);
  const headR = rig.head.r;
  const headUp = T.neck_overlap - headR;
  const ht = deg(pose.head_tilt || 0) + lean;
  const head = [neck[0] + Math.sin(ht) * -headUp, neck[1] + Math.cos(ht) * headUp + (pose.nod || 0)];
  return {
    hip: [0, hipY], neck, head, headAngle: ht, lean,
    legs: { l: { ...ll, knee: off(ll.knee), foot: off(ll.foot) }, r: { ...rl, knee: off(rl.knee), foot: off(rl.foot) } },
    arms: { l: arm(lsh, pose.l_sh, pose.l_el, -1), r: arm(rsh, pose.r_sh, pose.r_el, 1) },
  };
}

function drawLimb(ctx, rig, a, b, c) {
  ctx.beginPath();
  ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineTo(...c);
  ctx.strokeStyle = rig.colors.line; ctx.lineWidth = rig.line.limb; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.stroke();
}

function drawTorso(ctx, rig, sk) {
  const T = rig.torso;
  ctx.save();
  ctx.translate(...sk.hip);
  ctx.rotate(sk.lean);
  const len = Math.hypot(sk.neck[0] - sk.hip[0], sk.neck[1] - sk.hip[1]);
  const tw = T.top_w / 2, bw = T.bottom_w / 2;
  ctx.beginPath();
  ctx.moveTo(-tw, -len);
  ctx.quadraticCurveTo(0, -len - 8, tw, -len);
  ctx.bezierCurveTo(tw + 4, -len * 0.55, bw + 2, -len * 0.25, bw, -10);
  ctx.quadraticCurveTo(bw - 2, 6, 0, 8);
  ctx.quadraticCurveTo(-bw + 2, 6, -bw, -10);
  ctx.bezierCurveTo(-bw - 2, -len * 0.25, -tw - 4, -len * 0.55, -tw, -len);
  ctx.closePath();
  ctx.fillStyle = rig.colors.fill; ctx.fill();
  ctx.strokeStyle = rig.colors.line; ctx.lineWidth = rig.line.outline; ctx.lineJoin = 'round'; ctx.stroke();
  // Soft form shading on the side away from the key light (A4 gentle light).
  if (rig.colors.shade) {
    ctx.clip();
    ctx.fillStyle = rig.colors.shade;
    ctx.fillRect(bw * 0.25, -len - 10, bw * 2, len + 20);
  }
  ctx.restore();
}

function drawHead(ctx, rig, sk, expr, opts) {
  const r = rig.head.r, F = rig.face;
  ctx.save();
  ctx.translate(...sk.head);
  ctx.rotate(sk.headAngle);
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fillStyle = rig.colors.fill; ctx.fill();
  if (rig.colors.shade) {
    ctx.save(); ctx.clip();
    ctx.beginPath(); ctx.arc(r * 0.55, r * 0.2, r * 0.95, 0, Math.PI * 2);
    ctx.fillStyle = rig.colors.shade; ctx.fill();
    ctx.restore();
  }
  ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.strokeStyle = rig.colors.line; ctx.lineWidth = rig.line.outline; ctx.stroke();

  const fx = (opts.facing ? F.turn * r : 0) + (opts.gaze?.x || 0) * r * 0.08;
  const fy = (opts.gaze?.y || 0) * r * 0.06;
  const ex = F.eye_spacing * r, ey = F.eye_y * r + fy;
  const line = rig.colors.line;
  ctx.strokeStyle = line; ctx.fillStyle = line; ctx.lineCap = 'round'; ctx.lineWidth = rig.line.face;

  // Extras behind features
  if (expr.extras.includes('blush')) {
    ctx.save(); ctx.globalAlpha = 0.55; ctx.fillStyle = rig.colors.cheek;
    for (const s of [-1, 1]) { ctx.beginPath(); ctx.ellipse(fx + s * ex * 1.25, ey + r * 0.28, r * 0.15, r * 0.085, 0, 0, Math.PI * 2); ctx.fill(); }
    ctx.restore();
  }
  // Eyes
  const blink = opts.blink;
  for (const s of [-1, 1]) {
    const x = fx + s * ex, y = ey;
    const kind = blink ? 'closed' : expr.eyes;
    ctx.beginPath();
    if (kind === 'dot' || kind === 'sad') {
      const k = kind === 'sad' ? 0.9 : 1;
      ctx.ellipse(x, y, F.eye_rx * k, F.eye_ry * k, 0, 0, Math.PI * 2); ctx.fill();
    } else if (kind === 'wide') {
      ctx.ellipse(x, y, F.eye_rx * 1.35, F.eye_ry * 1.4, 0, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.fillStyle = '#FFFFFF'; ctx.arc(x + F.eye_rx * 0.4, y - F.eye_ry * 0.5, F.eye_rx * 0.42, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = line;
    } else if (kind === 'happy') {
      ctx.arc(x, y + F.eye_ry * 0.5, F.eye_rx * 1.5, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke();
    } else if (kind === 'closed') {
      ctx.moveTo(x - F.eye_rx * 1.3, y + 1); ctx.quadraticCurveTo(x, y + F.eye_ry * 0.55, x + F.eye_rx * 1.3, y + 1); ctx.stroke();
    } else if (kind === 'squint') {
      ctx.ellipse(x, y + 1, F.eye_rx * 1.1, F.eye_ry * 0.45, 0, 0, Math.PI * 2); ctx.fill();
    } else throw new Error(`Unknown eyes "${kind}"`);
  }
  // Brows: [left angle, right angle] in degrees (+ = inner end up), raise in px
  const [bl, br] = expr.brows || [0, 0];
  const by = F.brow_y * r - (expr.brow_raise || 0) + fy;
  const bLen = F.brow_len * r;
  if (expr.brows !== null) {
    for (const [s, a] of [[-1, bl], [1, br]]) {
      const cx = fx + s * ex, ang = deg(a) * s;
      ctx.beginPath();
      ctx.moveTo(cx - Math.cos(ang) * bLen / 2, by - Math.sin(ang) * bLen / 2);
      ctx.lineTo(cx + Math.cos(ang) * bLen / 2, by + Math.sin(ang) * bLen / 2);
      ctx.stroke();
    }
  }
  // Mouth
  const mx = fx, my = F.mouth_y * r + fy, mw = F.mouth_w * r;
  let mouth = expr.mouth;
  if (opts.talking) mouth = Math.floor(opts.time * 9) % 2 ? 'open_smile' : (mouth === 'frown' ? 'flat' : 'smile');
  ctx.beginPath();
  switch (mouth) {
    case 'smile': ctx.moveTo(mx - mw / 2, my - 2); ctx.quadraticCurveTo(mx, my + mw * 0.42, mx + mw / 2, my - 2); ctx.stroke(); break;
    case 'small_smile': ctx.moveTo(mx - mw / 3, my); ctx.quadraticCurveTo(mx, my + mw * 0.25, mx + mw / 3, my); ctx.stroke(); break;
    case 'flat': ctx.moveTo(mx - mw / 3, my + 2); ctx.lineTo(mx + mw / 3, my + 2); ctx.stroke(); break;
    case 'frown': ctx.moveTo(mx - mw / 2.4, my + 6); ctx.quadraticCurveTo(mx, my - mw * 0.25, mx + mw / 2.4, my + 6); ctx.stroke(); break;
    case 'o': ctx.ellipse(mx, my + 3, mw * 0.2, mw * 0.27, 0, 0, Math.PI * 2); ctx.fill(); break;
    case 'open_smile': case 'grin':
      ctx.moveTo(mx - mw / 2, my - 3); ctx.quadraticCurveTo(mx, my + mw * (mouth === 'grin' ? 0.7 : 0.5), mx + mw / 2, my - 3); ctx.closePath(); ctx.fill(); break;
    case 'wobble':
      ctx.moveTo(mx - mw / 2, my + 3);
      for (let i = 1; i <= 4; i++) ctx.lineTo(mx - mw / 2 + (mw * i) / 4, my + (i % 2 ? -3 : 3));
      ctx.stroke(); break;
    case 'smirk': ctx.moveTo(mx - mw / 3, my + 3); ctx.quadraticCurveTo(mx + mw * 0.1, my + 5, mx + mw / 2.2, my - 5); ctx.stroke(); break;
    default: throw new Error(`Unknown mouth "${mouth}"`);
  }
  // Extras in front
  if (expr.extras.includes('sweat')) {
    ctx.save(); ctx.fillStyle = '#9FD3F2'; ctx.strokeStyle = line; ctx.lineWidth = 2.5;
    const sx = -r * 0.82, sy = -r * 0.25;
    ctx.beginPath(); ctx.moveTo(sx, sy - 14); ctx.quadraticCurveTo(sx + 10, sy + 2, sx, sy + 8); ctx.quadraticCurveTo(sx - 10, sy + 2, sx, sy - 14); ctx.fill(); ctx.stroke();
    ctx.restore();
  }
  if (expr.extras.includes('tear')) {
    ctx.save(); ctx.fillStyle = '#9FD3F2';
    const tx = fx + ex, ty = ey + F.eye_ry * 1.6 + ((opts.time * 30) % 18);
    ctx.beginPath(); ctx.ellipse(tx, ty, 3.5, 5.5, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  if (expr.extras.includes('sparkle')) {
    ctx.save(); ctx.fillStyle = '#FFD36E'; ctx.strokeStyle = line; ctx.lineWidth = 2;
    const tw = 1 + Math.sin(opts.time * 8) * 0.25;
    for (const [x, y, k] of [[r * 1.15, -r * 0.8, 1], [r * 1.45, -r * 0.25, 0.6], [-r * 1.2, -r * 0.9, 0.7]]) star(ctx, x, y, 11 * k * tw);
    ctx.restore();
  }
  ctx.restore();
}
function star(ctx, x, y, s) {
  ctx.beginPath();
  ctx.moveTo(x, y - s); ctx.quadraticCurveTo(x, y, x + s, y); ctx.quadraticCurveTo(x, y, x, y + s);
  ctx.quadraticCurveTo(x, y, x - s, y); ctx.quadraticCurveTo(x, y, x, y - s);
  ctx.fill(); ctx.stroke();
}

function drawHand(ctx, rig, p) {
  ctx.beginPath(); ctx.arc(p[0], p[1], rig.arm.hand_r, 0, Math.PI * 2);
  ctx.fillStyle = rig.colors.line; ctx.fill();
}
function drawFoot(ctx, rig, leg, facing) {
  const f = leg.foot, d = 1;
  ctx.beginPath();
  const len = rig.leg.foot;
  const dx = facing === 0 ? (f[0] < 0 ? -len * 0.55 : len * 0.55) : len;
  ctx.moveTo(f[0] - (facing === 0 ? 0 : len * 0.2), f[1]);
  ctx.lineTo(f[0] + dx * d, f[1]);
  ctx.strokeStyle = rig.colors.line; ctx.lineWidth = rig.line.limb + 3; ctx.lineCap = 'round'; ctx.stroke();
}

/**
 * Draw a character at actor-local origin. `state` = {pose, expr, facing, blink,
 * gaze, talking, time, props:[{draw(ctx, hand)}]} — props are drawn at hands.
 */
export function drawCharacter(ctx, rig, state) {
  const sk = solve(rig, state.pose);
  const behind = new Set(state.pose.behind || []);
  ctx.save();
  if (state.facing === -1) ctx.scale(-1, 1);
  // Contact shadow (grounds the figure; A4 keeps soft cast shadows)
  if (state.shadow !== false && state.pose.anchor !== 'hip') {
    const h = clamp(1 - (state.pose.lift || 0) / 120, 0.4, 1);
    ctx.save(); ctx.fillStyle = rig.colors.shadow; ctx.filter = 'blur(4px)';
    ctx.beginPath(); ctx.ellipse(0, 4, 62 * h, 11 * h, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  const armSeq = side => {
    const a = sk.arms[side];
    drawLimb(ctx, rig, a.shoulder, a.elbow, a.hand);
    drawHand(ctx, rig, a.hand);
    for (const pr of state.props || []) if (pr.hand === side) pr.draw(ctx, a, state.facing === -1);
  };
  for (const side of ['l', 'r']) if (behind.has(side)) armSeq(side);
  for (const side of ['l', 'r']) {
    const lg = sk.legs[side];
    drawLimb(ctx, rig, [lg === sk.legs.l ? -rig.leg.hip_spread : rig.leg.hip_spread, sk.hip[1] - 4], lg.knee, lg.foot);
    drawFoot(ctx, rig, lg, state.facing);
  }
  drawTorso(ctx, rig, sk);
  drawHead(ctx, rig, sk, state.expr, state);
  for (const side of ['l', 'r']) if (!behind.has(side)) armSeq(side);
  ctx.restore();
  return sk;
}

/** Automatic blinking, deterministic per actor. */
export function isBlinking(actorId, t, expr) {
  if (expr.eyes === 'closed' || expr.eyes === 'happy') return false;
  const seed = hashSeed(actorId);
  const period = 3.1 + seed * 1.6;
  const local = (t + seed * period) % period;
  return local < 0.11;
}

/** Evaluate a full actor state at scene time t. */
export function actorStateAt(lib, rig, actor, t) {
  const path = actor.path?.length ? actor.path : [{ t: 0, x: actor.x ?? 0, y: actor.y ?? 0 }];
  const x = sampleKeys(path, 'x', t, 0), y = sampleKeys(path, 'y', t, 0);
  // Distance travelled for foot-planted walk cycles.
  let distance = 0;
  const steps = Math.max(1, Math.ceil(t * 30));
  let px = sampleKeys(path, 'x', 0, 0), py = sampleKeys(path, 'y', 0, 0);
  for (let i = 1; i <= steps; i++) {
    const ti = (t * i) / steps;
    const nx = sampleKeys(path, 'x', ti, 0), ny = sampleKeys(path, 'y', ti, 0);
    distance += Math.hypot(nx - px, ny - py); px = nx; py = ny;
  }
  const scale = actor.scale_keys ? sampleKeys(actor.scale_keys, 'scale', t, actor.scale ?? 1) : (actor.scale ?? 1);
  let pose = poseAt(lib, actor.pose, t);
  const action = actor.action?.length ? stepKey(actor.action, t).key : null;
  pose = applyAction(pose, action, { t, distance: distance / scale, scale: 1, seed: hashSeed(actor.id), rig });
  const exprKey = actor.expression?.length ? stepKey(actor.expression, t).key : { expr: 'neutral' };
  const expr = resolveExpression(lib, exprKey.expr);
  const facing = typeof actor.facing === 'number' || actor.facing === undefined ? (actor.facing ?? 0)
    : stepKey(actor.facing, t).key.facing;
  const gaze = actor.gaze?.length ? { x: sampleKeys(actor.gaze, 'x', t, 0), y: sampleKeys(actor.gaze, 'y', t, 0) } : null;
  const talking = (actor.talk || []).some(r => t >= r.t && t < r.until);
  return { x, y, scale, pose, expr, facing, gaze, talking, blink: isBlinking(actor.id, t, expr), time: t, alpha: actor.alpha_keys ? sampleKeys(actor.alpha_keys, 'alpha', t, 1) : 1 };
}
