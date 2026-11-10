"""Encode selected source ranges in bounded batches and check each standalone file."""
import math
import re
import shutil
import sys
import time
from fractions import Fraction

from export_library import ff, video_info
from pack_intake import MOVIES, PACKS, WORK, cool, load, require_guard, save


def batches(plan, span):
    # Reuse a single GPU decoder/encoder for nearby ranges.
    batch = []
    for row in plan:
        if batch and row["end"] - batch[0]["start"] > span:
            yield batch
            batch = []
        batch.append(row)
    if batch:
        yield batch


def frame_ranges(rows, rate, seconds):
    result = []
    cursor = 0
    for row in rows:
        start = round(row["start"] * rate)
        end = min(round(row["end"] * rate), math.floor(seconds * rate))
        if end <= start or (result and start < result[-1][2]):
            raise ValueError(f"Overlapping or invalid candidate {row['id']}")
        result.append((row, start, end, cursor))
        cursor += end - start
    return result


def encode(source, record, batch, temporary):
    rate = Fraction(record["rate"])
    fps = float(rate)
    wanted = frame_ranges(batch, fps, record["video_seconds"])
    start = wanted[0][1]
    end = wanted[-1][2]
    cuts = ",".join(f"{offset / fps:.9f}" for _, _, _, offset in wanted[1:])
    selections = "+".join(f"between(n,{a - start},{b - start - 1})" for _, a, b, _ in wanted)
    frames = sum(b - a for _, a, b, _ in wanted)
    directory = temporary
    if directory.exists():
        raise FileExistsError(f"Preserve existing batch evidence: {directory}")
    directory.mkdir(parents=True)
    output = directory / "%03d.mp4"
    profile = "main10" if record["pixel_format"] == "yuv420p10le" else "main"
    # CUDA frames stay on the GPU. Use forced closed GOPs at each new excerpt.
    codec = ["-c:v", "hevc_nvenc", "-profile:v", profile, "-tag:v", "hvc1",
             "-preset", "p4", "-rc", "vbr", "-cq", "20", "-b:v", "0", "-bf", "0",
             "-forced-idr", "1", "-g", "300", "-fps_mode", "passthrough",
             "-enc_time_base", f"{rate.denominator}:{rate.numerator}"]
    budget = max(2500000, round(record["bytes"] * 10 / record["video_seconds"]))
    codec += ["-maxrate", str(budget), "-bufsize", str(budget * 2)]
    formatting = ["-movflags", "+faststart", output]
    if cuts:
        formatting = ["-force_key_frames", "0," + cuts,
                      "-f", "segment", "-segment_format", "mp4",
                      "-segment_format_options", "movflags=+faststart",
                      "-segment_times", cuts, "-segment_time_delta", f"{.49 / fps:.9f}",
                      "-reset_timestamps", "1", output]
    ff("-y", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
       "-ss", f"{max(0, start / fps - .000001):.6f}",
       "-t", f"{(end - start + 2) / fps:.6f}", "-i", source,
       "-map", "0:v:0", "-an", "-sn", "-dn",
       "-vf", f"select='{selections}',setpts=N*{rate.denominator}/({rate.numerator}*TB)",
       "-frames:v", frames, *codec, "-map_metadata", -1, *formatting)
    files = sorted(directory.glob("*.mp4"))
    if len(files) != len(wanted):
        raise RuntimeError(f"Expected {len(wanted)} files, got {len(files)}")
    return wanted, files


