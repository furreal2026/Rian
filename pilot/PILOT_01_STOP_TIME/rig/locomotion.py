"""Walk / run gaits for the side view, solved with two-bone IK so planted feet never slide.

The gait is parameterised by *distance travelled* (rig units), not time: the cycle phase is
u = u0 + distance / (2 * step_length). While a foot is in stance its ankle moves backwards in
root space by exactly the distance the root moves forwards, so it stays fixed on the ground in
world space whatever the speed curve of the root (ease-in/out included). The stance foot rolls
heel -> flat -> toe; during toe-off the toe is the fixed contact point. Swing feet follow an
eased arc. Hip height comes from a smooth envelope that keeps both legs within reach, plus the
gait's own bob. Arms counter-swing with a phase lag (overlap) and the forearms lag the upper
arms (follow-through).

`gait_params(rig, kind, distance, ...)` returns *effective* params (see Rig.effective_params)
for the legs, hips, torso, head and (optionally) arms; draw them with raw=True.
"""
from __future__ import annotations

import math
from functools import lru_cache

GAITS: dict[str, dict] = {
    "walk": dict(stance=0.62, lift=22.0, heel=0.10, roll=0.20, heel_angle=-16.0, toe_angle=34.0,
                 bob=3.0, compress=0.0, flight_rise=0.0, lean=3.0, head=-1.5,
                 arm_swing=22.0, elbow=(-12.0, -30.0), arm_lag=0.06, forearm_lag=0.05, step=150.0),
    "run": dict(stance=0.36, lift=58.0, heel=0.0, roll=0.30, heel_angle=-4.0, toe_angle=42.0,
                bob=4.0, compress=14.0, flight_rise=8.0, lean=10.0, head=-6.0,
                arm_swing=36.0, elbow=(-78.0, -100.0), arm_lag=0.05, forearm_lag=0.04, step=230.0),
}

TOE = (20.0, 4.0)          # toe point in the foot's local frame (ankle pivot at 0,0; sole at y~4)
HIP_Y = -214.0             # hips joint (root space) at hips_dy = 0
LEG_REACH = 211.0 * 0.992  # thigh 107 + shin 104, keep a hair of knee bend


def _rot(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _smooth(x):
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, max(0.0, x)))


def foot_state(g: dict, v: float, step: float) -> tuple[float, float, float, bool]:
    """Ankle (x relative to the hips, y root space) and foot world angle at leg phase v."""
    beta = g["stance"]
    C = 2.0 * step
    xc = beta * C / 2.0                       # contact point ahead of the hips
    v %= 1.0

    def stance(s):
        x_lin = xc - s * beta * C             # world-fixed contact, moving back in root space
        r0 = 1.0 - g["roll"]
        if s > r0:                            # toe-off: rotate about the (fixed) toe
            k = ((s - r0) / g["roll"]) ** 1.5
            ang = g["toe_angle"] * k
            toe = (x_lin + TOE[0], TOE[1])
            off = _rot(TOE, ang)
            return toe[0] - off[0], toe[1] - off[1], ang
        if g["heel"] > 0 and s < g["heel"]:   # heel strike: toe comes down
            return x_lin, 0.0, g["heel_angle"] * (1.0 - s / g["heel"]) ** 1.3
        return x_lin, 0.0, 0.0

    if v < beta:
        x, y, a = stance(v / beta)
        return x, y, a, True
    s = (v - beta) / (1.0 - beta)
    x0, y0, a0 = stance(1.0)
    x1, y1, a1 = xc, 0.0, g["heel_angle"]
    # swing: run feet trail and tuck up first, walk feet move on an even arc
    ex = _smooth(s) ** (1.35 if g["compress"] > 0 else 1.0)
    peak = 0.38 if g["compress"] > 0 else 0.45
    arc = math.sin(math.pi * min(1.0, s / (2 * peak))) if s < peak else math.sin(math.pi * (0.5 + 0.5 * (s - peak) / (1 - peak)))
    y = y0 + (y1 - y0) * _smooth(s) - g["lift"] * max(0.0, arc)
    a = a0 + (a1 - a0) * _smooth(min(1.0, s * 1.25))
    return x0 + (x1 - x0) * ex, y, a, False


