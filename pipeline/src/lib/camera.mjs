// 2.5D virtual camera over layered 2D artwork.
//
// Every environment layer has a `depth` (parallax factor): 0 = infinitely far
// (never moves), 1 = actor plane, >1 = foreground (moves/scales faster).
//   pan/tilt/track  -> layer center moves by (camera - restCenter) * depth
//   zoom            -> lens zoom, scales all layers equally (no parallax)
//   dolly           -> camera travels forward: layer scale = dolly ^ depth
//   roll            -> dutch angle / whip roll
// This is an illusion from 2D layers and must never be described as full 3D
// (Master Guide §9, Camera Guide §11).
import { sampleKeys, noise1, ease, clamp } from './util.mjs';

const PROPS = ['x', 'y', 'zoom', 'dolly', 'roll'];

/**
 * Resolve a scene camera spec into absolute keys (scene-relative seconds).
 * spec: {preset?, at?: anchor|{x,y}, zoom?, amount?, ease?, start?, end?,
 *        keys?: [{t,x,y,zoom,dolly,roll,ease}], follow?, shake?}
 */
export function resolveCamera(spec = {}, { presets, env, duration, actors = [] }) {
  const anchorPt = a => {
    if (!a) return { x: env.world.width / 2, y: env.world.height / 2 };
    if (typeof a === 'string') {
      const p = env.anchors?.[a];
      if (!p) throw new Error(`Camera anchor "${a}" not in environment ${env.id}. Known: ${Object.keys(env.anchors || {}).join(', ')}`);
      return p;
    }
    return a;
  };
  const base = { ...anchorPt(spec.at), zoom: spec.zoom ?? 1, dolly: 1, roll: 0 };
  if (spec.offset) { base.x += spec.offset.x || 0; base.y += spec.offset.y || 0; }
  let keys;
  if (spec.keys?.length) {
    keys = spec.keys.map(k => ({ ...k, x: k.x ?? base.x, y: k.y ?? base.y, zoom: k.zoom ?? base.zoom, dolly: k.dolly ?? 1, roll: k.roll ?? 0 }));
  } else {
    const name = spec.preset || 'static';
    const pr = presets[name];
    if (!pr) throw new Error(`Unknown camera preset "${name}". Known: ${Object.keys(presets).filter(k => !k.startsWith('_')).join(', ')}`);
    const amount = spec.amount ?? 1;
    const start = spec.start ?? 0;
    const end = spec.end ?? (pr.duration ? start + pr.duration : duration);
    keys = pr.keys.map(k => {
      const t = start + (k.u ?? 0) * (end - start);
      return {
        t,
        x: base.x + (k.dx || 0) * amount,
        y: base.y + (k.dy || 0) * amount,
        zoom: base.zoom * Math.pow(k.zoom ?? 1, amount),
        dolly: Math.pow(k.dolly ?? 1, amount),
        roll: (k.roll || 0) * amount,
        ease: k.ease || spec.ease || pr.ease,
      };
    });
    if (pr.shake && !spec.shake) spec = { ...spec, shake: pr.shake };
  }
  return { keys, follow: spec.follow || null, shake: spec.shake || null, base, actors };
}

/** Sample camera state at scene time t. `actorPos(id, t)` resolves follow targets. */
export function cameraAt(cam, t, actorPos) {
  const s = {};
  for (const p of PROPS) s[p] = sampleKeys(cam.keys, p, t, cam.base[p] ?? (p === 'zoom' || p === 'dolly' ? 1 : 0));
  if (cam.follow && actorPos) {
    const f = cam.follow;
    const lag = f.lag ?? 0.25;
    const pos = actorPos(f.actor, Math.max(0, t - lag));
    const k = clamp(f.strength ?? 1);
    const axis = f.axis || 'x';
    if (axis === 'x' || axis === 'xy') s.x = s.x + (pos.x + (f.offset?.x || 0) - s.x) * k;
    if (axis === 'y' || axis === 'xy') s.y = s.y + (pos.y + (f.offset?.y || 0) - s.y) * k;
  }
  if (cam.shake) {
    const a = cam.shake.amp ?? 6, sp = cam.shake.speed ?? 1;
    s.x += noise1(1, t * sp) * a;
    s.y += noise1(2, t * sp) * a * 0.7;
    s.roll += noise1(3, t * sp) * (cam.shake.roll ?? 0.002);
  }
  return s;
}

/**
 * Apply the camera transform for a layer of parallax `depth` to ctx.
 * `out` = {w, h} output size, `env.world` rest size, `scale` = output px per world unit at zoom 1.
 */
export function applyLayerTransform(ctx, cam, depth, env, out) {
  const restX = env.world.width / 2, restY = env.world.height / 2;
  const cx = restX + (cam.x - restX) * depth;
  const cy = restY + (cam.y - restY) * depth;
  const s = out.scale * cam.zoom * Math.pow(cam.dolly, depth);
  ctx.translate(out.w / 2, out.h / 2);
  if (cam.roll) ctx.rotate(cam.roll);
  ctx.scale(s, s);
  ctx.translate(-cx, -cy);
}

/** Map a world point on a layer of given depth to screen coordinates (for tests/overlays). */
export function worldToScreen(pt, cam, depth, env, out) {
  const restX = env.world.width / 2, restY = env.world.height / 2;
  const cx = restX + (cam.x - restX) * depth, cy = restY + (cam.y - restY) * depth;
  const s = out.scale * cam.zoom * Math.pow(cam.dolly, depth);
  let x = (pt.x - cx) * s, y = (pt.y - cy) * s;
  if (cam.roll) { const c = Math.cos(cam.roll), n = Math.sin(cam.roll); [x, y] = [x * c - y * n, x * n + y * c]; }
  return { x: x + out.w / 2, y: y + out.h / 2 };
}

export { ease };
