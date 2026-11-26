"""Extract shot timecodes and narration from the EP004 final storyboard (pandoc gfm).
usage: python parse_storyboard.py storyboard.md shots.json"""
import re, sys, json
md = open(sys.argv[1], encoding='utf-8').read()
shots = []
for m in re.finditer(r'### SHOT (\d+) \\\| (\d\d):(\d\d)–(\d\d):(\d\d)(.*?)(?=### SHOT|\# E\.)', md, re.S):
    n, a1, a2, b1, b2, body = m.groups()
    nar = re.search(r'\*\*NARRATION \(ENGLISH\)\*\*\s*\|\s*(.+?)\s*\|\s*$', body, re.M)
    text = nar.group(1).strip()
    if text[0] in '“"' and text[-1] in '”"': text = text[1:-1]
    shots.append({'shot': int(n), 'start': int(a1)*60+int(a2), 'end': int(b1)*60+int(b2), 'text': text})
json.dump(shots, open(sys.argv[2], 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(len(shots), 'shots;', shots[0]['start'], '→', shots[-1]['end'], 's')
for s in shots: print(f"{s['shot']:02d} {s['start']:>3}-{s['end']:<3} {s['text']}")
