"""Fast keyframe-aligned extraction for the two short-GOP 4K packs."""
import csv
import shutil
import sys
import time
from bisect import bisect_left
from fractions import Fraction

from export_batches import ff, verify_and_save
from pack_intake import MOVIES, PACKS, WORK, cool, load, require_guard, save


def closest(keys, target):
    index = bisect_left(keys, target)
    if index == 0:
        return keys[0]
    if index == len(keys):
        return keys[-1]
    return min(keys[index - 1:index + 1], key=lambda timecode: abs(timecode - target))


def batches(rows, fps):
    current = []
    frames = 0
    for row in rows:
        length = row[0][2] - row[0][1]
        if current and frames + length > 36 * fps:
            yield current
            current = []
            frames = 0
        current.append(row)
        frames += length
    if current:
        yield current


def remux(pack, trial=False):
    original, title, short_gop = PACKS[pack]
    assert short_gop
    source = MOVIES / original
    work = WORK / pack
    packet = load(work / "candidates.json")
    metadata = packet["source"]
    stat = source.stat()
    assert (stat.st_size, stat.st_mtime_ns) == (metadata["bytes"], metadata["mtime_ns"])
    fps = float(Fraction(metadata["rate"]))
    keys = sorted({round(value * fps) for value in load(WORK / f"{source.stem}-keys.json")})
    last = round(metadata["video_seconds"] * fps)
    keys.append(last)
    assert keys == sorted(set(keys)) and keys[0] == 0
    plan = load(work / "selection.json")
    if trial:
        plan = plan[:3]
    scratch = work / f"remux-{time.time_ns()}"
    if shutil.disk_usage(work).free < (stat.st_size if not trial else 0) + 4 * 1024**3:
        raise RuntimeError("Insufficient space for bounded remux staging")
    scratch.mkdir()
    folder = (scratch / "trial-verified") if trial else MOVIES / title
    folder.mkdir(exist_ok=True)
    manifest = folder / "catalogue.json"
    data = load(manifest) if manifest.exists() else {
        "source": source.name, "source_bytes": stat.st_size, "source_mtime_ns": stat.st_mtime_ns,
        "source_resolution": [metadata["width"], metadata["height"]], "source_frame_rate": metadata["rate"],
        "source_duration": metadata["video_seconds"], "posting_reuse_basis": "Unresolved. Local library.",
        "time_basis": "Seconds in the original local pack. Excerpts are snapped to nearby source keyframes.",
        "clips": [],
    }
    assert (data["source"], data["source_bytes"], data["source_mtime_ns"]) == (source.name, stat.st_size, stat.st_mtime_ns)
    done = {item["candidate_id"] for item in data["clips"]}
    wanted = []
    for row in plan:
        if row["id"] in done:
            continue
        start = closest(keys, row["start"] * fps)
        end = closest(keys, row["end"] * fps)
        if end <= start or (wanted and start < wanted[-1][2]):
            raise RuntimeError(f"Unsafe keyframe interval: {row['id']} {start}..{end}")
        wanted.append((row, start, end, 0))
    if not wanted:
        return
    points = sorted({value for _, start, end, _ in wanted for value in (start, end)} - {0, last})
    boundaries = ",".join(f"{value/fps:.9f}" for value in points)
    listing = scratch / "segments.csv"
    duration = ["-t", f"{min(last / fps, wanted[-1][2] / fps + 1.5):.6f}"] if trial else []
    ff("-y", *duration, "-i", source, "-map", "0:v:0", "-an", "-sn", "-dn", "-map_metadata", -1,
       "-c:v", "copy", "-avoid_negative_ts", "disabled", "-f", "segment", "-segment_format", "mp4",
       "-segment_format_options", "use_editlist=1:movflags=+faststart",
       "-segment_times", boundaries, "-segment_time_delta", "0.00001", "-reset_timestamps", "1",
       "-segment_list", listing, "-segment_list_type", "csv", scratch / "%04d.mp4")
    by_start = {}
    with listing.open(encoding="utf-8", newline="") as handle:
        for name, start, end in csv.reader(handle):
            file = scratch / name
            if not file.resolve().is_relative_to(scratch.resolve()) or not file.is_file():
                raise RuntimeError(f"Unexpected temporary file {file}")
            by_start[round(float(start) * fps)] = file
    pairs = [(row, by_start[row[1]]) for row in wanted]
    keep = {file for _, file in pairs}
    # Drop only this run's temporary gap segments.
    for file in by_start.values():
        if file not in keep:
            file.unlink()
    for batch in batches(pairs, fps):
        cool(76)
        entries = verify_and_save([row for row, _ in batch], [file for _, file in batch], metadata, folder,
                                  method="Original video packets copied at source keyframes")
        data["clips"].extend(entries)
        data["clips"].sort(key=lambda row: row["source_start"])
        save(manifest, data)
        print("REMUX_BATCH", pack, len(data["clips"]), "/", len(plan), flush=True)
    if len(data["clips"]) != len(plan):
        raise RuntimeError(f"Incomplete remux: {title}")
    if not trial:
        data["scan"] = {key: value for key, value in packet.items() if key not in ("source", "candidates")}
        data["scan"]["method"] = metadata["scan_mode"]
        data["selection_complete"] = True
        save(manifest, data)
        print("VERIFIED_PACK", pack, len(plan), flush=True)
    else:
        print("REMUX_TRIAL", pack, len(plan), flush=True)


if __name__ == "__main__":
    require_guard(gpu=True)
    trial = sys.argv[1] == "trial"
    for pack in sys.argv[2:]:
        remux(pack, trial)

