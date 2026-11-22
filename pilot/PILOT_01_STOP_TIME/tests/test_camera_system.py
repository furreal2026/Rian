"""Camera system tests: framings, moves, shake, lens vs dolly, coverage, new transitions (demo scene, real plates)."""
import json
import unittest
from pathlib import Path

from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.camera.camera import Camera, CameraState, Reference, layer_matrix, shake_envelope
from pilot.PILOT_01_STOP_TIME.camera.presets import FRAMINGS, PresetError, resolve_preset
from pilot.PILOT_01_STOP_TIME.compositor.compositor import ConfigError, Scene
from pilot.PILOT_01_STOP_TIME.tests.helpers import EPISODE

DEMO = EPISODE / "config" / "camera_demo_10_scenarios.json"
FOLLOW = lambda t: (-120.0, -140.0)  # fixed subject for preset resolution


def cam(cfg):
    return Camera(cfg, FOLLOW, 24.0, 300.0)


class FramingTests(unittest.TestCase):
    def test_all_framings_resolve_and_sizes_are_ordered(self):
        zooms = {}
        for name in FRAMINGS:
            c = cam({"preset": "static", "start": 0.0, "shot": name})
            zooms[name] = c.state(0.0).zoom
            self.assertGreater(zooms[name], 0.0)
        self.assertLess(zooms["establishing"], zooms["wide"])
        self.assertLess(zooms["wide"], zooms["medium"])
        self.assertLess(zooms["medium"], zooms["close_up"])
        self.assertLess(zooms["close_up"], zooms["extreme_close_up"])

    def test_high_and_low_angle_move_the_subject_in_frame_without_pitch(self):
        hi = cam({"preset": "static", "start": 0.0, "shot": "high_angle"}).state(0.0)
        lo = cam({"preset": "static", "start": 0.0, "shot": "low_angle"}).state(0.0)
        self.assertLess(hi.y, lo.y)  # a raised camera sits higher (smaller y = up)... subject lower in frame
        self.assertFalse(hasattr(hi, "pitch") or hasattr(hi, "yaw"), "no yaw/pitch exists: do not claim it")

    def test_over_the_shoulder_is_refused_not_faked(self):
        with self.assertRaises(PresetError):
            resolve_preset({"preset": "static", "start": 0.0, "shot": "over_the_shoulder"}, FOLLOW, 300.0)


class MoveTests(unittest.TestCase):
    def test_push_in_and_pull_back_change_zoom_monotonically(self):
        push = cam({"preset": "push_in", "start": 0.0, "end": 2.0, "shot_from": "wide", "shot_to": "medium"})
        back = cam({"preset": "pull_back", "start": 0.0, "end": 2.0, "zoom": 2.4, "zoom_to": 1.4})
        zp = [push.state(i / 24).zoom for i in range(0, 49)]
        zb = [back.state(i / 24).zoom for i in range(0, 49)]
        self.assertTrue(all(b >= a - 1e-9 for a, b in zip(zp, zp[1:])))
        self.assertTrue(all(b <= a + 1e-9 for a, b in zip(zb, zb[1:])))
        self.assertGreater(zp[-1], zp[0] * 1.4)
        self.assertLess(zb[-1], zb[0] * 0.7)

    def test_smooth_easings_have_zero_slope_at_both_ends(self):
        for name in ("smoothstep", "smootherstep", "inOutSine"):
            self.assertLess(abs(mx.ease(name, 1e-3) - mx.ease(name, 0.0)), 1e-4, name)
            self.assertLess(abs(mx.ease(name, 1.0) - mx.ease(name, 1.0 - 1e-3)), 1e-4, name)

    def test_lens_zoom_has_no_parallax_but_dolly_does(self):
        ref = Reference(0.0, 0.0, 1.0)
        far, near = 0.15, 1.5

        def scale(c, p):
            m = layer_matrix(c, p, ref, 1920, 1080)
            return m[0, 0]

        dolly = CameraState(0, 0, 2.0)
        lens = CameraState(0, 0, 1.0, 0.0, 2.0)
        # lens: every plane scales by the same factor
        self.assertAlmostEqual(scale(lens, near) / scale(lens, far), 1.0, places=6)
        # dolly: planes scale by zoom**p, so the near plane grows faster than the far one
        self.assertAlmostEqual(scale(dolly, near) / scale(dolly, far), 2.0 ** (near - far), places=6)

    def test_horizontal_track_follows_the_subject_with_lag(self):
        moving = lambda t: (200.0 * t, -140.0)
        c = Camera({"preset": "track_h", "start": 0.0, "end": 2.0, "shot": "wide", "lag": 0.35}, moving, 24.0, 300.0)
        x = [c.state(i / 24).x for i in range(0, 49)]
        self.assertGreater(x[-1], x[0] + 200.0)
        steps = [b - a for a, b in zip(x, x[1:])]
        self.assertLess(max(abs(b - a) for a, b in zip(steps, steps[1:])), 6.0, "tracking must not jerk")


