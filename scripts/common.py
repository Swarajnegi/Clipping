"""Shared paths and ffmpeg helpers for the autoclipper scripts."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
PUBLIC = ROOT / "public"
OUT = ROOT / "out"

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
NODE = ROOT / ".runtime" / "node" / "node.exe"
REMOTION = ROOT / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
for _name, _path in (("FFMPEG", ROOT / ".runtime/ffmpeg/bin/ffmpeg.exe"),
                     ("FFPROBE", ROOT / ".runtime/ffmpeg/bin/ffprobe.exe")):
    if _path.is_file():
        globals()[_name] = str(_path)


def require_guard(*, gpu: bool = False) -> None:
    """Reject model/video work unless this process belongs to the launcher's job."""
    import ctypes
    from ctypes import wintypes as w

    name = os.environ.get("CLIPPING_GUARD_JOB", "")
    if os.name != "nt" or not name.startswith("Local\\ViralShorts-"):
        raise RuntimeError("Run this stage through .agents/skills/viral-shorts/scripts/run_guarded.ps1")
    if gpu and os.environ.get("CLIPPING_GUARD_WORKLOAD") != "Gpu":
        raise RuntimeError("This stage requires -Workload Gpu; CPU admission cannot authorize GPU work")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenJobObjectW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
    kernel.OpenJobObjectW.restype = w.HANDLE
    kernel.GetCurrentProcess.restype = w.HANDLE
    kernel.IsProcessInJob.argtypes = [w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    handle = kernel.OpenJobObjectW(4, False, name)
    if not handle:
        raise RuntimeError("Clipping guard job is unavailable")
    try:
        belongs = w.BOOL()
        if not kernel.IsProcessInJob(kernel.GetCurrentProcess(), handle, ctypes.byref(belongs)) or not belongs.value:
            raise RuntimeError("This process is outside the clipping resource guard")
    finally:
        kernel.CloseHandle(handle)


def ffmpeg_command(command: list[str]) -> list[str]:
    """Bound every input decoder, filter graph and output encoder to two threads."""
    bounded = [command[0], "-threads", "2", "-filter_threads", "2", "-filter_complex_threads", "2"]
    for arg in command[1:]:
        if arg in {"-i", "-c:v"}:
            bounded.extend(["-threads", "2"])
        bounded.append(arg)
    bounded[-1:-1] = ["-threads", "2"]
    return bounded


def wait_headroom(*, gpu: bool = False) -> None:
    """Re-admit a nested stage without acquiring the already-held clipping lock."""
    require_guard(gpu=gpu)
    launcher = ROOT / '.agents/skills/viral-shorts/scripts/run_guarded.ps1'
    result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                             '-File', str(launcher), '-Mode', 'Wait',
                             '-Workload', 'Gpu' if gpu else 'Cpu'], cwd=ROOT)
    if result.returncode:
        raise SystemExit(result.returncode)


def encoder(quality: int = 18) -> list[str]:
    return ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", str(quality),
            "-b:v", "0", "-pix_fmt", "yuv420p"]


@dataclass(frozen=True)
class Media:
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool
    # exact rational rate for ffmpeg (-r); rounding 30000/1001 to 29.97 put frames on a grid
    # Remotion's exact-time seek could not find ("No frame found at position").
    rate: str = "30/1"


def probe(path: Path) -> Media:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    info = json.loads(out)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    # r_frame_rate is the nominal rate (30000/1001); avg_frame_rate can be a jitter artefact
    # on YouTube VP9 files (7016500/234117).
    rate = video.get("r_frame_rate") or video.get("avg_frame_rate")
    if not rate:
        raise ValueError("Cannot determine source frame rate: metadata is missing")
    num, den = (int(x) for x in rate.split("/"))
    if not den or num / den > 121:
        rate = video.get("avg_frame_rate")
        if not rate:
            raise ValueError("Cannot determine source frame rate: average rate is missing")
        num, den = (int(x) for x in rate.split("/"))
    if num <= 0 or den <= 0:
        raise ValueError(f"Cannot determine source frame rate: {rate}")
    fps = num / den
    return Media(
        path=path,
        duration=float(info["format"]["duration"]),
        width=int(video["width"]),
        height=int(video["height"]),
        fps=fps,
        rate=f"{num}/{den}",
        has_audio=any(s["codec_type"] == "audio" for s in info["streams"]),
    )


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")[:60] or "video"


def mmss(sec: float) -> str:
    m, s = divmod(max(sec, 0.0), 60)
    return f"{int(m):02d}:{s:05.2f}"


def run(cmd: list[str]) -> None:
    require_guard(gpu=any(encoder in cmd for encoder in ("h264_nvenc", "hevc_nvenc")))
    subprocess.run(ffmpeg_command(cmd) if Path(cmd[0]).name.lower() in {"ffmpeg", "ffmpeg.exe"} else cmd, check=True)
