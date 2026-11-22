"""TEST — QC renders of the production rig after the face v2 port (heads front/side + full body)."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from PIL import Image, ImageDraw
from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig
EP = pathlib.Path("pilot/PILOT_01_STOP_TIME")
OUT = pathlib.Path(__file__).resolve().parent
rig = Rig(EP / "rig/stick_figure_rig.json")
names = list(rig.spec["expressions"])
# heads, front + side
W = 300
img = Image.new("RGBA", (W * len(names), 700), "white")
d = ImageDraw.Draw(img)
for i, n in enumerate(names):
    for row, sp in enumerate(("head_front", "head_side")):
        m = rig.sprite(f"{sp}:{n}")
        im = m.levels[0].convert("RGBA").resize((m.size[0] * 2 // 3, m.size[1] * 2 // 3), Image.LANCZOS)
        img.alpha_composite(im, (i * W + (W - im.width) // 2, 20 + row * 330))
    d.text((i * W + 20, 670), n, fill="black", font_size=26)
img.save(OUT / "rig_v2_heads_front_side_TEST.png")
# full body through Rig.draw (FK), one pose per expression sample
poses = [("stand", "deadpan"), ("look_up", "deadpan_up"), ("snap", "shocked"), ("smug_stand", "smug"), ("side_stand", "skeptical")]
body = Image.new("RGBA", (420 * len(poses), 760), "white")
d = ImageDraw.Draw(body)
for i, (pose, ex) in enumerate(poses):
    p = rig.pose_angles(pose)
    view = rig.poses[pose].get("view", "front")
    rig.draw(body, view, p, ex, mx.translate(210 + i * 420, 700) @ mx.scale(1.15))
    d.text((i * 420 + 20, 720), f"{pose} / {ex}", fill="black", font_size=24)
body.save(OUT / "rig_v2_full_body_TEST.png")
print("ok", img.size, body.size)
