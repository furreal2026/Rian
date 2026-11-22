"""TEST — Rian outfit variations (Casual / Police / Hoodie), full body front, Neutral face.

Same head, proportions and joint positions as the rig (stick_figure_rig.json, front view) and the
v2 expression sheet. Does NOT touch production assets.

    python output/character_revision_v2_TEST/build_outfits.py
"""
from __future__ import annotations

import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_sheet as B  # noqa: E402
from build_sheet import INK, SKIN, catmull, poly_path, taper, f  # noqa: E402

OY = B.HEAD_TO_TORSO  # hips y (head centre = 0)

OUTFITS = {
    "casual": dict(main=B.SHIRT, shade=B.SHIRT_SH, fold=B.FOLD),
    "police": dict(main="#2F5FB3", shade="#244C94", fold="#183669"),
    "hoodie": dict(main="#34353D", shade="#26272D", fold="#17181C"),
}
GOLD, GOLD_SH = "#E9B92F", "#C99A1C"


def uid(p):
    B._uid[0] += 1
    return f"{p}{B._uid[0]}"


def rot(v, deg):
    a = math.radians(deg)
    return (-math.sin(a) * v, math.cos(a) * v)


def T(pts, sx=1.0):
    return [(x * sx, y + OY) for x, y in pts]


# ------------------------------------------------------------------ skeleton (rig front view)
def arm_points(sgn):
    s = (sgn * 52, -104 + OY)
    r_sh, r_el = (12, -8) if sgn < 0 else (-12, 8)
    d1 = rot(64, r_sh)
    e = (s[0] + d1[0], s[1] + d1[1])
    d2 = rot(64, r_sh + r_el)
    w = (e[0] + d2[0], e[1] + d2[1])
    d3 = rot(11, r_sh + r_el)
    h = (w[0] + d3[0], w[1] + d3[1])
    return s, e, w, h, r_sh


def legs():
    out = []
    for sgn in (-1, 1):
        hip = (sgn * 20, OY)
        r1, r2 = (3, -2) if sgn < 0 else (-3, 2)
        d1 = rot(107, r1)
        k = (hip[0] + d1[0], hip[1] + d1[1])
        d2 = rot(104, r1 + r2)
        a = (k[0] + d2[0], k[1] + d2[1])
        out.append(taper([hip, ((hip[0] + k[0]) / 2 + 0.6, (hip[1] + k[1]) / 2), k], 6.9, 6.8, 6.6))
        out.append(taper([k, ((k[0] + a[0]) / 2 + 0.6, (k[1] + a[1]) / 2), a], 6.6, 6.6, 6.1))
        d = sgn
        foot = [(a[0], a[1] - 1), (a[0] + d * 7, a[1] + 2.6), (a[0] + d * 15, a[1] + 3.6), (a[0] + d * 20, a[1] + 3.0)]
        out.append(taper(foot, 6.8, 9.0, 6.2))
    return "".join(out)


def shadow():
    g = OY + 211 + 3
    return (f'<ellipse cx="0" cy="{g}" rx="96" ry="11" fill="#000" fill-opacity="0.12"/>'
            f'<ellipse cx="0" cy="{g}" rx="64" ry="7" fill="#000" fill-opacity="0.08"/>')


def bare_arm(sgn, from_elbow=False, cuff=None):
    s, e, w, h, _ = arm_points(sgn)
    out = []
    if not from_elbow:
        out.append(taper([s, ((s[0] + e[0]) / 2 + 0.5, (s[1] + e[1]) / 2), e], 6.6, 6.6, 6.5))
    start = cuff or e
    out.append(taper([start, ((start[0] + w[0]) / 2 + 0.5, (start[1] + w[1]) / 2), w], 6.5, 6.5, 6.1))
    out.append(f'<circle cx="{f(h[0])}" cy="{f(h[1])}" r="11.5" fill="{SKIN}" stroke="{INK}" stroke-width="4.8"/>')
    return "".join(out)


# ------------------------------------------------------------------ garments
def torso_path(sx=1.0, hem=0.0):
    pts = [(-26, -149), (-12, -143), (0, -141), (12, -143), (26, -149), (46, -145), (57, -131), (58, -112),
           (52, -92), (50, -50), (53, -3 + hem), (0, 0 + hem), (-53, -3 + hem), (-50, -50), (-52, -92), (-58, -112), (-57, -131), (-46, -145)]
    p = T(pts, sx)
    return catmull(p + [p[0]], 8)


