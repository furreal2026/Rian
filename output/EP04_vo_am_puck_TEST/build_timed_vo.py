"""Place each VO line inside its shot (with the 6 s intro card after shot 06) (timecodes from the EP004 final storyboard) and write:
  ep04_vo_am_puck_timed.wav (48 kHz mono, -16 LUFS), cues.json, ep04_vo_am_puck.srt
Thought lines get a light treatment (short room echo, slight high-pass) so they read as 'inside a head'.
usage: python build_timed_vo.py   (run in this folder; needs ffmpeg)"""
import json, subprocess, numpy as np, soundfile as sf
LEAD, GAP, TAIL = 0.40, 0.80, 0.20          # seconds: delay after the cut, gap between two lines in one shot, keep clear of the next cut
shots = {s['shot']: s for s in json.load(open('shots.json', encoding='utf-8'))}
# intro title card (Curious Mind logo + episode title) inserted after shot 06, owner request 2026-11-26:
# every shot from 07 on moves later by INTRO_LEN; the intro itself has no narration
INTRO_AFTER, INTRO_LEN = 6, 6.0
for k, s in shots.items():
    if k > INTRO_AFTER: s['start'] += INTRO_LEN; s['end'] += INTRO_LEN
lines = json.load(open('lines.json', encoding='utf-8'))
script_text = {s['shot']: s['text'] for s in shots.values()}
SR = 24000; total = shots[max(shots)]['end']
track = np.zeros(int(total * SR) + SR); cues = []; cursor = {}
def treat(x):  # thought voice: high-pass 180 Hz + two short echoes, mixed in lightly
    from numpy import convolve
    a = np.exp(-2*np.pi*180/SR); y = np.zeros_like(x); prev_x = prev_y = 0.0
    for i, v in enumerate(x): prev_y = a*(prev_y + v - prev_x); prev_x = v; y[i] = prev_y
    out = y.copy()
    for d, g in ((0.045, .35), (0.090, .18)):
        k = int(d*SR); out[k:] += g * y[:-k]
    return out / max(1e-9, np.abs(out).max()) * np.abs(x).max()
for l in lines:
    s = shots[l['shot']]; a, sr = sf.read(f"wav/{l['id']}.wav"); assert sr == SR
    if l['kind'] == 'thought': a = treat(a)
    dur = len(a) / SR
    start = cursor.get(l['shot'], s['start'] + LEAD)
    latest = s['end'] - TAIL - dur
    if start > latest: start = max(s['start'], latest)
    end = start + dur
    track[int(start*SR):int(start*SR)+len(a)] += a
    cursor[l['shot']] = end + GAP
    cues.append({'id': l['id'], 'shot': l['shot'], 'kind': l['kind'], 'start': round(start, 3), 'end': round(end, 3),
                 'shot_start': s['start'], 'shot_end': s['end'], 'fits': end <= s['end'] + 1e-6,
                 'text': l['text'].replace('...', '…').replace("'", '’')})
track = track[:int(total * SR)]
sf.write('_timed_24k.wav', track, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '_timed_24k.wav', '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '1', 'ep04_vo_am_puck_timed.wav'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'ep04_vo_am_puck_timed.wav', '-codec:a', 'libmp3lame', '-b:a', '192k', 'ep04_vo_am_puck_timed_preview.mp3'], check=True)
json.dump(cues, open('cues.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
def tc(t): h, r = divmod(t, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}"
with open('ep04_vo_am_puck.srt', 'w', encoding='utf-8') as f:
    for i, c in enumerate(cues, 1): f.write(f"{i}\n{tc(c['start'])} --> {tc(c['end'])}\n{c['text']}\n\n")
bad = [c['id'] for c in cues if not c['fits']]
print(len(cues), 'cues; overflow:', bad or 'none'); print('tightest:', sorted(cues, key=lambda c: c['shot_end'] - c['end'])[:3])
