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
    _masks: dict = field(default_factory=dict, repr=False)

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

    # ------------------------------------------------------------ coverage
    def painted_bounds(self, layer: Layer) -> tuple[float, float, float, float] | None:
        """World rectangle where a layer actually has paint (bounding box of its non-transparent pixels), cached.

        The plates are delivered on a larger transparent canvas than the area that was painted, so the canvas
        (`Layer.world_bounds`) says nothing about what can be shown without a hole.
        """
        if layer.image is None:
            return None
        if layer.id not in self._masks:
            a = layer.image.levels[1].split()[-1] if len(layer.image.levels) > 1 else layer.image.levels[0].split()[-1]
            scale = layer.image.size[0] / a.size[0]
            bb = a.point(lambda v: 255 if v >= 8 else 0).getbbox()
            if bb is None:
                self._masks[layer.id] = None
            else:
                x0, y0, x1, y1 = (bb[0] * scale, bb[1] * scale, bb[2] * scale, bb[3] * scale)
                self._masks[layer.id] = (layer.position[0] + x0 * layer.world_per_px, layer.position[1] + y0 * layer.world_per_px,
                                         layer.position[0] + x1 * layer.world_per_px, layer.position[1] + y1 * layer.world_per_px)
        return self._masks[layer.id]

    def _camera_limits(self, cam: CameraState, out_w: int, out_h: int, frame_world_width: float, inset: float = -1.5):
        """Allowed camera-centre range (x0, x1, y0, y1) so every background/action-plane layer shows only painted area.

        Returns (limits, feasible). `inset` < 0 tolerates that many world units of edge bleed (plate edges are anti-aliased).
        Layers with parallax above 1 are foreground decoration and are ignored.
        """
        ref = self.reference
        ppw = out_w / frame_world_width
        r = np.radians(cam.rot)
        lo_x, hi_x, lo_y, hi_y = -np.inf, np.inf, -np.inf, np.inf
        feasible = True
        for l in self.layers:
            b = self.painted_bounds(l)
            p = l.parallax
            if b is None or p <= 1e-9 or p > 1.0 + 1e-9:
                continue
            z = ref.zoom * (cam.zoom / ref.zoom) ** p * cam.lens
            hw, hh = out_w / 2 / (ppw * z), out_h / 2 / (ppw * z)
            ehw = hw * abs(np.cos(r)) + hh * abs(np.sin(r)) + inset
            ehh = hh * abs(np.cos(r)) + hw * abs(np.sin(r)) + inset
            for axis, (c0, c1, e, ref_c) in enumerate(((b[0], b[2], ehw, ref.x), (b[1], b[3], ehh, ref.y))):
                lo_c, hi_c = c0 + e, c1 - e
                if lo_c > hi_c:
                    feasible = False
                    lo_c = hi_c = (c0 + c1) / 2
                lo_cam, hi_cam = ref_c + (lo_c - ref_c) / p, ref_c + (hi_c - ref_c) / p
                if axis == 0:
                    lo_x, hi_x = max(lo_x, lo_cam), min(hi_x, hi_cam)
                else:
                    lo_y, hi_y = max(lo_y, lo_cam), min(hi_y, hi_cam)
        if lo_x > hi_x:
            feasible, lo_x, hi_x = False, (lo_x + hi_x) / 2, (lo_x + hi_x) / 2
        if lo_y > hi_y:
            feasible, lo_y, hi_y = False, (lo_y + hi_y) / 2, (lo_y + hi_y) / 2
        return (lo_x, hi_x, lo_y, hi_y), feasible

    def view_painted(self, cam: CameraState, out_w: int, out_h: int, frame_world_width: float = 1920.0) -> bool:
        """True when the view at this camera shows only painted area on every background/action-plane layer."""
        (lo_x, hi_x, lo_y, hi_y), feasible = self._camera_limits(cam, out_w, out_h, frame_world_width)
        return feasible and lo_x - 1e-6 <= cam.x <= hi_x + 1e-6 and lo_y - 1e-6 <= cam.y <= hi_y + 1e-6

    def clamp_camera(self, cam: CameraState, out_w: int, out_h: int, frame_world_width: float = 1920.0, margin: float = 0.0) -> tuple[CameraState, bool]:
        """Move the camera centre the least amount needed so the view shows only painted area.

        Returns (camera, feasible). Infeasible means no centre works at this zoom/lens/roll (the painted area is
        smaller than the view): the camera is centred and the caller should zoom in or supply larger plates.
        Missing plates: no-op.
        `margin` (world units, default 0) keeps the view that far inside the painted edge, away from the soft alpha rim.
        """
        if not any(l.image is not None for l in self.layers):
            return cam, True
        (lo_x, hi_x, lo_y, hi_y), feasible = self._camera_limits(cam, out_w, out_h, frame_world_width, inset=-1.5 + float(margin))
        x = float(np.clip(cam.x, lo_x, hi_x)) if np.isfinite(lo_x) else cam.x
        y = float(np.clip(cam.y, lo_y, hi_y)) if np.isfinite(lo_y) else cam.y
        return CameraState(x, y, cam.zoom, cam.rot, cam.lens), feasible

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