def filled(path_pts, c, shade_poly=None, inner=""):
    cid = uid("clip")
    s = [f'<clipPath id="{cid}"><path d="{poly_path(path_pts)}"/></clipPath>',
         f'<path d="{poly_path(path_pts)}" fill="{c["main"]}"/>']
    if shade_poly:
        s.append(f'<path clip-path="url(#{cid})" d="{poly_path(shade_poly)}" fill="{c["shade"]}"/>')
    if inner:
        s.append(f'<g clip-path="url(#{cid})">{inner}</g>')
    s.append(f'<path d="{poly_path(path_pts)}" fill="none" stroke="{INK}" stroke-width="5.6" stroke-linejoin="round"/>')
    return "".join(s)


def short_sleeve(sgn, c, extra=""):
    s, *_ = arm_points(sgn)
    r = 12 if sgn < 0 else -12
    a = math.radians(r)
    ca, sa = math.cos(a), math.sin(a)
    R = lambda pts: [(s[0] + x * ca - y * sa, s[1] + x * sa + y * ca) for x, y in pts]
    sleeve = R(catmull([(-14, -18), (0, -21), (14, -18), (17, 6), (19, 30), (0, 32), (-19, 30), (-17, 6), (-14, -18)], 8))
    shade = R([(4, -30), (30, -30), (30, 40), (8, 40)] if sgn > 0 else [(-30, -30), (-24, -30), (-22, 40), (-30, 40)])
    hem = R([(-18, 24), (0, 26), (18, 24)])
    inner = taper(hem, 1.0, 2.4, 1.0, color=c["fold"]) + (extra and extra(R) or "")
    return filled(sleeve, c, shade, inner)


def long_sleeve(sgn, c):
    s, e, w, h, _ = arm_points(sgn)
    cuff_at = (w[0] + (e[0] - w[0]) * 0.17, w[1] + (e[1] - w[1]) * 0.17)
    pts = [(s[0], s[1] - 12), s, ((s[0] + e[0]) / 2, (s[1] + e[1]) / 2), e, cuff_at]
    body = taper(pts, 30, 31, 24, color=INK, power=0.25)
    fill_ = taper(pts, 24.5, 25.5, 18.5, color=c["main"], power=0.25)
    # shade on the outer side
    off = sgn * 5
    shade = taper([(x + off, y) for x, y in pts], 10, 11, 8, color=c["shade"], power=0.25)
    cid = uid("ls")
    clip = f'<clipPath id="{cid}">{fill_.replace(c["main"], "#fff")}</clipPath>'
    # ribbed cuff
    d = (w[0] - e[0], w[1] - e[1])
    n = math.hypot(*d)
    ux, uy = d[0] / n, d[1] / n
    px, py = -uy, ux
    cx_, cy_ = cuff_at[0] - ux * 8, cuff_at[1] - uy * 8
    cuff_line = taper([(cx_ - px * 12, cy_ - py * 12), (cx_ + px * 12, cy_ + py * 12)], 2.4, 2.8, 2.4, color=c["fold"], smooth=False)
    elbow_fold = taper([(e[0] - px * 6 - ux * 2, e[1] - py * 6 - uy * 2), (e[0] + px * 2, e[1] + py * 2 + 3)], 0.8, 2.4, 0.8, color=c["fold"])
    return body + fill_ + clip + f'<g clip-path="url(#{cid})">{shade}{cuff_line}{elbow_fold}</g>', cuff_at


# ------------------------------------------------------------------ outfits
def casual():
    c = OUTFITS["casual"]
    shade = T([(30, -160), (80, -160), (80, 10), (36, 10), (40, -60)])
    collar = catmull(T([(-22, -147), (-10, -138), (0, -136), (10, -138), (22, -147)]), 8)
    inner = (taper(collar, 2.0, 4.0, 2.0, color=c["fold"], smooth=False)
             + taper(T([(18, -74), (22, -66), (24, -60)]), 0.8, 2.4, 0.8, color=c["fold"])
             + taper(T([(34, -20), (38, -10), (40, -2)]), 0.8, 2.4, 0.8, color=c["fold"]))
    out = [bare_arm(-1), bare_arm(1), filled(torso_path(), c, shade, inner), short_sleeve(-1, c), short_sleeve(1, c)]
    return "".join(out)


