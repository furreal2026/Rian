// Audio: probing and the final mix via FFmpeg.
// Voice is never time-stretched (upstream Kaomei rule: fit pictures to speech).
// Music is ducked under narration with a sidechain compressor.
import { spawnSync } from 'node:child_process';

export const FFMPEG = process.env.FFMPEG || 'ffmpeg';
export const FFPROBE = process.env.FFPROBE || 'ffprobe';

export function run(cmd, args, label, { input } = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024, input });
  if (r.error || r.status !== 0) throw new Error(`${label} failed: ${r.error?.message || (r.stderr || '').trim().split('\n').slice(-6).join('\n')}`);
  return r.stdout;
}

export function probeDuration(file) {
  const out = run(FFPROBE, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', file], `ffprobe ${file}`);
  const d = parseFloat(out.trim());
  if (!Number.isFinite(d)) throw new Error(`Cannot read duration of ${file}`);
  return d;
}

export function probeStreams(file) {
  return JSON.parse(run(FFPROBE, ['-v', 'error', '-show_streams', '-show_format', '-of', 'json', file], `ffprobe ${file}`));
}

/**
 * tracks: {voice:[{file,start,gain}], music:{file,gain,fade_in,fade_out,offset,duck}|null,
 *          ambience:[{file,start,end,gain,fade}], sfx:[{file,time,gain}]}
 */
export function mixAudio(tracks, duration, outFile, { loudness = { I: -14, TP: -1.5, LRA: 11 } } = {}) {
  const args = ['-y', '-v', 'error'];
  const filters = [];
  let idx = 0;
  const voiceLabels = [], busLabels = [];
  for (const v of tracks.voice) {
    args.push('-i', v.file);
    const ms = Math.round(v.start * 1000);
    filters.push(`[${idx}:a]aresample=48000,aformat=channel_layouts=stereo,adelay=${ms}|${ms},volume=${v.gain ?? 1}[v${idx}]`);
    voiceLabels.push(`[v${idx}]`); idx++;
  }
  if (voiceLabels.length) {
    filters.push(`${voiceLabels.join('')}amix=inputs=${voiceLabels.length}:normalize=0:duration=longest,apad=whole_dur=${duration}[vo]`);
    filters.push(`[vo]asplit=2[vomix][vosc]`);
    busLabels.push('[vomix]');
  }
  if (tracks.music) {
    const m = tracks.music;
    args.push('-stream_loop', '-1', '-ss', String(m.offset || 0), '-i', m.file);
    const fo = Math.max(0, duration - (m.fade_out ?? 1.5));
    filters.push(`[${idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:${duration},asetpts=N/SR/TB,volume=${m.gain ?? 0.12},afade=t=in:d=${m.fade_in ?? 0.4},afade=t=out:st=${fo}:d=${m.fade_out ?? 1.5}[mraw]`);
    if (voiceLabels.length && m.duck !== false) {
      filters.push(`[mraw][vosc]sidechaincompress=threshold=${m.duck_threshold ?? 0.02}:ratio=${m.duck_ratio ?? 6}:attack=${m.duck_attack ?? 15}:release=${m.duck_release ?? 350}[mus]`);
    } else {
      filters.push(`[mraw]anull[mus]`);
      if (voiceLabels.length) filters.push(`[vosc]anullsink`);
    }
    busLabels.push('[mus]'); idx++;
  } else if (voiceLabels.length) filters.push(`[vosc]anullsink`);
  for (const a of tracks.ambience) {
    const len = a.end - a.start;
    args.push('-stream_loop', '-1', '-i', a.file);
    const ms = Math.round(a.start * 1000), f = a.fade ?? 0.4;
    filters.push(`[${idx}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:${len},asetpts=N/SR/TB,afade=t=in:d=${f},afade=t=out:st=${Math.max(0, len - f)}:d=${f},volume=${a.gain ?? 0.05},adelay=${ms}|${ms}[a${idx}]`);
    busLabels.push(`[a${idx}]`); idx++;
  }
  for (const s of tracks.sfx) {
    args.push('-i', s.file);
    const ms = Math.round(s.time * 1000);
    const trim = s.duration ? `,atrim=0:${s.duration},afade=t=out:st=${Math.max(0, s.duration - 0.05)}:d=0.05` : '';
    filters.push(`[${idx}:a]aresample=48000,aformat=channel_layouts=stereo${trim},volume=${s.gain ?? 0.5},adelay=${ms}|${ms}[s${idx}]`);
    busLabels.push(`[s${idx}]`); idx++;
  }
  if (!busLabels.length) throw new Error('Nothing to mix: no voice, music, ambience or SFX');
  const L = loudness;
  filters.push(`${busLabels.join('')}amix=inputs=${busLabels.length}:normalize=0:duration=longest,apad=whole_dur=${duration},atrim=0:${duration},loudnorm=I=${L.I}:TP=${L.TP}:LRA=${L.LRA},aresample=48000[out]`);
  args.push('-filter_complex', filters.join(';'), '-map', '[out]', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', outFile);
  run(FFMPEG, args, 'audio mix');
  return outFile;
}

/** Integrated loudness / true peak of a file (for the delivery report). */
export function measureLoudness(file) {
  const r = spawnSync(FFMPEG, ['-hide_banner', '-nostats', '-i', file, '-af', 'loudnorm=print_format=json', '-f', 'null', '-'], { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  const m = (r.stderr || '').match(/\{[\s\S]*?\}/g);
  if (!m) return null;
  try { const j = JSON.parse(m[m.length - 1]); return { integrated_lufs: Number(j.input_i), true_peak_dbtp: Number(j.input_tp), lra: Number(j.input_lra) }; }
  catch { return null; }
}
