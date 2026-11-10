"""Translate reviewed sheet IDs into excerpt ranges and generate browseable catalogues."""
import json
import re
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
MOVIES = WORK.parents[1] / "Movie Clips"
NAMES = ("Fight Club", "Jon Snow", "Iron Man")

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def selection():
    indices = [{item["id"]: item for item in read(MOVIES / name / "shot-index.json")["candidates"]} for name in NAMES]
    earlier = [read(MOVIES / name / "catalogue.json")["clips"] for name in NAMES]
    selected = []
    seen = set()
    for line in (WORK / "library-tags.txt").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        number, ident, title, tags = line.split("|", 3)
        pack, key = int(number) - 1, int(ident)
        assert (pack, key) not in seen and 0 <= pack < len(NAMES)
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", title)
        seen.add((pack, key))
        row = indices[pack][key]
        start = row["start"]
        end = row["end"]
        if any(min(end, clip["source_end_exclusive"]) - max(start, clip["source_start"]) > .75
               for clip in earlier[pack]):
            print("SKIP_OVERLAP", NAMES[pack], key)
            continue
        assert 2.5 <= end - start <= 5.6
        selected.append([pack, start, round(end - start, 3), title, tags])
    (WORK / "library-selection.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
    print("SELECTED", [sum(row[0] == pack for row in selected) for pack in range(3)])

def timecode(seconds):
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours:02d}:{minutes:02d}:{sec:06.3f}"

def catalogues():
    total = 0
    summary = ["# Movie cutaway library", "",
        "Silent source-native excerpts for choosing cutaways by action or emotion. "
        "Use each title's catalogue to find a shot and check its source time. "
        "The original scenepacks remain in this folder.", "",
        "| Pack | Excerpts | Source dimensions |", "| --- | ---: | --- |"]
    for name in NAMES:
        folder = MOVIES / name
        data = read(folder / "catalogue.json")
        clips = data["clips"]
        listed = {row["file"] for row in clips}
        actual = {path.name for path in folder.glob("*.mp4") if ".partial." not in path.name}
        assert len(listed) == len(clips) and actual == listed, (name, actual - listed, listed - actual)
        assert all(row["bytes"] == (folder / row["file"]).stat().st_size and row["video_decoded"] and row["silent"] for row in clips)
        total += len(clips)
        dimensions = "×".join(map(str, data["source_resolution"]))
        link = name.replace(" ", "%20")
        summary.append(f"| [{name}]({link}/CATALOGUE.md) | {len(clips)} | {dimensions} |")
        lines = [f"# {name}", "", f"Source pack **{data['source']}**.", "",
                 f"All {len(clips)} excerpts are silent, {dimensions}, at {data['source_frame_rate']} FPS.",
                 "The timecodes refer to the local pack and identify the requested range to the nearest source frame.",
                 "", "| Time in pack | Excerpt | Use it for |", "| --- | --- | --- |"]
        for row in clips:
            file = row["file"]
            label = file.split("-", 1)[1].removesuffix(".mp4").replace("-", " ")
            lines.append(f"| {timecode(row['source_start'])} | [{label}]({file}) | {', '.join(row['tags'])} |")
        lines += ["", "See [catalogue.json](catalogue.json) for exact requested offsets, clip sizes and review coverage."]
        if (folder / "shot-index.json").exists():
            lines.append("See [shot-index.json](shot-index.json) for the candidate scan and sample windows.")
        (folder / "CATALOGUE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary += ["", f"**{total} excerpts.** All exported files passed a full decode. "
        "Editorial tags are based on inspected sample frames and the denser test windows.", "",
        "Coverage includes windows distributed across each pack. Review adjacent action before committing to a cut. "
        "Posting reuse for the film and television footage is unresolved."]
    (MOVIES / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print("CATALOGUED", total)

{"select": selection, "catalogue": catalogues}[sys.argv[1]]()
