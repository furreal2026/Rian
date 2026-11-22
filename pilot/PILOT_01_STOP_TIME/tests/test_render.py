"""MP4 export through FFmpeg, verified with ffprobe."""
import os
import subprocess
import sys
import unittest

from tools.render.encode import probe
from pilot.PILOT_01_STOP_TIME.tests.helpers import EPISODE, PILOT, REPO, TempDir, pilot_config_without_final_plates

OUT = EPISODE / "output" / "test"


class RenderExportTests(unittest.TestCase):
    def test_short_full_resolution_clip(self):
        out = OUT / "export_check_TEST.mp4"
        cmd = [sys.executable, "-m", "tools.render", "render", "--config", str(PILOT), "--test-plates",
               "--out", str(out), "--frames", "60-83", "--workers", "2"]
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        p = probe(out)
        self.assertEqual((p["width"], p["height"]), (1920, 1080))
        self.assertEqual(p["fps"], 24.0)
        self.assertEqual(p["frames"], 24)
        self.assertAlmostEqual(p["format_duration"], 1.0, delta=0.05)
        self.assertEqual((p["codec"], p["pix_fmt"]), ("h264", "yuv420p"))

    def test_final_render_blocked_without_plates(self):
        """CLI refuses a final render when plates are missing: exit code 2, BLOCKED message, no video."""
        import contextlib
        import io
        from pilot.PILOT_01_STOP_TIME.compositor.compositor import Scene
        from tools.render import cli
        with TempDir() as tmp:
            cfg = pilot_config_without_final_plates(tmp)
            out = tmp / "should_not_exist.mp4"
            orig = cli.scene_class
            cli.scene_class = lambda config: Scene  # the temp config lives outside the episode folder
            err = io.StringIO()
            try:
                with contextlib.redirect_stderr(err):
                    code = cli.main(["render", "--config", str(cfg), "--out", str(out), "--workers", "1"])
            finally:
                cli.scene_class = orig
            self.assertEqual(code, 2)
            self.assertIn("BLOCKED", err.getvalue())
            self.assertFalse(out.exists())

    @unittest.skipUnless(os.environ.get("CM_FULL_RENDER") == "1", "set CM_FULL_RENDER=1 to render and QC all 240 frames")
    def test_full_pilot_render_and_qc(self):
        out = OUT / "pilot_01_stop_time_TEST.mp4"
        r = subprocess.run([sys.executable, "tools/render/render.py", str(EPISODE), "--test-plates", "--out", str(out)], cwd=REPO, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
