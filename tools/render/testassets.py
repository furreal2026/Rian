"""TEST-ONLY assets for exercising the pipeline before the approved courtyard plates exist.

These are measurement charts, not an environment: numbered grids stamped
"TEST PLATE - NOT FINAL ENVIRONMENT" on every tile so they can never be mistaken for, or
shipped as, the courtyard. They are written outside assets/ (default <episode>/output/test_assets/)
with the exact file names the manifest expects, plus test_layout.json that positions each test
plate to cover the scene's camera moves.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LABEL = "TEST PLATE - NOT FINAL ENVIRONMENT"

TINTS = {  # per parallax factor, deliberately unlike any approved palette
    0.15: ((200, 210, 228), (150, 165, 195)),
    0.35: ((170, 190, 220), (110, 130, 175)),
    1.0: ((222, 214, 196), (150, 135, 110)),
    1.5: ((60, 60, 70), (25, 25, 30)),
}


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()


def make_test_plate(size_px, parallax: float, layer_id: str, world_origin, world_per_px: float, ground_y: float = 0.0) -> Image.Image:
    w, h = size_px
    fill, ink = TINTS.get(parallax, ((200, 200, 200), (90, 90, 90)))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_big, f_small = _font(34), _font(22)
    step = 200  # world units between grid lines
    x0w, y0w = world_origin

    def wx(px):
        return x0w + px * world_per_px

    def to_px(world, origin):
        return (world - origin) / world_per_px

    if parallax <= 0.2:
        d.rectangle([0, 0, w, h], fill=fill + (255,))
    elif parallax < 1.0:
        top = int(max(0, to_px(ground_y - 900, y0w)))
        d.rectangle([0, top, w, h], fill=fill + (235,))
    elif parallax == 1.0:
        top = int(max(0, to_px(ground_y - 40, y0w)))
        d.rectangle([0, top, w, h], fill=fill + (255,))
        gy = to_px(ground_y, y0w)
        d.line([(0, gy), (w, gy)], fill=ink + (255,), width=6)
        d.text((20, gy + 12), "TEST GROUND LINE y=0 (character plane, parallax 1.0)", fill=ink + (255,), font=f_small)

    gx_start = math.floor(x0w / step) * step
    gy_start = math.floor(y0w / step) * step
    if parallax >= 1.5:
        # sparse foreground markers so the layer is mostly transparent
        xw = gx_start
        k = 0
        while to_px(xw, x0w) < w:
            if k % 4 == 2:
                px = to_px(xw, x0w)
                d.rectangle([px, 0, px + 70, h], fill=fill + (230,))
                for yy in range(40, h, 420):
                    d.text((px + 6, yy), f"L1\nTEST\np={parallax}\nx={int(xw)}", fill=(255, 220, 0, 255), font=f_small)
            xw += step
            k += 1
        return img
    xw = gx_start
    while to_px(xw, x0w) < w:
        px = to_px(xw, x0w)
        d.line([(px, 0), (px, h)], fill=ink + (255,), width=3 if int(xw) % 1000 == 0 else 1)
        xw += step
    yw = gy_start
    while to_px(yw, y0w) < h:
        py = to_px(yw, y0w)
        d.line([(0, py), (w, py)], fill=ink + (255,), width=3 if int(yw) % 1000 == 0 else 1)
        yw += step
    yw = gy_start
    row = 0
    while to_px(yw, y0w) < h:
        xw = gx_start + (step if row % 2 else 0)
        while to_px(xw, x0w) < w:
            px, py = to_px(xw, x0w), to_px(yw, y0w)
            d.text((px + 8, py + 8), f"{layer_id}  p={parallax}", fill=ink + (255,), font=f_small)
            d.text((px + 8, py + 34), f"x={int(xw)} y={int(yw)}", fill=ink + (255,), font=f_small)
            xw += step * 2
        if row % 3 == 0:
            d.text((40, to_px(yw, y0w) + 100), LABEL, fill=(200, 30, 30, 255), font=f_big)
        yw += step
        row += 1
    return img


def make_test_leaf(path: Path, size=(900, 380)):
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(121):
        u = i / 120
        x = u * w
        y = h / 2 - (h / 2 - 6) * math.sin(math.pi * u) ** 0.8
        pts.append((x, y))
    for i in range(120, -1, -1):
        u = i / 120
        pts.append((u * w, h / 2 + (h / 2 - 6) * math.sin(math.pi * u) ** 0.8))
    d.polygon(pts, fill=(60, 150, 70, 255), outline=(20, 60, 25, 255))
    d.line([(10, h / 2), (w - 10, h / 2)], fill=(20, 60, 25, 255), width=6)
    d.text((w * 0.3, h * 0.36), "TEST LEAF - NOT FINAL", fill=(255, 255, 255, 255), font=_font(40))
    img.save(path)


def generate(scene_config: str | Path, out_dir: str | Path, scene_cls) -> dict:
    """Write test plates sized to the scene's camera coverage + a test leaf. Returns the layout.

    `scene_cls` is the episode's compositor Scene class (episode code lives in its own folder)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    scene = scene_cls(scene_config, allow_missing_plates=True)
    req = scene.env.required_bounds(scene.all_cameras(), *scene.nominal_size, scene.frame_world_width, margin=96)
    layout = {}
    for layer in scene.env.layers:
        r = req[layer.id]
        wpp = layer.world_per_px
        size = tuple(r["min_size_px"])
        img = make_test_plate(size, layer.parallax, layer.id, tuple(r["position"]), wpp, scene.env.ground_y)
        img.save(out / layer.file)
        layout[layer.id] = {"position": r["position"], "world_units_per_pixel": wpp, "size_px": list(size), "file": layer.file}
    make_test_leaf(out / "leaf_wipe.png")
    (out / "test_layout.json").write_text(json.dumps(layout, indent=2), encoding="utf-8")
    (out / "README_TEST_ONLY.txt").write_text(
        "Generated TEST assets. Not an environment, not approved art. Do not copy into assets/.\n", encoding="utf-8")
    return layout
