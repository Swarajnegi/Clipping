"""Replace selected cutaways while reusing the verified speaker and retained inserts."""
import os
import shutil
import sys
import time
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import cv2

import cutaway_batch as batch
from varied_candidates import WORK

OLD = batch.WORK
for name in ("PUBLIC", "QA", "REVIEW", "PARTS", "BUNDLE"):
    setattr(batch, name, WORK / name.lower())
batch.WORK = WORK
batch.prior.QA = batch.QA
OUT = batch.ROOT / "Main/shorts-clips/Exports"
ORIGINAL = OUT / "01 Finished Edits/2026-11-10 - Speeches and Podcasts - Original Footage"
EXPORT = OUT / "02 Private Reviews/2026-11-10 - Speeches and Podcasts - Varied Cutaways"


def retained(source, target):
    if not target.exists():
        os.link(source, target)
    assert source.samefile(target), target


def wrap_phrases(placement, splits):
    result = []
    for group, words in placement:
        split = splits.get(group["text"])
        if split is None:
            result.append((group, words))
            continue
        rows = (words[:split], words[split:])
        heights = [max(word["size"] for word in row) + 8 for row in rows]
        x, y = group["centre"]
        top = y - sum(heights) / 2
        arranged = []
        for row, height in zip(rows, heights):
            width = sum(word["width"] for word in row) + 10 * (len(row) - 1)
            left = x - width / 2
            for word in row:
                arranged.append(dict(word, x=left, y=top + (height - word["size"]) * .52))
                left += word["width"] + 10
            top += height
        result.append((group, arranged))
    return result


def prepare(only=None):
    from varied_plan import CHANGES, PLACEMENT, WRAPS

    for folder in (batch.PUBLIC, batch.QA, batch.REVIEW, batch.PARTS):
        folder.mkdir(parents=True, exist_ok=True)
    if not (batch.PUBLIC / "fonts").exists():
        shutil.copytree(batch.FONT_DIR, batch.PUBLIC / "fonts")
    available = batch.read(WORK / "candidate-review/inventory.json")
    cv2.setNumThreads(2)
    records = batch.read(OLD / "shot-map.json")
    saved = batch.read(WORK / "shot-map.json") if only else records
    for index, item in enumerate(records):
        ident, fps = item["id"], item["fps"]
        number = ident[:2]
        if only and number not in only:
            records[index] = saved[index]
            continue
        for base in (OLD / "parts").glob(number + "-base-*.mp4"):
            retained(base, batch.PARTS / base.name)
        props = batch.read(batch.F / "props" / (ident + ".json"))
        groups = batch.read(batch.F / "qa" / (ident + "-placement.json"))
        placement = batch.bind_layers(groups, props["referenceEdit"]["layers"])
        parts, layers = [], []
        cursor = 0
        for slot, previous in enumerate(item["inserts"], 1):
            a, b = previous["start_frame"], previous["end_frame"]
            count = b - a
            choice = CHANGES[number].get(slot)
            if choice is None:
                overlay = f"{number}-overlay-{slot:02d}.mp4"
                retained(OLD / "parts" / overlay, batch.PARTS / overlay)
                previous["retained"] = True
                continue
            title, slug, offset, crop, reason = choice
            asset = available[slug]
            assert asset["title"] == title and Path(asset["file"]).is_file()
            assert offset + count / fps <= asset["clip_seconds"] + .025, slug
            width, height = asset["dimensions"]
            top = 120 if title.endswith("S06") else 24 if title.endswith("S04") else 0
            side = min(width, height - 2 * top)
            left = max(0, min(width - side, round((crop * width - side / 2) / 2) * 2))
            shot = dict(asset, start_frame=a, end_frame=b, montage_frame=cursor, offset=offset,
                        source_in=asset["source_start"] + offset,
                        source_out=asset["source_start"] + offset + count / fps,
                        side=side, top=top, left=left, reason=reason, caption_placements=[],
                        retained=False)
            segment = batch.PARTS / f"{number}-insert-{slot:02d}.mp4"
            batch.normalize(asset["file"], 0, count, item, segment, square=True, shot=shot)
            layout = wrap_phrases(placement, WRAPS.get((number, slot), {}))
            if (number, slot) in PLACEMENT:
                x, y = PLACEMENT[number, slot]

                def fixed(rows, views, start, end, _punches):
                    width = max(sum(word[4] for word in row) + 10 * (len(row)-1) for row in rows)
                    height = sum(max(word[1] for word in row) + 8 for row in rows)
                    assert 86 <= x-width/2 and x+width/2 <= 994
                    assert 494 <= y-height/2 and y+height/2 <= 1412
                    overlaps = sum(
                        min(x+width/2, 50+fx+fw+16) > max(x-width/2, 50+fx-16)
                        and min(y+height/2, 470+fy+fh+24) > max(y-height/2, 470+fy-18)
                        for t, _, faces in views if start-.18 <= t <= end+.18
                        for fx, fy, fw, fh in faces
                    )
                    return x, y, height, overlaps

                with patch.object(batch, "preferred_position", fixed):
                    layers.extend(batch.caption_patch(layout, shot, segment, fps))
                shot["placement_method"] = "Manually positioned after rendered frame inspection"
            else:
                layers.extend(batch.caption_patch(layout, shot, segment, fps))
            item["inserts"][slot - 1] = shot
            parts.append((segment, count))
            cursor += count
        assert len(item["inserts"]) == 6 and parts
        assert len({shot["title"] for shot in item["inserts"]}) >= 4, ident
        item["montage_frames"] = cursor
        video = batch.PUBLIC / (number + "-montage.mp4")
        listing = batch.PARTS / (number + "-montage.txt")
        batch.join_list(parts, fps, listing)
        batch.ff("-y", "-f", "concat", "-safe", 0, "-i", listing, "-map", "0:v:0", "-c", "copy",
                 "-video_track_timescale", Fraction(item["rate"]).numerator, video)
        clock = batch.video_clock(video)
        assert clock["frames"] == cursor and clock["regular"] and clock["rate"] == item["rate"]
        treatment = dict(props["referenceEdit"], layers=layers)
        batch.validate_reference_edit(treatment, cursor / fps)
        assert all(layer["surface"] == "difference" and layer["shadow"] == "none" for layer in layers)
        props.update(src=video.name, durationSec=cursor / fps, punchIns=[], hook="", referenceEdit=treatment)
        batch.save(WORK / (number + "-props.json"), props)
        print("STAGED", ident, len(parts), "replacements", cursor, "frames", flush=True)
    batch.save(WORK / "shot-map.json", records)
    batch.prior.run(batch.NODE, batch.REMOTION, "bundle", "src/index.ts",
                    f"--public-dir={batch.PUBLIC}", f"--out-dir={batch.BUNDLE}")


