"""Build a scene candidate bank from every completed timeline block."""
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

from pack_intake import BLACK, PACKS, WORK, load, require_guard, save


def view(samples, ident):
    # Strip stable matte when measuring footage. Preserve original raster in exports.
    lo = np.percentile(samples.mean(axis=3), 85, axis=0)
    usable_rows = np.flatnonzero(lo.mean(axis=1) > 9)
    if len(usable_rows) > 35:
        return samples[ident, usable_rows[0]:usable_rows[-1] + 1, 5:-5]
    return samples[ident, 4:-4, 5:-5]


def candidates(pack):
    directory = WORK / pack
    source = load(directory / "source.json")
    files = sorted(directory.glob("block-*.npz"))
    seconds = source["video_seconds"]
    expected = math.ceil(seconds / source["block_seconds"])
    if len(files) != expected:
        raise RuntimeError(f"Only {len(files)}/{expected} scan blocks exist for {pack}")
    all_times, all_images = [], []
    for path in files:
        with np.load(path) as block:
            all_times.extend(block["times"])
            all_images.append(block["frames"])
    times = np.array(all_times)
    rgb = np.concatenate(all_images)
    del all_images
    if not np.all(np.diff(times) > 0):
        raise RuntimeError(f"Nonmonotonic scan samples for {pack}")
    # A coarse grid distinguishes new shots from small movement within one angle.
    measured = view(rgb[::max(1, len(rgb)//240)], slice(None))
    height = measured.shape[1]
    top = (rgb.shape[1] - height) // 2
    small = rgb[:, top:top + height:6, 5:-5:6].astype(np.int16)
    levels = small.mean(axis=(1, 2, 3))
    contrasts = small.std(axis=(1, 2, 3))
    differences = np.abs(small[1:] - small[:-1]).mean(axis=3)
    motion = np.r_[0, differences.mean(axis=(1, 2))]
    changed = np.r_[0, (differences > 32).mean(axis=(1, 2))]
    boundaries = [0, *np.flatnonzero((motion > 21) & (changed > .26)), len(times)]
    validity = (levels > 8.5) & (contrasts > 9)
    # Preserve distinct action. Collapse repeated nearby angles if their entire
    # small image is nearly identical and neither range carries visible movement.
    rows = []
    vectors = []
    for start, stop in zip(boundaries, boundaries[1:]):
        first = times[start]
        end = times[stop] if stop < len(times) else seconds
        duration = end - first
        if duration < 1.8 or not validity[start:stop].any():
            continue
        for left in np.arange(first, end, 9.0):
            right = min(left + 9.0, end)
            if right - left < 1.8:
                continue
            trim_start = min(.3, (right - left) * .1)
            trim_end = min(.26, (right - left) * .1)
            a, b = left + trim_start, right - trim_end
            inside = np.flatnonzero((times >= left) & (times < right) & validity)
            if not len(inside):
                continue
            sample = int(inside[np.argmin(abs(times[inside] - (a + b) / 2))])
            pace = float(np.median(motion[inside[1:]])) if len(inside) > 1 else 0.0
            vector = small[sample]
            if any(a - row["end"] < 25 and pace < 8 and row["motion_score"] < 8
                   and np.mean(np.abs(other - vector)) < 5 for row, other in zip(rows[-12:], vectors[-12:])):
                continue
            # Save source-relative times. The low-resolution boundary is an estimate.
            row = {"id": len(rows) + 1, "start": round(float(a), 3), "end": round(float(b), 3),
                   "sample_time": round(float(times[sample]), 3), "sample_index": sample,
                   "motion_score": round(pace, 2), "mean_rgb": round(float(levels[sample]), 1),
                   "score": round(min(b-a, 5) + min(float(contrasts[sample]), 47) / 17, 2)}
            rows.append(row)
            vectors.append(vector)
    packet = {"source": source, "scan_samples": len(times), "scan_blocks": len(files),
              "first_sample": float(times[0]), "last_sample": float(times[-1]),
              "max_sample_gap_seconds": round(float(np.max(np.diff(times))), 4),
              "candidate_count": len(rows), "candidates": rows}
    save(directory / "candidates.json", packet)
    sheet(directory, source, rows, rgb)
    print("CANDIDATES", pack, len(rows), "scan_samples", len(times), "max_gap",
          packet["max_sample_gap_seconds"], flush=True)


def sheet(directory, source, rows, rgb):
    # An evenly distributed browse sheet highlights high-quality candidates
    # without choosing a fixed number of final excerpts.
    count = min(len(rows), 108)
    selected = []
    for i in range(count):
        block = rows[i * len(rows) // count:(i + 1) * len(rows) // count]
        selected.append(max(block, key=lambda row: row["score"]))
    width = 135
    height = round(width * source["height"] / source["width"])
    cols = 8
    for page, offset in enumerate(range(0, len(selected), 48), 1):
        items = selected[offset:offset + 48]
        canvas = Image.new("RGB", (cols * width, math.ceil(len(items) / cols) * (height + 18)), BLACK)
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(items):
            x, y = i % cols * width, i // cols * (height + 18)
            draw.text((x + 3, y + 2), f'{row["id"]:04d}  {row["sample_time"]:.1f}s', fill="white")
            image = Image.fromarray(rgb[row["sample_index"]]).resize((width, height), Image.Resampling.LANCZOS)
            canvas.paste(image, (x, y + 18))
        canvas.save(directory / f"browse-{page:02d}.jpg", quality=91)


if __name__ == "__main__":
    require_guard(gpu=True)
    for name in sys.argv[1:] or PACKS:
        candidates(name)
