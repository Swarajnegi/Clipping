"""Author shot-aware word layers and render the private Goggins test."""
import json
from cooling import cool
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
P = WORK.parent / "complete-thoughts-20261108"
BASE = P / "finish-v1/props/02-goggins-learning-to-fail"
MASTER = P / "drafts/02-goggins-learning-to-fail-clean-assembly.mp4"
PROPS = WORK / "review-props.json"
BUNDLE = WORK / "bundle"
QA = WORK / "qa"
OUTPUT = WORK / "02-goggins-learning-to-fail-movie-cutaways-REVIEW.mp4"
FPS = 30000 / 1001
N = 1089
sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, NODE, REMOTION, ffmpeg_command, probe, require_guard
from motion_edit import audio_packets, decode, video_clock

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def normalize(word):
    return re.sub(r"[^a-z]", "", word.lower())

def width(word, size, font, weight):
    fontroot = ROOT / ".agents/skills/viral-shorts/assets/fonts"
    if font == "inter":
        face = ImageFont.truetype(fontroot / "InterVariable.woff2", round(size * 8))
        face.set_variation_by_axes([min(32, size), weight])
    else:
        face = ImageFont.truetype(fontroot / "CormorantGaramond-Italic.ttf", round(size * 8))
    return max(size * .34, face.getlength(word) / 8 - max(0, len(word) - 1) * size * .026 + 5)

def author():
    props = read(BASE.with_suffix(".json"))
    plan = read(BASE.with_name(BASE.name + "-caption-plan.json"))
    original = props["referenceEdit"]["layers"]
    assert len(original) == len(plan["words"])
    props.update(src="goggins.mp4", srcWidth=1920, srcHeight=1080)
    props["cutaways"] = [{k: cut[k] for k in ("src", "t", "dur")} for cut in read(WORK / "test-cuts.json")]
    # Each tuple sets a phrase centre, maximum width, and explicit line breaks.
    layouts = {
        1: (281, 740, 400, [1, 1], {"victory": (96, "inter", 800)}),
        2: (550, 1205, 740, [3, 1], {"failure": (112, "cormorant", 400)}),
        3: (535, 1220, 740, [3], {}),
        4: (535, 1220, 740, [3], {"fail": (86, "inter", 800)}),
        16: (360, 1210, 560, [4], {}),
        17: (360, 1210, 560, [4], {"fail": (80, "inter", 800)}),
        18: (640, 1240, 670, [3, 1], {"victory": (114, "inter", 850)}),
        21: (550, 552, 760, [4], {"winning": (69, "inter", 800)}),
        22: (550, 552, 760, [3], {}),
        23: (550, 552, 760, [4], {"failing": (82, "cormorant", 400)}),
        25: (286, 741, 405, [3, 1], {"fail": (77, "inter", 820), "properly": (101, "cormorant", 400)}),
    }
    layers = []
    cursor = 0
    for index, group in enumerate(plan["groups"]):
        tokens = group["text"].split()
        count = len(tokens)
        active = original[cursor:cursor + count]
        assert list(map(normalize, tokens)) == [normalize(layer["text"]) for layer in active]
        cursor += count
        if index not in layouts:
            layers.extend(active)
            continue
        xc, yc, maximum, split, emphasis = layouts[index]
        assert sum(split) == count
        lines = []
        cursor_line = 0
        for columns in split:
            line = []
            for layer in active[cursor_line:cursor_line + columns]:
                text = layer["text"]
                size, font, weight = emphasis.get(normalize(text), (61 if index < 21 else 59, "inter", 700))
                line.append((layer, size, font, weight, width(text, size, font, weight)))
            lines.append(line)
            cursor_line += columns
        heights = [max(item[1] for item in line) for line in lines]
        gap_y = 2
        y = yc - (sum(heights) + gap_y * (len(lines) - 1)) / 2
        for line, height in zip(lines, heights):
            gap = 12
            total = sum(item[4] for item in line) + gap * (len(line) - 1)
            scale = min(1, maximum / total)
            x = xc - total * scale / 2
            for layer, size, font, weight, span in line:
                updated = dict(layer, x=round(x, 2), y=round(y + (height - size * scale) * .65, 2),
                               width=round(span * scale, 2), size=round(size * scale, 2),
                               font=font, weight=weight, italic=font == "cormorant", tracking=-.026,
                               motion={"inSec": .09, "outSec": .035, "rise": 5, "scaleFrom": .98,
                                       "blur": 1.3, "easing": "cubic"})
                assert updated["x"] >= 70 and updated["x"] + updated["width"] <= 1010
                layers.append(updated)
                x += (span + gap) * scale
            y += height + gap_y
    assert cursor == len(original) == len(layers)
    assert all(l["surface"] == "difference" and l["color"] == "#ffffff" for l in layers)
    assert [(l["t"], l["dur"], l["text"]) for l in layers] == [(l["t"], l["dur"], l["text"]) for l in original]
    props["referenceEdit"]["layers"] = layers
    save(PROPS, props)
    print("CAPTIONS", len(layers), flush=True)

def run(*args):
    subprocess.run(list(map(str, args)), cwd=ROOT, check=True)

def ff(*args):
    run(*ffmpeg_command([FFMPEG, "-v", "error", "-xerror", "-y", *map(str, args)]))

