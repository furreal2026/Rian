"""Curious Mind — draft generator for the master character sheet and core expressions.

Draws everything as SVG from one shared geometry, so every view and expression
keeps the same head, face layout and body proportions. Renders PNG with rsvg-convert.

Usage:  python3 generate_drafts.py <output_dir>
"""
import subprocess
import sys
from pathlib import Path

INK = "#1A1A1A"
SKIN = "#FFFFFF"
SHIRT = "#D64541"
SHIRT_DARK = "#A8322F"
MOUTH = "#7A2323"
BAG = "#A0A0A0"
GROUND = "#E6E6E6"
LABEL_BG = "#2B2F3A"
FONT = "Inter, DejaVu Sans, sans-serif"

LINE = 7        # body + head outline
LID = 11        # heavy upper lid
BROW = 10       # eyebrows
R = 100         # head radius (all geometry is in head-radius units)

_uid = [0]


def uid(prefix):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


# ---------------------------------------------------------------- face

def eye(cx, cy, rx=30, ry=21, lid=(-3, -3), p=(8, 5), pr=9, bag=False):
    return dict(cx=cx, cy=cy, rx=rx, ry=ry, lid=lid, p=p, pr=pr, bag=bag)


def draw_eye(e):
    cx, cy, rx, ry = e["cx"], e["cy"], e["rx"], e["ry"]
    ell = uid("ell")
    out = [f'<clipPath id="{ell}"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}"/></clipPath>']
    px, py = cx + e["p"][0], cy + e["p"][1]
    if e["lid"] is None:
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{SKIN}"/>')
        out.append(f'<g clip-path="url(#{ell})"><circle cx="{px}" cy="{py}" r="{e["pr"]}" fill="{INK}"/></g>')
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{INK}" stroke-width="{LINE}"/>')
    else:
        yl, yr = cy + e["lid"][0], cy + e["lid"][1]
        slope = (yr - yl) / (2 * rx)
        ext = 14
        below = uid("below")
        x0, x1 = cx - rx - ext, cx + rx + ext
        y0, y1 = yl - slope * ext, yr + slope * ext
        out.append(
            f'<clipPath id="{below}"><polygon points="{x0},{y0} {x1},{y1} {x1},{cy + ry + 30} {x0},{cy + ry + 30}"/></clipPath>'
        )
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{SKIN}"/>')
        out.append(
            f'<g clip-path="url(#{ell})"><g clip-path="url(#{below})"><circle cx="{px}" cy="{py}" r="{e["pr"]}" fill="{INK}"/></g></g>'
        )
        out.append(
            f'<g clip-path="url(#{below})"><ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{INK}" stroke-width="{LINE}"/></g>'
        )
        a, b = 3, 3
        out.append(
            f'<line x1="{cx - rx - a}" y1="{yl - slope * a}" x2="{cx + rx + b}" y2="{yr + slope * b}" '
            f'stroke="{INK}" stroke-width="{LID}" stroke-linecap="round"/>'
        )
    if e["bag"]:
        out.append(
            f'<path d="M {cx - rx * 0.7} {cy + ry + 7} Q {cx} {cy + ry + 15} {cx + rx * 0.7} {cy + ry + 7}" '
            f'fill="none" stroke="{BAG}" stroke-width="4" stroke-linecap="round"/>'
        )
    return "".join(out)


def brow(x1, y1, x2, y2, arch=0):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + arch
    return (
        f'<path d="M {x1} {y1} Q {mx} {my} {x2} {y2}" fill="none" stroke="{INK}" '
        f'stroke-width="{BROW}" stroke-linecap="round"/>'
    )


def mouth_line(d, width=5):
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'


def mouth_open(d):
    return f'<path d="{d}" fill="{MOUTH}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'


LX, LY, RX_, RY_ = -38, -4, 36, -6   # fixed eye anchors: identity stays the same


