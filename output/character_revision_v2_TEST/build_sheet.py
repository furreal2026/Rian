"""TEST — Rian expression sheet revision v2 (awaiting owner approval).

Generates a vector SVG expression sheet for Rian and renders it to PNG with the
pre-installed Chromium. Does NOT touch production rig assets.

Units: head radius = 100, head centre = (0, 0), y down (same as the rig).
Palette and line widths follow pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json.

    python output/character_revision_v2_TEST/build_sheet.py
"""
from __future__ import annotations

import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = json.loads((ROOT / "pilot/PILOT_01_STOP_TIME/rig/stick_figure_rig.json").read_text())
PAL = SPEC["palette"]
INK, SKIN, SHIRT, SHIRT_SH, FOLD, MOUTH = (PAL[k] for k in ("ink", "skin", "shirt", "shirt_shadow", "shirt_fold", "mouth"))
BAG = "#C9C9D1"


# ------------------------------------------------------------------ geometry helpers
def catmull(pts, n=10):
    if len(pts) < 3:
        return list(pts)
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


def f(v):
    return f"{v:.2f}"


def taper(pts, w_end0, w_mid, w_end1, color=INK, smooth=True, power=0.55):
    """Filled tapered stroke (clean ink line with thin ends)."""
    s = catmull(pts, 12) if smooth else list(pts)
    # arc-length parameter
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
        bump = math.sin(math.pi * t) ** power
        base = w_end0 + (w_end1 - w_end0) * t
        w = base + (w_mid - base) * bump
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    poly = left + right[::-1]
    path = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in poly) + " Z"
    return (f'<path d="{path}" fill="{color}"/>'
            f'<circle cx="{f(s[0][0])}" cy="{f(s[0][1])}" r="{f(w_end0 / 2)}" fill="{color}"/>'
            f'<circle cx="{f(s[-1][0])}" cy="{f(s[-1][1])}" r="{f(w_end1 / 2)}" fill="{color}"/>')


def poly_path(pts, close=True):
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + (" Z" if close else "")


# ------------------------------------------------------------------ face parts
EYE_X, EYE_Y, EYE_RX, EYE_RY = 40.0, -10.0, 29.0, 22.0
MOUTH_Y = 46.0
_uid = [0]


