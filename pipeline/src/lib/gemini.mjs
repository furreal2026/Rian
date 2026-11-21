// Gemini API adapter (image + speech), one request per call, no automatic retries.
// Adapted from kaomei/stickman-video-director scripts/gemini-media.mjs (MIT, see
// third_party/kaomei-stickman-video-director/LICENSE). Changes: library module
// form, receipts include prompt/text hash for reuse checks, WAV wrapping shared.
//
// Credentials: GEMINI_API_KEY from the environment — never pasted in chat or
// written to disk. (In proxy-injected cloud sessions any placeholder value works;
// the proxy substitutes the stored key.)
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models';

export function pcmToWav(pcm, rate, channels = 1) {
  const h = Buffer.alloc(44);
  h.write('RIFF'); h.writeUInt32LE(36 + pcm.length, 4); h.write('WAVEfmt ', 8); h.writeUInt32LE(16, 16);
  h.writeUInt16LE(1, 20); h.writeUInt16LE(channels, 22); h.writeUInt32LE(rate, 24); h.writeUInt32LE(rate * 2 * channels, 28);
  h.writeUInt16LE(2 * channels, 32); h.writeUInt16LE(16, 34); h.write('data', 36); h.writeUInt32LE(pcm.length, 40);
  return Buffer.concat([h, pcm]);
}

/**
 * kind: 'speech' | 'image'. input: text (speech) or prompt (image).
 * Writes `output` and `output.request.json` (receipt). Refuses if either exists.
 */
export async function geminiGenerate({ kind, model, input, output, voice, references = [], allowNetwork, meta = {} }) {
  if (!allowNetwork) throw new Error('Network disabled: pass --allow-network only after the owner has authorised this (possibly billable) generation');
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error('Set GEMINI_API_KEY in the environment (do not paste keys in chat)');
  if (!/^[a-zA-Z0-9._-]+$/.test(model || '')) throw new Error('Invalid or missing --model');
  const receipt = `${output}.request.json`;
  if (fs.existsSync(output) || fs.existsSync(receipt)) throw new Error(`${output} or its receipt already exists — inspect it before any retry (no automatic regeneration)`);
  const parts = [{ text: input }];
  for (const f of references) {
    if (!/\.(png|jpe?g)$/i.test(f) || fs.statSync(f).size > 10 * 1024 * 1024) throw new Error('Reference must be PNG/JPEG up to 10 MiB');
    parts.push({ inlineData: { mimeType: /\.png$/i.test(f) ? 'image/png' : 'image/jpeg', data: fs.readFileSync(f).toString('base64') } });
  }
  const generationConfig = kind === 'speech'
    ? { responseModalities: ['AUDIO'], speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: voice } } } }
    : { responseModalities: ['TEXT', 'IMAGE'] };
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const record = {
    kind, provider: 'google-gemini-api', model, voice: voice || null,
    input_sha256: crypto.createHash('sha256').update(input).digest('hex'),
    input_text: input, references: references.map(r => path.basename(r)),
    requested_at: new Date().toISOString(), request_id: crypto.randomUUID(),
    status: 'submitted_or_unknown', ...meta,
  };
  fs.writeFileSync(receipt, JSON.stringify(record, null, 2), { flag: 'wx' });
  try {
    const res = await fetch(`${ENDPOINT}/${model}:generateContent`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'x-goog-api-key': key },
      body: JSON.stringify({ contents: [{ role: 'user', parts }], generationConfig }), signal: AbortSignal.timeout(180000),
    });
    if (!res.ok) {
      let reason = '';
      try { reason = (await res.json())?.error?.status || ''; } catch { /* body omitted */ }
      throw new Error(`Provider HTTP ${res.status} ${reason}`.trim());
    }
    const data = await res.json();
    const outParts = data.candidates?.[0]?.content?.parts || [];
    const payload = outParts.map(p => p.inlineData || p.inline_data).find(p => p && (kind === 'speech' ? p.mimeType?.startsWith('audio/') : p.mimeType?.startsWith('image/')));
    if (!payload?.data) throw new Error('No native media payload returned');
    let bytes = Buffer.from(payload.data, 'base64');
    if (kind === 'speech') {
      if (!/\.wav$/i.test(output) || !/^audio\/(?:L16|pcm)/i.test(payload.mimeType)) throw new Error(`Expected PCM audio and .wav output (got ${payload.mimeType})`);
      bytes = pcmToWav(bytes, Number(payload.mimeType.match(/rate=(\d+)/)?.[1] || 24000));
    } else if (!((payload.mimeType === 'image/png' && /\.png$/i.test(output)) || (payload.mimeType === 'image/jpeg' && /\.jpe?g$/i.test(output)))) {
      throw new Error(`Output extension must match native ${payload.mimeType}`);
    }
    fs.writeFileSync(output, bytes, { flag: 'wx' });
    Object.assign(record, { status: 'complete', completed_at: new Date().toISOString(), output_sha256: crypto.createHash('sha256').update(bytes).digest('hex') });
  } catch (e) {
    record.status = 'failed_or_unknown'; record.error = e.message; throw e;
  } finally {
    fs.writeFileSync(receipt, JSON.stringify(record, null, 2));
  }
  return { output, receipt, record };
}