def police():
    c = OUTFITS["police"]
    shade = T([(30, -160), (80, -160), (80, 10), (36, 10), (40, -60)])
    fold = c["fold"]
    inner = []
    # placket + buttons
    inner.append(taper(T([(1, -136), (1, -70), (0, -14)]), 2.4, 2.8, 2.4, color=fold))
    for y in (-118, -94, -70, -46):
        inner.append(f'<circle cx="5" cy="{f(y + OY)}" r="2.6" fill="{fold}"/>')
    # chest pockets with flaps
    for sx in (-1, 1):
        x0, x1 = (-40, -14) if sx < 0 else (14, 40)
        pk = T([(x0, -100), (x1, -100), (x1, -74), ((x0 + x1) / 2, -71), (x0, -74)])
        inner.append(f'<path d="{poly_path(pk)}" fill="none" stroke="{fold}" stroke-width="2.4" stroke-linejoin="round"/>')
        flap = T([(x0 - 1, -103), (x1 + 1, -103), (x1 + 1, -94), ((x0 + x1) / 2, -90), (x0 - 1, -94)])
        inner.append(f'<path d="{poly_path(flap)}" fill="{c["main"]}" stroke="{fold}" stroke-width="2.4" stroke-linejoin="round"/>')
        inner.append(f'<circle cx="{f((x0 + x1) / 2)}" cy="{f(-94 + OY)}" r="2.2" fill="{fold}"/>')
    # folds
    inner.append(taper(T([(34, -40), (38, -30), (40, -22)]), 0.8, 2.4, 0.8, color=fold))
    # belt
    belt = T([(-70, -18), (70, -18), (70, 4), (-70, 4)])
    inner.append(f'<path d="{poly_path(belt)}" fill="#23242A"/>')
    bk = T([(-9, -16), (9, -16), (9, 1), (-9, 1)])
    inner.append(f'<path d="{poly_path(bk)}" fill="#C9CBD3" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>')
    inner.append(f'<rect x="-4" y="{f(-11 + OY)}" width="8" height="7" fill="#23242A"/>')
    body = filled(torso_path(), c, shade, "".join(inner))
    # badge (character's left chest = screen right), above the pocket
    bx, by = 27, -118 + OY
    shield = [(bx - 8, by - 8), (bx, by - 11), (bx + 8, by - 8), (bx + 7.5, by + 2), (bx, by + 9), (bx - 7.5, by + 2)]
    badge = (f'<path d="{poly_path(catmull(shield + [shield[0]], 4))}" fill="{GOLD}" stroke="{INK}" stroke-width="2.6" stroke-linejoin="round"/>'
             f'<path d="{poly_path([(bx + 1, by - 6), (bx + 7, by - 5), (bx + 6.5, by + 2), (bx + 1, by + 6)])}" fill="{GOLD_SH}"/>'
             f'<circle cx="{bx}" cy="{f(by)}" r="2.6" fill="#FFF3C4"/>')
    # collar points
    collar = []
    for sx in (-1, 1):
        pts = [(sx * 27, -150), (sx * 3, -139), (sx * 13, -122)]
        p = T(pts)
        collar.append(f'<path d="{poly_path(p)}" fill="{c["main"]}" stroke="{INK}" stroke-width="3.4" stroke-linejoin="round"/>')
    # epaulettes on sleeves + small patch on screen-left sleeve
    def epaulette(R):
        return f'<path d="{poly_path(R([(-12, -16), (12, -16), (12, -9), (-12, -9)]))}" fill="{fold}"/>'

    def patch(R):
        p = R([(-7, 2), (7, 2), (7, 13), (0, 18), (-7, 13)])
        return epaulette(R) + f'<path d="{poly_path(p)}" fill="{GOLD}" stroke="{fold}" stroke-width="1.6" stroke-linejoin="round"/>'
    out = [bare_arm(-1), bare_arm(1), body, "".join(collar), badge,
           short_sleeve(-1, c, patch), short_sleeve(1, c, epaulette)]
    return "".join(out)


