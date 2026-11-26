// Write retime.json: new shot times and the new start of every VO line (tight cut, VO 1.1x).
import { writeFileSync, readFileSync } from 'node:fs';
import { TIMELINE, DURATION, mapOld, RATE, CUES } from './episode.mjs';
const cues = CUES;
const out = { rate: RATE, duration: DURATION, shots: TIMELINE.map((e) => ({ id: e.id, start: +e.start.toFixed(3), end: +e.end.toFixed(3), oldStart: e.oldStart, oldEnd: e.oldEnd })), cues: cues.map((c) => ({ id: c.id, start: +mapOld(c.start).toFixed(3) })) };
writeFileSync('retime.json', JSON.stringify(out, null, 1));
console.log('duration', DURATION.toFixed(2), 's,', Math.round(DURATION * 24), 'frames');
for (const s of out.shots) console.log(s.id.padStart(4), s.start.toFixed(2), (s.end - s.start).toFixed(2), 'old', s.oldEnd - s.oldStart);
