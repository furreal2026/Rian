"""Curious Mind — master character draft V2 (ink-style SVG illustration).

Method (replaces the flat-geometry V1 generator):
- Every line is an ink stroke: a centreline through key points, smoothed with
  Catmull-Rom splines, then expanded to a filled shape with a width profile
  (tapered ends, thicker on the shadow side). No constant-width primitives.
- The head is an organic closed curve (slightly fuller cranium, softer jaw),
  outlined with a ring whose weight grows toward the lower right.
- Eyes are built from an upper-lid curve and a lower curve; the pupil is
  clipped by the lid, which gives the heavy, half-lidded look.
- The shirt is drawn from the stick skeleton (neck, shoulders, arm angle,
  hip), with sleeve openings, fold strokes and a shadow side.

All views and expressions share one geometry, so identity stays fixed.
Usage:  python3 generate_v2.py <output_dir>
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

INK = "#1D1D21"
SKIN = "#FFFFFF"
SHIRT = "#D9463F"
SHIRT_SHADE = "#B8352F"
SHIRT_FOLD = "#9E2B27"
MOUTH = "#6E2020"
BAG = "#BDBDC3"
GROUND = "#ECECEF"
LABEL_BG = "#2B2F3A"
FONT = "Inter, DejaVu Sans, sans-serif"

_uid = [0]


def uid(p):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


# ------------------------------------------------------------------ geometry

def cr(pts, closed=False, n=18):
    """Catmull-Rom spline through key points -> dense polyline."""
    P = np.asarray(pts, float)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([P[0], P, P[-1]])
    out = []
    t = np.linspace(0, 1, n, endpoint=False)[:, None]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        out.append(P[-2][None])
    return np.vstack(out)


def cubic(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.asarray, (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def _normals(P, closed=False):
    if closed:
        tang = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else:
        tang = np.gradient(P, axis=0)
    tang /= np.linalg.norm(tang, axis=1)[:, None] + 1e-9
    return tang, np.c_[-tang[:, 1], tang[:, 0]]


def _smooth(x):
    return x * x * (3 - 2 * x)


def d_of(P, close=True):
    s = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in P)
    return s + (" Z" if close else "")


def ink(P, w, t0=0.25, t1=0.25, mn=0.3, mn1=None, color=INK, extra=""):
    """Tapered ink stroke along polyline P."""
    P = np.asarray(P, float)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    s = s / s[-1]
    tang, nrm = _normals(P)
    wp = np.full(len(P), float(w))
    mn1 = mn if mn1 is None else mn1
    if t0 > 0:
        wp *= mn + (1 - mn) * _smooth(np.clip(s / t0, 0, 1))
    if t1 > 0:
        wp *= mn1 + (1 - mn1) * _smooth(np.clip((1 - s) / t1, 0, 1))
    L = P + nrm * wp[:, None] / 2
    R_ = P - nrm * wp[:, None] / 2

    def cap(c, n_, r, start):
        a0 = math.atan2(n_[1], n_[0])
        angs = np.linspace(a0 + math.pi, a0, 10) if start else np.linspace(a0, a0 - math.pi, 10)
        return c + r * np.c_[np.cos(angs), np.sin(angs)]

    poly = np.vstack([L, cap(P[-1], nrm[-1], wp[-1] / 2, False), R_[::-1], cap(P[0], nrm[0], wp[0] / 2, True)])
    return f'<path d="{d_of(poly)}" fill="{color}" {extra}/>'


def ring(P, w, color=INK, light=(1, 1), vary=0.45):
    """Closed ink outline, heavier on the side facing `light` (shadow side)."""
    P = np.asarray(P, float)
    _, nrm = _normals(P, closed=True)
    c = P.mean(0)
    dirs = P - c
    dirs /= np.linalg.norm(dirs, axis=1)[:, None] + 1e-9
    lv = np.asarray(light, float) / np.linalg.norm(light)
    k = (dirs @ lv + 1) / 2
    wp = w * (1 - vary / 2 + vary * k)
    outer = P + nrm * wp[:, None] / 2
    inner = P - nrm * wp[:, None] / 2
    return f'<path d="{d_of(outer)} {d_of(inner)}" fill="{color}" fill-rule="evenodd"/>'


def fill(P, color, extra=""):
    return f'<path d="{d_of(P)}" fill="{color}" {extra}/>'


# ------------------------------------------------------------------ head

def head_outline():
    th = np.linspace(0, 2 * np.pi, 220, endpoint=False)
    x = 100 * np.cos(th)
    y = 97 * np.sin(th)
    low = np.clip(np.sin(th), 0, None)
    x = x * (1 - 0.07 * low ** 2)
    y = y * (1 + 0.025 * low)
    up = np.clip(-np.sin(th), 0, None)
    x = x * (1 + 0.02 * up)
    return np.c_[x, y]


HEAD = head_outline()


def head_base():
    return fill(HEAD, SKIN) + ring(HEAD, 6.4)


# ------------------------------------------------------------------ face parts

def _xf(P, cx, cy, ang):
    a = math.radians(ang)
    R_ = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return P @ R_.T + [cx, cy]


def eye(cx, cy, w=54, arch=3, depth=21, tilt=0, side="L", p=(0.3, 7), pr=11, bag=0.0, hl=True):
    """Upper lid curve + lower curve. arch: lid bulge (low = heavy lid).
    tilt > 0 lowers the inner corner (annoyed/angry); < 0 raises it (worried)."""
    hw = w / 2
    lid = cubic((-hw, 0), (-hw * 0.5, -arch * 1.33), (hw * 0.5, -arch * 1.33), (hw, 0))
    low = cubic((hw, 0), (hw * 0.95, depth * 1.32), (-hw * 0.95, depth * 1.32), (-hw, 0))
    ang = tilt if side == "L" else -tilt
    lid_w, low_w = _xf(lid, cx, cy, ang), _xf(low, cx, cy, ang)
    shape = np.vstack([lid_w, low_w[1:-1]])
    clip = uid("eye")
    out = [f'<clipPath id="{clip}"><path d="{d_of(shape)}"/></clipPath>', fill(shape, SKIN)]
    pc = _xf(np.array([[p[0] * hw * 0.62, p[1]]]), cx, cy, ang)[0]
    out.append(f'<g clip-path="url(#{clip})"><circle cx="{pc[0]:.2f}" cy="{pc[1]:.2f}" r="{pr}" fill="{INK}"/>')
    if hl:
        out.append(f'<circle cx="{pc[0] - pr * 0.38:.2f}" cy="{pc[1] + pr * 0.05:.2f}" r="{pr * 0.24:.2f}" fill="#FFFFFF"/>')
    out.append("</g>")
    out.append(ink(low_w, 3.4, 0.35, 0.35, 0.15))
    over = _xf(cubic((-hw + 1, -1), (-hw * 0.5, -arch * 1.33 - 2), (hw * 0.5, -arch * 1.33 - 2), (hw - 1, -1)), cx, cy, ang)
    # heavier toward the outer corner of each eye
    t0, t1 = (0.22, 0.14) if side == "L" else (0.14, 0.22)
    out.append(ink(over, 11, t0, t1, 0.55))
    if bag > 0:
        b = _xf(cubic((-hw * 0.6, depth + 6), (-hw * 0.2, depth + 11), (hw * 0.3, depth + 11), (hw * 0.65, depth + 5)), cx, cy, ang)
        out.append(ink(b, 3.2, 0.4, 0.4, 0.1, color=BAG, extra=f'opacity="{bag}"'))
    return "".join(out)


def brow(outer, inner, arch=0, w=9.5):
    mid = ((outer[0] + inner[0]) / 2, (outer[1] + inner[1]) / 2 - arch)
    P = cr([outer, mid, inner], n=24)
    return ink(P, w, 0.55, 0.0, 0.3)


def mouth(pts, w=4.4):
    pts = [(3 + (x - 3) * 1.3, y) for x, y in pts]
    return ink(cr(pts, n=16), w, 0.4, 0.4, 0.25)


def mouth_open(pts, teeth=None):
    P = cr(pts, closed=True, n=16)
    out = fill(P, MOUTH)
    if teeth:
        T = cr(teeth, closed=True, n=12)
        clip = uid("m")
        out += f'<clipPath id="{clip}"><path d="{d_of(P)}"/></clipPath><g clip-path="url(#{clip})">{fill(T, "#FFFFFF")}</g>'
    return out + ring(P, 4.4, vary=0.3)


LE = (-36, -2)
RE = (34, -4)


def eyes(L=None, R=None):
    L = {**dict(w=58), **(L or {})}
    R = {**dict(w=54), **(R or {})}
    return eye(*LE, side="L", **L) + eye(*RE, side="R", **R)


EXPR = {
    "deadpan": dict(
        label="Neutral / Deadpan",
        eyes=eyes(dict(bag=0.55, p=(0.3, 5)), dict(bag=0.55, p=(0.3, 5))),
        brows=brow((-62, -30), (-14, -28), 1.5) + brow((60, -32), (12, -30), 1.5),
        mouth=mouth([(-7, 52), (3, 51.6), (13, 50.6)]),
    ),
    "skeptical": dict(
        label="Skeptical",
        eyes=eyes(dict(arch=1, depth=16, tilt=3, bag=0.5), dict(arch=9, depth=22, p=(0.3, 6), bag=0.4)),
        brows=brow((-62, -26), (-14, -23), 0.5) + brow((60, -47), (12, -37), 9),
        mouth=mouth([(-9, 54), (2, 52.5), (13, 48)]),
    ),
    "annoyed": dict(
        label="Annoyed",
        eyes=eyes(dict(arch=2, depth=18, tilt=9, p=(0.25, 7), bag=0.5), dict(arch=2, depth=18, tilt=9, p=(0.25, 7), bag=0.5)),
        brows=brow((-63, -37), (-14, -24), 0) + brow((61, -39), (12, -26), 0),
        mouth=mouth([(-9, 55.5), (2, 51.5), (13, 55)]),
    ),
    "exhausted": dict(
        label="Exhausted",
        eyes=eyes(dict(arch=-3, depth=15, p=(0.05, 8), pr=10, bag=1.0), dict(arch=-3, depth=15, p=(0.05, 8), pr=10, bag=1.0)),
        brows=brow((-62, -23), (-14, -30), 0) + brow((60, -24), (12, -31), 0),
        mouth=mouth([(-10, 55), (2, 55.6), (14, 56.4)]),
    ),
    "confused": dict(
        label="Confused",
        eyes=eyes(dict(arch=19, depth=20, p=(0.35, -3), pr=10), dict(arch=21, depth=20, p=(0.4, -4), pr=10)),
        brows=brow((-60, -36), (-14, -34), 1) + brow((58, -49), (12, -45), 8),
        mouth=mouth([(-10, 55), (-4, 52), (2, 55), (8, 57), (14, 54)]),
        mark="?",
    ),
    "shocked": dict(
        label="Shocked",
        eyes=eyes(dict(arch=25, depth=25, w=56, p=(0, 2), pr=7), dict(arch=25, depth=25, w=52, p=(0, 2), pr=7)),
        brows=brow((-60, -50), (-16, -53), 7) + brow((58, -50), (14, -53), 7),
        mouth=mouth_open([(3, 47), (14, 54), (14, 70), (3, 77), (-8, 70), (-8, 54)]),
        mark="!!",
    ),
    "angry": dict(
        label="Angry",
        eyes=eyes(dict(arch=1, depth=18, tilt=16, p=(0.15, 7)), dict(arch=1, depth=18, tilt=16, p=(0.15, 7))),
        brows=brow((-64, -41), (-12, -20), -2, w=11) + brow((62, -41), (10, -20), -2, w=11),
        mouth=mouth_open([(-16, 59), (2, 51), (20, 59), (16, 71), (2, 75), (-12, 71)],
                         teeth=[(-16, 58), (2, 50), (20, 58), (18, 62), (2, 56), (-14, 62)]),
    ),
    "disgusted": dict(
        label="Disgusted",
        eyes=eyes(dict(arch=0, depth=15, tilt=6, p=(0.35, 7), bag=0.5), dict(arch=4, depth=19, p=(0.35, 7), bag=0.4)),
        brows=brow((-62, -30), (-14, -22), 0) + brow((60, -38), (12, -34), 3),
        mouth=mouth([(-10, 57), (-3, 52), (5, 55), (11, 58), (16, 62)]),
    ),
    "worried": dict(
        label="Worried",
        eyes=eyes(dict(arch=14, depth=21, tilt=-8, p=(0.45, 3), pr=10), dict(arch=14, depth=21, tilt=-8, p=(0.45, 3), pr=10)),
        brows=brow((-62, -29), (-16, -42), 0) + brow((60, -29), (14, -42), 0),
        mouth=mouth([(-10, 58), (-3, 53), (5, 56), (11, 58), (14, 57)]),
    ),
    "smug": dict(
        label="Smug",
        eyes=eyes(dict(arch=0, depth=18, p=(0.35, 7), bag=0.4), dict(arch=0, depth=18, p=(0.35, 7), bag=0.4)),
        brows=brow((-62, -30), (-14, -29), 1) + brow((60, -40), (12, -34), 4),
        mouth=mouth([(-12, 52), (-2, 55), (8, 53), (15, 47)]),
    ),
}


def face(name):
    e = EXPR[name]
    return e["eyes"] + e["brows"] + e["mouth"]


def head(name="deadpan", blank=False):
    return head_base() + ("" if blank else face(name))


def mark(sym):
    if not sym:
        return ""
    return (f'<text x="98" y="-90" font-family="{FONT}" font-weight="800" font-size="60" fill="{INK}" '
            f'text-anchor="middle">{sym}</text>')


# ------------------------------------------------------------------ body (front)
# Stick skeleton (head radius = 100): neck (0,102), shoulders (±40,114),
# hip (0,236), hands (±72,282), feet (±27,448).

def limb(pts, w=6.6):
    return ink(cr(pts, n=20), w, 0.06, 0.06, 0.8)


def hand(x, y, flip=1):
    th = np.linspace(0, 2 * np.pi, 80, endpoint=False)
    P = np.c_[x + 11.5 * np.cos(th), y + 12.5 * np.sin(th)]
    return fill(P, SKIN) + ring(P, 5.4, vary=0.5)


def foot(x, y, d):
    return ink(cr([(x, y - 4), (x + d * 9, y + 1), (x + d * 21, y + 3)], n=12), 10.5, 0.05, 0.35, 0.9, mn1=0.62)


def shadow(rx=88):
    return f'<ellipse cx="0" cy="456" rx="{rx}" ry="8.5" fill="{GROUND}"/>'


SHIRT_KEYS = [
    (-17, 96), (-8, 100), (0, 101), (8, 100), (17, 96),           # neckline (hidden under head)
    (32, 104), (44, 111), (54, 124), (63, 145), (70, 166),         # shoulder -> sleeve top
    (66, 171), (56, 177),                                          # sleeve opening
    (49, 160), (46, 150),                                          # armpit
    (45, 175), (45.5, 205), (47, 236),                             # side seam
    (24, 240), (0, 241.5), (-24, 240),                             # hem
    (-47, 236), (-45.5, 205), (-45, 175),
    (-46, 150), (-49, 160),
    (-56, 177), (-66, 171),
    (-70, 166), (-63, 145), (-54, 124), (-44, 111), (-32, 104),
]


def shirt_front(back=False):
    keys = list(SHIRT_KEYS)
    if back:
        pass
    P = cr(keys, closed=True, n=10)
    clip = uid("shirt")
    out = [f'<clipPath id="{clip}"><path d="{d_of(P)}"/></clipPath>', fill(P, SHIRT)]
    shade = cr([(22, 96), (40, 112), (52, 140), (40, 160), (30, 200), (34, 250), (90, 250), (90, 96)], closed=True, n=10)
    out.append(f'<g clip-path="url(#{clip})">{fill(shade, SHIRT_SHADE, "opacity=\"0.55\"")}')
    # sleeve underside shade
    out.append(fill(cr([(46, 150), (60, 158), (68, 170), (56, 178), (48, 162)], closed=True, n=8), SHIRT_SHADE))
    out.append(fill(cr([(-46, 150), (-60, 158), (-68, 170), (-56, 178), (-48, 162)], closed=True, n=8), SHIRT_SHADE, 'opacity="0.6"'))
    out.append("</g>")
    # folds
    out.append(ink(cr([(42, 154), (36, 168), (31, 186)]), 3.2, 0.2, 0.5, 0.15, color=SHIRT_FOLD))
    out.append(ink(cr([(-42, 156), (-37, 170), (-33, 184)]), 3.0, 0.2, 0.5, 0.15, color=SHIRT_FOLD))
    out.append(ink(cr([(12, 238), (15, 226), (20, 218)]), 2.6, 0.2, 0.6, 0.15, color=SHIRT_FOLD))
    out.append(ink(cr([(-22, 238), (-24, 229)]), 2.4, 0.2, 0.6, 0.15, color=SHIRT_FOLD))
    out.append(ring(P, 5.2, vary=0.5))
    return "".join(out)


def body_front(back=False):
    out = shadow()
    out += limb([(-17, 232), (-21, 340), (-27, 446)]) + limb([(17, 232), (20, 340), (27, 446)])
    out += foot(-27, 448, -1) + foot(27, 448, 1)
    out += limb([(-58, 168), (-64, 222), (-71, 272)]) + limb([(58, 168), (65, 222), (72, 272)])
    out += shirt_front(back)
    out += hand(-72, 282) + hand(73, 282)
    return out


COLLAR = ink(cr([(-26, 96), (-13, 103.5), (0, 105), (13, 103.5), (26, 96)]), 5, 0.3, 0.3, 0.3, color=SHIRT_FOLD)


def figure_front(name="deadpan"):
    return body_front() + head(name) + COLLAR


def figure_back():
    return body_front(back=True) + head(blank=True)


def figure_side():
    out = shadow(72)
    out += limb([(-4, 232), (-5, 340), (-6, 446)]) + limb([(6, 232), (7, 340), (8, 446)])
    out += foot(-6, 448, 1) + foot(8, 448, 1)
    body = cr([(-20, 100), (16, 99), (28, 110), (31, 150), (30, 200), (31, 240), (0, 242), (-30, 240),
               (-30, 200), (-31, 150), (-29, 112)], closed=True, n=10)
    clip = uid("side")
    out += f'<clipPath id="{clip}"><path d="{d_of(body)}"/></clipPath>' + fill(body, SHIRT)
    out += f'<g clip-path="url(#{clip})">' + fill(cr([(8, 96), (40, 96), (40, 250), (12, 250), (18, 180)], closed=True, n=8), SHIRT_SHADE, 'opacity="0.55"') + "</g>"
    out += ring(body, 5.2, vary=0.5)
    out += limb([(4, 175), (6, 228), (9, 272)])
    sleeve = cr([(-10, 112), (12, 108), (20, 140), (17, 174), (-5, 177), (-11, 146)], closed=True, n=10)
    out += fill(sleeve, SHIRT) + ink(cr([(-2, 150), (6, 172)]), 2.6, 0.3, 0.5, 0.15, color=SHIRT_FOLD) + ring(sleeve, 4.8, vary=0.5)
    out += hand(9, 282)
    out += head_base()
    out += eye(66, -4, w=26, arch=3, depth=20, p=(0.55, 7), pr=10, side="R", bag=0.5)
    out += brow((84, -32), (52, -30), 1)
    out += ink(cr([(68, 52), (77, 51.6), (86, 50.4)], n=16), 4.4, 0.4, 0.4, 0.25)
    return out


# ------------------------------------------------------------------ sheets

def g(x, y, s, inner):
    return f'<g transform="translate({x},{y}) scale({s})">{inner}</g>'


def pill(x, y, text, size=30):
    w = len(text) * size * 0.6 + 48
    return (f'<rect x="{x - w / 2}" y="{y - size}" width="{w}" height="{size * 1.55}" rx="{size * 0.77}" fill="#ECECEF"/>'
            f'<text x="{x}" y="{y + size * 0.08}" font-family="{FONT}" font-weight="700" font-size="{size}" '
            f'fill="{INK}" text-anchor="middle">{text}</text>')


def header(x, y, text, line_to):
    w = len(text) * 22 + 60
    return (f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="29" fill="{LABEL_BG}"/>'
            f'<text x="{x + w / 2}" y="{y + 41}" font-family="{FONT}" font-weight="800" font-size="32" '
            f'fill="#FFFFFF" text-anchor="middle" letter-spacing="1">{text}</text>'
            f'<line x1="{x + w + 16}" y1="{y + 29}" x2="{line_to}" y2="{y + 29}" stroke="#D2D2D7" stroke-width="3"/>')


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}</svg>')


def title(w, text):
    return (f'<text x="60" y="80" font-family="{FONT}" font-weight="800" font-size="46" fill="{INK}">{text}</text>'
            f'<text x="{w - 50}" y="72" font-family="{FONT}" font-weight="700" font-size="28" fill="#A8A8AF" '
            f'text-anchor="end">DRAFT V2 · menunggu persetujuan</text>')


def master_sheet():
    W, H = 2600, 1500
    b = title(W, "CURIOUS MIND — MASTER CHARACTER V1.0")
    b += header(60, 130, "MAIN CHARACTER", 760)
    s, ox, oy = 1.45, 420, 420
    for gy, lbl in [(-100, "puncak kepala"), (99, "dagu · 1 kepala"), (241, "ujung baju"), (282, "tangan"), (452, "telapak kaki")]:
        y = oy + gy * s
        b += f'<line x1="110" y1="{y}" x2="640" y2="{y}" stroke="#DCDCE0" stroke-width="2" stroke-dasharray="10 8"/>'
        b += f'<text x="650" y="{y + 8}" font-family="{FONT}" font-size="22" fill="#8A8A92">{lbl}</text>'
    b += g(ox, oy, s, figure_front())
    b += (f'<text x="420" y="1165" font-family="{FONT}" font-size="24" fill="#6A6A72" text-anchor="middle">'
          f'Tinggi total ≈ 2,8 diameter kepala · kepala ≈ 36% tinggi</text>')

    b += header(860, 130, "TURNAROUND", 1560)
    for i, (fig, lbl) in enumerate([(figure_front(), "Front"), (figure_side(), "Side"), (figure_back(), "Back")]):
        x = 980 + i * 240
        b += g(x, 380, 0.95, fig)
        b += pill(x, 860, lbl)

    b += header(1660, 130, "PALETTE", 2540)
    sw = [(INK, "Garis tinta", INK), (SKIN, "Kepala &amp; tangan", SKIN), (SHIRT, "Kaos merah (casual)", SHIRT),
          (SHIRT_SHADE, "Bayangan kaos", SHIRT_SHADE), (SHIRT_FOLD, "Lipatan / kerah", SHIRT_FOLD), (MOUTH, "Dalam mulut", MOUTH)]
    for i, (c, name, hexv) in enumerate(sw):
        y = 225 + i * 100
        b += f'<rect x="1680" y="{y}" width="76" height="76" rx="14" fill="{c}" stroke="{INK}" stroke-width="3"/>'
        b += f'<text x="1786" y="{y + 33}" font-family="{FONT}" font-weight="700" font-size="28" fill="{INK}">{name}</text>'
        b += f'<text x="1786" y="{y + 66}" font-family="{FONT}" font-size="24" fill="#6A6A72">{hexv}</text>'

    b += header(860, 960, "ATURAN IDENTITAS", 2540)
    rules = [
        "Kepala bulat organik, putih, tanpa rambut. Wajah dewasa, deadpan, sedikit lelah.",
        "Kelopak atas tebal meruncing = ciri utama; pupil terpotong kelopak (half-lidded).",
        "Posisi mata, alis, mulut tetap; ekspresi hanya mengubah kelopak, pupil, alis, mulut.",
        "Garis tinta halus dengan ujung meruncing; lebih tebal di sisi bayangan (kanan bawah).",
        "Badan stickman; baju mengikuti bahu, lengan, dan pinggul. Tanpa celana &amp; sepatu.",
        "Senyum bukan ekspresi default. Hindari kesan ceria atau kekanak-kanakan.",
    ]
    for i, t in enumerate(rules):
        y = 1065 + i * 62
        b += f'<circle cx="890" cy="{y - 9}" r="7" fill="{SHIRT}"/>'
        b += f'<text x="912" y="{y}" font-family="{FONT}" font-size="28" fill="{INK}">{t}</text>'
    return svg(W, H, b)


def bust(name):
    clip = uid("bust")
    return (f'<clipPath id="{clip}"><rect x="-160" y="-170" width="320" height="345"/></clipPath>'
            f'<g clip-path="url(#{clip})">{body_front()}{head(name)}{COLLAR}{mark(EXPR[name].get("mark"))}</g>')


def expression_sheet():
    W, H = 2200, 1260
    b = title(W, "CURIOUS MIND — CORE EXPRESSIONS")
    b += header(60, 120, "EXPRESSIONS", 2140)
    for i, name in enumerate(EXPR):
        col, row = i % 5, i // 5
        x, y = 250 + col * 425, 400 + row * 500
        b += g(x, y, 1.15, bust(name))
        b += pill(x, y + 250, EXPR[name]["label"])
    return svg(W, H, b)


def closeup():
    """Large face study so line quality can be judged."""
    W, H = 1400, 900
    b = title(W, "FACE STUDY — DEADPAN")
    clip = uid("cu")
    b += (f'<clipPath id="{clip}"><rect x="-150" y="-130" width="300" height="270"/></clipPath>'
          f'<g transform="translate(700,470) scale(3)"><g clip-path="url(#{clip})">{body_front()}{head("deadpan")}{COLLAR}</g></g>')
    return svg(W, H, b)


def write(out_dir, stem, content):
    svg_path = out_dir / f"{stem}.svg"
    svg_path.write_text(content)
    subprocess.run(["rsvg-convert", "-o", str(out_dir / f"{stem}.png"), str(svg_path)], check=True)
    svg_path.unlink()
    print(out_dir / f"{stem}.png")


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    write(out, "stick_figure_master_sheet_draft_v2", master_sheet())
    write(out, "expressions_sheet_draft_v2", expression_sheet())
    write(out, "face_study_draft_v2", closeup())
