"""Shared fixtures: synthetic TEST environments built in temp dirs (never final art)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

EPISODE = Path(__file__).resolve().parents[1]
REPO = EPISODE.parents[1]
RIG = EPISODE / "rig" / "stick_figure_rig.json"
POSES = EPISODE / "rig" / "poses.json"
PILOT = EPISODE / "config" / "pilot_01_stop_time.json"
PARALLAX = {"L1": 1.5, "L2": 1.0, "L3": 0.35, "L4": 0.15}
COLORS = {"L1": (255, 0, 0), "L2": (0, 255, 0), "L3": (0, 0, 255), "L4": (255, 0, 255)}


def marker_plate(path: Path, size=(4000, 3000), marker_xy=(2000, 1500), color=(255, 0, 0), r=6, opaque_bg=None):
    img = Image.new("RGBA", size, (0, 0, 0, 0) if opaque_bg is None else opaque_bg + (255,))
    d = ImageDraw.Draw(img)
    x, y = marker_xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,))
    img.save(path)


def synthetic_scene(tmp: Path, layers: dict, shots: list, character_keys=None, transitions=None, fx=None, character_z=25,
                    duration=1.0, size=(1920, 1080)) -> Path:
    """layers: id -> dict(file, parallax, z, position). Writes manifest + scene config, returns config path."""
    manifest = {
        "name": "synthetic_test", "world_units_per_pixel": 1.0,
        "reference_camera": {"x": 0, "y": 0, "zoom": 1.0}, "ground_y": 0, "character_z": character_z,
        "layers": [dict(id=k, **v) for k, v in layers.items()], "fx": fx or {},
    }
    (tmp / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    cfg = {
        "title": "synthetic", "output": {"width": size[0], "height": size[1], "fps": 24, "duration": duration},
        "environment": {"manifest": "manifest.json"},
        "character": {"rig": str(RIG), "poses": str(POSES), "height": 430,
                      "keys": character_keys or [{"t": 0, "x": 0, "y": 0, "view": "front", "pose": "stand"}]},
        "shots": shots, "transitions": transitions or [],
    }
    p = tmp / "scene.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


class TempDir:
    def __enter__(self):
        self._td = tempfile.TemporaryDirectory()
        return Path(self._td.name)

    def __exit__(self, *a):
        self._td.cleanup()


def pilot_config_without_final_plates(tmp: Path) -> Path:
    """Copy of the pilot technical config + courtyard manifest in `tmp`, where no final plate files exist.
    Lets tests exercise TEST-plate and BLOCKED behaviour now that the real courtyard plates are delivered."""
    man_src = EPISODE / "assets" / "environment" / "courtyard" / "manifest.json"
    (tmp / "env").mkdir(parents=True, exist_ok=True)
    (tmp / "env" / "manifest.json").write_text(man_src.read_text(encoding="utf-8"), encoding="utf-8")
    cfg = json.loads(PILOT.read_text(encoding="utf-8"))
    cfg["environment"]["manifest"] = str(tmp / "env" / "manifest.json")
    cfg["character"]["rig"] = str(RIG)
    cfg["character"]["poses"] = str(POSES)
    p = tmp / "pilot_no_final_plates.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p
