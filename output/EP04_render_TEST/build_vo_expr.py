"""Expressive VO (Chatterbox, am_puck timbre) for the tight cut. Two steps:
  python build_vo_expr.py place   -> tempo-match the clips, place them on the OLD (storyboard) timeline -> vo_expr/cues_old.json
  node retime.mjs                 -> retime.json (episode.mjs reads vo_expr/cues_old.json when it exists)
  python build_vo_expr.py mix     -> vo_expr/ep04_vo_expressive.wav (48 kHz mono, -16 LUFS), cues_fast.json, words_fast.json
Pace: the clips are sped up (atempo, pitch kept) so the whole VO is no slower than the Kokoro VO at 1.1x (owner request)."""
import json, os, sys, subprocess, numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(HERE, '..', 'EP04_vo_expressive_TEST'); OLDVO = os.path.join(HERE, '..', 'EP04_vo_am_puck_TEST')
OUT = os.path.join(HERE, 'vo_expr'); os.makedirs(os.path.join(OUT, 'wav'), exist_ok=True)
SR = 24000; RATE = 1.1; LEAD, GAP, TAIL = 0.40, 0.70, 0.20
lines = json.load(open(os.path.join(OLDVO, 'lines.json'), encoding='utf-8'))
shots = {s['shot']: s for s in json.load(open(os.path.join(OLDVO, 'shots.json'), encoding='utf-8'))}
for k, s in shots.items():
    if k > 6: s['start'] += 6.0; s['end'] += 6.0     # intro card after shot 06 (as build_timed_vo.py)
def treat(x):  # thought voice: high-pass 180 Hz + two short echoes (as build_timed_vo.py)
    a = np.exp(-2*np.pi*180/SR); y = np.zeros_like(x); px = py = 0.0
    for i, v in enumerate(x): py = a*(py + v - px); px = v; y[i] = py
    o = y.copy()
    for d, g in ((0.045, .35), (0.090, .18)):
        k = int(d*SR); o[k:] += g * y[:-k]
    return o / max(1e-9, np.abs(o).max()) * np.abs(x).max()
step = sys.argv[1]
if step == 'place':
    kok = json.load(open(os.path.join(OLDVO, 'wav', 'dur.json'))); src = json.load(open(os.path.join(SRC, 'wav', 'dur.json')))
    tempo = max(1.0, sum(src.values()) / (sum(kok.values()) / RATE))
    print('Chatterbox total', round(sum(src.values()), 1), 's; Kokoro at 1.1x', round(sum(kok.values()) / RATE, 1), 's; tempo', round(tempo, 3))
    cues, cursor = [], {}
    for l in lines:
        f = os.path.join(OUT, 'wav', l['id'] + '.wav')
        # trim leading/trailing silence, then tempo
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(SRC, 'wav', l['id'] + '.wav'), '-af',
                        f'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,atempo={tempo:.4f}',
                        '-ar', str(SR), '-ac', '1', f], check=True)
        d = sf.info(f).duration; s = shots[l['shot']]; d_old = d * RATE    # length on the old timeline (retime plays old time at RATE)
        st = cursor.get(l['shot'], s['start'] + LEAD); latest = s['end'] - TAIL - d_old
        if st > latest: st = max(s['start'], latest)
        cursor[l['shot']] = st + d_old + GAP * RATE
        cues.append({'id': l['id'], 'shot': l['shot'], 'kind': l['kind'], 'start': round(st, 3), 'end': round(st + d_old, 3), 'dur': round(d, 3),
                     'fits': st + d_old <= s['end'] + 1e-6, 'text': l['text'].replace('...', '…').replace("'", '’')})
    json.dump({'tempo': tempo, 'cues': cues}, open(os.path.join(OUT, 'cues_old.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('overflow:', [c['id'] for c in cues if not c['fits']] or 'none')
elif step == 'mix':
    rt = json.load(open(os.path.join(HERE, 'retime.json'))); ns = {c['id']: c['start'] for c in rt['cues']}
    co = json.load(open(os.path.join(OUT, 'cues_old.json'), encoding='utf-8')); words = json.load(open(os.path.join(OUT, 'wav', 'words.json'), encoding='utf-8'))
    track = np.zeros(int(rt['duration'] * SR) + SR); out = []
    for c in co['cues']:
        a, sr = sf.read(os.path.join(OUT, 'wav', c['id'] + '.wav')); assert sr == SR
        if c['kind'] == 'thought': a = treat(a)
        i0 = int(ns[c['id']] * SR); track[i0:i0 + len(a)] += a
        out.append({**c, 'start': ns[c['id']], 'end': round(ns[c['id']] + len(a) / SR, 3)})
    for a, b in zip(out, out[1:]): assert a['end'] <= b['start'] + 1e-3, ('overlap', a['id'], b['id'])
    sf.write(os.path.join(OUT, '_mix.wav'), track[:int(rt['duration'] * SR)], SR)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, '_mix.wav'), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '1', os.path.join(OUT, 'ep04_vo_expressive.wav')], check=True)
    os.remove(os.path.join(OUT, '_mix.wav'))
    json.dump(out, open(os.path.join(OUT, 'cues_fast.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(words, open(os.path.join(OUT, 'words_fast.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    gaps = sorted(round(b['start'] - a['end'], 2) for a, b in zip(out, out[1:]))
    print(len(out), 'lines; gaps min/median/max', gaps[0], gaps[len(gaps)//2], gaps[-1], '; length', round(rt['duration'], 2))
