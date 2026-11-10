"""Build local contact sheets and a lightweight shot index from the supplied packs."""
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
MOVIES = WORK.parents[1] / "Movie Clips"
PACKS = sorted(MOVIES.glob("*.mp4"))
NAMES = ("Fight Club", "Jon Snow", "Iron Man")
sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, ffmpeg_command, probe, require_guard

require_guard(gpu=True)

def frames(source, rate, start=None, seconds=None, width=192, height=108):
    args = [FFMPEG, "-v", "error", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
    if start is not None:
        args.extend(["-ss", str(start)])
    args.extend(["-i", str(source)])
    if seconds is not None:
        args.extend(["-t", str(seconds)])
    args.extend(["-an", "-sn", "-vf",
                 f"fps={rate},scale_cuda={width}:{height}:format=nv12,hwdownload,format=nv12,format=rgb24",
                 "-f", "rawvideo", "-"])
    size = width * height * 3
    with subprocess.Popen(ffmpeg_command(args), stdout=subprocess.PIPE) as proc:
        index = 0
        while data := proc.stdout.read(size):
            if len(data) != size:
                raise RuntimeError("Incomplete frame")
            yield (start or 0) + index / rate, np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
            index += 1
        if proc.wait():
            raise RuntimeError(f"Decode failed for {source.name}")

def sheet(samples, name, aspect, columns=5):
    width = 220
    height = round(width / aspect)
    row = height + 20
    canvas = Image.new("RGB", (columns * width, math.ceil(len(samples) / columns) * row), "#14171a")
    draw = ImageDraw.Draw(canvas)
    for i, (label, sample) in enumerate(samples):
        x, y = i % columns * width, i // columns * row
        draw.text((x + 4, y + 3), label, fill="white")
        canvas.paste(Image.fromarray(sample).resize((width, height), Image.Resampling.LANCZOS), (x, y + 20))
    canvas.save(WORK / name, quality=91)

def targeted():
    windows = ((0, 450, 94, 0.5), (0, 1515, 55, 1), (0, 1820, 65, 0.5),
               (1, 485, 58, 1), (1, 2350, 145, 0.25), (1, 3035, 55, 0.5),
               (2, 2404, 56, 1), (2, 2570, 104, 0.25))
    for pack, start, duration, rate in windows:
        media = probe(PACKS[pack])
        samples = [(f"{t:.2f}s", frame) for t, frame in frames(PACKS[pack], rate, start, duration)]
        for page, offset in enumerate(range(0, len(samples), 25), 1):
            sheet(samples[offset:offset + 25], f"target-{pack+1}-{start}-{page}.jpg", media.width / media.height)
        print("WINDOW", NAMES[pack], start, len(samples), flush=True)

def shot_index(pack):
    from cooling import cool

    source = PACKS[pack]
    media = probe(source)
    directory = MOVIES / NAMES[pack]
    directory.mkdir(exist_ok=True)
    rows = []
    windows = []
    for i in range(48):
        if i % 3 == 0:
            cool()
        start = round(media.duration * (i + .5) / 48 - 5.5, 3)
        sample = list(frames(source, 4, start, 11, 160, 90))
        windows.append([start, round(start + len(sample) / 4, 3)])
        previous = None
        breaks = [0]
        for j, (_, frame) in enumerate(sample):
            current = frame[::3, ::3].astype(np.int16)
            if previous is not None:
                delta = np.abs(current - previous).mean(axis=2)
                if delta.mean() > 20 and np.mean(delta > 20) > .45:
                    breaks.append(j)
            previous = current
        breaks.append(len(sample))
        choices = []
        for lo, hi in zip(breaks, breaks[1:]):
            if hi - lo < 13:
                continue
            t, im = sample[(lo + hi) // 2]
            level, contrast = im.mean(), im.std()
            if level < 17 or contrast < 17:
                continue
            lower = max(sample[lo][0] + .25, t - 2.75)
            upper = min(sample[hi - 1][0] - .125, t + 2.75)
            if upper - lower < 2.5:
                continue
            score = min(upper - lower, 5) * 3 + min(contrast, 55) / 8
            row = {"id": i + 1, "start": round(lower, 3), "end": round(upper, 3),
                   "sample": round(t, 3), "brightness": round(float(level), 1)}
            choices.append((score, row, im))
        if choices:
            _, row, im = max(choices, key=lambda item: item[0])
            rows.append((row, im))
        if (i + 1) % 12 == 0:
            print("WINDOWS", NAMES[pack], i + 1, len(rows), flush=True)
    index = {"source": source.name, "source_bytes": source.stat().st_size,
             "resolution": [media.width, media.height], "frame_rate": media.rate,
             "duration_seconds": media.duration, "sample_windows": windows,
             "coverage": "48 distributed 11-second windows at 4 fps. Shot boundaries estimated within windows.",
             "candidates": [row for row, _ in rows]}
    (directory / "shot-index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    for page, offset in enumerate(range(0, len(rows), 20), 1):
        sheet([(f'{s["id"]:02d} | {s["sample"]:.1f}s', im) for s, im in rows[offset:offset + 20]],
              f"library-{pack+1}-{page}.jpg", media.width / media.height)
    print("INDEX", NAMES[pack], len(rows), flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "targets":
        targeted()
    else:
        for pack in map(int, sys.argv[2:]):
            shot_index(pack - 1)
