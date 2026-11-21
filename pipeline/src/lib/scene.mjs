// Composes one scene frame: environment layers (parallax), animated items and
// props, characters on the actor plane, then lighting.
import { drawShapes } from './shapes.mjs';
import { resolveCamera, cameraAt, applyLayerTransform } from './camera.mjs';
import { actorStateAt, drawCharacter } from './character.mjs';
import { drawLighting } from './lighting.mjs';
import { sampleKeys } from './util.mjs';

function propShapes(prop, state) {
  return prop.shapes.filter(s => !s.state || (state ? s.state === state : s.state === prop.default_state));
}

/** Prepare a scene once (resolve assets, camera keys, preload images). */
export async function prepareScene(lib, scene) {
  const env = lib.environment(scene.environment);
  for (const layer of env.layers) if (layer.shapes) await lib.preload(layer.shapes, env._dir);
  const actors = (scene.actors || []).map(a => ({ ...a, _char: lib.character(a.character || 'stick_figure') }));
  const items = (scene.items || []).map(it => ({ ...it, _prop: it.prop ? lib.prop(it.prop) : null }));
  for (const it of items) if (it._prop) await lib.preload(it._prop.shapes, it._prop._dir);
  for (const a of actors) for (const p of a.props || []) { p._prop = lib.prop(p.prop); await lib.preload(p._prop.shapes, p._prop._dir); }
  const camera = resolveCamera(scene.camera || {}, { presets: lib.presets.camera, env, duration: scene.duration });
  const lightingName = scene.lighting || env.lighting;
  const lighting = lightingName ? lib.presets.lighting[lightingName] : null;
  if (lightingName && !lighting) throw new Error(`Unknown lighting preset "${lightingName}"`);
  return { scene, env, actors, items, camera, lighting };
}

function actorPosFn(prep) {
  return (id, t) => {
    const a = prep.actors.find(x => x.id === id);
    if (!a) throw new Error(`Camera follow target "${id}" is not an actor in scene ${prep.scene.id}`);
    const path = a.path?.length ? a.path : [{ t: 0, x: a.x, y: a.y }];
    return { x: sampleKeys(path, 'x', t, 0), y: sampleKeys(path, 'y', t, 0) - (a.follow_height ?? 220) };
  };
}

const onActorPlane = i => !i.screen && !i.layer && (i.depth ?? 1) === 1;

function drawItem(ctx, lib, it, t, globalTime) {
  if ((it.from !== undefined && t < it.from) || (it.to !== undefined && t >= it.to)) return;
  const keys = it.keys || [];
  const x = sampleKeys(keys, 'x', t, it.x ?? 0), y = sampleKeys(keys, 'y', t, it.y ?? 0);
  const sc = sampleKeys(keys, 'scale', t, it.scale ?? 1), ang = sampleKeys(keys, 'angle', t, it.angle ?? 0);
  const alpha = sampleKeys(keys, 'alpha', t, it.alpha ?? 1);
  if (alpha <= 0.001) return;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(x, y); ctx.rotate(ang); ctx.scale(sc * (it.flip ? -1 : 1), sc);
  if (it._prop) {
    const g = it._prop.anchor || { x: 0, y: 0 };
    ctx.translate(-g.x, -g.y);
    drawShapes(ctx, propShapes(it._prop, it.state), { images: lib.images, time: globalTime });
  } else if (it.shapes) drawShapes(ctx, it.shapes, { images: lib.images, time: globalTime });
  ctx.restore();
}

export function renderScene(ctx, lib, prep, t, { w, h, scale, globalTime }) {
  const { env, camera } = prep;
  const out = { w, h, scale };
  const cam = cameraAt(camera, t, actorPosFn(prep));
  ctx.save();
  ctx.fillStyle = env.background || '#F3E6D2';
  ctx.fillRect(0, 0, w, h);
  for (const layer of env.layers) {
    if (layer.slot === 'actors') {
      ctx.save();
      applyLayerTransform(ctx, cam, 1, env, out);
      for (const it of prep.items.filter(i => onActorPlane(i) && (i.z || 'back') === 'back')) drawItem(ctx, lib, it, t, globalTime);
      const states = prep.actors.map(a => ({ a, s: actorStateAt(a._char.lib, a._char.rig, a, t) }))
        .filter(({ a, s }) => (a.from === undefined || t >= a.from) && (a.to === undefined || t < a.to))
        .sort((p, q) => (p.a.z ?? p.s.y) - (q.a.z ?? q.s.y));
      for (const { a, s } of states) {
        ctx.save();
        ctx.globalAlpha *= s.alpha;
        ctx.translate(s.x, s.y); ctx.scale(s.scale, s.scale);
        const props = (a.props || []).filter(p => (p.from === undefined || t >= p.from) && (p.to === undefined || t < p.to)).map(p => ({
          hand: p.hand || 'r',
          draw: (c, arm) => {
            const pr = p._prop, g = pr.grip || pr.anchor || { x: 0, y: 0 };
            c.save();
            c.translate(arm.hand[0] + (p.offset?.x || 0), arm.hand[1] + (p.offset?.y || 0));
            const follow = p.follow_arm ? (-arm.angle * Math.PI / 180 + Math.PI) : 0;
            c.rotate(follow + (p.angle || 0));
            const ps = p.scale ?? 1; c.scale(ps, ps);
            c.translate(-g.x, -g.y);
            drawShapes(c, propShapes(pr, p.state), { images: lib.images, time: globalTime });
            c.restore();
          },
        }));
        drawCharacter(ctx, a._char.rig, { ...s, props, shadow: a.shadow });
        ctx.restore();
      }
      for (const it of prep.items.filter(i => onActorPlane(i) && i.z === 'front')) drawItem(ctx, lib, it, t, globalTime);
      ctx.restore();
      continue;
    }
    ctx.save();
    applyLayerTransform(ctx, cam, layer.depth ?? 1, env, out);
    if (layer.alpha !== undefined) ctx.globalAlpha = layer.alpha;
    drawShapes(ctx, layer.shapes || [], { images: lib.images, time: globalTime });
    for (const it of prep.items.filter(i => i.layer === layer.id)) drawItem(ctx, lib, it, t, globalTime);
    ctx.restore();
  }
  // Items on their own depth (e.g. foreground pass-by wipes, depth 1.6)
  for (const it of prep.items.filter(i => !i.screen && !i.layer && (i.depth ?? 1) !== 1)) {
    ctx.save(); applyLayerTransform(ctx, cam, it.depth, env, out); drawItem(ctx, lib, it, t, globalTime); ctx.restore();
  }
  drawLighting(ctx, prep.lighting, { w, h, time: globalTime, intensity: prep.scene.lighting_intensity ?? 1 });
  // Screen-space overlays (metaphor icons, emphasis graphics) — never text.
  for (const it of prep.items.filter(i => i.screen)) {
    ctx.save(); ctx.scale(w / 1080, w / 1080); drawItem(ctx, lib, it, t, globalTime); ctx.restore();
  }
  ctx.restore();
  return cam;
}
