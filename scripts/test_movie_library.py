"""Regression checks for cue-first cross-title cutaway search."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from movie_library import inventory, prior_counts, search, title_family


def clip(title, name, cues, *, action="A person pauses.", status="source_frame", duration=3):
    return {
        "title": title, "family": title_family(title), "id": f"{title}/{name}", "duration": duration,
        "editorial": {"action": action, "fit": "", "framing": "", "mood": [],
                      "cues": cues, "evidence": {"status": status}},
    }


class MovieLibraryTest(unittest.TestCase):
    def test_semantic_matches_span_families_before_repeats(self):
        rows = [clip("Peaky Blinders - Tommy Shelby S04", "1", ["recovery", "setback"]),
                clip("Peaky Blinders - Tommy Shelby S06", "2", ["recovery", "setback"]),
                clip("Daredevil", "3", ["recovery"]),
                clip("Fight Club", "4", [], action="Someone stops after failure."),
                clip("Jon Snow", "5", ["recovery"], status="unresolved")]
        result = search(rows, "trying again after failure")
        self.assertEqual([row["id"].rsplit("/", 1)[-1] for row in result], ["1", "3", "2", "4"])

    def test_usage_breaks_ties_without_overriding_cue_fit(self):
        rows = [clip("Blade Runner 2049", "1", ["help", "trust"]),
                clip("Fight Club", "2", ["help", "trust"]),
                clip("Avengers Endgame", "3", ["help"])]
        result = search(rows, "asking for help and trust", used_titles=["Blade Runner 2049"])
        self.assertEqual([row["title"] for row in result],
                         ["Fight Club", "Blade Runner 2049", "Avengers Endgame"])
        self.assertEqual(len(search(rows, "help", min_duration=4)), 0)

    def test_only_latest_shot_map_for_each_edit_is_counted(self):
        with TemporaryDirectory() as folder:
            latest, earlier = Path(folder) / "latest.json", Path(folder) / "earlier.json"
            latest.write_text(json.dumps([{"id": "clip", "inserts": [{"title": "Blade Runner 2049"}]}]))
            earlier.write_text(json.dumps([{"id": "clip", "inserts": [{"title": "Iron Man"}]},
                                           {"id": "other", "inserts": [
                                               {"title": "Peaky Blinders - Tommy Shelby S06"}]}]))
            self.assertEqual(prior_counts([latest, earlier]), {"Blade Runner 2049": 1, "Peaky Blinders": 1})

    def test_strict_inventory_requires_editorial_record_and_existing_media(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            title = root / "Example"
            title.mkdir()
            path = title / "catalogue.json"
            record = {"file": "shot.mp4", "duration": 2, "bytes": 3}
            (title / "shot.mp4").write_bytes(b"abc")
            path.write_text(json.dumps({"clips": [record]}))
            with self.assertRaisesRegex(ValueError, "Missing editorial record"):
                inventory(root, strict=True)
            record["editorial"] = clip("Example", "shot", ["craft"])["editorial"]
            path.write_text(json.dumps({"clips": [record]}))
            self.assertEqual(inventory(root, strict=True)[0]["id"], "Example/shot.mp4")
            (title / "shot.mp4").unlink()
            with self.assertRaisesRegex(ValueError, "Missing or resized"):
                inventory(root, strict=True)


if __name__ == "__main__":
    unittest.main()
