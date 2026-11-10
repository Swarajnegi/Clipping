"""Render only the changed picture spans and restore the approved dialogue."""
import math
import re
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageFont

from study_candidates import WORK, ROOT, cool, ff, probe, read, require_guard, save, sheet
from common import NODE, REMOTION
from motion_edit import audio_packets, decode, video_clock

P = WORK.parent / "complete-thoughts-20261108"
PROOFS = {entry["id"]: entry for entry in read(P / "proofs.json")}
PLAN = read(WORK / "edit-plan.json")
PUBLIC = WORK / "public"
BUNDLE = WORK / "bundle"
QA = WORK / "qa"
RENDER = WORK / "render"
OUT = WORK / "review"
FONTS = ROOT / ".agents/skills/viral-shorts/assets/fonts"
TRACKING = -.025
ACCENTS = {
    "01": {"larger": (88, "cormorant", 500), "grow": (83, "inter", 820), "narrower": (91, "cormorant", 500)},
    "03": {"competing": (76, "inter", 800), "gold": (98, "cormorant", 500), "system": (94, "inter", 820),
           "habits": (86, "cormorant", 500)},
    "04": {"likes": (83, "inter", 820), "value": (84, "cormorant", 500), "already": (83, "cormorant", 500)},
    "05": {"hours": (85, "inter", 830), "jokes": (84, "cormorant", 500), "venue": (92, "inter", 820),
           "special": (79, "cormorant", 500), "one-liners": (86, "inter", 820), "care": (87, "cormorant", 500)},
}

def run(*arguments):
    subprocess.run(list(map(str, arguments)), cwd=ROOT, check=True)

def token(text):
    return re.sub(r"[^a-z-]", "", text.lower())

def width(text, size, font, weight):
    if font == "inter":
        face = ImageFont.truetype(FONTS / "InterVariable.woff2", round(size * 8))
        face.set_variation_by_axes([min(32, size), weight])
    else:
        face = ImageFont.truetype(FONTS / "CormorantGaramond-Italic.ttf", round(size * 8))
    return max(size * .34, face.getlength(text) / 8 + TRACKING * size * max(0, len(text)-1) + 6)

def font_rows(words, accents, maximum):
    measurements = []
    for word in words:
        size, font, weight = accents.get(token(word["text"]), (61, "inter", 700))
        measurements.append((word, size, font, weight, width(word["text"], size, font, weight)))
    def total(row):
        return sum(item[-1] for item in row) + 11 * (len(row)-1)
    if total(measurements) <= maximum or len(words) == 1:
        return [measurements]
    split = min(range(1,len(words)), key=lambda i: max(total(measurements[:i]), total(measurements[i:])))
    return [measurements[:split], measurements[split:]]

def patch_layers(groups, original_groups, caption, accents, start_frame, stop_frame, fps):
    start, end = start_frame / fps, stop_frame / fps
    xc, yc, maximum = caption
    layers = []
    for i in groups:
        rows = font_rows(original_groups[i], accents, maximum)
        heights = [max(word[1] for word in row) for row in rows]
        top = yc - (sum(heights) + 4 * (len(rows)-1)) / 2
        for row, height in zip(rows, heights):
            line_width = sum(item[-1] for item in row) + 11 * (len(row)-1)
            scale = min(1, maximum / line_width)
            left = xc - line_width * scale / 2
            for layer, size, font, weight, span in row:
                t = max(0, layer["t"] - start)
                duration = min(end, layer["t"] + layer["dur"]) - start - t
                assert duration > 0, (layer, start_frame, stop_frame)
                patched = dict(layer, t=t, dur=duration, x=round(left, 2),
                               y=round(top + (height - size * scale) * .6, 2),
                               width=round(span * scale, 2), size=round(size * scale, 2),
                               font=font, italic=font == "cormorant", weight=weight, tracking=TRACKING,
                               surface="difference", color="#ffffff", blend="difference",
                               motion={"inSec": .085, "outSec": .035, "rise": 5, "scaleFrom": .98,
                                       "blur": 1.3, "easing": "cubic"})
                assert 60 < patched["x"] < patched["x"] + patched["width"] < 1020
                assert 480 < patched["y"] < patched["y"] + patched["size"] * 1.2 < 1430
                layers.append(patched)
                left += (span + 11) * scale
            top += height + 4
    return layers

