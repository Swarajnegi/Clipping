"""Create standalone, silent movie-library excerpts and verify each file."""
import json
import math
import re
import shutil
import subprocess
import sys
from bisect import bisect_left
from fractions import Fraction

from pack_intake import FFMPEG, FFPROBE, MOVIES, PACKS, WORK, cool, ffmpeg_command, load, require_guard, save


def ff(*args):
    result = subprocess.run(ffmpeg_command([FFMPEG, "-v", "error", "-xerror", *map(str, args)]),
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout


def video_info(path):
    command = [FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = json.loads(subprocess.check_output(command))
    streams = result["streams"]
    if len(streams) != 1 or streams[0]["codec_type"] != "video":
        raise ValueError(f"Expected one standalone silent video stream in {path}")
    return streams[0]


def standalone(row, source, keys, title, record):
    stat = source.stat()
    if stat.st_size != record["bytes"] or stat.st_mtime_ns != record["mtime_ns"]:
        raise RuntimeError(f"Original pack changed: {source.name}")
    folder = MOVIES / title
    minimum = 8 * 1024**3
    if shutil.disk_usage(folder).free < minimum:
        raise RuntimeError(f"Disk reserve reached before {source.name} candidate {row['id']}")
    fps = float(Fraction(record["rate"]))
    a, b = row["start"], row["end"]
    # For common short-GOP material, a nearby keyframe allows direct stream copy.
    key_index = bisect_left(keys, a - .35)
    point = keys[key_index] if key_index < len(keys) else math.inf
    mode = "packet copy" if point <= a + .55 and b - point >= 1.45 else "NVENC precise trim"
    if mode == "packet copy":
        a = point
    else:
        a = round(a * fps) / fps
    duration = b - a
    slug = row.get("slug") or ("active-shot" if row["motion_score"] >= 8 else "steady-shot")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError(slug)
    dest = folder / f"{round(a * 1000):08d}-{slug}.mp4"
    part = dest.with_suffix(".partial.mp4")
    if dest.exists():
        raise FileExistsError(dest)
    cool(76)
    if mode == "packet copy":
        hw = []
        codec = ["-c:v", "copy", "-avoid_negative_ts", "disabled", "-use_editlist", "1"]
    else:
        hw = ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"]
        codec = (["-c:v", "hevc_nvenc", "-profile:v", "main10", "-tag:v", "hvc1"]
                 if record["pixel_format"] == "yuv420p10le" else ["-c:v", "h264_nvenc", "-profile:v", "high"])
        codec += ["-preset", "p4", "-rc", "vbr", "-cq", "20", "-b:v", "0", "-fps_mode", "passthrough"]
    ff("-y", *hw, "-ss", f"{a:.6f}", "-i", source, "-t", f"{duration:.6f}",
       "-map", "0:v:0", "-an", "-sn", "-dn", *codec, "-map_metadata", -1,
       "-movflags", "+faststart", part)
    video = video_info(part)
    assert (video["width"], video["height"]) == (record["width"], record["height"])
    assert Fraction(video["r_frame_rate"]) == Fraction(record["rate"]), (video["r_frame_rate"], record["rate"])
    assert abs(float(video["start_time"])) < .002, video["start_time"]
    assert abs(float(video["duration"]) - duration) < max(.135, 3/fps), (video["duration"], duration)
    decoded = ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", part,
                 "-map", "0:v:0", "-an", "-progress", "pipe:1", "-f", "null", "-")
    frames = int(re.findall(r"^frame=(\d+)", decoded, re.M)[-1])
    assert frames > 0 and abs(frames / fps - float(video["duration"])) < max(.125, 3/fps)
    part.replace(dest)
    tags = row.get("tags") or [("movement" if row["motion_score"] >= 8 else "steady framing"),
                               ("low light" if row["mean_rgb"] < 42 else "readable lighting")]
    return {"candidate_id": row["id"], "file": dest.name, "source_start": a,
            "source_end_exclusive": round(a + float(video["duration"]), 6),
            "duration": float(video["duration"]), "frames": frames, "tags": tags,
            "review": "Representative frame reviewed" if row.get("slug") else "End-to-end scan screened, tags are visual measurements",
            "codec_method": mode, "silent": True, "video_decoded": True, "bytes": dest.stat().st_size}


def materialize(pack, count=None):
    name, title, _ = PACKS[pack]
    source = MOVIES / name
    work = WORK / pack
    packet = load(work / "candidates.json")
    record = packet["source"]
    plan = load(work / "selection.json")
    keys = sorted(set(load(WORK / f"{source.stem}-keys.json")))
    folder = MOVIES / title
    folder.mkdir(exist_ok=True)
    manifest = folder / "catalogue.json"
    data = load(manifest) if manifest.exists() else {
        "source": name, "source_bytes": record["bytes"], "source_mtime_ns": record["mtime_ns"],
        "source_resolution": [record["width"], record["height"]], "source_frame_rate": record["rate"],
        "source_duration": record["video_seconds"], "posting_reuse_basis": "Unresolved. Local library.",
        "time_basis": "Seconds in the original local scenepack", "clips": [],
    }
    if (data["source"], data["source_bytes"], data["source_mtime_ns"]) != (name, record["bytes"], record["mtime_ns"]):
        raise RuntimeError(f"Manifest is for a different pack: {title}")
    done = {item["candidate_id"] for item in data["clips"]}
    remaining = [row for row in plan if row["id"] not in done]
    for row in remaining[:count]:
        entry = standalone(row, source, keys, title, record)
        data["clips"].append(entry)
        data["clips"].sort(key=lambda item: item["source_start"])
        save(manifest, data)
        print("CLIP", pack, len(data["clips"]), "/", len(plan), entry["file"], entry["codec_method"], flush=True)
    if len(data["clips"]) == len(plan):
        data["scan"] = {key: value for key, value in packet.items() if key not in ("source", "candidates")}
        data["scan"]["method"] = record["scan_mode"]
        data["selection_complete"] = True
        save(manifest, data)
        print("VERIFIED_PACK", pack, len(plan), flush=True)


if __name__ == "__main__":
    require_guard(gpu=True)
    if sys.argv[1] == "trial":
        for pack in ("matt", "steve"):
            materialize(pack, 1)
    else:
        for pack in sys.argv[1:]:
            materialize(pack)

