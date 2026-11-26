import time, torchaudio as ta, torch
from chatterbox.tts import ChatterboxTTS
t0=time.time(); m=ChatterboxTTS.from_pretrained(device='cpu'); print('load',round(time.time()-t0,1))
torch.manual_seed(7)
for ex,cfg in [(0.5,0.5),(0.75,0.35)]:
    t0=time.time()
    w=m.generate("Milo tried to pull them out. A little too late.", audio_prompt_path='ref_am_puck.wav', exaggeration=ex, cfg_weight=cfg)
    ta.save(f'test/s05_ex{ex}.wav', w, m.sr); print(ex, 'gen', round(time.time()-t0,1), 'dur', round(w.shape[-1]/m.sr,2))
