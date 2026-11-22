"""FFmpeg / ffprobe helpers (works on Windows 10, macOS, Linux)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path


class FFmpegNotFound(RuntimeError):
    pass


def find_tool(name: str) -> str:
    """Locate ffmpeg/ffprobe: env FFMPEG_BIN / FFPROBE_BIN, then a sibling of FFMPEG_BIN, then PATH."""
    env = os.environ.get(f"{name.upper()}_BIN")
    if env and Path(env).exists():
        return env
    ff = os.environ.get("FFMPEG_BIN")
    if ff and name != "ffmpeg":
        cand = Path(ff).with_name(name + (".exe" if ff.lower().endswith(".exe") else ""))
        if cand.exists():
            return str(cand)
    found = shutil.which(name)
    if not found:
        raise FFmpegNotFound(
            f"'{name}' not found. Install FFmpeg (Windows: winget install Gyan.FFmpeg, or unzip a build and add its bin\\ "
            f"folder to PATH) or set {name.upper()}_BIN to the full path of {name}.exe.")
    return found


class Encoder:
    """Pipe raw RGB24 frames into ffmpeg -> H.264 MP4 (yuv420p, constant frame rate)."""

    def __init__(self, out_path: str | Path, width: int, height: int, fps: float, crf: int = 18, preset: str = "medium"):
        self.out_path = Path(out_path)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.width, self.height = width, height
        cmd = [find_tool("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-framerate", str(fps), "-i", "-",
               "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
               "-r", str(fps), "-movflags", "+faststart", str(self.out_path)]
        self.cmd = cmd
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.frames = 0

    def write(self, rgb) -> None:
        if rgb.shape[:2] != (self.height, self.width):
            raise ValueError(f"frame size {rgb.shape[1]}x{rgb.shape[0]} != {self.width}x{self.height}")
        self.proc.stdin.write(rgb.tobytes())
        self.frames += 1

    def close(self) -> None:
        self.proc.stdin.close()
        err = self.proc.stderr.read().decode(errors="replace")
        code = self.proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg failed ({code}): {err}")


def probe(path: str | Path) -> dict:
    """Video stream facts verified by ffprobe (frames are actually counted)."""
    cmd = [find_tool("ffprobe"), "-v", "error", "-count_frames", "-select_streams", "v:0",
           "-show_entries", "stream=codec_name,profile,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_read_frames,duration,display_aspect_ratio",
           "-show_entries", "format=duration,format_name,size,bit_rate", "-of", "json", str(path)]
    data = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    s = data["streams"][0]
    f = data["format"]
    num, den = (int(x) for x in s["r_frame_rate"].split("/"))
    return {
        "codec": s.get("codec_name"), "profile": s.get("profile"), "pix_fmt": s.get("pix_fmt"),
        "width": int(s["width"]), "height": int(s["height"]),
        "display_aspect_ratio": s.get("display_aspect_ratio"),
        "fps": num / den, "r_frame_rate": s["r_frame_rate"], "avg_frame_rate": s.get("avg_frame_rate"),
        "frames": int(s["nb_read_frames"]),
        "stream_duration": float(s.get("duration", "nan")), "format_duration": float(f["duration"]),
        "container": f.get("format_name"), "size_bytes": int(f.get("size", 0)), "bit_rate": int(f.get("bit_rate", 0)),
    }


def extract_frames(video: str | Path, frame_numbers: list[int], out_dir: str | Path, fps: float) -> list[Path]:
    """Extract exact frames (by index) from the encoded MP4 to PNG."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sel = "+".join(f"eq(n\\,{n})" for n in frame_numbers)
    pattern = out_dir / "frame_%03d.png"
    subprocess.run([find_tool("ffmpeg"), "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
                    "-vf", f"select='{sel}'", "-vsync", "0", str(pattern)], check=True)
    paths = []
    for k, n in enumerate(frame_numbers, start=1):
        src = out_dir / f"frame_{k:03d}.png"
        dst = out_dir / f"frame_{n:04d}.png"
        if src.exists():
            src.replace(dst)
            paths.append(dst)
    return paths