def stills():
    QA.mkdir(exist_ok=True)
    run(NODE, REMOTION, "bundle", "src/index.ts", f"--public-dir={WORK / 'public'}", f"--out-dir={BUNDLE}")
    for frame in map(int, sys.argv[2:] or [60, 157, 238, 644, 705, 876, 969, 1081]):
        cool()
        run(NODE, REMOTION, "still", BUNDLE, "ViralShort", QA / f"still-{frame:04d}.png",
            f"--frame={frame}", f"--props={PROPS}", "--gl=angle", "--offthreadvideo-video-threads=2",
            "--offthreadvideo-cache-size-in-bytes=134217728")
    sheet(sorted(QA.glob("still-*.png")), "caption-stills.jpg", 4)

def sheet(images, name, cols=4, width=240):
    height = width * 16 // 9
    rows = (len(images) + cols - 1) // cols
    canvas = Image.new("RGB", (width * cols, (height + 18) * rows), "#191b20")
    draw = ImageDraw.Draw(canvas)
    for i, image in enumerate(images):
        x, y = i % cols * width, i // cols * (height + 18)
        draw.text((x + 5, y + 3), image.stem, fill="white")
        with Image.open(image) as frame:
            canvas.paste(frame.convert("RGB").resize((width, height), Image.Resampling.LANCZOS), (x, y + 18))
    canvas.save(QA / name, quality=93)

def render(polish=False):
    chunks = WORK / "render-chunks"
    chunks.mkdir(exist_ok=True)
    entries = []
    for start in range(0, N, 150):
        end = min(start + 150, N)
        part = chunks / f"{start:04d}-{end-1:04d}.mp4"
        if polish and start in {150, 750}:
            part = part.with_name(part.stem + "-clean-join.mp4")
        marker = part.with_suffix(".json")
        if not marker.exists():
            cool()
            run(NODE, REMOTION, "render", BUNDLE, "ViralShort", part,
                f"--props={PROPS}", f"--frames={start}-{end-1}", "--gl=angle", "--concurrency=1",
                "--offthreadvideo-video-threads=2", "--offthreadvideo-cache-size-in-bytes=134217728",
                "--hardware-acceleration=required", "--video-bitrate=22M", "--image-format=jpeg",
                "--jpeg-quality=100", "--muted")
            save(marker, decode(part, end - start))
        entries.append(f"file '{part.as_posix()}'\nduration {(end - start)/FPS:.9f}")
    listing = chunks / ("concat-clean-joins.txt" if polish else "concat.txt")
    listing.write_text("\n".join(entries) + "\n", encoding="utf-8")
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    ff("-f", "concat", "-safe", 0, "-i", listing, "-i", MASTER, "-map", "0:v:0", "-map", "1:a:0",
       "-c", "copy", "-map_metadata", -1, "-video_track_timescale", 30000, "-movflags", "+faststart", OUTPUT)
    assert audio_packets(MASTER) == audio_packets(OUTPUT)
    result = probe(OUTPUT)
    assert (result.width, result.height, result.rate) == (1080, 1920, "30000/1001")
    assert abs(result.duration - N / FPS) < .034
    cool()
    receipt = decode(OUTPUT, N)
    clock = video_clock(OUTPUT)
    assert clock['regular'] and clock['frames'] == N, clock
    ff("-i", OUTPUT, "-map", "0:a:0", "-f", "null", "-")
    ff("-i", OUTPUT, "-map", "0:a:0", "-ac", 1, "-ar", 16000, "-c:a", "libmp3lame", "-b:a", "24k", QA / "listening-copy.mp3")
    samples = [3, 20, 50, 82, 104, 105, 132, 167, 191, 225, 262, 263, 619, 620,
               641, 668, 669, 698, 722, 723, 823, 824, 850, 908, 957, 986, 987, 990, 1034, 1060, 1087]
    files = []
    for index, frame in enumerate(samples):
        if index % 5 == 0:
            cool()
        path = QA / f"frame-{frame:04d}.jpg"
        ff("-hwaccel", "cuda", "-ss", f"{frame/FPS:.6f}", "-i", OUTPUT, "-an",
           "-frames:v", 1, "-vf", "scale=360:640", "-q:v", 2, path)
        files.append(path)
    for i in range(0, len(files), 8):
        sheet(files[i:i+8], f"review-{i//8+1}.jpg")
    save(QA / "technical.json", {"width": result.width, "height": result.height, "fps": result.rate,
         "frames": N, "duration_seconds": result.duration, "full_decode": receipt, "picture_clock": clock,
         "dialogue_audio_decode": True, "dialogue_packets_and_timestamps_identical": True,
         "sample_frames": samples, "additional_audio": False})
    print("TEST_VALIDATED", OUTPUT, flush=True)

def polish():
    global PROPS, OUTPUT, QA
    props = read(PROPS)
    fixed = []
    for layer in props["referenceEdit"]["layers"]:
        for cut in (263 / FPS, 824 / FPS):
            if layer["t"] < cut < layer["t"] + layer["dur"]:
                layer["dur"] = cut - layer["t"]
                fixed.append(layer["text"])
    assert fixed
    print("CUT_BOUNDARY_FADES", fixed, flush=True)
    PROPS = WORK / "review-props-clean-joins.json"
    save(PROPS, props)
    QA = QA / "clean-joins"
    QA.mkdir(exist_ok=True)
    OUTPUT = OUTPUT.with_name(OUTPUT.stem + "-v2.mp4")
    render(polish=True)

mode = sys.argv[1]
if mode == "author":
    author()
else:
    require_guard(gpu=True)
    {"stills": stills, "render": render, "polish": polish}[mode]()





