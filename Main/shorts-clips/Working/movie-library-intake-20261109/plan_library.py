"""Choose varied stand-alone b-roll intervals from the candidate review."""
import sys

from pack_intake import PACKS, WORK, load, save


def select(pack):
    directory = WORK / pack
    packet = load(directory / "candidates.json")
    candidates = packet["candidates"]
    seen = {}
    review = directory / "reviewed.tsv"
    if review.exists():
        for line in review.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            ident, label, tags = line.split("|", 2)
            seen[int(ident)] = (label, tags.split(", "))
    choices = {}
    for row in candidates:
        if row["id"] in seen:
            row["slug"], row["tags"] = seen[row["id"]]
            choices[row["id"]] = row

    # Preserve representative footage all along the timeline, even in stretches
    # without a manually named highlight. Prefer visually clear stable moments
    # and retain dynamic angles when they add variety.
    def strength(row):
        return row["score"] + min(row["motion_score"], 18) / 24
    spacing = 24
    for start in range(0, int(packet["source"]["video_seconds"]) + 1, spacing):
        span = [row for row in candidates if start <= row["sample_time"] < start + spacing]
        if not span:
            continue
        named = [row for row in span if row["id"] in seen]
        if not named:
            choices[max(span, key=strength)["id"]] = max(span, key=strength)
        elif all(row["motion_score"] < 9 for row in named):
            alternative = [row for row in span if row["motion_score"] >= 12 and row["score"] >= 5.8
                           and all(abs(row["sample_time"] - existing["sample_time"]) >= 5 for existing in named)]
            if alternative:
                best = max(alternative, key=strength)
                choices[best["id"]] = best
    selection = sorted(choices.values(), key=lambda row: row["start"])
    if not selection or not set(seen).issubset(choices):
        raise RuntimeError(f"Missing selections or reviewed IDs for {pack}")
    assert all(a["end"] <= b["start"] for a, b in zip(selection, selection[1:]))
    save(directory / "selection.json", selection)
    print("PLAN", pack, len(selection), "/", len(candidates), "candidates", len(seen), "named",
          round(sum(row["end"] - row["start"] for row in selection), 1), "seconds", flush=True)


if __name__ == "__main__":
    for name in sys.argv[1:] or PACKS:
        select(name)
