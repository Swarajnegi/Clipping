"""Materialize source-native, silent excerpts and prepare the private cutaway test."""
import json
from cooling import cool
from PIL import Image
import shutil
import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
MOVIES = WORK.parents[1] / "Movie Clips"
PACKS = sorted(MOVIES.glob("*.mp4"))
NAMES = ("Fight Club", "Jon Snow", "Iron Man")
P = WORK.parent / "complete-thoughts-20261108"
MASTER = P / "drafts/02-goggins-learning-to-fail-clean-assembly.mp4"
PUBLIC = WORK / "public"
FPS = 30000 / 1001

sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, ffmpeg_command, probe, require_guard
require_guard(gpu=True)

# Range times are relative to the supplied scenepack, not the original release.
SEEDS = [
    (0, 464.4, 6, "first-fight-outside-the-bar", "setback, risk, sparring"),
    (0, 493.6, 7.4, "tyler-and-narrator-after-the-first-fight", "absorbing pain, regrouping, companionship"),
    (0, 511.7, 6.4, "walking-toward-paper-street-house", "arriving, uncertainty, solitude"),
    (0, 533.8, 6.2, "tyler-spars-in-parking-lot", "practice, persistence, rivalry"),
    (0, 1545, 7.3, "narrator-regroups-in-the-basement", "exhaustion, setback, composure"),
    (0, 1557, 5.2, "tyler-watches-the-narrator", "watching, reflection, tension"),
    (1, 509, 5, "night-watch-training-yard", "preparation, spectators, practice"),
    (1, 514.9, 1.7, "jon-braces-against-a-sword-strike", "pressure, defense, practice"),
    (1, 518.65, 2.1, "jon-counters-in-training", "adjusting, countering, composure"),
    (1, 523, 4.2, "jon-gets-back-up-in-training", "recovery, practice, persistence"),
    (1, 1017.8, 4.5, "figures-in-snowy-woods", "uncertainty, isolation, journey"),
    (1, 3058, 6, "jon-looks-down-after-battle", "reflection, loss, exhaustion"),
    (2, 2404, 6.7, "tony-and-robot-prepare-the-flight-test", "building, experimentation, preparation"),
    (2, 2427.9, 7.3, "tony-adjusts-and-lands-prototype", "trial and error, adaptation, balance"),
    (2, 2436.2, 5.6, "tony-resets-for-another-attempt", "reset, repetition, craft"),
    (2, 2577.5, 4.2, "suit-in-workshop", "preparation, testing, reveal"),
    (2, 2584.7, 4, "iron-man-flies-through-tunnel", "breakthrough, speed, risk"),
    (2, 2968.4, 4.1, "tony-listens-at-the-gala", "conversation, listening, intimacy"),
]

def ff(*args):
    subprocess.run(ffmpeg_command([FFMPEG, "-hide_banner", "-v", "error", "-xerror", *map(str, args)]), check=True)

def export(pack, start, length, label, tags, review):
    source = PACKS[pack]
    media = probe(source)
    folder = MOVIES / NAMES[pack]
    folder.mkdir(exist_ok=True)
    dest = folder / f"{round(start * 1000):08d}-{label}.mp4"
    manifest = folder / "catalogue.json"
    catalogue = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {
        "source": source.name, "source_bytes": source.stat().st_size,
        "source_resolution": [media.width, media.height], "source_frame_rate": media.rate,
        "time_basis": "seconds in the supplied local scenepack",
        "posting_reuse_basis": "Unresolved. Local review assets.", "clips": [],
    }
    if dest.exists():
        if any(row["file"] == dest.name for row in catalogue["clips"]):
            return dest
        raise FileExistsError(dest)
    if shutil.disk_usage(folder).free < 8 * 1024**3:
        raise RuntimeError("Stopping before encroaching on the 8 GiB disk reserve")
    cool()
    n = round(length * media.fps)
    part = dest.with_suffix(".partial.mp4")
    hevc = pack > 0
    encode = ["-c:v", "hevc_nvenc", "-profile:v", "main10", "-tag:v", "hvc1"] if hevc else [
        "-c:v", "h264_nvenc", "-profile:v", "high"]
    ff("-y", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-ss", f"{start:.6f}",
       "-i", source, "-map", "0:v:0", "-an", "-sn", "-dn", "-frames:v", n,
       *encode, "-preset", "p4", "-rc", "vbr", "-cq", 19, "-b:v", 0,
       "-map_metadata", -1, "-movflags", "+faststart", part)
    result = probe(part)
    assert (result.width, result.height, result.rate, result.has_audio) == (
        media.width, media.height, media.rate, False)
    assert abs(result.duration - n / media.fps) < 1 / media.fps
    ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", part, "-an", "-f", "null", "-")
    part.replace(dest)
    catalogue["clips"].append({"file": dest.name, "source_start": start,
        "source_end_exclusive": round(start + n / media.fps, 6),
        "duration": result.duration, "frames": n, "tags": tags.split(", "),
        "review": review, "video_decoded": True, "silent": True, "bytes": dest.stat().st_size})
    catalogue["clips"].sort(key=lambda row: row["source_start"])
    partial_manifest = manifest.with_suffix(".json.tmp")
    partial_manifest.write_text(json.dumps(catalogue, indent=2), encoding="utf-8")
    partial_manifest.replace(manifest)
    print("EXCERPT", NAMES[pack], dest.name, flush=True)
    return dest

