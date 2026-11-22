"""Author the v3 pose library into pilot/PILOT_01_STOP_TIME/rig/poses.json (existing poses kept).

Hand-authored poses are written as angles. Contact poses (hand on head/chin, crossed arms,
holding, sitting with feet on the floor, cross-legged, lying with knees up) are solved with the
rig's own two-bone IK and stored as plain angles, so they work everywhere poses work.

    python output/rig_v3_motion_TEST/author_poses.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.render import mathx as mx  # noqa: E402
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig  # noqa: E402

RIG = ROOT / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json"
POSES = ROOT / "pilot/PILOT_01_STOP_TIME/rig/poses.json"
rig = Rig(RIG, POSES)


def Z():
    return {p: 0.0 for p in rig.params}


def hand(view, angles):
    return {"view": view, "angles": angles}


def joints(view, q):
    return {px.name: mx.apply(px.m, 0, 0) for px in rig.solve(view, q, raw=True)}


def ik(view, base, side, target, limb="arm", bend=None, end_angle=None, outward=None):
    """Solve one chain on effective params. outward: pick the bend that puts the elbow/knee further out (front)."""
    spec = rig.spec["ik"][view][f"{limb}_{side}"]
    q = rig.effective_params(view, base) if "_eff" not in base else base
    cands = [bend] if bend is not None else [spec["bend"], -spec["bend"]]
    best = None
    for b in cands:
        r = rig.ik_two_bone(view, q, tuple(spec["chain"]), target, bend=b, end_angle=end_angle, effective=True)
        if limb == "arm":
            # the shoulder driver lifts the clavicle for raised arms: re-solve from the lifted shoulder
            for _ in range(6):
                raw = rig.authored_from_effective(view, {k: v for k, v in r.items() if k != "_eff"})
                r = rig.effective_params(view, raw)
                r = rig.ik_two_bone(view, r, tuple(spec["chain"]), target, bend=b, end_angle=end_angle, effective=True)
        mid = joints(view, r)[spec["chain"][1]]
        score = (-mid[0] if side == "r" else mid[0]) if outward else 0
        if best is None or score > best[0]:
            best = (score, r)
    r = best[1]
    r["_eff"] = 1
    return r


def store(view, q):
    q = {k: v for k, v in q.items() if k != "_eff"}
    raw = rig.authored_from_effective(view, q)   # clavicles return to driver control
    return {"view": view, "angles": {k: round(v, 2) for k, v in raw.items() if abs(v) > 0.005}}


P = {}
# ------------------------------------------------------------------ front: arms & gestures
P["arms_up"] = hand("front", {"shoulder_r": 146, "elbow_r": 6, "shoulder_l": -146, "elbow_l": -6, "head": -4, "hips_dy": -2})
P["arm_up_r"] = hand("front", {"shoulder_r": 138, "elbow_r": 6, "wrist_r": -4, "torso": -2, "head": -3, "shoulder_l": -4})
P["wave_a"] = hand("front", {"shoulder_r": 126, "elbow_r": 34, "wrist_r": 14, "torso": -1.5, "head": 3, "shoulder_l": -3, "elbow_l": 4})
P["wave_b"] = hand("front", {"shoulder_r": 132, "elbow_r": -8, "wrist_r": -16, "torso": -2.5, "head": 4, "shoulder_l": -3, "elbow_l": 4})
P["point_side"] = hand("front", {"shoulder_r": 80, "elbow_r": 2, "wrist_r": -2, "torso": -2, "head": 5, "shoulder_l": -3})
P["point_up"] = hand("front", {"shoulder_r": 140, "elbow_r": 10, "wrist_r": 0, "torso": -1, "head": -8, "shoulder_l": -3})
P["point_down"] = hand("front", {"shoulder_r": 38, "elbow_r": -6, "wrist_r": -4, "torso": 2, "head": 7})
P["point_across"] = hand("front", {"shoulder_r": -2, "elbow_r": -2, "shoulder_l": -78, "elbow_l": -2, "torso": 2, "head": -5})
P["talk_a"] = hand("front", {"shoulder_r": 26, "elbow_r": 72, "wrist_r": 18, "shoulder_l": -18, "elbow_l": -44, "wrist_l": -10, "head": 2})
P["talk_b"] = hand("front", {"shoulder_r": 44, "elbow_r": 38, "wrist_r": -8, "shoulder_l": -40, "elbow_l": -66, "wrist_l": -14, "torso": -1.5, "head": -3})
P["talk_c"] = hand("front", {"shoulder_r": 18, "elbow_r": 30, "shoulder_l": -54, "elbow_l": -88, "wrist_l": -20, "torso": 2, "head": 5})
P["shrug"] = hand("front", {"clavicle_r": 16, "clavicle_l": -16, "shoulder_r": 34, "elbow_r": 96, "wrist_r": 10, "shoulder_l": -34, "elbow_l": -96,
                            "wrist_l": -10, "head": -5})
P["weight_r"] = hand("front", {"hips_dx": -12, "hips": -3, "torso": 4, "head": -2, "shoulder_r": 3, "shoulder_l": -5})
P["weight_l"] = hand("front", {"hips_dx": 12, "hips": 3, "torso": -4, "head": 2, "shoulder_r": 5, "shoulder_l": -3})
P["crouch"] = hand("front", {"hips_dy": 46, "torso": 3, "head": 4, "shoulder_r": -18, "elbow_r": -16, "shoulder_l": 18, "elbow_l": 16})
P["jump_air"] = hand("front", {"hips_dy": -70, "torso": -2, "head": -5, "shoulder_r": 138, "elbow_r": 10, "shoulder_l": -138, "elbow_l": -10,
                               "hip_r": 6, "knee_r": -10, "ankle_r": 14, "hip_l": -6, "knee_l": 10, "ankle_l": -14})
P["land"] = hand("front", {"hips_dy": 34, "torso": 2, "head": 6, "shoulder_r": 46, "elbow_r": 14, "shoulder_l": -46, "elbow_l": -14})
P["legs_crossed"] = hand("front", {"hip_r": -9, "knee_r": 2, "ankle_r": 6, "hip_l": 4, "knee_l": -2, "hips_dx": 2, "torso": -2, "head": 3,
                                   "shoulder_r": 4, "shoulder_l": -6})
P["leg_lift_front"] = hand("front", {"hip_l": -34, "knee_l": 52, "ankle_l": -18, "hips_dx": -8, "hips": -2, "torso": 3,
                                     "shoulder_r": 30, "elbow_r": 10, "shoulder_l": -40, "elbow_l": -14})

# IK contact poses, front
# Arms are 128 units long and the head is 200 wide: hands reach the side of the head, not its top.
b = Z(); b.update(torso=-1, head=-8)
q = ik("front", b, "r", (-122, -440), outward=True)                  # hand on the side of the head (z hand_r 45)
P["hand_head"] = store("front", q)
b = Z(); b.update(torso=-3, head=-7)
q = ik("front", b, "r", (-128, -452), outward=True)                  # draw with z hand_r 45: fingers over the head edge                  # scratching the side/back of the head
P["scratch_head_a"] = store("front", q)
b = Z(); b.update(torso=-3, head=-8)
q = ik("front", b, "r", (-122, -462), outward=True)
P["scratch_head_b"] = store("front", q)
b = Z(); b.update(head=4)
q = ik("front", b, "r", (-26, -366), outward=True)                   # hand to the chin (draw with z hand_r 45)
P["touch_chin"] = store("front", q)
b = Z()
q = ik("front", b, "r", (34, -266), outward=True)                    # crossed arms
q = ik("front", q, "l", (-30, -252), outward=True)
P["arms_crossed"] = store("front", q)
b = Z(); b.update(head=6)
q = ik("front", b, "r", (-98, -262), outward=True)                   # holding an object in front
P["hold_object"] = store("front", q)
q = ik("front", Z(), "l", (96, -262), outward=True)
q = ik("front", q, "r", (-96, -262), outward=True)
P["hold_both"] = store("front", q)

# cross-legged on the floor (bersila), hands on the knees
b = Z(); b.update(hips_dy=165, torso=0, head=2)
q = ik("front", b, "r", (-6, -6), limb="leg", end_angle=-10, outward=True)   # knees out, feet tucked in the middle
q = ik("front", q, "l", (6, -2), limb="leg", end_angle=10, outward=True)
jp = joints("front", q)
q = ik("front", q, "r", (jp["shin_r"][0] + 10, jp["shin_r"][1] - 18), outward=True)
q = ik("front", q, "l", (jp["shin_l"][0] - 10, jp["shin_l"][1] - 18), outward=True)
P["sit_cross"] = store("front", q)

# ------------------------------------------------------------------ side
P["point_fwd"] = hand("side", {"shoulder_l": -86, "elbow_l": -4, "wrist_l": -2, "torso": 2, "head": -2})
P["reach_up"] = hand("side", {"shoulder_l": -162, "elbow_l": -6, "shoulder_r": -150, "elbow_r": -10, "torso": -3, "head": -10})
P["leg_lift"] = hand("side", {"hip_l": -72, "knee_l": 84, "ankle_l": 8, "torso": 2, "shoulder_l": 22, "elbow_l": -20,
                              "shoulder_r": -26, "elbow_r": -24})
P["arms_fwd_back"] = hand("side", {"shoulder_l": -60, "elbow_l": -20, "shoulder_r": 40, "elbow_r": -10, "torso": 2})

def sit(name, hips_dy, ankle, foot_angle, torso=-2.0, arms=True):
    b = Z(); b.update(hips_dy=hips_dy, torso=torso, head=-torso * 0.5, hip_l=-88, hip_r=-86, knee_l=88, knee_r=86)
    q = rig.effective_params("side", b); q["_eff"] = 1
    for s, dx in (("l", 0.0), ("r", -6.0)):
        q = ik("side", q, s, (ankle[0] + dx, ankle[1]), limb="leg", bend=-1, end_angle=foot_angle)
    if arms:   # hands resting on the thighs
        jp = joints("side", q)
        for s in "lr":
            k = jp[f"shin_{s}"]
            q = ik("side", q, s, (k[0] - 46, k[1] - 22), bend=1)
    P[name] = store("side", q)

sit("sit_chair", 104, (112, 0), 0.0)
sit("sit_high", 58, (100, -48), 26.0)
sit("sit_lean_fwd", 104, (98, 0), 0.0, torso=14)

b = Z(); b.update(hips_dy=185, torso=-8, head=3, shoulder_l=24, elbow_l=-6, shoulder_r=20, elbow_r=-6)
q = rig.effective_params("side", b); q["_eff"] = 1
for s, dx in (("l", 0.0), ("r", -8.0)):
    q = ik("side", q, s, (206 + dx, -6), limb="leg", bend=-1, end_angle=-74)
P["sit_floor"] = store("side", q)

# lying on the back; the head is big, so the torso rests inclined with the head on the floor
P["lie_back"] = hand("side", {"hips": -74, "hips_dy": 185, "hips_dx": 30, "head": 6, "hip_l": -10, "hip_r": -12, "ankle_l": -6,
                              "ankle_r": -4, "shoulder_l": 8, "elbow_l": -6, "shoulder_r": 4, "elbow_r": -4})
base = dict(Z(), **P["lie_back"]["angles"])
q = rig.effective_params("side", base); q["_eff"] = 1
hip0 = joints("side", q)["thigh_l"]
lb = dict(q)
for s_, dx in (("l", 0.0), ("r", -8.0)):      # straight legs, heels on the floor, toes up
    lb = ik("side", lb, s_, (hip0[0] + 204 + dx, -3), limb="leg", bend=-1, end_angle=-80.0)
P["lie_back"] = store("side", lb)
P["lie_arms_up"] = hand("side", dict(P["lie_back"]["angles"], shoulder_l=-150, elbow_l=-20, shoulder_r=-120, elbow_r=-30))
hip = joints("side", q)["thigh_l"]
q = ik("side", q, "l", (hip[0] + 122, -2), limb="leg", bend=-1, end_angle=0.0)
q = ik("side", q, "r", (hip[0] + 112, -2), limb="leg", bend=-1, end_angle=0.0)
P["lie_knees"] = store("side", q)
# getting up: half-way from lying to sitting (torso raised, hands pushing the floor)
P["lie_to_sit"] = hand("side", {"hips": -36, "hips_dy": 186, "hips_dx": 14, "head": 2, "hip_l": -54, "hip_r": -56,
                                "knee_l": 40, "knee_r": 44, "ankle_l": -20, "ankle_r": -18, "shoulder_l": 30, "elbow_l": -10,
                                "shoulder_r": 34, "elbow_r": -8})
b = dict(Z(), **P["lie_to_sit"]["angles"])
q = rig.effective_params("side", b); q["_eff"] = 1
hip0 = joints("side", q)["thigh_l"]
for s_, dx in (("l", 0.0), ("r", -10.0)):     # heels on the floor, knees slightly up
    q = ik("side", q, s_, (hip0[0] + 186 + dx, -3), limb="leg", bend=-1, end_angle=-50.0)
P["lie_to_sit"] = store("side", q)
# standing up from the chair: lean forward, weight over the feet (use with plant)
P["sit_to_stand"] = hand("side", {"hips_dy": 70, "hips_dx": 30, "torso": 32, "head": -18, "hip_l": -70, "hip_r": -68,
                                  "knee_l": 82, "knee_r": 80, "shoulder_l": -40, "elbow_l": -20, "shoulder_r": -30, "elbow_r": -20})

# deep squat on the way up from the floor (feet under the hips, used with plant)
P["squat_deep"] = hand("side", {"hips_dy": 128, "hips_dx": 6, "torso": 30, "head": -16, "shoulder_l": -50, "elbow_l": -30,
                                "shoulder_r": -40, "elbow_r": -30})
b = dict(Z(), **P["squat_deep"]["angles"])
q = rig.effective_params("side", b); q["_eff"] = 1
for s_, dx in (("l", 34.0), ("r", 22.0)):
    q = ik("side", q, s_, (dx, -2), limb="leg", bend=-1, end_angle=0.0)
P["squat_deep"] = store("side", q)


def planted(name, xs=None):
    """Bake planted-feet IK into a pose whose hips move: feet on the floor at the standing pose's
    ankle height and x (or the given x per leg), flat."""
    v = P[name]["view"]
    b = dict(Z(), **P[name]["angles"])
    q = rig.effective_params(v, b); q["_eff"] = 1
    stand = joints(v, rig.effective_params(v, Z()))
    for s_ in "lr":
        x = xs[s_] if xs else stand[f"foot_{s_}"][0]
        q = ik(v, q, s_, (x, stand[f"foot_{s_}"][1]), limb="leg", bend=rig.spec["ik"][v][f"leg_{s_}"]["bend"], end_angle=0.0)
    P[name] = store(v, q)


for n in ("crouch", "land", "weight_r", "weight_l"):
    planted(n)
planted("sit_to_stand", {"l": 44.0, "r": 34.0})

if __name__ == "__main__":
    data = json.loads(POSES.read_text(encoding="utf-8"))
    for k, v in P.items():
        data[k] = v
    out = ["{"]
    items = list(data.items())
    for i, (k, v) in enumerate(items):
        out.append(f"  {json.dumps(k)}: {json.dumps(v)}" + ("," if i < len(items) - 1 else ""))
    out.append("}")
    POSES.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("poses:", len(data), "new/updated:", len(P))
