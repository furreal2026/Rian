import test from 'node:test';
import assert from 'node:assert/strict';
import { createCanvas } from '@napi-rs/canvas';
import { Library } from '../src/lib/library.mjs';
import { resolveCamera, cameraAt, worldToScreen } from '../src/lib/camera.mjs';
import { cuesFromLine, toSrt, wrapCue } from '../src/lib/captions.mjs';
import { solve, resolvePose, resolveExpression, drawCharacter } from '../src/lib/character.mjs';
import { sampleKeys } from '../src/lib/util.mjs';
import * as registry from '../src/lib/registry.mjs';

const lib = new Library();
const env = { id: 't', world: { width: 1620, height: 2880 }, anchors: { a: { x: 810, y: 1440 } } };
const out = { w: 1080, h: 1920, scale: 1 };

test('keyframes interpolate and clamp', () => {
  const k = [{ t: 0, x: 0 }, { t: 2, x: 100, ease: 'linear' }];
  assert.equal(sampleKeys(k, 'x', -1), 0);
  assert.equal(sampleKeys(k, 'x', 1), 50);
  assert.equal(sampleKeys(k, 'x', 5), 100);
});

test('parallax: depth 0 never moves, depth 1 tracks camera, foreground moves faster', () => {
  const pt = { x: 810, y: 1440 };
  const a = { x: 810, y: 1440, zoom: 1, dolly: 1, roll: 0 };
  const b = { ...a, x: 1010 };
  assert.deepEqual(worldToScreen(pt, a, 0, env, out), worldToScreen(pt, b, 0, env, out));
  assert.equal(worldToScreen(pt, a, 1, env, out).x - worldToScreen(pt, b, 1, env, out).x, 200);
  assert.ok(worldToScreen(pt, a, 1.5, env, out).x - worldToScreen(pt, b, 1.5, env, out).x > 200);
});

test('dolly scales near layers more than far layers; zoom scales all equally', () => {
  const off = { x: 910, y: 1440 };
  const base = { x: 810, y: 1440, zoom: 1, dolly: 1, roll: 0 };
  const d = (cam, depth) => worldToScreen(off, cam, depth, env, out).x - 540;
  const dol = { ...base, dolly: 1.5 }, zm = { ...base, zoom: 1.5 };
  assert.ok(d(dol, 1.4) > d(dol, 0.3));
  assert.ok(Math.abs(d(zm, 1.4) - d(zm, 0.3)) < 1e-9);
});

test('every camera preset resolves and samples finite values', () => {
  for (const name of Object.keys(lib.presets.camera).filter(n => !n.startsWith('_'))) {
    const cam = resolveCamera({ preset: name, at: 'a' }, { presets: lib.presets.camera, env, duration: 3 });
    for (const t of [0, 0.1, 1.5, 3]) for (const v of Object.values(cameraAt(cam, t))) assert.ok(Number.isFinite(v), `${name} @${t}`);
  }
});

test('captions: chunks cover the line duration and SRT is well-formed', () => {
  const cues = cuesFromLine({ text: 'Everyone freezes. Cars, birds, even your neighbour\'s sneeze.' }, 1, 4);
  assert.ok(cues.length >= 2);
  assert.equal(cues[0].start, 1);
  assert.ok(Math.abs(cues.at(-1).end - 5) < 1e-9);
  assert.match(toSrt(cues), /^1\n00:00:01,000 --> /);
});

test('captions: emphasis runs and two-line wrap', () => {
  lib.loadFonts();
  const ctx = createCanvas(10, 10).getContext('2d');
  ctx.font = '900 68px CMNunito';
  const lines = wrapCue(ctx, 'still one minute of *your* whole life', 820);
  assert.ok(lines && lines.length <= 2);
  assert.ok(lines.flat().some(t => t.hi && t.text === 'your'));
});

test('rig: standing feet touch the ground; all poses and expressions draw', () => {
  const { rig, lib: cl } = lib.character('stick_figure');
  const sk = solve(rig, resolvePose(cl, 'stand'));
  assert.ok(Math.abs(Math.max(sk.legs.l.foot[1], sk.legs.r.foot[1])) < 1e-6);
  const ctx = createCanvas(400, 600).getContext('2d');
  for (const p of Object.keys(cl.poses)) for (const e of ['neutral', 'worried', 'joyful']) {
    drawCharacter(ctx, rig, { pose: resolvePose(cl, p), expr: resolveExpression(cl, e), facing: 1, time: 0 });
  }
  for (const e of Object.keys(cl.expressions)) drawCharacter(ctx, rig, { pose: resolvePose(cl, 'stand'), expr: resolveExpression(cl, e), facing: 0, time: 0 });
});

test('registry is consistent with library files', () => {
  assert.deepEqual(registry.check(), []);
});
