"""Procedural sprite art for the stick_figure rig parts.

Every sprite is drawn in *rig units* (head radius = 100) with the part's pivot at local (0, 0),
supersampled, and returned as a MipImage whose origin is the pivot. Shapes, proportions and
colours follow the master character draft V2 (MASTER_CHARACTER.md). Approved PNG parts can
replace any sprite through the rig's parts override directory (see rig.py).
"""
from __future__ import annotations

import math

from PIL import ImageColor, ImageFilter

from tools.render.raster import Canvas, MipImage, catmull_rom


def _rgba(hex_color: str, a: int = 255) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(hex_color)[:3]
    return (r, g, b, a)


class StickFigureArt:
    def __init__(self, spec: dict, px_per_unit: float = 2.0, ss: int = 4):
        self.pal = spec["palette"]
        self.lw = spec["line_widths"]
        self.spec = spec
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

    # Limbs v3: thicker solid ink with round caps. A segment's end width equals the next
    # segment's start width, and every segment ends in a round cap centred on the joint pivot,
    # so joints stay closed (no gaps or kinks) at any rotation.
    def _limb(self, length, w0, w1, bow=0.6):
        c = self._canvas((-10, -10, 10, length + 10))
        c.stroke([(0, 0), (bow, length * 0.5), (0, length)], 1.0, self.ink, taper=[w0, (w0 + w1) / 2, w1])
        return c.to_mip()

    def _arm_w(self):
        return float(self.lw.get("arm", self.lw.get("limb", 6.6)))

    def _leg_w(self):
        return float(self.lw.get("leg", self.lw.get("limb", 6.6)))

    def _sprite_leg_thigh(self):
        w = self._leg_w()
        return self._limb(107, w * 1.04, w * 0.98)

    def _sprite_leg_shin(self):
        w = self._leg_w()
        return self._limb(104, w * 0.98, w * 0.86)

    def _sprite_forearm(self):
        w = self._arm_w()
        return self._limb(64, w * 0.96, w * 0.86)

    def _foot(self, direction: int):
        c = self._canvas((-32, -12, 32, 14))
        d = direction
        w = float(self.lw.get("foot", 7.5))
        ankle = self._leg_w() * 0.86
        c.stroke([(0, -1), (d * 7, 3.0), (d * 15, 4.2), (d * 21, 3.6)], 1.0, self.ink, taper=[ankle, w * 1.08, w * 1.02, w * 0.84])
        return c.to_mip()

    def _sprite_foot_front_r(self):
        return self._foot(-1)

    def _sprite_foot_front_l(self):
        return self._foot(1)

    def _sprite_foot_side(self):
        return self._foot(1)

    HAND_R = 14.0

    def _sprite_hand(self, variant: str = "open"):
        variant = variant or "open"
        R = self.HAND_R
        cy = R - 1.0
        ow = float(self.lw.get("hand_outline", 4.8))
        c = self._canvas((-22, -10, 22, 46))
        # wrist stub: closes the joint between the forearm cap and the hand ring
        c.stroke([(0, 0), (0, 3)], 1.0, self.ink, taper=[self._arm_w() * 0.86, self._arm_w() * 0.8])
        if variant == "point":
            # index finger along the hand axis (local +y), same ink/skin language as the hand
            c.stroke([(0, cy), (0.8, cy + R + 10)], 7.0 + ow, self.ink)
        c.circle(0, cy, R + ow / 2, fill=self.ink)
        if variant == "point":
            c.stroke([(0, cy), (0.8, cy + R + 10)], 7.0 - 0.2, self.skin)
        c.circle(0, cy, R - ow / 2, fill=self.skin)
        if variant == "grip":
            # closed fingers: a short curved crease across the palm
            pts = [(-R * 0.55, cy + 1.5), (-R * 0.15, cy + 4.5), (R * 0.3, cy + 4.0), (R * 0.6, cy + 1.0)]
            c.stroke(catmull_rom(pts, 6), 3.0, self.ink, taper=[0.6] + [1.0] * 17 + [0.6])
        return c.to_mip()

    def _sprite_upper_arm(self):
        w = self._arm_w()
        c = self._canvas((-26, -26, 26, 74))
        c.stroke([(0, -6), (0, 0), (0.5, 32), (0, 64)], 1.0, self.ink, taper=[w * 1.02, w * 1.02, w, w * 0.96])
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

    # Shoulder caps: the shirt's shoulder region, drawn on the clavicle part so it rises with
    # the shoulder. At rest it is pixel-identical to the torso underneath; the inner edge sits
    # at the clavicle pivot so the seam does not open when it rotates.
    _CAP_ZONE_R = [(-12, -170), (-90, -170), (-90, -92), (-44, -92), (-12, -126)]

    def _shoulder_cap(self, pts, shade, collar, zone, pivot, bounds, lift_only=False):
        px_, py_ = pivot
        L = lambda q: [(x - px_, y - py_) for x, y in q]
        c = self._canvas(bounds)
        full = c.new_layer()
        body = catmull_rom(L(pts), 6, closed=True)
        fill = full.new_layer()
        fill.polygon(body, fill=_rgba(self.pal["shirt"]))
        bmask = fill.mask_of()
        sh = full.new_layer()
        sh.polygon(L(shade), fill=_rgba(self.pal["shirt_shadow"]))
        fill.paste_layer(sh, bmask)
        if collar:
            fl = full.new_layer()
            fl.stroke(catmull_rom(L(collar), 6), 4.0, _rgba(self.pal["shirt_fold"]))
            fill.paste_layer(fl, bmask)
        full.paste_layer(fill)
        tap = [1.0 + 0.25 * max(0.0, ((x + px_) / 60.0)) for x, _ in body]
        full.stroke(body + [body[0]], self.lw["shirt_outline"], self.ink, taper=tap + [tap[0]])
        zl = c.new_layer()
        zl.polygon(L(zone), fill=(255, 255, 255, 255))
        # feathered seam (~4 units): resampling differences and the lift spread over a soft edge
        soft = zl.mask_of().filter(ImageFilter.GaussianBlur(4.0 * self.ppu * self.ss))
        c.paste_layer(full, soft)
        return c.to_mip()

    def _sprite_shoulder_cap_r(self):
        return self._shoulder_cap(self.TORSO_FRONT, self.TORSO_FRONT_SHADE, self.TORSO_FRONT_COLLAR, self._CAP_ZONE_R,
                                  (-16, -136), (-80, -40, 10, 50))

    def _sprite_shoulder_cap_l(self):
        zone = [(-x, y) for x, y in self._CAP_ZONE_R]
        return self._shoulder_cap(self.TORSO_FRONT, self.TORSO_FRONT_SHADE, self.TORSO_FRONT_COLLAR, zone,
                                  (16, -136), (-10, -40, 80, 50))

    def _sprite_shoulder_cap_side(self):
        zone = [(-40, -170), (44, -170), (44, -116), (-40, -116)]
        return self._shoulder_cap(self.TORSO_SIDE, self.TORSO_SIDE_SHADE, None, zone, (0, -136), (-45, -40, 45, 25))

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

    TORSO_FRONT = [(-26, -149), (-12, -143), (0, -141), (12, -143), (26, -149), (46, -145), (57, -131), (58, -112),
                   (52, -92), (50, -50), (53, -3), (0, 0), (-53, -3), (-50, -50), (-52, -92), (-58, -112), (-57, -131), (-46, -145)]
    TORSO_FRONT_SHADE = [(30, -160), (80, -160), (80, 10), (36, 10), (40, -60)]
    TORSO_FRONT_COLLAR = [(-22, -147), (-10, -138), (0, -136), (10, -138), (22, -147)]
    TORSO_SIDE = [(-14, -150), (6, -151), (22, -144), (30, -124), (30, -96), (28, -50), (31, -3), (0, 0),
                  (-29, -3), (-27, -50), (-28, -100), (-27, -130)]
    TORSO_SIDE_SHADE = [(-40, -160), (-10, -160), (-14, 10), (-40, 10)]

    def _sprite_torso_front(self):
        folds = [[(34, -20), (38, -10), (40, -2)], [(-30, -12), (-28, -4)], [(18, -74), (24, -60)]]
        return self._shirt(self.TORSO_FRONT, self.TORSO_FRONT_SHADE, folds, self.TORSO_FRONT_COLLAR, (-72, -165, 72, 12))

    def _sprite_torso_side(self):
        folds = [[(14, -24), (18, -6)], [(-12, -40), (-10, -24)]]
        return self._shirt(self.TORSO_SIDE, self.TORSO_SIDE_SHADE, folds, None, (-45, -165, 45, 12))

    # -------------------------------------------------------------- heads
    # Face design v2 (owner-approved expression sheet, output/character_revision_v2_TEST/):
    # clean tapered ink, heavy upper lid over ~half the eye, pupil tucked under the lid, a
    # thinner brow just above the lid, short mouth line. All face geometry is in head-centred
    # units (head radius 100); the head sprite pivot stays at the neck joint, with a short
    # visible neck between the joint and the head (spec face.neck).
    def _face(self) -> dict:
        return self.spec.get("face", {})

    def _ink(self, c: Canvas, pts, w0, wm, w1, color=None, smooth=True, power=0.55):
        poly, a, b = tapered_outline(pts, w0, wm, w1, smooth=smooth, power=power)
        col = color or self.ink
        c.polygon(poly, fill=col)
        c.circle(a[0], a[1], w0 / 2, fill=col)
        c.circle(b[0], b[1], w1 / 2, fill=col)

    def _expr(self, variant: str) -> dict:
        name = variant or "deadpan"
        name = self.spec.get("expression_aliases", {}).get(name, name)
        if name not in self.expr:
            raise KeyError(f"unknown expression '{variant}'. Known: {sorted(self.expr)}")
        return self.expr[name]

    def _eye(self, c: Canvas, ex, ey, inner, idx, e: dict):
        """inner: x direction (+1/-1) of the eye's inner corner (towards the nose)."""
        fc = self._face()
        lw = self.lw
        pick = lambda k, d=None: (e[k][idx] if isinstance(e.get(k), (list, tuple)) else e.get(k, d))
        rx = pick("rx", fc.get("eye_rx", 29.0))
        ry = pick("ry", fc.get("eye_ry", 22.0))
        ex, ey = ex + e.get("dx", 0.0), ey + e.get("dy", 0.0)
        lid_in, lid_out = pick("lid_in"), pick("lid_out")
        open_eye = lid_in is None
        gx, gy = e.get("gaze", (0.0, 0.0))
        pr = e.get("pupil", fc.get("pupil", 12.5))
        arch = pick("lid_arch", 2.2)

        def lid_y(x):
            u = (x - ex) / rx * inner
            top = ey - ry
            yin, yout = top + 2 * ry * lid_in, top + 2 * ry * lid_out
            return yout + (yin - yout) * (u + 1) / 2 - arch * (1 - u * u)

        layer = c.new_layer()
        layer.ellipse(ex, ey, rx, ry, fill=self.skin)
        mask = layer.mask_of()
        pupil = c.new_layer()
        px = ex + gx * (rx - pr - 2.5)
        py = ey + gy * (ry - pr - 1.5)
        pupil.circle(px, py, pr, fill=self.ink)
        pupil.circle(px - pr * 0.36, py - pr * 0.4, max(1.7, pr * 0.24), fill=self.skin)
        layer.paste_layer(pupil, mask)
        if not open_eye:
            xs = [ex - rx - 2 + k * (2 * rx + 4) / 40 for k in range(41)]
            cover = c.new_layer()
            cover.polygon([(x, lid_y(x)) for x in xs] + [(ex + rx + 4, ey - ry - 6), (ex - rx - 4, ey - ry - 6)], fill=self.skin)
            layer.paste_layer(cover, mask)
        c.paste_layer(layer)

        if open_eye:
            ring = [(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in [k * 2 * math.pi / 72 for k in range(73)]]
            c.stroke(ring, lw["eye_outline_open"], self.ink)
            top = [(ex + rx * math.cos(a), ey - ry * math.sin(a)) for a in [math.pi * (0.12 + 0.76 * k / 20) for k in range(21)]]
            self._ink(c, top, lw["eye_outline_open"], lw["eye_outline_open"] * 1.57, lw["eye_outline_open"], smooth=False)
            lid_top = ey - ry
        else:
            # walk the ellipse starting at its top so the visible lower arc is one ordered run
            arc = [(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in [-math.pi / 2 + k * 2 * math.pi / 240 for k in range(241)]]
            arc = [p for p in arc if p[1] >= lid_y(p[0]) - 0.3 and p[1] >= ey - ry * 0.98]
            if len(arc) > 2:
                w = lw["eye_outline"]
                self._ink(c, arc, w * 0.68, w, w * 0.68, smooth=False, power=0.3)

            def edge(sgn):
                lo, hi = 0.0, rx * 1.2
                for _ in range(40):
                    m = (lo + hi) / 2
                    x = ex + sgn * m
                    inside = ((x - ex) / rx) ** 2 + ((lid_y(x) - ey) / ry) ** 2 <= 1
                    lo, hi = (m, hi) if inside else (lo, m)
                return ex + sgn * lo
            x_out, x_in = edge(-inner), edge(inner)
            x0 = x_out - inner * pick("lid_ext", 2.5)
            x1 = x_in + inner * 1.0
            pts = [(x0 + (x1 - x0) * k / 8, lid_y(x_out + (x_in - x_out) * k / 8)) for k in range(9)]
            pts[0] = (pts[0][0], pts[0][1] - pick("flick", 0.0))
            self._ink(c, pts, 4.6, pick("lid_w", lw["lid"]), 5.0, power=0.35)
            lid_top = min(lid_y(ex + inner * rx * 0.7), lid_y(ex - inner * rx * 0.7), lid_y(ex))

        if e.get("brow", True) is not False:
            by = lid_top - pick("brow_dy", 13.0)
            tin, tout, barch = pick("brow_in", 0.0), pick("brow_out", 0.0), pick("brow_arch", 3.0)
            xin, xout = ex + inner * rx * 0.72, ex - inner * rx * 0.95
            bpts = [(xin, by - tin), ((xin + ex) / 2, by - tin * 0.5 - barch * 0.8),
                    (ex - inner * rx * 0.2, by - (tin + tout) * 0.5 - barch), (xout, by - tout + 1.5)]
            self._ink(c, bpts, pick("brow_w0", lw["brow"] * 0.74), pick("brow_w", lw["brow"]), lw["brow"] * 0.5, power=0.4)
        if e.get("bags"):
            bag = _rgba(self.pal["eye_bag"])
            self._ink(c, [(ex - rx * 0.75, ey + ry + 5), (ex, ey + ry + 8.5), (ex + rx * 0.75, ey + ry + 5)], 0.8, 3.2, 0.8, color=bag)
            self._ink(c, [(ex - rx * 0.45, ey + ry + 11), (ex, ey + ry + 13), (ex + rx * 0.45, ey + ry + 11)], 0.6, 2.2, 0.6, color=bag)

    # mouth shapes in mouth-local units, drawn scaled (1.3, 1.15) about the mouth centre
    _MOUTH_LINES = {
        "line": [(-9, 0), (0, 0.6), (9, -0.2)],
        "line_tilt": [(-10, 1.6), (0, 0), (9, -2.2)],
        "frown_small": [(-10, 2.2), (0, -0.8), (10, 2.2)],
        "flat_low": [(-11, 1.5), (-2, 0.4), (9, 2.0)],
        "squiggle": [(-11, 1), (-5, -1.5), (1, 1.5), (7, -1.2), (11, 0.5)],
        "smirk": [(-10, 0.4), (-1, 2.0), (8, -0.6), (13, -4.6)],
        "worried": [(-11, 2.4), (-5, -0.6), (1, 0.6), (6, -0.6), (11, 2.4)],
        "disgust": [(-12, 3.5), (-6, -0.5), (1, 1.2), (7, -0.4), (12, 3.6)],
    }

    def _mouth(self, c: Canvas, mx_, my, kind: str, scale_x: float = 1.0):
        sx, sy = 1.3 * scale_x, 1.15
        k = math.sqrt(1.3 * 1.15)
        P = lambda pts: [(mx_ + x * sx, my + y * sy) for x, y in pts]
        w = self.lw["mouth"] * k
        if kind in self._MOUTH_LINES:
            end1 = 2.2 if kind in ("line", "line_tilt") else (2.4 if kind == "disgust" else (2.2 if kind == "smirk" else 2.0))
            self._ink(c, P(self._MOUTH_LINES[kind]), 2.0 * k, w, end1 * k)
            return
        if kind == "open":
            shape = [(9.5 * math.cos(a) * (1 - 0.08 * math.sin(a)), 3 + 12.5 * math.sin(a)) for a in [i * 2 * math.pi / 60 for i in range(60)]]
            inner = lambda L: L.ellipse(mx_, my + 13 * sy, 8 * sx, 5.5 * sy, fill=_rgba(self.pal["tongue"]))
            ow = 4.0 * k
        elif kind == "grimace":
            shape = catmull_rom([(-14, -3), (0, -4), (14, -3)], 10)[:-1] + catmull_rom([(14, -3), (12, 6), (0, 7.5), (-12, 6), (-14, -3)], 10)[:-1]
            inner = lambda L: L.polygon(P([(-16, -6), (16, -6), (16, 0), (-16, 0)]), fill=self.skin)
            ow = 3.6 * k
        else:
            raise ValueError(f"unknown mouth '{kind}'")
        pts = P(shape)
        layer = c.new_layer()
        layer.polygon(pts, fill=_rgba(self.pal["mouth"]))
        mask = layer.mask_of()
        inn = c.new_layer()
        inner(inn)
        layer.paste_layer(inn, mask)
        c.paste_layer(layer)
        c.closed_stroke(pts, ow, self.ink)

    def _mark(self, c: Canvas, cx, cy, mark):
        if mark == "?":
            ang = math.radians(12)
            R = lambda pts: [(cx + 100 + x * math.cos(ang) - y * math.sin(ang), cy - 128 + x * math.sin(ang) + y * math.cos(ang)) for x, y in pts]
            hook = catmull_rom([(-11, -10), (-6, -19), (4, -21), (12, -14), (11, -5), (3, 1), (0, 8), (0, 13)], 8)
            self._ink(c, R(hook), 8.0, 9.0, 8.0, smooth=False, power=0.2)
            d = R([(0, 25)])[0]
            c.circle(d[0], d[1], 5.4, fill=self.ink)
        elif mark == "!!":
            ang = math.radians(14)
            R = lambda pts: [(cx + 86 + x * math.cos(ang) - y * math.sin(ang), cy - 150 + x * math.sin(ang) + y * math.cos(ang)) for x, y in pts]
            for ox in (0, 18):
                self._ink(c, R([(ox, 0), (ox - 2, 28)]), 9, 8, 5)
                d = R([(ox - 3, 42)])[0]
                c.circle(d[0], d[1], 5, fill=self.ink)

    def _head_canvas(self):
        c = self._canvas((-122, -282, 140, 16))
        neck = float(self._face().get("neck", 0.0))
        cy = -100.0 - neck
        if neck > 0:
            self._ink(c, [(0, 6), (0, -neck * 0.5), (0, -neck - 8)], self.lw["neck"], self.lw["neck"], self.lw["neck"])
        c.circle(0, cy, 100, fill=self.skin)
        return c, 0.0, cy

    def _head_finish(self, c, cx, cy, e):
        ring = [(cx + 100 * math.cos(a), cy + 100 * math.sin(a)) for a in [i * 2 * math.pi / 144 for i in range(145)]]
        c.stroke(ring, self.lw["head_outline"], self.ink)
        if e.get("mark"):
            self._mark(c, cx, cy, e["mark"])
        return c.to_mip()

    def _sprite_head_front(self, variant: str = "deadpan"):
        e = self._expr(variant)
        fc = self._face()
        c, cx, cy = self._head_canvas()
        ex, ey = fc.get("eye_x", 40.0), cy + fc.get("eye_y", -10.0)
        self._eye(c, cx - ex, ey, +1, 0, e)
        self._eye(c, cx + ex, ey, -1, 1, e)
        self._mouth(c, cx + 1, cy + fc.get("mouth_y", 46.0), e["mouth"])
        return self._head_finish(c, cx, cy, e)

    def _sprite_head_side(self, variant: str = "deadpan"):
        e = dict(self._expr(variant))
        fc = self._face()
        e["gaze"] = [max(0.35, e["gaze"][0] + 0.4), e["gaze"][1]]
        e["rx"] = fc.get("side_eye_rx", 15.0)
        c, cx, cy = self._head_canvas()
        self._eye(c, cx + 62, cy + fc.get("eye_y", -10.0), +1, 1, e)
        self._mouth(c, cx + 70, cy + fc.get("mouth_y", 46.0), e["mouth"], scale_x=0.55)
        return self._head_finish(c, cx, cy, e)


def tapered_outline(pts, w0, wm, w1, smooth=True, power=0.55):
    """Outline polygon of a tapered ink stroke along `pts` (thin ends, full width mid-stroke).
    Returns (polygon, first_point, last_point); the ends get round caps of w0/2 and w1/2."""
    s = catmull_rom(pts, 12) if smooth and len(pts) > 2 else list(pts)
    d = [0.0]
    for a, b in zip(s, s[1:]):
        d.append(d[-1] + math.dist(a, b))
    L = d[-1] or 1.0
    left, right = [], []
    for i, (x, y) in enumerate(s):
        t = d[i] / L
        a = s[max(0, i - 1)]
        b = s[min(len(s) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        n = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / n, tx / n
        base = w0 + (w1 - w0) * t
        w = base + (wm - base) * math.sin(math.pi * t) ** power
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    return left + right[::-1], s[0], s[-1]
