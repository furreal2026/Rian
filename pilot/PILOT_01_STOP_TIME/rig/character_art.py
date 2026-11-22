"""Procedural sprite art for the stick_figure rig parts.

Every sprite is drawn in *rig units* (head radius = 100) with the part's pivot at local (0, 0),
supersampled, and returned as a MipImage whose origin is the pivot. Shapes, proportions and
colours follow the master character draft V2 (MASTER_CHARACTER.md). Approved PNG parts can
replace any sprite through the rig's parts override directory (see rig.py).
"""
from __future__ import annotations

import math

from PIL import ImageColor

from tools.render.raster import Canvas, MipImage, catmull_rom


def _rgba(hex_color: str, a: int = 255) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(hex_color)[:3]
    return (r, g, b, a)


class StickFigureArt:
    def __init__(self, spec: dict, px_per_unit: float = 2.0, ss: int = 4):
        self.pal = spec["palette"]
        self.lw = spec["line_widths"]
        self.expr = spec["expressions"]
        self.ppu = px_per_unit
        self.ss = ss
        self.ink = _rgba(self.pal["ink"])
        self.skin = _rgba(self.pal["skin"])

    # ------------------------------------------------------------ helpers
    def _canvas(self, bounds, bleed=None) -> Canvas:
        bleed = bleed or self.ink[:3]
        return Canvas(bounds, self.ppu, self.ss, bleed=bleed)

    def make(self, sprite: str) -> MipImage:
        name, _, variant = sprite.partition(":")
        fn = getattr(self, f"_sprite_{name}", None)
        if fn is None:
            raise KeyError(f"no procedural art for sprite '{sprite}'")
        return fn(variant) if variant or name.startswith("head_") else fn()

    # ------------------------------------------------------------- parts
    def _sprite_shadow(self):
        c = self._canvas((-110, -16, 110, 20), bleed=(0, 0, 0))
        c.ellipse(0, 2, 92, 11, fill=_rgba(self.pal["shadow"], 34))
        c.ellipse(0, 2, 64, 7, fill=_rgba(self.pal["shadow"], 22))
        return c.to_mip()

    def _limb(self, length, taper=(1.0, 0.94)):
        w = self.lw["limb"]
        c = self._canvas((-8, -8, 8, length + 8))
        c.stroke([(0, 0), (0.6, length * 0.5), (0, length)], w, self.ink, taper=[taper[0], (taper[0] + taper[1]) / 2, taper[1]])
        return c.to_mip()

    def _sprite_leg_thigh(self):
        return self._limb(107, (1.05, 1.0))

    def _sprite_leg_shin(self):
        return self._limb(104, (1.0, 0.92))

    def _sprite_forearm(self):
        return self._limb(64, (0.98, 0.92))

    def _foot(self, direction: int):
        c = self._canvas((-28, -10, 28, 12))
        d = direction
        c.stroke([(0, -1), (d * 7, 2.6), (d * 15, 3.6), (d * 19, 3.0)], 7.5, self.ink, taper=[0.9, 1.2, 1.1, 0.8])
        return c.to_mip()

    def _sprite_foot_front_r(self):
        return self._foot(-1)

    def _sprite_foot_front_l(self):
        return self._foot(1)

    def _sprite_foot_side(self):
        return self._foot(1)

    def _sprite_hand(self):
        c = self._canvas((-18, -8, 18, 30))
        c.circle(0, 11, 11.5, fill=self.skin)
        pts = [(0 + 11.5 * math.cos(a), 11 + 11.5 * math.sin(a)) for a in [i * 2 * math.pi / 40 for i in range(40)]]
        tap = [0.85 + 0.35 * max(0.0, math.cos(i * 2 * math.pi / 40 - math.pi / 4)) for i in range(40)]
        c.stroke(pts + [pts[0]], 4.8, self.ink, taper=tap + [tap[0]])
        return c.to_mip()

    def _sprite_upper_arm(self):
        w = self.lw["limb"]
        c = self._canvas((-26, -26, 26, 74))
        c.stroke([(0, 0), (0.5, 32), (0, 64)], w, self.ink, taper=[1.0, 1.0, 0.98])
        # short sleeve, belongs to the arm so it follows shoulder rotation
        sleeve = catmull_rom([(-14, -18), (0, -21), (14, -18), (17, 6), (19, 30), (0, 32), (-19, 30), (-17, 6)], 6, closed=True)
        fill = c.new_layer()
        fill.polygon(sleeve, fill=_rgba(self.pal["shirt"]))
        mask = fill.mask_of()
        shade = c.new_layer()
        shade.polygon([(4, -30), (30, -30), (30, 40), (8, 40)], fill=_rgba(self.pal["shirt_shadow"]))
        fill.paste_layer(shade, mask)
        fold = c.new_layer()
        fold.stroke([(-8, 18), (-4, 26)], 2.2, _rgba(self.pal["shirt_fold"]))
        fill.paste_layer(fold, mask)
        c.paste_layer(fill)
        c.closed_stroke(sleeve, self.lw["shirt_outline"], self.ink)
        return c.to_mip()

    def _shirt(self, outline_pts, shade_poly, folds, collar, bounds):
        c = self._canvas(bounds)
        body = catmull_rom(outline_pts, 6, closed=True)
        fill = c.new_layer()
        fill.polygon(body, fill=_rgba(self.pal["shirt"]))
        mask = fill.mask_of()
        shade = c.new_layer()
        shade.polygon(shade_poly, fill=_rgba(self.pal["shirt_shadow"]))
        fill.paste_layer(shade, mask)
        fl = c.new_layer()
        for f in folds:
            fl.stroke(f, 2.4, _rgba(self.pal["shirt_fold"]), taper=[0.4] + [1.0] * (len(f) - 2) + [0.3])
        if collar:
            fl.stroke(catmull_rom(collar, 6), 4.0, _rgba(self.pal["shirt_fold"]))
        fill.paste_layer(fl, mask)
        c.paste_layer(fill)
        tap = [1.0 + 0.25 * max(0.0, (x / 60.0)) for x, _ in body]
        c.stroke(body + [body[0]], self.lw["shirt_outline"], self.ink, taper=tap + [tap[0]])
        return c.to_mip()

    def _sprite_torso_front(self):
        pts = [(-26, -149), (-12, -143), (0, -141), (12, -143), (26, -149), (46, -145), (57, -131), (58, -112),
               (52, -92), (50, -50), (53, -3), (0, 0), (-53, -3), (-50, -50), (-52, -92), (-58, -112), (-57, -131), (-46, -145)]
        shade = [(30, -160), (80, -160), (80, 10), (36, 10), (40, -60)]
        folds = [[(34, -20), (38, -10), (40, -2)], [(-30, -12), (-28, -4)], [(18, -74), (24, -60)]]
        collar = [(-22, -147), (-10, -138), (0, -136), (10, -138), (22, -147)]
        return self._shirt(pts, shade, folds, collar, (-72, -165, 72, 12))

    def _sprite_torso_side(self):
        pts = [(-14, -150), (6, -151), (22, -144), (30, -124), (30, -96), (28, -50), (31, -3), (0, 0),
               (-29, -3), (-27, -50), (-28, -100), (-27, -130)]
        shade = [(-40, -160), (-10, -160), (-14, 10), (-40, 10)]
        folds = [[(14, -24), (18, -6)], [(-12, -40), (-10, -24)]]
        return self._shirt(pts, shade, folds, None, (-45, -165, 45, 12))

    # -------------------------------------------------------------- heads
    def _head_outline(self, c: Canvas, cx, cy):
        n = 72
        pts = []
        taper = []
        for i in range(n):
            a = i * 2 * math.pi / n
            r = 100 * (1 + 0.012 * math.sin(2 * a + 0.4) - 0.01 * math.cos(3 * a)) + (2.0 if math.sin(a) < 0 else 0.0) * abs(math.sin(a)) * 0.6
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a) * 0.985))
            taper.append(0.82 + 0.38 * max(0.0, math.cos(a - math.pi / 4)))
        c.polygon(pts, fill=self.skin)
        return pts, taper

    def _eye(self, c: Canvas, ex, ey, rx, ry, e: dict, idx: int, inner_dir: int, head_cy: float = -100.0):
        lid = float(e["lid"])
        gx, gy = e["gaze"]
        pr = float(e["pupil"])
        layer = c.new_layer()
        layer.ellipse(ex, ey, rx, ry, fill=self.skin)
        mask = layer.mask_of()
        pupil = c.new_layer()
        px = ex + gx * (rx - pr * 0.9)
        py = ey + gy * (ry - pr * 0.6)
        pupil.circle(px, py, pr, fill=self.ink)
        pupil.circle(px - pr * 0.35, py - pr * 0.4, max(1.6, pr * 0.22), fill=self.skin)
        layer.paste_layer(pupil, mask)
        lid_y = ey - ry + 2 * ry * lid
        if lid > 0.02:
            cover = c.new_layer()
            cover.polygon([(ex - rx - 4, ey - ry - 4), (ex + rx + 4, ey - ry - 4), (ex + rx + 4, lid_y), (ex - rx - 4, lid_y)], fill=self.skin)
            layer.paste_layer(cover, mask)
        c.paste_layer(layer)
        # lower lid / eye outline
        lo = []
        for i in range(25):
            a = i * math.pi / 24
            x, y = ex + rx * math.cos(a), ey + ry * math.sin(a)
            lo.append((x, y))
        lo = [(x, y) for x, y in lo if y >= lid_y - 0.5]
        if len(lo) > 1:
            c.stroke(lo, self.lw["eye_outline"], self.ink, taper=[0.5] + [1.0] * (len(lo) - 2) + [0.5])
        # upper lid: thick, tapering, the character's signature
        if lid > 0.02:
            dy = lid_y - ey
            half = rx * math.sqrt(max(0.0, 1 - (dy / ry) ** 2))
            xa, xb = ex - half - 3, ex + half + 3
            sag = 2.5
            pts = [(xa, lid_y + 1.5), ((xa + ex) / 2, lid_y - sag * 0.4), (ex, lid_y - sag * 0.2), ((xb + ex) / 2, lid_y + 0.2), (xb, lid_y + 2.0)]
            c.stroke(pts, self.lw["lid"], self.ink, taper=[0.45, 0.95, 1.0, 0.9, 0.4])
        else:
            up = [(ex + rx * math.cos(a), ey - ry * math.sin(a)) for a in [i * math.pi / 24 for i in range(25)]]
            c.stroke(up, self.lw["eye_outline"] * 1.6, self.ink, taper=[0.5] + [1.0] * 23 + [0.5])
        if lid > 0.3:
            bag = [(ex - rx * 0.6, ey + ry + 5), (ex, ey + ry + 7.5), (ex + rx * 0.6, ey + ry + 5)]
            c.stroke(bag, 2.4, _rgba(self.pal["eye_bag"]), taper=[0.2, 1.0, 0.2])
        # brow
        by = head_cy + e["brow_y"] - e["brow_raise"][idx]
        tilt = e["brow_tilt"][idx]
        inner_x = ex + inner_dir * rx * 0.8
        outer_x = ex - inner_dir * rx * 1.0
        pts = [(inner_x, by + tilt), (ex, by - 2.5), (outer_x, by - tilt * 0.3 + 1)]
        c.stroke(catmull_rom(pts, 5), self.lw["brow"], self.ink, taper=[0.75] * 3 + [1.0] * 5 + [0.95] * 2 + [0.55] * 1)

    def _mouth(self, c: Canvas, mx_, my, kind: str, scale_x: float = 1.0):
        w = self.lw["mouth"]
        if kind == "line":
            c.stroke([(mx_ - 9 * scale_x, my), (mx_, my + 0.8), (mx_ + 9 * scale_x, my - 0.4)], w, self.ink, taper=[0.5, 1.0, 0.5])
        elif kind == "line_tilt":
            c.stroke([(mx_ - 9 * scale_x, my + 2), (mx_ + 9 * scale_x, my - 2.5)], w, self.ink, taper=[0.5, 0.6])
        elif kind == "open":
            c.ellipse(mx_, my + 3, 10 * scale_x, 13, fill=_rgba(self.pal["mouth"]))
            c.ellipse(mx_, my + 3, 10 * scale_x, 13, outline=self.ink, width=w)
        elif kind == "smirk":
            c.stroke(catmull_rom([(mx_ - 10 * scale_x, my), (mx_, my + 1.5), (mx_ + 9 * scale_x, my - 2), (mx_ + 13 * scale_x, my - 5)], 5), w, self.ink,
                     taper=[0.4] + [1.0] * 14 + [0.4])
        else:
            raise ValueError(f"unknown mouth '{kind}'")

    def _sprite_head_front(self, variant: str = "deadpan"):
        e = self.expr[variant or "deadpan"]
        c = self._canvas((-112, -212, 112, 12))
        cx, cy = 0, -100
        pts, tap = self._head_outline(c, cx, cy)
        self._eye(c, cx - 38, cy - 6, 27, 17, e, 0, inner_dir=1)
        self._eye(c, cx + 38, cy - 6, 27, 17, e, 1, inner_dir=-1)
        self._mouth(c, cx + 1, cy + 52, e["mouth"])
        c.stroke(pts + [pts[0]], self.lw["head_outline"], self.ink, taper=tap + [tap[0]])
        return c.to_mip()

    def _sprite_head_side(self, variant: str = "deadpan"):
        e = dict(self.expr[variant or "deadpan"])
        e["gaze"] = [max(0.35, e["gaze"][0] + 0.4), e["gaze"][1]]
        c = self._canvas((-112, -212, 112, 12))
        cx, cy = 0, -100
        pts, tap = self._head_outline(c, cx, cy)
        self._eye(c, cx + 60, cy - 6, 14, 17, e, 1, inner_dir=-1)
        self._mouth(c, cx + 76, cy + 52, e["mouth"], scale_x=0.55)
        c.stroke(pts + [pts[0]], self.lw["head_outline"], self.ink, taper=tap + [tap[0]])
        return c.to_mip()
