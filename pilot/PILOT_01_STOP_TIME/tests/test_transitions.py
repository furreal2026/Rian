"""Transitions tested on rendered frames using TEST assets (<episode>/output/test_assets, never final art)."""
import unittest
from pathlib import Path

import numpy as np

from tools.render import mathx as mx
from pilot.PILOT_01_STOP_TIME.transitions import transitions as tr
from pilot.PILOT_01_STOP_TIME.compositor.compositor import ConfigError, Scene
from tools.render.testassets import generate
from pilot.PILOT_01_STOP_TIME.compositor.compositor import Scene as _Scene
from pilot.PILOT_01_STOP_TIME.tests.helpers import EPISODE, PILOT, TempDir, pilot_config_without_final_plates

TEST_DIR = EPISODE / "output" / "test_assets"


def detail(rgb):
    """Mean absolute horizontal gradient: drops sharply under horizontal motion blur."""
    g = rgb.astype(np.float32).mean(axis=2)
    return float(np.abs(np.diff(g, axis=1)).mean())


class TransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (TEST_DIR / "test_layout.json").exists():
            generate(PILOT, TEST_DIR, _Scene)
        # final courtyard plates now exist next to the real manifest; these tests use the TEST assets,
        # so they run on a manifest copy that has no final plate files beside it
        cls._td = TempDir()
        cls.cfg = pilot_config_without_final_plates(cls._td.__enter__())
        cls.scene = Scene(cls.cfg, test_plates=TEST_DIR, scale=0.5)
        cls.w = {w.type: w for w in cls.scene.windows}

    # ------------------------------------------------------- cut on action
    def test_cut_on_action_lands_on_event_frame(self):
        w = self.w["cut_on_action"]
        ev = self.scene.character.events["snap"]
        b = round(w.boundary * 24)
        self.assertEqual(b, round(ev * 24))
        _, ia = self.scene.render_frame_rgba(b - 1)
        _, ib = self.scene.render_frame_rgba(b)
        self.assertEqual((ia["shot"], ib["shot"]), ("S01", "S02"))

    def test_cut_on_action_keeps_action_continuous(self):
        """The hand keeps moving through the cut along the same world trajectory."""
        sc = self.scene
        b = round(self.w["cut_on_action"].boundary * 24)

        def hand(i):
            t = i / 24
            _, _, view, _, _, params = sc.character.state(t)
            parts = {p.name: p for p in sc.rig.solve(view, params)}
            return mx.apply(sc.character.root_matrix(t) @ parts["hand_r"].m, 0, 0)

        pts = [hand(i) for i in range(b - 3, b + 3)]
        steps = [np.hypot(q[0] - p[0], q[1] - p[1]) for p, q in zip(pts, pts[1:])]
        self.assertGreater(steps[2], 0.5, "hand must be in motion at the cut (cut ON action)")
        self.assertLess(max(steps), 40, f"no jump in the action across the cut: {steps}")

    # ------------------------------------------------------------ whip pan
    def test_whip_offsets(self):
        w = self.w["whip_pan"]
        sid0, dx0 = tr.whip_offset(w, w.t_in, 1.0)
        sid1, dx1 = tr.whip_offset(w, w.boundary - 1e-6, 1.0)
        sid2, dx2 = tr.whip_offset(w, w.boundary, 1.0)
        sid3, dx3 = tr.whip_offset(w, w.t_out, 1.0)
        self.assertEqual((sid0, sid1, sid2, sid3), ("S02", "S02", "S03", "S03"))
        self.assertAlmostEqual(dx0, 0.0)
        self.assertAlmostEqual(dx1, 2200, delta=1)
        self.assertAlmostEqual(dx2, -2200, delta=1)
        self.assertAlmostEqual(dx3, 0.0)

    def test_whip_frames_are_motion_blurred(self):
        w = self.w["whip_pan"]
        b = round(w.boundary * 24)
        sharp_a = detail(self.scene.render_frame(round(w.t_in * 24) - 2))
        sharp_b = detail(self.scene.render_frame(round(w.t_out * 24) + 1))
        blurred = detail(self.scene.render_frame(b))
        self.assertLess(blurred, 0.35 * min(sharp_a, sharp_b), (blurred, sharp_a, sharp_b))
        # the frame at the boundary mixes both shots (samples straddle the cut)
        _, info = self.scene.render_frame_rgba(b)
        self.assertEqual(info["transition"], "whip_pan")

    # ----------------------------------------------------------- leaf wipe
    def test_leaf_matte_sweeps_full_frame(self):
        leaf = self.scene._leaf(self.w["leaf_wipe"])
        covs = [float(np.asarray(leaf.matte(u)).mean() / 255) for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
        self.assertLess(covs[0], 0.02)
        self.assertTrue(all(b >= a for a, b in zip(covs, covs[1:])), covs)
        self.assertGreater(covs[2], 0.3)
        self.assertGreater(covs[-1], 0.999, covs)

    def test_leaf_wipe_frames(self):
        w = self.w["leaf_wipe"]
        mid = round((w.t_in + w.t_out) / 2 * 24)
        img, info = self.scene.render_frame_rgba(mid)
        self.assertEqual(info["transition"], "leaf_wipe")
        self.assertTrue(0.2 < info["matte_coverage"] < 0.95, info)
        rgb = np.asarray(img.convert("RGB")).astype(int)
        green = ((rgb[..., 1] - rgb[..., 0] > 50) & (rgb[..., 1] - rgb[..., 2] > 40)).mean()
        self.assertGreater(green, 0.05, "leaf must be visible on top")
        _, after = self.scene.render_frame_rgba(round(w.t_out * 24))
        self.assertEqual(after["shot"], "S04")

    @classmethod
    def tearDownClass(cls):
        cls._td.__exit__(None, None, None)

    def test_leaf_wipe_requires_asset(self):
        sc = Scene(self.cfg, allow_missing_plates=True, scale=0.25)
        with self.assertRaises(ConfigError):
            sc._leaf(sc.windows[2])


if __name__ == "__main__":
    unittest.main()
