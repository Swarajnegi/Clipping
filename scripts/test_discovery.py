"""Offline behavioural checks for source discovery and paired-export audio routing."""
from __future__ import annotations

import unittest
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import build
import discover
import prep


class DiscoveryChecks(unittest.TestCase):
    def factory(self, responses):
        @contextmanager
        def create(options):
            self.assertTrue(options["skip_download"])
            self.assertFalse(options["cachedir"])
            def extract(url, download):
                self.assertFalse(download)
                result = responses[url]
                if isinstance(result, Exception):
                    raise result
                return result
            yield SimpleNamespace(extract_info=extract)
        return create

    def test_aliases_deduplicate_but_platforms_do_not(self):
        shared = {"id": "same", "extractor_key": "Youtube", "title": "episode"}
        sources = ["https://youtu.be/same", "https://youtube.com/watch?v=same", "https://rumble.com/vsame.html"]
        data = discover.collect(sources, 2, self.factory({sources[0]: shared, sources[1]: shared,
            sources[2]: {**shared, "extractor_key": "Rumble"}}))
        self.assertEqual(len(data["episodes"]), 2)
        self.assertEqual(len(data["episodes"][0]["found_via"]), 2)

    def test_no_captions_is_distinct_from_access_denied(self):
        good, bad = "https://example.org/ok", "https://example.org/blocked"
        data = discover.collect([good, bad], 2, self.factory({good: {"id": "ok", "extractor_key": "Youtube"},
                                                        bad: RuntimeError("HTTP Error 403: Forbidden")}))
        self.assertEqual(data["episodes"][0]["captions"]["status"], "none_reported")
        self.assertEqual(data["listings"][1]["status"], "blocked")
        self.assertEqual(data["listings"][1]["errors"][0]["captions_status"], "not_checked")

    def test_listing_bound_is_reported_and_only_limit_entries_hydrated(self):
        channel, one, two = "https://example.org/channel", "https://example.org/one", "https://example.org/two"
        responses = {channel: {"entries": [{"_type": "url", "url": one}, {"_type": "url", "url": two}]},
                     one: {"id": "one", "extractor_key": "Youtube", "subtitles": {"en": []}}}
        data = discover.collect([channel], 1, self.factory(responses))
        self.assertEqual(data["listings"][0]["status"], "limited")
        self.assertEqual(len(data["episodes"]), 1)
        self.assertEqual(data["episodes"][0]["captions"]["manual_languages"], ["en"])

    def test_listing_error_preserves_successful_entries(self):
        channel = "https://example.org/channel"
        def entries():
            yield {"id": "one", "extractor_key": "Youtube"}
            raise RuntimeError("HTTP 429")
        data = discover.collect([channel], 5, self.factory({channel: {"entries": entries()}}))
        self.assertEqual(len(data["episodes"]), 1)
        self.assertEqual(data["listings"][0]["status"], "partial")

    def test_music_mix_copies_picture_and_keeps_original_audio(self):
        with patch.object(build, "probe", return_value=SimpleNamespace(duration=3.0, has_audio=True)), \
             patch.object(build, "run") as run:
            build.mix_companion(Path("speech.mp4"), {"file": "bed.wav", "db": -12}, Path("mixed.mp4"))
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        filters = command[command.index("-filter_complex") + 1]
        self.assertIn("[0:a][bed]amix", filters)
        self.assertIn("normalize=0", filters)
        self.assertIn("volume=-12.0dB", filters)

    def test_pair_requires_speech_stream(self):
        with patch.object(build, "probe", return_value=SimpleNamespace(duration=3.0, has_audio=False)):
            with self.assertRaisesRegex(ValueError, "audio stream"):
                build.mix_companion(Path("silent.mp4"), {"file": "bed.wav"}, Path("mixed.mp4"))

    def test_local_staging_collision_does_not_reuse_transcript(self):
        with tempfile.TemporaryDirectory(dir=discover.ROOT / ".runtime") as tmp:
            root=Path(tmp)
            first,second=root / "first.mp4",root / "second.mp4"
            first.touch()
            second.touch()
            work=root / "shared"
            work.mkdir()
            (work / "source.json").write_text(json.dumps({"path":str(first)}))
            with patch.object(prep,"WORK",root):
                with self.assertRaisesRegex(ValueError,"another local file"):
                    prep.fetch(str(second),"shared")

    def test_unsafe_staging_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"safe"):
            prep.fetch("unused", "../outside")

    def test_reference_emphasis_obeys_assembled_timeline(self):
        build.validate_reference_edit({"profile":"kinetic","emphasis":[{"t":1,"dur":1,"text":"100%"}]},2)
        with self.assertRaisesRegex(ValueError,"timeline"):
            build.validate_reference_edit({"profile":"kinetic","emphasis":[{"t":1,"dur":2,"text":"100%"}]},2)

    def test_reference_band_cannot_leave_canvas(self):
        with self.assertRaisesRegex(ValueError,"canvas"):
            build.validate_reference_edit({"profile":"restrained","bandHeight":2500},2)

    def test_pair_accepts_mux_rounding_but_rejects_a_lost_frame(self):
        first={"sha256":"same","nb_read_packets":"727","r_frame_rate":"30/1","duration":"24.233333"}
        second={**first,"duration":"24.233000"}
        self.assertTrue(build.matching_pictures(first,second))
        self.assertFalse(build.matching_pictures(first,{**second,"nb_read_packets":"726"}))
        self.assertFalse(build.matching_pictures(first,{**second,"sha256":"different"}))
        self.assertFalse(build.matching_pictures(first,{**second,"duration":"24.2"}))

    def test_source_level_adjustment_cannot_amplify_or_use_nan(self):
        for gain in (3,float('nan')):
            with self.assertRaisesRegex(ValueError,'sourceAudioDb'):
                build.adjust_source_audio(Path('source.mp4'),gain,Path('output.mp4'))

    def test_caption_pages_cannot_bleed_across_a_source_cut(self):
        words=[{'w':' Question?','s':0,'e':1,'p':1},
               {'w':' Answer.','s':5,'e':6,'p':1}]
        captions=build.rebase_words(words,[(0,1.1,0),(5,6.1,1.1)])
        self.assertTrue(captions[0]['pageBreakAfter'])
        self.assertEqual(captions[1]['startMs'],1100)

    def test_editorial_sentence_break_survives_timestamp_rebasing(self):
        words=[{'w':' First.','s':3,'e':3.5,'p':1,'pageBreakAfter':True},
               {'w':' Next','s':3.6,'e':4,'p':1}]
        captions=build.rebase_words(words,[(3,4.1,0)])
        self.assertTrue(captions[0]['pageBreakAfter'])
        self.assertEqual(captions[0]['startMs'],0)

    def test_layered_caption_words_are_timed_inside_their_layer(self):
        layer={'t':0.5,'dur':1,'text':'two words','x':50,'y':950,'size':70,'wordTimes':[0.5,0.8]}
        build.validate_reference_edit({'profile':'kinetic','layers':[layer]},2)
        for times in ([0.5,1.6],[0.8,0.5],[0.5]):
            with self.assertRaisesRegex(ValueError,'word times'):
                build.validate_reference_edit({'profile':'kinetic','layers':[{**layer,'wordTimes':times}]},2)

    def test_layered_caption_cannot_escape_timeline_or_canvas(self):
        layer={'t':0.5,'dur':1,'text':'caption','x':50,'y':950,'size':70}
        with self.assertRaisesRegex(ValueError,'timeline'):
            build.validate_reference_edit({'profile':'kinetic','layers':[{**layer,'dur':3}]},2)
        with self.assertRaisesRegex(ValueError,'canvas'):
            build.validate_reference_edit({'profile':'kinetic','layers':[{**layer,'x':1300}]},2)

    def test_layered_only_requires_authored_layers_and_a_boolean(self):
        with self.assertRaisesRegex(ValueError,'require authored'):
            build.validate_reference_edit({'profile':'kinetic','layeredOnly':True},2)
        with self.assertRaisesRegex(ValueError,'boolean'):
            build.validate_reference_edit({'profile':'kinetic','layeredOnly':'true'},2)
        layer={'t':0,'dur':1,'text':'complete caption','x':50,'y':950,'size':70,'wordTimes':[0,0.5]}
        build.validate_reference_edit({'profile':'kinetic','layeredOnly':True,'layers':[layer]},2)
        build.validate_reference_edit({'profile':'kinetic','layeredOnly':False},2)


if __name__ == "__main__":
    unittest.main()
