"""Source-led motion contracts: timing, protected regions and safe delivery."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import motion_edit as motion


class MotionChecks(unittest.TestCase):
    def setUp(self):
        self.temp_root = motion.ROOT / '.runtime/tmp'
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.temp_root)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source.mp4'
        self.source.write_bytes(b'unit fixture; not media')
        self.spec = {'id': 'unit-fixture', 'source': {'path': str(self.source), 'sha256': motion.digest(self.source),
            'rate': '25/1', 'fps': 25, 'frames': 100, 'duration': 4, 'width': 1080, 'height': 1920, 'has_audio': False},
            'scenes': [{'kind': 'speaker', 'start': 0, 'end': 4}], 'assets': {}, 'captionLayers': [],
            'reuseBasis': 'Software unit fixture', 'posting': {}}

    def tearDown(self):
        assert self.root.resolve().is_relative_to(self.temp_root.resolve())
        self.temp.cleanup()

    def test_native_fractional_rate_and_complete_coverage(self):
        self.spec['source'].update(rate='30000/1001', fps=30000/1001, frames=120, duration=4.004)
        self.spec['scenes'][0]['end'] = 4.004
        result = motion.validate(self.spec, require_ready=True)
        self.assertEqual(result['frames'], 120)

    def test_gaps_overlaps_empty_cues_and_invalid_numbers(self):
        for second_start in (1.8, 2.2):
            edit = copy.deepcopy(self.spec)
            edit['scenes'] = [{'kind': 'speaker', 'start': 0, 'end': 2}, {'kind': 'speaker', 'start': second_start, 'end': 4}]
            with self.assertRaisesRegex(ValueError, 'gaps or overlaps'): motion.validate(edit)
        for value in (float('nan'), float('inf'), -1):
            edit = copy.deepcopy(self.spec); edit['scenes'][0]['end'] = value
            with self.assertRaises(ValueError): motion.validate(edit)
        self.spec['scenes'][0]['end'] = 0
        with self.assertRaises(ValueError): motion.validate(self.spec)

    def test_graphics_require_real_assets_and_permission(self):
        self.spec['scenes'] = [{'kind': 'illustration', 'start': 0, 'end': 4, 'title': 'An idea', 'asset': 'chip'}]
        with self.assertRaisesRegex(ValueError, 'Unknown scene asset'): motion.validate(self.spec)
        file = self.root / 'chip.svg'; file.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.spec['assets']['chip'] = {'path': str(file)}
        with self.assertRaisesRegex(ValueError, 'reuse basis'): motion.validate(self.spec, require_ready=True)
        self.spec['assets']['chip']['reuseBasis'] = 'Original test drawing'
        motion.validate(self.spec, require_ready=True)
        file.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'): motion.validate(self.spec)

    def test_caption_bounds_and_face_regions(self):
        layer = {'t': 0, 'dur': 1, 'text': 'A thought', 'wordTimes': [0, .4], 'font': 'inter',
                 'x': 90, 'y': 1400, 'width': 900, 'size': 72}
        self.spec['captionLayers'] = [layer]
        motion.validate(self.spec)
        self.spec['protectedRegions'] = [{'start': 0, 'end': 1, 'x': 400, 'y': 1360, 'width': 220, 'height': 160}]
        with self.assertRaisesRegex(ValueError, 'protected'): motion.validate(self.spec)
        self.spec['protectedRegions'][0]['start'] = 2
        self.spec['protectedRegions'][0]['end'] = 3
        motion.validate(self.spec)
        layer['y'] = 1490
        with self.assertRaisesRegex(ValueError, 'phone-safe'): motion.validate(self.spec)

    def test_badge_onsets_and_comparison_content(self):
        scene = {'kind': 'badges', 'start': 0, 'end': 4, 'badges': [{'text': 'Mentor', 'at': .5, 'x': 80, 'y': 1000, 'width': 350}]}
        self.spec['scenes'] = [scene]
        motion.validate(self.spec)
        scene['badges'][0]['at'] = 4
        with self.assertRaises(ValueError): motion.validate(self.spec)
        self.spec['scenes'] = [{'kind': 'comparison', 'start': 0, 'end': 4, 'title': 'Choose', 'left': {'title': 'Before'}}]
        with self.assertRaisesRegex(ValueError, 'Comparison'): motion.validate(self.spec)

    def test_audio_changes_are_never_silently_ignored(self):
        self.spec['music'] = {'path': 'requested.mp3'}
        with self.assertRaisesRegex(ValueError, 'original dialogue'): motion.validate(self.spec)

    def test_preview_preserves_full_render_and_unknown_music_is_not_final(self):
        motion.record_render(self.root,self.root/'full-qa',{'preview':False,'sha256':'full'})
        motion.record_render(self.root,self.root/'preview-qa',{'preview':True,'sha256':'preview'})
        self.assertEqual(motion.read(self.root/'last-render.json')['sha256'],'full')
        self.assertEqual(motion.read(self.root/'last-preview.json')['sha256'],'preview')
        self.spec['source']['has_audio']=True
        project=self.root/'project.json';motion.save(project,self.spec)
        with self.assertRaisesRegex(ValueError,'music-free'):motion.deliver(project)
        self.spec['sourceMusic']='unknown'
        with self.assertRaisesRegex(ValueError,'sourceMusic'):motion.validate(self.spec)

    def test_picture_clock_checks_duration_start_and_fractional_rate(self):
        signature={'nb_read_packets':'102','r_frame_rate':'30000/1001','duration':'3.4034','start_time':'0.000000'}
        motion.validate_picture_clock(signature,102,30000/1001)
        for key,value in [('nb_read_packets','101'),('r_frame_rate','30/1'),('duration','3.4'),('start_time','0.033367')]:
            with self.assertRaisesRegex(RuntimeError,'timestamps'):
                motion.validate_picture_clock({**signature,key:value},102,30000/1001)

    def test_audio_signature_ignores_container_labels_but_keeps_packets(self):
        from types import SimpleNamespace
        data={'streams':[{'codec_name':'aac','time_base':'1/48000','sample_rate':'48000','channels':2,
                          'tags':{'language':'eng','handler_name':'Google source handler'}}],
              'packets':[{'pts':0,'dts':0,'duration':1024,'size':'100','data_hash':'SHA256:owned'}]}
        def signature(value):
            with patch.object(motion.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps(value))):
                return motion.audio_packets(self.root/'fixture.mp4')
        before=signature(data)
        data['streams'][0]['tags']={'language':'und','handler_name':'SoundHandler'}
        self.assertEqual(before,signature(data))
        data['packets'][0]['pts']=1
        self.assertNotEqual(before,signature(data))

    def test_delivery_requires_matching_real_review_and_preserves_draft(self):
        self.spec['posting']={'title':'Owned fixture','description':'Software delivery-copy test only.'}
        project = self.root / 'project.json'; motion.save(project, self.spec)
        draft = self.root / 'draft.mp4'; draft.write_bytes(b'unit rendered picture/audio')
        receipt = {'file': str(draft), 'sha256': motion.digest(draft), 'project_sha256': motion.digest(project), 'passed': True}
        motion.save(self.root / 'last-render.json', receipt)
        review = {'render_sha256': receipt['sha256'], 'reviewed_by': 'unit test', 'reviewed_at': 'test',
                  'coverage': 'Synthetic software fixture, no human playback claim', 'issues': [],
                  'visual_complete': True, 'caption_timing_checked': True, 'branding_checked': True,
                  'continuous_playback_with_sound': False}
        motion.save(self.root / 'review.json', review)
        with self.assertRaisesRegex(ValueError, 'coverage'): motion.deliver(project)
        review['continuous_playback_with_sound'] = True
        motion.save(self.root / 'review.json', review)
        # This tests copying only. The fake fixture never goes to real channel Exports.
        with patch.object(motion, 'HOME', self.root / 'isolated-delivery'):
            exported = motion.deliver(project)
            self.assertEqual(exported.read_bytes(), draft.read_bytes())
            self.assertTrue(draft.exists())
            with self.assertRaises(FileExistsError): motion.deliver(project)
        for flag in ('preview', 'synthetic'):
            altered = dict(receipt); altered[flag] = True
            motion.save(self.root / 'last-render.json', altered)
            with self.assertRaisesRegex(ValueError, 'synthetic'): motion.deliver(project)
        altered = dict(receipt); altered['project_sha256'] = 'stale'
        motion.save(self.root / 'last-render.json', altered)
        with self.assertRaisesRegex(ValueError, 'stale'): motion.deliver(project)


if __name__ == '__main__': unittest.main()
