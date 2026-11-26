"""s40b in two parts ('Milo sighed.' + 0.35 s + 'Tomorrow was going to be a very long day.'): one take kept being heard
as 'Milo's side ... is going'. Writes wav/s40b.wav and updates wav/dur.json."""
import json, os, torch, torchaudio as ta
from chatterbox.tts import ChatterboxTTS
HERE = os.path.dirname(os.path.abspath(__file__)); m = ChatterboxTTS.from_pretrained(device='cpu'); ref = os.path.join(HERE, 'ref_am_puck.wav')
torch.manual_seed(41); a = m.generate('Milo sighed.', audio_prompt_path=ref, exaggeration=0.7, cfg_weight=0.5)
torch.manual_seed(int(os.environ.get('S2', 42))); b = m.generate('Tomorrow... was going to be a very long day.', audio_prompt_path=ref, exaggeration=0.75, cfg_weight=0.45)
w = torch.cat([a, torch.zeros(1, int(0.35 * m.sr)), b], dim=1); ta.save(os.path.join(HERE, 'wav', 's40b.wav'), w, m.sr)
p = os.path.join(HERE, 'wav', 'dur.json'); d = json.load(open(p)); d['s40b'] = round(w.shape[-1] / m.sr, 3); json.dump(d, open(p, 'w'), indent=1); print('s40b', d['s40b'])
