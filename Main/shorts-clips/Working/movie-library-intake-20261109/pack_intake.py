"""Scan owner-supplied scenepacks in guarded, resumable timeline blocks."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
MOVIES = WORK.parents[1] / "Movie Clips"
sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, FFPROBE, ffmpeg_command, probe, require_guard

PACKS = {
    "walter": ("Walter White - Breaking Bad (2008) S05A [WEB-DL 4K] - 411editing.mp4", "Breaking Bad - Walter White S05A", False),
    "tommy-s06": ("Tommy Shelby - Peaky Blinders S06 2022 [WEB-DL 4K] - AgentPDonley.mp4", "Peaky Blinders - Tommy Shelby S06", True),
    "tommy-s04": ("Tommy Shelby - Peaky Blinders S04 2017 [REMUX 1080p] - AgentPDonley.mp4", "Peaky Blinders - Tommy Shelby S04", True),
    "steve": ("Steve Rogers - Avengers Endgame [2019] - [REMUX 4K HEVC-H265] - chaszq.mp4", "Avengers Endgame - Steve Rogers", False),
    "matt": ("Matt Murdock Daredevil S02 - WEB-DL (4K) h264-xp.mp4", "Daredevil - Matt Murdock S02", True),
}
WIDTH, HEIGHT = 128, 72
SHOW = re.compile(r"\bpts_time:([\d.e+-]+)")
BLACK = "#15171a"


def save(path, data):
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def cool(target=74):
    deadline = time.monotonic() + 180
    while True:
        out = subprocess.check_output(["nvidia-smi", "-i", "0", "--query-gpu=temperature.gpu",
                                       "--format=csv,noheader,nounits"], text=True, timeout=6)
        if int(out.strip()) <= target:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(f"GPU did not cool to {target} C. Last reading: {out.strip()} C")
        time.sleep(5)


def source_stream(path):
    args = [FFPROBE, "-v", "error", "-select_streams", "v:0",
            "-show_streams", "-of", "json", str(path)]
    return json.loads(subprocess.check_output(args))["streams"][0]


def scan_block(source, start, duration, key_only):
    mode = ["-discard:v", "nokey"] if key_only else []
    sampling = "" if key_only else "fps=2,"
    arguments = ffmpeg_command([
        FFMPEG, "-hide_banner", "-v", "info", "-nostats", "-xerror",
        "-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-ss", f"{start:.6f}",
        *mode, "-i", str(source), "-t", f"{duration:.6f}", "-map", "0:v:0",
        "-an", "-sn", "-dn", "-vf",
        f"{sampling}scale_cuda={WIDTH}:{HEIGHT}:format=nv12,hwdownload,format=nv12,format=rgb24,showinfo",
        "-fps_mode", "passthrough", "-f", "rawvideo", "-",
    ])
    completed = subprocess.run(arguments, capture_output=True)
    log = completed.stderr.decode("utf-8", errors="replace")
    if completed.returncode:
        raise RuntimeError(log[-4800:])
    frames = np.frombuffer(completed.stdout, dtype=np.uint8).reshape(-1, HEIGHT, WIDTH, 3)
    # showinfo is upstream of the output trim and may observe one extra frame.
    seconds = [start + float(match) for match in SHOW.findall(log)][:len(frames)]
    if len(seconds) != len(frames) or len(frames) < 1:
        raise RuntimeError(f"Frame/timestamp mismatch for {source.name} at {start}")
    return np.array(seconds), frames


def scan(pack, only_first=False):
    name, _, key_only = PACKS[pack]
    source = MOVIES / name
    media = probe(source)
    video = source_stream(source)
    directory = WORK / pack
    directory.mkdir(exist_ok=True)
    seconds = float(video.get("duration") or media.duration)
    span = 150 if key_only else 45
    stat = source.stat()
    identity = {"name": name, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                "video_seconds": seconds, "width": media.width, "height": media.height,
                "rate": media.rate, "average_rate": video.get("avg_frame_rate"),
                "pixel_format": video["pix_fmt"], "codec": video["codec_name"],
                "color_space": video.get("color_space"), "scan_mode": "keyframes" if key_only else "2 fps",
                "block_seconds": span}
    record = directory / "source.json"
    if record.exists() and load(record) != identity:
        raise RuntimeError(f"Source changed since scan: {name}")
    save(record, identity)
    total = int(np.ceil(seconds / span))
    for index in range(1 if only_first else total):
        start = index * span
        path = directory / f"block-{index:04d}.npz"
        if path.exists():
            continue
        cool()
        begun = time.monotonic()
        times, frames = scan_block(source, start, min(span, seconds - start), key_only)
        if times[0] - start > (2 if key_only else .55):
            raise RuntimeError(f"Unexpected scan gap at {start}: first frame is {times[0]}")
        staged = path.with_suffix(".tmp")
        with staged.open("wb") as handle:
            np.savez_compressed(handle, times=times, frames=frames)
        staged.replace(path)
        if index == 0 or (index + 1) % 5 == 0 or index == total - 1:
            print("SCAN", pack, index + 1, total, len(frames),
                  round(float(times[0]), 3), round(float(times[-1]), 3),
                  "work_seconds", round(time.monotonic() - begun, 1), flush=True)


if __name__ == "__main__":
    require_guard(gpu=True)
    command = sys.argv[1]
    if command == "trial":
        for pack in ("matt", "steve"):
            scan(pack, only_first=True)
    elif command == "scan":
        for pack in sys.argv[2:]:
            scan(pack)
    else:
        raise ValueError(command)
