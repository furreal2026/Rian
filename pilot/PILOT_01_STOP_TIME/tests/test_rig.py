import math
import random
import unittest

import numpy as np
from PIL import Image

from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig, walk_cycle
from pilot.PILOT_01_STOP_TIME.tests.helpers import POSES, RIG

LIMB_CHAINS = [("upper_arm_r", "forearm_r", "hand_r"), ("upper_arm_l", "forearm_l", "hand_l"),
               ("thigh_r", "shin_r", "foot_r"), ("thigh_l", "shin_l", "foot_l"), ("torso", "head")]
REQUIRED_PARTS = {"head", "torso", "upper_arm_r", "upper_arm_l", "forearm_r", "forearm_l", "hand_r", "hand_l",
                  "thigh_r", "thigh_l", "shin_r", "shin_l", "foot_r", "foot_l"}


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class RigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rig = Rig(RIG, POSES)

    def zero(self):
        return {p: 0.0 for p in self.rig.params}

    def test_parts_are_separate_and_drawn(self):
        for view in ("front", "side"):
            parts = {p.name: p for p in self.rig.solve(view, self.zero())}
            self.assertTrue(REQUIRED_PARTS <= set(parts), f"{view}: missing {REQUIRED_PARTS - set(parts)}")
            for name in REQUIRED_PARTS:
                self.assertIsNotNone(parts[name].sprite, name)
                spr = self.rig.sprite(parts[name].sprite)
                self.assertGreater(np.asarray(spr.levels[0].getchannel(3)).max(), 0, f"{name} sprite empty")

    def test_every_part_rotates_about_its_own_joint(self):
        for view in ("front", "side"):
            base = self.rig.joint_positions(view, self.zero())
            spec = {p["name"]: p for p in self.rig.views[view]["parts"]}
            for name in REQUIRED_PARTS:
                param = spec[name]["param"]
                self.assertIsNotNone(param, f"{name} has no rotation parameter")
                pose = self.zero()
                pose[param] = 37.0
                moved = self.rig.joint_positions(view, pose)
                # its own pivot does not move
                self.assertLess(dist(base[name], moved[name]), 1e-6, f"{view}/{name} pivot moved")
                # its children's pivots rotate around it by exactly 37 degrees
                for child, cs in spec.items():
                    if cs["parent"] == name:
                        a0 = math.atan2(base[child][1] - base[name][1], base[child][0] - base[name][0])
                        a1 = math.atan2(moved[child][1] - moved[name][1], moved[child][0] - moved[name][0])
                        self.assertAlmostEqual(math.degrees(a1 - a0) % 360, 37.0, places=6)
                        self.assertAlmostEqual(dist(base[child], base[name]), dist(moved[child], moved[name]), places=6)

    def test_pivots_at_anatomical_joints(self):
        j = self.rig.joint_positions("front", self.zero())
        H = self.rig.units_height
        # head joint at chin/neck, shoulders at shirt shoulders, hips at the hem, ankles on the ground
        self.assertAlmostEqual(j["head"][1], -360, delta=6)
        self.assertAlmostEqual(j["upper_arm_r"][1], -318, delta=6)
        self.assertAlmostEqual(j["thigh_r"][1], -214, delta=1)
        self.assertAlmostEqual(j["foot_r"][1], 0, delta=5)  # ankle; the foot stroke sits ~3 units lower
        self.assertLess(j["upper_arm_r"][0], 0)
        self.assertGreater(j["upper_arm_l"][0], 0)
        self.assertEqual(H, 568)  # 560 + 8-unit visible neck (face design v2)

    def test_proportions_constant_across_poses(self):
        rng = random.Random(4)
        base = self.rig.joint_positions("front", self.zero())
        ref = {c: [dist(base[a], base[b]) for a, b in zip(c[:-1], c[1:])] for c in LIMB_CHAINS}
        poses = list(self.rig.poses)
        for k in range(60):
            pose = self.rig.pose_angles(rng.choice(poses)) if k % 2 else {p: rng.uniform(-90, 90) for p in self.rig.params if not p.endswith(("_dx", "_dy"))}
            pose = {**self.zero(), **pose}
            for p, v in walk_cycle(rng.uniform(0, 6.28)).items():
                if not p.endswith("_dy"):
                    pose[p] += v
            jp = self.rig.joint_positions("front", pose)
            for c in LIMB_CHAINS:
                for (a, b), L in zip(zip(c[:-1], c[1:]), ref[c]):
                    self.assertAlmostEqual(dist(jp[a], jp[b]), L, places=6)

    def test_rendered_hand_follows_fk(self):
        """Raise the right arm 90 deg: the hand ink must appear where FK predicts."""
        pose = self.zero()
        pose["shoulder_r"] = 78.0  # 12 rest + 78 = 90 -> arm points screen-left
        pose["elbow_r"] = 8.0
        root = mx.translate(600, 900)
        img = Image.new("RGBA", (1200, 1000), (0, 0, 0, 0))
        self.rig.draw(img, "front", pose, "deadpan", root, include_shadow=False)
        parts = {p.name: p for p in self.rig.solve("front", pose)}
        hx, hy = mx.apply(root @ parts["hand_r"].m, 0, 11)  # centre of the hand circle
        a = np.asarray(img.getchannel("A"))
        self.assertGreater(a[int(hy), int(hx) + 11], 128)  # outline right of centre
        self.assertGreater(a[int(hy), int(hx) - 11], 128)  # outline left of centre
        sx, sy = mx.apply(root @ parts["upper_arm_r"].m, 0, 0)
        self.assertAlmostEqual(hy, sy, delta=2)            # arm horizontal
        self.assertAlmostEqual(sx - hx, 64 + 64 + 11, delta=2)

    def test_head_size_constant_in_render(self):
        widths = set()
        for pose in ("stand", "look_up", "snap", "smug_stand"):
            img = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
            p = self.rig.pose_angles(pose)
            p["head"] = 0.0
            p["torso"] = 0.0
            p["hips"] = 0.0
            self.rig.draw(img, "front", p, "deadpan", mx.translate(400, 700), include_shadow=False)
            a = np.asarray(img.getchannel("A")) > 128
            row = a[700 - 460]  # head centre height
            xs = np.nonzero(row)[0]
            widths.add(int(xs.max() - xs.min()))
        self.assertLessEqual(max(widths) - min(widths), 1, widths)

    def test_expression_set_v2(self):
        """All ten approved expressions (plus deadpan_up and the neutral alias) render, front and side, and differ."""
        sheet = ["deadpan", "skeptical", "annoyed", "exhausted", "confused", "shocked", "angry", "disgusted", "worried", "smug"]
        self.assertTrue(set(sheet + ["deadpan_up"]) <= set(self.rig.spec["expressions"]))
        seen = {}
        for name in sheet + ["deadpan_up", "neutral"]:
            for view in ("head_front", "head_side"):
                a = np.asarray(self.rig.sprite(f"{view}:{name}").levels[0].getchannel(3))
                self.assertGreater(a.max(), 0, f"{view}:{name} empty")
                if view == "head_front":
                    seen[name] = np.asarray(self.rig.sprite(f"{view}:{name}").levels[0].convert("L"), dtype=np.int16)
        self.assertTrue(np.array_equal(seen["neutral"], seen["deadpan"]))
        for i, a in enumerate(sheet):
            for b in sheet[i + 1:]:
                diff = np.abs(seen[a] - seen[b]) > 64
                self.assertGreater(diff.sum(), 150, f"{a} vs {b} too similar")

    def test_neck_visible_and_head_top(self):
        img = Image.new("RGBA", (800, 800), (0, 0, 0, 0))
        self.rig.draw(img, "front", self.zero(), "deadpan", mx.translate(400, 700), include_shadow=False)
        a = np.asarray(img.getchannel("A")) > 128
        # neck: a thin ink line on the centre between the collar and the head bottom, gaps either side
        self.assertTrue(a[700 - 363, 398:402].all())
        self.assertFalse(a[700 - 363, 388:395].any())
        self.assertFalse(a[700 - 363, 405:412].any())
        top = np.nonzero(a.any(axis=1))[0].min()
        self.assertAlmostEqual(700 - top, self.rig.units_height + 3.2, delta=3)  # head top incl. half outline

    def test_png_override_hook(self):
        self.assertEqual(self.rig.sprite_source("torso_front"), "procedural")


if __name__ == "__main__":
    unittest.main()