EXPRESSIONS = {
    "deadpan": dict(
        label="Neutral / Deadpan",
        L=eye(LX, LY), R=eye(RX_, RY_, rx=28),
        bL=(-58, -31, -14, -31), bR=(12, -33, 54, -33),
        mouth=mouth_line("M -6 55 L 12 54"),
    ),
    "skeptical": dict(
        label="Skeptical",
        L=eye(LX, LY, lid=(2, 3)), R=eye(RX_, RY_, rx=28, lid=(-9, -9), p=(8, 4)),
        bL=(-58, -26, -14, -24), bR=(12, -44, 56, -49, -10),
        mouth=mouth_line("M -8 56 L 12 51"),
    ),
    "annoyed": dict(
        label="Annoyed",
        L=eye(LX, LY, lid=(-3, 4), p=(6, 6)), R=eye(RX_, RY_, rx=28, lid=(4, -3), p=(6, 6)),
        bL=(-58, -38, -14, -26), bR=(12, -28, 56, -40),
        mouth=mouth_line("M -8 58 Q 3 51 14 58"),
    ),
    "exhausted": dict(
        label="Exhausted",
        L=eye(LX, LY, lid=(5, 5), p=(2, 10), pr=8, bag=True),
        R=eye(RX_, RY_, rx=28, lid=(5, 5), p=(2, 10), pr=8, bag=True),
        bL=(-58, -24, -14, -31), bR=(12, -33, 56, -26),
        mouth=mouth_line("M -10 58 L 14 58"),
    ),
    "confused": dict(
        label="Confused",
        L=eye(LX, LY, lid=None, p=(7, -5), pr=8), R=eye(RX_, RY_, rx=28, lid=None, p=(7, -6), pr=8),
        bL=(-56, -32, -16, -31), bR=(12, -45, 54, -42, -6),
        mouth=mouth_line("M -10 57 Q -4 52 2 57 T 14 57"),
        mark="?",
    ),
    "shocked": dict(
        label="Shocked",
        L=eye(LX, LY - 2, rx=31, ry=28, lid=None, p=(0, 0), pr=7),
        R=eye(RX_, RY_ - 2, rx=29, ry=27, lid=None, p=(0, 0), pr=7),
        bL=(-58, -46, -16, -49, -6), bR=(14, -49, 56, -46, -6),
        mouth=mouth_open("M 3 46 C 18 46 18 76 3 76 C -12 76 -12 46 3 46 Z"),
        mark="!!",
    ),
    "angry": dict(
        label="Angry",
        L=eye(LX, LY, lid=(-6, 6), p=(4, 6)), R=eye(RX_, RY_, rx=28, lid=(6, -6), p=(4, 6)),
        bL=(-60, -40, -12, -23), bR=(10, -23, 58, -40),
        mouth=mouth_open("M -16 56 Q 2 46 20 56 L 17 70 Q 2 76 -13 70 Z") + mouth_line("M -12 58 Q 2 52 16 58", 4).replace(INK, SKIN),
    ),
    "disgusted": dict(
        label="Disgusted",
        L=eye(LX, LY, lid=(1, 1)), R=eye(RX_, RY_, rx=28, lid=(-4, -2)),
        bL=(-58, -30, -14, -24), bR=(12, -37, 56, -39),
        mouth=mouth_line("M -10 59 Q -2 52 6 56 Q 12 59 16 63"),
    ),
    "worried": dict(
        label="Worried",
        L=eye(LX, LY, lid=None, p=(10, 3), pr=8), R=eye(RX_, RY_, rx=28, lid=None, p=(10, 3), pr=8),
        bL=(-58, -30, -16, -41), bR=(14, -41, 56, -30),
        mouth=mouth_line("M -10 60 Q -2 53 6 57 Q 11 60 14 59"),
    ),
    "smug": dict(
        label="Smug",
        L=eye(LX, LY, lid=(-1, -1)), R=eye(RX_, RY_, rx=28, lid=(-1, -1)),
        bL=(-58, -31, -14, -31), bR=(12, -37, 56, -41),
        mouth=mouth_line("M -12 54 Q 4 61 16 49"),
    ),
}


def _b(spec):
    x1, y1, x2, y2, *arch = spec
    return brow(x1 * 1.12, y1 - 5, x2 * 1.12, y2 - 5, *arch)


def face(name):
    x = EXPRESSIONS[name]
    parts = [draw_eye(x["L"]), draw_eye(x["R"]), _b(x["bL"]), _b(x["bR"]), x["mouth"]]
    return "".join(parts)


def head(name="deadpan", blank=False):
    out = f'<circle cx="0" cy="0" r="{R}" fill="{SKIN}" stroke="{INK}" stroke-width="{LINE}"/>'
    if not blank:
        out += face(name)
    return out


def mark(sym):
    if not sym:
        return ""
    return (
        f'<text x="96" y="-92" font-family="{FONT}" font-weight="800" font-size="62" fill="{INK}" '
        f'text-anchor="middle">{sym}</text>'
    )


# ---------------------------------------------------------------- body

SHIRT_FRONT = (
    "M -15 98 Q 0 112 15 98 L 42 108 L 74 162 L 57 176 L 45 152 L 45 240 "
    "L -45 240 L -45 152 L -57 176 L -74 162 L -42 108 Z"
)