def eye(side, e):
    """side: -1 = screen-left eye, +1 = screen-right eye. Inner corner faces the nose (x=0)."""
    _uid[0] += 1
    cid = f"eye{_uid[0]}"
    ex = side * EYE_X + e.get("dx", 0.0)
    ey = EYE_Y + e.get("dy", 0.0)
    rx = e.get("rx", EYE_RX)
    ry = e.get("ry", EYE_RY)
    i = 0 if side < 0 else 1
    pick = lambda k, d=None: (e[k][i] if isinstance(e.get(k), (list, tuple)) else e.get(k, d))
    lid_in, lid_out = pick("lid_in", None), pick("lid_out", None)
    open_eye = lid_in is None
    gx, gy = e.get("gaze", (0.0, 0.0))
    pr = e.get("pupil", 12.5)
    inner = -side  # direction (in x) towards the nose

    def lid_y(x):
        # u = -1 at outer edge, +1 at inner edge
        u = (x - ex) / rx * inner
        top = ey - ry
        yin, yout = top + 2 * ry * lid_in, top + 2 * ry * lid_out
        y = yout + (yin - yout) * (u + 1) / 2
        return y - pick("lid_arch", 2.2) * (1 - u * u)

    out = []
    px = ex + gx * (rx - pr - 2.5)
    py = ey + gy * (ry - pr - 1.5)
    out.append(f'<clipPath id="{cid}"><ellipse cx="{f(ex)}" cy="{f(ey)}" rx="{f(rx)}" ry="{f(ry)}"/></clipPath>')
    g = [f'<ellipse cx="{f(ex)}" cy="{f(ey)}" rx="{f(rx)}" ry="{f(ry)}" fill="{SKIN}"/>',
         f'<circle cx="{f(px)}" cy="{f(py)}" r="{f(pr)}" fill="{INK}"/>',
         f'<circle cx="{f(px - pr * 0.36)}" cy="{f(py - pr * 0.4)}" r="{f(max(1.7, pr * 0.24))}" fill="{SKIN}"/>']
    if not open_eye:
        xs = [ex - rx - 2 + k * (2 * rx + 4) / 40 for k in range(41)]
        cover = [(x, lid_y(x)) for x in xs] + [(ex + rx + 4, ey - ry - 6), (ex - rx - 4, ey - ry - 6)]
        g.append(f'<path d="{poly_path(cover)}" fill="{SKIN}"/>')
    out.append(f'<g clip-path="url(#{cid})">' + "".join(g) + "</g>")

    # eye outline (lower arc below the lid, or full for open eyes)
    if open_eye:
        ring = [(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in [k * 2 * math.pi / 72 for k in range(73)]]
        out.append(f'<path d="{poly_path(ring, False)}" fill="none" stroke="{INK}" stroke-width="4.2" stroke-linejoin="round"/>')
        top = [(ex + rx * math.cos(a), ey - ry * math.sin(a)) for a in [math.pi * (0.12 + 0.76 * k / 20) for k in range(21)]]
        out.append(taper(top, 4.2, 6.6, 4.2, smooth=False))
    else:
        arc = [(ex + rx * math.cos(a), ey + ry * math.sin(a)) for a in [-math.pi / 2 + k * 2 * math.pi / 240 for k in range(241)]]
        arc = [p for p in arc if p[1] >= lid_y(p[0]) - 0.3]
        if len(arc) > 2:
            low = [p for p in arc if p[1] >= ey - ry * 0.98]
            out.append(taper(low, 3.0, 4.4, 3.0, smooth=False, power=0.3))
        # heavy upper lid — Rian's signature
        def edge(sgn):
            lo, hi = 0.0, rx * 1.2
            for _ in range(40):
                m = (lo + hi) / 2
                x = ex + sgn * m
                inside = ((x - ex) / rx) ** 2 + ((lid_y(x) - ey) / ry) ** 2 <= 1
                lo, hi = (m, hi) if inside else (lo, m)
            return ex + sgn * lo
        x_out, x_in = edge(-inner), edge(inner)
        ext_out, ext_in = pick("lid_ext", 2.5), 1.0
        x0 = x_out - inner * ext_out
        x1 = x_in + inner * ext_in
        pts = [(x0 + (x1 - x0) * k / 8, lid_y(x_out + (x_in - x_out) * k / 8) + 0.0) for k in range(9)]
        flick = pick("flick", 0.0)
        pts[0] = (pts[0][0], pts[0][1] - flick)
        out.append(taper(pts, 4.6, pick("lid_w", 11.0), 5.0, power=0.35))

    # brow
    if e.get("brow") is not False:
        bdy, tin, tout = pick("brow_dy", 13.0), pick("brow_in", 0.0), pick("brow_out", 0.0)
        arch = pick("brow_arch", 3.0)
        top = ey - ry
        if not open_eye:
            top = min(lid_y(ex + inner * rx * 0.7), lid_y(ex - inner * rx * 0.7), lid_y(ex))
        by = top - bdy
        xin, xout = ex + inner * rx * 0.72, ex - inner * rx * 0.95
        bpts = [(xin, by - tin), ((xin + ex) / 2, by - tin * 0.5 - arch * 0.8), (ex - inner * rx * 0.2, by - (tin + tout) * 0.5 - arch),
                (xout, by - tout + 1.5)]
        out.append(taper(bpts, pick("brow_w0", 5.6), pick("brow_w", 7.6), 3.8, power=0.4))
    if e.get("bags"):
        bag1 = [(ex - rx * 0.75, ey + ry + 5), (ex, ey + ry + 8.5), (ex + rx * 0.75, ey + ry + 5)]
        out.append(taper(bag1, 0.8, 3.2, 0.8, color=BAG))
        bag2 = [(ex - rx * 0.45, ey + ry + 11), (ex, ey + ry + 13), (ex + rx * 0.45, ey + ry + 11)]
        out.append(taper(bag2, 0.6, 2.2, 0.6, color=BAG))
    return "".join(out)


def mouth(kind, mx=1.0, my=MOUTH_Y):
    return f'<g transform="translate({mx} {my}) scale(1.3 1.15) translate({-mx} {-my})">' + _mouth(kind, mx, my) + "</g>"


def _mouth(kind, mx=1.0, my=MOUTH_Y):
    w = 5.4
    if kind == "line":
        return taper([(mx - 9, my), (mx, my + 0.6), (mx + 9, my - 0.2)], 2.2, w, 2.0)
    if kind == "line_tilt":
        return taper([(mx - 10, my + 1.6), (mx, my), (mx + 9, my - 2.2)], 2.2, w, 2.0)
    if kind == "frown_small":
        return taper([(mx - 10, my + 2.2), (mx, my - 0.8), (mx + 10, my + 2.2)], 2.0, w, 2.0)
    if kind == "flat_low":
        return taper([(mx - 11, my + 1.5), (mx - 2, my + 0.4), (mx + 9, my + 2.0)], 2.0, w, 2.0)
    if kind == "squiggle":
        return taper([(mx - 11, my + 1), (mx - 5, my - 1.5), (mx + 1, my + 1.5), (mx + 7, my - 1.2), (mx + 11, my + 0.5)], 2.0, w, 2.0)
    if kind == "smirk":
        return taper([(mx - 10, my + 0.4), (mx - 1, my + 2.0), (mx + 8, my - 0.6), (mx + 13, my - 4.6)], 2.0, w, 2.2)
    if kind == "worried":
        return taper([(mx - 11, my + 2.4), (mx - 5, my - 0.6), (mx + 1, my + 0.6), (mx + 6, my - 0.6), (mx + 11, my + 2.4)], 2.0, w, 2.0)
    if kind == "disgust":
        return taper([(mx - 12, my + 3.5), (mx - 6, my - 0.5), (mx + 1, my + 1.2), (mx + 7, my - 0.4), (mx + 12, my + 3.6)], 2.0, w, 2.4)
    if kind == "open":
        cx, cy, rx, ry = mx, my + 3, 9.5, 12.5
        shape = [(cx + rx * math.cos(a) * (1 - 0.08 * math.sin(a)), cy + ry * math.sin(a)) for a in [k * 2 * math.pi / 60 for k in range(61)]]
        tongue = f'<clipPath id="mo1"><path d="{poly_path(shape)}"/></clipPath><ellipse clip-path="url(#mo1)" cx="{f(cx)}" cy="{f(cy + 10)}" rx="8" ry="5.5" fill="#B9484A"/>'
        return (f'<path d="{poly_path(shape)}" fill="{MOUTH}"/>' + tongue +
                f'<path d="{poly_path(shape)}" fill="none" stroke="{INK}" stroke-width="3.6" stroke-linejoin="round"/>')
    if kind == "grimace":
        top = catmull([(mx - 14, my - 3), (mx, my - 4), (mx + 14, my - 3)], 10)
        bot = catmull([(mx + 14, my - 3), (mx + 12, my + 6), (mx, my + 7.5), (mx - 12, my + 6), (mx - 14, my - 3)], 10)
        shape = top + bot
        teeth = f'<clipPath id="mo2"><path d="{poly_path(shape)}"/></clipPath><rect clip-path="url(#mo2)" x="{f(mx - 16)}" y="{f(my - 6)}" width="32" height="6" fill="{SKIN}"/>'
        return (f'<path d="{poly_path(shape)}" fill="{MOUTH}"/>' + teeth +
                f'<path d="{poly_path(shape)}" fill="none" stroke="{INK}" stroke-width="3.6" stroke-linejoin="round"/>')
    raise ValueError(kind)


# ------------------------------------------------------------------ expressions
BASE = dict(lid_in=0.47, lid_out=0.47, gaze=(0.12, 0.62), brow_dy=12.5, brow_in=0.0, brow_out=-1.5, brow_arch=2.2)


def X(**kw):
    d = dict(BASE)
    d.update(kw)
    return d


EXPRESSIONS = {
    "Neutral":   (X(), "line", None),
    "Skeptical": (X(lid_in=[0.56, 0.36], lid_out=[0.56, 0.36], gaze=(0.55, 0.45), brow_dy=[12.0, 18.0], brow_in=[-1.0, 2.0],
                    brow_out=[-1.0, 6.0], brow_arch=[1.5, 6.5]), "line_tilt", None),
    "Annoyed":   (X(lid_in=0.58, lid_out=0.40, lid_arch=1.0, gaze=(0.35, 0.55), brow_dy=13.0, brow_in=-4.0, brow_out=2.0, brow_arch=0.5),
                  "frown_small", None),
    "Exhausted": (X(lid_in=0.60, lid_out=0.70, lid_arch=3.0, gaze=(0.0, 0.75), brow_dy=10.0, brow_in=2.5, brow_out=-3.5, bags=True,
                    lid_w=7.8), "flat_low", None),
    "Confused":  (X(lid_in=None, lid_out=None, rx=24, ry=21, gaze=(0.5, -0.45), pupil=9.0, brow_dy=[10.0, 17.0], brow_in=[1.0, 4.0],
                    brow_out=[-2.5, 5.0], brow_arch=[2.0, 6.0], brow_w=5.6), "squiggle", "?"),
    "Shocked":   (X(lid_in=None, lid_out=None, rx=25, ry=23.5, gaze=(0.0, 0.0), pupil=6.2, brow_dy=17.0, brow_in=3.0, brow_out=1.0,
                    brow_arch=6.0, brow_w=5.8, dy=-2.0), "open", "!!"),
    "Angry":     (X(lid_in=0.56, lid_out=0.30, lid_arch=0.5, gaze=(0.0, 0.5), brow_dy=13.0, brow_in=-7.0, brow_out=4.0, brow_arch=-0.5,
                    brow_w=8.6, brow_w0=6.0), "grimace", None),
    "Disgusted": (X(lid_in=[0.56, 0.50], lid_out=[0.50, 0.42], gaze=(0.6, 0.5), brow_dy=[11.5, 14.0], brow_in=[-3.5, -0.5],
                    brow_out=[0.0, 1.0], brow_arch=[0.5, 2.0]), "disgust", None),
    "Worried":   (X(lid_in=0.26, lid_out=0.34, lid_arch=-0.5, gaze=(0.5, 0.25), lid_w=6.8, brow_dy=12.0, brow_in=8.5, brow_out=-3.0,
                    brow_arch=1.0, flick=1.0), "worried", None),
    "Smug":      (X(lid_in=0.55, lid_out=0.53, lid_arch=3.0, gaze=(0.5, 0.6), brow_dy=[11.0, 14.0], brow_in=[0.0, 1.5],
                    brow_out=[-2.0, 2.5], brow_arch=[2.0, 3.5]), "smirk", None),
}


# ------------------------------------------------------------------ body (bust)
HEAD_TO_TORSO = 246.0 + 8.0  # rig: head centre 246 units above hips; +8 shows a short neck


def tshirt_bust():
    """Rig torso_front + sleeves, translated so the head centre is (0,0)."""
    oy = HEAD_TO_TORSO
    T = lambda pts: [(x, y + oy) for x, y in pts]
    body = T([(-26, -149), (-12, -143), (0, -141), (12, -143), (26, -149), (46, -145), (57, -131), (58, -112),
              (52, -92), (50, -50), (53, -3), (0, 0), (-53, -3), (-50, -50), (-52, -92), (-58, -112), (-57, -131), (-46, -145)])
    body_s = catmull(body + [body[0]], 8)
    out = []
    # arms (behind the sleeves, in front of nothing)
    for sgn, rot in ((-1, 12), (1, -12)):
        sx, sy = sgn * 52, -104 + oy
        a = math.radians(rot)
        dx, dy = -math.sin(a), math.cos(a)
        end = (sx + dx * 140, sy + dy * 140)
        out.append(taper([(sx, sy), ((sx + end[0]) / 2 + 0.6, (sy + end[1]) / 2), end], 6.6, 6.6, 6.4))
    out.append(f'<clipPath id="shirtclip"><path d="{poly_path(body_s)}"/></clipPath>')
    out.append(f'<path d="{poly_path(body_s)}" fill="{SHIRT}"/>')
    sh = T([(30, -160), (80, -160), (80, 10), (36, 10), (40, -60)])
    out.append(f'<path clip-path="url(#shirtclip)" d="{poly_path(sh)}" fill="{SHIRT_SH}"/>')
    collar = catmull(T([(-22, -147), (-10, -138), (0, -136), (10, -138), (22, -147)]), 8)
    out.append(f'<g clip-path="url(#shirtclip)">{taper(collar, 2.0, 4.0, 2.0, color=FOLD, smooth=False)}'
               f'{taper(T([(18, -74), (22, -66), (24, -60)]), 0.8, 2.4, 0.8, color=FOLD)}</g>')
    out.append(f'<path d="{poly_path(body_s)}" fill="none" stroke="{INK}" stroke-width="5.6" stroke-linejoin="round"/>')
    # sleeves
    for sgn, rot in ((-1, 12), (1, -12)):
        sx, sy = sgn * 52, -104 + oy
        sleeve = catmull([(-14, -18), (0, -21), (14, -18), (17, 6), (19, 30), (0, 32), (-19, 30), (-17, 6), (-14, -18)], 8)
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(sx + x * ca - y * sa, sy + x * sa + y * ca) for x, y in sleeve]
        sid = f"slv{sgn + 1}"
        shade = [(4, -30), (30, -30), (30, 40), (8, 40)] if sgn > 0 else [(-30, -30), (-24, -30), (-22, 40), (-30, 40)]
        shade = [(sx + x * ca - y * sa, sy + x * sa + y * ca) for x, y in shade]
        out.append(f'<clipPath id="{sid}"><path d="{poly_path(pts)}"/></clipPath>')
        out.append(f'<path d="{poly_path(pts)}" fill="{SHIRT}"/>')
        out.append(f'<path clip-path="url(#{sid})" d="{poly_path(shade)}" fill="{SHIRT_SH}"/>')
        out.append(f'<path d="{poly_path(pts)}" fill="none" stroke="{INK}" stroke-width="5.6" stroke-linejoin="round"/>')
    return "".join(out)


