"""Guarded local study of the supplied examples and a sparse scenepack index."""

import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[4]
SHORTS = ROOT / "Main/shorts-clips"
sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, ffmpeg_command, probe, require_guard

require_guard(gpu=True)


def ffmpeg(*arguments):
    return subprocess.run(
        ffmpeg_command([FFMPEG, "-v", "error", "-y", *map(str, arguments)]),
        check=True, stdout=subprocess.PIPE,
    ).stdout


def contact_sheet(samples, path, width, height, columns):
    row_height = height + 22
    canvas = Image.new("RGB", (columns * width, math.ceil(len(samples) / columns) * row_height), "#181a1e")
    draw = ImageDraw.Draw(canvas)
    for index, (time, frame) in enumerate(samples):
        x = index % columns * width
        y = index // columns * row_height
        with Image.open(frame) as im:
            im.thumbnail((width, height))
            canvas.paste(im, (x + (width - im.width) // 2, y + 22 + (height - im.height) // 2))
        draw.text((x + 5, y + 4), f"{time:.2f}s", fill="white")
    canvas.save(path, quality=94)


def metadata(path):
    media = probe(path)
    stat = path.stat()
    return {
        "file": str(path), "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
        "seconds": media.duration, "width": media.width, "height": media.height,
        "rate": media.rate,
    }


references = []
for index, source in enumerate(sorted((SHORTS / "Reference/movie-cutaways-20261109").glob("*.mp4")), 1):
    record = metadata(source)
    frames = STUDY / f"reference-{index:02d}-frames"
    frames.mkdir(exist_ok=True)
    ffmpeg("-hwaccel", "cuda", "-i", source, "-an", "-vf", "fps=2", "-q:v", 3, frames / "%03d.jpg")
    samples = [(i / 2, frame) for i, frame in enumerate(sorted(frames.glob("*.jpg")))]
    for page, start in enumerate(range(0, len(samples), 18), 1):
        contact_sheet(samples[start:start + 18], STUDY / f"reference-{index:02d}-sheet-{page}.jpg", 180, 320, 6)
    record.update(sha256=hashlib.sha256(source.read_bytes()).hexdigest(), frame_samples=len(samples))
    references.append(record)
    print("REFERENCE_FRAMES", index, len(samples), flush=True)

packs = []
for index, source in enumerate(sorted((SHORTS / "Movie Clips").glob("*.mp4")), 1):
    record = metadata(source)
    frames = STUDY / f"pack-{index:02d}-frames"
    frames.mkdir(exist_ok=True)
    times = [4, 18, 40] + [round(record["seconds"] * i / 16, 2) for i in range(1, 16)]
    samples = []
    for slot, time in enumerate(times, 1):
        frame = frames / f"{slot:02d}.jpg"
        ffmpeg("-hwaccel", "cuda", "-ss", time, "-i", source, "-an", "-frames:v", 1, "-vf", "scale=320:-2", frame)
        samples.append((time, frame))
    contact_sheet(samples, STUDY / f"pack-{index:02d}-sheet.jpg", 320, 180, 4)
    record.update(sample_times=times, reuse_basis="Unconfirmed", coverage="Sparse discovery sample")
    packs.append(record)
    print("PACK_FRAMES", index, len(samples), flush=True)

(STUDY / "inventory.json").write_text(json.dumps({"references": references, "packs": packs}, indent=2), encoding="utf-8")

from prep import _load_whisper
model, device = _load_whisper("small")
for index, record in enumerate(references, 1):
    pcm = ffmpeg("-i", record["file"], "-vn", "-ac", 1, "-ar", 16000, "-f", "f32le", "-")
    segments, _ = model.transcribe(np.frombuffer(pcm, np.float32), language="en", word_timestamps=True,
                                   vad_filter=True, beam_size=5)
    rows = [{"start": seg.start, "end": seg.end, "text": seg.text.strip(),
             "words": [{"word": w.word.strip(), "start": w.start, "end": w.end} for w in seg.words or []]}
            for seg in segments]
    (STUDY / f"reference-{index:02d}-transcript.json").write_text(
        json.dumps({"device": device, "segments": rows}, indent=2), encoding="utf-8",
    )
    print("REFERENCE_SPEECH", index, [row["text"] for row in rows], flush=True)