def author():
    PUBLIC.mkdir(exist_ok=True)
    QA.mkdir(exist_ok=True)
    RENDER.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "public/fonts", PUBLIC / "fonts", dirs_exist_ok=True)
    items = []
    records = read(WORK / "candidate-review/inventory.json")
    for ident, shots in PLAN.items():
        base = P / "finish-v1/props" / ident
        props = read(base.with_suffix(".json"))
        caption_plan = read(base.with_name(ident + "-caption-plan.json"))
        fps = PROOFS[ident]["fps"]
        groups = caption_plan["groups"]
        layers = props["referenceEdit"]["layers"]
        position = 0
        grouped = []
        for group in groups:
            n = len(group["text"].split())
            grouped.append(layers[position:position+n])
            assert [token(l["text"]) for l in grouped[-1]] == [token(w) for w in group["text"].split()]
            position += n
        assert position == len(layers)
        parts = []
        for index, shot in enumerate(shots, 1):
            start, end = shot["from"], shot["to"]
            a = round(groups[start]["start"] * fps)
            # Where an insert changes on the next phrase, start that phrase on
            # the same frame as its first timed word.
            after = groups[end-1]["end"]
            b = round(after * fps) if index < len(shots) and shots[index]["from"] == end else math.ceil(after * fps - 1e-7)
            item = records[shot["slug"]]
            assert shot["offset"] + (b-a) / fps <= item["clip_seconds"] + .01
            assert not parts or parts[-1]["end_frame"] <= a
            patch_id = f"{ident[:2]}-insert-{index:02d}"
            patch = dict(shot, **item, id=patch_id, start_frame=a, end_frame=b,
                         spoken=" ".join(g["text"] for g in groups[start:end]))
            side = min(item["dimensions"])
            crop = min(item["dimensions"][0]-side, max(0, round((shot["crop_x"] * item["dimensions"][0] - side/2)/2)*2))
            patch.update(square_side=side, crop_left=crop, staged_side=min(side, 1960))
            picture = props["referenceEdit"]["frame"]
            made = patch_layers(range(start, end), grouped, shot["caption"], ACCENTS[ident[:2]], a, b, fps)
            new = dict(props, src=patch_id+".mp4", srcWidth=patch["staged_side"], srcHeight=patch["staged_side"],
                       widthFrac=1, shots=[{"t":0,"x":.5,"w":1,"lock":True}], track=[], durationSec=(b-a)/fps,
                       punchIns=[], grade={"brightness":1,"contrast":1,"saturate":1}, watermark=None, cutaways=[],
                       referenceEdit={"profile":"editorial","palette":"silver","layeredOnly":True,"frame":picture,"layers":made})
            propfile = WORK / f"{patch_id}.json"
            save(propfile, new)
            parts.append(patch)
        items.append({**PROOFS[ident], "inserts": parts})
    save(WORK / "shot-map.json", items)
    print("AUTHORED", len(items), sum(len(item["inserts"]) for item in items), flush=True)

def stage(item, patch):
    dest = PUBLIC / (patch["id"] + ".mp4")
    if dest.exists():
        raise FileExistsError(dest)
    cool()
    side = patch["square_side"]
    out = patch["staged_side"]
    args = ["-y", "-hwaccel", "cuda", "-ss", patch["offset"], "-i", patch["file"]]
    filt = (f"crop={side}:{side}:{patch['crop_left']}:{patch.get('crop_top', 0)},scale={out}:{out}:flags=lanczos,"
            f"format=yuv420p,fps={item['rate']}")
    maps = ["-map", "0:v:0", "-vf", filt]
    if patch.get("top_scrim"):
        scrim = WORK / (patch["id"] + "-scrim.png")
        canvas = Image.new("RGBA", (out, out))
        for y in range(round(.225*out)):
            alpha = round(98 * max(0, min(1, (.225*out-y)/(.095*out))))
            canvas.paste((0,0,0,alpha), (0,y,out,y+1))
        canvas.save(scrim)
        args += ["-i", scrim]
        maps = ["-filter_complex", f"[0:v]{filt}[base];[base][1:v]overlay=eof_action=repeat:format=yuv420[v]", "-map", "[v]"]
    n = patch["end_frame"] - patch["start_frame"]
    ff(*args, *maps, "-an", "-sn", "-frames:v", n,
       "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", 16, "-b:v", 0, "-movflags", "+faststart", dest)
    assert abs(probe(dest).duration - n / item["fps"]) < .002

def shared(patch):
    return [f"--props={WORK / (patch['id'] + '.json')}", "--scale=2", "--gl=angle",
            "--offthreadvideo-video-threads=2", "--offthreadvideo-cache-size-in-bytes=134217728"]

