"""Layered environment plates driven by a manifest JSON.

The manifest (e.g. pilot/PILOT_01_STOP_TIME/assets/environment/courtyard/manifest.json) lists each layer's file,
parallax factor, draw order and placement. Plates are *not* generated here: if a required file
is missing the environment refuses to load (MissingPlateError) unless an explicit test-plate
directory is supplied, in which case files with the same names are read from that directory.
The test directory is produced by `testassets.py` and is never the final environment.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from tools.render import mathx as mx
from ..camera.camera import CameraState, Reference, layer_matrix, visible_world_rect
from tools.render.raster import MipImage, draw_affine


class MissingPlateError(FileNotFoundError):
    pass


@dataclass
class Layer:
    id: str
    file: str
    parallax: float
    z: float
    role: str
    position: tuple[float, float]
    world_per_px: float
    required: bool
    image: MipImage | None = None
    source: str = "missing"  # final | test | missing

    def world_to_px(self) -> np.ndarray:
        """World units on this plane -> plate pixels."""
        return mx.scale(1.0 / self.world_per_px) @ mx.translate(-self.position[0], -self.position[1])

    def world_bounds(self) -> tuple[float, float, float, float] | None:
        if self.image is None:
            return None
        w, h = self.image.size
        x0, y0 = self.position
        return (x0, y0, x0 + w * self.world_per_px, y0 + h * self.world_per_px)


@dataclass
class Environment:
    name: str
    manifest_path: Path
    reference: Reference
    layers: list[Layer]
    character_z: float
    base_color: tuple[int, int, int]
    fx: dict[str, Path] = field(default_factory=dict)
    fx_source: dict[str, str] = field(default_factory=dict)
    ground_y: float = 0.0

    @classmethod
    def load(cls, manifest_path: str | Path, test_dir: str | Path | None = None, allow_missing: bool = False) -> "Environment":
        manifest_path = Path(manifest_path)
        m = json.loads(manifest_path.read_text(encoding="utf-8"))
        base = manifest_path.parent
        tdir = Path(test_dir) if test_dir else None
        wpp = float(m.get("world_units_per_pixel", 1.0))
        layers: list[Layer] = []
        missing: list[str] = []
        for L in m["layers"]:
            layer = Layer(
                id=L["id"], file=L["file"], parallax=float(L["parallax"]), z=float(L["z"]), role=L.get("role", ""),
                position=tuple(L.get("position", [0.0, 0.0])), world_per_px=float(L.get("world_units_per_pixel", wpp)),
                required=bool(L.get("required", True)),
            )
            final = base / L["file"]
            if final.exists():
                im = Image.open(final)
                if im.mode != "RGBA":
                    warnings.warn(f"{final.name}: mode {im.mode}, expected RGBA PNG (transparency needed for layering)")
                need = L.get("min_size_px")
                if need and (im.width < need[0] or im.height < need[1]):
                    warnings.warn(f"{final.name}: {im.width}x{im.height} px is smaller than the {need[0]}x{need[1]} px the camera "
                                  "moves need (run plate-spec); uncovered areas will be reported per frame")
                layer.image = MipImage(im)
                layer.source = "final"
            elif tdir is not None and (tdir / L["file"]).exists():
                layer.image = MipImage(Image.open(tdir / L["file"]))
                layer.source = "test"
                tm = tdir / "test_layout.json"
                if tm.exists():
                    lay = json.loads(tm.read_text(encoding="utf-8")).get(L["id"])
                    if lay:
                        layer.position = tuple(lay["position"])
                        layer.world_per_px = float(lay.get("world_units_per_pixel", layer.world_per_px))
            elif layer.required:
                missing.append(str(final))
            layers.append(layer)
        if missing and not allow_missing:
            raise MissingPlateError(
                "Courtyard plate(s) not available yet:\n  " + "\n  ".join(missing)
                + "\nAdd the approved plates (see the README next to the manifest) or render with --test-plates.")
        fx, fx_src = {}, {}
        for key, rel in m.get("fx", {}).items():
            p = base / rel
            if p.exists():
                fx[key], fx_src[key] = p, "final"
            elif tdir is not None and (tdir / Path(rel).name).exists():
                fx[key], fx_src[key] = tdir / Path(rel).name, "test"
            else:
                fx_src[key] = "missing"
        ref = m.get("reference_camera", {})
        return cls(
            name=m.get("name", manifest_path.stem), manifest_path=manifest_path,
            reference=Reference(float(ref.get("x", 0.0)), float(ref.get("y", 0.0)), float(ref.get("zoom", 1.0))),
            layers=sorted(layers, key=lambda l: l.z), character_z=float(m.get("character_z", 25)),
            base_color=tuple(m.get("base_color", [0, 0, 0])), fx=fx, fx_source=fx_src,
            ground_y=float(m.get("ground_y", 0.0)),
        )

    def layer_by_parallax(self, p: float) -> Layer:
        for l in self.layers:
            if abs(l.parallax - p) < 1e-9:
                return l
        raise KeyError(p)

    def draw_layer(self, dst: Image.Image, layer: Layer, cam: CameraState, frame_world_width: float = 1920.0):
        if layer.image is None:
            return
        m = layer_matrix(cam, layer.parallax, self.reference, dst.width, dst.height, frame_world_width) @ np.linalg.inv(layer.world_to_px())
        draw_affine(dst, layer.image, m, resample=Image.BILINEAR)

    def required_bounds(self, cams: list[CameraState], out_w: int, out_h: int, frame_world_width: float = 1920.0, margin: float = 64.0) -> dict[str, dict]:
        """For each layer, the world rectangle that must be painted to cover every camera in `cams`."""
        res = {}
        for l in self.layers:
            xs0, ys0, xs1, ys1 = [], [], [], []
            for c in cams:
                a, b, cc, d = visible_world_rect(c, l.parallax, self.reference, out_w, out_h, frame_world_width)
                xs0.append(a); ys0.append(b); xs1.append(cc); ys1.append(d)
            x0, y0, x1, y1 = min(xs0) - margin, min(ys0) - margin, max(xs1) + margin, max(ys1) + margin
            res[l.id] = {
                "parallax": l.parallax, "file": l.file,
                "world_rect": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                "min_size_px": [int(np.ceil((x1 - x0) / l.world_per_px)), int(np.ceil((y1 - y0) / l.world_per_px))],
                "position": [round(x0, 1), round(y0, 1)],
            }
        return res