def neck():
    return taper([(0, 92), (0, 100), (0, HEAD_TO_TORSO - 141 + 2)], 6.4, 6.6, 6.4)


def head(expr_name):
    e, m, mark = EXPRESSIONS[expr_name]
    out = [f'<circle cx="0" cy="0" r="100" fill="{SKIN}"/>']
    out.append(eye(-1, e))
    out.append(eye(1, e))
    out.append(mouth(m))
    out.append(f'<circle cx="0" cy="0" r="100" fill="none" stroke="{INK}" stroke-width="6.4"/>')
    if mark == "?":
        out.append(f'<text x="82" y="-92" font-family="Arial Rounded MT Bold, Nunito, Arial, sans-serif" font-weight="900" '
                   f'font-size="62" fill="{INK}" transform="rotate(12 96 -110)">?</text>')
    elif mark == "!!":
        out.append(f'<g transform="translate(86 -150) rotate(14)">'
                   + taper([(0, 0), (-2, 28)], 9, 8, 5) + f'<circle cx="-3" cy="42" r="5" fill="{INK}"/>'
                   + taper([(18, 2), (16, 30)], 9, 8, 5) + f'<circle cx="15" cy="44" r="5" fill="{INK}"/></g>')
    return "".join(out)


def bust(expr_name, clip_bottom=230):
    _uid[0] += 1
    cid = f"bust{_uid[0]}"
    return (f'<clipPath id="{cid}"><rect x="-170" y="-260" width="340" height="{260 + clip_bottom}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{tshirt_bust()}{neck()}{head(expr_name)}</g>')


