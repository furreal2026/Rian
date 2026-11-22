"""TEST — render the same poses with a given rig checkout (old or new) for before/after sheets.

    python output/rig_v3_motion_TEST/compare_sheet.py <repo_root> <out_png> <label>
Uses only APIs present in both versions (Rig.draw, pose params, walk_cycle).
"""
import sys, pathlib
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
from PIL import Image, ImageDraw
from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig, walk_cycle

rig = Rig(root / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json")
Z = {p: 0.0 for p in rig.params}

def P(**kw):
    d = dict(Z); d.update(kw); return d

panels = [
    ("berdiri", "front", P()),
    ("angkat tangan 90°", "front", P(shoulder_r=78, elbow_r=8)),
    ("angkat tangan tinggi", "front", P(shoulder_r=160, elbow_r=0, shoulder_l=-160)),
    ("siku 110° + wrist", "front", P(shoulder_r=60, elbow_r=110, wrist_r=30)),
    ("lutut tekuk (samping)", "side", P(hip_l=-60, knee_l=90, ankle_l=-30)),
    ("walk φ=0.5 (samping)", "side", {**Z, **{k: Z.get(k, 0) + v for k, v in walk_cycle(1.2).items()}}),
]
W, H = 330, 760
img = Image.new("RGBA", (W * len(panels), H + 40), "white")
d = ImageDraw.Draw(img)
d.text((12, 6), sys.argv[3], fill="black", font_size=28)
for i, (name, view, p) in enumerate(panels):
    rig.draw(img, view, p, "deadpan", mx.translate(W * i + W / 2, H - 20) @ mx.scale(1.12))
    d.text((W * i + 14, H + 4), name, fill="black", font_size=22)
img.convert("RGB").save(sys.argv[2])
print("ok", sys.argv[2])