@lru_cache(maxsize=32)
def _hip_curve(kind: str, step: float, n: int = 192) -> tuple[float, ...]:
    """hips_dy over one cycle (n samples): gait bob, raised where needed to keep feet in reach."""
    g = GAITS[kind]
    req, base = [], []
    for i in range(n):
        u = i / n
        need = -1e9
        compress = 0.0
        flight = True
        for side, v in (("l", u), ("r", u + 0.5)):
            x, y, a, planted = foot_state(g, v, step)
            if planted:
                flight = False
                compress = max(compress, math.sin(math.pi * ((v % 1.0) / g["stance"])))
            dx = x - (-2.0 if side == "l" else 2.0)
            reach = math.sqrt(max(1.0, LEG_REACH ** 2 - dx * dx))
            need = max(need, (y - reach) - HIP_Y)       # hips_dy must be >= this (y down)
        req.append(need)
        base.append(g["bob"] * (0.5 - 0.5 * math.cos(4 * math.pi * u)) + g["compress"] * compress
                    - (g["flight_rise"] if flight else 0.0))
    # smooth periodic envelope over the reach requirement (no kinks), then combine
    w = max(2, n // 24)
    env = [max(req[(i + k) % n] for k in range(-w, w + 1)) for i in range(n)]
    for _ in range(3):
        env = [(env[(i - 1) % n] + 2 * env[i] + env[(i + 1) % n]) / 4 for i in range(n)]
    out = [max(b, e + 0.5) for b, e in zip(base, env)]
    for _ in range(2):
        out = [(out[(i - 1) % n] + 2 * out[i] + out[(i + 1) % n]) / 4 for i in range(n)]
    return tuple(max(o, r + 0.2) for o, r in zip(out, req))


def _sample(curve, u):
    n = len(curve)
    f = (u % 1.0) * n
    i = int(f)
    k = f - i
    return curve[i % n] * (1 - k) + curve[(i + 1) % n] * k


def cycle_phase(distance: float, step: float, u0: float | None = None, kind: str = "walk") -> float:
    """Gait phase for a travelled distance. Default u0 starts at the left foot's mid-stance
    (feet together, right foot passing), which blends cleanly from a standing pose."""
    g = GAITS[kind]
    if u0 is None:
        u0 = g["stance"] / 2.0
    return (u0 + distance / (2.0 * step)) % 1.0


def gait_raw(rig, kind: str, distance: float, base: dict[str, float] | None = None, step: float | None = None,
             arms: bool = True, amp: float = 1.0, u0: float | None = None) -> dict[str, float]:
    """Authored-level (pre-driver) params for hips, torso, head and arms. Legs come from IK."""
    g = GAITS[kind]
    step = float(step or g["step"])
    u = cycle_phase(distance, step, u0, kind)
    p = {k: float((base or {}).get(k, 0.0)) for k in rig.params}
    p["hips"] = 0.0
    p["hips_dx"] = 0.0
    p["hips_dy"] = _sample(_hip_curve(kind, step), u)
    p["torso"] = g["lean"] * amp + 1.2 * math.sin(4 * math.pi * u) * amp
    p["head"] = g["head"] * amp - 0.6 * p["torso"] + 1.0 * math.sin(4 * math.pi * (u - 0.06))
    if arms:
        s = math.cos(2 * math.pi * (u - g["arm_lag"]))       # near arm back when near leg is forward
        p["shoulder_l"] = g["arm_swing"] * amp * s
        p["shoulder_r"] = -g["arm_swing"] * amp * s
        e0, e1 = g["elbow"]
        for side, sign in (("l", 1.0), ("r", -1.0)):
            fwd = max(0.0, -sign * math.cos(2 * math.pi * (u - g["arm_lag"] - g["forearm_lag"])))
            p[f"elbow_{side}"] = (e0 + (e1 - e0) * fwd) * min(1.0, amp)
            p[f"wrist_{side}"] = -6.0 * fwd
    return p


def leg_targets(kind: str, distance: float, step: float | None = None, u0: float | None = None) -> dict[str, tuple[float, float, float]]:
    """Root-space ankle target (x, y) and foot world angle per leg ('l'/'r'), hips at x = 0."""
    g = GAITS[kind]
    step = float(step or g["step"])
    u = cycle_phase(distance, step, u0, kind)
    out = {}
    for side, v in (("l", u), ("r", u + 0.5)):
        x, y, a, _ = foot_state(g, v, step)
        out[side] = (x, y, a)
    return out


def gait_params(rig, kind: str, distance: float, base: dict[str, float] | None = None, step: float | None = None,
                arms: bool = True, amp: float = 1.0, u0: float | None = None) -> dict[str, float]:
    """Effective side-view params for `kind` ('walk'/'run') after travelling `distance` rig units."""
    p = gait_raw(rig, kind, distance, base, step, arms, amp, u0)
    q = rig.effective_params("side", p)
    for side, (x, y, a) in leg_targets(kind, distance, step, u0).items():
        q = rig.ik_two_bone("side", q, (f"thigh_{side}", f"shin_{side}", f"foot_{side}"), (x, y), bend=-1,
                            end_angle=a, effective=True)
    return q


def stance_ankles(rig, kind: str, distance: float, step: float | None = None) -> dict[str, tuple[float, float, bool]]:
    """Root-space ankle targets + planted flag (for tests / QC of foot sliding)."""
    g = GAITS[kind]
    step = float(step or g["step"])
    u = cycle_phase(distance, step, None, kind)
    out = {}
    for side, v in (("l", u), ("r", u + 0.5)):
        x, y, a, planted = foot_state(g, v, step)
        s = ((v % 1.0) / g["stance"]) if planted else 1.0
        out[side] = (x, y, planted and s < 1.0 - g["roll"])
    return out
