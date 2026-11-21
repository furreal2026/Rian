// Render orchestration: frames -> FFmpeg, audio mix, mux, sidecars, contact
// sheet, full decode check and a hash-bound report. A successful render is a
// technical result only; creative/owner acceptance stays a separate human step.
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { createCanvas } from '@napi-rs/canvas';
import { Library } from './library.mjs';
import { loadEpisode, validateEpisode } from './episode.mjs';
import { prepareScene, renderScene } from './scene.mjs';
import { composeTransition } from './transitions.mjs';
import { cameraAt, worldToScreen } from './camera.mjs';
import { actorStateAt } from './character.mjs';
import { drawCaption, toSrt, toVtt } from './captions.mjs';
import { mixAudio, run, FFMPEG, probeStreams, measureLoudness } from './audio.mjs';
import { sha256File, writeJson, rel, readJson } from './util.mjs';

export function drawSafeGuides(ctx, guides, w) {
  const k = w / 1080;
  ctx.save();
  ctx.fillStyle = 'rgba(255,0,80,0.18)';
  for (const z of guides) ctx.fillRect(z.x * k, z.y * k, z.w * k, z.h * k);
  ctx.restore();
}

export class FrameRenderer {
  constructor(lib, ep, tl, { w, h }) {
    Object.assign(this, { lib, ep, tl, w, h });
    this.canvas = createCanvas(w, h);
    this.ctx = this.canvas.getContext('2d');
    this.A = createCanvas(w, h); this.B = createCanvas(w, h);
    this.preps = [];
  }
  async init() { for (const s of this.tl.scenes) this.preps.push(await prepareScene(this.lib, s)); lib_fonts(this.lib); }
  sceneIndexAt(T) {
    const sc = this.tl.scenes;
    for (let i = 0; i < sc.length; i++) if (T < sc[i]._start + sc[i]._duration) return i;
    return sc.length - 1;
  }
  drawSceneTo(ctx, i, T) {
    const s = this.tl.scenes[i];
    renderScene(ctx, this.lib, this.preps[i], T - s._start, { w: this.w, h: this.h, scale: this.w / 1080, globalTime: T });
  }
  /** Choose a caption slot that does not cover any visible character (sampled over the cue). */
  captionY(cue) {
    if (cue._y !== undefined) return cue._y;
    const P = this.tl.capPreset, slots = P.slots || { low: P.center_y };
    const i = this.sceneIndexAt((cue.start + cue.end) / 2);
    const prep = this.preps[i], s = this.tl.scenes[i];
    if (s.caption_slot) return (cue._y = slots[s.caption_slot]);
    const half = (P.font_size * P.line_height * P.max_lines) / 2 + 20;
    const boxes = [];
    for (const T of [cue.start, (cue.start + cue.end) / 2, cue.end - 0.01]) {
      const lt = T - s._start;
      const cam = cameraAt(prep.camera, lt, (id, tt) => { const a = prep.actors.find(x => x.id === id); const st = actorStateAt(a._char.lib, a._char.rig, a, tt); return { x: st.x, y: st.y - (a.follow_height ?? 220) }; });
      const out = { w: 1080, h: 1080 * this.h / this.w, scale: 1 };
      for (const a of prep.actors) {
        const st = actorStateAt(a._char.lib, a._char.rig, a, lt);
        const top = worldToScreen({ x: st.x, y: st.y - 430 * st.scale }, cam, 1, prep.env, out).y;
        const bot = worldToScreen({ x: st.x, y: st.y }, cam, 1, prep.env, out).y;
        boxes.push([top, bot]);
      }
    }
    for (const name of P.slot_order || Object.keys(slots)) {
      const y = slots[name];
      if (!boxes.some(([t0, b0]) => y + half > t0 && y - half < b0)) return (cue._y = y);
    }
    return (cue._y = slots[(P.slot_order || ['low'])[0]]);
  }
  frame(T, { captions = true, guides = false } = {}) {
    const { ctx, w, h } = this;
    ctx.save();
    ctx.clearRect(0, 0, w, h);
    const win = this.tl.windows.find(x => T >= x.start && T < x.end);
    if (win) {
      this.drawSceneTo(this.A.getContext('2d'), win.from, T);
      this.drawSceneTo(this.B.getContext('2d'), win.to, T);
      composeTransition(ctx, win.tr, (T - win.start) / win.duration, this.A, this.B, { w, h });
    } else this.drawSceneTo(ctx, this.sceneIndexAt(T), T);
    if (captions) for (const c of this.tl.cues) if (T >= c.start && T < c.end) drawCaption(ctx, c, T, this.tl.capPreset, { w, centerY: this.captionY(c) });
    if (guides) drawSafeGuides(ctx, this.tl.format.ui_overlay_zones || [], w);
    ctx.restore();
    return this.canvas;
  }
}
function lib_fonts(lib) { lib.loadFonts(); }

