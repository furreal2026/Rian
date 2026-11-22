import unittest

import numpy as np
from PIL import Image

from pilot.PILOT_01_STOP_TIME.compositor.compositor import ConfigError, Scene
from pilot.PILOT_01_STOP_TIME.compositor.environment import MissingPlateError
from pilot.PILOT_01_STOP_TIME.tests.helpers import PILOT, TempDir, synthetic_scene


def solid(path, color, size=(3000, 2000), alpha=255, box=None):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    if box is None:
        img.paste(color + (alpha,), (0, 0, size[0], size[1]))
    else:
        img.paste(color + (alpha,), box)
    img.save(path)


class CompositorTests(unittest.TestCase):
    def _layered(self, tmp, fg_box):
        solid(tmp / "bg.png", (0, 0, 255))                     # opaque far plate
        solid(tmp / "mid.png", (0, 255, 0), box=(0, 1400, 3000, 2000))  # ground strip below y=-100
        solid(tmp / "fg.png", (255, 0, 0), box=fg_box)         # foreground block
        layers = {
            "layer4": {"file": "bg.png", "parallax": 0.15, "z": 0, "position": [-1500, -1500]},
            "layer2": {"file": "mid.png", "parallax": 1.0, "z": 20, "position": [-1500, -1500]},
            "layer1": {"file": "fg.png", "parallax": 1.5, "z": 30, "position": [-1500, -1500]},
        }
        shots = [{"id": "A", "start": 0, "end": 1.0, "camera": {"keys": [{"t": 0, "x": 0, "y": -300, "zoom": 1}]}}]
        return Scene(synthetic_scene(tmp, layers, shots))

    def test_layer_order_and_character_insertion(self):
        with TempDir() as tmp:
            # foreground block covers world x in [60, 360] (screen right of the character)
            sc = self._layered(tmp, fg_box=(1560, 0, 1860, 2000))
            img, info = sc.render_frame_rgba(0)
            rgb = np.asarray(img.convert("RGB"))
            self.assertEqual(sc.coverage(img), 1.0)
            cx = 960
            # torso (red shirt) at world y ~ -220 (430-unit character) -> screen y 620
            self.assertTrue(np.allclose(rgb[620, cx], (217, 70, 63), atol=30), rgb[620, cx])
            self.assertTrue((rgb[200, 200] == (0, 0, 255)).all())  # sky = far plate
            self.assertTrue((rgb[1000, 200] == (0, 255, 0)).all())  # ground = midground
            self.assertTrue((rgb[540, cx + 200] == (255, 0, 0)).all())  # foreground over everything
            # same scene, foreground moved over the character: it must hide him
            sc2 = self._layered(tmp, fg_box=(1400, 0, 1600, 2000))
            rgb2 = sc2.render_frame(0)
            self.assertTrue((rgb2[620, cx] == (255, 0, 0)).all())

    def test_deterministic(self):
        with TempDir() as tmp:
            sc = self._layered(tmp, fg_box=(1560, 0, 1860, 2000))
            self.assertTrue(np.array_equal(sc.render_frame(5), sc.render_frame(5)))

    def test_missing_plates_block_final_render(self):
        with self.assertRaises(MissingPlateError):
            Scene(PILOT)

    def test_pilot_timeline(self):
        sc = Scene(PILOT, allow_missing_plates=True)
        self.assertEqual((sc.width, sc.height, sc.fps, sc.n_frames), (1920, 1080, 24.0, 240))
        rows = sc.timeline()
        self.assertEqual([r["shot"] for r in rows], ["S01", "S02", "S03", "S04"])
        self.assertEqual(sum(r["frames"] for r in rows), 240)
        for a, b in zip(rows, rows[1:]):
            self.assertEqual(a["last_frame"] + 1, b["first_frame"])
        self.assertEqual([w.type for w in sc.windows], ["cut_on_action", "whip_pan", "leaf_wipe"])

    def test_character_scale_and_position_consistent(self):
        sc = Scene(PILOT, allow_missing_plates=True)
        scales = {round(abs(sc.character.root_matrix(i / 24)[0, 0]), 9) for i in range(240)}
        self.assertEqual(len(scales), 1)
        xs = [sc.character.root(i / 24)[0] for i in range(240)]
        self.assertLess(max(abs(b - a) for a, b in zip(xs, xs[1:])), 30, "no position jumps across shots")

    def test_bad_config_rejected(self):
        with TempDir() as tmp:
            solid(tmp / "bg.png", (0, 0, 255))
            layers = {"layer4": {"file": "bg.png", "parallax": 0.15, "z": 0, "position": [-1500, -1500]}}
            shots = [{"id": "A", "start": 0, "end": 0.5, "camera": {"keys": [{"t": 0, "x": 0, "y": 0}]}},
                     {"id": "B", "start": 0.5, "end": 1, "camera": {"keys": [{"t": 0, "x": 0, "y": 0}]}}]
            p = synthetic_scene(tmp, layers, shots, transitions=[{"from": "A", "to": "B", "type": "whip_pan"}])
            with self.assertRaises(ConfigError):
                Scene(p)


if __name__ == "__main__":
    unittest.main()
