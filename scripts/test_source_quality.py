"""Offline format selection with the installed yt-dlp, not live download assertions."""
import copy
import unittest
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from yt_dlp import YoutubeDL
from source_quality import PRODUCTION_FORMAT, PRODUCTION_SORT, compatible_4k_available, quality_record
from build import validate_reference_edit
import prep


def video(id, width, height, codec, fps=25):
    return {'format_id': id, 'url': f'https://example.invalid/{id}.mp4', 'ext': 'mp4',
            'width': width, 'height': height, 'vcodec': codec, 'acodec': 'none', 'fps': fps}


def select(formats, return_info=False):
    fixture = {'id': 'offline-fixture', 'title': 'Offline selection',
               'formats': formats + [{'format_id': 'audio', 'url': 'https://example.invalid/audio.m4a',
                                      'ext': 'm4a', 'vcodec': 'none', 'acodec': 'mp4a.40.2'}]}
    with YoutubeDL({'quiet': True, 'no_warnings': True, 'cachedir': False,
                    'format': PRODUCTION_FORMAT, 'format_sort': PRODUCTION_SORT,
                    'format_sort_force': True, 'check_formats': False}) as ydl:
        result = ydl.process_ie_result(fixture, download=False)
    return result if return_info else result['requested_formats'][0]['format_id']


class SourceQualityTests(unittest.TestCase):
    def test_original_dialogue_beats_higher_bitrate_dub(self):
        audio = [dict(format_id='original', url='https://example.invalid/original.m4a', ext='m4a',
                      vcodec='none', acodec='mp4a.40.2', language='en', language_preference=10, abr=110),
                 dict(format_id='dubbed', url='https://example.invalid/dubbed.m4a', ext='m4a',
                      vcodec='none', acodec='mp4a.40.2', language='id', language_preference=-1, abr=145)]
        result = select([video('4k', 3840, 2160, 'vp9'), *audio], return_info=True)
        self.assertEqual(result['requested_formats'][1]['format_id'], 'original')
    def test_4k_vp9_beats_1080_h264_even_at_higher_fps(self):
        formats = [video('1080', 1920, 1080, 'avc1', 60), video('4k', 3840, 2160, 'vp9')]
        self.assertEqual(select(formats), '4k')

    def test_unsupported_av1_does_not_hide_supported_4k(self):
        self.assertEqual(select([video('av1', 3840, 2160, 'av01', 60),
                                 video('vp9', 3840, 2160, 'vp9')]), 'vp9')

    def test_portrait_native_4k_is_not_capped_at_2160_height(self):
        self.assertEqual(select([video('vertical', 2160, 3840, 'vp9'),
                                 video('small', 1080, 1920, 'avc1')]), 'vertical')

    def test_native_3840_wide_two_to_one_original_is_identified(self):
        self.assertTrue(compatible_4k_available({'formats': [video('wide', 3840, 1920, 'vp9')]}))
        self.assertEqual(quality_record(3840, 1920, True)['status'], 'native_4k_wide_aspect')
        self.assertEqual(select([video('wide', 3840, 1920, 'vp9'), video('small', 1920, 960, 'avc1')]), 'wide')

    def test_8k_is_not_selected(self):
        self.assertEqual(select([video('8k', 7680, 4320, 'vp9'),
                                 video('4k', 3840, 2160, 'vp9')]), '4k')

    def test_lower_resolution_is_identified(self):
        self.assertEqual(select([video('1080', 1920, 1080, 'avc1')]), '1080')
        self.assertFalse(quality_record(1920, 1080, False)['native_4k'])
        self.assertEqual(quality_record(2160, 3840, True)['status'], 'native_4k')

    def test_missing_or_unsupported_availability_stays_honest(self):
        self.assertFalse(compatible_4k_available({'formats': [video('av1', 3840, 2160, 'av01')]}))
        self.assertFalse(compatible_4k_available({'formats': [{'vcodec': 'vp9'}]}))
        self.assertIsNone(quality_record(720, 1280, None)['compatible_4k_available'])

    def test_existing_1080_master_cannot_silently_satisfy_4k(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp) / 'fixture'
            work.mkdir()
            (work / 'source.mp4').write_bytes(b'not-decoded')
            (work / 'source.json').write_text(json.dumps({'source_key': 'Youtube:fixture'}))
            mock_ydl = Mock()
            mock_ydl.__enter__ = Mock(return_value=mock_ydl)
            mock_ydl.__exit__ = Mock(return_value=False)
            mock_ydl.extract_info.return_value = {'id': 'fixture', 'extractor_key': 'Youtube',
                'formats': [video('4k', 3840, 2160, 'vp9')]}
            with patch.object(prep, 'WORK', Path(temp)), patch('yt_dlp.YoutubeDL', return_value=mock_ydl), \
                    patch.object(prep, 'probe', return_value=SimpleNamespace(width=1920, height=1080)):
                with self.assertRaisesRegex(ValueError, 'new --work-id'):
                    prep.fetch('https://example.invalid/watch?v=fixture')
            mock_ydl.download.assert_not_called()
            self.assertEqual((work / 'source.mp4').read_bytes(), b'not-decoded')

    def test_picture_bounds_and_legacy_layout(self):
        validate_reference_edit({'profile': 'kinetic', 'bandHeight': 608}, 1)
        edit = {'profile': 'kinetic', 'frame': {'x': 50, 'y': 470, 'width': 980, 'height': 980, 'radius': 48}}
        validate_reference_edit(edit, 1)
        for patch in ({'width': 1100}, {'radius': 500}, {'y': float('nan')}, {'height': 0}):
            bad = copy.deepcopy(edit)
            bad['frame'].update(patch)
            with self.assertRaises(ValueError):
                validate_reference_edit(bad, 1)


if __name__ == '__main__':
    unittest.main()
