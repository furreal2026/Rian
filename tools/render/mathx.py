"""Matrices (3x3 homogeneous, y-down screen convention), easing and keyframe tracks."""
from __future__ import annotations

import functools
import math
from typing import Any, Iterable, Sequence

import numpy as np


# ---------------------------------------------------------------- matrices
def ident() -> np.ndarray:
    return np.eye(3)


def translate(x: float, y: float) -> np.ndarray:
    m = np.eye(3)
    m[0, 2] = x
    m[1, 2] = y
    return m


def scale(sx: float, sy: float | None = None) -> np.ndarray:
    if sy is None:
        sy = sx
    m = np.eye(3)
    m[0, 0] = sx
    m[1, 1] = sy
    return m


def rotate_deg(deg: float) -> np.ndarray:
    """Rotation by `deg` degrees. With y pointing down, positive = clockwise on screen."""
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    m = np.eye(3)
    m[0, 0], m[0, 1] = c, -s
    m[1, 0], m[1, 1] = s, c
    return m


def apply(m: np.ndarray, x: float, y: float) -> tuple[float, float]:
    v = m @ np.array([x, y, 1.0])
    return float(v[0]), float(v[1])


def chain(*ms: np.ndarray) -> np.ndarray:
    out = np.eye(3)
    for m in ms:
        out = out @ m
    return out


# ----------------------------------------------------------------- easing
def _clamp01(t: float) -> float:
    return 0.0 if t < 0 else 1.0 if t > 1 else t


def _back_out(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


EASINGS = {
    "linear": lambda t: t,
    "step": lambda t: 0.0 if t < 1 else 1.0,
    "inQuad": lambda t: t * t,
    "outQuad": lambda t: 1 - (1 - t) * (1 - t),
    "inOutQuad": lambda t: 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2,
    "inCubic": lambda t: t ** 3,
    "outCubic": lambda t: 1 - (1 - t) ** 3,
    "inOutCubic": lambda t: 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2,
    "inOutSine": lambda t: -(math.cos(math.pi * t) - 1) / 2,
    "inSine": lambda t: 1 - math.cos(math.pi * t / 2),
    "outSine": lambda t: math.sin(math.pi * t / 2),
    "smoothstep": lambda t: t * t * (3 - 2 * t),
    "smootherstep": lambda t: t * t * t * (t * (6 * t - 15) + 10),
    "inExpo": lambda t: 0.0 if t == 0 else 2 ** (10 * t - 10),
    "outExpo": lambda t: 1.0 if t == 1 else 1 - 2 ** (-10 * t),
    "outBack": _back_out,
}


def ease(name: str, t: float) -> float:
    try:
        fn = EASINGS[name]
    except KeyError as exc:
        raise ValueError(f"unknown easing '{name}'. Known: {sorted(EASINGS)}") from exc
    return fn(_clamp01(t))


def lerp(a, b, u):
    if isinstance(a, (list, tuple)):
        return type(a)(lerp(x, y, u) for x, y in zip(a, b))
    return a + (b - a) * u


# ------------------------------------------------------------------ tracks
class Track:
    """Keyframe track over a list of dict keys, each with a time 't' (seconds).

    Every field is interpolated independently using only the keys that define it,
    so a key may set just `zoom` or just `pose`. Numeric fields (and numeric lists)
    are eased with the `ease` of the *arriving* key (default `default_ease`);
    non-numeric fields (strings, bools) hold until the next key that sets them.
    Values are held (clamped) before the first and after the last key.
    """

    def __init__(self, keys: Iterable[dict], default_ease: str = "inOutCubic"):
        self.keys = sorted((dict(k) for k in keys), key=lambda k: float(k["t"]))
        self.default_ease = default_ease
        self._by_field: dict[str, list[dict]] = {}
        for k in self.keys:
            for f in k:
                if f in ("t", "ease"):
                    continue
                self._by_field.setdefault(f, []).append(k)

    def fields(self) -> list[str]:
        return list(self._by_field)

    def has(self, field: str) -> bool:
        return field in self._by_field

    def value(self, t: float, field: str, default: Any = None) -> Any:
        ks = self._by_field.get(field)
        if not ks:
            return default
        if t <= ks[0]["t"]:
            return ks[0][field]
        if t >= ks[-1]["t"]:
            return ks[-1][field]
        # binary search for the segment
        lo, hi = 0, len(ks) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if ks[mid]["t"] <= t:
                lo = mid
            else:
                hi = mid
        a, b = ks[lo], ks[hi]
        va, vb = a[field], b[field]
        if not _is_numeric(va) or not _is_numeric(vb):
            return va
        span = b["t"] - a["t"]
        u = 0.0 if span <= 0 else (t - a["t"]) / span
        return lerp(va, vb, ease(b.get("ease", self.default_ease), u))


def _is_numeric(v: Any) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, (list, tuple)) and v and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
        return True
    return False


# ------------------------------------------------------------------ noise
@functools.lru_cache(maxsize=256)
def _noise_phases(seed: int) -> tuple[float, ...]:
    return tuple(np.random.default_rng(seed).uniform(0, 2 * math.pi, 3))


def smooth_noise(t: float, seed: int, freq: float) -> float:
    """Deterministic smooth pseudo-noise in roughly [-1, 1] (sum of 3 incommensurate sines)."""
    phases = _noise_phases(seed)
    mults = (1.0, 2.13, 3.71)
    weights = (0.6, 0.28, 0.12)
    return float(sum(w * math.sin(2 * math.pi * freq * m * t + p) for w, m, p in zip(weights, mults, phases)))