def prepare():
    records = read(WORK / "shot-map.json")
    for item in records:
        for patch in item["inserts"]:
            stage(item, patch)
    run(NODE, REMOTION, "bundle", "src/index.ts", f"--public-dir={PUBLIC}", f"--out-dir={BUNDLE}")
    for item in records:
        previews = []
        for patch in item["inserts"]:
            cool()
            dest = QA / f"{patch['id']}-still.png"
            frame = round((patch["end_frame"] - patch["start_frame"] - 1) * .72)
            run(NODE, REMOTION, "still", BUNDLE, "ViralShort", dest, f"--frame={frame}", *shared(patch))
            with Image.open(dest) as image:
                region = image.crop((100, 940, 2060, 2900)).convert("RGB")
                previews.append((patch["id"], region))
        sheet(previews, QA / f"{item['id'][:2]}-patch-stills.jpg", 320, 320, 3)

def normalize(item, source, start, count, dest):
    cool()
    numerator = Fraction(item["rate"]).numerator
    ff("-y", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
       "-ss", f"{max(0, start / item['fps'] - .000001):.6f}", "-i", source, "-map", "0:v:0",
       "-an", "-frames:v", count, "-c:v", "h264_nvenc", "-preset", "p4", "-profile:v", "high",
       "-rc", "vbr", "-cq", 17, "-b:v", 0, "-maxrate", "55M", "-bufsize", "110M", "-bf", 0,
       "-vf", "scale_cuda=format=nv12,hwdownload,format=nv12", "-pix_fmt", "nv12", "-fps_mode", "passthrough",
       "-video_track_timescale", numerator, dest)
    m = probe(dest)
    assert m.rate == item["rate"] and (m.width, m.height) == (2160,3840)
    assert abs(m.duration - count / item["fps"]) < .002, (dest, m.duration, count)

def render(item, refresh=None):
    ident = item["id"]
    source = P / "finish-v1/finished" / f"{ident}-music-free.mp4"
    clean = P / "drafts" / f"{ident}-clean-assembly.mp4"
    final = OUT / f"{ident}-movie-cutaways-REVIEW.mp4"
    if final.exists():
        raise FileExistsError(final)
    parts = []
    cursor = 0
    for patch in item["inserts"]:
        a, b = patch["start_frame"], patch["end_frame"]
        if a > cursor:
            dest = RENDER / f"{ident[:2]}-speaker-{cursor:04d}.mp4"
            if refresh is None or not dest.exists():
                normalize(item, source, cursor, a-cursor, dest)
            parts.append((dest,a-cursor))
        tag = patch["id"] + ("-fit" if refresh and patch["id"] in refresh else "")
        dest = RENDER / (tag + "-normalized.mp4")
        if refresh is None or patch["id"] in refresh or not dest.exists():
            raw = RENDER / (tag + "-render.mp4")
            cool()
            run(NODE, REMOTION, "render", BUNDLE, "ViralShort", raw,
                "--concurrency=1", "--hardware-acceleration=required", "--video-bitrate=34M",
                "--image-format=jpeg", "--jpeg-quality=100", "--muted", *shared(patch))
            normalize(item, raw, 0, b-a, dest)
        parts.append((dest,b-a))
        cursor = b
    dest = RENDER / f"{ident[:2]}-speaker-{cursor:04d}.mp4"
    if refresh is None or not dest.exists():
        normalize(item, source, cursor, item["frames"]-cursor, dest)
    parts.append((dest,item["frames"]-cursor))
    assert sum(n for _,n in parts) == item["frames"]
    listing = RENDER / f"{ident[:2]}-concat.txt"
    listing.write_text("\n".join(f"file '{f.as_posix()}'\nduration {n/item['fps']:.9f}" for f,n in parts)+"\n", encoding="utf-8")
    ff("-y", "-f", "concat", "-safe", 0, "-i", listing, "-i", clean, "-map", "0:v:0", "-map", "1:a:0",
       "-c", "copy", "-map_metadata", -1, "-video_track_timescale", Fraction(item["rate"]).numerator, "-movflags", "+faststart", final)
    cool()
    clock = video_clock(final)
    assert clock["frames"] == item["frames"] and clock["regular"] and clock["rate"] == item["rate"], clock
    assert abs(clock["duration"] - item["duration"]) < .001 and abs(clock["first_pts"]) < .001
    assert audio_packets(final) == audio_packets(clean) == audio_packets(source)
    ff("-i", final, "-map", "0:a:0", "-f", "null", "-")
    verified = review_frames(item, final)
    save(QA / f"{ident[:2]}-technical.json", {"file": str(final), "clock":clock, "dialogue_packet_equal":True,
         "all_frames_cuda_decoded":True, "audio_decoded":True, "review_frames":verified,
         "reuse_basis":"Private owner review. Posting reuse for cutaways is unresolved."})
    print("VERIFIED", ident, item["frames"], flush=True)

