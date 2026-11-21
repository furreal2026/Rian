// Asset registry: one machine-readable record per reusable asset, with the
// source file's SHA-256. Approved assets are frozen: if an approved file's hash
// changes, `registry check` fails, so nobody silently edits/regenerates it.
import fs from 'node:fs';
import path from 'node:path';
import { REPO_ROOT, readJson, writeJson, sha256File, rel } from './util.mjs';

const REG = path.join(REPO_ROOT, 'assets/registry.json');
export const STATUSES = ['needed', 'in_progress', 'draft', 'candidate_master', 'approved', 'archived'];

export function loadRegistry() {
  return fs.existsSync(REG) ? readJson(REG) : { schema: 'curious-mind/asset-registry@1', assets: [] };
}
export function saveRegistry(reg) {
  reg.assets.sort((a, b) => a.id.localeCompare(b.id));
  writeJson(REG, reg);
}

/** Discover library source files. */
export function discover() {
  const found = [];
  const walk = (dir, fn) => { if (fs.existsSync(dir)) for (const e of fs.readdirSync(dir, { withFileTypes: true })) { const p = path.join(dir, e.name); if (e.isDirectory()) walk(p, fn); else fn(p); } };
  walk(path.join(REPO_ROOT, 'characters'), p => { if (p.endsWith('.rig.json')) found.push({ id: `character/${path.basename(p, '.rig.json')}`, kind: 'character', file: p }); });
  walk(path.join(REPO_ROOT, 'environments'), p => { if (path.basename(p) === 'environment.json') found.push({ id: `environment/${rel(path.dirname(p)).replace(/^environments\//, '')}`, kind: 'environment', file: p }); });
  walk(path.join(REPO_ROOT, 'assets/props'), p => { if (path.basename(p) === 'prop.json') found.push({ id: `prop/${path.basename(path.dirname(p))}`, kind: 'prop', file: p }); });
  for (const n of ['camera', 'transitions', 'lighting', 'captions', 'formats']) found.push({ id: `preset/${n}`, kind: 'preset', file: path.join(REPO_ROOT, 'assets/presets', `${n}.json`) });
  return found;
}

/** Add unregistered assets as their declared status (default draft); refresh hashes of non-approved ones. */
export function scan() {
  const reg = loadRegistry();
  const changes = [];
  for (const f of discover()) {
    const sha = sha256File(f.file);
    let declared = 'draft';
    try { declared = readJson(f.file).status || 'draft'; } catch { /* preset */ }
    const cur = reg.assets.find(a => a.id === f.id);
    if (!cur) {
      reg.assets.push({ id: f.id, kind: f.kind, path: rel(f.file), status: STATUSES.includes(declared) ? declared : 'draft', sha256: sha, source: 'code-drawn vector JSON (editable source)', generation: null, license: 'project-original', registered_at: new Date().toISOString().slice(0, 10), approved_by: null, approved_at: null });
      changes.push(`added ${f.id}`);
    } else if (cur.sha256 !== sha && cur.status !== 'approved') { cur.sha256 = sha; changes.push(`rehashed ${f.id} (${cur.status})`); }
  }
  saveRegistry(reg);
  return changes;
}

/** Verify files exist and approved assets are unchanged. Returns problems. */
export function check() {
  const reg = loadRegistry();
  const problems = [];
  for (const a of reg.assets) {
    const f = path.join(REPO_ROOT, a.path);
    if (!fs.existsSync(f)) { if (a.status !== 'needed' && a.status !== 'archived') problems.push(`${a.id}: file missing (${a.path})`); continue; }
    if (!STATUSES.includes(a.status)) problems.push(`${a.id}: unknown status ${a.status}`);
    const sha = sha256File(f);
    if (a.status === 'approved' && sha !== a.sha256) problems.push(`${a.id}: APPROVED asset modified (hash mismatch). Revert, or create a new version id and get it approved.`);
    if (a.status !== 'approved' && sha !== a.sha256) problems.push(`${a.id}: hash stale — run "registry scan"`);
  }
  for (const f of discover()) if (!reg.assets.find(a => a.id === f.id)) problems.push(`${f.id}: not registered — run "registry scan"`);
  return problems;
}

export function approve(id, by) {
  if (!by) throw new Error('--by "<owner name>" is required: approval is the project owner\'s decision');
  const reg = loadRegistry();
  const a = reg.assets.find(x => x.id === id);
  if (!a) throw new Error(`No asset ${id}`);
  a.status = 'approved'; a.approved_by = by; a.approved_at = new Date().toISOString().slice(0, 10);
  a.sha256 = sha256File(path.join(REPO_ROOT, a.path));
  saveRegistry(reg);
  return a;
}
