import math
import unittest

import numpy as np

from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.camera.camera import Camera, CameraState, Reference, layer_matrix
from pilot.PILOT_01_STOP_TIME.compositor.compositor import Scene
from pilot.PILOT_01_STOP_TIME.tests.helpers import PILOT


class TrackAndEasingTests(unittest.TestCase):
    def test_easing_endpoints(self):
        for name in mx.EASINGS:
            self.assertAlmostEqual(mx.ease(name, 0.0), 0.0, places=6, msg=name)
            self.assertAlmostEqual(mx.ease(name, 1.0), 1.0, places=6, msg=name)

    def test_track_interpolates_per_field_and_holds(self):
        tr = mx.Track([{"t": 0, "x": 0, "view": "front"}, {"t": 1, "x": 10, "ease": "linear"}, {"t": 2, "view": "side"}])
        self.assertEqual(tr.value(-1, "x"), 0)
        self.assertAlmostEqual(tr.value(0.25, "x"), 2.5)
        self.assertEqual(tr.value(5, "x"), 10)
        self.assertEqual(tr.value(1.99, "view"), "front")
        self.assertEqual(tr.value(2.0, "view"), "side")


class CameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = Scene(PILOT, allow_missing_plates=True)

    def series(self, sid, attr):
        s = self.scene.shot(sid)
        fr = range(int(round(s.start * 24)), int(round(s.end * 24)))
        return [getattr(s.camera.state(i / 24), attr) for i in fr], [getattr(s.camera.base(i / 24), attr) for i in fr]

    def test_tilt_down_S01(self):
        ys, base = self.series("S01", "y")
        self.assertLess(base[0], -1300)
        self.assertAlmostEqual(base[-1], -400, delta=1)
        self.assertTrue(all(b2 >= b1 - 1e-9 for b1, b2 in zip(base, base[1:])), "tilt must move monotonically down")
        self.assertGreater(ys[-1] - ys[0], 900)

    def test_drift_is_smooth_bounded_and_deterministic(self):
        s = self.scene.shot("S02")
        xs = [s.camera.state(3.0 + i / 24).x - s.camera.base(3.0 + i / 24).x for i in range(48)]
        self.assertGreater(max(xs) - min(xs), 2.0, "drift must actually move the camera")
        self.assertLessEqual(max(abs(v) for v in xs), 10.0 + 1e-6)
        steps = [abs(b - a) for a, b in zip(xs, xs[1:])]
        self.assertLess(max(steps), 1.5, "drift must be smooth frame to frame")
        self.assertEqual(xs, [s.camera.state(3.0 + i / 24).x - s.camera.base(3.0 + i / 24).x for i in range(48)])

    def test_tracking_follows_character_with_lag(self):
        s = self.scene.shot("S03")
        ch = self.scene.character
        t_mid, t_end = 6.5, 7.79
        cx_mid = s.camera.state(t_mid).x
        x_mid = ch.root(t_mid)[0]
        self.assertLess(cx_mid, x_mid + 110, "lagged camera trails the moving target")
        self.assertGreater(cx_mid, x_mid - 200)
        # after the character stops (t=7.6) the lagged camera keeps converging on target + lead offset
        err_stop = abs(s.camera.state(7.6).x - (ch.root(7.6)[0] + 110))
        err_end = abs(s.camera.state(t_end).x - (ch.root(t_end)[0] + 110))
        self.assertLess(err_end, err_stop * 0.7)
        self.assertLess(err_end, 60)
        xs = [s.camera.state(5.3 + i / 24).x for i in range(55)]
        self.assertGreater(xs[-1] - xs[0], 500)

    def test_pull_back_S04(self):
        zs, base = self.series("S04", "zoom")
        self.assertAlmostEqual(base[0], 1.75, delta=1e-6)
        self.assertLess(base[-1], 0.75)
        self.assertTrue(all(b2 <= b1 + 1e-9 for b1, b2 in zip(base, base[1:])))

    def test_cut_is_a_discontinuity(self):
        b = round(self.scene.windows[0].boundary * 24)
        a = self.scene.camera_at(self.scene.shot_at((b - 1) / 24), (b - 1) / 24)
        c = self.scene.camera_at(self.scene.shot_at(b / 24), b / 24)
        self.assertGreater(abs(c.zoom - a.zoom), 0.5)

    def test_projection(self):
        ref = Reference(0, 0, 1)
        cam = CameraState(100, -50, 2.0, 0.0)
        m = layer_matrix(cam, 1.0, ref, 1920, 1080)
        self.assertEqual(tuple(np.round(mx.apply(m, 100, -50), 6)), (960.0, 540.0))
        x1, _ = mx.apply(m, 110, -50)
        self.assertAlmostEqual(x1 - 960, 20.0)  # zoom 2 doubles distances
        m_half = layer_matrix(cam, 1.0, ref, 960, 540)
        self.assertAlmostEqual(mx.apply(m_half, 110, -50)[0] - 480, 10.0)  # resolution independent
        mr = layer_matrix(CameraState(0, 0, 1, 90), 1.0, ref, 1920, 1080)
        x, y = mx.apply(mr, 100, 0)
        self.assertAlmostEqual(x, 960, places=6)   # roll rotates the view
        self.assertAlmostEqual(y, 440, places=6)


if __name__ == "__main__":
    unittest.main()
