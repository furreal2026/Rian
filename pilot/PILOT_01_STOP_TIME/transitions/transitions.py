"""Shot transitions with real per-frame animation.

cut_on_action  Hard cut placed exactly on a character action event (e.g. the finger snap).
               The cut frame is the event frame, so the action starts in shot A and its
               continuation is seen in shot B (character animation runs on scene time).
whip_pan       Outgoing camera accelerates sideways, incoming camera decelerates from the
               opposite side. Each frame is the average of several sub-frame renders across
               the shutter (true camera motion blur, including per-layer parallax).
leaf_wipe      Object wipe: a leaf sprite flies across the frame. Everything the leaf has
               swept over reveals shot B (union of the leaf's alpha along its path); the leaf
               is drawn on top. Needs the leaf asset (manifest fx 'leaf_wipe').
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageChops

from tools.render import mathx as mx
from tools.render.raster import MipImage, draw_affine

TYPES = ("cut", "cut_on_action", "whip_pan", "leaf_wipe")


@dataclass
class Window:
    type: str
    from_shot: str
    to_shot: str
    boundary: float
    t_in: float
    t_out: float
    params: dict = field(default_factory=dict)

    def contains(self, t: float) -> bool:
        return self.t_in <= t < self.t_out


# ----------------------------------------------------------------- whip pan
def whip_offset(w: Window, t: float, zoom: float) -> tuple[str, float]:
    """Which shot is visible at time t and the camera x offset (world units) to apply."""
    dist = float(w.params.get("distance", 2200.0)) / max(zoom, 1e-6)
    sign = -1.0 if w.params.get("direction", "right") == "left" else 1.0
    half_in = w.boundary - w.t_in
    half_out = w.t_out - w.boundary
    if t < w.boundary:
        u = 0.0 if half_in <= 0 else (t - w.t_in) / half_in
        return w.from_shot, sign * dist * mx.ease("inCubic", u)
    v = 1.0 if half_out <= 0 else (t - w.boundary) / half_out
    return w.to_shot, -sign * dist * (1.0 - mx.ease("outCubic", v))


def whip_sample_times(t: float, fps: float, samples: int, shutter: float) -> list[float]:
    if samples <= 1:
        return [t]
    span = shutter / fps
    return [t + (i / (samples - 1) - 0.5) * span for i in range(samples)]


def box_blur_x(arr: np.ndarray, k: int) -> np.ndarray:
    """Horizontal box blur (premultiplied float HxWxC) with an odd-or-even kernel of k pixels."""
    if k <= 1:
        return arr
    pad_l, pad_r = k // 2, k - 1 - k // 2
    padded = np.pad(arr, ((0, 0), (pad_l + 1, pad_r), (0, 0)), mode="edge")
    c = np.cumsum(padded, axis=1, dtype=np.float32)
    return (c[:, k:, :] - c[:, :-k, :]) / k


# ---------------------------------------------------------------- leaf wipe
class LeafWipe:
    def __init__(self, leaf_png, out_w: int, out_h: int, params: dict):
        img = Image.open(leaf_png).convert("RGBA")
        self.leaf = MipImage(img, origin=(img.width / 2, img.height / 2), px_per_unit=1.0)
        self.w, self.h = out_w, out_h
        self.p = params
        self.direction = params.get("direction", "right_to_left")
        self.length_frac = float(params.get("length_frac", 2.3))  # leaf long axis vs frame height
        self.arc = float(params.get("arc_frac", 0.12))
        self.rot = params.get("rotation", [-78, -102])  # degrees over the move
        self.long_axis_px = max(img.width, img.height)

    def leaf_matrix(self, u: float, scale_out: float = 1.0) -> np.ndarray:
        e = mx.ease(self.p.get("ease", "inOutSine"), u)
        s = self.length_frac * self.h / self.long_axis_px
        reach = self.w / 2 + self.length_frac * self.h * 0.45
        x = self.w / 2 + reach * (1 - 2 * e) * (1 if self.direction == "right_to_left" else -1)
        y = self.h / 2 - self.arc * self.h * math.sin(math.pi * e)
        rot = self.rot[0] + (self.rot[1] - self.rot[0]) * e
        return mx.scale(scale_out) @ mx.translate(x, y) @ mx.rotate_deg(rot) @ mx.scale(s) @ np.linalg.inv(self.leaf.local_to_px)

    def matte(self, u: float, substeps: int = 48, matte_scale: float = 0.25) -> Image.Image:
        """Union of leaf alpha for progress 0..u, as an 'L' image at full output size."""
        mw, mh = max(1, int(self.w * matte_scale)), max(1, int(self.h * matte_scale))
        acc = Image.new("L", (mw, mh), 0)
        n = max(1, int(math.ceil(substeps * u)))
        for i in range(n + 1):
            ui = u * i / n
            tmp = Image.new("RGBA", (mw, mh), (0, 0, 0, 0))
            draw_affine(tmp, self.leaf, self.leaf_matrix(ui, matte_scale))
            acc = ImageChops.lighter(acc, tmp.getchannel("A"))
        # leaf body is opaque; threshold soft edges so the reveal is a clean wipe
        acc = acc.point(lambda v: 255 if v > 96 else int(v * 255 / 96))
        return acc.resize((self.w, self.h), Image.BILINEAR)

    def draw_leaf(self, dst: Image.Image, u: float):
        draw_affine(dst, self.leaf, self.leaf_matrix(u, dst.width / self.w))
