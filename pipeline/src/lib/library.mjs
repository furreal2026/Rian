// Resolves reusable Curious Mind assets by ID from the permanent library.
//   characters/<id>/{<id>.rig.json, poses.json, expressions.json}
//   environments/<category>/<name>/environment.json      (id "category/name")
//   assets/props/<name>/prop.json
//   assets/presets/{camera,transitions,lighting,captions,formats}.json
//   assets/audio/library/audio-selection.json             (licensed audio by ID)
//   assets/registry.json                                  (status + hashes)
import fs from 'node:fs';
import path from 'node:path';
import { loadImage, GlobalFonts } from '@napi-rs/canvas';
import { REPO_ROOT, readJson, rel } from './util.mjs';
import { shapeImages } from './shapes.mjs';

export class Library {
  constructor(root = REPO_ROOT) {
    this.root = root;
    this.cache = new Map();
    this.images = {};
    this.used = new Map(); // asset id -> {kind, file}
    this.presets = {};
    for (const n of ['camera', 'transitions', 'lighting', 'captions', 'formats']) {
      this.presets[n] = readJson(path.join(root, 'assets/presets', `${n}.json`));
    }
    const reg = path.join(root, 'assets/registry.json');
    this.registry = fs.existsSync(reg) ? readJson(reg) : { assets: [] };
    this.fontsLoaded = false;
  }

  status(id) {
    return this.registry.assets.find(a => a.id === id)?.status || 'unregistered';
  }
  _mark(id, kind, file) { this.used.set(id, { kind, file: rel(file), status: this.status(id) }); }

  loadFonts() {
    if (this.fontsLoaded) return;
    const f = path.join(this.root, 'assets/fonts/Nunito.ttf');
    if (!fs.existsSync(f)) throw new Error('Missing assets/fonts/Nunito.ttf (caption font)');
    GlobalFonts.registerFromPath(f, 'CMNunito');
    this.fontsLoaded = true;
  }

  character(id) {
    const key = `char:${id}`;
    if (!this.cache.has(key)) {
      const dir = path.join(this.root, 'characters', id);
      const rigFile = path.join(dir, `${id}.rig.json`);
      if (!fs.existsSync(rigFile)) throw new Error(`Character "${id}" not found (${rel(rigFile)})`);
      const rig = readJson(rigFile);
      const poses = readJson(path.join(dir, 'poses.json')).poses;
      const expressions = readJson(path.join(dir, 'expressions.json')).expressions;
      this.cache.set(key, { rig, lib: { poses, expressions } });
      this._mark(`character/${id}`, 'character', rigFile);
    }
    return this.cache.get(key);
  }

  environment(id) {
    const key = `env:${id}`;
    if (!this.cache.has(key)) {
      const file = path.join(this.root, 'environments', id, 'environment.json');
      if (!fs.existsSync(file)) throw new Error(`Environment "${id}" not found (${rel(file)})`);
      const env = readJson(file);
      env._dir = path.dirname(file);
      this.cache.set(key, env);
      this._mark(`environment/${id}`, 'environment', file);
    }
    return this.cache.get(key);
  }

  prop(id) {
    const key = `prop:${id}`;
    if (!this.cache.has(key)) {
      const file = path.join(this.root, 'assets/props', id, 'prop.json');
      if (!fs.existsSync(file)) throw new Error(`Prop "${id}" not found (${rel(file)})`);
      const p = readJson(file);
      p._dir = path.dirname(file);
      this.cache.set(key, p);
      this._mark(`prop/${id}`, 'prop', file);
    }
    return this.cache.get(key);
  }

  audio(ref, episodeDir) {
    if (ref.path) {
      const f = path.resolve(episodeDir, ref.path);
      if (!fs.existsSync(f)) throw new Error(`Audio file missing: ${rel(f)}`);
      return { file: f, id: null, license: ref.license || 'project-original' };
    }
    if (!this.cache.has('audiosel')) {
      const f = path.join(this.root, 'assets/audio/library/audio-selection.json');
      this.cache.set('audiosel', readJson(f));
    }
    const sel = this.cache.get('audiosel');
    const a = sel.assets.find(x => x.id === ref.id);
    if (!a) throw new Error(`Audio id "${ref.id}" is not in assets/audio/library/audio-selection.json. Export it from the upstream library first (see assets/audio/README.md).`);
    const file = path.join(this.root, 'assets/audio/library', a.path);
    this.used.set(`audio/${a.id}`, { kind: 'audio', file: rel(file), status: 'licensed-third-party', license: a.license.id, attribution_required: a.license.attribution_required, attribution: a.license.attribution });
    return { file, id: a.id, license: a.license.id, attribution_required: a.license.attribution_required, attribution: a.license.attribution, duration: a.duration };
  }

  /** Preload every raster referenced by shapes/layers (relative to the asset dir). */
  async preload(shapes, baseDir) {
    for (const p of shapeImages(shapes)) {
      const key = p;
      if (this.images[key]) continue;
      const f = path.resolve(baseDir, p);
      if (!fs.existsSync(f)) throw new Error(`Image missing: ${rel(f)}`);
      this.images[key] = await loadImage(fs.readFileSync(f));
    }
  }
}