class ShakeTests(unittest.TestCase):
    BASE = {"type": "shake", "start": 1.0, "duration": 1.0, "intensity": 1.0, "seed": 4}

    def make(self, intensity):
        m = dict(self.BASE, intensity=intensity)
        return Camera({"keys": [{"t": 0, "x": 0, "y": 0, "zoom": 1.0}], "modifiers": [m]})

    def test_zero_outside_window_and_envelope_range(self):
        c = self.make(1.0)
        self.assertEqual((c.state(0.5).x, c.state(0.5).y, c.state(0.5).rot), (0, 0, 0))
        self.assertEqual((c.state(2.6).x, c.state(2.6).y), (0, 0))
        for i in range(0, 120):
            self.assertTrue(0.0 <= shake_envelope(i / 24, self.BASE) <= 1.0)

    def test_deterministic_and_intensity_scales_amplitude(self):
        a, b = self.make(0.5), self.make(1.5)
        ts = [1.0 + i / 24 for i in range(1, 20)]
        self.assertEqual([a.state(t).x for t in ts], [self.make(0.5).state(t).x for t in ts])
        amp = lambda c: max(abs(c.state(t).x) + abs(c.state(t).y) for t in ts)
        self.assertGreater(amp(b), amp(a) * 2.0)

    def test_shake_is_continuous(self):
        c = self.make(1.0)
        xs = [c.state(1.0 + i / 240).x for i in range(0, 240)]
        self.assertLess(max(abs(b - a) for a, b in zip(xs, xs[1:])), 8.0)


class DemoSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = Scene(DEMO)

    def test_every_transition_type_in_demo_is_resolved(self):
        types = {w.type for w in self.scene.windows}
        for t in ("match_cut", "blur", "whip_pan", "push_through", "cut_on_action", "foreground_wipe"):
            self.assertIn(t, types)

    def test_cut_on_action_lands_on_the_snap_event(self):
        w = next(w for w in self.scene.windows if w.type == "cut_on_action")
        self.assertLess(abs(w.boundary - 16.4), 1.0 / 24 + 1e-6)

    def test_match_cut_records_a_matched_frame(self):
        w = next(w for w in self.scene.windows if w.type == "match_cut")
        self.assertLess(w.params["match"]["pos_error_frac"], 0.04)

    def test_match_cut_with_mismatched_framing_is_rejected(self):
        cfg = json.loads(DEMO.read_text(encoding="utf-8"))
        cfg["shots"][1]["camera"] = {"preset": "static", "start": 2.2, "shot": "extreme_close_up"}
        tmp = DEMO.with_name("_tmp_match_mismatch_test.json")
        try:
            tmp.write_text(json.dumps(cfg), encoding="utf-8")
            with self.assertRaises(ConfigError):
                Scene(tmp)
        finally:
            tmp.unlink(missing_ok=True)

    def test_all_cameras_including_transition_offsets_stay_on_painted_plates(self):
        bad = [i for i, c in enumerate(self.scene.all_cameras()) if not self.scene.env.view_painted(c, 1920, 1080)]
        self.assertEqual(bad, [])
        self.assertEqual(self.scene.coverage_log, [])

    def test_clamp_pulls_an_out_of_range_camera_back_onto_plates(self):
        env = self.scene.env
        out = CameraState(900, -100, 1.4)
        self.assertFalse(env.view_painted(out, 1920, 1080))
        fixed, ok = env.clamp_camera(out, 1920, 1080)
        self.assertTrue(ok)
        self.assertTrue(env.view_painted(fixed, 1920, 1080))

    def test_rendered_demo_frames_are_valid_images_at_transition_peaks(self):
        for i in (53, 105, 181, 250, 277, 394, 468):  # match cut, blur, whip, track, push_through, cut_on_action, wipe
            img, info = self.scene.render_frame_rgba(i)
            self.assertEqual(img.size, (1920, 1080))
            self.assertGreater(img.getchannel("A").getextrema()[0], 250, f"transparent pixels in frame {i}")


if __name__ == "__main__":
    unittest.main()
