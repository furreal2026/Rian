"""Parallax measured on rendered pixels, not just on configuration values."""
import unittest

import numpy as np

from pilot.PILOT_01_STOP_TIME.camera.camera import CameraState
from pilot.PILOT_01_STOP_TIME.compositor.compositor import Scene
from pilot.PILOT_01_STOP_TIME.tests.helpers import COLORS, PARALLAX, PILOT, TempDir, marker_plate, synthetic_scene


def centroid(rgb, color, tol=40):
    m = np.all(np.abs(rgb.astype(int) - np.array(color)) < tol, axis=2)
    ys, xs = np.nonzero(m)
    if len(xs) < 5:
        return None
    return xs.mean(), ys.mean()


class ParallaxRenderTests(unittest.TestCase):
    def _scene(self, tmp, cam_keys):
        layers = {}
        for i, (lid, p) in enumerate(PARALLAX.items()):
            # stagger markers vertically so they never overlap
            marker_plate(tmp / f"{lid}.png", size=(4000, 3000), marker_xy=(2000, 1200 + 150 * i), color=COLORS[lid], r=7)
            layers[lid] = {"file": f"{lid}.png", "parallax": p, "z": {1.5: 30, 1.0: 20, 0.35: 10, 0.15: 0}[p], "position": [-2000, -1500]}
        shots = [{"id": "A", "start": 0, "end": 1.0, "camera": {"keys": cam_keys}}]
        return Scene(synthetic_scene(tmp, layers, shots, character_keys=[{"t": 0, "x": 5000, "y": 0, "view": "front", "pose": "stand"}]))

    def test_horizontal_pan_ratios(self):
        with TempDir() as tmp:
            sc = self._scene(tmp, [{"t": 0, "x": 0, "y": 0, "zoom": 1}, {"t": 1, "x": 200, "ease": "linear"}])
            f0, f1 = sc.render_frame(0), sc.render_frame(12)  # t = 0 and 0.5 -> camera moved 100 units
            shifts = {}
            for lid in PARALLAX:
                a, b = centroid(f0, COLORS[lid]), centroid(f1, COLORS[lid])
                self.assertIsNotNone(a, lid)
                self.assertIsNotNone(b, lid)
                shifts[lid] = a[0] - b[0]
                self.assertAlmostEqual(a[1], b[1], delta=0.5)
            for lid, p in PARALLAX.items():
                self.assertAlmostEqual(shifts[lid], 100 * p, delta=0.6, msg=f"{lid}: {shifts}")
            self.assertGreater(shifts["L1"], shifts["L2"])
            self.assertGreater(shifts["L2"], shifts["L3"])
            self.assertGreater(shifts["L3"], shifts["L4"])

    def test_vertical_tilt_ratios(self):
        with TempDir() as tmp:
            sc = self._scene(tmp, [{"t": 0, "x": 0, "y": 0, "zoom": 1}, {"t": 1, "y": -160, "ease": "linear"}])
            f0, f1 = sc.render_frame(0), sc.render_frame(12)
            for lid, p in PARALLAX.items():
                a, b = centroid(f0, COLORS[lid]), centroid(f1, COLORS[lid])
                self.assertAlmostEqual(b[1] - a[1], 80 * p, delta=0.6, msg=lid)

    def test_pilot_layers_use_approved_ratios(self):
        sc = Scene(PILOT, allow_missing_plates=True)
        got = sorted((l.parallax for l in sc.env.layers), reverse=True)
        self.assertEqual(got, [1.5, 1.0, 0.35, 0.15])
        names = {l.parallax: l.id for l in sc.env.layers}
        self.assertTrue(names[1.5].startswith("layer1"))
        self.assertTrue(names[1.0].startswith("layer2"))
        self.assertTrue(names[0.35].startswith("layer3"))
        self.assertTrue(names[0.15].startswith("layer4"))


if __name__ == "__main__":
    unittest.main()