# ------------------------------------------------------------------ sheet layout
FONT = "'Nunito', 'Arial Rounded MT Bold', Arial, sans-serif"


def label(cx, y, text, w=200):
    return (f'<rect x="{cx - w / 2}" y="{y}" width="{w}" height="46" rx="23" fill="#ECECEF"/>'
            f'<text x="{cx}" y="{y + 32}" text-anchor="middle" font-family="{FONT}" font-weight="700" font-size="25" fill="#2A2A30">{text}</text>')


def build_svg():
    W, H = 2400, 1500
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             '<style>@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&amp;display=swap");</style>',
             f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    # header
    parts.append(f'<rect x="40" y="34" width="560" height="62" rx="31" fill="#2E3140"/>'
                 f'<text x="70" y="77" font-family="{FONT}" font-weight="900" font-size="32" fill="#FFF" letter-spacing="1">RIAN — EXPRESSION SHEET</text>')
    parts.append(f'<text x="625" y="76" font-family="{FONT}" font-weight="700" font-size="24" fill="#8A8A96">'
                 f'Revisi v2 · TEST · menunggu persetujuan pemilik</text>')
    parts.append(f'<line x1="40" y1="122" x2="{W - 40}" y2="122" stroke="#DADAE0" stroke-width="3"/>')
    # hero (base identity)
    parts.append(f'<rect x="40" y="150" width="610" height="1310" rx="28" fill="#F6F6F8"/>')
    parts.append(f'<text x="345" y="210" text-anchor="middle" font-family="{FONT}" font-weight="900" font-size="30" fill="#2E3140">EKSPRESI DASAR</text>')
    parts.append(f'<g transform="translate(345 640) scale(2.25)">{bust("Neutral", clip_bottom=215)}</g>')
    parts.append(label(345, 1180, "Neutral / Deadpan", 300))
    notes = ["Kelopak atas tebal menutup ~½ mata",
             "Pupil tertahan di bawah kelopak",
             "Alis lebih tipis dari kelopak, datar",
             "Mulut garis pendek, sedikit miring"]
    for k, t in enumerate(notes):
        parts.append(f'<text x="90" y="{1268 + k * 44}" font-family="{FONT}" font-weight="700" font-size="23" fill="#5A5A66">• {t}</text>')
    # grid 5 x 2
    names = list(EXPRESSIONS)
    gx0, gy0, cw, ch = 690, 150, 334, 655
    for idx, n in enumerate(names):
        r, c = divmod(idx, 5)
        cx = gx0 + c * cw + cw / 2
        cy = gy0 + r * ch
        parts.append(f'<rect x="{gx0 + c * cw + 8}" y="{cy}" width="{cw - 16}" height="{ch - 20}" rx="24" fill="#F6F6F8"/>')
        parts.append(f'<g transform="translate({cx} {cy + 295}) scale(1.28)">{bust(n, clip_bottom=185)}</g>')
        parts.append(label(cx, cy + 560, n, 210))
    parts.append("</svg>")
    return "\n".join(parts)


