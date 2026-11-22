"""Camera presets: named framings and moves that resolve into plain camera keys + modifiers.

A shot's camera may be written as a preset instead of raw keys:

    {"preset": "push_in", "start": 3.0, "end": 5.0, "shot_from": "wide", "shot_to": "medium"}

and is resolved once, at load time, into `{"keys": [...], "modifiers": [...]}` that `Camera` already understands.
Nothing here renders: every preset is just a way to write keys, so the projection, parallax and clamping
code is shared with hand-written cameras.

Framings (angle / size). `zoom` is the camera dolly (layers scale by zoom**parallax), `focus` is the frame
centre as a fraction of the subject's height above its feet (the subject is the character root):

    establishing      whole master frame, subject small
    wide              full body with surroundings
    medium            knees up
    close_up          head and shoulders
    extreme_close_up  face
    high_angle        camera raised: subject low in frame, more ground
    low_angle         camera lowered: subject high in frame, towering

high_angle / low_angle are *framings* (position + zoom). The camera has no pitch: the plates are painted at eye
level, so the view of the walls and floor does not change perspective. over_the_shoulder needs a foreground
actor or prop that does not exist yet and is refused with an explanation.

Moves: static/frame, push_in (= dolly_in), pull_back (= dolly_out), zoom_in/zoom_out (lens: no parallax change),
snap_zoom_in/out, pan, tilt, center_shift, track (horizontal / vertical / both), drift, shake. Several moves can be
combined in one shot with `"also": [ {...}, ... ]` as long as they animate different fields.

Common controls: start, end (scene seconds), ease, amount (intensity multiplier, default 1), direction,
distance (world units), focus ([x, y] or "character"), offset ([dx, dy]), shot / shot_from / shot_to.
"""
from __future__ import annotations

from typing import Callable

# name -> (zoom, focus height as a fraction of the subject height above its feet)
FRAMINGS: dict[str, tuple[float, float]] = {
    "establishing": (1.0, 0.93),
    "wide": (1.4, 0.55),
    "medium": (2.4, 0.62),
    "close_up": (3.6, 0.80),
    "extreme_close_up": (5.8, 0.82),
    "high_angle": (1.15, 1.35),
    "low_angle": (1.7, 0.25),
}
FRAMING_ALIASES = {"wide_shot": "wide", "medium_shot": "medium", "cu": "close_up", "ecu": "extreme_close_up",
                   "extreme_closeup": "extreme_close_up", "closeup": "close_up", "establishing_shot": "establishing",
                   "high_angle_shot": "high_angle", "low_angle_shot": "low_angle", "ots": "over_the_shoulder"}

MOVES = ("static", "frame", "push_in", "dolly_in", "pull_back", "dolly_out", "zoom_in", "zoom_out", "snap_zoom_in",
         "snap_zoom_out", "pan", "tilt", "center_shift", "track", "track_h", "track_v", "drift", "shake")

PUSH_FACTOR = 0.35   # zoom multiplier per unit of `amount` for push_in / pull_back
LENS_FACTOR = 0.25   # lens multiplier per unit of `amount` for zoom_in / zoom_out
FIELDS = ("x", "y", "zoom", "lens", "rot")


class PresetError(ValueError):
    pass


class _Ctx:
    def __init__(self, target_fn: Callable[[float], tuple[float, float]] | None, subject_height: float):
        self.target_fn = target_fn
        self.H = float(subject_height)


def _framing(name: str | None) -> tuple[float, float] | None:
    if name is None:
        return None
    name = FRAMING_ALIASES.get(name, name)
    if name == "over_the_shoulder":
        raise PresetError("over_the_shoulder needs a second actor or a foreground shoulder asset, which the project does not have yet. "
                          "Use a framing preset, or add the asset first.")
    if name not in FRAMINGS:
        raise PresetError(f"unknown framing '{name}'. Known: {sorted(FRAMINGS)}")
    return FRAMINGS[name]


def _state(cfg: dict, ctx: _Ctx, t: float, shot: str | None, zoom: float | None = None, focus=None) -> dict:
    """Camera x, y, zoom for a framing at scene time t."""
    fr = _framing(shot)
    z = fr[0] if fr else float(zoom if zoom is not None else cfg.get("zoom", 1.0))
    frac = fr[1] if fr else float(cfg.get("focus_frac", 0.62))
    focus = focus if focus is not None else cfg.get("focus", "character")
    if isinstance(focus, (list, tuple)):
        x, y = float(focus[0]), float(focus[1])
    else:
        if ctx.target_fn is None:
            raise PresetError("preset needs a character target (focus 'character') or an explicit focus [x, y]")
        tx, ty = ctx.target_fn(t)
        x, y = tx, ty - frac * ctx.H
    ox, oy = cfg.get("offset", [0.0, 0.0])
    return {"x": x + float(ox), "y": y + float(oy), "zoom": z}