def repair(numbers):
    from varied_plan import CHANGES

    archive = WORK / f"before-placement-revision-{time.time_ns()}"
    archive.mkdir()
    records = batch.read(WORK / "shot-map.json")
    for item in records:
        ident, number = item["id"], item["id"][:2]
        if number not in numbers:
            continue
        paths = [
            batch.QA / (number + "-technical.json"),
            batch.REVIEW / (ident + "-movie-cutaways-PRIVATE-REVIEW.mp4"),
            batch.PARTS / (number + "-montage-render.mp4"),
            *batch.QA.glob(number + "-final-*.jpg"),
        ]
        for slot, shot in enumerate(item["inserts"], 1):
            if not shot["retained"] or slot in CHANGES[number]:
                paths += [batch.PARTS / f"{number}-{kind}-{slot:02d}.mp4"
                          for kind in ("insert", "overlay")]
        for path in paths:
            assert path.resolve().is_relative_to(WORK)
            if path.exists():
                path.replace(archive / path.name)
    prepare(numbers)
    batch.render()
    checks = {
        "01": (5.40, 26.26),
        "02": (26.95, 27.39, 28.10),
        "03": (14.90, 15.34),
        "04": (1.92, 2.42, 3.30, 16.48, 17.63),
        "05": (11.98, 12.23, 12.48),
    }
    for item in records:
        number = item["id"][:2]
        if number not in numbers:
            continue
        proof = batch.read(batch.QA / (number + "-technical.json"))
        for second in checks[number]:
            batch.ff("-y", "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
                     "-ss", f"{second:.3f}", "-i", proof["video"], "-map", "0:v:0", "-an",
                     "-vf", "scale_cuda=540:960:format=nv12,hwdownload,format=nv12",
                     "-frames:v", 1, batch.QA / f"{number}-placement-{second:.2f}.jpg")


def deliver():
    items = batch.read(WORK / "shot-map.json")
    proofs = [batch.read(batch.QA / (item["id"][:2] + "-technical.json")) for item in items]
    assert len(proofs) == 5 and all(
        proof["full_decode"] and proof["original_dialogue_packet_match"] and proof["inserts"] == 6
        for proof in proofs
    )
    assert (batch.QA / "visual-review.json").is_file()
    EXPORT.mkdir()
    notes = [
        "# Five varied movie cutaway revisions", "",
        "Private review. Posting reuse for the film and TV footage remains unresolved.", "",
        "Each edit has six inserts. Picture timing and the original music-free dialogue packets were verified.",
        "Opening, insert boundaries, selected motion frames and caption placement were visually sampled.",
        "Continuous viewing with sound remains unverified.", "",
    ]
    for item, proof in zip(items, proofs):
        ident = item["id"]
        src = Path(proof["video"])
        dest = EXPORT / (ident + "-varied-movie-cutaways-PRIVATE-REVIEW.mp4")
        retained(src, dest)
        proof["video"] = str(dest)
        thumb = ORIGINAL / (ident + "-thumbnail.jpg")
        retained(thumb, EXPORT / thumb.name)
        notes += [f"## [{ident[3:].replace('-', ' ').title()}]({dest.name})", ""]
        for shot in item["inserts"]:
            notes.append(f"- {shot['start_frame']/item['fps']:.2f}s — {shot['title']}. {shot['reason']}")
        notes.append("")
    (EXPORT / "REVIEW.md").write_text("\n".join(notes), encoding="utf-8")
    batch.save(EXPORT / "QA.json", proofs)
    batch.save(EXPORT / "SHOT-MAP.json", items)
    batch.save(EXPORT / "VISUAL-REVIEW.json", batch.read(batch.QA / "visual-review.json"))
    print(EXPORT)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode != "deliver":
        batch.require_guard(gpu=True)
    if mode in ("prepare", "batch"):
        prepare()
    if mode in ("render", "batch"):
        batch.render()
    if mode == "repair":
        repair(set(sys.argv[2:]))
    if mode == "deliver":
        deliver()
