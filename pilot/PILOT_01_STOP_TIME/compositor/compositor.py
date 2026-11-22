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
from ..camera.camera import Camera, CameraState, layer_matrix
from .environment import Environment
from ..rig.rig import Rig, walk_cycle
from ..rig import locomotion as loco
from ..transitions import transitions as tr


class ConfigError(ValueError):
    pass


# --------------------------------------------------------------- character
LEG_PARAMS = ("hip_{s}", "knee_{s}", "ankle_{s}")
ARM_PARAMS = ("shoulder_{s}", "elbow_{s}", "wrist_{s}")
# follow-through / overlap: (source, target, gain). The target gets gain * (spring(source) - source),
# i.e. it lags when the source starts moving and swings past when it stops.
DEFAULT_SECONDARY = [("shoulder_r", "elbow_r", 0.35), ("shoulder_l", "elbow_l", 0.35),
                     ("elbow_r", "wrist_r", 0.30), ("elbow_l", "wrist_l", 0.30),
                     ("torso", "head", 0.45), ("hips", "torso", 0.20)]


class CharacterTrack:
    """Character animation on the scene timeline.

    Key fields: t, x, y, view, flip, expression, pose, angles, ease, plus (v3 rig)
    - hand_r / hand_l: hand shape ("open", "point", "grip"), held until the next key;
    - z: {"hand_r": 45, ...} draw-order override (held), e.g. a hand in front of the face;
    - plant: 0..1 weight of planted-feet IK. The ankles stay where they were in world space when the
      planted interval started (last key with plant 0), so moving the hips or the whole pose (weight
      shift, squat, sit -> stand, landing) keeps the feet on the floor. feet: {"l": [x, y], ...}
      overrides the target in root space;
    - reach: {"r": [x, y, w], "l": [x, y, w, bend]} arm IK target + weight (+ optional elbow bend).
    Cycles: {"type": "walk" | "run" | "walk_legacy", "t0", "t1", "blend", "step_length", "amp",
    "arms": "swing" | "pose"} - walk/run lock planted feet to the floor (see rig/locomotion.py).
    `secondary`: true (default chains), false, or a list of [source, target, gain].
    """

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
            pk = {f: v for f, v in k.items() if f not in ("pose", "angles", "z", "feet", "reach")}
            for part, z in k.get("z", {}).items():
                pk[f"z:{part}"] = str(z)                     # strings hold until the next key
            for side, xy in k.get("feet", {}).items():
                pk[f"feet:{side}"] = [float(v) for v in xy]
            for side, r in k.get("reach", {}).items():
                r = [float(v) for v in r]
                pk[f"reach:{side}"] = r[:3] if len(r) >= 3 else r + [1.0]
                if len(r) >= 4:
                    pk[f"reach_bend:{side}"] = str(int(r[3]))
            if "ease" in k:
                pk["ease"] = k["ease"]
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
        for c in self.cycles:
            if c["type"] not in ("walk", "run", "walk_legacy"):
                raise ConfigError(f"unknown cycle '{c['type']}'")
        self.events = {e["name"]: float(e["t"]) for e in cfg.get("events", [])}
        self.shadow = bool(cfg.get("shadow", True))
        sec = cfg.get("secondary", True)
        self.secondary = [tuple(s) for s in (DEFAULT_SECONDARY if sec is True else (sec or []))]
        self.sec_freq = float(cfg.get("secondary_hz", 2.2))
        self.sec_damp = float(cfg.get("secondary_damping", 0.42))
        self._kernel = self._spring_kernel()

    # ------------------------------------------------------------ helpers
    def root(self, t: float) -> tuple[float, float]:
        return float(self.track.value(t, "x", 0.0)), float(self.track.value(t, "y", 0.0))

    def _spring_kernel(self, dt: float = 1 / 96):
        """Discrete impulse response of a damped 2nd-order follower (sums to 1)."""
        w = 2 * math.pi * self.sec_freq
        z = self.sec_damp
        wd = w * math.sqrt(max(1e-6, 1 - z * z))
        n = int(math.ceil(5.0 / (z * w) / dt))
        h = [math.exp(-z * w * k * dt) * math.sin(wd * k * dt + 1e-9) for k in range(n)]
        s = sum(h)
        return dt, [v / s for v in h]

    def _cycle_weight(self, c, t):
        t0, t1, blend = float(c["t0"]), float(c["t1"]), float(c.get("blend", 0.15))
        if not (t0 - blend <= t <= t1 + blend):
            return 0.0
        wgt = min(1.0, max(0.0, (t - (t0 - blend)) / (2 * blend)), max(0.0, ((t1 + blend) - t) / (2 * blend)))
        return mx.ease("inOutSine", wgt)

    def _base(self, t: float) -> tuple[dict[str, float], list]:
        """Authored params at t: pose track + cycles (upper body). Returns (params, active cycles)."""
        params = {p: 0.0 for p in self.rig.params}
        if self.pose_track:
            for p in self.rig.params:
                params[p] = float(self.pose_track.value(t, f"a:{p}", 0.0))
        active = []
        x, _ = self.root(t)
        for c in self.cycles:
            wgt = self._cycle_weight(c, t)
            if wgt <= 0:
                continue
            x0, _ = self.root(float(c["t0"]))
            dist = abs(x - x0) / self.scale
            if c["type"] == "walk_legacy":
                phase = math.pi * dist / float(c.get("step_length", 190.0))
                for p, v in walk_cycle(phase, float(c.get("amp", 1.0))).items():
                    params[p] += v * wgt
                continue
            kind = c["type"]
            step = float(c.get("step_length", loco.GAITS[kind]["step"]))
            arms = c.get("arms", "swing") == "swing"
            g = loco.gait_raw(self.rig, kind, dist, params, step, arms=arms, amp=float(c.get("amp", 1.0)))
            keep = set() if arms else {f.format(s=s) for f in ARM_PARAMS for s in "lr"} | {"clavicle_l", "clavicle_r"}
            for p in self.rig.params:
                if p not in keep:
                    params[p] += (g[p] - params[p]) * wgt
            active.append((c, wgt, kind, dist, step))
        return params, active

    def _secondary_offsets(self, t: float) -> dict[str, float]:
        if not self.secondary:
            return {}
        dt, h = self._kernel
        srcs = sorted({s for s, _, _ in self.secondary})
        now = self._base(t)[0]
        follow = {s: 0.0 for s in srcs}
        for k, w in enumerate(h):
            past = self._base(t - k * dt)[0] if k else now
            for s in srcs:
                follow[s] += w * past[s]
        off: dict[str, float] = {}
        for s, tgt, gain in self.secondary:
            off[tgt] = off.get(tgt, 0.0) + float(gain) * (follow[s] - now[s])
        return off

    def _ik_chain(self, view, q, name, target, end_angle=None, bend=None):
        spec = self.rig.spec.get("ik", {}).get(view, {}).get(name)
        if not spec:
            raise ConfigError(f"no IK chain '{name}' for view '{view}'")
        return self.rig.ik_two_bone(view, q, tuple(spec["chain"]), target, bend=bend if bend is not None else spec["bend"],
                                    end_angle=end_angle, effective=True)

    # -------------------------------------------------------------- state
    def _plant_anchor(self, t: float) -> dict[str, tuple[float, float, float]]:
        """World ankle position + foot world angle per leg at the start of the current planted interval
        (the last 'plant' key at or before t whose value is 0, else the start of the track)."""
        ks = [k for k in self.track.keys if "plant" in k]
        t_s = self.track.keys[0]["t"]
        for k in ks:
            if k["t"] <= t and float(k["plant"]) <= 0.0:
                t_s = k["t"]
        cache = self.__dict__.setdefault("_anchor_cache", {})
        if t_s not in cache:
            st = self.pose_at(t_s, _no_plant=True)
            sx = -self.scale if st["flip"] else self.scale
            xf = {px.name: px.m for px in self.rig.solve(st["view"], st["params"], raw=True)}
            out = {}
            for s in "lr":
                ax, ay = mx.apply(xf[f"foot_{s}"], 0, 0)
                out[s] = (st["x"] + ax * sx, st["y"] + ay * self.scale, self.rig._world_angle(xf[f"foot_{s}"]))
            cache[t_s] = out
        return cache[t_s]

    def pose_at(self, t: float, _no_plant: bool = False) -> dict:
        """Everything needed to draw the character at t (params are *effective*: draw with raw=True)."""
        x, y = self.root(t)
        view = self.track.value(t, "view", "front")
        expr = self.track.value(t, "expression", "deadpan")
        flip = bool(self.track.value(t, "flip", False))
        params, active = self._base(t)
        for p, v in self._secondary_offsets(t).items():
            params[p] = params.get(p, 0.0) + v
        q = self.rig.effective_params(view, params)
        legs_done = set()
        # locomotion: legs from IK, blended with the pose by the cycle weight
        for c, wgt, kind, dist, step in active:
            tg = loco.leg_targets(kind, dist, step)
            solved = dict(q)
            for s in "lr":
                tx, ty, a = tg[s]
                solved = self._ik_chain("side", solved, f"leg_{s}", (tx, ty), end_angle=a)
            for s in "lr":
                for f in LEG_PARAMS:
                    p = f.format(s=s)
                    q[p] += (solved[p] - q[p]) * wgt
                legs_done.add(s)
        # planted feet: ankles stay where they were (in world space) when the plant started
        plant = float(self.track.value(t, "plant", 0.0)) if not _no_plant else 0.0
        if plant > 0 and len(legs_done) < 2:
            anchor = self._plant_anchor(t)
            solved = dict(q)
            for s in "lr":
                if s in legs_done:
                    continue
                tgt = self.track.value(t, f"feet:{s}", None)
                if tgt is None:
                    wx, wy, end = anchor[s]
                    sx = -self.scale if flip else self.scale
                    tgt = ((wx - x) / sx, (wy - y) / self.scale)
                else:
                    end = anchor[s][2]
                solved = self._ik_chain(view, solved, f"leg_{s}", tuple(tgt), end_angle=end)
                for f in LEG_PARAMS:
                    p = f.format(s=s)
                    q[p] += (solved[p] - q[p]) * plant
        # arm reach
        for s in "lr":
            r = self.track.value(t, f"reach:{s}", None)
            if r is None or float(r[2]) <= 0:
                continue
            bend = self.track.value(t, f"reach_bend:{s}", None)
            solved = self._ik_chain(view, dict(q), f"arm_{s}", (float(r[0]), float(r[1])),
                                    bend=int(bend) if bend is not None else None)
            w = min(1.0, float(r[2]))
            for f in ARM_PARAMS[:2]:
                p = f.format(s=s)
                q[p] += (solved[p] - q[p]) * w
        hands = {f"hand_{s}": self.track.value(t, f"hand_{s}", "open") for s in "lr"}
        z = {f[2:]: float(self.track.value(t, f, 0)) for f in self.track.fields() if f.startswith("z:")}
        return {"x": x, "y": y, "view": view, "expression": expr, "flip": flip, "params": q, "hands": hands, "z": z}

    def state(self, t: float):
        s = self.pose_at(t)
        return s["x"], s["y"], s["view"], s["expression"], s["flip"], s["params"]

    def root_matrix(self, t: float) -> np.ndarray:
        x, y = self.root(t)
        flip = bool(self.track.value(t, "flip", False))
        return mx.translate(x, y) @ mx.scale(-self.scale if flip else self.scale, self.scale)

    def draw(self, img, m_scene_to_px: np.ndarray, t: float, include_shadow: bool = True):
        s = self.pose_at(t)
        m = m_scene_to_px @ mx.translate(s["x"], s["y"]) @ mx.scale(-self.scale if s["flip"] else self.scale, self.scale)
        self.rig.draw(img, s["view"], s["params"], s["expression"], m, include_shadow=include_shadow,
                      hands=s["hands"], z_override=s["z"] or None, raw=True)


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
            cam = Camera(s["camera"], target_fn=self._char_target(s["camera"]), fps=self.fps)
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
            d = float(t.get("duration", 0.0)) if typ in ("whip_pan", "leaf_wipe") else 0.0
            if typ in ("whip_pan", "leaf_wipe") and d <= 0:
                raise ConfigError(f"{typ} {a.id}->{b.id} needs a positive duration")
            t_in, t_out = self.snap(boundary - d / 2), self.snap(boundary + d / 2)
            windows.append(tr.Window(typ, a.id, b.id, boundary, t_in, t_out, dict(t)))
        self.shots[-1].end = max(self.shots[-1].end, self.duration)
        return windows

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
    def camera_at(self, shot: Shot, t: float, dx: float = 0.0) -> CameraState:
        return shot.camera.state(t).offset(dx, 0.0)

    def render_shot(self, shot: Shot, t: float, dx: float = 0.0) -> Image.Image:
        """Render one shot at scene time t (camera x offset dx). Returns RGBA (alpha = plate coverage)."""
        cam = self.camera_at(shot, t, dx)
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        drawn_char = False
        for layer in self.env.layers:
            if not drawn_char and layer.z > self.env.character_z:
                self._draw_character(img, cam, t)
                drawn_char = True
            self.env.draw_layer(img, layer, cam, self.frame_world_width)
        if not drawn_char:
            self._draw_character(img, cam, t)
        return img

    def _draw_character(self, img: Image.Image, cam: CameraState, t: float):
        m = layer_matrix(cam, 1.0, self.env.reference, self.width, self.height, self.frame_world_width)
        self.character.draw(img, m, t, include_shadow=self.character.shadow)

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
        if w is None or w.type in ("cut", "cut_on_action"):
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
        if w.type == "leaf_wipe":
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
            elif w is not None and w.type == "leaf_wipe":
                cams.append(self.camera_at(self.shot(w.from_shot), t))
                cams.append(self.camera_at(self.shot(w.to_shot), t))
            else:
                cams.append(self.camera_at(self.shot_at(t), t))
        return cams
