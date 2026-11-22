"""Camera: per-frame transform from keyframes plus additive modifiers, and parallax projection.

World units: at zoom 1 the frame shows `frame_world_width` (default 1920) world units across.
Layers are 2D planes with a parallax factor p (1.0 = the character/action plane). Relative to a
reference camera (where the plates line up as painted), a layer with factor p sees the camera
displacement multiplied by p and the zoom raised to the power p:

    cam_p  = ref + (cam - ref) * p
    zoom_p = ref_zoom * (zoom / ref_zoom) ** p
    screen = C + R(-roll) * zoom_p * (world - cam_p)

So with p = 1.5 a foreground plane moves 1.5x faster than the action plane and with p = 0.15
the far background barely moves. Camera moves supported through keys and modifiers:

    tilt      vertical move of y between keys (2.5D tilt: layers shift at their own rates)
    pan       horizontal move of x between keys
    push/pull zoom keys (pull back = zoom decreasing)
    roll      `rot` keys (degrees)
    lens      uniform zoom of every layer (no parallax change), unlike `zoom` which is a dolly (layers scale by zoom**p)
    drift     modifier: smooth deterministic noise on x / y / rot
    shake     modifier: fast, enveloped shake with controllable intensity (impacts, handheld)
    track     modifier: follow the character root with exponential lag (axis x, y or xy)
    offset    transient screen-space offsets (used by the whip-pan transition)

A shot's camera can also be written as a preset (`{"preset": "push_in", "start": ..., "end": ...}`),
resolved by `camera/presets.py` into keys and modifiers. There is no yaw/pitch: high and low angles are
framings (position + zoom), not rotations of the view.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Callable

import numpy as np

from tools.render import mathx as mx


@dataclass(frozen=True)
class CameraState:
    x: float
    y: float
    zoom: float = 1.0
    rot: float = 0.0
    lens: float = 1.0

    def offset(self, dx: float = 0.0, dy: float = 0.0) -> "CameraState":
        return replace(self, x=self.x + dx, y=self.y + dy)


@dataclass(frozen=True)
class Reference:
    x: float = 0.0
    y: float = 0.0
    zoom: float = 1.0


class Camera:
    """Camera of one shot. `keys` times are in scene seconds."""

    def __init__(self, cfg: dict, target_fn: Callable[[float], tuple[float, float]] | None = None, fps: float = 24.0,
                 subject_height: float = 300.0):
        if "preset" in cfg and "keys" not in cfg:
            from .presets import resolve_preset
            cfg = resolve_preset(cfg, target_fn, subject_height)
        if "keys" not in cfg or not cfg["keys"]:
            raise ValueError("camera needs at least one key")
        self.cfg = cfg
        self.track = mx.Track(cfg["keys"], default_ease=cfg.get("ease", "inOutCubic"))
        self.modifiers = list(cfg.get("modifiers", []))
        self.target_fn = target_fn
        self.fps = fps
        self.t0 = float(min(k["t"] for k in cfg["keys"]))
        for m in self.modifiers:
            if m["type"] not in ("drift", "track", "shake"):
                raise ValueError(f"unknown camera modifier '{m['type']}'")
            if m["type"] == "track" and target_fn is None:
                raise ValueError("track modifier needs a target")

    def base(self, t: float) -> CameraState:
        return CameraState(
            x=float(self.track.value(t, "x", 0.0)),
            y=float(self.track.value(t, "y", 0.0)),
            zoom=float(self.track.value(t, "zoom", 1.0)),
            rot=float(self.track.value(t, "rot", 0.0)),
            lens=float(self.track.value(t, "lens", 1.0)),
        )

    def state(self, t: float) -> CameraState:
        st = self.base(t)
        x, y, zoom, rot, lens = st.x, st.y, st.zoom, st.rot, st.lens
        for m in self.modifiers:
            if m["type"] == "track":
                tx, ty = self._tracked_target(t, m)
                w = float(m.get("strength", 1.0))
                axis = m.get("axis", "x")
                ox, oy = m.get("offset", [0.0, 0.0])
                if "x" in axis:
                    x = x * (1 - w) + (tx + ox) * w
                if "y" in axis:
                    y = y * (1 - w) + (ty + oy) * w
            elif m["type"] == "drift":
                seed = int(m.get("seed", 1))
                f = float(m.get("freq", 0.25))
                x += float(m.get("amp_x", 0.0)) * mx.smooth_noise(t, seed, f)
                y += float(m.get("amp_y", 0.0)) * mx.smooth_noise(t, seed + 101, f)
                rot += float(m.get("amp_rot", 0.0)) * mx.smooth_noise(t, seed + 202, f)
                zoom *= 1.0 + float(m.get("amp_zoom", 0.0)) * mx.smooth_noise(t, seed + 303, f)
            elif m["type"] == "shake":
                k = shake_envelope(t, m)
                if k > 0.0:
                    seed = int(m.get("seed", 7))
                    f = float(m.get("freq", 9.0))
                    a = float(m.get("intensity", 1.0)) * k
                    x += float(m.get("amp_x", 14.0)) * a * mx.smooth_noise(t, seed, f)
                    y += float(m.get("amp_y", 10.0)) * a * mx.smooth_noise(t, seed + 101, f)
                    rot += float(m.get("amp_rot", 0.35)) * a * mx.smooth_noise(t, seed + 202, f)
        return CameraState(x, y, zoom, rot, lens)

    def _tracked_target(self, t: float, m: dict) -> tuple[float, float]:
        """Exponentially lagged target: d(c)/dt = (target - c) / lag, integrated from shot start."""
        lag = float(m.get("lag", 0.25))
        start = float(m.get("t0", self.t0))
        tx, ty = self.target_fn(start)
        if lag <= 0 or t <= start:
            return self.target_fn(t) if lag <= 0 else (tx, ty)
        dt = 1.0 / (self.fps * 4)
        n = int(math.ceil((t - start) / dt))
        dt = (t - start) / n
        k = 1.0 - math.exp(-dt / lag)
        for i in range(1, n + 1):
            gx, gy = self.target_fn(start + i * dt)
            tx += (gx - tx) * k
            ty += (gy - ty) * k
        return tx, ty


def shake_envelope(t: float, m: dict) -> float:
    """0..1 envelope of a shake modifier: `start`, `duration` (default: to the end of the shot), `attack`, `decay` (seconds).
    The decay uses a smooth tail so an impact dies away instead of stopping."""
    start = float(m.get("start", 0.0))
    if t < start:
        return 0.0
    attack = max(1e-6, float(m.get("attack", 0.02)))
    decay = max(1e-6, float(m.get("decay", 0.35)))
    dur = m.get("duration")
    up = min(1.0, (t - start) / attack)
    if dur is None:
        return up
    end = start + float(dur)
    if t >= end:
        return 0.0
    down = min(1.0, (end - t) / decay)
    return up * mx.ease("smoothstep", down)


def layer_matrix(cam: CameraState, parallax: float, ref: Reference, out_w: int, out_h: int, frame_world_width: float = 1920.0) -> np.ndarray:
    """3x3 matrix mapping world units on a plane with factor `parallax` to output pixels."""
    p = float(parallax)
    cx = ref.x + (cam.x - ref.x) * p
    cy = ref.y + (cam.y - ref.y) * p
    z = ref.zoom * (cam.zoom / ref.zoom) ** p * cam.lens
    px_per_world = out_w / frame_world_width
    return (mx.translate(out_w / 2.0, out_h / 2.0) @ mx.scale(px_per_world) @ mx.rotate_deg(-cam.rot)
            @ mx.scale(z) @ mx.translate(-cx, -cy))


def visible_world_rect(cam: CameraState, parallax: float, ref: Reference, out_w: int, out_h: int, frame_world_width: float = 1920.0) -> tuple[float, float, float, float]:
    """Axis-aligned world-space bounds of the viewport on a given plane."""
    inv = np.linalg.inv(layer_matrix(cam, parallax, ref, out_w, out_h, frame_world_width))
    pts = np.array([[0, 0, 1], [out_w, 0, 1], [0, out_h, 1], [out_w, out_h, 1]], dtype=float).T
    w = inv @ pts
    return float(w[0].min()), float(w[1].min()), float(w[0].max()), float(w[1].max())
