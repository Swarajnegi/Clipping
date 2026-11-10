"""
sheet.py -- contact sheets of candidate windows so Claude can LOOK before committing.

Audio and transcript rank candidates; they do not see replays, menus, loading
screens or a dead corridor. One row per window, N frames evenly spread across it.

Usage: python scripts/sheet.py <id> "12.5-24,60-75,..." [--frames 6] [--name round1]
       python scripts/sheet.py <id> --shots 476.3-536.6 [--name clip1_shots]

--shots draws one frame per camera shot (scene cuts from signals.json) with x gridlines at
0.25/0.50/0.75 and prints a clip-relative "shots" skeleton to fill in for clips.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FFMPEG, WORK, ffmpeg_command, mmss, require_guard  # noqa: E402

TW, TH = 320, 180


def grab(src: str, t: float) -> Image.Image:
    raw = subprocess.run(
        ffmpeg_command([FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
         "-vf", f"scale={TW}:{TH}:force_original_aspect_ratio=decrease,pad={TW}:{TH}:(ow-iw)/2:(oh-ih)/2",
         "-f", "image2pipe", "-vcodec", "png", "-"]),
        capture_output=True, check=True,
    ).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


def shot_sheet(vid: str, src: str, window: str, name: str) -> int:
    a, b = (float(x) for x in window.split("-"))
    cuts = json.loads((WORK / vid / "signals.json").read_text(encoding="utf-8"))["cuts"]
    cut_starts = [a] + [c for c in cuts if a + 0.4 < c < b - 0.4]
    # Same-palette cuts can score below any safe threshold, so long shots are sub-sampled
    # every 4s; a visible change between S3 and S3b is a missed cut to add by hand.
    starts, labels = [], []
    for i, (s0, e0) in enumerate(zip(cut_starts, cut_starts[1:] + [b])):
        starts.append(s0); labels.append(f"S{i + 1}")
        if e0 - s0 > 6:
            k = 1
            while s0 + 4 * k < e0 - 1.5:
                starts.append(s0 + 4 * k); labels.append(f"S{i + 1}b{k}")
                k += 1
    ends = starts[1:] + [b]
    cols = 6
    rows = (len(starts) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * TW, rows * (TH + 22)), (14, 14, 16))
    draw = ImageDraw.Draw(sheet)
    mids = [s + min(max((e - s) / 2, 0.3), 1.5) for s, e in zip(starts, ends)]
    with ThreadPoolExecutor(max_workers=1) as pool:
        imgs = list(pool.map(lambda t: grab(src, t), mids))
    skeleton = []
    for i, (s, e, img) in enumerate(zip(starts, ends, imgs)):
        x0, y0 = (i % cols) * TW, (i // cols) * (TH + 22)
        sheet.paste(img, (x0, y0 + 22))
        for gx in (0.25, 0.5, 0.75):
            draw.line([(x0 + gx * TW, y0 + 22), (x0 + gx * TW, y0 + 22 + TH)], fill=(0, 255, 255), width=1)
        draw.text((x0 + 4, y0 + 4), f"{labels[i]} +{s - a:.1f}s", fill=(150, 200, 255) if 'b' in labels[i] else (255, 235, 90))
        if 'b' not in labels[i]:
            skeleton.append({"t": round(s - a, 2), "x": 0.5})
    out_dir = WORK / vid / "sheets"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{name}.jpg"
    sheet.save(out, quality=86)
    print(out)
    print(json.dumps(skeleton))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("windows", nargs="?", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--frames", type=int, default=6)
    ap.add_argument("--name", default="sheet")
    args = ap.parse_args()
    require_guard()

    meta = json.loads((WORK / args.id / "source.json").read_text(encoding="utf-8"))
    src = meta["path"]
    if args.shots:
        return shot_sheet(args.id, src, args.shots, args.name)
    windows = [tuple(float(x) for x in w.split("-")) for w in args.windows.split(",") if w.strip()]

    label_w = 150
    sheet = Image.new("RGB", (label_w + args.frames * TW, len(windows) * (TH + 6)), (14, 14, 16))
    draw = ImageDraw.Draw(sheet)
    jobs = []
    for r, (a, b) in enumerate(windows):
        step = (b - a) / max(args.frames - 1, 1)
        for c in range(args.frames):
            jobs.append((r, c, a + c * step))

    with ThreadPoolExecutor(max_workers=1) as pool:
        frames = list(pool.map(lambda j: (j, grab(src, j[2])), jobs))
    for (r, c, t), img in frames:
        y = r * (TH + 6)
        sheet.paste(img, (label_w + c * TW, y))
        draw.text((label_w + c * TW + 4, y + 4), mmss(t), fill=(255, 235, 90))
    for r, (a, b) in enumerate(windows):
        y = r * (TH + 6)
        draw.text((8, y + 8), f"#{r + 1}", fill=(255, 255, 255))
        draw.text((8, y + 28), f"{mmss(a)}", fill=(200, 200, 200))
        draw.text((8, y + 46), f"{mmss(b)}", fill=(200, 200, 200))
        draw.text((8, y + 64), f"{b - a:.1f}s", fill=(160, 220, 160))

    out_dir = WORK / args.id / "sheets"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{args.name}.jpg"
    sheet.save(out, quality=86)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
