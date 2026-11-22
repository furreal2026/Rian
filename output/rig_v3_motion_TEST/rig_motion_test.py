"""TEST — Rian rig v3 motion test (production CharacterTrack + Rig, same code path as the compositor).

Renders labelled segments to one 1920x1080 / 24 fps H.264 MP4 plus a contact sheet per segment.
Background, floor line, ticks and grey prop blocks are TEST scaffolding only (not environment art).
Walk/run segments also plot every planted ankle in world space: a foot that does not slide
leaves one dot per footstep.

    python output/rig_v3_motion_TEST/rig_motion_test.py [--only NAME] [--scale 1.0]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from tools.render import mathx as mx  # noqa: E402
from tools.render.encode import Encoder, probe  # noqa: E402
from pilot.PILOT_01_STOP_TIME.rig.rig import Rig  # noqa: E402
from pilot.PILOT_01_STOP_TIME.rig import locomotion as loco  # noqa: E402
from pilot.PILOT_01_STOP_TIME.compositor.compositor import CharacterTrack  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent
RIG = ROOT / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json"
W, H, FPS = 1920, 1080, 24
FLOOR = 930
BG = (246, 246, 248)


def K(t, **kw):
    d = {"t": t}
    d.update(kw)
    return d


# ---------------------------------------------------------------- segments
SEG = []


def seg(name, title, dur, keys, height=640, ox=960, oy=FLOOR, cycles=None, follow=False, props=(), secondary=True):
    SEG.append(dict(name=name, title=title, dur=dur, keys=keys, height=height, ox=ox, oy=oy, cycles=cycles or [],
                    follow=follow, props=props, secondary=secondary))


# 1 shoulders: slow raise / lower, both arms, shrug (close framing on the upper body)
seg("01_bahu", "1. Bahu ikut naik saat tangan diangkat (pelan naik-turun, dua tangan, shrug)", 7.0, [
    K(0.0, x=0, view="front", pose="stand", expression="deadpan"),
    K(0.4, pose="stand"),
    K(1.9, pose="arm_up_r", ease="inOutSine"),
    K(2.5, pose="arm_up_r"),
    K(3.6, pose="stand", ease="inOutSine"),
    K(4.6, pose="arms_up", ease="inOutCubic", expression="deadpan_up"),
    K(5.2, pose="arms_up"),
    K(5.8, pose="shrug", ease="outBack", expression="skeptical"),
    K(6.5, pose="stand", ease="inOutSine", expression="deadpan"),
], height=1350, oy=1500)

# 2 elbow + wrist
seg("02_siku_wrist", "2. Siku menekuk berbagai sudut + orientasi pergelangan", 6.0, [
    K(0.0, x=0, view="front", pose="point_side", hand_r="point"),
    K(0.8, pose="point_side", angles={"elbow_r": 35}, ease="inOutSine"),
    K(1.5, pose="point_side", angles={"elbow_r": 75, "wrist_r": 20}, ease="inOutSine"),
    K(2.2, pose="point_side", angles={"elbow_r": 115, "wrist_r": 40}, ease="inOutSine"),
    K(2.9, pose="point_side", angles={"elbow_r": 140, "wrist_r": -30}, ease="inOutSine"),
    K(3.6, pose="point_side", angles={"elbow_r": 60, "wrist_r": 35}, ease="inOutSine"),
    K(4.3, pose="point_side", angles={"elbow_r": 60, "wrist_r": -35}, ease="inOutSine"),
    K(5.0, pose="point_side", angles={"elbow_r": 0, "wrist_r": 0}, ease="inOutSine"),
    K(5.8, pose="stand", ease="inOutSine", hand_r="open"),
], height=1150, oy=1300)

# 3 hand gestures
g = [K(0.0, x=0, view="front", pose="stand", expression="deadpan")]
t = 0.3
for k in range(4):                                   # wave
    g.append(K(t + 0.35, pose="wave_a" if k % 2 == 0 else "wave_b", ease="inOutSine"))
    t += 0.35
g += [K(t + 0.6, pose="point_side", hand_r="point", ease="inOutCubic"), K(t + 1.2, pose="point_up", ease="inOutCubic"),
      K(t + 1.8, pose="point_down", ease="inOutCubic"), K(t + 2.4, pose="point_across", hand_r="open", hand_l="point", ease="inOutCubic"),
      K(t + 3.1, pose="arms_crossed", hand_l="open", ease="inOutCubic", expression="skeptical"),
      K(t + 3.9, pose="touch_chin", ease="inOutCubic", z={"hand_r": 45, "forearm_r": 44}),
      K(t + 4.6, pose="hand_head", ease="inOutCubic", z={"hand_r": 45, "forearm_r": 32}, expression="deadpan_up"),
      K(t + 5.1, pose="scratch_head_a", ease="inOutSine", hand_r="grip"),
      K(t + 5.35, pose="scratch_head_b", ease="inOutSine"), K(t + 5.6, pose="scratch_head_a", ease="inOutSine"),
      K(t + 5.85, pose="scratch_head_b", ease="inOutSine"),
      K(t + 6.6, pose="hold_object", ease="inOutCubic", z={"hand_r": 32, "forearm_r": 31}, expression="deadpan"),
      K(t + 7.3, pose="hold_both", hand_l="grip", ease="inOutCubic"),
      K(t + 8.0, pose="stand", hand_r="open", hand_l="open", ease="inOutCubic")]
seg("03_gestur", "3. Gestur: lambai, tunjuk 4 arah, silang tangan, sentuh dagu/kepala, garuk, pegang", 11.6, g)

# 4 legs: lift, cross, weight shift (planted), crouch-jump-land
seg("04_kaki", "4. Paha/lutut/ankle: angkat kaki, silang kaki, pindah berat, lompat-mendarat", 9.0, [
    K(0.0, x=-200, view="front", pose="stand", plant=0.0),
    K(0.8, pose="leg_lift_front", ease="inOutCubic"),
    K(1.4, pose="leg_lift_front", angles={"ankle_l": 30}),
    K(1.9, pose="stand", ease="inOutSine"),
    K(2.6, pose="legs_crossed", ease="inOutCubic"),
    K(3.3, pose="stand", ease="inOutCubic", plant=1.0),
    K(3.9, pose="weight_r", ease="inOutSine"),
    K(4.6, pose="weight_l", ease="inOutSine"),
    K(5.2, pose="stand", ease="inOutSine"),
    K(5.9, pose="crouch", ease="inOutCubic", expression="skeptical"),          # anticipation
    K(6.05, plant=1.0),
    K(6.25, pose="jump_air", ease="outCubic", plant=0.0, expression="shocked"),
    K(6.6, pose="jump_air", angles={"hips_dy": -10}, ease="inQuad"),
    K(6.85, pose="land", ease="inQuad", plant=0.0),      # touch-down: feet anchor here
    K(6.9, plant=1.0),
    K(7.0, pose="land"),
    K(7.7, pose="stand", ease="outBack", expression="deadpan"),
], ox=1160)

# 5 walk / 6 run (side view, camera follows, ground ticks + planted-ankle dots)
seg("05_jalan", "5. Berjalan (IK, kaki terkunci di lantai - titik merah = posisi ankle saat menapak)", 6.0, [
    K(0.0, x=0, view="side", pose="side_stand"), K(0.6, x=0), K(5.4, x=1500, ease="inOutSine"),
], cycles=[{"type": "walk", "t0": 0.6, "t1": 5.4, "blend": 0.2, "step_length": 150}], follow=True)
seg("06_lari", "6. Berlari (fase melayang, lutut menekuk, lengan menekuk)", 5.0, [
    K(0.0, x=0, view="side", pose="side_stand"), K(0.5, x=0), K(4.5, x=2600, ease="inOutSine"),
], cycles=[{"type": "run", "t0": 0.5, "t1": 4.5, "blend": 0.2, "step_length": 230}], follow=True)

# 7 sitting: chair, legs hanging & swinging, cross-legged gesturing, floor
seg("07_duduk", "7. Duduk: kursi, kaki menggantung (diayun), duduk bersila + gestur", 10.0, [
    K(0.0, x=-160, view="side", pose="side_stand"),
    K(1.0, pose="sit_to_stand", ease="inOutSine", plant=1.0),
    K(1.8, pose="sit_chair", ease="inOutCubic"),
    K(2.0, plant=0.0),
    K(2.8, pose="sit_lean_fwd", ease="inOutSine"),
    K(3.4, pose="sit_chair", ease="inOutSine"),
    K(3.5, view="side", pose="sit_high", x=-160),
    K(4.0, pose="sit_high", angles={"knee_l": -26, "knee_r": 18}, ease="inOutSine"),
    K(4.5, pose="sit_high", angles={"knee_l": 18, "knee_r": -26}, ease="inOutSine"),
    K(5.0, pose="sit_high", angles={"knee_l": -26, "knee_r": 18, "shoulder_l": -60, "elbow_l": -40}, ease="inOutSine"),
    K(5.5, pose="sit_high", angles={"knee_l": 18, "knee_r": -26}, ease="inOutSine"),
    K(6.0, view="front", pose="sit_cross", x=-160),
    K(6.7, pose="sit_cross", angles={"shoulder_r": 40, "elbow_r": 60}, ease="inOutCubic", expression="skeptical"),
    K(7.4, pose="sit_cross", angles={"shoulder_l": -50, "elbow_l": -70, "shoulder_r": 10}, ease="inOutCubic"),
    K(8.1, pose="sit_cross", angles={"clavicle_r": 14, "clavicle_l": -14, "shoulder_r": 30, "elbow_r": 90, "shoulder_l": -30, "elbow_l": -90},
      ease="outBack", expression="smug"),
    K(9.2, pose="sit_cross", ease="inOutSine", expression="deadpan"),
], props=[("chair", 0.0, 3.5), ("stool", 3.5, 6.0)])

# 8 lying, moving arms + legs, then up: lie -> sit -> squat -> stand
seg("08_berbaring_bangun", "8. Berbaring (tangan & kaki bergerak) lalu bangun: berbaring -> duduk -> berdiri", 11.0, [
    K(0.0, x=-330, view="side", pose="lie_back", expression="deadpan_up"),
    K(0.9, pose="lie_knees", ease="inOutCubic"),
    K(1.6, pose="lie_arms_up", ease="inOutCubic"),
    K(2.2, pose="lie_arms_up", angles={"shoulder_l": 40, "shoulder_r": 30, "elbow_l": 30}, ease="inOutSine"),
    K(2.8, pose="lie_knees", angles={"hip_l": -20, "knee_l": -30}, ease="inOutSine"),
    K(3.4, pose="lie_back", ease="inOutSine"),
    K(4.0, pose="lie_back", angles={"hip_l": -30}, ease="inOutSine"),
    K(4.5, pose="lie_back", ease="inOutSine", expression="deadpan"),
    K(5.3, pose="lie_to_sit", ease="inOutCubic"),
    K(6.1, pose="sit_floor", ease="inOutCubic"),
    K(6.8, pose="sit_floor", angles={"shoulder_l": -40, "shoulder_r": -30}, ease="inOutSine"),
    K(7.8, pose="squat_deep", ease="inOutCubic", plant=0.0),
    K(8.0, plant=1.0),
    K(9.0, pose="sit_to_stand", ease="inOutSine"),
    K(9.9, pose="side_stand", ease="inOutSine", plant=1.0),
    K(10.2, plant=0.0),
], ox=1010)

# 9 combinations A-G
seg("09A_bicara", "A. Berdiri sambil bicara, kedua tangan bergerak (beda-beda) + pindah berat", 6.0, [
    K(0.0, x=0, view="front", pose="stand", plant=1.0, expression="deadpan"),
    K(0.6, pose="talk_a", ease="inOutCubic"),
    K(1.2, pose="talk_b", ease="inOutCubic", angles={"hips_dx": -8}, expression="skeptical"),
    K(1.8, pose="talk_c", ease="inOutCubic", angles={"hips_dx": 6}),
    K(2.4, pose="talk_a", ease="inOutCubic", angles={"hips_dx": -4}),
    K(3.0, pose="point_side", hand_r="point", ease="inOutCubic"),
    K(3.7, pose="talk_b", hand_r="open", ease="inOutCubic"),
    K(4.4, pose="shrug", ease="outBack", expression="smug"),
    K(5.4, pose="stand", ease="inOutSine", expression="deadpan"),
])
seg("09B_jalan_gestur", "B. Berjalan sambil gestur (lengan dari key, kaki dari walk IK)", 6.0, [
    K(0.0, x=0, view="side", pose="side_stand"), K(0.5, x=0),
    K(1.4, pose="point_fwd", hand_l="point", ease="inOutCubic"),
    K(2.3, pose="arms_fwd_back", hand_l="open", ease="inOutCubic"),
    K(3.2, pose="point_fwd", hand_l="point", ease="inOutCubic"),
    K(4.2, pose="side_stand", hand_l="open", ease="inOutCubic"),
    K(5.5, x=1350, ease="inOutSine"),
], cycles=[{"type": "walk", "t0": 0.5, "t1": 5.5, "blend": 0.2, "step_length": 150, "arms": "pose"}], follow=True)
seg("09C_duduk_gerak", "C. Duduk sambil menggerakkan tangan dan kaki", 5.0, [
    K(0.0, x=-120, view="side", pose="sit_chair"),
    K(0.7, pose="sit_chair", angles={"shoulder_l": -70, "elbow_l": -40, "knee_l": -30, "ankle_l": 20}, ease="inOutSine"),
    K(1.4, pose="sit_chair", angles={"shoulder_l": -100, "elbow_l": -10, "knee_r": -24}, ease="inOutSine", hand_l="point"),
    K(2.2, pose="sit_lean_fwd", angles={"shoulder_l": -40, "elbow_l": -80, "hip_l": -20, "knee_l": 30}, ease="inOutSine", hand_l="open"),
    K(3.0, pose="sit_chair", angles={"shoulder_r": -60, "knee_l": -40, "ankle_l": 30}, ease="inOutSine"),
    K(4.2, pose="sit_chair", ease="inOutSine"),
], props=[("chair", 0.0, 5.0)])
seg("09D_baring_gerak", "D. Berbaring sambil menggerakkan tangan dan kaki", 5.0, [
    K(0.0, x=-330, view="side", pose="lie_knees"),
    K(0.8, pose="lie_knees", angles={"shoulder_l": -150, "elbow_l": -30}, ease="inOutSine"),
    K(1.5, pose="lie_knees", angles={"shoulder_l": -110, "elbow_l": -60, "hip_l": -30, "knee_l": -40}, ease="inOutSine"),
    K(2.3, pose="lie_arms_up", angles={"hip_r": -20}, ease="inOutSine"),
    K(3.1, pose="lie_knees", angles={"hip_r": -35, "knee_r": -50}, ease="inOutSine"),
    K(4.2, pose="lie_back", ease="inOutSine"),
], ox=1010)
seg("09F_tangan_tubuh", "F. Satu tangan terangkat sambil posisi tubuh berubah (berat, jongkok, condong)", 6.0, [
    K(0.0, x=0, view="front", pose="stand", plant=1.0),
    K(0.7, pose="arm_up_r", ease="inOutCubic"),
    K(1.5, pose="arm_up_r", angles={"hips_dx": -12, "hips": -3, "torso": 6, "head": -4}, ease="inOutSine"),
    K(2.3, pose="arm_up_r", angles={"hips_dx": 12, "hips": 3, "torso": -6, "head": 4}, ease="inOutSine"),
    K(3.2, pose="arm_up_r", angles={"hips_dy": 44, "torso": 3}, ease="inOutCubic"),
    K(4.0, pose="arm_up_r", angles={"torso": -8, "head": -6}, ease="inOutSine"),
    K(5.2, pose="stand", ease="inOutSine"),
])
seg("09G_jalan_berhenti_tunjuk", "G. Berjalan, berhenti, menoleh, lalu menunjuk", 7.0, [
    K(0.0, x=-700, view="side", pose="side_stand", expression="deadpan"), K(0.4, x=-700),
    K(3.0, x=300, ease="inOutSine"),
    K(3.3, pose="side_stand", angles={"head": -6}, ease="outBack"),
    K(3.7, view="front", pose="stand", angles={"head": 4}, expression="deadpan_up"),
    K(4.0, pose="stand", angles={"head": -3}, ease="outBack"),
    K(4.8, pose="point_side", hand_r="point", ease="inOutBack", expression="skeptical"),
    K(5.8, pose="point_side", angles={"elbow_r": 8, "torso": -3}),
    K(6.6, pose="stand", hand_r="open", ease="inOutSine", expression="deadpan"),
], cycles=[{"type": "walk", "t0": 0.4, "t1": 3.0, "blend": 0.2, "step_length": 150}], follow=True)


# ---------------------------------------------------------------- render
def prop_shapes(d: ImageDraw.ImageDraw, kind, x_px, scale, oy):
    grey, edge = (205, 205, 212), (150, 150, 160)
    if kind == "chair":       # seat top at the sit_chair hips height (rig units ~ 106 above the floor)
        top = oy - 106 * scale
        d.rectangle([x_px - 40 * scale, top, x_px + 70 * scale, oy], fill=grey, outline=edge, width=3)
    elif kind == "stool":
        top = oy - 150 * scale
        d.rectangle([x_px - 40 * scale, top, x_px + 60 * scale, oy], fill=grey, outline=edge, width=3)
    d.text((x_px - 34 * scale, oy - 30), "TEST prop", fill=(120, 120, 130), font_size=18)


def render_segment(rig, s, enc, sheet_frames, scale_out=1.0):
    cfg = {"height": s["height"], "keys": s["keys"], "cycles": s["cycles"], "secondary": s["secondary"]}
    ch = CharacterTrack(cfg, rig)
    n = int(round(s["dur"] * FPS))
    planted_dots = []
    cam_x = None
    picks = set(np.linspace(0, n - 1, 8).round().astype(int).tolist())
    t0 = time.time()
    for i in range(n):
        t = i / FPS
        st = ch.pose_at(t)
        if s["follow"]:
            target = st["x"]
            cam_x = target if cam_x is None else cam_x + (target - cam_x) * 0.18
        else:
            cam_x = 0.0
        img = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(img)
        oy = s["oy"]
        d.line([(0, min(oy, H - 2)), (W, min(oy, H - 2))], fill=(170, 170, 178), width=3)
        if s["follow"]:
            for xw in range(int(cam_x - 1200) // 100 * 100, int(cam_x + 1200), 100):
                xp = s["ox"] + (xw - cam_x)
                d.line([(xp, oy), (xp, oy + 18)], fill=(170, 170, 178), width=2)
        for kind, a, b in s["props"]:
            if a <= t < b:
                prop_shapes(d, kind, s["ox"] + (st["x"] - cam_x) + 60 * ch.scale, ch.scale, oy)
        m = mx.translate(s["ox"] - cam_x, oy)
        ch.draw(img, m, t)
        # planted ankle dots (walk/run): world-space ankle positions while the foot is in stance
        for c in s["cycles"]:
            w = ch._cycle_weight(c, t)
            if c["type"] in ("walk", "run") and w >= 0.999:
                x0, _ = ch.root(float(c["t0"]))
                dist = abs(st["x"] - x0) / ch.scale
                flags = loco.stance_ankles(rig, c["type"], dist, c.get("step_length"))
                jp = {px.name: mx.apply(px.m, 0, 0) for px in rig.solve("side", st["params"], raw=True)}
                for side in "lr":
                    if flags[side][2]:
                        ax, ay = jp[f"foot_{side}"]
                        planted_dots.append((st["x"] + ax * ch.scale, ay * ch.scale))
        for wx, wy in planted_dots:
            xp, yp = s["ox"] + (wx - cam_x), oy + wy + 26
            d.ellipse([xp - 4, yp - 4, xp + 4, yp + 4], fill=(214, 60, 60))
        d.rectangle([0, 0, W, 64], fill=(40, 42, 54))
        d.text((24, 16), s["title"], fill="white", font_size=30)
        d.text((W - 360, 18), f"rig v3 TEST  t={t:4.2f}s", fill=(190, 190, 200), font_size=24)
        frame = img.convert("RGB")
        if scale_out != 1.0:
            frame = frame.resize((int(W * scale_out), int(H * scale_out)), Image.LANCZOS)
        enc.write(np.asarray(frame))
        if i in picks:
            sheet_frames.append((s["name"], i, frame.copy()))
    return n, time.time() - t0, planted_dots


def stance_spread(dots, tol=40.0):
    """Group planted-ankle dots into footsteps (by world x) and return the max spread within a step."""
    if not dots:
        return 0.0, 0
    xs = sorted(x for x, _ in dots)
    groups, cur = [], [xs[0]]
    for x in xs[1:]:
        if x - cur[-1] > tol:
            groups.append(cur)
            cur = [x]
        else:
            cur.append(x)
    groups.append(cur)
    return max(max(g) - min(g) for g in groups), len(groups)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    rig = Rig(RIG)
    segs = [s for s in SEG if a.only is None or a.only in s["name"]]
    name = "rian_rig_v3_motion_test_TEST" + (f"_{a.only}" if a.only else "")
    out = OUT / f"{name}.mp4"
    enc = Encoder(out, int(W * a.scale), int(H * a.scale), FPS)
    sheet, report = [], {"segments": []}
    for s in segs:
        n, secs, dots = render_segment(rig, s, enc, sheet, a.scale)
        spread, steps = stance_spread(dots)
        report["segments"].append({"name": s["name"], "frames": n, "seconds": s["dur"], "render_s": round(secs, 1),
                                   "planted_footsteps": steps, "max_planted_ankle_spread_px": round(spread, 3)})
        print(s["name"], n, "frames", round(secs, 1), "s", "footsteps", steps, "spread_px", round(spread, 3), flush=True)
    enc.close()
    report["video"] = probe(out)
    # contact sheets: 8 frames per segment
    tw = 480
    th = int(tw * 9 / 16)
    by = {}
    for nm, i, fr in sheet:
        by.setdefault(nm, []).append((i, fr))
    rows = len(by)
    cs = Image.new("RGB", (tw * 8, th * rows), "white")
    for r, (nm, frs) in enumerate(by.items()):
        for c, (i, fr) in enumerate(frs[:8]):
            cs.paste(fr.resize((tw, th), Image.LANCZOS), (c * tw, r * th))
    cs.save(OUT / f"{name}_contact.png")
    (OUT / f"{name}.report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["video"], indent=1))


if __name__ == "__main__":
    main()
