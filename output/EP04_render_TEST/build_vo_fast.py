"""Tight-cut VO (owner 2026-11-26): every am_puck clip sped up 1.1x (ffmpeg atempo, pitch kept) and placed at its new start
from retime.json (node retime.mjs). Thought lines get the same light 'inside a head' treatment as before.
Writes vo_fast/ep04_vo_am_puck_fast.wav (48 kHz mono, -16 LUFS), vo_fast/cues_fast.json, vo_fast/words_fast.json."""
import json, os, subprocess, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); VO = os.path.join(HERE, '..', 'EP04_vo_am_puck_TEST'); OUT = os.path.join(HERE, 'vo_fast')
os.makedirs(os.path.join(OUT, 'wav'), exist_ok=True)
rt = json.load(open(os.path.join(HERE, 'retime.json'))); R = rt['rate']; new_start = {c['id']: c['start'] for c in rt['cues']}
cues = json.load(open(os.path.join(VO, 'cues.json'), encoding='utf-8')); words = json.load(open(os.path.join(VO, 'wav', 'words.json'), encoding='utf-8'))
SR = 24000
def treat(x):  # same as build_timed_vo.py: high-pass 180 Hz + two short echoes
    a = np.exp(-2*np.pi*180/SR); y = np.zeros_like(x); px = py = 0.0
    for i, v in enumerate(x): py = a*(py + v - px); px = v; y[i] = py
    o = y.copy()
    for d, g in ((0.045, .35), (0.090, .18)):
        k = int(d*SR); o[k:] += g * y[:-k]
    return o / max(1e-9, np.abs(o).max()) * np.abs(x).max()
track = np.zeros(int(rt['duration'] * SR) + SR); out_cues = []; out_words = {}
for c in cues:
    fast = os.path.join(OUT, 'wav', c['id'] + '.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(VO, 'wav', c['id'] + '.wav'), '-af', f'atempo={R}', '-ar', str(SR), '-ac', '1', fast], check=True)
    a, sr = sf.read(fast); assert sr == SR
    if c['kind'] == 'thought': a = treat(a)
    st = new_start[c['id']]; i0 = int(st * SR); track[i0:i0 + len(a)] += a
    out_cues.append({**c, 'start': round(st, 3), 'end': round(st + len(a) / SR, 3)})
    out_words[c['id']] = [[w, s / R, e / R] for w, s, e in words.get(c['id'], [])]
track = track[:int(rt['duration'] * SR)]
for a, b in zip(out_cues, out_cues[1:]):
    assert a['end'] <= b['start'] + 1e-3, ('overlap', a['id'], b['id'])
sf.write(os.path.join(OUT, '_fast_24k.wav'), track, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, '_fast_24k.wav'), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '1', os.path.join(OUT, 'ep04_vo_am_puck_fast.wav')], check=True)
os.remove(os.path.join(OUT, '_fast_24k.wav'))
json.dump(out_cues, open(os.path.join(OUT, 'cues_fast.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
json.dump(out_words, open(os.path.join(OUT, 'words_fast.json'), 'w', encoding='utf-8'), ensure_ascii=False)
gaps = [round(b['start'] - a['end'], 2) for a, b in zip(out_cues, out_cues[1:])]
print(len(out_cues), 'lines; gap between lines min/median/max', min(gaps), sorted(gaps)[len(gaps)//2], max(gaps), '; length', rt['duration'])