function writeFrame(stream, buf) {
  return new Promise(resolve => {
    if (stream.write(buf)) resolve();
    else stream.once('drain', resolve);
  });
}

export async function renderEpisode(epFile, opts = {}) {
  const lib = new Library();
  const ep = loadEpisode(epFile);
  const tl = await validateEpisode(ep, lib, prepareScene);
  if (tl.errors.length) throw new Error(`Episode is not renderable:\n- ${tl.errors.join('\n- ')}`);
  const draft = !!opts.draft;
  const fmt = tl.format;
  const scaleK = draft ? fmt.draft.scale : 1;
  const w = Math.round(fmt.width * scaleK / 2) * 2, h = Math.round(fmt.height * scaleK / 2) * 2;
  const fps = draft ? fmt.draft.fps : fmt.fps;
  const duration = opts.seconds ? Math.min(opts.seconds, tl.duration) : tl.duration;
  const name = opts.name || (draft ? 'draft' : 'final') + (opts.seconds ? `-${opts.seconds}s` : '');
  const outDir = path.join(ep._dir, 'output', name);
  if (fs.existsSync(outDir) && !opts.replace) throw new Error(`${rel(outDir)} exists; pass --replace to overwrite this render`);
  fs.mkdirSync(outDir, { recursive: true });
  const log = opts.log || (() => {});

  // 1. Audio
  log(`audio: mixing ${tl.lines.length} voice clip(s), ${tl.sfx.length} sfx, ${tl.ambience.length} ambience, music=${tl.music?.id || 'none'}`);
  const mixFile = path.join(outDir, 'mix.wav');
  mixAudio({
    voice: tl.lines.filter(l => l._file).map(l => ({ file: l._file, start: l._start, gain: l.gain ?? ep.voice?.gain ?? 1 })),
    music: tl.music ? { ...tl.music, file: tl.music.file } : null,
    ambience: tl.ambience.filter(a => a.start < duration).map(a => ({ ...a, end: Math.min(a.end, duration) })),
    sfx: tl.sfx.filter(s => s.time < duration),
  }, duration, mixFile, { loudness: fmt.loudness });

  // 2. Video frames
  const fr = new FrameRenderer(lib, ep, tl, { w, h });
  await fr.init();
  const videoFile = path.join(outDir, 'video.mp4');
  const enc = draft ? fmt.draft.encode : fmt.encode;
  const ff = spawn(FFMPEG, ['-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${w}x${h}`, '-r', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', enc.preset, '-crf', String(enc.crf), '-pix_fmt', 'yuv420p', '-r', String(fps), '-movflags', '+faststart', videoFile],
  { stdio: ['pipe', 'ignore', 'pipe'] });
  let ffErr = '';
  ff.stderr.on('data', d => { ffErr += d; });
  ff.stdin.on('error', e => { ffErr += `\nstdin: ${e.message}`; });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error(`ffmpeg video encode failed: ${ffErr.slice(-800)}`)))));
  const frames = Math.round(duration * fps);
  const t0 = Date.now();
  for (let f = 0; f < frames; f++) {
    const T = f / fps;
    const c = fr.frame(T, { guides: opts.guides });
    const data = c.getContext('2d').getImageData(0, 0, w, h).data;
    await writeFrame(ff.stdin, Buffer.from(data.buffer, data.byteOffset, data.byteLength));
    if (f % (fps * 2) === 0) log(`video: ${f}/${frames} frames (${((Date.now() - t0) / 1000).toFixed(1)}s)`);
  }
  ff.stdin.end();
  await done;

  // 3. Mux
  const finalFile = path.join(outDir, `${ep.id}${draft ? '_draft' : ''}.mp4`);
  run(FFMPEG, ['-y', '-v', 'error', '-i', videoFile, '-i', mixFile, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', String(duration), '-movflags', '+faststart', finalFile], 'mux');
  fs.rmSync(videoFile);

  // 4. Sidecars, contact sheet, decode check, report
  const cues = tl.cues.filter(c => c.start < duration);
  fs.writeFileSync(path.join(outDir, `${ep.id}.srt`), toSrt(cues));
  fs.writeFileSync(path.join(outDir, `${ep.id}.vtt`), toVtt(cues));
  const sheet = path.join(outDir, 'contact-sheet.png');
  const every = Math.max(1, Math.floor(frames / 12));
  run(FFMPEG, ['-y', '-v', 'error', '-i', finalFile, '-vf', `select='not(mod(n\\,${every}))',scale=270:-1,tile=6x2:padding=6:color=white`, '-frames:v', '1', sheet], 'contact sheet');
  run(FFMPEG, ['-v', 'error', '-i', finalFile, '-f', 'null', '-'], 'full decode check');
  const streams = probeStreams(finalFile);
  const credits = [...lib.used.values()].filter(u => u.kind === 'audio' && u.attribution_required);
  const creditText = ['Audio credits (paste into the video description):', ...credits.map(c => `- ${c.attribution}`), ''].join('\n');
  fs.writeFileSync(path.join(outDir, 'CREDITS.txt'), creditText);
  const report = {
    kind: draft ? 'draft' : 'final-candidate',
    episode: ep.id, episode_file: rel(ep._file), episode_sha256: sha256File(ep._file),
    rendered_at: new Date().toISOString(),
    output: rel(finalFile), output_sha256: sha256File(finalFile),
    width: w, height: h, fps, frames, duration_seconds: Number(duration.toFixed(3)),
    scenes: tl.scenes.map(s => ({ id: s.id, start: +s._start.toFixed(3), duration: +s._duration.toFixed(3), environment: s.environment, camera: s.camera?.preset || (s.camera?.keys ? 'keys' : 'static'), transition_out: s.transition_out?.type || 'cut' })),
    voice: tl.lines.map(l => ({ id: l.id, file: l._file ? rel(l._file) : null, start: +l._start.toFixed(3), duration: l._duration ? +l._duration.toFixed(3) : null, sha256: l._file ? sha256File(l._file) : null })),
    voice_provider: ep.voice?.provider || null,
    caption_timing: [...new Set(cues.map(c => c.timing))],
    loudness: measureLoudness(finalFile),
    streams: streams.streams.map(s => ({ type: s.codec_type, codec: s.codec_name, w: s.width, h: s.height, rate: s.r_frame_rate || s.sample_rate })),
    decode_check: 'passed (ffmpeg full decode, no errors)',
    assets_used: Object.fromEntries(lib.used),
    warnings: tl.warnings,
    render_seconds: +((Date.now() - t0) / 1000).toFixed(1),
    not_verified_by_this_report: ['human viewing at phone size', 'listening review of mix/intelligibility', 'creative acceptance of acting and camera', 'factual accuracy of narration', 'owner approval'],
  };
  writeJson(path.join(outDir, 'report.json'), report);
  fs.rmSync(mixFile);
  return { outDir, finalFile, report };
}

/** Render single stills for review (no audio). */
export async function renderStills(epFile, times, outDir, { scale = 0.5, guides = false } = {}) {
  const lib = new Library();
  const ep = loadEpisode(epFile);
  const tl = await validateEpisode(ep, lib, prepareScene, { requireVoice: false });
  const fatal = tl.errors.filter(e => !/Voice|narration/i.test(e));
  if (fatal.length) throw new Error(fatal.join('\n'));
  const w = Math.round(tl.format.width * scale), h = Math.round(tl.format.height * scale);
  const fr = new FrameRenderer(lib, ep, tl, { w, h });
  await fr.init();
  fs.mkdirSync(outDir, { recursive: true });
  const files = [];
  for (const T of times) {
    const f = path.join(outDir, `still_${T.toFixed(2)}s.png`);
    fs.writeFileSync(f, await fr.frame(T, { guides }).encode('png'));
    files.push(f);
  }
  return { files, timeline: tl };
}

export { readJson };