def limb(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="{LINE}" stroke-linecap="round"/>'


def hand(x, y):
    return f'<circle cx="{x}" cy="{y}" r="12" fill="{SKIN}" stroke="{INK}" stroke-width="{LINE - 1}"/>'


def foot(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="13" stroke-linecap="round"/>'


def shadow(rx=85):
    return f'<ellipse cx="0" cy="458" rx="{rx}" ry="9" fill="{GROUND}"/>'


def body_front(back=False):
    out = shadow()
    out += limb(-20, 230, -29, 450) + limb(20, 230, 29, 450)
    out += foot(-29, 452, -49, 454) + foot(29, 452, 49, 454)
    out += limb(-58, 150, -76, 286) + limb(58, 150, 76, 286)
    out += f'<path d="{SHIRT_FRONT}" fill="{SHIRT}" stroke="{INK}" stroke-width="{LINE - 1}" stroke-linejoin="round"/>'
    collar = "M -15 98 Q 0 104 15 98" if back else "M -15 98 Q 0 112 15 98"
    out += f'<path d="{collar}" fill="none" stroke="{SHIRT_DARK}" stroke-width="5" stroke-linecap="round"/>'
    out += hand(-77, 290) + hand(77, 290)
    return out


def figure_front(name="deadpan"):
    return body_front() + head(name)


def figure_back():
    return body_front(back=True) + head(blank=True)


def figure_side():
    out = shadow(70)
    out += limb(-4, 230, -6, 450) + limb(6, 230, 8, 450)
    out += foot(-6, 452, 16, 454) + foot(8, 452, 30, 454)
    shirt = "M -24 100 L 22 100 Q 30 104 30 116 L 30 240 L -30 240 L -30 116 Q -30 104 -24 100 Z"
    out += f'<path d="{shirt}" fill="{SHIRT}" stroke="{INK}" stroke-width="{LINE - 1}" stroke-linejoin="round"/>'
    out += limb(2, 150, 6, 286)
    out += f'<path d="M -12 112 L 16 112 L 18 178 L -10 178 Z" fill="{SHIRT}" stroke="{INK}" stroke-width="{LINE - 1}" stroke-linejoin="round"/>'
    out += hand(7, 290)
    out += f'<circle cx="0" cy="0" r="{R}" fill="{SKIN}" stroke="{INK}" stroke-width="{LINE}"/>'
    out += draw_eye(eye(66, -7, rx=15, ry=18, lid=(-3, -3), p=(7, 5), pr=8))
    out += brow(52, -33, 82, -34)
    out += mouth_line("M 66 55 L 84 54")
    return out


# ---------------------------------------------------------------- sheets

def g(x, y, s, inner):
    return f'<g transform="translate({x},{y}) scale({s})">{inner}</g>'


def pill(x, y, text, w=None, size=34, dark=True):
    w = w or (len(text) * size * 0.62 + 48)
    bg, fg = (LABEL_BG, "#FFFFFF") if dark else ("#E9E9EC", INK)
    return (
        f'<rect x="{x - w / 2}" y="{y - size}" width="{w}" height="{size * 1.55}" rx="{size * 0.77}" fill="{bg}"/>'
        f'<text x="{x}" y="{y + size * 0.08}" font-family="{FONT}" font-weight="700" font-size="{size}" '
        f'fill="{fg}" text-anchor="middle">{text}</text>'
    )


def header(x, y, text, line_to):
    w = len(text) * 22 + 60
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="29" fill="{LABEL_BG}"/>'
        f'<text x="{x + w / 2}" y="{y + 41}" font-family="{FONT}" font-weight="800" font-size="32" '
        f'fill="#FFFFFF" text-anchor="middle" letter-spacing="1">{text}</text>'
        f'<line x1="{x + w + 16}" y1="{y + 29}" x2="{line_to}" y2="{y + 29}" stroke="#C9C9CE" stroke-width="3"/>'
    )


def svg(w, h, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}</svg>'
    )


def draft_tag(w):
    return (
        f'<text x="{w - 50}" y="70" font-family="{FONT}" font-weight="700" font-size="28" fill="#B0B0B6" '
        f'text-anchor="end">DRAFT · menunggu persetujuan</text>'
    )


