"""shots.json -> lines.json for core/tts/tts.py (voice am_puck). Thought lines get a slightly different pace."""
import json
shots = json.load(open('shots.json', encoding='utf-8'))
THOUGHT = {9, 15, 23}
NARR_SPEED, THOUGHT_SPEED = 0.95, 1.0
def clean(t):  # ASCII punctuation for the phonemizer; text content unchanged
    return t.replace('…', '...').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
lines = []
for s in shots:
    n = s['shot']
    if n == 40:
        lines.append({'id': 's40a', 'shot': 40, 'kind': 'thought', 'text': clean('Feed me. And… open the door.'), 'voice': 'am_puck', 'speed': THOUGHT_SPEED, 'lang': 'en-us'})
        lines.append({'id': 's40b', 'shot': 40, 'kind': 'narrator', 'text': clean('Milo sighed. Tomorrow was going to be a very long day.'), 'voice': 'am_puck', 'speed': NARR_SPEED, 'lang': 'en-us'})
        continue
    k = 'thought' if n in THOUGHT else 'narrator'
    lines.append({'id': f's{n:02d}', 'shot': n, 'kind': k, 'text': clean(s['text']), 'voice': 'am_puck', 'speed': THOUGHT_SPEED if k == 'thought' else NARR_SPEED, 'lang': 'en-us'})
json.dump(lines, open('lines.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(lines), 'lines')
