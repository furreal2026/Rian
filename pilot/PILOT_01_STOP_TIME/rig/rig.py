"""Modular cut-out rig with forward kinematics.

A rig is a JSON spec (see pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json). Each view lists
parts with: parent, joint (pivot position in the parent's local frame), rest angle, the pose
parameter that rotates it, sprite and draw order (z). The local frame of a part has its origin
at its pivot (the anatomical joint), so rotating a parameter rotates that part and all of its
children about the joint.

    world(part) = world(parent) @ T(joint + translate_params) @ R(rest + pose[param])
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
    def solve(self, view: str, params: dict[str, float], expression: str = "deadpan") -> list[PartXform]:
        if view not in self.views:
            raise KeyError(f"unknown view '{view}'. Known: {sorted(self.views)}")
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
            ang = float(p.get("rest", 0.0)) + (float(params.get(p["param"], 0.0)) if p.get("param") else 0.0)
            m = world[p["parent"]] @ mx.translate(jx, jy) @ mx.rotate_deg(ang)
            world[p["name"]] = m
            sprite = p.get("sprite")
            if sprite and sprite.startswith("head_"):
                sprite = f"{sprite}:{expression}"
            out.append(PartXform(p["name"], sprite, float(p["z"]), m))
        out.sort(key=lambda x: x.z)
        return out

    def joint_positions(self, view: str, params: dict[str, float]) -> dict[str, tuple[float, float]]:
        """Pivot position (root space, rig units) of every part."""
        return {px.name: mx.apply(px.m, 0, 0) for px in self.solve(view, params)}

    def draw(self, dst: Image.Image, view: str, params: dict[str, float], expression: str, root_to_px: np.ndarray, include_shadow: bool = True):
        """Draw the posed character. `root_to_px` maps root-space rig units to destination pixels."""
        for px in self.solve(view, params, expression):
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
