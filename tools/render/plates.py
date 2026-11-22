"""Plate intake for an episode environment: archive -> key -> verify -> (place) -> stack preview.

    python -m tools.render ingest-plates --config <episode>/config/<x>.json --inbox <folder with uploads>
    python -m tools.render place-plates  --config ... --layers layer2_midground,layer1_foreground,...
    python -m tools.render stack-preview --config ...

Folder layout next to the manifest (e.g. .../assets/environment/courtyard/):
    source/            originals exactly as delivered (never overwritten)
    keyed/             new RGBA copies: <name>_rgba.png
    qc/<stem>/         composites on white/black/gray50, detail crops, overlays, report.json
    <manifest files>   placed copies (only after review, via place-plates)

Magenta keying is only applied to layers listed in KEYED (bg, mid, fg, leaf). bg_far is opaque and
is never keyed: it is checked for full opacity and copied to RGBA.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from . import chroma_key as ck

KEYED_ROLES = {"layer3_background", "layer2_midground", "layer1_foreground", "fx:leaf_wipe"}
OPAQUE_ROLES = {"layer4_far_background"}
EXTRA_SOURCES = ["courtyard_master_ref.png"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _manifest(config: Path) -> tuple[Path, dict]:
    cfg = json.loads(Path(config).read_text(encoding="utf-8"))
    mpath = (Path(config).parent / cfg["environment"]["manifest"]).resolve()
    return mpath, json.loads(mpath.read_text(encoding="utf-8"))


def _items(man: dict) -> list[dict]:
    items = [{"id": L["id"], "file": L["file"], "min_size": L.get("min_size_px"), "keyed": L["id"] in KEYED_ROLES} for L in man["layers"]]
    for key, rel in man.get("fx", {}).items():
        items.append({"id": f"fx:{key}", "file": rel, "min_size": None, "min_long_axis": 2500 if key == "leaf_wipe" else None,
                      "keyed": f"fx:{key}" in KEYED_ROLES})
    return items


def archive(inbox: Path, base: Path, rel: str) -> tuple[Path | None, str]:
    """Copy inbox/<rel> (or inbox/<basename>) to base/source/<rel>. Never overwrites a different file."""
    cands = [inbox / rel, inbox / Path(rel).name]
    src = next((c for c in cands if c.exists()), None)
    dst = base / "source" / rel
    if src is None:
        return (dst if dst.exists() else None), ("already archived" if dst.exists() else "missing in inbox")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if _sha(dst) == _sha(src):
            return dst, "already archived (identical)"
        raise FileExistsError(f"{dst} already exists with different content; originals are never overwritten")
    shutil.copy2(src, dst)
    return dst, "archived"


def _overlay(rgba: Image.Image, mask: np.ndarray, color, out: Path, max_side=2400):
    base = Image.new("RGBA", rgba.size, (128, 128, 128, 255))
    base.alpha_composite(rgba)
    ov = np.zeros((*mask.shape, 4), np.uint8)
    ov[mask] = color + (200,)
    base.alpha_composite(Image.fromarray(ov, "RGBA"))
    img = base.convert("RGB")
    img.thumbnail((max_side, max_side), Image.LANCZOS)
    img.save(out)


def ingest(config: Path, inbox: Path) -> dict:
    mpath, man = _manifest(config)
    base = mpath.parent
    results = {"manifest": str(mpath), "layers": {}, "extra": {}}
    for extra in EXTRA_SOURCES:
        p, st = archive(inbox, base, extra)
        results["extra"][extra] = {"archived": str(p) if p else None, "status": st}
    for it in _items(man):
        src, st = archive(inbox, base, it["file"])
        entry = {"file": it["file"], "archive": st, "source": str(src) if src else None}
        results["layers"][it["id"]] = entry
        if src is None:
            entry["status"] = "BLOCKED"
            entry["reason"] = "source file not delivered"
            continue
        stem = Path(it["file"]).stem
        out = base / "keyed" / f"{stem}_rgba.png"
        qc = base / "qc" / stem
        qc.mkdir(parents=True, exist_ok=True)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise FileExistsError(f"{out} exists; move it away before re-keying (results are never overwritten)")
        with Image.open(src) as im:
            im.load()
        entry["source_info"] = {"mode": im.mode, "size": list(im.size), "icc_profile": "icc_profile" in im.info}
        if it["keyed"]:
            rgba, rep, maps = ck.key_magenta(src, out)
            rgba.save(out)
            entry["key"] = {k: v for k, v in rep.__dict__.items() if k not in ("source", "output")}
            ck.detail_crops(im, rgba, maps["zone"], qc / f"{stem}_detail_crops.png")
            if maps["enclosed"].any():
                _overlay(rgba, maps["enclosed"], (0, 255, 255), qc / f"{stem}_enclosed_magenta_overlay.png")
            if maps["fringe"].any():
                _overlay(rgba, maps["fringe"], (255, 255, 0), qc / f"{stem}_fringe_overlay.png")
        else:
            rgb = np.asarray(im.convert("RGBA"))
            entry["opaque_check"] = {"min_alpha": int(rgb[..., 3].min())}
            mag = ck.delta_e(ck.srgb_to_lab(rgb[..., :3]), ck.MAGENTA_LAB) < 25
            entry["opaque_check"]["magenta_like_px"] = int(mag.sum())
            rgba = Image.fromarray(np.dstack([rgb[..., :3], np.full(rgb.shape[:2], 255, np.uint8)]), "RGBA")
            rgba.save(out)
        entry["output"] = str(out)
        entry["previews"] = [str(p) for p in ck.composite_previews(rgba, qc, stem, max_side=2400)]
        ms = tuple(it["min_size"]) if it.get("min_size") else None
        entry["format_check"] = ck.check_output(out, min_size=ms, min_long_axis=it.get("min_long_axis"))
        (qc / "report.json").write_text(json.dumps(entry, indent=2), encoding="utf-8")
        entry["status"] = "NEEDS_REVIEW" if entry["format_check"]["pass"] else "BLOCKED"
        if not entry["format_check"]["pass"]:
            entry["reason"] = "format/size check failed"
    (base / "qc" / "ingest_report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def place(config: Path, layer_ids: list[str]) -> list[str]:
    """Copy reviewed keyed/<stem>_rgba.png to the manifest file name. Refuses to overwrite a different placed file."""
    mpath, man = _manifest(config)
    base = mpath.parent
    done = []
    for it in _items(man):
        if it["id"] not in layer_ids:
            continue
        src = base / "keyed" / f"{Path(it['file']).stem}_rgba.png"
        dst = base / it["file"]
        if not src.exists():
            raise FileNotFoundError(src)
        if dst.exists() and _sha(dst) != _sha(src):
            raise FileExistsError(f"{dst} exists with different content")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        done.append(str(dst))
    return done


def stack_preview(config: Path, out: Path, scene_cls, with_character: bool = True) -> dict:
    """Reference-camera composite of all placed layers with guides: horizon, ground line, action band 62-90%."""
    import importlib
    scene = scene_cls(config, allow_missing_plates=True)
    env = scene.env
    ref = env.reference
    cam_mod = importlib.import_module(scene_cls.__module__.rsplit(".", 2)[0] + ".camera.camera")
    cam = cam_mod.CameraState(ref.x, ref.y, ref.zoom, 0.0)
    img = Image.new("RGBA", (scene.width, scene.height), (0, 0, 0, 0))
    drawn = False
    for layer in env.layers:
        if with_character and not drawn and layer.z > env.character_z:
            scene._draw_character(img, cam, 0.0)
            drawn = True
        env.draw_layer(img, layer, cam, scene.frame_world_width)
    if with_character and not drawn:
        scene._draw_character(img, cam, 0.0)
    clean = img.copy()
    guides = img.copy()
    d = ImageDraw.Draw(guides)
    W, H = scene.width, scene.height
    m = cam_mod.layer_matrix(cam, 1.0, ref, W, H, scene.frame_world_width)
    gy = mx_apply(m, 0, env.ground_y)[1]
    hy = H / 2
    d.line([(0, hy), (W, hy)], fill=(0, 200, 255, 255), width=2)
    d.text((10, hy + 4), "horizon / eye level (ref camera)", fill=(0, 200, 255, 255))
    d.line([(0, gy), (W, gy)], fill=(255, 220, 0, 255), width=2)
    d.text((10, gy + 4), "ground line y=0 (character feet)", fill=(255, 220, 0, 255))
    for frac in (0.62, 0.90):
        d.line([(0, H * frac), (W, H * frac)], fill=(255, 60, 60, 255), width=2)
    d.text((W - 260, H * 0.62 + 4), "action band 62%-90%", fill=(255, 60, 60, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    clean.save(out.with_name(out.stem + "_clean.png"))
    guides.save(out)
    a = np.asarray(img.getchannel("A"))
    return {"preview": str(out), "clean": str(out.with_name(out.stem + "_clean.png")),
            "coverage": float((a >= 250).mean()), "ground_line_y_px": round(gy, 1), "horizon_y_px": hy,
            "layers": {l.id: l.source for l in env.layers}}


def mx_apply(m, x, y):
    v = m @ np.array([x, y, 1.0])
    return float(v[0]), float(v[1])
