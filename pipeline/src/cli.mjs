#!/usr/bin/env node
// Curious Mind Code Engine CLI. Run from the repository root or anywhere:
//   node pipeline/src/cli.mjs <command> ...
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createCanvas, loadImage } from '@napi-rs/canvas';
import { REPO_ROOT, rel, sha256Text, readJson, writeJson } from './lib/util.mjs';
import { Library } from './lib/library.mjs';
import { loadEpisode, validateEpisode } from './lib/episode.mjs';
import { prepareScene } from './lib/scene.mjs';
import { renderEpisode, renderStills } from './lib/render.mjs';
import { geminiGenerate } from './lib/gemini.mjs';
import * as registry from './lib/registry.mjs';
import { characterSheets, propSheet, environmentPreview } from './tools/sheets.mjs';
import { FFMPEG, FFPROBE, probeDuration } from './lib/audio.mjs';

const [cmd, ...argv] = process.argv.slice(2);
const BOOL = new Set(['draft', 'replace', 'guides', 'allow-network', 'no-voice']);
const flags = {}, positional = [];
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) { const k = a.slice(2); if (BOOL.has(k)) flags[k] = true; else flags[k] = argv[++i]; }
  else positional.push(a);
}
const flag = n => !!flags[n];
const opt = (n, d) => (flags[n] !== undefined && flags[n] !== true ? flags[n] : d);
const log = m => console.error(`[cm] ${m}`);

const HELP = `Curious Mind Code Engine
  doctor                                   check node/ffmpeg/fonts/library
  validate <episode.json>                  timing, assets, captions, poses (no render)
  stills <episode.json> --times 0.5,3,6 [--scale 0.5] [--guides] [--out DIR]
  render <episode.json> [--draft] [--seconds N] [--replace] [--guides]
  voice <episode.json> --engine gemini --model M --voice NAME --allow-network
  voice <episode.json> --engine espeak     (technical fixture voice — never publish)
  image <request.json> --allow-network     generate a raster plate from a request file
  key <in.png> <out.png> [--color #00FF00] [--tolerance 80]   chroma-key a plate to alpha
  sheets [all|character|props|environments]  regenerate reference PNGs from sources
  registry scan|check|list|approve <id> --by "<owner>"`;

async function main() {
  switch (cmd) {
    case 'doctor': return doctor();
    case 'validate': {
      const lib = new Library();
      const ep = loadEpisode(positional[0]);
      const tl = await validateEpisode(ep, lib, prepareScene, { requireVoice: !flag('no-voice') });
      console.log(JSON.stringify({
        episode: ep.id, duration: +tl.duration.toFixed(2),
        scenes: tl.scenes.map(s => `${s.id} @${s._start.toFixed(2)}s +${s._duration.toFixed(2)}s ${s.environment} cam=${s.camera?.preset || 'keys/static'} → ${s.transition_out?.type || 'cut'}`),
        cues: tl.cues.length, errors: tl.errors, warnings: tl.warnings,
      }, null, 2));
      process.exitCode = tl.errors.length ? 1 : 0; return;
    }
    case 'stills': {
      const times = (opt('times', '0.5') || '').split(',').map(Number);
      const ep = loadEpisode(positional[0]);
      const out = opt('out', path.join(ep._dir, 'output', 'stills'));
      const { files } = await renderStills(positional[0], times, out, { scale: Number(opt('scale', 0.5)), guides: flag('guides') });
      files.forEach(f => console.log(rel(f))); return;
    }
    case 'render': {
      const { finalFile, report } = await renderEpisode(positional[0], { draft: flag('draft'), seconds: opt('seconds') ? Number(opt('seconds')) : null, replace: flag('replace'), guides: flag('guides'), log });
      console.log(JSON.stringify({ output: rel(finalFile), duration: report.duration_seconds, frames: report.frames, size: `${report.width}x${report.height}@${report.fps}`, loudness: report.loudness, warnings: report.warnings }, null, 2));
      return;
    }
    case 'voice': return voice();
    case 'image': return image();
    case 'key': return chromaKey(positional[0], positional[1], opt('color', '#00FF00'), Number(opt('tolerance', 80)));
    case 'sheets': {
      const what = positional[0] || 'all';
      const out = [];
      if (what === 'all' || what === 'character') out.push(...await characterSheets('stick_figure'));
      if (what === 'all' || what === 'props') {
        const ids = fs.readdirSync(path.join(REPO_ROOT, 'assets/props')).filter(d => fs.existsSync(path.join(REPO_ROOT, 'assets/props', d, 'prop.json')));
        out.push(await propSheet(ids, path.join(REPO_ROOT, 'assets/props/props_sheet.png')));
      }
      if (what === 'all' || what === 'environments') {
        for (const e of registry.discover().filter(x => x.kind === 'environment')) {
          const id = e.id.replace('environment/', '');
          out.push(await environmentPreview(id, path.join(REPO_ROOT, 'environments', id, 'reference/preview.png'), { scale: 0.5 }));
        }
      }
      out.forEach(f => console.log(rel(f))); return;
    }
    case 'registry': {
      const sub = positional[0];
      if (sub === 'scan') { const c = registry.scan(); console.log(c.length ? c.join('\n') : 'registry up to date'); return; }
      if (sub === 'check') { const p = registry.check(); console.log(p.length ? p.join('\n') : 'registry OK'); process.exitCode = p.length ? 1 : 0; return; }
      if (sub === 'list') { for (const a of registry.loadRegistry().assets) console.log(`${a.status.padEnd(16)} ${a.id.padEnd(40)} ${a.path}`); return; }
      if (sub === 'approve') { const a = registry.approve(positional[1], opt('by')); console.log(`approved ${a.id} by ${a.approved_by} (${a.approved_at})`); return; }
      throw new Error('registry scan|check|list|approve');
    }
    default: console.log(HELP); if (cmd) process.exitCode = 1;
  }
}

