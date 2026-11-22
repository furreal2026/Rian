"""End-to-end plate intake on synthetic magenta TEST plates in a temp folder (never the real courtyard)."""
import json
import unittest

import numpy as np
from PIL import Image, ImageDraw

from pilot.PILOT_01_STOP_TIME.compositor.compositor import Scene
from pilot.PILOT_01_STOP_TIME.tests.helpers import TempDir, synthetic_scene
from tools.render import plates

BG = (250, 4, 246)


def magenta_plate(path, size, draw):
    img = Image.new("RGB", size, BG)
    draw(ImageDraw.Draw(img), size)
    img.save(path)


class PlateIntakeTests(unittest.TestCase):
    def test_archive_key_verify_place_preview(self):
        with TempDir() as tmp:
            env = tmp / "env"
            env.mkdir()
            layers = {
                "layer4_far_background": {"file": "far.png", "parallax": 0.15, "z": 0, "position": [-1300, -1000], "min_size_px": [2600, 1600]},
                "layer2_midground": {"file": "mid.png", "parallax": 1.0, "z": 20, "position": [-1300, -1000], "min_size_px": [2600, 1600]},
            }
            cfg = synthetic_scene(env, layers, [{"id": "A", "start": 0, "end": 1, "camera": {"keys": [{"t": 0, "x": 0, "y": -300}]}}],
                                  fx={"leaf_wipe": "fx/leaf_wipe.png"})
            inbox = tmp / "inbox"
            (inbox / "fx").mkdir(parents=True)
            Image.new("RGB", (2600, 1600), (120, 170, 220)).save(inbox / "far.png")
            magenta_plate(inbox / "mid.png", (2600, 1600), lambda d, s: d.rectangle([0, 1200, s[0], s[1]], fill=(150, 120, 90)))
            magenta_plate(inbox / "fx" / "leaf_wipe.png", (2600, 1000), lambda d, s: d.ellipse([20, 20, s[0] - 20, s[1] - 20], fill=(60, 150, 60)))
            Image.new("RGB", (100, 60), (0, 0, 0)).save(inbox / "courtyard_master_ref.png")
            orig = {p.name: p.read_bytes() for p in inbox.rglob("*.png")}

            res = plates.ingest(cfg, inbox)
            L = res["layers"]
            self.assertEqual(L["layer4_far_background"]["status"], "NEEDS_REVIEW")
            self.assertEqual(L["layer4_far_background"]["opaque_check"]["min_alpha"], 255)
            self.assertEqual(L["layer2_midground"]["status"], "NEEDS_REVIEW")
            self.assertEqual(L["fx:leaf_wipe"]["status"], "NEEDS_REVIEW")
            self.assertEqual(res["extra"]["courtyard_master_ref.png"]["status"], "archived")
            # originals archived byte-identical, inbox untouched
            for p in (env / "source").rglob("*.png"):
                self.assertEqual(p.read_bytes(), orig[p.name])
            # keyed copies are new files, previews exist
            mid = np.asarray(Image.open(env / "keyed" / "mid_rgba.png"))
            self.assertEqual(mid[100, 100, 3], 0)
            self.assertEqual(mid[1400, 100, 3], 255)
            for bgname in ("white", "black", "gray50"):
                self.assertTrue((env / "qc" / "mid" / f"mid_on_{bgname}.png").exists())
            # re-ingest never overwrites results
            with self.assertRaises(FileExistsError):
                plates.ingest(cfg, inbox)
            # placement + stack preview at the reference camera
            placed = plates.place(cfg, ["layer4_far_background", "layer2_midground", "fx:leaf_wipe"])
            self.assertEqual(len(placed), 3)
            info = plates.stack_preview(cfg, tmp / "stack.png", Scene)
            self.assertEqual(info["layers"], {"layer4_far_background": "final", "layer2_midground": "final"})
            self.assertGreater(info["coverage"], 0.999)


if __name__ == "__main__":
    unittest.main()