def review_frames(item, final):
    want = {0, round(1.5*item["fps"]), round(2.95*item["fps"]), item["frames"]-2}
    for patch in item["inserts"]:
        a,b=patch["start_frame"],patch["end_frame"]
        want.update([a-1,a, (a+b)//2,b-1,b])
    want = sorted(want)
    # Decode every frame and count it while retaining only requested frames.
    from common import FFMPEG, ffmpeg_command
    command = ffmpeg_command([FFMPEG,"-v","error","-xerror","-hwaccel","cuda","-hwaccel_output_format","cuda",
                              "-i",str(final),"-an","-vf","scale_cuda=180:320:format=nv12,hwdownload,format=nv12,format=rgb24",
                              "-fps_mode","passthrough","-f","rawvideo","-"])
    frames = []
    with subprocess.Popen(command, stdout=subprocess.PIPE) as proc:
        n = 0
        while raw := proc.stdout.read(180*320*3):
            assert len(raw) == 180*320*3
            if n in want:
                frames.append((f"{n/item['fps']:.2f}s   f{n}",Image.frombytes("RGB",(180,320),raw)))
            n += 1
        assert proc.wait() == 0 and n == item["frames"], (n,item["frames"])
    for page, start in enumerate(range(0,len(frames),12),1):
        sheet(frames[start:start+12],QA/f"{item['id'][:2]}-final-{page}.jpg",180,320,6)
    return want

def fit_picture():
    import numpy as np

    items = read(WORK / "shot-map.json")
    changes = {}
    for item in items:
        for patch in item["inserts"]:
            cool()
            name = patch["id"] + ".mp4"
            asset = PUBLIC / name
            sampled = ff("-hwaccel", "cuda", "-hwaccel_output_format", "cuda", "-i", asset, "-an",
                         "-vf", "fps=3,scale_cuda=160:160:format=nv12,hwdownload,format=nv12,format=rgb24",
                         "-f", "rawvideo", "-")
            image = np.frombuffer(sampled, dtype=np.uint8).reshape(-1, 160, 160, 3)
            bright = np.quantile(image, .985, axis=(0, 2, 3)) > 14
            if not bright.any():
                continue
            top = int(bright.argmax())
            bottom = int(bright[::-1].argmax())
            # Only remove stable, near-symmetric source matte, measured across
            # the entire chosen interval.
            if min(top, bottom) < 4 or abs(top - bottom) > 4 or max(top, bottom) > 24:
                continue
            old_side = patch["square_side"]
            up = math.ceil((top + 1) * old_side / 320) * 2
            down = math.ceil((bottom + 1) * old_side / 320) * 2
            side = old_side - up - down
            source_width = patch["dimensions"][0]
            left = min(source_width - side, max(0, round((patch["crop_x"] * source_width - side/2)/2)*2))
            patch.update(square_side=side, crop_left=left, crop_top=up, staged_side=min(side,1960),
                         removed_matte=[up,down])
            asset.replace(QA / (patch["id"] + "-letterboxed.mp4"))
            stage(item, patch)
            shutil.copy2(asset, BUNDLE / "public" / name)
            props = WORK / (patch["id"] + ".json")
            revised = read(props)
            revised.update(srcWidth=patch["staged_side"], srcHeight=patch["staged_side"])
            save(props, revised)
            changes.setdefault(item["id"], set()).add(patch["id"])
            print("MATTE", patch["id"], up, down, flush=True)
    save(WORK / "shot-map.json", items)
    for item in items:
        ident = item["id"]
        if ident in changes:
            name = f"{ident}-movie-cutaways-REVIEW.mp4"
            (OUT / name).replace(QA / (ident + "-first-review.mp4"))
            render(item, changes[ident])

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "author":
        author()
    else:
        require_guard(gpu=True)
        if mode == "prepare":
            prepare()
        elif mode == "fit-picture":
            fit_picture()
        elif mode == "adjust-walter":
            item = read(WORK / "shot-map.json")[-1]
            patch = item["inserts"][-1]
            name = patch["id"] + ".mp4"
            (PUBLIC / name).replace(QA / "walter-first-crop.mp4")
            stage(item, patch)
            shutil.copy2(PUBLIC / name, BUNDLE / "public" / name)
            dest = QA / "walter-adjusted.png"
            run(NODE, REMOTION, "still", BUNDLE, "ViralShort", dest, "--frame=56", *shared(patch))
            with Image.open(dest) as im:
                im.crop((100,940,2060,2900)).resize((560,560)).convert("RGB").save(QA / "walter-adjusted.jpg", quality=93)
        elif mode == "render":
            for item in read(WORK / "shot-map.json"):
                if not sys.argv[2:] or item["id"][:2] in sys.argv[2:]:
                    render(item)
        else:
            raise ValueError(mode)



