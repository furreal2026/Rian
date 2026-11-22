"""Chroma key for plates delivered on a flat magenta background (no alpha).

Rules implemented (see pilot courtyard README):
  * Originals are never modified; results are written as new files (e.g. courtyard_mid_rgba.png).
  * The key colour is SAMPLED from the real background (border-connected magenta region), not
    assumed to be #FF00FF.
  * Distance is CIE Lab Delta-E to the sampled colour, with an inner tolerance (fully transparent)
    and an outer tolerance (partial alpha), so edges get graded alpha.
  * Only background CONNECTED to the image border becomes transparent. Magenta/purple regions
    enclosed inside objects are kept opaque (and listed in the report for review).
  * Partial alpha is restricted to a thin band next to the connected background, so purple
    detail inside objects never becomes semi-transparent.
  * Despill only touches edge pixels (partial alpha, or opaque pixels touching the background)
    that are more magenta than the object interior next to them. Interior pixels are untouched.
  * Feather is applied only if the edge is hard/jagged, only inside the edge band, and only by
    lowering alpha (so no background colour is ever exposed).

Pure NumPy + Pillow (no SciPy needed).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

MAGENTA_LAB = np.array([60.32, 98.23, -60.82], dtype=np.float32)


# ------------------------------------------------------------------ colour
def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """uint8 (...,3) sRGB -> float32 CIE Lab (D65)."""
    c = rgb.astype(np.float32) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]], dtype=np.float32)
    xyz = c @ m.T
    del c
    xyz /= np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    eps, kap = 216 / 24389, 24389 / 27
    f = np.where(xyz > eps, np.cbrt(xyz), (kap * xyz + 16) / 116).astype(np.float32)
    del xyz
    lab = np.empty(f.shape, dtype=np.float32)
    lab[..., 0] = 116 * f[..., 1] - 16
    lab[..., 1] = 500 * (f[..., 0] - f[..., 1])
    lab[..., 2] = 200 * (f[..., 1] - f[..., 2])
    return lab


def delta_e(lab: np.ndarray, ref: np.ndarray, rows: int = 512) -> np.ndarray:
    out = np.empty(lab.shape[:2], dtype=np.float32)
    for y in range(0, lab.shape[0], rows):
        d = lab[y:y + rows] - ref
        out[y:y + rows] = np.sqrt((d * d).sum(axis=2))
    return out


# ---------------------------------------------------------- morphology (numpy)
def dilate(mask: np.ndarray, r: int) -> np.ndarray:
    """Binary dilation with a (2r+1) square, separable (fast)."""
    if r <= 0:
        return mask.copy()
    out = mask.copy()
    for axis in (0, 1):
        acc = out.copy()
        for s in range(1, r + 1):
            acc[tuple(slice(s, None) if a == axis else slice(None) for a in range(2))] |= \
                out[tuple(slice(None, -s) if a == axis else slice(None) for a in range(2))]
            acc[tuple(slice(None, -s) if a == axis else slice(None) for a in range(2))] |= \
                out[tuple(slice(s, None) if a == axis else slice(None) for a in range(2))]
        out = acc
    return out


def dilate_cross(mask: np.ndarray) -> np.ndarray:
    """Binary dilation with the 4-neighbour cross."""
    out = mask.copy()
    out[1:] |= mask[:-1]
    out[:-1] |= mask[1:]
    out[:, 1:] |= mask[:, :-1]
    out[:, :-1] |= mask[:, 1:]
    return out


def box_mean(arr: np.ndarray, r: int) -> np.ndarray:
    """Mean over a (2r+1)^2 window via summed-area table (edges clamped by count)."""
    a = np.pad(arr.astype(np.float64), r, mode="constant")
    s = a.cumsum(0).cumsum(1)
    s = np.pad(s, ((1, 0), (1, 0)))
    k = 2 * r + 1
    tot = s[k:, k:] - s[:-k, k:] - s[k:, :-k] + s[:-k, :-k]
    return tot.astype(np.float32)


def _propagate_runs(mask: np.ndarray, reached: np.ndarray) -> np.ndarray:
    """One pass: any horizontal run of `mask` containing a reached pixel becomes reached."""
    h, w = mask.shape
    flat = mask.ravel()
    starts = flat.copy()
    starts[1:] &= ~flat[:-1]
    starts[::w] = flat[::w]  # runs never wrap across rows
    run_id = np.cumsum(starts) * flat  # 0 = not in mask
    hit = np.zeros(run_id.max() + 1, dtype=bool)
    hit[run_id[reached.ravel() & flat]] = True
    hit[0] = False
    return hit[run_id].reshape(h, w)


def connected_from(mask: np.ndarray, seeds: np.ndarray, max_iter: int = 400) -> np.ndarray:
    """Pixels of `mask` 4-connected to `seeds` (alternating row/column run propagation)."""
    reached = seeds & mask
    for _ in range(max_iter):
        before = int(reached.sum())
        reached = _propagate_runs(mask, reached)
        reached = _propagate_runs(mask.T.copy(), reached.T.copy()).T
        if int(reached.sum()) == before:
            return reached
    raise RuntimeError("connectivity did not converge")


def border(mask_shape) -> np.ndarray:
    b = np.zeros(mask_shape, dtype=bool)
    b[0, :] = b[-1, :] = b[:, 0] = b[:, -1] = True
    return b


def label_islands(mask: np.ndarray, min_area: int, limit: int = 50) -> list[dict]:
    """Bounding boxes/areas of connected regions of `mask` (largest first, up to `limit`)."""
    remaining = mask.copy()
    out = []
    ys, xs = np.nonzero(remaining)
    order = np.random.default_rng(0).permutation(len(ys))[:4000] if len(ys) else []
    for i in order:
        y, x = ys[i], xs[i]
        if not remaining[y, x]:
            continue
        seed = np.zeros_like(mask)
        seed[y, x] = True
        comp = connected_from(remaining, seed)
        remaining &= ~comp
        area = int(comp.sum())
        if area >= min_area:
            cy, cx = np.nonzero(comp)
            out.append({"area_px": area, "bbox": [int(cx.min()), int(cy.min()), int(cx.max()), int(cy.max())]})
        if len(out) >= limit or not remaining.any():
            break
    return sorted(out, key=lambda d: -d["area_px"])


def max_filter(arr: np.ndarray, r: int) -> np.ndarray:
    out = arr.copy()
    for axis in (0, 1):
        acc = out.copy()
        for k in range(1, r + 1):
            sl_a = [slice(None), slice(None)]
            sl_b = [slice(None), slice(None)]
            sl_a[axis], sl_b[axis] = slice(k, None), slice(None, -k)
            np.maximum(acc[tuple(sl_a)], out[tuple(sl_b)], out=acc[tuple(sl_a)])
            np.maximum(acc[tuple(sl_b)], out[tuple(sl_a)], out=acc[tuple(sl_b)])
        out = acc
    return out


def _edge_alpha(rgb, d, bg_core, band, alpha, bg_rgb, t_in, opts) -> dict:
    """Alpha for pixels in the edge band (next to the connected background).

    Primary: unmix against the local object colour F (mean of opaque interior pixels within
    `fg_radius`): alpha = <C-B, F-B> / |F-B|^2. Fallback (thin detail with no interior nearby, or
    F too close to the key): Delta-E ramp from the inner tolerance to the most object-like pixel
    in the neighbourhood.
    """
    r = opts.fg_radius
    interior = ~dilate(bg_core, opts.edge_band) & (d >= t_in + opts.soft)
    cnt = box_mean(interior.astype(np.float32), r)
    idx = np.nonzero(band)
    c = rgb[idx].astype(np.float32)
    have = cnt[idx] > 0.5
    F = np.zeros_like(c)
    for ch in range(3):
        num = box_mean(np.where(interior, rgb[..., ch], 0).astype(np.float32), r)
        F[:, ch] = num[idx] / np.maximum(cnt[idx], 1e-6)
    fb = F - bg_rgb
    nrm = (fb * fb).sum(axis=1)
    proj_ok = have & (nrm > opts.min_contrast ** 2)
    a_proj = np.clip(((c - bg_rgb) * fb).sum(axis=1) / np.maximum(nrm, 1e-6), 0.0, 1.0)
    dmax = max_filter(d, 2)[idx]
    a_ramp = np.clip((d[idx] - t_in) / np.maximum(dmax - t_in, 1.0), 0.0, 1.0)
    a = np.where(proj_ok, a_proj, a_ramp)
    a[a >= opts.snap_opaque] = 1.0  # sensor/compression noise must not make object pixels translucent
    a[d[idx] < t_in] = np.minimum(a[d[idx] < t_in], 0.0)  # key-coloured pixels in the band stay clear
    alpha[idx] = a
    return {"edge_band_px": int(len(c)), "unmixed_with_local_object_colour": int(proj_ok.sum()),
            "ramp_fallback": int((~proj_ok).sum())}


# ------------------------------------------------------------------- keying
@dataclass
class KeyOptions:
    seed_loose_de: float = 45.0     # how far from magenta a border pixel may be to seed the background search
    inner_min: float = 4.0          # inner tolerance clamp (Delta-E)
    inner_max: float = 22.0
    inner_mult: float = 1.15        # inner = p99.5 of background spread * mult
    soft: float = 18.0              # outer = inner + soft (pixels beyond it count as clear object)
    fg_radius: int = 4              # window for the local object colour used to unmix edge pixels
    min_contrast: float = 40.0      # RGB distance object-vs-key needed for unmixing (else ramp)
    snap_opaque: float = 0.95       # edge alpha at or above this is treated as fully opaque
    edge_band: int = 2              # px from connected background where partial alpha is allowed
    despill_band: int = 3           # px from background where despill may act
    despill_ref_radius: int = 7     # window for the local interior reference
    despill_margin: float = 12.0    # spill excess tolerated before correction
    feather_if_partial_below: float = 0.35
    feather_radius: float = 0.8
    island_min_area: int = 64


@dataclass
class KeyReport:
    source: str
    output: str
    size: list
    source_mode: str
    source_icc: bool
    bg_sample_rgb: list = field(default_factory=list)
    bg_sample_lab: list = field(default_factory=list)
    bg_spread_p99_5: float = 0.0
    tol_inner: float = 0.0
    tol_outer: float = 0.0
    bg_fraction: float = 0.0
    partial_px: int = 0
    edge_px: int = 0
    partial_ratio: float = 0.0
    feather_applied: bool = False
    despilled_px: int = 0
    object_px_made_transparent: int = 0
    unconnected_transparent_px: int = 0
    enclosed_bg_colour_islands: list = field(default_factory=list)
    enclosed_bg_colour_area_px: int = 0
    residual_fringe_px: int = 0
    residual_fringe_ratio: float = 0.0
    alpha_method: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


def key_magenta(src: Path, out: Path, opts: KeyOptions | None = None) -> tuple[Image.Image, KeyReport, dict]:
    opts = opts or KeyOptions()
    im = Image.open(src)
    rep = KeyReport(str(src), str(out), list(im.size), im.mode, "icc_profile" in im.info)
    if im.mode not in ("RGB", "RGBA", "P"):
        rep.notes.append(f"source mode {im.mode} converted to RGB for keying")
    if im.mode == "RGBA" and np.asarray(im.getchannel("A")).min() < 255:
        rep.notes.append("source already has transparency; it is ignored and the magenta key is used")
    rgb = np.asarray(im.convert("RGB"))
    h, w, _ = rgb.shape
    lab = srgb_to_lab(rgb)

    # 1) find the real background: magenta-ish pixels connected to the border
    loose = delta_e(lab, MAGENTA_LAB) < opts.seed_loose_de
    bg_loose = connected_from(loose, border((h, w)) & loose)
    if bg_loose.mean() < 0.005:
        raise ValueError("no magenta background connected to the image border was found")
    rng = np.random.default_rng(1)
    ys, xs = np.nonzero(bg_loose)
    pick = rng.choice(len(ys), size=min(200_000, len(ys)), replace=False)
    samp = lab[ys[pick], xs[pick]]
    bg_lab = np.median(samp, axis=0).astype(np.float32)
    spread = np.sqrt(((samp - bg_lab) ** 2).sum(axis=1))
    # the loose region also contains edge pixels; use the tight core of the sample for the spread
    core = spread <= np.percentile(spread, 90)
    p995 = float(np.percentile(spread[core], 99.5))
    t_in = float(np.clip(p995 * opts.inner_mult, opts.inner_min, opts.inner_max))
    t_out = t_in + opts.soft
    rep.bg_sample_lab = [round(float(v), 2) for v in bg_lab]
    rep.bg_sample_rgb = [int(v) for v in np.median(rgb[ys[pick], xs[pick]], axis=0)]
    rep.bg_spread_p99_5 = round(p995, 2)
    rep.tol_inner, rep.tol_outer = round(t_in, 2), round(t_out, 2)
    del samp, spread, loose, bg_loose

    # 2) graded matte, connected background only
    d = delta_e(lab, bg_lab)
    del lab
    bg_core = connected_from(d < t_in, border((h, w)) & (d < t_in))
    near = dilate(bg_core, opts.edge_band)
    band = near & ~bg_core
    alpha = np.ones((h, w), dtype=np.float32)
    alpha[bg_core] = 0.0
    bg_rgb = np.median(rgb[ys[pick], xs[pick]], axis=0).astype(np.float32)
    rep.alpha_method = _edge_alpha(rgb, d, bg_core, band, alpha, bg_rgb, t_in, opts)
    rep.bg_fraction = round(float(bg_core.mean()), 4)
    rep.partial_px = int(((alpha > 0) & (alpha < 1)).sum())

    # enclosed background-coloured regions are kept, but reported
    enclosed = (d < t_in) & ~bg_core
    rep.enclosed_bg_colour_area_px = int(enclosed.sum())
    if rep.enclosed_bg_colour_area_px:
        rep.enclosed_bg_colour_islands = label_islands(enclosed, opts.island_min_area)

    # 3) unmix partial pixels against the sampled background colour
    out_rgb = rgb.astype(np.float32)
    part = (alpha > 0) & (alpha < 1)
    a = alpha[part][:, None]
    out_rgb[part] = np.clip((out_rgb[part] - (1 - a) * bg_rgb) / np.maximum(a, 1e-3), 0, 255)

    # 4) despill: only edge pixels that are more magenta than the nearby object interior
    zone = dilate(bg_core, opts.despill_band) & (alpha > 0)
    rep.edge_px = int((zone & (alpha >= 1)).sum())
    s = np.minimum(out_rgb[..., 0], out_rgb[..., 2]) - out_rgb[..., 1]
    interior = (alpha >= 1) & ~dilate(bg_core, opts.despill_band + 2)
    num = box_mean(np.where(interior, s, 0.0), opts.despill_ref_radius)
    cnt = box_mean(interior.astype(np.float32), opts.despill_ref_radius)
    has_ref = cnt > 0
    s_ref = np.where(has_ref, num / np.maximum(cnt, 1e-6), 0.0)
    # without any interior reference (very thin detail) only correct pixels that are close to the key
    close_to_key = d < (t_out + 10)
    excess = s - np.maximum(s_ref, 0.0) - opts.despill_margin
    fix = zone & (excess > 0) & (has_ref | close_to_key) & (out_rgb[..., 0] > out_rgb[..., 1]) & (out_rgb[..., 2] > out_rgb[..., 1])
    rep.despilled_px = int(fix.sum())
    ex = excess[fix]
    out_rgb[..., 0][fix] -= ex
    out_rgb[..., 2][fix] -= ex
    del s, num, cnt, s_ref, excess

    # 5) feather only if the edge is hard: share of the pixels directly touching the background
    #    (4-neighbours) that already carry partial alpha. Anti-aliased art scores high, hard cut-outs ~0.
    touch = (dilate_cross(bg_core) & ~bg_core)
    boundary = int(touch.sum())
    rep.partial_ratio = round(int((touch & (alpha < 1)).sum()) / max(1, boundary), 3)
    if rep.partial_ratio < opts.feather_if_partial_below:
        a8 = Image.fromarray((alpha * 255).astype(np.uint8))
        blurred = np.asarray(a8.filter(ImageFilter.GaussianBlur(opts.feather_radius)), dtype=np.float32) / 255
        fband = dilate(bg_core, 1) & ~bg_core
        alpha[fband] = np.minimum(alpha[fband], blurred[fband])
        rep.feather_applied = True

    # 6) checks
    # alpha < 1 is only allowed in the edge band next to the connected background
    rep.object_px_made_transparent = int(((alpha < 1) & ~dilate(bg_core, opts.edge_band)).sum())
    transparent = alpha <= 0
    rep.unconnected_transparent_px = int((transparent & ~bg_core).sum())
    s2 = np.minimum(out_rgb[..., 0], out_rgb[..., 2]) - out_rgb[..., 1]
    fringe = zone & (alpha > 0.05) & (s2 > 40) & (d < t_out + 15)
    rep.residual_fringe_px = int(fringe.sum())
    rep.residual_fringe_ratio = round(rep.residual_fringe_px / max(1, int(zone.sum())), 5)

    out_rgb[transparent] = 0
    rgba = np.dstack([np.clip(out_rgb + 0.5, 0, 255).astype(np.uint8), np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)])
    res = Image.fromarray(rgba, "RGBA")
    maps = {"enclosed": enclosed, "fringe": fringe, "zone": zone}
    return res, rep, maps


# -------------------------------------------------------------- verification
def composite_previews(rgba: Image.Image, out_dir: Path, stem: str, max_side: int = 0) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, col in (("white", (255, 255, 255)), ("black", (0, 0, 0)), ("gray50", (128, 128, 128))):
        base = Image.new("RGBA", rgba.size, col + (255,))
        base.alpha_composite(rgba)
        img = base.convert("RGB")
        if max_side and max(img.size) > max_side:
            img.thumbnail((max_side, max_side), Image.LANCZOS)
        p = out_dir / f"{stem}_on_{name}.png"
        img.save(p)
        paths.append(p)
    return paths


def detail_crops(src: Image.Image, rgba: Image.Image, zone: np.ndarray, out: Path, n: int = 6, tile: int = 384) -> Path:
    """Side-by-side crops (original | on black | on white | on gray) at the busiest edge areas."""
    h, w = zone.shape
    gy, gx = h // tile, w // tile
    dens = zone[: gy * tile, : gx * tile].reshape(gy, tile, gx, tile).sum(axis=(1, 3))
    picks = np.dstack(np.unravel_index(np.argsort(dens.ravel())[::-1], dens.shape))[0][:n]
    rows = []
    for ty, tx in picks:
        box = (int(tx * tile), int(ty * tile), int(tx * tile + tile), int(ty * tile + tile))
        cells = [src.convert("RGB").crop(box)]
        for col in ((0, 0, 0), (255, 255, 255), (128, 128, 128)):
            b = Image.new("RGBA", (tile, tile), col + (255,))
            b.alpha_composite(rgba.crop(box))
            cells.append(b.convert("RGB"))
        rows.append(cells)
    sheet = Image.new("RGB", (tile * 4, tile * len(rows)), (40, 40, 40))
    for r, cells in enumerate(rows):
        for c, im in enumerate(cells):
            sheet.paste(im, (c * tile, r * tile))
    sheet.save(out)
    return out


def check_output(path: Path, min_size: tuple[int, int] | None = None, min_long_axis: int | None = None) -> dict:
    with Image.open(path) as im:
        im.load()
    res = {"mode": im.mode, "size": list(im.size), "bits": 8 if im.mode in ("RGBA", "RGB") else None,
           "icc_profile": "icc_profile" in im.info, "format": im.format}
    ok = im.mode == "RGBA" and im.format == "PNG"
    if min_size:
        res["min_size"] = list(min_size)
        ok &= im.size[0] >= min_size[0] and im.size[1] >= min_size[1]
    if min_long_axis:
        res["min_long_axis"] = min_long_axis
        ok &= max(im.size) >= min_long_axis
    res["pass"] = bool(ok)
    return res


def save_report(rep: KeyReport, extra: dict, path: Path):
    path.write_text(json.dumps({**asdict(rep), **extra}, indent=2), encoding="utf-8")
