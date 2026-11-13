"""Regression checks for cue validation and frame-to-sample alignment."""
import unittest
from pathlib import Path
from unittest.mock import patch

import transition_sounds as transitions


class TransitionChecks(unittest.TestCase):
    def test_rejects_invalid_or_stacked_cues(self):
        frame = {"frame": {"x": 50, "y": 470, "width": 980, "height": 980}}
        cue = {"frame": 21, "preset": "inversion-flicker"}
        fps = 30000 / 1001
        self.assertEqual(transitions.resolve_cues([], 136, 25, None), {})
        self.assertEqual(transitions.resolve_cues([cue], 163, fps, frame), {})
        for cues in (None, [None], [{**cue, "frame": True}], [{**cue, "frame": 163}],
                     [{**cue, "preset": "typo"}], [{**cue, "soundId": "../stock"}],
                     [cue, {**cue, "frame": 50}]):
            with self.subTest(cues=cues), self.assertRaises(ValueError):
                transitions.resolve_cues(cues, 163, fps, frame)
        with self.assertRaisesRegex(ValueError, "explicit referenceEdit.frame"):
            transitions.resolve_cues([cue], 163, fps, None)
        with patch.object(transitions, "LIBRARY", Path("missing-sfx-test")), \
                self.assertRaisesRegex(ValueError, "Missing or mismatched"):
            transitions.resolve_cues([{**cue, "soundId": "glitch-static"}], 163, fps, frame)

    def test_aligns_sweep_in_samples_after_intro_at_fractional_rate(self):
        fps = 30000 / 1001
        cue = {"frame": 45, "preset": "blu-ray-scanning", "soundId": "sweep"}
        asset = {"file": Path("sweep.wav"), "startMs": 180, "accentMs": 375,
                 "endMs": 560, "gainDb": -20}
        with patch.object(transitions, "require_guard"), patch.object(transitions, "probe") as probe, \
                patch.object(transitions, "run") as run:
            probe.return_value.has_audio = True
            transitions.mix_transition_sounds(Path("in.mp4"), Path("out.mp4"), [cue], {"sweep": asset},
                                              fps, 180, intro_frames=30, source_gain_db=-4)
        command = run.call_args.args[0]
        graph = command[command.index("-filter_complex") + 1]
        self.assertIn("adelay=110760S:all=1", graph)
        self.assertIn("volume=-4dB[dialogue]", graph)
        self.assertIn("duration=first:normalize=0", graph)
        self.assertIn("atrim=end_sample=288288", graph)
        self.assertEqual(command[command.index("-c:v") + 1], "copy")

    def test_separate_dialogue_bypasses_renderer_audio_and_offsets_intro(self):
        with patch.object(transitions, "require_guard"), patch.object(transitions, "probe") as probe, \
                patch.object(transitions, "run") as run:
            probe.return_value.has_audio = True
            transitions.mix_transition_sounds(Path("picture.mp4"), Path("out.mp4"), [], {}, 25, 125,
                                              intro_frames=25, dialogue=Path("dialogue.mp4"),
                                              intro_audio=Path("narration.wav"))
        probe.assert_called_once_with(Path("dialogue.mp4"))
        command = run.call_args.args[0]
        graph = command[command.index("-filter_complex") + 1]
        self.assertNotIn("[0:a:0]", graph)
        self.assertIn("[2:a:0]aresample=48000", graph)
        self.assertIn("apad=whole_len=48000,atrim=end_sample=48000[intro]", graph)
        self.assertIn("[intro][body]concat=n=2:v=0:a=1", graph)


if __name__ == "__main__":
    unittest.main()
