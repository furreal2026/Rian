"""Raster primitives: premultiplied mip-mapped images, affine blitting and a unit-space drawing canvas.

Coordinate convention: continuous pixel coordinates, pixel (i, j) covers [i, i+1) x [j, j+1).
Pillow's AFFINE transform samples at pixel centres with the same convention.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw

from . import mathx as mx


class MipImage:
    """An RGBA image stored premultiplied ('RGBa') with a 2x box-filtered mip chain.

    `origin` is the pixel coordinate (level 0) of the image's local (0, 0) point and
    `px_per_unit` how many level-0 pixels one local unit spans. `local_to_px` maps local
    units to level-0 pixel coordinates.
    """

    def __init__(self, img: Image.Image, origin: tuple[float, float] = (0.0, 0.0), px_per_unit: float = 1.0):
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        base = img.convert("RGBa")
        self.levels: list[Image.Image] = [base]
        while min(self.levels[-1].size) >= 16 and len(self.levels) < 8:
            prev = self.levels[-1]
            if prev.width < 2 or prev.height < 2:
                break
            self.levels.append(prev.reduce(2))
        self.origin = origin
        self.px_per_unit = px_per_unit
        self.size = img.size

    @property
    def local_to_px(self) -> np.ndarray:
        return mx.translate(*self.origin) @ mx.scale(self.px_per_unit)

    def level_for(self, magnification: float) -> int:
        """Pick the mip level whose texels are closest to (but not smaller than) one output pixel."""
        if magnification <= 0:
            return len(self.levels) - 1
        k = int(math.floor(math.log2(1.0 / magnification))) if magnification < 1 else 0
        return max(0, min(k, len(self.levels) - 1))


def draw_affine(dst: Image.Image, src: MipImage, m_px: np.ndarray, resample=Image.BICUBIC) -> tuple[int, int, int, int] | None:
    """Composite `src` onto RGBA image `dst` using matrix `m_px` (src level-0 px -> dst px).

    Only the destination bounding box of the transformed image is resampled. Returns the bbox
    drawn (x0, y0, x1, y1) or None if fully outside.
    """
    lin = m_px[:2, :2]
    mag = math.sqrt(abs(np.linalg.det(lin)))
    k = src.level_for(mag)
    lvl = src.levels[k]
    m = m_px @ mx.scale(2 ** k)  # level-k px -> dst px
    w, h = lvl.size
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], dtype=float).T
    pc = m @ corners
    x0 = max(0, int(math.floor(pc[0].min())) - 1)
    y0 = max(0, int(math.floor(pc[1].min())) - 1)
    x1 = min(dst.width, int(math.ceil(pc[0].max())) + 1)
    y1 = min(dst.height, int(math.ceil(pc[1].max())) + 1)
    if x1 <= x0 or y1 <= y0:
        return None
    inv = np.linalg.inv(mx.translate(-x0, -y0) @ m)
    data = (inv[0, 0], inv[0, 1], inv[0, 2], inv[1, 0], inv[1, 1], inv[1, 2])
    patch = lvl.transform((x1 - x0, y1 - y0), Image.AFFINE, data=data, resample=resample)
    dst.alpha_composite(patch.convert("RGBA"), (x0, y0))
    return (x0, y0, x1, y1)


class Canvas:
    """Supersampled drawing surface addressed in local units.

    bounds = (ux0, uy0, ux1, uy1) in units; drawing is done at px_per_unit * ss and reduced
    by `ss` (box filter, premultiplied) in `to_mip`. Transparent pixels carry `bleed` RGB so
    resampling never produces light halos around the dark ink.
    """

    def __init__(self, bounds: Sequence[float], px_per_unit: float, ss: int = 4, bleed=(29, 29, 33)):
        self.ux0, self.uy0, self.ux1, self.uy1 = bounds
        self.ppu = px_per_unit
        self.ss = ss
        self.k = px_per_unit * ss
        w = int(math.ceil((self.ux1 - self.ux0) * self.k / ss)) * ss
        h = int(math.ceil((self.uy1 - self.uy0) * self.k / ss)) * ss
        self.img = Image.new("RGBA", (max(ss, w), max(ss, h)), bleed + (0,))
        self.draw = ImageDraw.Draw(self.img)

    # unit -> supersampled px
    def p(self, x: float, y: float) -> tuple[float, float]:
        return ((x - self.ux0) * self.k, (y - self.uy0) * self.k)

    def s(self, v: float) -> float:
        return v * self.k

    def new_layer(self) -> "Canvas":
        c = Canvas.__new__(Canvas)
        c.__dict__.update(self.__dict__)
        c.img = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        c.draw = ImageDraw.Draw(c.img)
        return c

    def paste_layer(self, layer: "Canvas", mask: Image.Image | None = None):
        img = layer.img
        if mask is not None:
            a = np.asarray(img.getchannel("A"), dtype=np.uint16)
            m = np.asarray(mask, dtype=np.uint16)
            img = img.copy()
            img.putalpha(Image.fromarray((a * m // 255).astype(np.uint8)))
        self.img.alpha_composite(img)

    def mask_of(self) -> Image.Image:
        return self.img.getchannel("A")

    # primitives -----------------------------------------------------
    def circle(self, cx, cy, r, fill=None, outline=None, width=0.0):
        self.ellipse(cx, cy, r, r, fill, outline, width)

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, width=0.0):
        x0, y0 = self.p(cx - rx, cy - ry)
        x1, y1 = self.p(cx + rx, cy + ry)
        if fill is not None:
            self.draw.ellipse([x0, y0, x1, y1], fill=fill)
        if outline is not None and width > 0:
            self.draw.ellipse([x0, y0, x1, y1], outline=outline, width=max(1, int(round(self.s(width)))))

    def polygon(self, pts, fill=None):
        self.draw.polygon([self.p(x, y) for x, y in pts], fill=fill)

    def stroke(self, pts, width, color, round_caps=True, taper: Sequence[float] | None = None):
        """Polyline ink stroke. With `taper` (per-point width multipliers) it is drawn as a
        chain of round-capped segments of varying width."""
        if len(pts) < 2:
            return
        if taper is None:
            taper = [1.0] * len(pts)
        for (xa, ya), (xb, yb), ta, tb in zip(pts[:-1], pts[1:], taper[:-1], taper[1:]):
            self._capsule(xa, ya, xb, yb, width * ta, width * tb, color)
        if not round_caps:
            return

    def _capsule(self, xa, ya, xb, yb, wa, wb, color):
        ax, ay = self.p(xa, ya)
        bx, by = self.p(xb, yb)
        ra, rb = self.s(wa) / 2, self.s(wb) / 2
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L > 1e-6:
            nx, ny = -dy / L, dx / L
            self.draw.polygon([(ax + nx * ra, ay + ny * ra), (bx + nx * rb, by + ny * rb),
                               (bx - nx * rb, by - ny * rb), (ax - nx * ra, ay - ny * ra)], fill=color)
        self.draw.ellipse([ax - ra, ay - ra, ax + ra, ay + ra], fill=color)
        self.draw.ellipse([bx - rb, by - rb, bx + rb, by + rb], fill=color)

    def closed_stroke(self, pts, width, color):
        self.stroke(list(pts) + [pts[0]], width, color)

    def to_mip(self, origin_units=(0.0, 0.0)) -> MipImage:
        img = self.img.convert("RGBa").reduce(self.ss).convert("RGBA")
        ox = (origin_units[0] - self.ux0) * self.ppu
        oy = (origin_units[1] - self.uy0) * self.ppu
        return MipImage(img, origin=(ox, oy), px_per_unit=self.ppu)


def catmull_rom(points: Sequence[tuple[float, float]], samples: int = 8, closed: bool = False) -> list[tuple[float, float]]:
    """Smooth a polyline through `points` with a Catmull-Rom spline."""
    pts = list(points)
    if closed:
        pts = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(points[-1])
    return out
