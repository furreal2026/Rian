"""TEST — contact sheet of every pose in poses.json (production rig, shoulder drivers active)."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig
rig = Rig(ROOT / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json")
names = [k for k in rig.poses]
HANDS = {"point_side": {"hand_r": "point"}, "point_up": {"hand_r": "point"}, "point_down": {"hand_r": "point"},
         "point_across": {"hand_l": "point"}, "point_fwd": {"hand_l": "point"}, "hold_object": {"hand_r": "grip"},
         "hold_both": {"hand_r": "grip", "hand_l": "grip"}}
ZO = {"touch_chin": {"hand_r": 45, "forearm_r": 44}, "hand_head": {"hand_r": 45}, "scratch_head_a": {"hand_r": 45}, "scratch_head_b": {"hand_r": 45}}
cols, W, H = 8, 270, 470
rows = (len(names) + cols - 1) // cols
img = Image.new("RGBA", (cols * W, rows * H), "white")
d = ImageDraw.Draw(img)
for i, n in enumerate(names):
    r_, c_ = divmod(i, cols)
    v = rig.poses[n].get("view", "front")
    ox, oy = c_ * W + W / 2, r_ * H + H - 50
    d.line([(c_ * W + 10, oy + 4), (c_ * W + W - 10, oy + 4)], fill=(205, 205, 205), width=2)
    rig.draw(img, v, rig.pose_angles(n), "deadpan", mx.translate(ox - (40 if n.startswith("lie") or n in ("sit_floor",) else 0), oy) @ mx.scale(0.66),
             hands=HANDS.get(n), z_override=ZO.get(n))
    d.text((c_ * W + 8, r_ * H + H - 40), f"{n} ({v})", fill="black", font_size=18)
img.convert("RGB").save(sys.argv[1])
print(len(names), "poses")
