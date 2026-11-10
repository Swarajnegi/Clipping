"""Offline regression checks for the recovered pipeline's timing and resource contracts."""
from __future__ import annotations

import json
import base64
import hashlib
import io
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import build
import common
import prep
import install_locked_packages as locked
import watch_review


class PipelineChecks(unittest.TestCase):
    def test_cloud_helpers_frame_extraction_uses_guard_and_thread_bounds(self):
        runtime = SimpleNamespace()
        frames = SimpleNamespace()
        with patch.dict('sys.modules', {'runtime': runtime, 'frames': frames}), \
                patch.object(common, 'require_guard') as guard, patch.object(watch_review.subprocess, 'run') as run:
            watch_review.bound_helper_processes()
            frames.subprocess.run(['ffmpeg', '-i', 'input.mp4', '-frames:v', '1', 'out.jpg'])
        guard.assert_called_once_with()
        command = run.call_args.args[0]
        self.assertEqual(command[0], common.FFMPEG)
        self.assertEqual(command[-3:], ['-threads', '2', 'out.jpg'])
        self.assertIn('-filter_complex_threads', command)

    def test_cloud_helpers_ffmpeg_help_probe_is_not_rewritten(self):
        runtime, frames = SimpleNamespace(), SimpleNamespace()
        with patch.dict('sys.modules', {'runtime': runtime, 'frames': frames}), \
                patch.object(common, 'require_guard'), patch.object(watch_review.subprocess, 'run') as run:
            watch_review.bound_helper_processes()
            frames.subprocess.run(['ffmpeg', '-hide_banner', '-h', 'full'])
        self.assertEqual(run.call_args.args[0], ['ffmpeg', '-hide_banner', '-h', 'full'])

    def test_guard_rejects_uncontained_model_work(self):
        with patch.dict("os.environ", {}, clear=True), self.assertRaisesRegex(RuntimeError, "resource|run_guarded"):
            common.require_guard()

    def test_cuda_failure_does_not_fall_back(self):
        factory = Mock(side_effect=RuntimeError("missing CUDA library"))
        with patch.object(prep, "require_guard"), patch.object(common, "wait_headroom"), patch.object(prep, "_cuda_dll_dirs", return_value=[]), \
                patch.dict("sys.modules", {"faster_whisper": SimpleNamespace(WhisperModel=factory)}):
            with self.assertRaisesRegex(RuntimeError, "no CPU fallback"):
                prep._load_whisper("small")
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(factory.call_args.kwargs["device"], "cuda")
        self.assertEqual(factory.call_args.kwargs["cpu_threads"], 2)

    def test_cpu_admission_cannot_authorize_gpu_model_work(self):
        with patch.dict("os.environ", {"CLIPPING_GUARD_JOB": "Local\\ViralShorts-test", "CLIPPING_GUARD_WORKLOAD": "Cpu"}):
            with self.assertRaisesRegex(RuntimeError, "requires -Workload Gpu"):
                common.require_guard(gpu=True)

    def test_exact_nominal_rate(self):
        info = {"streams": [{"codec_type": "video", "width": 1920, "height": 1080,
                "r_frame_rate": "30000/1001", "avg_frame_rate": "7016500/234117"}], "format": {"duration": "4"}}
        with patch.object(common.subprocess, "run", return_value=SimpleNamespace(stdout=json.dumps(info))):
            media = common.probe(Path("sample.mp4"))
        self.assertEqual(media.rate, "30000/1001")
        self.assertEqual(media.fps, 30000 / 1001)

    def test_unknown_frame_rate_is_not_invented(self):
        info = {"streams": [{"codec_type": "video", "width": 100, "height": 100,
                "r_frame_rate": "0/0", "avg_frame_rate": "0/0"}], "format": {"duration": "4"}}
        with patch.object(common.subprocess, "run", return_value=SimpleNamespace(stdout=json.dumps(info))):
            with self.assertRaisesRegex(ValueError, "frame rate"):
                common.probe(Path("sample.mp4"))

    def test_missing_frame_rate_is_not_invented(self):
        info = {"streams": [{"codec_type": "video", "width": 100, "height": 100}], "format": {"duration": "4"}}
        with patch.object(common.subprocess, "run", return_value=SimpleNamespace(stdout=json.dumps(info))):
            with self.assertRaisesRegex(ValueError, "frame rate"):
                common.probe(Path("sample.mp4"))

    def test_nested_stage_rechecks_capacity_and_preserves_deferral(self):
        with patch.object(common, 'require_guard') as guard, \
                patch.object(common.subprocess, 'run', return_value=SimpleNamespace(returncode=75)) as run:
            with self.assertRaises(SystemExit) as result:
                common.wait_headroom(gpu=True)
        self.assertEqual(result.exception.code, 75)
        guard.assert_called_once_with(gpu=True)
        self.assertIn('Wait', run.call_args.args[0])

    def test_each_decoder_and_encoder_is_bounded(self):
        cmd = common.ffmpeg_command([common.FFMPEG, "-i", "a.mp4", "-i", "b.mp4", *common.encoder(), "out.mp4"])
        for i, arg in enumerate(cmd):
            if arg in ("-i", "-c:v"):
                self.assertEqual(cmd[i - 2:i], ["-threads", "2"])
        self.assertIn("-filter_complex_threads", cmd)
        self.assertEqual(cmd[-3:], ["-threads", "2", "out.mp4"])
        self.assertIn("h264_nvenc", cmd)
        self.assertNotIn("libx264", cmd)

    def test_compilation_captions_follow_piece_order_and_repeats(self):
        words = [{"w": "early", "s": 1, "e": 2}, {"w": "peak", "s": 10, "e": 11}]
        captions = build.rebase_words(words, [(10, 12, 0), (1, 3, 2), (10, 12, 4)])
        self.assertEqual([x["text"] for x in captions], ["peak", "early", "peak"])
        self.assertEqual([x["startMs"] for x in captions], [0, 2000, 4000])

    def test_trim_is_opt_in(self):
        clip = {"start": 0, "end": 4, "type": "talk"}
        transcript = [{"words": [{"s": 0, "e": 0.5}, {"s": 3, "e": 4}]}]
        self.assertEqual(build.plan_pieces(clip, transcript), [(0, 4)])
        self.assertEqual(len(build.plan_pieces({**clip, "trimSilence": True}, transcript)), 2)

    def test_silent_compilation_has_no_audio_input_reference(self):
        with tempfile.TemporaryDirectory(prefix="clipping-check-") as folder, \
                patch.object(build, "probe", return_value=SimpleNamespace(has_audio=False)), patch.object(build, "run") as run:
            spans = build.assemble(Path("silent.mp4"), [(0, 1), (2, 3)], Path(folder) / "joined.mp4", "30000/1001")
        command = run.call_args.args[0]
        graph = command[command.index("-filter_complex") + 1]
        self.assertNotIn(":a:0", graph)
        self.assertIn("a=0", graph)
        self.assertEqual(spans, [(0, 1, 0.0), (2, 3, 1.0)])
        self.assertIn("30000/1001", command)

    def check_locked_archive(self, *, traversal: bool = False, bad_integrity: bool = False):
        with tempfile.TemporaryDirectory(prefix='clipping-lock-check-') as folder:
            root = Path(folder) / 'project'
            root.mkdir()
            (root / '.runtime/pipeline-restore').mkdir(parents=True)
            archive = Path(folder) / 'pkg.tgz'
            with tarfile.open(archive, 'w:gz') as out:
                data = json.dumps({'name': 'test-pkg', 'version': '1.0.0'}).encode()
                member = tarfile.TarInfo('package/package.json'); member.size = len(data)
                out.addfile(member, io.BytesIO(data))
                if traversal:
                    member = tarfile.TarInfo('package/../../../outside.txt'); member.size = 3
                    out.addfile(member, io.BytesIO(b'bad'))
            integrity = base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()
            if bad_integrity:
                integrity = base64.b64encode(b'x' * 64).decode()
            (root / 'package.json').write_text(json.dumps({'dependencies': {'test-pkg': '1.0.0'}}))
            lock = {'packages': {'': {'dependencies': {'test-pkg': '1.0.0'}},
                'node_modules/test-pkg': {'version': '1.0.0', 'resolved': 'https://registry.npmjs.org/test-pkg/-/test-pkg.tgz',
                                          'integrity': 'sha512-' + integrity}}}
            (root / 'package-lock.json').write_text(json.dumps(lock))
            with patch.object(locked, 'ROOT', root), patch.object(locked, 'require_guard'), \
                    patch.object(locked, 'download', return_value=archive), patch.object(locked.time, 'sleep'), \
                    patch.object(locked.subprocess, 'run'), patch.dict('os.environ', {'npm_config_cache': str(root / 'cache')}):
                if traversal or bad_integrity:
                    with self.assertRaisesRegex(ValueError, 'Unsafe|integrity'):
                        locked.install()
                else:
                    locked.install()
                    receipt = json.loads((root / '.runtime/pipeline-restore/node-packages.json').read_text())
                    self.assertTrue(receipt['complete'])
                    self.assertTrue(receipt['packages'][0]['integrity_verified'])
            self.assertFalse((Path(folder) / 'outside.txt').exists())

    def test_locked_install_validates_integrity(self):
        self.check_locked_archive()

    def test_locked_install_rejects_corrupt_archive(self):
        self.check_locked_archive(bad_integrity=True)

    def test_locked_install_rejects_archive_path_escape(self):
        self.check_locked_archive(traversal=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
