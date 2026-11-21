// Reference sheets rendered from source data (rig/poses/expressions, props,
// environments). The PNGs are previews of the JSON source of truth.
import fs from 'node:fs';
import path from 'node:path';
import { createCanvas } from '@napi-rs/canvas';
import { Library } from '../lib/library.mjs';
import { resolvePose, resolveExpression, drawCharacter } from '../lib/character.mjs';
import { drawShapes } from '../lib/shapes.mjs';
import { prepareScene, renderScene } from '../lib/scene.mjs';
import { REPO_ROOT } from '../lib/util.mjs';

function label(ctx, text, x, y, size = 22) {
  ctx.save(); ctx.font = `900 ${size}px CMNunito`; ctx.fillStyle = '#1F2236'; ctx.textAlign = 'center'; ctx.fillText(text, x, y); ctx.restore();
}

export async function characterSheets(charId = 'stick_figure', outDir) {
  const lib = new Library(); lib.loadFonts();
  const { rig, lib: cl } = lib.character(charId);
  outDir = outDir || path.join(REPO_ROOT, 'characters', charId, 'reference');
  fs.mkdirSync(outDir, { recursive: true });
  const files = [];
  // Expressions (head close-ups)
  const exprs = Object.keys(cl.expressions);
  const cols = 5, cw = 260, ch = 300;
  let c = createCanvas(cols * cw, Math.ceil(exprs.length / cols) * ch), x = c.getContext('2d');
  x.fillStyle = '#F6EFE4'; x.fillRect(0, 0, c.width, c.height);
  exprs.forEach((e, i) => {
    const cx = (i % cols) * cw + cw / 2, cy = Math.floor(i / cols) * ch;
    x.save(); x.beginPath(); x.rect(cx - cw / 2, cy, cw, 236); x.clip(); x.translate(cx, cy + 640); x.scale(1.45, 1.45);
    drawCharacter(x, rig, { pose: resolvePose(cl, 'stand'), expr: resolveExpression(cl, e), facing: 0, time: 0.3, shadow: false });
    x.restore();
    x.fillStyle = '#F6EFE4'; x.fillRect(cx - cw / 2, cy + 236, cw, ch - 236);
    label(x, e, cx, cy + 275);
  });
  let f = path.join(outDir, 'expressions_sheet.png'); fs.writeFileSync(f, await c.encode('png')); files.push(f);
  // Poses (full body)
  const poses = Object.keys(cl.poses);
  const pw = 250, ph = 560;
  c = createCanvas(6 * pw, Math.ceil(poses.length / 6) * ph); x = c.getContext('2d');
  x.fillStyle = '#F6EFE4'; x.fillRect(0, 0, c.width, c.height);
  poses.forEach((p, i) => {
    const cx = (i % 6) * pw + pw / 2, by = Math.floor(i / 6) * ph + 480;
    const pose = resolvePose(cl, p);
    x.save(); x.translate(cx, pose.anchor === 'hip' ? by - 180 : by); x.scale(0.95, 0.95);
    if (pose.anchor === 'hip') { x.fillStyle = '#C9A27A'; x.fillRect(-60, 6, 70, 14); }
    drawCharacter(x, rig, { pose, expr: resolveExpression(cl, 'neutral'), facing: pose.anchor === 'hip' ? 1 : 0, time: 0.3 });
    x.restore();
    label(x, p, cx, by + 50, 20);
  });
  f = path.join(outDir, 'poses_sheet.png'); fs.writeFileSync(f, await c.encode('png')); files.push(f);
  // Turnaround: front, facing right, facing left
  c = createCanvas(900, 620); x = c.getContext('2d');
  x.fillStyle = '#F6EFE4'; x.fillRect(0, 0, c.width, c.height);
  [[0, 'front'], [1, 'facing right'], [-1, 'facing left']].forEach(([fc, name], i) => {
    x.save(); x.translate(150 + i * 300, 540);
    drawCharacter(x, rig, { pose: resolvePose(cl, 'stand'), expr: resolveExpression(cl, 'neutral'), facing: fc, time: 0.3 });
    x.restore(); label(x, name, 150 + i * 300, 590);
  });
  f = path.join(outDir, 'turnaround.png'); fs.writeFileSync(f, await c.encode('png')); files.push(f);
  return files;
}

export async function propSheet(ids, outFile) {
  const lib = new Library(); lib.loadFonts();
  const cw = 240, ch = 260;
  const c = createCanvas(Math.min(ids.length, 5) * cw, Math.ceil(ids.length / 5) * ch), x = c.getContext('2d');
  x.fillStyle = '#F6EFE4'; x.fillRect(0, 0, c.width, c.height);
  for (const [i, id] of ids.entries()) {
    const p = lib.prop(id); await lib.preload(p.shapes, p._dir);
    const cx = (i % 5) * cw + cw / 2, cy = Math.floor(i / 5) * ch + 110;
    const s = Math.min(1.6, 150 / Math.max(p.size.w, p.size.h));
    x.save(); x.translate(cx, cy); x.scale(s, s); x.translate(-p.size.w / 2, -p.size.h / 2);
    drawShapes(x, p.shapes.filter(sh => !sh.state || sh.state === p.default_state), { images: lib.images });
    x.restore();
    label(x, id, cx, cy + 130, 20);
  }
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, await c.encode('png'));
  return outFile;
}

export async function environmentPreview(envId, outFile, { scale = 0.5, actor = true } = {}) {
  const lib = new Library(); lib.loadFonts();
  const env = lib.environment(envId);
  const scene = { id: 'preview', environment: envId, duration: 1, camera: { at: env.default_camera || undefined },
    actors: actor ? [{ id: 'ref', character: 'stick_figure', x: env.anchors?.stage?.x ?? env.world.width / 2, y: env.anchors?.stage?.y ?? env.floor_y, pose: [{ t: 0, pose: 'stand' }], expression: [{ t: 0, expr: 'happy' }] }] : [] };
  const prep = await prepareScene(lib, scene);
  const w = Math.round(1080 * scale), h = Math.round(1920 * scale);
  const c = createCanvas(w, h);
  renderScene(c.getContext('2d'), lib, prep, 0.5, { w, h, scale, globalTime: 0.5 });
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, await c.encode('png'));
  return outFile;
}
