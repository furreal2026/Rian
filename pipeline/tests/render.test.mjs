import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { renderEpisode } from '../src/lib/render.mjs';
import { probeStreams } from '../src/lib/audio.mjs';
import { REPO_ROOT } from '../src/lib/util.mjs';

const EP = path.join(REPO_ROOT, 'episodes/ep000_pipeline_smoke_test/episode.json');

test('integration: draft render of the first 1.5 s produces a decodable 9:16 MP4 with audio', { timeout: 120000 }, async () => {
  const { outDir, finalFile, report } = await renderEpisode(EP, { draft: true, seconds: 1.5, replace: true, name: 'test-draft' });
  try {
    const s = probeStreams(finalFile);
    const v = s.streams.find(x => x.codec_type === 'video'), a = s.streams.find(x => x.codec_type === 'audio');
    assert.equal(v.codec_name, 'h264');
    assert.equal(v.width / v.height, 9 / 16);
    assert.ok(a, 'audio stream present');
    assert.ok(Math.abs(parseFloat(s.format.duration) - 1.5) < 0.15);
    assert.equal(report.kind, 'draft');
  } finally { fs.rmSync(outDir, { recursive: true, force: true }); }
});
