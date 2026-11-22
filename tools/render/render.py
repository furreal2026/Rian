"""One command: render an episode to MP4 and QC it.

    python tools/render/render.py                                  # Pilot 01, final (needs courtyard plates, else BLOCKED)
    python tools/render/render.py --test-plates                    # Pilot 01 with generated TEST plates (not final art)
    python tools/render/render.py pilot/PILOT_01_STOP_TIME --test-plates

Options: --config PATH (if the episode has several configs)  --out PATH  --scale 0.5 (preview, no QC)  --workers N  --no-qc
Outputs go to <episode>/output/ (final) or <episode>/output/test/ (test plates).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.render.cli import main as cli  # noqa: E402

DEFAULT_EPISODE = REPO / "pilot" / "PILOT_01_STOP_TIME"


def find_config(episode: Path) -> Path:
    cfgs = sorted((episode / "config").glob("*.json"))
    if len(cfgs) != 1:
        raise SystemExit(f"expected exactly one config in {episode / 'config'}, found {len(cfgs)}; pass --config")
    return cfgs[0]


def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode", nargs="?", default=str(DEFAULT_EPISODE))
    ap.add_argument("--config", default=None)
    ap.add_argument("--test-plates", nargs="?", const="auto", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--no-qc", action="store_true")
    a = ap.parse_args(argv)
    episode = Path(a.episode).resolve()
    config = Path(a.config).resolve() if a.config else find_config(episode)
    stem = config.stem
    if a.out:
        out = Path(a.out)
    elif a.test_plates:
        out = episode / "output" / "test" / f"{stem}_TEST.mp4"
    else:
        out = episode / "output" / f"{stem}.mp4"
    argv2 = ["render", "--config", str(config), "--out", str(out), "--scale", str(a.scale)]
    if a.test_plates:
        argv2 += ["--test-plates"] + ([a.test_plates] if a.test_plates != "auto" else [])
    if a.workers:
        argv2 += ["--workers", str(a.workers)]
    code = cli(argv2)
    if code != 0 or a.no_qc or a.scale != 1.0:
        return code
    return cli(["qc", "--config", str(config), "--video", str(out)])


if __name__ == "__main__":
    sys.exit(run())
