// Burned-in semantic subtitles for Shorts + SRT/VTT sidecars.
// Cue text may mark emphasis with *asterisks* (drawn in the highlight colour).
import { ease, clamp } from './util.mjs';

const SPLIT_PUNCT = /([,.;:!?…—]+)\s+/;
// A chunk should not end on a word that binds to the next one.
const BINDING = new Set(['a', 'an', 'the', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'and', 'or', 'but', 'your', 'my', 'our', 'their', 'his', 'her', 'its', 'is', 'are', 'was', 'be', 'could', 'would', 'can', 'will', 'if', 'that', 'this', 'very', 'so', 'yang', 'di', 'ke', 'dan', 'atau', 'untuk', 'dengan', 'dari', 'kalau', 'jika']);

/**
 * Split a voice line into readable cues timed proportionally to characters
 * WITHIN the line's measured audio. This is not forced alignment; reports
 * label it as such. Explicit `captions` on the line override it.
 */
export function cuesFromLine(line, start, duration, maxWords = 6) {
  if (line.captions?.length) {
    return line.captions.map(c => ({ start: start + c.start, end: start + c.end, text: c.text, timing: 'explicit' }));
  }
  const words = line.text.trim().split(/\s+/);
  const chunks = [];
  let cur = [];
  for (const wd of words) {
    cur.push(wd);
    const endsClause = SPLIT_PUNCT.test(wd + ' ');
    const binds = BINDING.has(wd.replace(/[^\p{L}']/gu, '').toLowerCase());
    if ((endsClause && cur.length >= 2) || (cur.length >= maxWords && !binds) || cur.length >= maxWords + 2) { chunks.push(cur.join(' ')); cur = []; }
  }
  if (cur.length) {
    if (cur.length <= 2 && chunks.length) chunks[chunks.length - 1] += ' ' + cur.join(' ');
    else chunks.push(cur.join(' '));
  }
  const weights = chunks.map(c => c.replace(/\*/g, '').length + 4);
  const total = weights.reduce((a, b) => a + b, 0);
  let t = start;
  return chunks.map((text, i) => {
    const d = (duration * weights[i]) / total;
    const cue = { start: t, end: t + d, text, timing: 'proportional-within-line' };
    t += d;
    return cue;
  });
}

function parseRuns(text) {
  const runs = [];
  text.split(/(\*[^*]+\*)/).filter(Boolean).forEach(s => {
    if (s.startsWith('*') && s.endsWith('*')) runs.push({ text: s.slice(1, -1), hi: true });
    else runs.push({ text: s, hi: false });
  });
  return runs;
}
const plain = text => text.replace(/\*/g, '');

/** Greedy wrap with balancing; returns lines of word tokens {text, hi}. */
export function wrapCue(ctx, text, maxWidth) {
  const tokens = [];
  for (const r of parseRuns(text)) for (const wd of r.text.split(/\s+/).filter(Boolean)) tokens.push({ text: wd, hi: r.hi });
  const width = arr => ctx.measureText(arr.map(t => t.text).join(' ')).width;
  if (width(tokens) <= maxWidth) return [tokens];
  // Try the most balanced 2-line split that fits.
  let best = null;
  for (let i = 1; i < tokens.length; i++) {
    const a = tokens.slice(0, i), b = tokens.slice(i);
    const wa = width(a), wb = width(b);
    if (wa <= maxWidth && wb <= maxWidth) {
      const score = Math.abs(wa - wb);
      if (!best || score < best.score) best = { score, lines: [a, b] };
    }
  }
  if (best) return best.lines;
  return null; // does not fit in two lines → validation error
}

export function drawCaption(ctx, cue, t, preset, { w, centerY }) {
  if (t < cue.start || t >= cue.end) return;
  const k = w / 1080;
  const size = preset.font_size * k;
  ctx.save();
  ctx.font = `900 ${size}px CMNunito`;
  ctx.textBaseline = 'alphabetic';
  const lines = wrapCue(ctx, cue.text, preset.max_width * k);
  if (!lines) throw new Error(`Caption does not fit in ${preset.max_lines} lines: "${cue.text}"`);
  const pop = preset.pop_in ? ease('easeOutBack', clamp((t - cue.start) / preset.pop_in)) : 1;
  const lh = size * preset.line_height;
  const cx = preset.center_x * k, cy = (centerY ?? preset.center_y) * k;
  ctx.translate(cx, cy);
  ctx.scale(0.86 + 0.14 * pop, 0.86 + 0.14 * pop);
  const top = -((lines.length - 1) * lh) / 2;
  lines.forEach((line, li) => {
    const space = ctx.measureText(' ').width;
    const widths = line.map(tk => ctx.measureText(tk.text).width);
    const total = widths.reduce((a, b) => a + b, 0) + space * (line.length - 1);
    let x = -total / 2;
    const y = top + li * lh + size * 0.35;
    line.forEach((tk, i) => {
      ctx.lineJoin = 'round';
      ctx.shadowColor = preset.shadow_color; ctx.shadowBlur = preset.shadow_blur * k; ctx.shadowOffsetY = preset.shadow_offset * k;
      ctx.lineWidth = preset.outline * k; ctx.strokeStyle = preset.outline_color;
      ctx.strokeText(tk.text, x, y);
      ctx.shadowColor = 'transparent';
      ctx.fillStyle = tk.hi ? preset.highlight_color : preset.color;
      ctx.fillText(tk.text, x, y);
      x += widths[i] + space;
    });
  });
  ctx.restore();
}

/** Validate every cue fits; returns list of problems. */
export function checkCaptions(ctx, cues, preset) {
  const problems = [];
  ctx.save(); ctx.font = `900 ${preset.font_size}px CMNunito`;
  for (const c of cues) {
    const lines = wrapCue(ctx, c.text, preset.max_width);
    if (!lines || lines.length > preset.max_lines) problems.push(`Caption too long for ${preset.max_lines} line(s): "${plain(c.text)}" — split it at a meaning boundary`);
    if (c.end - c.start < preset.min_duration) problems.push(`Caption shorter than ${preset.min_duration}s: "${plain(c.text)}"`);
  }
  ctx.restore();
  return problems;
}

const ts = (s, sep) => {
  const ms = Math.round(s * 1000);
  const hh = String(Math.floor(ms / 3600000)).padStart(2, '0');
  const mm = String(Math.floor(ms / 60000) % 60).padStart(2, '0');
  const ss = String(Math.floor(ms / 1000) % 60).padStart(2, '0');
  return `${hh}:${mm}:${ss}${sep}${String(ms % 1000).padStart(3, '0')}`;
};
export const toSrt = cues => cues.map((c, i) => `${i + 1}\n${ts(c.start, ',')} --> ${ts(c.end, ',')}\n${plain(c.text)}\n`).join('\n');
export const toVtt = cues => 'WEBVTT\n\n' + cues.map(c => `${ts(c.start, '.')} --> ${ts(c.end, '.')}\n${plain(c.text)}\n`).join('\n');
