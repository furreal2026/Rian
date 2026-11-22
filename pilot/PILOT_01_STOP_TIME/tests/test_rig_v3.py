"""Rig v3: shoulders, limb thickness/joints, IK, locomotion without foot sliding, planted feet,
secondary motion, hand shapes, draw order, pose library."""
import math
import unittest

import numpy as np
from PIL import Image

from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig
from pilot.PILOT_01_STOP_TIME.rig import locomotion as loco
from pilot.PILOT_01_STOP_TIME.compositor.compositor import CharacterTrack
from pilot.PILOT_01_STOP_TIME.tests.helpers import POSES, RIG


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class RigV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rig = Rig(RIG, POSES)

    def zero(self, **kw):
        z = {p: 0.0 for p in self.rig.params}
        z.update(kw)
        return z

    def world(self, view, q, raw=True):
        return {px.name: px.m for px in self.rig.solve(view, q, raw=raw)}

    # ------------------------------------------------------------ shoulders
    def test_shoulder_lifts_when_arm_raised_and_keeps_arm_direction(self):
        for side, sign in (("r", 1), ("l", -1)):
            base = self.rig.joint_positions("front", self.zero())
            low = self.rig.joint_positions("front", self.zero(**{f"shoulder_{side}": sign * 20}))
            high = self.rig.joint_positions("front", self.zero(**{f"shoulder_{side}": sign * 150}))
            self.assertAlmostEqual(low[f"upper_arm_{side}"][1], base[f"upper_arm_{side}"][1], places=6)  # dead zone
            self.assertLess(high[f"upper_arm_{side}"][1], base[f"upper_arm_{side}"][1] - 12)          # shoulder up
            # the authored arm direction is unchanged by the clavicle (compensation)
            a = math.atan2(high[f"forearm_{side}"][1] - high[f"upper_arm_{side}"][1], high[f"forearm_{side}"][0] - high[f"upper_arm_{side}"][0])
            ref = self.rig.joint_positions("front", self.zero(**{f"shoulder_{side}": sign * 150}), raw=True)
            b = math.atan2(ref[f"forearm_{side}"][1] - ref[f"upper_arm_{side}"][1], ref[f"forearm_{side}"][0] - ref[f"upper_arm_{side}"][0])
            self.assertAlmostEqual(a, b, places=6)
        side_hi = self.rig.joint_positions("side", self.zero(shoulder_l=-160))
        side_lo = self.rig.joint_positions("side", self.zero())
        self.assertLess(side_hi["upper_arm_l"][1], side_lo["upper_arm_l"][1] - 8)

    def test_shoulder_cap_invisible_at_rest(self):
        """At rest the shoulder caps reproduce the torso underneath (no seam)."""
        out = []
        for zo in (None, {"clavicle_r": 5, "clavicle_l": 5}):
            img = Image.new("RGBA", (500, 800), (255, 255, 255, 255))
            self.rig.draw(img, "front", self.zero(), "deadpan", mx.translate(250, 780) @ mx.scale(1.12), z_override=zo)
            out.append(np.asarray(img.convert("RGB"), dtype=np.int16))
        self.assertLessEqual(int(np.abs(out[0] - out[1]).sum(-1).max()), 30)

    # ------------------------------------------------------------ thickness & joints
    def test_limbs_thicker_than_v2(self):
        for sprite, min_units in (("forearm", 11.0), ("leg_thigh", 14.0), ("leg_shin", 12.5)):
            m = self.rig.sprite(sprite)
            a = np.asarray(m.levels[0].convert("RGBA").getchannel("A")) > 128
            xs = np.nonzero(a[a.shape[0] // 2])[0]
            self.assertGreaterEqual((xs.max() - xs.min() + 1) / m.px_per_unit, min_units, sprite)

    def test_joints_stay_closed_at_any_bend(self):
        """Ink along every bone of the arm and leg chains, at many joint angles (no gaps at elbows/knees)."""
        for elbow in range(-150, 151, 30):
            for view, chain, params in (("front", ("upper_arm_r", "forearm_r", "hand_r"), dict(shoulder_r=70, elbow_r=elbow)),
                                        ("side", ("thigh_l", "shin_l", "foot_l"), dict(hip_l=-40, knee_l=max(0, elbow)))):
                img = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
                root = mx.translate(450, 820) @ mx.scale(1.3)
                q = self.zero(**params)
                self.rig.draw(img, view, q, "deadpan", root, include_shadow=False)
                a = np.asarray(img.getchannel("A"))
                jp = {n: mx.apply(root @ m, 0, 0) for n, m in self.world(view, self.rig.effective_params(view, q)).items()}
                for p0, p1 in zip(chain[:-1], chain[1:]):
                    for u in np.linspace(0, 1, 25):
                        x = jp[p0][0] + (jp[p1][0] - jp[p0][0]) * u
                        y = jp[p0][1] + (jp[p1][1] - jp[p0][1]) * u
                        self.assertGreater(a[int(round(y)), int(round(x))], 128, f"{view} {p0}->{p1} gap at u={u:.2f}, bend {elbow}")

    # ------------------------------------------------------------ IK
    def test_ik_two_bone_reaches_and_bends_correctly(self):
        q = self.rig.ik_two_bone("side", self.zero(), ("thigh_l", "shin_l", "foot_l"), (60, -40), bend=-1, end_angle=0)
        w = self.world("side", q)
        self.assertLess(dist(mx.apply(w["foot_l"], 0, 0), (60, -40)), 1e-6)
        self.assertGreater(mx.apply(w["shin_l"], 0, 0)[0], mx.apply(w["thigh_l"], 0, 0)[0])   # knee forward
        self.assertAlmostEqual(self.rig._world_angle(w["foot_l"]), 0.0, places=6)            # foot flat
        q = self.rig.ik_two_bone("front", self.zero(), ("upper_arm_r", "forearm_r", "hand_r"), (-120, -300), bend=1)
        self.assertLess(dist(mx.apply(self.world("front", q)["hand_r"], 0, 0), (-120, -300)), 1e-6)

    # ------------------------------------------------------------ locomotion
    def _planted_spread(self, kind, step, eased=True):
        keys = [{"t": 0, "x": 0, "view": "side", "pose": "side_stand"}, {"t": 0.5, "x": 0},
                {"t": 4.5, "x": 1800 if kind == "walk" else 2800, "ease": "inOutSine" if eased else "linear"}]
        ch = CharacterTrack({"height": 640, "keys": keys, "secondary": False,
                             "cycles": [{"type": kind, "t0": 0.5, "t1": 4.5, "blend": 0.2, "step_length": step}]}, self.rig)
        steps = {}
        for i in range(int(4.5 * 48)):
            t = i / 48
            c = ch.cycles[0]
            if ch._cycle_weight(c, t) < 0.999:
                continue
            st = ch.pose_at(t)
            d = abs(st["x"]) / ch.scale
            flags = loco.stance_ankles(self.rig, kind, d, step)
            w = self.world("side", st["params"])
            u = loco.cycle_phase(d, step, None, kind)
            for s, v in (("l", u), ("r", (u + 0.5) % 1.0)):
                if flags[s][2]:
                    n = math.floor((d / (2 * step)) - v + 0.5 + 1e-9) * 2 + (0 if s == "l" else 1)   # footstep id
                    ax, ay = mx.apply(w[f"foot_{s}"], 0, 0)
                    steps.setdefault((s, round((st["x"] + ax * ch.scale) / 60)), []).append(st["x"] + ax * ch.scale)
        spread = max(max(v) - min(v) for v in steps.values())
        return spread, len(steps)

    def test_walk_and_run_have_no_foot_sliding(self):
        for kind, step in (("walk", 150), ("walk", 190), ("run", 230)):
            spread, n = self._planted_spread(kind, step)
            self.assertGreater(n, 4, kind)
            self.assertLess(spread, 0.5, f"{kind} step {step}: planted ankle moved {spread:.3f} px")

    def test_gait_legs_within_reach_and_knees_forward(self):
        for kind in ("walk", "run"):
            for k in range(60):
                d = k * 7.3
                q = loco.gait_params(self.rig, kind, d)
                w = self.world("side", q)
                tg = loco.leg_targets(kind, d)
                for s in "lr":
                    self.assertLess(dist(mx.apply(w[f"foot_{s}"], 0, 0), tg[s][:2]), 1e-3)
                    self.assertGreaterEqual(q[f"knee_{s}"], -4.0)

    def test_legacy_walk_cycle_still_available(self):
        keys = [{"t": 0, "x": 0, "view": "side", "pose": "side_stand"}, {"t": 2, "x": 600}]
        ch = CharacterTrack({"height": 640, "keys": keys, "cycles": [{"type": "walk_legacy", "t0": 0, "t1": 2}]}, self.rig)
        self.assertNotAlmostEqual(ch.pose_at(1.0)["params"]["hip_l"], 0.0)

    # ------------------------------------------------------------ planted feet
    def test_planted_feet_stay_put_while_hips_move(self):
        keys = [{"t": 0, "x": 0, "view": "front", "pose": "stand", "plant": 1.0},
                {"t": 1, "pose": "stand", "angles": {"hips_dx": 14, "hips_dy": 40, "hips": 4}},
                {"t": 2, "pose": "stand", "angles": {"hips_dx": -14, "hips_dy": 10}}]
        ch = CharacterTrack({"height": 640, "keys": keys, "secondary": False}, self.rig)
        ref = None
        for i in range(0, 49):
            st = ch.pose_at(i / 24)
            w = self.world("front", st["params"])
            feet = [mx.apply(w[f"foot_{s}"], 0, 0) for s in "lr"]
            ref = ref or feet
            for a, b in zip(feet, ref):
                self.assertLess(dist(a, b), 0.5)

    # ------------------------------------------------------------ secondary motion
    def test_secondary_motion_lags_then_settles(self):
        keys = [{"t": 0, "x": 0, "view": "front", "pose": "stand"},
                {"t": 0.6, "pose": "stand"}, {"t": 1.0, "pose": "arm_up_r", "ease": "inOutCubic"}]
        on = CharacterTrack({"height": 640, "keys": keys}, self.rig)
        off = CharacterTrack({"height": 640, "keys": keys, "secondary": False}, self.rig)
        mid = on.pose_at(0.85)["params"]["elbow_r"] - off.pose_at(0.85)["params"]["elbow_r"]
        self.assertGreater(abs(mid), 0.5)                          # forearm lags while the arm moves
        late = on.pose_at(3.0)["params"]["elbow_r"] - off.pose_at(3.0)["params"]["elbow_r"]
        self.assertLess(abs(late), 0.05)                           # and settles when it holds

    # ------------------------------------------------------------ hands / draw order
    def test_hand_shapes_and_z_override(self):
        for shape in self.rig.spec["hand_shapes"]:
            spr = self.rig.sprite("hand" if shape == "open" else f"hand:{shape}")
            self.assertGreater(np.asarray(spr.levels[0].convert("RGBA").getchannel("A")).max(), 0)
        point = np.asarray(self.rig.sprite("hand:point").levels[0].convert("RGBA").getchannel("A")) > 128
        open_ = np.asarray(self.rig.sprite("hand").levels[0].convert("RGBA").getchannel("A")) > 128
        self.assertGreater(point.sum(), open_.sum() * 1.15)        # the finger adds ink
        order = [p.name for p in self.rig.solve("front", self.zero(), z_override={"hand_r": 45})]
        self.assertGreater(order.index("hand_r"), order.index("head"))
        order = [p.name for p in self.rig.solve("side", self.zero())]
        self.assertGreater(order.index("hand_l"), order.index("head"))   # near arm in front of the head

    # ------------------------------------------------------------ pose library
    def test_pose_library_valid(self):
        needed = {"arms_up", "wave_a", "wave_b", "point_side", "point_up", "point_down", "arms_crossed", "touch_chin",
                  "hand_head", "scratch_head_a", "talk_a", "talk_b", "talk_c", "hold_object", "sit_chair", "sit_high",
                  "sit_cross", "sit_floor", "lie_back", "lie_knees", "lie_to_sit", "squat_deep", "sit_to_stand",
                  "crouch", "jump_air", "land", "leg_lift", "legs_crossed", "weight_l", "weight_r"}
        self.assertTrue(needed <= set(self.rig.poses), needed - set(self.rig.poses))
        for name in self.rig.poses:
            view = self.rig.poses[name].get("view", "front")
            jp = self.rig.joint_positions(view, self.rig.pose_angles(name))
            for n, (x, y) in jp.items():
                self.assertTrue(math.isfinite(x) and math.isfinite(y), f"{name}/{n}")
            if name.startswith(("sit", "lie", "crouch", "land", "squat", "weight", "stand", "side_stand")):
                for s in "lr":    # feet on (not through) the floor
                    self.assertGreater(jp[f"foot_{s}"][1], -60 if name == "sit_high" else -14, f"{name} foot {s} floats")
                    self.assertLess(jp[f"foot_{s}"][1], 8, f"{name} foot {s} below floor")
        for name in ("lie_back", "lie_knees"):            # the big head rests on the floor, not in it
            head = self.rig.joint_positions("side", self.rig.pose_angles(name))["head"]
            w = self.world("side", self.rig.effective_params("side", self.rig.pose_angles(name)))
            cx, cy = mx.apply(w["head"], 0, -108)
            self.assertLess(cy + 100, 12, name)
            self.assertGreater(cy + 100, -15, name)


if __name__ == "__main__":
    unittest.main()
