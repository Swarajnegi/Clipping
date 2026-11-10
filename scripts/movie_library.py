"""Search the local film and TV excerpt catalogues without opening video."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from common import ROOT

LIBRARY = ROOT / "Main" / "shorts-clips" / "Movie Clips"
CUES = {
    "anticipation": ("waiting", "anticipation", "expectation", "before the moment"),
    "choice": ("choice", "decision", "choose", "crossroads", "commitment", "threshold"),
    "conflict": ("conflict", "confrontation", "argument", "fight", "disagreement", "resistance"),
    "connection": ("connection", "friendship", "companionship", "conversation", "bond", "together"),
    "craft": ("craft", "patient craft", "hands at work", "making", "repair", "workshop", "building", "precision"),
    "focus": ("focus", "attention", "concentration", "practice", "discipline", "preparation"),
    "grief": ("grief", "loss", "mourning", "bereavement", "goodbye"),
    "help": ("help", "asking for help", "care", "support", "comfort", "reassurance", "vulnerability"),
    "hesitation": ("hesitation", "doubt", "uncertainty", "unease", "reluctance"),
    "isolation": ("isolation", "loneliness", "solitude", "alone", "lonely"),
    "listening": ("listening", "listen", "hearing someone", "attentive"),
    "pressure": ("pressure", "urgency", "stakes", "danger", "threat", "under fire"),
    "recovery": ("recovery", "recover", "trying again", "try again", "get back up", "regroup", "reset"),
    "reflection": ("reflection", "quiet reflection", "contemplation", "introspection", "thinking", "reflect", "quiet thought"),
    "relief": ("relief", "release", "calm after", "catch a breath", "catch his breath"),
    "repetition": ("repetition", "routine", "habit", "training", "practice", "daily work"),
    "resolve": ("resolve", "determination", "persist", "persistence", "perseverance", "push forward", "keep going"),
    "sacrifice": ("sacrifice", "cost", "giving something up"),
    "setback": ("setback", "failure", "fail", "defeat", "fall", "disappointment"),
    "teamwork": ("teamwork", "working together", "cooperation", "collaboration", "coordination"),
    "transition": ("transition", "journey", "travel", "arrival", "departure", "new chapter", "moving on"),
    "trust": ("trust", "confide", "opening up", "rely", "faith in someone"),
    "victory": ("victory", "win", "triumph", "success", "achievement", "celebration"),
}
EVIDENCE = {"prior_visual_review", "source_frame", "excerpt_samples", "motion_review", "unresolved"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def title_family(title):
    return title.split(" - ", 1)[0] if title.startswith("Peaky Blinders - ") else title


def inventory(root=LIBRARY, *, strict=False):
    rows = []
    seen = set()
    root = root.resolve()
    for path in sorted(root.glob("*/catalogue.json")):
        catalogue = read_json(path)
        title = path.parent.name
        family = catalogue.get("editorial_title", title_family(title))
        declared = set()
        for clip in catalogue["clips"]:
            name = clip["file"]
            file = path.parent / name
            asset_id = f"{title}/{name}"
            if (Path(name).name != name or file.suffix.lower() != ".mp4"
                    or not file.resolve().is_relative_to(root) or asset_id.casefold() in seen):
                raise ValueError(f"Invalid or duplicate excerpt identity: {asset_id}")
            seen.add(asset_id.casefold())
            declared.add(name)
            editorial = clip.get("editorial")
            if editorial is None:
                if strict:
                    raise ValueError(f"Missing editorial record: {asset_id}")
                editorial = {"action": "", "cues": [], "mood": [], "framing": "",
                             "fit": "", "evidence": {"status": "unresolved"}}
            status = editorial["evidence"]["status"]
            if status not in EVIDENCE or set(editorial["cues"]) - CUES.keys():
                raise ValueError(f"Invalid cues or evidence: {asset_id}")
            if strict and (not file.is_file() or clip.get("bytes", file.stat().st_size) != file.stat().st_size):
                raise ValueError(f"Missing or resized excerpt: {asset_id}")
            if not file.is_file():
                continue
            rows.append(dict(clip, id=asset_id, path=str(file), title=title, family=family,
                             editorial=editorial, reuse_basis=catalogue.get("posting_reuse_basis", "Unresolved")))
        if strict and declared != {p.name for p in path.parent.glob("*.mp4")}:
            raise ValueError(f"Catalogue and files differ: {path.parent}")
    if strict and not rows:
        raise ValueError(f"No catalogued excerpts in {root}")
    return rows


def normalized(value):
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def semantic_cues(text):
    query = " " + normalized(text) + " "
    return {tag for tag, phrases in CUES.items()
            if any(" " + normalized(term) + " " in query for term in (tag, *phrases))}


def prior_counts(maps):
    counts, seen = Counter(), set()
    for path in maps:
        for item in read_json(path):
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            for shot in item.get("inserts", []):
                title = shot.get("title") or shot.get("asset", {}).get("title")
                if title:
                    counts[title_family(title)] += 1
    return counts


def search(rows, query, *, cues=(), min_duration=0, title=None, used_titles=(), history=None, limit=12):
    requested = semantic_cues(query) | set(cues)
    words = set(normalized(query).split()) - {
        "a", "after", "an", "and", "at", "for", "his", "in", "of", "on", "or", "the", "to", "with"
    }
    history = history or {}
    used = Counter(title_family(name) for name in used_titles)
    ranked = []
    for row in rows:
        if row["duration"] < min_duration or (title and title.casefold() not in row["title"].casefold()):
            continue
        item = row["editorial"]
        overlap = requested.intersection(item["cues"])
        text = " ".join((item["action"], item["fit"], item["framing"], *item["mood"]))
        matched = words.intersection(normalized(text).split())
        if not (overlap or matched):
            continue
        evidence = item["evidence"]["status"]
        if evidence == "unresolved":
            continue
        family = row["family"]
        score = (-len(overlap), -len(matched), used[family], history.get(family, 0), row["id"])
        ranked.append((score, dict(row, matched_cues=sorted(overlap))))
    ranked.sort(key=lambda pair: pair[0])
    result = []
    for cue_match in (True, False):
        first, rest, families = [], [], set()
        for _, row in ranked:
            if bool(row["matched_cues"]) != cue_match:
                continue
            if row["family"] in families:
                rest.append(row)
            else:
                families.add(row["family"])
                first.append(row)
        result.extend(first + rest)
    return result[:limit]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=LIBRARY)
    commands = parser.add_subparsers(dest="command", required=True)
    find = commands.add_parser("search")
    find.add_argument("query")
    find.add_argument("--cue", action="append", choices=sorted(CUES), default=[])
    find.add_argument("--min-duration", type=float, default=0)
    find.add_argument("--title")
    find.add_argument("--used-title", action="append", default=[])
    find.add_argument("--shot-map", type=Path, action="append", default=[], help="Latest maps first")
    find.add_argument("--limit", type=int, default=12)
    find.add_argument("--json", action="store_true")
    commands.add_parser("validate")
    args = parser.parse_args()
    if args.command == "validate":
        rows = inventory(args.library, strict=True)
        print(json.dumps({"excerpts": len(rows), "packs": len({r["title"] for r in rows}),
                          "evidence": Counter(r["editorial"]["evidence"]["status"] for r in rows)}, indent=2))
        return
    if args.limit < 1 or args.min_duration < 0:
        parser.error("limit must be positive and minimum duration nonnegative")
    rows = search(inventory(args.library), args.query, cues=args.cue, min_duration=args.min_duration,
                  title=args.title, used_titles=args.used_title, history=prior_counts(args.shot_map),
                  limit=args.limit)
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=True))
        return
    for row in rows:
        info = row["editorial"]
        print(f"{row['title']} | {row['duration']:.2f}s | {info['action']}")
        print(f"  {info['fit']} [{', '.join(info['cues'])}]")
        print(f"  {info['framing']} | Mood: {', '.join(info['mood']) or 'Unspecified'}")
        print(f"  Evidence: {info['evidence']['status']} | Reuse: {row['reuse_basis']}")
        print(f"  {row['path']}")
    if not rows:
        print("No matching reviewed excerpts.")


if __name__ == "__main__":
    main()
