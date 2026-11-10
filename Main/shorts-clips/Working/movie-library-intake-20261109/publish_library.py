"""Reconcile the standalone files and publish pack and library browse indexes."""
import sys

from pack_intake import MOVIES, PACKS, WORK, load, save


def timecode(value):
    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def reconcile(folder, data):
    clips = data["clips"]
    names = {row["file"] for row in clips}
    files = {p.name for p in folder.glob("*.mp4") if not p.name.endswith(".partial.mp4")}
    if len(names) != len(clips) or names != files:
        raise RuntimeError(f"Catalogue/file mismatch in {folder}: {names ^ files}")
    for clip in clips:
        path = folder / clip["file"]
        if path.stat().st_size != clip["bytes"] or not clip["silent"] or not clip["video_decoded"]:
            raise RuntimeError(f"Missing verification: {path}")
    return len(clips), sum(clip["bytes"] for clip in clips)


def publish(complete_only=False):
    new_titles = {title for _, title, _ in PACKS.values()}
    summary = [
        "# Movie cutaway library", "",
        "Standalone, silent source-native excerpts. They remain usable after the owner removes the original pack.",
        "", "| Pack | Excerpts | Source dimensions | Intake status |", "| --- | ---: | --- | --- |",
    ]
    added = 0
    total = 0
    reports = []
    for folder in sorted(MOVIES.iterdir()):
        if not folder.is_dir() or not (folder / "catalogue.json").is_file():
            continue
        data = load(folder / "catalogue.json")
        new = folder.name in new_titles
        if new and complete_only and not data.get("selection_complete"):
            continue
        count, bytes_saved = reconcile(folder, data)
        status = "Existing library"
        if new:
            added += count
            status = "Verified intake" if data.get("selection_complete") else "In progress"
            lines = [f"# {folder.name}", "", f"Original pack **{data['source']}**.", "",
                     f"{count} standalone, silent clips at {data['source_resolution'][0]}×{data['source_resolution'][1]} "
                     f"and {data['source_frame_rate']} FPS.", "",
                     "| Source time | Clip | Tags | Review |", "| --- | --- | --- | --- |"]
            for row in data["clips"]:
                name = row["file"].split("-", 1)[1].removesuffix(".mp4").replace("-", " ")
                lines.append(f"| {timecode(row['source_start'])} | [{name}]({row['file']}) | "
                             f"{', '.join(row['tags'])} | {row['review']} |")
            lines += ["", "The source timecodes are relative to the original local pack. "
                      "See [catalogue.json](catalogue.json) for the complete source and verification records.",
                      "", "Posting reuse is unresolved."]
            (folder / "CATALOGUE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
            reports.append({"title": folder.name, "file_count": count, "bytes": bytes_saved,
                            "status": status, "source": data["source"], "scan": data.get("scan")})
        total += count
        dim = "×".join(map(str, data["source_resolution"]))
        url = folder.name.replace(" ", "%20")
        summary.append(f"| [{folder.name}]({url}/CATALOGUE.md) | {count} | {dim} | {status} |")
    summary += ["", f"**{total} standalone excerpts**. Catalogue and files reconciled.",
                "", "Posting reuse for the film and television footage is unresolved."]
    (MOVIES / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    save(WORK / "handoff.json", {"new_clips": added, "total_clips": total, "packs": reports})
    print("CATALOGUED", added, "new clips;", total, "overall", flush=True)


if __name__ == "__main__":
    publish("--complete-only" in sys.argv)