function doctor() {
  const r = {};
  r.node = process.version;
  const v = c => { const x = spawnSync(c, ['-version'], { encoding: 'utf8' }); return x.status === 0 ? x.stdout.split('\n')[0] : null; };
  r.ffmpeg = v(FFMPEG); r.ffprobe = v(FFPROBE);
  r.libx264 = /libx264/.test(spawnSync(FFMPEG, ['-hide_banner', '-encoders'], { encoding: 'utf8' }).stdout || '');
  r.caption_font = fs.existsSync(path.join(REPO_ROOT, 'assets/fonts/Nunito.ttf'));
  r.audio_library = fs.existsSync(path.join(REPO_ROOT, 'assets/audio/library/audio-selection.json'));
  r.espeak_ng_fixture_voice = spawnSync('espeak-ng', ['--version'], { encoding: 'utf8' }).status === 0;
  r.gemini_key_env_present = !!process.env.GEMINI_API_KEY;
  r.note = 'Key presence is not proof of quota/model access. Image/TTS generation is NOT tested by doctor.';
  const problems = registry.check();
  r.registry = problems.length ? problems : 'OK';
  console.log(JSON.stringify(r, null, 2));
  if (!r.ffmpeg || !r.ffprobe || !r.libx264 || !r.caption_font) process.exitCode = 1;
}

async function voice() {
  const ep = loadEpisode(positional[0]);
  const engine = opt('engine');
  if (!['gemini', 'espeak'].includes(engine)) throw new Error('--engine gemini|espeak required');
  const lines = ep.voice?.lines || [];
  for (const l of lines) {
    const out = path.resolve(ep._dir, l.path);
    const receipt = `${out}.request.json`;
    const spoken = l.text.replace(/\*/g, '');
    if (fs.existsSync(out)) {
      // Reuse: never regenerate approved/accepted narration silently.
      const rec = fs.existsSync(receipt) ? readJson(receipt) : null;
      if (rec && rec.input_sha256 && rec.input_sha256 !== sha256Text(spoken)) log(`${l.id}: TEXT CHANGED since audio was made — delete ${rel(out)} and its receipt deliberately to regenerate`);
      else log(`${l.id}: reuse existing ${rel(out)}`);
      continue;
    }
    if (engine === 'espeak') {
      fs.mkdirSync(path.dirname(out), { recursive: true });
      const r = spawnSync('espeak-ng', ['-v', opt('voice', 'en-us'), '-s', opt('rate', '160'), '-w', out, spoken], { encoding: 'utf8' });
      if (r.status !== 0) throw new Error(`espeak-ng failed: ${r.stderr}`);
      writeJson(receipt, { kind: 'speech', provider: 'espeak-ng', purpose: 'TECHNICAL FIXTURE ONLY — robotic placeholder for pipeline tests; never publish', input_sha256: sha256Text(spoken), input_text: spoken, status: 'complete', requested_at: new Date().toISOString() });
      log(`${l.id}: espeak fixture ${probeDuration(out).toFixed(2)}s`);
    } else {
      const model = opt('model'), vname = opt('voice');
      if (!vname) throw new Error('--voice NAME required (record the approved named voice in the episode voice.provider)');
      await geminiGenerate({ kind: 'speech', model, input: spoken, output: out, voice: vname, allowNetwork: flag('allow-network'), meta: { episode: ep.id, line: l.id } });
      log(`${l.id}: gemini ${vname} ${probeDuration(out).toFixed(2)}s`);
    }
  }
}

/**
 * Request file (JSON): {id, kind: "environment_layer"|"prop"|"reference", output: "relative.png",
 *  model, prompt, references?: [paths], chroma?: "#00FF00", registry_id?}
 * Refuses when the target registry id is already approved (reuse instead).
 */
async function image() {
  const file = path.resolve(positional[0]);
  const req = readJson(file);
  const dir = path.dirname(file);
  const regId = req.registry_id;
  if (regId) {
    const a = registry.loadRegistry().assets.find(x => x.id === regId);
    if (a?.status === 'approved') throw new Error(`${regId} is already approved — reuse it; create a new versioned id if a change is truly needed`);
  }
  const output = path.resolve(dir, req.output);
  const { receipt } = await geminiGenerate({ kind: 'image', model: req.model, input: req.prompt, output, references: (req.references || []).map(r => path.resolve(dir, r)), allowNetwork: flag('allow-network'), meta: { request_file: rel(file), asset_id: req.id } });
  console.log(JSON.stringify({ output: rel(output), receipt: rel(receipt) }));
}

async function chromaKey(inp, out, color, tol) {
  if (!inp || !out) throw new Error('key <in.png> <out.png>');
  if (fs.existsSync(out)) throw new Error(`${out} exists (no overwrite)`);
  const img = await loadImage(fs.readFileSync(inp));
  const c = createCanvas(img.width, img.height), x = c.getContext('2d');
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, img.width, img.height);
  const [kr, kg, kb] = [1, 3, 5].map(i => parseInt(color.slice(i, i + 2), 16));
  for (let i = 0; i < d.data.length; i += 4) {
    const dist = Math.hypot(d.data[i] - kr, d.data[i + 1] - kg, d.data[i + 2] - kb);
    if (dist < tol) d.data[i + 3] = 0;
    else if (dist < tol * 1.6) d.data[i + 3] = Math.round(255 * (dist - tol) / (tol * 0.6));
  }
  x.putImageData(d, 0, 0);
  fs.writeFileSync(out, await c.encode('png'));
  console.log(rel(path.resolve(out)));
}

main().catch(e => { console.error(`[cm] ERROR: ${e.message}`); process.exitCode = 1; });
