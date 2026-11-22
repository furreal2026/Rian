"""Chroma key tests on a synthetic magenta plate (TEST image only, generated in a temp dir)."""
import unittest

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pilot.PILOT_01_STOP_TIME.tests.helpers import TempDir
from tools.render import chroma_key as ck

BG = (247, 6, 241)          # real-world magenta, deliberately not #FF00FF
LEAF = (60, 140, 60)
PURPLE = (150, 60, 170)     # legit purple inside an object


def synthetic(path, size=(900, 600)):
    w, h = size
    ss = 4
    big = Image.new("RGB", (w * ss, h * ss), BG)
    d = ImageDraw.Draw(big)
    d.ellipse([200 * ss, 150 * ss, 600 * ss, 450 * ss], fill=LEAF)                 # object
    d.ellipse([330 * ss, 230 * ss, 400 * ss, 300 * ss], fill=PURPLE)               # purple flower inside
    d.ellipse([460 * ss, 320 * ss, 520 * ss, 380 * ss], fill=BG)                   # enclosed magenta gap
    d.line([(600 * ss, 300 * ss), (850 * ss, 120 * ss)], fill=LEAF, width=int(1.2 * ss))  # ~1 px tendril
    d.line([(100 * ss, 500 * ss), (300 * ss, 560 * ss)], fill=PURPLE, width=3 * ss)       # purple twig touching bg
    img = big.resize((w, h), Image.BOX)                                            # anti-aliased, spill in edges
    a = np.asarray(img).astype(np.int16)
    rng = np.random.default_rng(3)
    a = a + rng.integers(-3, 4, a.shape)                                           # sensor-like noise
    a[..., 0] += (np.linspace(-4, 4, w)[None, :]).astype(np.int16)                 # slight gradient
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)
    return np.asarray(Image.open(path))


class ChromaKeyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = TempDir()
        tmp = cls.td.__enter__()
        cls.src = tmp / "plate.png"
        cls.orig = synthetic(cls.src)
        cls.orig_bytes = cls.src.read_bytes()
        cls.res, cls.rep, cls.maps = ck.key_magenta(cls.src, tmp / "plate_rgba.png")
        cls.res.save(tmp / "plate_rgba.png")
        cls.a = np.asarray(cls.res)
        cls.tmp = tmp

    @classmethod
    def tearDownClass(cls):
        cls.td.__exit__(None, None, None)

    def test_samples_real_background(self):
        self.assertLess(np.abs(np.array(self.rep.bg_sample_rgb) - BG).max(), 6, self.rep.bg_sample_rgb)
        self.assertGreater(self.rep.tol_outer, self.rep.tol_inner)

    def test_background_transparent_object_opaque(self):
        self.assertEqual(self.a[20, 20, 3], 0)
        self.assertEqual(self.a[300, 260, 3], 255)
        self.assertEqual(self.rep.unconnected_transparent_px, 0)
        self.assertEqual(self.rep.object_px_made_transparent, 0)

    def test_enclosed_purple_and_magenta_kept(self):
        self.assertEqual(self.a[265, 365, 3], 255)                       # purple flower opaque
        self.assertTrue(np.array_equal(self.a[265, 365, :3], self.orig[265, 365]))  # colour untouched
        self.assertEqual(self.a[350, 490, 3], 255)                       # enclosed magenta gap kept
        self.assertGreater(self.rep.enclosed_bg_colour_area_px, 1500)
        self.assertTrue(any(i["bbox"][0] >= 455 and i["bbox"][2] <= 525 for i in self.rep.enclosed_bg_colour_islands))

    def test_thin_detail_survives(self):
        # sample along the 1.2 px tendril: alpha must stay substantial
        alphas = []
        for t in np.linspace(0.1, 0.9, 30):
            x, y = 600 + 250 * t, 300 - 180 * t
            alphas.append(self.a[int(round(y)) - 1:int(round(y)) + 2, int(round(x)) - 1:int(round(x)) + 2, 3].max())
        self.assertGreater(min(alphas), 150, alphas)
        # purple twig touching the background keeps its purple core
        self.assertEqual(self.a[530, 200, 3], 255)
        self.assertLess(np.abs(self.a[530, 200, :3].astype(int) - PURPLE).max(), 25)

    def test_graded_edges_and_no_magenta_fringe(self):
        self.assertGreater(self.rep.partial_px, 500)
        self.assertLess(self.rep.residual_fringe_ratio, 0.01)
        edge = (self.a[..., 3] > 10) & (self.a[..., 3] < 245)
        rgb = self.a[..., :3].astype(int)
        mag = (np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1])[edge & (np.abs(np.arange(900)[None, :] - 400) < 1000)]
        # around the green leaf the unmixed edge colour must not be magenta
        leaf_edge = edge.copy()
        leaf_edge[:, 600:] = False
        leaf_edge[480:, :] = False
        m = (np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1])[leaf_edge]
        self.assertLess(np.percentile(m, 95), 20)

    def test_interior_untouched_and_original_preserved(self):
        inner = np.zeros(self.a.shape[:2], bool)
        inner[200:400, 250:550] = True
        inner &= ~ck.dilate(self.a[..., 3] < 255, 6)
        self.assertTrue(np.array_equal(self.a[inner][:, :3], self.orig[inner]))
        self.assertEqual(self.src.read_bytes(), self.orig_bytes)

    def test_previews_and_format(self):
        ps = ck.composite_previews(self.res, self.tmp / "pv", "plate")
        self.assertEqual([p.name for p in ps], ["plate_on_white.png", "plate_on_black.png", "plate_on_gray50.png"])
        chk = ck.check_output(self.tmp / "plate_rgba.png", min_size=(900, 600))
        self.assertTrue(chk["pass"], chk)

    def test_connectivity_helper(self):
        m = np.zeros((7, 7), bool)
        m[1:6, 1] = m[5, 1:6] = m[1:6, 5] = True   # U shape
        m[3, 3] = True                             # isolated
        seed = np.zeros_like(m)
        seed[1, 1] = True
        r = ck.connected_from(m, seed)
        self.assertTrue(r[1, 5] and not r[3, 3])
        self.assertTrue(np.array_equal(ck.dilate(np.pad([[True]], 2), 1)[1:4, 1:4], np.ones((3, 3), bool)))


if __name__ == "__main__":
    unittest.main()


class FeatherDecisionTests(unittest.TestCase):
    def _run(self, aa: bool):
        with TempDir() as tmp:
            w, h = 400, 300
            if aa:
                big = Image.new("RGB", (w * 4, h * 4), BG)
                ImageDraw.Draw(big).ellipse([400, 300, 1200, 900], fill=LEAF)
                img = big.resize((w, h), Image.BOX)
            else:
                img = Image.new("RGB", (w, h), BG)
                ImageDraw.Draw(img).ellipse([100, 75, 300, 225], fill=LEAF)   # hard, aliased edge
            img.save(tmp / "p.png")
            return ck.key_magenta(tmp / "p.png", tmp / "o.png")[1]

    def test_antialiased_edge_not_feathered(self):
        rep = self._run(True)
        self.assertFalse(rep.feather_applied, rep.partial_ratio)

    def test_hard_edge_feathered_only_at_edge(self):
        rep = self._run(False)
        self.assertTrue(rep.feather_applied, rep.partial_ratio)
