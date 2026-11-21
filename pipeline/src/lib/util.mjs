// Shared helpers: easing, keyframe interpolation, hashing, JSON IO.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, u) => a + (b - a) * u;
export const deg = d => (d * Math.PI) / 180;

export const EASES = {
  linear: u => u,
  easeInSine: u => 1 - Math.cos((u * Math.PI) / 2),
  easeOutSine: u => Math.sin((u * Math.PI) / 2),
  easeInOutSine: u => -(Math.cos(Math.PI * u) - 1) / 2,
  easeInCubic: u => u * u * u,
  easeOutCubic: u => 1 - Math.pow(1 - u, 3),
  easeInOutCubic: u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
  easeOutQuart: u => 1 - Math.pow(1 - u, 4),
  easeInExpo: u => (u === 0 ? 0 : Math.pow(2, 10 * u - 10)),
  easeOutExpo: u => (u === 1 ? 1 : 1 - Math.pow(2, -10 * u)),
  easeInOutExpo: u => (u === 0 ? 0 : u === 1 ? 1 : u < 0.5 ? Math.pow(2, 20 * u - 10) / 2 : (2 - Math.pow(2, -20 * u + 10)) / 2),
  easeOutBack: u => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2); },
  smooth: u => u * u * (3 - 2 * u),
};
export function ease(name, u) {
  const f = EASES[name || 'easeInOutSine'];
  if (!f) throw new Error(`Unknown ease "${name}". Known: ${Object.keys(EASES).join(', ')}`);
  return f(clamp(u));
}

/**
 * Sample a numeric property from keys [{t, [prop], ease}] (t ascending).
 * The ease on the *destination* key shapes the segment that ends there.
 */
export function sampleKeys(keys, prop, t, fallback) {
  const ks = keys.filter(k => k[prop] !== undefined);
  if (!ks.length) return fallback;
  if (t <= ks[0].t) return ks[0][prop];
  const last = ks[ks.length - 1];
  if (t >= last.t) return last[prop];
  for (let i = 0; i < ks.length - 1; i++) {
    const a = ks[i], b = ks[i + 1];
    if (t >= a.t && t <= b.t) {
      const u = b.t === a.t ? 1 : (t - a.t) / (b.t - a.t);
      return lerp(a[prop], b[prop], ease(b.ease, u));
    }
  }
  return fallback;
}

/** Step lookup: latest key with t <= time; returns {key, index, since}. */
export function stepKey(keys, t) {
  let idx = -1;
  for (let i = 0; i < keys.length; i++) if (keys[i].t <= t + 1e-9) idx = i;
  if (idx < 0) return { key: keys[0], index: 0, since: 0, prev: null };
  return { key: keys[idx], index: idx, since: t - keys[idx].t, prev: idx > 0 ? keys[idx - 1] : null };
}

/** Deterministic pseudo-noise in [-1, 1]. */
export function noise1(seed, t) {
  return (Math.sin(t * 1.7 + seed * 12.9898) * 0.5 + Math.sin(t * 2.9 + seed * 78.233) * 0.3 + Math.sin(t * 5.3 + seed * 3.7) * 0.2);
}
export function hashSeed(str) {
  let h = 2166136261;
  for (const c of String(str)) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
  return ((h >>> 0) % 10000) / 10000;
}

export const sha256File = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
export const sha256Text = text => crypto.createHash('sha256').update(text).digest('hex');

export function readJson(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch (e) { throw new Error(`Cannot read JSON ${path.relative(process.cwd(), file)}: ${e.message}`); }
}
export function writeJson(file, data, { overwrite = true } = {}) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n', { flag: overwrite ? 'w' : 'wx' });
}
export const rel = p => path.relative(REPO_ROOT, p).split(path.sep).join('/');

export function mixColor(a, b, u) {
  const pa = parseHex(a), pb = parseHex(b);
  const c = pa.map((v, i) => Math.round(lerp(v, pb[i], u)));
  return `#${c.map(v => v.toString(16).padStart(2, '0')).join('')}`;
}
export function parseHex(hex) {
  const h = hex.replace('#', '');
  const full = h.length === 3 ? h.split('').map(c => c + c).join('') : h;
  return [0, 2, 4].map(i => parseInt(full.slice(i, i + 2), 16));
}