def build_compare_svg():
    """Before (current rig head, rendered separately) is placed by render step; this is the 'after' strip."""
    names = list(EXPRESSIONS)
    W, H = 260 * len(names), 300
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
             f'<rect width="{W}" height="{H}" fill="#FFF"/>']
    for i, n in enumerate(names):
        parts.append(f'<g transform="translate({130 + i * 260} 150) scale(1.15)">{head(n)}</g>')
    parts.append("</svg>")
    return "\n".join(parts)


def render(svg_path, png_path, w, h, scale=1):
    import subprocess
    js = ("const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();"
          f"const p=await b.newPage({{viewport:{{width:{w},height:{h}}},deviceScaleFactor:{scale}}});"
          f"await p.goto('{svg_path.as_uri()}');await p.waitForTimeout(800);"
          f"await p.screenshot({{path:'{png_path}'}});await b.close();}})();")
    subprocess.run(["node", "-e", js], check=True)


if __name__ == "__main__":
    svg = HERE / "rian_expression_sheet_v2_TEST.svg"
    svg.write_text(build_svg())
    render(svg, HERE / "rian_expression_sheet_v2_TEST.png", 2400, 1500)
    strip = HERE / "rian_heads_v2_strip_TEST.svg"
    strip.write_text(build_compare_svg())
    render(strip, HERE / "rian_heads_v2_strip_TEST.png", 2600, 300)
    print("ok")