def _part(cfg: dict, ctx: _Ctx, base: dict | None) -> dict:
    name = cfg["preset"]
    if name not in MOVES:
        raise PresetError(f"unknown preset '{name}'. Moves: {list(MOVES)}; framings go in 'shot'/'shot_from'/'shot_to'")
    t0 = float(cfg.get("start", 0.0))
    amt = float(cfg.get("amount", 1.0))
    fast = name.startswith("snap_zoom")
    t1 = float(cfg["end"]) if "end" in cfg else t0 + (0.18 if fast else 0.0)
    if name not in ("static", "frame") and t1 <= t0 and not name in ("drift", "shake", "track", "track_h", "track_v"):
        raise PresetError(f"preset '{name}' needs end > start")
    shot_from = cfg.get("shot_from") or cfg.get("shot")
    s0 = _state(cfg, ctx, t0, shot_from)
    if base is not None:  # an `also` move without its own framing continues from the primary move's base
        for k in ("x", "y", "zoom"):
            if not (shot_from or k in cfg):
                s0[k] = base[k]
    anim: dict[str, tuple[float, float]] = {}
    mods: list[dict] = []
    ease = cfg.get("ease", "outExpo" if fast else "inOutSine")
    d = cfg.get("direction")
    if name in ("push_in", "dolly_in", "pull_back", "dolly_out"):
        s1 = _state(cfg, ctx, t1, cfg["shot_to"]) if cfg.get("shot_to") else None
        if s1 is None:
            f = 1.0 + PUSH_FACTOR * amt
            z1 = float(cfg["zoom_to"]) if "zoom_to" in cfg else (s0["zoom"] * f if name in ("push_in", "dolly_in") else s0["zoom"] / f)
            s1 = {"x": s0["x"], "y": s0["y"], "zoom": z1}
        anim["zoom"] = (s0["zoom"], s1["zoom"])
        if abs(s1["x"] - s0["x"]) > 1e-9:
            anim["x"] = (s0["x"], s1["x"])
        if abs(s1["y"] - s0["y"]) > 1e-9:
            anim["y"] = (s0["y"], s1["y"])
    elif name in ("zoom_in", "zoom_out", "snap_zoom_in", "snap_zoom_out"):
        zin = name.endswith("in")
        f = (1.5 if fast else 1.0 + LENS_FACTOR * amt)
        l1 = float(cfg["lens_to"]) if "lens_to" in cfg else (f if zin else 1.0 / f)
        anim["lens"] = (float(cfg.get("lens", 1.0)), l1)
    elif name == "pan":
        dist = float(cfg.get("distance", 300.0 * amt)) * (-1.0 if d == "left" else 1.0)
        if d not in ("left", "right"):
            raise PresetError("pan needs direction 'left' or 'right'")
        anim["x"] = (s0["x"], s0["x"] + dist)
    elif name == "tilt":
        if d not in ("up", "down"):
            raise PresetError("tilt needs direction 'up' or 'down'")
        dist = float(cfg.get("distance", 200.0 * amt)) * (-1.0 if d == "up" else 1.0)
        anim["y"] = (s0["y"], s0["y"] + dist)
    elif name == "center_shift":
        if "focus_to" not in cfg and "shot_to" not in cfg:
            raise PresetError("center_shift needs focus_to [x, y] (or shot_to)")
        s1 = _state(cfg, ctx, t1, cfg.get("shot_to") or shot_from, focus=cfg.get("focus_to"))
        anim["x"], anim["y"] = (s0["x"], s1["x"]), (s0["y"], s1["y"])
    elif name in ("track", "track_h", "track_v"):
        axis = "x" if name == "track_h" else "y" if name == "track_v" else cfg.get("axis", "xy")
        mods.append({"type": "track", "axis": axis, "lag": float(cfg.get("lag", 0.3)), "strength": float(cfg.get("strength", 1.0)),
                     "offset": list(cfg.get("track_offset", [0.0, 0.0])), "t0": t0})
    elif name == "drift":
        mods.append({"type": "drift", "amp_x": 6.0 * amt, "amp_y": 3.0 * amt, "amp_rot": 0.15 * amt,
                     "freq": float(cfg.get("freq", 0.2)), "seed": int(cfg.get("seed", 1)),
                     **{k: cfg[k] for k in ("amp_x", "amp_y", "amp_rot", "amp_zoom") if k in cfg}})
    elif name == "shake":
        mods.append({"type": "shake", "start": t0, "duration": t1 - t0, "intensity": float(cfg.get("intensity", amt)),
                     "freq": float(cfg.get("freq", 9.0)), "attack": float(cfg.get("attack", 0.02)),
                     "decay": float(cfg.get("decay", 0.35)), "seed": int(cfg.get("seed", 7)),
                     **{k: cfg[k] for k in ("amp_x", "amp_y", "amp_rot") if k in cfg}})
    return {"t0": t0, "t1": t1, "base": s0, "anim": anim, "mods": mods, "ease": ease}


def resolve_preset(cfg: dict, target_fn: Callable[[float], tuple[float, float]] | None, subject_height: float = 300.0) -> dict:
    """Turn a preset camera config into {'keys', 'modifiers', 'ease'} understood by Camera."""
    ctx = _Ctx(target_fn, subject_height)
    primary = _part(cfg, ctx, None)
    parts = [primary] + [_part(dict(c), ctx, primary["base"]) for c in cfg.get("also", [])]
    base = primary["base"]
    keys: list[dict] = [{"t": primary["t0"], "x": base["x"], "y": base["y"], "zoom": base["zoom"], "lens": 1.0, "rot": float(cfg.get("rot", 0.0))}]
    used: dict[str, int] = {}
    mods: list[dict] = []
    for i, p in enumerate(parts):
        mods.extend(p["mods"])
        for f, (a, b) in p["anim"].items():
            if f in used:
                raise PresetError(f"two moves in one shot both animate '{f}'; combine moves that animate different fields")
            used[f] = i
            if i == 0:
                keys[0][f] = a
            else:
                keys.append({"t": p["t0"], f: a})
            keys.append({"t": p["t1"], f: b, "ease": p["ease"]})
    mods.extend(cfg.get("modifiers", []))
    return {"keys": keys, "modifiers": mods, "ease": cfg.get("ease", "inOutSine")}
