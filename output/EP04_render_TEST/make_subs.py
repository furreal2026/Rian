"""Burn-in subtitles for EP004 (ASS, libass).
- Text block limited to 70 % of the frame width (MarginL = MarginR = 15 % of 1920 = 288 px), smart wrapping, never outside the frame.
- Inter 46 px on a 1080 p canvas: a normal documentary subtitle size; white with a thin dark outline and soft shadow.
- Each VO line is split into chunks of at most ~2 lines (sentence first, then comma/word boundary); chunk timing comes from
  the per-word timestamps of the TTS clip (wav/words.json), so a chunk appears when its first word is spoken.
usage: python3 make_subs.py  -> ep04_subtitles.ass (+ ep04_subtitles.srt)
"""
import json, re, os

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, '..', 'EP04_vo_am_puck_TEST')
FAST = os.path.join(HERE, 'vo_expr')  # expressive VO, tight cut (build_vo_expr.py)
cues = json.load(open(os.path.join(FAST, 'cues_fast.json'), encoding='utf-8'))
words = json.load(open(os.path.join(FAST, 'words_fast.json'), encoding='utf-8'))
MAX = 88  # characters per subtitle event (two lines of ~44-56 characters at 46 px in a 1344 px wide box)


def split_long(sentence):
    if len(sentence) <= MAX:
        return [sentence]
    # split at a comma/colon/ellipsis near the middle, else at the word boundary nearest the middle
    mid = len(sentence) / 2
    cands = [m.end() for m in re.finditer(r'[,:;…]\s', sentence)]
    if not cands:
        cands = [m.start() for m in re.finditer(r'\s', sentence)]
    cut = min(cands, key=lambda c: abs(c - mid))
    return split_long(sentence[:cut].strip()) + split_long(sentence[cut:].strip())


def chunks(text):
    sents = [s.strip() for s in re.split(r'(?<=[.?!])\s+(?=[A-Z‘“"\'])', text) if s.strip()]
    out = []
    cur = ''
    for s in sents:
        for piece in split_long(s):
            if cur and len(cur) + 1 + len(piece) <= MAX:
                cur += ' ' + piece
            else:
                if cur:
                    out.append(cur)
                cur = piece
    if cur:
        out.append(cur)
    return out


def ts_ass(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'


def ts_srt(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60); ms = int(round((t - int(t)) * 1000))
    if ms == 1000:
        s += 1; ms = 0
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


events = []
for c in cues:
    parts = chunks(c['text'])
    w = words.get(c['id'], [])
    nwords = [len(p.split()) for p in parts]
    starts = []
    k = 0
    for i, p in enumerate(parts):
        if w and k < len(w) and sum(nwords) == len(w):
            starts.append(c['start'] + max(0.0, w[k][1]))
        else:  # word counts differ (ASR merged/split a word): place by character position
            off = sum(len(q) + 1 for q in parts[:i]) / max(1, len(c['text']))
            starts.append(c['start'] + off * (c['end'] - c['start']))
        k += nwords[i]
    for i, p in enumerate(parts):
        a = starts[i] if i else c['start']
        b = starts[i + 1] if i + 1 < len(parts) else c['end'] + 0.25
        events.append((a, max(b, a + 1.0), p))
# no overlaps between consecutive events
for i in range(len(events) - 1):
    a, b, p = events[i]
    if b > events[i + 1][0]:
        events[i] = (a, events[i + 1][0] - 0.02, p)

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Doc,Inter,46,&H00FFFFFF,&H00FFFFFF,&H00141414,&H96000000,0,0,0,0,100,100,0.3,0,1,2.4,1.2,2,288,288,62,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open(os.path.join(HERE, 'ep04_subtitles.ass'), 'w', encoding='utf-8') as f:
    f.write(head)
    for a, b, p in events:
        f.write(f'Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Doc,,0,0,0,,{p}\n')
with open(os.path.join(HERE, 'ep04_subtitles.srt'), 'w', encoding='utf-8') as f:
    for i, (a, b, p) in enumerate(events, 1):
        f.write(f'{i}\n{ts_srt(a)} --> {ts_srt(b)}\n{p}\n\n')
print(len(events), 'subtitle events; longest', max(len(p) for _, _, p in events), 'chars')