def master_sheet():
    W, H = 2600, 1500
    b = draft_tag(W)
    b += f'<text x="60" y="80" font-family="{FONT}" font-weight="800" font-size="46" fill="{INK}">CURIOUS MIND — MASTER CHARACTER V1.0</text>'

    # main figure with proportion guides
    b += header(60, 130, "MAIN CHARACTER", 760)
    s, ox, oy = 1.45, 420, 420
    guides = [(-100, "puncak kepala"), (100, "dagu · 1 kepala"), (240, "ujung baju"), (290, "tangan"), (452, "telapak kaki")]
    for gy, lbl in guides:
        y = oy + gy * s
        b += f'<line x1="120" y1="{y}" x2="640" y2="{y}" stroke="#D5D5DA" stroke-width="2" stroke-dasharray="10 8"/>'
        b += f'<text x="650" y="{y + 8}" font-family="{FONT}" font-size="22" fill="#8A8A92">{lbl}</text>'
    b += g(ox, oy, s, figure_front())
    b += (
        f'<text x="420" y="1160" font-family="{FONT}" font-size="24" fill="#6A6A72" text-anchor="middle">'
        f'Tinggi total ≈ 2,8 diameter kepala · kepala ≈ 36% tinggi</text>'
    )

    # turnaround
    b += header(860, 130, "TURNAROUND", 1560)
    for i, (fig, lbl) in enumerate([(figure_front(), "Front"), (figure_side(), "Side"), (figure_back(), "Back")]):
        x = 980 + i * 240
        b += g(x, 380, 0.95, fig)
        b += pill(x, 860, lbl, w=150, size=30, dark=False)

    # palette
    b += header(1660, 130, "PALETTE", 2540)
    sw = [(INK, "Outline / mata / alis", "#1A1A1A"), (SKIN, "Kepala &amp; tangan", "#FFFFFF"),
          (SHIRT, "Kaos merah (casual)", "#D64541"), (SHIRT_DARK, "Kerah / bayangan kaos", "#A8322F"),
          (MOUTH, "Dalam mulut", "#7A2323")]
    for i, (c, name, hexv) in enumerate(sw):
        y = 230 + i * 110
        b += f'<rect x="1680" y="{y}" width="80" height="80" rx="14" fill="{c}" stroke="{INK}" stroke-width="3"/>'
        b += f'<text x="1790" y="{y + 35}" font-family="{FONT}" font-weight="700" font-size="28" fill="{INK}">{name}</text>'
        b += f'<text x="1790" y="{y + 70}" font-family="{FONT}" font-size="24" fill="#6A6A72">{hexv}</text>'

    # rules
    b += header(860, 960, "ATURAN IDENTITAS", 2540)
    rules = [
        "Kepala bulat putih, tanpa rambut. Wajah dewasa, deadpan, half-lidded.",
        "Kelopak atas tebal (garis 11) adalah ciri utama; alis terpisah di atasnya (garis 10).",
        "Posisi mata, alis, dan mulut tetap; ekspresi hanya mengubah kelopak, pupil, alis, mulut.",
        "Badan stickman: lengan dan kaki garis hitam (7), tangan bulat putih, kaki hitam pendek.",
        "Tanpa celana, tanpa sepatu. Pakaian hanya bagian atas, proporsi tidak berubah.",
        "Senyum bukan ekspresi default. Hindari kesan ceria atau kekanak-kanakan.",
    ]
    for i, t in enumerate(rules):
        y = 1065 + i * 62
        b += f'<circle cx="890" cy="{y - 9}" r="7" fill="{SHIRT}"/>'
        b += f'<text x="912" y="{y}" font-family="{FONT}" font-size="28" fill="{INK}">{t}</text>'
    return svg(W, H, b)


def bust(name):
    clip = uid("bust")
    return (
        f'<clipPath id="{clip}"><rect x="-160" y="-170" width="320" height="345"/></clipPath>'
        f'<g clip-path="url(#{clip})">{body_front()}{head(name)}{mark(EXPRESSIONS[name].get("mark"))}</g>'
    )


def expression_sheet():
    W, H = 2200, 1260
    b = draft_tag(W)
    b += f'<text x="60" y="80" font-family="{FONT}" font-weight="800" font-size="46" fill="{INK}">CURIOUS MIND — CORE EXPRESSIONS</text>'
    b += header(60, 120, "EXPRESSIONS", 2140)
    for i, name in enumerate(EXPRESSIONS):
        col, row = i % 5, i // 5
        x, y = 250 + col * 425, 400 + row * 500
        b += g(x, y, 1.15, bust(name))
        b += pill(x, y + 250, EXPRESSIONS[name]["label"], size=30, dark=False)
    return svg(W, H, b)


def write(out_dir, stem, content):
    svg_path = out_dir / f"{stem}.svg"
    png_path = out_dir / f"{stem}.png"
    svg_path.write_text(content)
    subprocess.run(["rsvg-convert", "-o", str(png_path), str(svg_path)], check=True)
    svg_path.unlink()
    print(png_path)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    write(out, "stick_figure_master_sheet_draft", master_sheet())
    write(out, "expressions_sheet_draft", expression_sheet())