def test_asset(source, name, offset, frame_count, crop=None):
    dest = PUBLIC / (name + ".mp4")
    if dest.exists() and dest.stat().st_size == 0:
        dest.rename(dest.with_suffix(".interrupted.mp4"))
    if dest.exists():
        existing = probe(dest)
        if abs(existing.duration - frame_count / FPS) < 1 / FPS:
            return dest
        dest.rename(dest.with_suffix('.interrupted.mp4'))
    cool()
    if crop:
        side, left, top = crop
        vf = f"crop={side}:{side}:{left}:{top},scale=980:980:flags=lanczos,format=yuv420p,fps=30000/1001"
    else:
        vf = "scale_cuda=1920:1080:format=nv12"
    hw = [] if crop else ["-hwaccel_output_format", "cuda"]
    inputs = ["-hwaccel", "cuda", *hw, "-ss", offset, "-i", source]
    filters = ["-map", "0:v:0", "-vf", vf]
    if name == "tony-v2":
        scrim = WORK / "tony-top-falloff.png"
        im = Image.new("RGBA", (980, 980))
        for y in range(225):
            a = round(105 * max(0, min(1, (225 - y) / 95)))
            im.paste((0, 0, 0, a), (0, y, 980, y + 1))
        im.save(scrim)
        inputs += ["-i", scrim]
        filters = ["-filter_complex", f"[0:v]{vf}[base];[base][1:v]overlay=eof_action=repeat:format=yuv420[out]", "-map", "[out]"]
    ff("-y", *inputs, *filters, "-an", "-sn", "-frames:v", frame_count, "-c:v", "h264_nvenc",
       "-preset", "p4", "-rc", "vbr", "-cq", 17, "-b:v", 0, "-movflags", "+faststart", dest)
    result = probe(dest)
    assert abs(result.duration - frame_count / FPS) < 1 / FPS, (name, result)
    return dest

def seeds():
    files = {}
    for pack, start, length, label, tags in SEEDS:
        files[label] = export(pack, start, length, label, tags, "Timestamped contact-sheet review")
    PUBLIC.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "public/fonts", PUBLIC / "fonts", dirs_exist_ok=True)
    test_asset(MASTER, "goggins", 0, 1089)
    cuts = [
        ("tyler", "tyler-and-narrator-after-the-first-fight", 0.15, 105, 263, (800, 38, 0)),
        ("jon-brace", "jon-braces-against-a-sword-strike", 0.04, 620, 669, (2160, 1400, 0)),
        ("jon-counter-v2", "jon-counters-in-training", 0.12, 669, 723, (2160, 454, 0)),
        ("tony-v2", "tony-adjusts-and-lands-prototype", 0.3, 824, 987, (1600, 1260, 0)),
    ]
    for name, label, offset, start, end, crop in cuts:
        test_asset(files[label], name, offset, end - start, crop)
    (WORK / "test-cuts.json").write_text(json.dumps([
        {"src": name + ".mp4", "t": start / FPS, "dur": (end - start) / FPS,
         "start_frame": start, "end_frame_exclusive": end, "library_file": str(files[label]),
         "library_offset": offset, "crop": crop}
        for name, label, offset, start, end, crop in cuts], indent=2), encoding="utf-8")

if sys.argv[1] == "seeds":
    seeds()
else:
    supplemental = [
        (1, 485.25, 4.2, "training-yard-through-a-wooden-gate", "anticipation, setting, observation"),
        (1, 491.1, 4.1, "wide-shot-of-sparring-in-the-yard", "practice, effort, preparation"),
        (1, 496.1, 3.5, "figures-cross-the-snowy-yard", "arrival, walking, winter"),
        (1, 503.1, 3.2, "crowd-forms-around-jon", "belonging, pressure, watchfulness"),
        (1, 528.3, 3.8, "sparring-partners-square-up-again", "persistence, reset, anticipation"),
        (1, 538.2, 2.2, "young-spectator-lowers-his-gaze", "doubt, reflection, disappointment"),
        (1, 3035.3, 3.1, "torchlight-through-the-gate", "aftermath, suspense, threshold"),
        (2, 2454.4, 2.9, "prototype-boots-firing-close-up", "craft, experiment, ignition"),
    ]
    for entry in supplemental:
        export(*entry, "Timestamped contact-sheet review")
    selected = json.loads((WORK / "library-selection.json").read_text(encoding="utf-8"))
    for entry in selected:
        export(*entry, "Reviewed representative frame and screened approximate shot boundary")