def hoodie():
    c = OUTFITS["hoodie"]
    fold = c["fold"]
    path = torso_path(sx=1.05, hem=6)
    shade = T([(30, -160), (80, -160), (80, 14), (36, 14), (40, -60)])
    inner = []
    # ribbed hem
    inner.append(taper(T([(-58, -8), (0, -6), (58, -8)]), 2.4, 2.8, 2.4, color=fold))
    # kangaroo pocket
    pk = T([(-30, -58), (30, -58), (40, -10), (-40, -10)])
    inner.append(f'<path d="{poly_path(pk)}" fill="none" stroke="{fold}" stroke-width="2.6" stroke-linejoin="round"/>')
    for sx in (-1, 1):
        inner.append(taper(T([(sx * 30, -58), (sx * 37, -40), (sx * 39, -26)]), 2.4, 2.8, 2.4, color=fold))
    inner.append(taper(T([(18, -82), (22, -74), (24, -68)]), 0.8, 2.4, 0.8, color=fold))
    body = filled(path, c, shade, "".join(inner))
    # hood lying behind the neck (drawn over the torso, under the head)
    hood_pts = catmull([(-48, 112), (-40, 92), (-18, 82), (0, 80), (18, 82), (40, 92), (48, 112), (34, 128), (12, 132),
                        (0, 120), (-12, 132), (-34, 128), (-48, 112)], 8)
    hood = filled(hood_pts, c, [(18, 70), (60, 70), (60, 140), (24, 140)],
                  taper([(-30, 118), (-14, 124)], 0.8, 2.2, 0.8, color=fold) + taper([(30, 118), (14, 124)], 0.8, 2.2, 0.8, color=fold))
    strings = (taper([(-9, 126), (-11, 146), (-12, 162)], 2.6, 3.0, 2.6, color="#E4E4EA")
               + taper([(9, 126), (11, 144), (12, 158)], 2.6, 3.0, 2.6, color="#E4E4EA")
               + f'<rect x="-15" y="161" width="6" height="7" rx="2" fill="#B9BAC2"/><rect x="9" y="157" width="6" height="7" rx="2" fill="#B9BAC2"/>')
    sl_l, cuff_l = long_sleeve(-1, c)
    sl_r, cuff_r = long_sleeve(1, c)
    out = [bare_arm(-1, from_elbow=True, cuff=cuff_l), bare_arm(1, from_elbow=True, cuff=cuff_r),
           body, sl_l, sl_r, hood, strings]
    return "".join(out)


def figure(outfit):
    body = {"casual": casual, "police": police, "hoodie": hoodie}[outfit]()
    return shadow() + legs() + body + B.neck() + B.head("Neutral")


# ------------------------------------------------------------------ sheet
def build_svg():
    W, H = 2400, 1260
    FONT = B.FONT
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<style>@import url("https://fonts.googleapis.com/css2?family=Nunito:wght@700;900&amp;display=swap");</style>',
         f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>',
         f'<rect x="40" y="34" width="520" height="62" rx="31" fill="#2E3140"/>'
         f'<text x="70" y="77" font-family="{FONT}" font-weight="900" font-size="32" fill="#FFF" letter-spacing="1">RIAN — OUTFIT TEST</text>',
         f'<text x="585" y="76" font-family="{FONT}" font-weight="700" font-size="24" fill="#8A8A96">'
         f'Kepala v2 · ekspresi Neutral · proporsi rig sama · TEST, menunggu persetujuan</text>',
         f'<line x1="40" y1="122" x2="{W - 40}" y2="122" stroke="#DADAE0" stroke-width="3"/>']
    items = [("casual", "Casual (pembanding)"), ("police", "Polisi"), ("hoodie", "Hoodie")]
    cw = (W - 80) / 3
    for i, (k, name) in enumerate(items):
        x0 = 40 + i * cw
        p.append(f'<rect x="{x0 + 12}" y="150" width="{cw - 24}" height="1080" rx="28" fill="#F6F6F8"/>')
        p.append(f'<g transform="translate({x0 + cw / 2} {370}) scale(1.62)">{figure(k)}</g>')
        p.append(B.label(x0 + cw / 2, 1150, name, 320))
    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    svg = here / "rian_outfits_v2_TEST.svg"
    svg.write_text(build_svg())
    B.render(svg, here / "rian_outfits_v2_TEST.png", 2400, 1260)
    print("ok")
