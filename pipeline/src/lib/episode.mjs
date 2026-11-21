// Episode manifest: loading, timing resolution and validation.
// Timing is editable data: scene durations (number or "auto" = fit narration),
// voice lines anchored to scenes, SFX anchored to scenes. Moving a scene moves
// its narration, captions and sound with it.
import fs from 'node:fs';
import path from 'node:path';
import { createCanvas } from '@napi-rs/canvas';
import { readJson, rel } from './util.mjs';
import { probeDuration } from './audio.mjs';
import { cuesFromLine, checkCaptions } from './captions.mjs';
import { transitionWindow, TRANSITION_TYPES } from './transitions.mjs';
import { actorStateAt } from './character.mjs';

export const EPISODE_SCHEMA = 'curious-mind/episode@1';

export function loadEpisode(file) {
  const ep = readJson(file);
  if (ep.schema !== EPISODE_SCHEMA) throw new Error(`${rel(file)}: schema must be "${EPISODE_SCHEMA}"`);
  ep._file = path.resolve(file);
  ep._dir = path.dirname(ep._file);
  return ep;
}

/** Resolve formats, voice durations, scene timing, cues and audio cues. */
export function resolveTimeline(ep, lib, { requireVoice = true } = {}) {
  const errors = [], warnings = [];
  const format = lib.presets.formats[ep.format || 'shorts_9x16'];
  if (!format) throw new Error(`Unknown format "${ep.format}"`);
  const scenes = ep.scenes || [];
  if (!scenes.length) errors.push('Episode has no scenes');
  const sceneIds = new Set();
  for (const s of scenes) { if (sceneIds.has(s.id)) errors.push(`Duplicate scene id ${s.id}`); sceneIds.add(s.id); }

  // Voice lines: measure actual audio (never stretched).
  const lines = (ep.voice?.lines || []).map(l => ({ ...l }));
  for (const l of lines) {
    if (!l.path) { errors.push(`Voice line ${l.id} has no audio path`); continue; }
    const f = path.resolve(ep._dir, l.path);
    if (!fs.existsSync(f)) { (requireVoice ? errors : warnings).push(`Voice audio missing for ${l.id}: ${rel(f)} (run: node pipeline/src/cli.mjs voice ${rel(ep._file)})`); continue; }
    l._file = f; l._duration = probeDuration(f);
    if (l.scene && !sceneIds.has(l.scene)) errors.push(`Voice line ${l.id} references unknown scene ${l.scene}`);
  }

  // Scene durations
  for (const s of scenes) {
    if (s.duration === 'auto' || s.duration === undefined) {
      const own = lines.filter(l => l.scene === s.id && l._duration);
      const end = own.length ? Math.max(...own.map(l => (l.offset ?? 0) + l._duration)) : 0;
      s._duration = Math.max(s.min_duration ?? 1.2, end + (s.pad ?? 0.3));
      if (!own.length && s.duration === 'auto') warnings.push(`Scene ${s.id} is "auto" but has no measured narration; using ${s._duration}s`);
    } else if (typeof s.duration === 'number' && s.duration > 0) s._duration = s.duration;
    else errors.push(`Scene ${s.id}: duration must be a positive number or "auto"`);
  }
  let t = 0;
  for (const s of scenes) { s._start = t; t += s._duration || 0; }
  const duration = t;
  const sceneStart = id => scenes.find(s => s.id === id)?._start;

  // Transition windows
  const windows = [];
  scenes.forEach((s, i) => {
    const tr = s.transition_out;
    if (!tr) return;
    if (!TRANSITION_TYPES.includes(tr.type)) errors.push(`Scene ${s.id}: unknown transition "${tr.type}"`);
    if (tr.preset) Object.assign(tr, { ...lib.presets.transitions[tr.preset], ...tr });
    if (i === scenes.length - 1) { warnings.push(`Scene ${s.id}: transition_out on last scene ignored`); return; }
    const w = transitionWindow(tr, s._start + s._duration, s._duration, scenes[i + 1]._duration);
    if (w) windows.push({ ...w, from: i, to: i + 1, tr });
  });

  // Voice placement + captions
  const capPreset = lib.presets.captions[ep.captions?.preset || 'cm_shorts_v1'];
  const cues = [];
  for (const l of lines) {
    l._start = l.start ?? ((sceneStart(l.scene) ?? 0) + (l.offset ?? 0));
    if (l._duration) {
      if (l._start + l._duration > duration + 0.01) errors.push(`Voice line ${l.id} ends at ${(l._start + l._duration).toFixed(2)}s, after the episode end ${duration.toFixed(2)}s`);
      if (ep.captions?.enabled !== false) cues.push(...cuesFromLine(l, l._start, l._duration, capPreset.max_words));
    }
  }
  lines.sort((a, b) => a._start - b._start);
  for (let i = 1; i < lines.length; i++) {
    const a = lines[i - 1], b = lines[i];
    if (a._duration && b._start < a._start + a._duration - 0.02) warnings.push(`Voice lines ${a.id} and ${b.id} overlap`);
  }
  if (ep.voice?.track) {
    const f = path.resolve(ep._dir, ep.voice.track.path);
    if (!fs.existsSync(f)) (requireVoice ? errors : warnings).push(`Voice track missing: ${rel(f)}`);
    else lines.push({ id: 'track', _file: f, _start: ep.voice.track.start ?? 0, _duration: probeDuration(f), gain: ep.voice.track.gain });
    for (const c of ep.voice.track.captions || []) cues.push({ ...c, timing: 'aligned' });
  }
  cues.sort((a, b) => a.start - b.start);

  // Caption fit
  if (cues.length) {
    lib.loadFonts();
    const ctx = createCanvas(10, 10).getContext('2d');
    errors.push(...checkCaptions(ctx, cues, capPreset));
  }

  // Audio cues
  const at = (cue, field = 'time') => cue[field] ?? ((sceneStart(cue.scene) ?? 0) + (cue.at ?? 0));
  const sfx = (ep.sfx || []).map(c => {
    const a = lib.audio(c, ep._dir);
    const time = at(c);
    if (c.scene && !sceneIds.has(c.scene)) errors.push(`SFX ${c.id || c.path} references unknown scene ${c.scene}`);
    if (time < 0 || time > duration) errors.push(`SFX ${c.id || c.path} at ${time.toFixed(2)}s is outside the episode`);
    return { ...a, time, gain: c.gain, duration: c.duration, note: c.note };
  });
  const ambience = (ep.ambience || []).map(c => {
    const a = lib.audio(c, ep._dir);
    const sc = c.scene ? scenes.find(s => s.id === c.scene) : null;
    const start = c.start ?? sc?._start ?? 0;
    const end = c.end ?? (sc ? sc._start + sc._duration : duration);
    return { ...a, start, end: Math.min(end, duration), gain: c.gain, fade: c.fade };
  });
  const music = ep.music ? { ...lib.audio(ep.music, ep._dir), ...ep.music } : null;
  if (!music) warnings.push('No background music (Kaomei completeness gate expects suitable music unless deliberately omitted)');
  if (!lines.length) (requireVoice ? errors : warnings).push('No narration: Curious Mind Shorts require voice-over');
  if (format.max_duration && duration > format.max_duration) errors.push(`Duration ${duration.toFixed(2)}s exceeds ${format.max_duration}s limit for ${ep.format}`);

  return { format, scenes, duration, windows, lines, cues, capPreset, sfx, ambience, music, errors, warnings };
}

/** Deep validation: prepares scenes and evaluates every actor at sampled times. */
export async function validateEpisode(ep, lib, prepareScene, opts = {}) {
  const tl = resolveTimeline(ep, lib, opts);
  for (const s of tl.scenes) {
    try {
      const prep = await prepareScene(lib, s);
      for (const a of prep.actors) for (let k = 0; k <= 8; k++) actorStateAt(a._char.lib, a._char.rig, a, (s._duration * k) / 8);
      const st = lib.status(`environment/${s.environment}`);
      if (st !== 'approved') tl.warnings.push(`Scene ${s.id}: environment ${s.environment} registry status is "${st}" (not owner-approved yet)`);
    } catch (e) { tl.errors.push(`Scene ${s.id}: ${e.message}`); }
  }
  return tl;
}