def verify_and_save(wanted, files, record, folder, method="NVENC HEVC independent closed GOP"):
    fps = float(Fraction(record["rate"]))
    entries = []
    for (row, start, end, _), path in zip(wanted, files):
        video = video_info(path)
        assert (video["width"], video["height"]) == (record["width"], record["height"])
        assert Fraction(video["r_frame_rate"]) == Fraction(record["rate"]), video["r_frame_rate"]
        assert int(video["nb_frames"]) == end - start, (path.name, video["nb_frames"], end - start)
        assert abs(float(video["start_time"])) < .002, video["start_time"]
        assert abs(float(video["duration"]) - (end - start) / fps) < .002
        label = row.get("slug") or ("active-shot" if row["motion_score"] >= 8 else "steady-shot")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", label):
            raise ValueError(label)
        name = f"{round(start * 1000 / fps):08d}-{label}.mp4"
        if (folder / name).exists():
            raise FileExistsError(folder / name)
        entries.append({"candidate_id": row["id"], "file": name, "source_start": start / fps,
                        "source_end_exclusive": end / fps, "duration": float(video["duration"]),
                        "frames": end - start, "tags": row.get("tags") or [
                            ("movement" if row["motion_score"] >= 8 else "steady framing"),
                            ("low light" if row["mean_rgb"] < 42 else "readable lighting")],
                        "review": "Representative frame reviewed" if row.get("slug") else
                                  "Timeline screened; labels describe motion and lighting",
                        "codec_method": method,
                        "silent": True, "video_decoded": True, "bytes": path.stat().st_size})
    # All segments begin on a forced IDR and each has the expected zero-based duration.
    # Decode every frame in the batch and verify the aggregate count.
    playlist = files[0].parent / "verify.txt"
    playlist.write_text("\n".join(f"file '{path.as_posix()}'" for path in files) + "\n", encoding="utf-8")
    output = ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                "-f", "concat", "-safe", "0", "-i", playlist, "-map", "0:v:0",
                "-an", "-fps_mode", "passthrough", "-progress", "pipe:1", "-f", "null", "-")
    decoded = int(re.findall(r"^frame=(\d+)", output, re.M)[-1])
    assert decoded == sum(row["frames"] for row in entries), (decoded, len(files))
    for row, path in zip(entries, files):
        path.replace(folder / row["file"])
    return entries


def process(pack, trial=False):
    original, title, _ = PACKS[pack]
    work = WORK / pack
    source = MOVIES / original
    source_record = load(work / "candidates.json")
    metadata = source_record["source"]
    stat = source.stat()
    if (stat.st_size, stat.st_mtime_ns) != (metadata["bytes"], metadata["mtime_ns"]):
        raise RuntimeError(f"Source changed after study: {source}")
    plan = load(work / "selection.json")
    folder = MOVIES / title
    folder.mkdir(exist_ok=True)
    manifest = folder / "catalogue.json"
    data = load(manifest) if manifest.exists() else {
        "source": source.name, "source_bytes": stat.st_size, "source_mtime_ns": stat.st_mtime_ns,
        "source_resolution": [metadata["width"], metadata["height"]], "source_frame_rate": metadata["rate"],
        "source_duration": metadata["video_seconds"], "posting_reuse_basis": "Unresolved. Local library.",
        "time_basis": "Source-relative seconds on the native frame clock. Scanned boundaries are estimates.",
        "clips": [],
    }
    if (data["source"], data["source_bytes"], data["source_mtime_ns"]) != (source.name, stat.st_size, stat.st_mtime_ns):
        raise RuntimeError(f"Catalogue is for a different pack: {title}")
    done = {row["candidate_id"] for row in data["clips"]}
    span = 115 if metadata['width'] <= 1920 else 45
    for batch in batches([row for row in plan if row['id'] not in done], span):
        if shutil.disk_usage(folder).free < 4 * 1024**3:
            raise RuntimeError(f"Four GiB disk reserve reached while processing {title}")
        begun = time.monotonic()
        cool(75)
        scratch = work / f'batch-{batch[0]["id"]:04d}-{time.time_ns()}'
        wanted, files = encode(source, metadata, batch, scratch)
        entries = verify_and_save(wanted, files, metadata, folder)
        data["clips"].extend(entries)
        data["clips"].sort(key=lambda row: row["source_start"])
        save(manifest, data)
        print("BATCH", pack, len(data["clips"]), "/", len(plan), "last_clip", batch[-1]["id"],
              "seconds", round(time.monotonic() - begun, 1), flush=True)
        if trial:
            break
    if len(data["clips"]) == len(plan):
        data["scan"] = {key: value for key, value in source_record.items() if key not in ("source", "candidates")}
        data["scan"]["method"] = metadata["scan_mode"]
        data["selection_complete"] = True
        save(manifest, data)
        print("VERIFIED_PACK", pack, len(plan), flush=True)


if __name__ == "__main__":
    require_guard(gpu=True)
    if sys.argv[1] == "trial":
        process("tommy-s04", True)
        process("steve", True)
    else:
        for name in sys.argv[1:]:
            process(name)


