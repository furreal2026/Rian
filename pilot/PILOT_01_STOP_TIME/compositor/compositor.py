"""Scene loading and frame-by-frame compositing.

A scene config (JSON) defines output format, environment manifest, character animation on a
single scene timeline (so position/scale stay continuous across shots), shots with their camera,
and the transitions between consecutive shots. `Scene.render_frame(i)` returns an RGB uint8
array for frame i; layers are composited back-to-front with the character inserted at the
manifest's `character_z`.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from tools.render import mathx as mx
from dataclasses import replace as _replace
from ..camera.camera import Camera, CameraState, layer_matrix
from .environment import Environment
from ..rig.rig import Rig, walk_cycle
from ..transitions import transitions as tr


class ConfigError(ValueError):
    pass


# --------------------------------------------------------------- character
class CharacterTrack:
    def __init__(self, cfg: dict, rig: Rig):
        self.rig = rig
        self.height = float(cfg["height"])
        self.scale = self.height / rig.units_height
        keys = cfg["keys"]
        if not keys:
            raise ConfigError("character needs keys")
        plain, posed = [], []
        last_pose = None
        for k in keys:
            pk = {f: v for f, v in k.items() if f not in ("pose", "angles")}
            plain.append(pk)
            if "pose" in k or "angles" in k:
                pose = k.get("pose", last_pose)
                if pose is None:
                    raise ConfigError(f"character key at t={k['t']} sets angles before any pose")
                last_pose = pose
                ang = rig.pose_angles(pose)
                for p, v in k.get("angles", {}).items():
                    if p not in ang:
                        raise ConfigError(f"unknown rig param '{p}' at t={k['t']}")
                    ang[p] += float(v)
                d = {"t": k["t"]}
                if "ease" in k:
                    d["ease"] = k["ease"]
                d.update({f"a:{p}": v for p, v in ang.items()})
                posed.append(d)
        self.track = mx.Track(plain)
        self.pose_track = mx.Track(posed) if posed else None
        self.cycles = list(cfg.get("cycles", []))
        self.events = {e["name"]: float(e["t"]) for e in cfg.get("events", [])}
        self.shadow = bool(cfg.get("shadow", True))

    def root(self, t: float) -> tuple[float, float]:
        return float(self.track.value(t, "x", 0.0)), float(self.track.value(t, "y", 0.0))

    def state(self, t: float):
        x, y = self.root(t)
        view = self.track.value(t, "view", "front")
        expr = self.track.value(t, "expression", "deadpan")
        flip = bool(self.track.value(t, "flip", False))
        params = {p: 0.0 for p in self.rig.params}
        if self.pose_track:
            for p in self.rig.params:
                params[p] = float(self.pose_track.value(t, f"a:{p}", 0.0))
        for c in self.cycles:
            if c["type"] != "walk":
                raise ConfigError(f"unknown cycle '{c['type']}'")
            t0, t1, blend = float(c["t0"]), float(c["t1"]), float(c.get("blend", 0.15))
            if t0 - blend <= t <= t1 + blend:
                x0, _ = self.root(t0)
                dist = abs(x - x0) / self.scale
                phase = math.pi * dist / float(c.get("step_length", 190.0))
                wgt = min(1.0, max(0.0, (t - (t0 - blend)) / (2 * blend)), max(0.0, ((t1 + blend) - t) / (2 * blend)))
                wgt = mx.ease("inOutSine", wgt)
                for p, v in walk_cycle(phase, float(c.get("amp", 1.0))).items():
                    params[p] += v * wgt
        return x, y, view, expr, flip, params

    def root_matrix(self, t: float) -> np.ndarray:
        x, y, _, _, flip, _ = self.state(t)
        return mx.translate(x, y) @ mx.scale(-self.scale if flip else self.scale, self.scale)


# -------------------------------------------------------------------- scene
@dataclass
class Shot:
    id: str
    start: float
    end: float
    camera: Camera
    cfg: dict


class Scene:
    def __init__(self, config_path: str | Path, test_plates: str | Path | None = None, scale: float = 1.0,
                 allow_missing_plates: bool = False, px_per_unit: float | None = None):
        self.config_path = Path(config_path).resolve()
        self.cfg = json.loads(self.config_path.read_text(encoding="utf-8"))
        base = self.config_path.parent
        out = self.cfg["output"]
        self.fps = float(out["fps"])
        self.width = int(round(int(out["width"]) * scale))
        self.height = int(round(int(out["height"]) * scale))
        self.nominal_size = (int(out["width"]), int(out["height"]))
        self.duration = float(out["duration"])
        self.n_frames = int(round(self.duration * self.fps))
        self.frame_world_width = float(out.get("frame_world_width", out["width"]))
        self.env = Environment.load(base / self.cfg["environment"]["manifest"], test_dir=test_plates, allow_missing=allow_missing_plates)
        ch = self.cfg["character"]
        ppu = px_per_unit or float(ch.get("sprite_px_per_unit", 2.0))
        self.rig = Rig(base / ch["rig"], (base / ch["poses"]) if "poses" in ch else None, px_per_unit=ppu)
        self.character = CharacterTrack(ch, self.rig)
        self.shots: list[Shot] = []
        for s in self.cfg["shots"]:
            cam = Camera(s["camera"], target_fn=self._char_target(s["camera"]), fps=self.fps, subject_height=self.character.height)
            self.shots.append(Shot(s["id"], float(s["start"]), float(s["end"]), cam, s))
        self.shots.sort(key=lambda s: s.start)
        self.windows = self._build_transitions()
        self._leaf_cache: dict[str, tr.LeafWipe] = {}
        self.coverage_log: list[tuple[int, float]] = []

    def _char_target(self, cam_cfg):
        def fn(t):
            x, y = self.character.root(t)
            return x, y
        return fn

    def snap(self, t: float) -> float:
        return round(t * self.fps) / self.fps

    def _build_transitions(self) -> list[tr.Window]:
        ids = [s.id for s in self.shots]
        by_pair = {(t["from"], t["to"]): t for t in self.cfg.get("transitions", [])}
        for (a, b) in by_pair:
            if a not in ids or b not in ids or ids.index(b) != ids.index(a) + 1:
                raise ConfigError(f"transition {a}->{b} must join consecutive shots")
        if abs(self.shots[0].start) > 1e-9:
            raise ConfigError("first shot must start at 0")
        windows = []
        for a, b in zip(self.shots[:-1], self.shots[1:]):
            t = by_pair.get((a.id, b.id), {"type": "cut"})
            typ = t["type"]
            if typ not in tr.TYPES:
                raise ConfigError(f"unknown transition type '{typ}'")
            boundary = self.snap(b.start)
            if typ == "cut_on_action":
                ev = t["event"]
                if ev not in self.character.events:
                    raise ConfigError(f"cut_on_action {a.id}->{b.id}: unknown event '{ev}'")
                boundary = self.snap(self.character.events[ev] + float(t.get("offset", 0.0)))
            a.end = boundary
            b.start = boundary
            d = float(t.get("duration", 0.0)) if typ in tr.WINDOWED else 0.0
            if typ in tr.WINDOWED and d <= 0:
                raise ConfigError(f"{typ} {a.id}->{b.id} needs a positive duration")
            t_in, t_out = self.snap(boundary - d / 2), self.snap(boundary + d / 2)
            params = dict(t)
            if typ == "match_cut":
                params["match"] = self._check_match_cut(a, b, boundary, params)
            windows.append(tr.Window(typ, a.id, b.id, boundary, t_in, t_out, params))
        self.shots[-1].end = max(self.shots[-1].end, self.duration)
        return windows

    def subject_screen(self, shot: Shot, t: float) -> tuple[float, float, float]:
        """Screen position (px) of the character's centre and its height in px, for a shot's camera at time t."""
        cam = self.camera_at(shot, t)
        m = layer_matrix(cam, 1.0, self.env.reference, self.width, self.height, self.frame_world_width) @ self.character.root_matrix(t)
        uh = self.rig.units_height
        fx, fy = mx.apply(m, 0.0, 0.0)
        tx, ty = mx.apply(m, 0.0, -uh)
        return (fx + tx) / 2, (fy + ty) / 2, abs(fy - ty)

    def _check_match_cut(self, a: Shot, b: Shot, boundary: float, params: dict) -> dict:
        """A match cut must put the subject at the same place and size on both sides of the cut."""
        ta, tb = boundary - 1.0 / self.fps, boundary
        ax, ay, ah = self.subject_screen(a, ta)
        bx, by, bh = self.subject_screen(b, tb)
        pos = math.hypot(ax - bx, ay - by) / self.width
        ratio = max(ah, bh) / max(1e-9, min(ah, bh))
        tol_pos = float(params.get("tolerance_pos", 0.04))
        tol_scale = float(params.get("tolerance_scale", 1.15))
        res = {"pos_error_frac": round(pos, 4), "scale_ratio": round(ratio, 4), "tolerance_pos": tol_pos, "tolerance_scale": tol_scale}
        if pos > tol_pos or ratio > tol_scale:
            raise ConfigError(f"match_cut {a.id}->{b.id}: subject does not match across the cut ({res}). "
                              "Adjust the cameras so the subject has the same screen position and size, or use another transition.")
        return res

    def shot(self, sid: str) -> Shot:
        for s in self.shots:
            if s.id == sid:
                return s
        raise KeyError(sid)

    def shot_at(self, t: float) -> Shot:
        for s in self.shots:
            if s.start <= t < s.end:
                return s
        return self.shots[-1] if t >= self.shots[-1].start else self.shots[0]

    def window_at(self, t: float) -> tr.Window | None:
        for w in self.windows:
            if w.contains(t):
                return w
        return None

    # -------------------------------------------------------- rendering
    def camera_at(self, shot: Shot, t: float, dx: float = 0.0, zmul: float = 1.0) -> CameraState:
        cam = shot.camera.state(t).offset(dx, 0.0)
        if zmul != 1.0:
            cam = _replace(cam, zoom=cam.zoom * zmul)
        if shot.cfg.get("coverage") == "clamp":
            # clamp last, so transition offsets (whip pan dx, push-through dolly) also stay on painted plates
            cam, ok = self.env.clamp_camera(cam, self.width, self.height, self.frame_world_width, float(shot.cfg.get("clamp_margin", 0.0)))
            if not ok:
                self.coverage_log.append((shot.id, t))
        return cam

    def _dof_radius(self, shot: Shot, layer, cam: CameraState, t: float) -> float:
        """Gaussian blur radius (output px) for a layer from the shot's depth-of-field settings (0 = sharp)."""
        d = shot.cfg.get("dof")
        if not d:
            return 0.0
        strength = float(d.get("strength", 8.0))
        if d.get("keys"):
            strength = float(mx.Track(d["keys"]).value(t, "strength", strength))
        focus = float(d.get("focus", 1.0))
        r = strength * abs(layer.parallax - focus) * math.sqrt(max(1e-6, cam.zoom * cam.lens)) * self.width / 1920.0
        return min(r, float(d.get("max", 30.0)) * self.width / 1920.0)

    def render_shot(self, shot: Shot, t: float, dx: float = 0.0, zmul: float = 1.0) -> Image.Image:
        """Render one shot at scene time t (camera x offset dx, dolly multiplier zmul). Returns RGBA (alpha = plate coverage)."""
        cam = self.camera_at(shot, t, dx, zmul)
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        drawn_char = False
        for layer in self.env.layers:
            if not drawn_char and layer.z > self.env.character_z:
                self._draw_character(img, cam, t)
                drawn_char = True
            r = self._dof_radius(shot, layer, cam, t)
            if r >= 0.5 and layer.image is not None:
                tmp = Image.new("RGBA", img.size, (0, 0, 0, 0))
                self.env.draw_layer(tmp, layer, cam, self.frame_world_width)
                img.alpha_composite(tr.blur_rgba(tmp, r))
            else:
                self.env.draw_layer(img, layer, cam, self.frame_world_width)
        if not drawn_char:
            self._draw_character(img, cam, t)
        return img

    def _draw_character(self, img: Image.Image, cam: CameraState, t: float):
        _, _, view, expr, _, params = self.character.state(t)
        m = layer_matrix(cam, 1.0, self.env.reference, self.width, self.height, self.frame_world_width) @ self.character.root_matrix(t)
        self.rig.draw(img, view, params, expr, m, include_shadow=self.character.shadow)

    def _flatten(self, img: Image.Image) -> np.ndarray:
        base = Image.new("RGBA", img.size, tuple(self.env.base_color) + (255,))
        base.alpha_composite(img)
        return np.asarray(base.convert("RGB"))

    def frame_time(self, i: int) -> float:
        return i / self.fps

    def render_frame_rgba(self, i: int) -> tuple[Image.Image, dict]:
        t = self.frame_time(i)
        w = self.window_at(t)
        info = {"frame": i, "t": round(t, 4), "transition": None}
        if w is None or w.type in ("cut", "cut_on_action", "match_cut"):
            s = self.shot_at(t)
            info["shot"] = s.id
            return self.render_shot(s, t), info
        info["transition"] = w.type
        if w.type == "whip_pan":
            samples = int(w.params.get("samples", 7))
            shutter = float(w.params.get("shutter", 0.75))
            times = tr.whip_sample_times(t, self.fps, samples, shutter)
            px_per_world = self.width / self.frame_world_width
            plan = []
            for ts in times:
                sid, _ = tr.whip_offset(w, ts, 1.0)
                shot = self.shot(sid)
                zoom = shot.camera.state(ts).zoom
                sid, dx = tr.whip_offset(w, ts, zoom)
                plan.append((ts, shot, dx, dx * zoom * px_per_world))
            acc = None
            names = set()
            for k, (ts, shot, dx, sx) in enumerate(plan):
                names.add(shot.id)
                # screen-space gap to the neighbouring samples -> streak length that fills it
                gaps = [abs(sx - plan[j][3]) for j in (k - 1, k + 1) if 0 <= j < len(plan) and plan[j][1] is shot]
                streak = int(min(max(gaps) if gaps else 0.0, self.width * 0.6))
                arr = np.asarray(self.render_shot(shot, ts, dx).convert("RGBa"), dtype=np.float32)
                arr = tr.box_blur_x(arr, streak)
                acc = arr if acc is None else acc + arr
            acc /= len(plan)
            info["shot"] = "+".join(sorted(names))
            out = Image.fromarray(np.clip(acc + 0.5, 0, 255).astype(np.uint8), "RGBa").convert("RGBA")
            return out, info
        if w.type == "blur":
            sid, radius, zmul = tr.blur_state(w, t, self.width)
            info["shot"] = sid
            info["blur_radius_px"] = round(radius, 2)
            return tr.blur_rgba(self.render_shot(self.shot(sid), t, 0.0, zmul), radius), info
        if w.type == "push_through":
            samples = int(w.params.get("samples", 7))
            shutter = float(w.params.get("shutter", 0.75))
            acc, names = None, set()
            for ts in tr.whip_sample_times(t, self.fps, samples, shutter):
                sid, zmul = tr.push_offset(w, ts)
                names.add(sid)
                arr = np.asarray(self.render_shot(self.shot(sid), ts, 0.0, zmul).convert("RGBa"), dtype=np.float32)
                acc = arr if acc is None else acc + arr
            acc /= samples
            info["shot"] = "+".join(sorted(names))
            return Image.fromarray(np.clip(acc + 0.5, 0, 255).astype(np.uint8), "RGBa").convert("RGBA"), info
        if w.type in ("leaf_wipe", "foreground_wipe"):
            leaf = self._leaf(w)
            u = (t - w.t_in) / (w.t_out - w.t_in)
            a = self.render_shot(self.shot(w.from_shot), t)
            b = self.render_shot(self.shot(w.to_shot), t)
            matte = leaf.matte(u)
            out = Image.composite(b, a, matte)
            leaf.draw_leaf(out, u)
            info["shot"] = f"{w.from_shot}>{w.to_shot}"
            info["matte_coverage"] = float(np.asarray(matte, dtype=np.float32).mean() / 255.0)
            return out, info
        raise ConfigError(w.type)

    def _leaf(self, w: tr.Window) -> tr.LeafWipe:
        key = w.params.get("asset", "leaf_wipe")
        if key not in self._leaf_cache:
            if key not in self.env.fx:
                raise ConfigError(
                    f"leaf_wipe needs fx asset '{key}' (manifest fx entry) which is {self.env.fx_source.get(key, 'not declared')}. "
                    "Provide the approved leaf PNG or render with --test-plates.")
            self._leaf_cache[key] = tr.LeafWipe(self.env.fx[key], self.width, self.height, w.params)
        return self._leaf_cache[key]

    def render_frame(self, i: int) -> np.ndarray:
        img, _ = self.render_frame_rgba(i)
        return self._flatten(img)

    def coverage(self, img: Image.Image) -> float:
        """Fraction of pixels fully covered by plates/character (1.0 = no holes)."""
        a = np.asarray(img.getchannel("A"))
        return float((a >= 250).mean())

    # ------------------------------------------------------- reporting
    def timeline(self) -> list[dict]:
        rows = []
        for s in self.shots:
            rows.append({"shot": s.id, "start": round(s.start, 4), "end": round(s.end, 4),
                         "first_frame": int(round(s.start * self.fps)), "last_frame": int(round(s.end * self.fps)) - 1,
                         "frames": int(round(s.end * self.fps)) - int(round(s.start * self.fps)),
                         "framing": s.cfg.get("framing", ""), "camera_move": s.cfg.get("camera_move", "")})
        return rows

    def all_cameras(self) -> list[CameraState]:
        """Every camera state used by the render (including whip-pan offsets), for plate coverage."""
        cams = []
        for i in range(self.n_frames):
            t = self.frame_time(i)
            w = self.window_at(t)
            if w is not None and w.type == "whip_pan":
                for ts in tr.whip_sample_times(t, self.fps, int(w.params.get("samples", 7)), float(w.params.get("shutter", 0.75))):
                    sid, _ = tr.whip_offset(w, ts, 1.0)
                    shot = self.shot(sid)
                    sid, dx = tr.whip_offset(w, ts, shot.camera.state(ts).zoom)
                    cams.append(self.camera_at(shot, ts, dx))
            elif w is not None and w.type == "push_through":
                for ts in tr.whip_sample_times(t, self.fps, int(w.params.get("samples", 7)), float(w.params.get("shutter", 0.75))):
                    sid, zmul = tr.push_offset(w, ts)
                    cams.append(self.camera_at(self.shot(sid), ts, 0.0, zmul))
            elif w is not None and w.type == "blur":
                sid, _, zmul = tr.blur_state(w, t, self.width)
                cams.append(self.camera_at(self.shot(sid), t, 0.0, zmul))
            elif w is not None and w.type in ("leaf_wipe", "foreground_wipe"):
                cams.append(self.camera_at(self.shot(w.from_shot), t))
                cams.append(self.camera_at(self.shot(w.to_shot), t))
            else:
                cams.append(self.camera_at(self.shot_at(t), t))
        return cams
