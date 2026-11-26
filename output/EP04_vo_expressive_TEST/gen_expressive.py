"""EP04 expressive VO (TEST, owner 2026-11-26: 'tidak ada ekspresi di suara narator').
Chatterbox TTS (open source, emotion 'exaggeration' control) cloning the approved am_puck timbre from ref_am_puck.wav
(a Kokoro am_puck clip). Same script text as ../EP04_vo_am_puck_TEST/lines.json; per-line expression level below.
usage: ~/tts-venv/bin/python gen_expressive.py [ids...]   -> wav/<id>.wav (24 kHz), wav/dur.json"""
import json, os, sys, time, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
HERE = os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(HERE, 'wav'), exist_ok=True)
lines = json.load(open(os.path.join(HERE, '..', 'EP04_vo_am_puck_TEST', 'lines.json'), encoding='utf-8'))
# expression: narrator storytelling 0.6; comic punchlines / reveals 0.75; inner-voice thoughts 0.8 (more animated)
PUNCH = {'s03', 's05', 's06', 's10', 's13', 's15', 's24', 's29', 's30', 's31', 's38', 's40b', 's41'}
CALM = {'s32', 's33', 's34', 's35', 's36'}   # the reflective section stays warm and steady
def level(l):
    if l['kind'] == 'thought': return 0.8, 0.4
    if l['id'] in PUNCH: return 0.75, 0.45
    if l['id'] in CALM: return 0.5, 0.5
    return 0.62, 0.5
only = set(sys.argv[1:])
m = ChatterboxTTS.from_pretrained(device='cpu')
dur_p = os.path.join(HERE, 'wav', 'dur.json'); dur = json.load(open(dur_p)) if os.path.exists(dur_p) else {}
for i, l in enumerate(lines):
    if only and l['id'] not in only: continue
    ex, cfg = level(l); torch.manual_seed(int(os.environ.get('SEED', 1000)) + i); t0 = time.time()
    w = m.generate(l['text'], audio_prompt_path=os.path.join(HERE, 'ref_am_puck.wav'), exaggeration=ex, cfg_weight=cfg)
    ta.save(os.path.join(HERE, 'wav', l['id'] + '.wav'), w, m.sr)
    dur[l['id']] = round(w.shape[-1] / m.sr, 3); json.dump(dur, open(dur_p, 'w'), indent=1)
    print(l['id'], 'ex', ex, 'dur', dur[l['id']], 'gen', round(time.time() - t0, 1), flush=True)
