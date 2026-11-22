"""Modular cut-out rig with forward kinematics.

A rig is a JSON spec (see pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json). Each view lists
parts with: parent, joint (pivot position in the parent's local frame), rest angle, the pose
parameter that rotates it, sprite and draw order (z). The local frame of a part has its origin
at its pivot (the anatomical joint), so rotating a parameter rotates that part and all of its
children about the joint.

    world(part) = world(parent) @ T(joint + translate_params + lift) @ R(rest + pose[param])

Before FK the pose goes through `effective_params`: per-view drivers (e.g. raising an arm lifts
its clavicle/shoulder) are added, then joint limits are applied. `ik_two_bone` solves a
two-bone chain (shoulder-elbow-wrist or hip-knee-ankle) so its end pivot reaches a root-space
target; locomotion and planted-feet keys use it.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from tools.render import mathx as mx
from .character_art import StickFigureArt
from tools.render.raster import MipImage, draw_affine


@dataclass
class PartXform:
    name: str
    sprite: str | None
    z: float
    m: np.ndarray  # local rig units -> character root space (rig units)


class Rig:
    def __init__(self, spec_path: str | Path, poses_path: str | Path | None = None, px_per_unit: float = 2.0, ss: int = 4):
        self.spec_path = Path(spec_path)
        self.spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        self.params = list(self.spec["params"])
        self.units_height = float(self.spec["units_height"])
        self.views = self.spec["views"]
        self.poses: dict = {}
        if poses_path is None:
            cand = self.spec_path.parent / "poses.json"
            poses_path = cand if cand.exists() else None
        if poses_path:
            self.poses = {k: v for k, v in json.loads(Path(poses_path).read_text(encoding="utf-8")).items() if not k.startswith("_")}
        self.art = StickFigureArt(self.spec, px_per_unit=px_per_unit, ss=ss)
        self._sprites: dict[str, MipImage] = {}
        self._overrides = self._load_overrides()
        for vname, view in self.views.items():
            names = [p["name"] for p in view["parts"]]
            for p in view["parts"]:
                if p["parent"] != "root" and p["parent"] not in names:
                    raise ValueError(f"rig view '{vname}': part '{p['name']}' has unknown parent '{p['parent']}'")
                if p.get("param") and p["param"] not in self.params:
                    raise ValueError(f"rig view '{vname}': part '{p['name']}' uses undeclared param '{p['param']}'")

    # ---------------------------------------------------------- sprites
    def _load_overrides(self) -> dict:
        d = self.spec_path.parent / self.spec.get("parts_override_dir", "parts")
        meta_path = d / "parts.json"
        if not meta_path.exists():
            return {}
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        out = {}
        for name, m in meta.items():
            png = d / f"{name.replace(':', '__')}.png"
            if png.exists():
                out[name] = (png, m)
        return out

    def sprite(self, name: str) -> MipImage:
        if name not in self._sprites:
            if name in self._overrides:
                png, m = self._overrides[name]
                self._sprites[name] = MipImage(Image.open(png), origin=tuple(m["pivot_px"]), px_per_unit=float(m["px_per_unit"]))
            else:
                self._sprites[name] = self.art.make(name)
        return self._sprites[name]

    def sprite_source(self, name: str) -> str:
        return "png_override" if name in self._overrides else "procedural"

    # -------------------------------------------------------------- poses
    def pose_angles(self, pose_name: str) -> dict[str, float]:
        if pose_name not in self.poses:
            raise KeyError(f"unknown pose '{pose_name}'. Known: {sorted(self.poses)}")
        a = {p: 0.0 for p in self.params}
        a.update({k: float(v) for k, v in self.poses[pose_name]["angles"].items()})
        return a

    # ---------------------------------------------------------------- FK
    # ------------------------------------------------------- drivers/limits
    def effective_params(self, view: str, params: dict[str, float]) -> dict[str, float]:
        """Pose params after drivers (added), joint limits (clamped) and clavicle compensation.
        The result is meant for `solve(..., raw=True)`; do not feed it through this again."""
        out = {p: float(params.get(p, 0.0)) for p in self.params}
        for d in self.spec.get("drivers", {}).get(view, []):
            src = out.get(d["source"], 0.0)
            sign = int(d.get("sign", 1))
            v = abs(src) if sign == 0 else sign * src
            v = min(float(d.get("max", 1e9)), float(d["gain"]) * max(0.0, v - float(d.get("dead", 0.0))))
            out[d["target"]] = out.get(d["target"], 0.0) + (v if sign == 0 else sign * v)
        for name, (lo, hi) in self.spec.get("limits", {}).get(view, {}).items():
            if name in out:
                out[name] = min(float(hi), max(float(lo), out[name]))
        for clav, arm in self.spec.get("clavicle_compensate", {}).get(view, {}).items():
            if not clav.startswith("_"):
                out[arm] = out.get(arm, 0.0) - out.get(clav, 0.0)
        return out

    def authored_from_effective(self, view: str, q: dict[str, float]) -> dict[str, float]:
        """Authored params whose arm directions equal those of effective params q (used to store
        IK-derived poses). With compensation the upper-arm world angle is torso + rest + authored
        shoulder, so authored = q_shoulder + q_clavicle; clavicles return to driver control."""
        out = dict(q)
        comp = {k: v for k, v in self.spec.get("clavicle_compensate", {}).get(view, {}).items() if not k.startswith("_")}
        for clav, arm in comp.items():
            out[arm] = q.get(arm, 0.0) + q.get(clav, 0.0)
            out[clav] = 0.0
        return out

    # ---------------------------------------------------------------- FK
    def solve(self, view: str, params: dict[str, float], expression: str = "deadpan",
              hands: dict[str, str] | None = None, z_override: dict[str, float] | None = None,
              raw: bool = False) -> list[PartXform]:
        """Forward kinematics. `hands` maps a hand part ("hand_r") to a shape ("point");
        `z_override` changes draw order per part (e.g. a hand in front of the face);
        `raw=True` skips drivers/limits (used by the IK solver on already-effective params)."""
        if view not in self.views:
            raise KeyError(f"unknown view '{view}'. Known: {sorted(self.views)}")
        if not raw:
            params = self.effective_params(view, params)
        parts = self.views[view]["parts"]
        world: dict[str, np.ndarray] = {"root": np.eye(3)}
        out: list[PartXform] = []
        pending = list(parts)
        guard = 0
        while pending:
            guard += 1
            if guard > 1000:
                raise ValueError("rig hierarchy has a cycle")
            p = pending.pop(0)
            if p["parent"] not in world:
                pending.append(p)
                continue
            jx, jy = p["joint"]
            for i, tp in enumerate(p.get("translate_params", [])):
                v = float(params.get(tp, 0.0))
                if i == 0:
                    jx += v
                else:
                    jy += v
            lift = p.get("lift")
            if lift:
                v = float(params.get(lift["param"], 0.0))
                jx += lift["per_deg"][0] * v
                jy += lift["per_deg"][1] * v
            ang = float(p.get("rest", 0.0)) + (float(params.get(p["param"], 0.0)) if p.get("param") else 0.0)
            m = world[p["parent"]] @ mx.translate(jx, jy) @ mx.rotate_deg(ang)
            world[p["name"]] = m
            sprite = p.get("sprite")
            if sprite and sprite.startswith("head_"):
                sprite = f"{sprite}:{expression}"
            elif sprite == "hand" and hands and hands.get(p["name"], "open") != "open":
                shape = hands[p["name"]]
                if shape not in self.spec.get("hand_shapes", ["open"]):
                    raise KeyError(f"unknown hand shape '{shape}'. Known: {self.spec.get('hand_shapes')}")
                sprite = f"hand:{shape}"
            z = float(z_override[p["name"]]) if z_override and p["name"] in z_override else float(p["z"])
            out.append(PartXform(p["name"], sprite, z, m))
        out.sort(key=lambda x: x.z)
        return out

    # ---------------------------------------------------------------- IK
    @staticmethod
    def _world_angle(m: np.ndarray) -> float:
        return math.degrees(math.atan2(m[1, 0], m[0, 0]))

    def ik_two_bone(self, view: str, params: dict[str, float], chain: tuple[str, str, str], target: tuple[float, float],
                    bend: int, end_angle: float | None = None, effective: bool = False) -> dict[str, float]:
        """Return a copy of (effective) params where chain[0..1] are rotated so chain[2]'s pivot
        lands on `target` (root space, clamped to reach). `bend` = sign of cross(target-root,
        mid-root): side-view legs with the knee forward use bend=-1, elbows forward bend=+1.
        `end_angle`: optional world angle (degrees) for chain[2] (e.g. 0 = foot flat)."""
        spec = {p["name"]: p for p in self.views[view]["parts"]}
        q = dict(params) if effective else self.effective_params(view, params)
        a, b, c = (spec[n] for n in chain)
        xf = {px.name: px.m for px in self.solve(view, q, raw=True)}
        parent_m = xf[a["parent"]] if a["parent"] != "root" else np.eye(3)
        P = np.array(mx.apply(xf[a["name"]], 0, 0))
        T = np.array(target, dtype=float)
        jb, jc = np.array(b["joint"], float), np.array(c["joint"], float)
        L1, L2 = float(np.hypot(*jb)), float(np.hypot(*jc))
        off1 = math.degrees(math.atan2(jb[1], jb[0])) - 90.0
        off2 = math.degrees(math.atan2(jc[1], jc[0])) - 90.0
        v = T - P
        d = float(np.hypot(*v))
        d = min(max(d, abs(L1 - L2) + 1e-3), L1 + L2 - 1e-3)
        phi0 = math.atan2(v[1], v[0])
        alpha = math.acos(max(-1.0, min(1.0, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d))))
        best = None
        for phi1 in (phi0 + alpha, phi0 - alpha):
            K = P + L1 * np.array([math.cos(phi1), math.sin(phi1)])
            cross = v[0] * (K - P)[1] - v[1] * (K - P)[0]
            if best is None or (math.copysign(1, cross) == math.copysign(1, bend)):
                best = (phi1, K)
                if math.copysign(1, cross) == math.copysign(1, bend):
                    break
        phi1, K = best
        Tc = P + d * np.array([math.cos(phi0), math.sin(phi0)])
        th_parent = self._world_angle(parent_m)
        th1 = math.degrees(phi1) - 90.0 - off1
        th2 = math.degrees(math.atan2(Tc[1] - K[1], Tc[0] - K[0])) - 90.0 - off2

        def wrap(x):
            return (x + 180.0) % 360.0 - 180.0
        q[a["param"]] = wrap(th1 - th_parent - float(a.get("rest", 0.0)))
        q[b["param"]] = wrap(th2 - th1 - float(b.get("rest", 0.0)))
        if end_angle is not None and c.get("param"):
            q[c["param"]] = wrap(end_angle - th2 - float(c.get("rest", 0.0)))
        return q

    def joint_positions(self, view: str, params: dict[str, float], raw: bool = False) -> dict[str, tuple[float, float]]:
        """Pivot position (root space, rig units) of every part (raw=True: pure FK, no drivers/limits)."""
        return {px.name: mx.apply(px.m, 0, 0) for px in self.solve(view, params, raw=raw)}

    def draw(self, dst: Image.Image, view: str, params: dict[str, float], expression: str, root_to_px: np.ndarray,
             include_shadow: bool = True, hands: dict[str, str] | None = None, z_override: dict[str, float] | None = None,
             raw: bool = False):
        """Draw the posed character. `root_to_px` maps root-space rig units to destination pixels."""
        for px in self.solve(view, params, expression, hands=hands, z_override=z_override, raw=raw):
            if not px.sprite:
                continue
            if px.sprite == "shadow" and not include_shadow:
                continue
            spr = self.sprite(px.sprite)
            m = root_to_px @ px.m @ np.linalg.inv(spr.local_to_px)
            draw_affine(dst, spr, m)


# ------------------------------------------------------------ procedural cycles
def walk_cycle(phase: float, amp: float = 1.0) -> dict[str, float]:
    """Side-view walk (facing +x). `phase` in radians, one step per pi. Returns additive params."""
    s, c = math.sin(phase), math.cos(phase)
    hip = 26.0 * amp
    knee = 34.0 * amp
    arm = 22.0 * amp
    p = {
        "hip_l": -hip * s, "hip_r": hip * s,
        "knee_l": knee * max(0.0, c) ** 1.2 + 4 * amp, "knee_r": knee * max(0.0, -c) ** 1.2 + 4 * amp,
        "shoulder_l": arm * s, "shoulder_r": -arm * s,
        "elbow_l": -12 * amp - 8 * amp * max(0.0, -s), "elbow_r": -12 * amp - 8 * amp * max(0.0, s),
        "torso": -3.0 * amp, "head": 2.0 * amp,
        "hips_dy": 7.0 * amp * (0.5 - 0.5 * math.cos(2 * phase)),
    }
    p["ankle_l"] = -(p["hip_l"] + p["knee_l"]) * 0.8
    p["ankle_r"] = -(p["hip_r"] + p["knee_r"]) * 0.8
    return p
