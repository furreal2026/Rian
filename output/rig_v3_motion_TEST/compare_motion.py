"""TEST — same animation on the old (v2) and new (v3) rig, for a side-by-side before/after video.

    python output/rig_v3_motion_TEST/compare_motion.py <repo_root> <out.mp4> <label> [v3]
The animation uses only the Rig.draw API common to both versions; with 'v3' the walk uses the
new IK gait (rig/locomotion.py), otherwise the legacy walk_cycle.
"""
import math
import sys
import pathlib

root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from tools.render import mathx as mx  # noqa: E402
from tools.render.encode import Encoder  # noqa: E402
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig, walk_cycle  # noqa: E402

V3 = len(sys.argv) > 4 and sys.argv[4] == "v3"
if V3:
    from pilot.PILOT_01_STOP_TIME.rig import locomotion as loco  # noqa: E402
rig = Rig(root / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json")
W, H, FPS = 960, 1080, 24
Z = {p: 0.0 for p in rig.params}
enc = Encoder(sys.argv[2], W, H, FPS)


def frame(draw_fn, title):
    img = Image.new("RGBA", (W, H), (246, 246, 248, 255))
    d = ImageDraw.Draw(img)
    d.line([(0, 900), (W, 900)], fill=(170, 170, 178), width=3)
    draw_fn(img, d)
    d.rectangle([0, 0, W, 60], fill=(40, 42, 54))
    d.text((20, 14), f"{sys.argv[3]}  |  {title}", fill="white", font_size=28)
    enc.write(np.asarray(img.convert("RGB")))


def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, u)))


# A: raise both arms slowly overhead and back (shoulder test), 4 s
for i in range(96):
    u = i / 95
    a = ease(u * 2) if u < 0.5 else ease((1 - u) * 2)
    p = dict(Z, shoulder_r=146 * a, shoulder_l=-146 * a, elbow_r=6 * a, elbow_l=-6 * a)
    frame(lambda img, d: rig.draw(img, "front", p, "deadpan", mx.translate(480, 900) @ mx.scale(1.25)), "angkat dua tangan pelan")
# B: elbow pump + wrist, 2 s
for i in range(48):
    u = i / 47
    p = dict(Z, shoulder_r=70, elbow_r=60 + 60 * math.sin(2 * math.pi * u * 2), wrist_r=30 * math.sin(2 * math.pi * u * 2 + 1))
    frame(lambda img, d: rig.draw(img, "front", p, "deadpan", mx.translate(480, 900) @ mx.scale(1.25)), "siku + pergelangan")
# C: walk 4 s with ground ticks (camera follows; a sliding foot drifts against the ticks)
scale = 1.1
speed = 260.0        # rig units per second
for i in range(96):
    t = i / FPS
    dist = speed * t
    if V3:
        p = loco.gait_params(rig, "walk", dist, step=150)
        raw = True
    else:
        p = dict(Z)
        for k, v in walk_cycle(math.pi * dist / 150.0).items():
            p[k] += v
        raw = False

    def draw(img, d, p=p, dist=dist, raw=raw):
        cam = dist * scale
        for xw in range(int(cam - 600) // 60 * 60, int(cam + 600), 60):
            xp = 480 + xw - cam
            d.line([(xp, 900), (xp, 918)], fill=(150, 150, 160), width=2)
        if raw:
            rig.draw(img, "side", p, "deadpan", mx.translate(480, 900) @ mx.scale(scale), raw=True)
        else:
            rig.draw(img, "side", p, "deadpan", mx.translate(480, 900) @ mx.scale(scale))
    frame(draw, "berjalan (kamera ikut)")
enc.close()
print("ok", sys.argv[2])
