"""Command line interface.

    python -m tools.render render     --config CFG --out OUT.mp4 [--test-plates [DIR]] [--scale S] [--workers N]
    python -m tools.render stills     --config CFG --frames 0,70,130 --out-dir DIR [--test-plates [DIR]]
    python -m tools.render test-assets --config CFG [--out-dir DIR]
    python -m tools.render plate-spec --config CFG [--json OUT.json]
    python -m tools.render qc         --config CFG --video OUT.mp4 [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import importlib
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def episode_dir(config) -> Path:
    """An episode folder holds config/, rig/, camera/, compositor/, transitions/; config lives in <episode>/config/."""
    return Path(config).resolve().parent.parent


def episode_module(config, name: str):
    rel = episode_dir(config).relative_to(REPO)
    return importlib.import_module(".".join(rel.parts + tuple(name.split("."))))


def scene_class(config):
    return episode_module(config, "compositor.compositor").Scene


def default_test_dir(config) -> Path:
    return episode_dir(config) / "output" / "test_assets"

_SCENE = None


def _init_worker(config, test_dir, scale):
    global _SCENE
    _SCENE = scene_class(config)(config, test_plates=test_dir, scale=scale)


def _render_one(i):
    img, info = _SCENE.render_frame_rgba(i)
    info["coverage"] = _SCENE.coverage(img)
    return i, _SCENE._flatten(img), info


def _parse_frames(spec: str | None, n: int) -> list[int]:
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return [i for i in out if 0 <= i < n]


def _resolve_test_dir(args) -> Path | None:
    if args.test_plates is None:
        return None
    d = Path(args.test_plates) if args.test_plates != "auto" else default_test_dir(args.config)
    if not (d / "test_layout.json").exists():
        from .testassets import generate
        print(f"[test-assets] generating TEST plates in {d}")
        generate(args.config, d, scene_class(args.config))
    return d


def cmd_render(args) -> int:
    from .encode import Encoder
    Scene = scene_class(args.config)
    test_dir = _resolve_test_dir(args)
    scene = Scene(args.config, test_plates=test_dir, scale=args.scale)  # validates config + plates up front
    frames = _parse_frames(args.frames, scene.n_frames)
    out = Path(args.out)
    print(f"[render] {scene.cfg.get('title')} | {scene.width}x{scene.height} @ {scene.fps:g} fps | {len(frames)} frames | "
          f"plates: {', '.join(f'{l.id}={l.source}' for l in scene.env.layers)}")
    for row in scene.timeline():
        print(f"[timeline] {row['shot']}: frames {row['first_frame']}-{row['last_frame']} ({row['frames']}f) {row['camera_move']}")
    for w in scene.windows:
        print(f"[transition] {w.from_shot}->{w.to_shot} {w.type} boundary={w.boundary:.4f}s (frame {round(w.boundary*scene.fps)}) window={w.t_in:.4f}-{w.t_out:.4f}")
    enc = Encoder(out, scene.width, scene.height, scene.fps, crf=args.crf, preset=args.preset)
    keep = Path(args.keep_frames) if args.keep_frames else None
    if keep:
        keep.mkdir(parents=True, exist_ok=True)
    infos = []
    t0 = time.time()
    workers = max(1, args.workers)
    try:
        if workers == 1:
            _init_worker(args.config, test_dir, args.scale)
            it = map(_render_one, frames)
            pool = None
        else:
            ctx = mp.get_context("spawn")
            pool = ctx.Pool(workers, initializer=_init_worker, initargs=(args.config, test_dir, args.scale))
            it = pool.imap(_render_one, frames, chunksize=2)
        for k, (i, rgb, info) in enumerate(it):
            enc.write(rgb)
            infos.append(info)
            if keep:
                Image.fromarray(rgb).save(keep / f"frame_{i:04d}.png")
            if (k + 1) % 24 == 0 or k + 1 == len(frames):
                el = time.time() - t0
                print(f"[render] {k+1}/{len(frames)} frames  {el:.1f}s  ({(k+1)/el:.2f} fps)", flush=True)
        if pool:
            pool.close()
            pool.join()
    finally:
        enc.close()
    holes = [inf for inf in infos if inf["coverage"] < 0.999]
    report = {"video": str(out), "frames_written": enc.frames, "render_seconds": round(time.time() - t0, 2),
              "plates": {l.id: l.source for l in scene.env.layers}, "fx": scene.env.fx_source,
              "timeline": scene.timeline(),
              "transitions": [{"from": w.from_shot, "to": w.to_shot, "type": w.type, "boundary_s": w.boundary,
                               "boundary_frame": round(w.boundary * scene.fps), "window_s": [w.t_in, w.t_out]} for w in scene.windows],
              "frames_with_plate_holes": [(i["frame"], round(i["coverage"], 4)) for i in holes]}
    rp = out.with_suffix(".render.json")
    rp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[render] wrote {out} ({enc.frames} frames). Report: {rp}")
    if holes:
        print(f"[render] WARNING: {len(holes)} frame(s) show areas not covered by plates (see report).")
    return 0


def cmd_stills(args) -> int:
    Scene = scene_class(args.config)
    scene = Scene(args.config, test_plates=_resolve_test_dir(args), scale=args.scale)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i in _parse_frames(args.frames, scene.n_frames):
        Image.fromarray(scene.render_frame(i)).save(out / f"still_{i:04d}.png")
        print(out / f"still_{i:04d}.png")
    return 0


def cmd_test_assets(args) -> int:
    from .testassets import generate
    layout = generate(args.config, args.out_dir or default_test_dir(args.config), scene_class(args.config))
    print(json.dumps(layout, indent=2))
    return 0


def cmd_plate_spec(args) -> int:
    Scene = scene_class(args.config)
    scene = Scene(args.config, allow_missing_plates=True)
    req = scene.env.required_bounds(scene.all_cameras(), *scene.nominal_size, scene.frame_world_width, margin=args.margin)
    print(f"Plate coverage required by {Path(args.config).name} (world units; 1 unit = 1 px at zoom 1, wpp from manifest):")
    for lid, r in req.items():
        print(f"  {lid:24s} p={r['parallax']:<5} file={r['file']:22s} min size {r['min_size_px'][0]}x{r['min_size_px'][1]} px, "
              f"top-left at world {r['position']}")
    if args.json:
        Path(args.json).write_text(json.dumps(req, indent=2), encoding="utf-8")
    return 0


def contact_sheet(paths: list[Path], labels: list[str], out: Path, cols: int = 4, thumb_w: int = 480):
    ims = [Image.open(p).convert("RGB") for p in paths]
    th = int(thumb_w * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (th + 28)), (20, 20, 24))
    d = ImageDraw.Draw(sheet)
    for k, (im, lab) in enumerate(zip(ims, labels)):
        x, y = (k % cols) * thumb_w, (k // cols) * (th + 28)
        sheet.paste(im.resize((thumb_w, th), Image.LANCZOS), (x, y + 28))
        d.text((x + 6, y + 6), lab, fill=(240, 240, 240))
    sheet.save(out)


def cmd_qc(args) -> int:
    from .encode import extract_frames, probe
    Scene = scene_class(args.config)
    scene = Scene(args.config, allow_missing_plates=True)
    video = Path(args.video)
    out = Path(args.out_dir) if args.out_dir else video.parent / (video.stem + "_qc")
    out.mkdir(parents=True, exist_ok=True)
    pr = probe(video)
    W, H = scene.nominal_size
    checks = {
        "resolution": (pr["width"], pr["height"]) == (W, H),
        "fps": abs(pr["fps"] - scene.fps) < 1e-6,
        "frame_count": pr["frames"] == scene.n_frames,
        "duration": abs(pr["format_duration"] - scene.duration) < 0.5 / scene.fps + 1e-3,
        "codec_h264": pr["codec"] == "h264",
        "pix_fmt_yuv420p": pr["pix_fmt"] == "yuv420p",
        "container_mp4": "mp4" in (pr["container"] or ""),
        "aspect_16_9": abs(pr["width"] / pr["height"] - 16 / 9) < 1e-3,
    }
    # frames to inspect: start, each shot's first/last, transition windows, end
    picks = {0, scene.n_frames - 1}
    for row in scene.timeline():
        picks.update({row["first_frame"], max(row["first_frame"], row["last_frame"])})
    for w in scene.windows:
        b = round(w.boundary * scene.fps)
        picks.update({b - 1, b})
        if w.t_out > w.t_in:
            picks.update({round(w.t_in * scene.fps), round((w.t_in + w.t_out) / 2 * scene.fps), round(w.t_out * scene.fps) - 1})
    picks = sorted(p for p in picks if 0 <= p < scene.n_frames)
    paths = extract_frames(video, picks, out / "frames", scene.fps)
    labels = []
    for p in paths:
        n = int(p.stem.split("_")[1])
        t = n / scene.fps
        w = scene.window_at(t)
        labels.append(f"f{n:03d} t={t:.3f}s {scene.shot_at(t).id}" + (f" [{w.type}]" if w and w.type not in ('cut', 'cut_on_action') else ""))
    sheet = out / "contact_sheet.png"
    contact_sheet(paths, labels, sheet)
    report = {"video": str(video), "probe": pr, "checks": checks, "all_pass": all(checks.values()),
              "extracted_frames": [str(p) for p in paths], "contact_sheet": str(sheet)}
    (out / "qc_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"probe": pr, "checks": checks}, indent=2))
    print(f"[qc] {'PASS' if report['all_pass'] else 'FAIL'} — frames + contact sheet in {out}")
    return 0 if report["all_pass"] else 1


def cmd_ingest(args) -> int:
    from .plates import ingest
    only = [x.strip() for x in args.layers.split(",")] if args.layers else None
    res = ingest(Path(args.config), Path(args.inbox), only, args.tag)
    for lid, e in res["layers"].items():
        print(f"[ingest] {lid:24s} {e.get('archive'):28s} -> {e.get('status')}  {e.get('reason', '')}")
    print(f"[ingest] report: {Path(res['manifest']).parent / 'qc' / 'ingest_report.json'}")
    return 0


def cmd_place(args) -> int:
    from .plates import place
    for p in place(Path(args.config), [x.strip() for x in args.layers.split(",") if x.strip()]):
        print(f"[place] {p}")
    return 0


def cmd_stack(args) -> int:
    from .plates import stack_preview
    out = Path(args.out) if args.out else episode_dir(args.config) / "output" / "stack_preview" / "stack_reference.png"
    print(json.dumps(stack_preview(Path(args.config), out, scene_class(args.config), not args.no_character), indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="tools.render", description="Curious Mind 2D animation pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--config", required=True)
        p.add_argument("--test-plates", nargs="?", const="auto", default=None,
                       help="use generated TEST plates (not final art). Optional DIR, default <episode>/output/test_assets")
        p.add_argument("--scale", type=float, default=1.0, help="output scale for previews (1.0 = config size)")

    p = sub.add_parser("render"); common(p)
    p.add_argument("--out", required=True)
    p.add_argument("--frames", default=None, help="e.g. 0-47 or 0,70,130 (default: all)")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--crf", type=int, default=18)
    p.add_argument("--preset", default="medium")
    p.add_argument("--keep-frames", default=None, help="also save PNG frames to this folder")
    p.set_defaults(fn=cmd_render)

    p = sub.add_parser("stills"); common(p)
    p.add_argument("--frames", required=True)
    p.add_argument("--out-dir", required=True)
    p.set_defaults(fn=cmd_stills)

    p = sub.add_parser("test-assets")
    p.add_argument("--config", required=True)
    p.add_argument("--out-dir", default=None, help="default: <episode>/output/test_assets")
    p.set_defaults(fn=cmd_test_assets)

    p = sub.add_parser("plate-spec")
    p.add_argument("--config", required=True)
    p.add_argument("--margin", type=float, default=64.0)
    p.add_argument("--json", default=None)
    p.set_defaults(fn=cmd_plate_spec)

    p = sub.add_parser("qc")
    p.add_argument("--config", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--out-dir", default=None)
    p.set_defaults(fn=cmd_qc)

    p = sub.add_parser("ingest-plates", help="archive originals, key magenta, verify (writes new files only)")
    p.add_argument("--config", required=True)
    p.add_argument("--inbox", required=True, help="folder containing the delivered PNGs (fx/leaf_wipe.png may be flat)")
    p.add_argument("--layers", default=None, help="only these layer ids")
    p.add_argument("--tag", default="", help="label for a new keying pass (keeps earlier results), e.g. pass2")
    p.set_defaults(fn=cmd_ingest)

    p = sub.add_parser("place-plates", help="copy reviewed keyed/*_rgba.png to the manifest file names")
    p.add_argument("--config", required=True)
    p.add_argument("--layers", required=True, help="comma list, e.g. layer4_far_background,layer3_background,fx:leaf_wipe")
    p.set_defaults(fn=cmd_place)

    p = sub.add_parser("stack-preview", help="reference-camera composite of placed layers with horizon/ground/action guides")
    p.add_argument("--config", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--no-character", action="store_true")
    p.set_defaults(fn=cmd_stack)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except Exception as exc:  # friendly top-level errors
        if type(exc).__name__ in ("MissingPlateError", "FFmpegNotFound"):
            print(f"BLOCKED: {exc}", file=sys.stderr)
            return 2
        raise
