"""LAYER: Engineer. THE BIG PICTURE: prove admission decisions before expensive generation.
THE FLOW: offline storyboard/profile cases -> isolated review fallback -> no model/network calls.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import ai_video
import watch_review


class VideoDecisions(unittest.TestCase):
    def spec(self, backend: str = 'illustrated', seconds: float = 45) -> dict:
        return {'id': 'test', 'backend': backend, 'scenes': [{'heading': 'Test', 'duration': seconds}]}

    def test_illustrated_stays_one_batch(self):
        result = ai_video.plan(self.spec(), {'illustrated': {'certified': True, 'seconds_per_output_second': 3}})
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['render_strategy'], 'single batch')

    def test_no_invented_performance_without_measurement(self):
        result = ai_video.plan(self.spec(), {})
        self.assertEqual(result['status'], 'needs_benchmark')
        self.assertIsNone(result['estimated_seconds'])

    def test_uncertified_diffusion_is_not_made_feasible_by_splitting(self):
        self.assertEqual(ai_video.plan(self.spec('local-diffusion'), {})['status'], 'needs_benchmark')

    def test_certified_short_request_does_not_split(self):
        profile = {'local-diffusion': {'certified': True, 'max_seconds': 6, 'seconds_per_output_second': 100}}
        result = ai_video.plan(self.spec('local-diffusion', 5), profile)
        self.assertEqual(result['generation_strategy'], 'single batch')
        self.assertEqual(result['segment_count'], 1)

    def test_only_profile_exceeding_request_segments(self):
        profile = {'local-diffusion': {'certified': True, 'max_seconds': 6, 'seconds_per_output_second': 100}}
        self.assertEqual(ai_video.plan(self.spec('local-diffusion', 13), profile)['segment_count'], 3)

    def test_authored_cuts_are_not_resource_splits(self):
        profile = {'local-diffusion': {'certified': True, 'max_seconds': 6, 'seconds_per_output_second': 100}}
        spec = self.spec('local-diffusion', 4)
        spec['scenes'].append({'heading': 'Second shot', 'duration': 4})
        result = ai_video.plan(spec, profile)
        self.assertEqual(result['generation_strategy'], 'authored scenes')
        self.assertEqual(result['segments_per_scene'], [1, 1])

    def test_24_hour_forecast_stops_before_queueing(self):
        result = ai_video.plan(self.spec(), {'illustrated': {'certified': True, 'seconds_per_output_second': 2000}})
        self.assertEqual(result['status'], 'needs_decision')
        self.assertFalse(result['paid_cloud_allowed'])

    def test_storyboard_rejects_invalid_timing(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'story.json'
            for duration in (True, 0, -1, float('nan'), float('inf')):
                source.write_text(json.dumps(self.spec(seconds=duration)))
                with self.assertRaisesRegex(ValueError, 'duration'):
                    ai_video.read_spec(source)

    def test_output_id_cannot_escape_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'story.json'
            source.write_text(json.dumps({**self.spec(), 'id': '../escape'}))
            with self.assertRaisesRegex(ValueError, 'id'):
                ai_video.read_spec(source)

    def test_review_falls_back_once_and_labels_it(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'watch.py').touch()
            config = SimpleNamespace(CONFIG_DIR=None, CONFIG_FILE=None,
                read_env_file=lambda: {'WATCH_FREE_TIER_CONFIRMED': '1'}, load_gemini_key=lambda: 'test-secret')
            calls = []
            def invoke():
                engine = sys.argv[sys.argv.index('--engine') + 1]
                calls.append(engine)
                if engine == 'gemini':
                    raise OSError('network unavailable')
                return 0
            loader = SimpleNamespace(exec_module=lambda module: setattr(module, 'main', invoke))
            module_spec = SimpleNamespace(loader=loader)
            with patch.object(watch_review, 'HELPER', root), patch.object(watch_review, 'CONFIG', root), \
                 patch.dict(sys.modules, {'config': config}), patch.object(watch_review, 'bound_helper_processes'), \
                 patch.object(watch_review.importlib.util, 'spec_from_file_location', return_value=module_spec), \
                 patch.object(watch_review.importlib.util, 'module_from_spec', return_value=SimpleNamespace()), \
                 patch.object(sys, 'argv', ['watch_review.py', 'sample.mp4', '--engine', 'auto']), \
                 contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(watch_review.main(), 0)
            self.assertEqual(calls, ['gemini', 'local'])
            result = json.loads((root / 'last-review.json').read_text())
            self.assertTrue(result['local_preparation_only'])
            self.assertFalse(result['gemini_succeeded'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
