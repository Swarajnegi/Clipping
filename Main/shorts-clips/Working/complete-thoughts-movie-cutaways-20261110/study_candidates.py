"""Inspect candidate motion across the exact saved library files."""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
MOVIES = WORK.parents[1] / "Movie Clips"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(WORK.parent / "movie-cutaway-test-20261109"))
from common import FFMPEG, ffmpeg_command, probe, require_guard
from cooling import cool

OPTIONS = {
    "hollis": [
        ("Peaky Blinders - Tommy Shelby S06", "figure-walks-across-the-grass"),
        ("Peaky Blinders - Tommy Shelby S06", "vehicle-in-an-open-landscape"),
        ("Breaking Bad - Walter White S05A", "figure-walks-down-a-dusty-track"),
        ("Daredevil - Matt Murdock S02", "silhouette-in-an-arched-tunnel"),
        ("Fight Club", "empty-office-corridor"),
    ],
    "clear": [
        ("Peaky Blinders - Tommy Shelby S04", "boxing-ring-from-the-crowd"),
        ("Jon Snow", "wide-shot-of-sparring-in-the-yard"),
        ("Jon Snow", "sparring-partners-square-up-again"),
        ("Iron Man", "tony-works-at-a-crowded-bench"),
        ("Iron Man", "yinsen-works-at-the-bench"),
        ("Iron Man", "prototype-boots-firing-close-up"),
    ],
    "robbins": [
        ("Fight Club", "embrace-at-the-support-group"),
        ("Iron Man", "tony-listens-at-the-gala"),
        ("Peaky Blinders - Tommy Shelby S04", "woman-listens-across-the-table"),
        ("Avengers Endgame - Steve Rogers", "older-steve-in-the-woods"),
        ("Avengers Endgame - Steve Rogers", "two-people-by-the-lake"),
    ],
    "carr": [
        ("Fight Club", "tyler-reads-in-the-basement"),
        ("Peaky Blinders - Tommy Shelby S04", "tommy-alone-in-the-office"),
        ("Peaky Blinders - Tommy Shelby S06", "speaker-faces-the-crowd"),
        ("Peaky Blinders - Tommy Shelby S06", "speaker-in-silhouette-before-a-crowd"),
        ("Breaking Bad - Walter White S05A", "man-looks-up-while-reading"),
        ("Breaking Bad - Walter White S05A", "hands-at-work-in-low-light"),
        ("Breaking Bad - Walter White S05A", "walter-alone-at-a-table"),
    ],
}

def ff(*args):
    return subprocess.run(ffmpeg_command([FFMPEG, "-hide_banner", "-v", "error", "-xerror", *map(str, args)]),
                          check=True, stdout=subprocess.PIPE).stdout

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def catalogue_file(title, slug):
    folder = MOVIES / title
    data = read(folder / "catalogue.json")
    row, = [r for r in data["clips"] if r["file"].endswith(f"-{slug}.mp4")]
    return folder / row["file"], row, data

def sheet(items, target, width=184, height=106, columns=6):
    canvas = Image.new("RGB", (width * columns, (height + 20) * math.ceil(len(items) / columns)), "#14171a")
    draw = ImageDraw.Draw(canvas)
    for index, (label, frame) in enumerate(items):
        x, y = index % columns * width, index // columns * (height + 20)
        frame.thumbnail((width, height), Image.Resampling.LANCZOS)
        canvas.paste(frame, (x + (width - frame.width) // 2, y + 20 + (height - frame.height) // 2))
        draw.text((x + 4, y + 3), label, fill="white")
    canvas.save(target, quality=93)

def study():
    dest = WORK / "candidate-review"
    dest.mkdir(exist_ok=True)
    records = {}
    for group, options in OPTIONS.items():
        for index, (title, slug) in enumerate(options, 1):
            cool()
            path, entry, cat = catalogue_file(title, slug)
            info = probe(path)
            w, h = 240, round(240 * info.height / info.width / 2) * 2
            filt = f"fps=2,scale_cuda={w}:{h}:format=nv12,hwdownload,format=nv12,format=rgb24"
            raw = ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", path, "-an",
                     "-vf", filt, "-f", "rawvideo", "-")
            size = w*h*3
            frames = [(f"{slug[:21]}  {i/2:.1f}s", Image.frombytes("RGB",(w,h),raw[i*size:(i+1)*size]))
                      for i in range(len(raw)//size)]
            for page, offset in enumerate(range(0, len(frames), 24), 1):
                sheet(frames[offset:offset+24], dest / f"{group}-{index:02d}-{page}.jpg", 190, 108)
            records[slug] = {"title": title, "file": str(path), "clip_seconds": info.duration,
                             "source_start": entry["source_start"], "pack": cat["source"],
                             "dimensions": [info.width, info.height], "rate": info.rate,
                             "sample_count": len(frames), "sheet": f"{group}-{index:02d}-1.jpg"}
            print("CANDIDATE", group, index, slug, len(frames), flush=True)
    save(dest / "inventory.json", records)

if __name__ == "__main__":
    require_guard(gpu=True)
    study()
