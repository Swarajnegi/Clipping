"""LAYER: Engineer. THE BIG PICTURE: produce AI-authored reels without uncontrolled generation.
THE FLOW: validate brief -> measured route/forecast -> optional voice -> one guarded render -> QA.
Commands: check; plan <spec>; render <spec>; benchmark. Heavy commands require the shared guard.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from common import NODE, REMOTION, ROOT, OUT, PUBLIC, WORK, probe, require_guard, wait_headroom

PROFILES = ROOT / '.runtime/ai-video/benchmarks.json'


def read_spec(path: Path) -> dict:
    spec = json.loads(path.read_text(encoding='utf-8-sig'))
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', spec.get('id', '')):
        raise ValueError('id must contain 1–60 letters, digits, underscores or hyphens')
    if spec.get('backend', 'illustrated') not in ('illustrated', 'local-diffusion'):
        raise ValueError('Use illustrated or local-diffusion; online assets must be imported explicitly')
    scenes = spec.get('scenes')
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 100:
        raise ValueError('Provide 1–100 scenes')
    for scene in scenes:
        duration = scene.get('duration', 0)
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 0 < duration <= 3600:
            raise ValueError('Scene duration must be a finite number between 0 and 3600 seconds')
        if not isinstance(scene.get('heading'), str) or not scene['heading'].strip():
            raise ValueError('Every scene needs a heading')
        if scene.get('asset'):
            source = Path(scene['asset']).resolve()
            if not source.is_relative_to(ROOT.parent) or not source.is_file():
                raise ValueError('Scene assets must be existing files under D:\\J.A.R.V.I.S')
            if scene.get('kind', 'image') not in ('image', 'video'):
                raise ValueError('Asset kind must be image or video')
            if scene.get('kind') == 'video' and probe(source).duration + .05 < duration:
                raise ValueError('Video asset is shorter than its scene; explicitly edit the scene or extend the asset')
    fps = spec.get('fps', 30)
    if fps not in (24, 25, 30, 60):
        raise ValueError('AI compositions support 24, 25, 30 or 60 FPS')
    spec['fps'] = fps
    return spec


def capabilities() -> dict:
    return {'illustrated': 'available; benchmark receipt determines verified speed',
            'local_diffusion': {'certified': False, 'torch_in_clipping_environment': importlib.util.find_spec('torch') is not None,
                                'reason': 'No certified local diffusion profile. Do not infer capability from NVENC or a 6 GB model advertisement.'},
            'online': {'policy': 'verified free only; no purchases, credit top-ups or paid fallback',
                       'pomelli': 'browser route; account, region and current free quota must be checked',
                       'open_higgsfield': 'remote API frontend, not a local generator'},
            'benchmarks': json.loads(PROFILES.read_text()) if PROFILES.exists() else {}}


def plan(spec: dict, profiles: dict | None = None) -> dict:
    duration = sum(s['duration'] for s in spec['scenes'])
    backend = spec.get('backend', 'illustrated')
    known = profiles if profiles is not None else (json.loads(PROFILES.read_text()) if PROFILES.exists() else {})
    measured = known.get(backend)
    report = {'id': spec['id'], 'backend': backend, 'duration_seconds': duration,
              'render_strategy': 'single batch', 'generation_strategy': 'not required' if backend == 'illustrated' else 'undetermined',
              'paid_cloud_allowed': False, 'status': 'ready', 'estimated_seconds': None}
    if backend == 'local-diffusion':
        if not measured or not measured.get('certified'):
            return {**report, 'status': 'needs_benchmark', 'reason': 'No certified model/RAM/VRAM/continuity profile; splitting cannot fix an oversized model.'}
        maximum = measured['max_seconds']
        counts = [math.ceil(scene['duration'] / maximum) for scene in spec['scenes']]
        report['generation_strategy'] = ('conditional segments' if any(count > 1 for count in counts)
                                         else 'single batch' if len(counts) == 1 else 'authored scenes')
        report['segments_per_scene'] = counts
        report['segment_count'] = sum(counts)
    if measured:
        if not measured.get('certified'):
            return {**report, 'status': 'needs_benchmark', 'reason': 'The measured profile is not certified'}
        report['estimated_seconds'] = round(duration * measured['seconds_per_output_second'] * 1.5 + 120)
        if report['estimated_seconds'] > 86400:
            report.update(status='needs_decision', reason='Conservative project forecast exceeds 24 hours; simplify or discuss cloud. Nothing is queued.')
    elif backend == 'illustrated':
        report.update(status='needs_benchmark', reason='Run the short illustrated benchmark before forecasting a full project')
    return report


def render(spec: dict, *, benchmark: bool = False) -> Path:
    require_guard(gpu=True)
    decision = plan(spec)
    if decision['status'] != 'ready' and not (benchmark and spec.get('backend', 'illustrated') == 'illustrated'):
        raise RuntimeError(json.dumps(decision))
    if spec.get('backend', 'illustrated') != 'illustrated':
        raise RuntimeError('Generate and certify local shots first, then import them as video scenes into the illustrated compositor')
    started = time.monotonic()
    work = WORK / 'ai-video' / spec['id']; work.mkdir(parents=True, exist_ok=True)
    assets = PUBLIC / 'ai-video' / spec['id']; assets.mkdir(parents=True, exist_ok=True)
    output = OUT / 'ai-video' / spec['id']; output.mkdir(parents=True, exist_ok=True)
    props = {'title': spec.get('title', spec['id']), 'scenes': [], 'fps': spec['fps'], 'captions': []}
    for index, scene in enumerate(spec['scenes']):
        current = dict(scene)
        if current.get('asset'):
            original = Path(current['asset']).resolve()
            target = assets / f'{index:03d}{original.suffix}'
            if original != target.resolve():
                shutil.copy2(original, target)
            current['asset'] = target.relative_to(PUBLIC).as_posix()
        props['scenes'].append(current)
    narration = spec.get('narration')
    if narration:
        voice = work / 'narration'
        subprocess.run([sys.executable, str(ROOT / 'scripts/voice.py'), narration, '--out', str(voice),
                        '--voice', spec.get('voice', 'am_michael')], cwd=ROOT, check=True)
        meta = json.loads(voice.with_suffix('.json').read_text())
        if not meta.get('words'):
            raise RuntimeError('Narration word alignment is empty; inspect the voice stage before rendering')
        if meta['durationSec'] > decision['duration_seconds']:
            raise ValueError('Narration exceeds scene duration; revise scene timing instead of truncating speech')
        shutil.copy2(voice.with_suffix('.wav'), assets / 'narration.wav')
        props.update(audio=(assets / 'narration.wav').relative_to(PUBLIC).as_posix(), captions=meta['words'])
    props_path = work / 'render-props.json'
    props_path.write_text(json.dumps(props, ensure_ascii=False), encoding='utf-8')
    wait_headroom(gpu=True)
    pending = output / f'{uuid4().hex}.partial.mp4'
    log = work / 'render.log'
    render_started = time.monotonic()
    with log.open('w', encoding='utf-8') as stream:
        subprocess.run([str(NODE), str(REMOTION), 'render', 'src/index.ts', 'AIReel', str(pending),
                        f'--props={props_path}', '--concurrency=1', '--offthreadvideo-video-threads=2',
                        '--hardware-acceleration=required', '--gl=angle', '--log=verbose'],
                       cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    media = probe(pending)
    expected_frames = sum(round(scene['duration'] * spec['fps']) for scene in spec['scenes'])
    if (media.width, media.height) != (1080, 1920) or abs(media.fps - spec['fps']) > .001 or abs(media.duration - expected_frames / spec['fps']) > .1:
        raise RuntimeError('Rendered dimensions, frame rate or duration failed validation')
    if narration and not media.has_audio:
        raise RuntimeError('Narration audio stream is missing')
    if 'Encoder: h264_nvenc, hardware accelerated: true' not in log.read_text(encoding='utf-8'):
        raise RuntimeError('Actual NVENC encoding was not established')
    final = output / 'video.mp4'
    pending.replace(final)
    from build import qa_strip
    qa_strip(final, output / 'qa.jpg', media.duration)
    receipt = {'backend': 'illustrated', 'certified': True, 'checked_at': datetime.now(timezone.utc).isoformat(),
               'duration_seconds': media.duration, 'render_seconds': time.monotonic() - render_started,
               'pipeline_seconds': time.monotonic() - started, 'seconds_per_output_second': (time.monotonic() - started) / media.duration,
               'render_strategy': 'single batch', 'actual_encoder': 'h264_nvenc', 'concurrency': 1,
               'output': str(final), 'qa': str(output / 'qa.jpg'), 'source_sha256': hashlib.sha256(props_path.read_bytes()).hexdigest()}
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    if benchmark:
        PROFILES.parent.mkdir(parents=True, exist_ok=True)
        known = json.loads(PROFILES.read_text()) if PROFILES.exists() else {}
        known['illustrated'] = receipt
        PROFILES.write_text(json.dumps(known, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2), flush=True)
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['check', 'plan', 'render', 'benchmark'])
    parser.add_argument('spec', type=Path, nargs='?')
    parser.add_argument('--seconds', type=int, choices=[8, 30], default=8, help='Bounded illustrated benchmark duration')
    args = parser.parse_args()
    if args.command == 'check':
        print(json.dumps(capabilities(), indent=2)); return
    if args.command == 'benchmark':
        half = args.seconds / 2
        narration = ('Start with one clear idea. Build the story, then bring it to life.' if args.seconds == 8 else
                     'Every strong video starts with a clear idea. First, plan the story and choose what the viewer should remember. '
                     'Then create consistent visuals, add a natural voice, and time the captions to the words. '
                     'Finally, render the whole film in one batch and check the result. This example was built locally, with no video generation service.')
        spec = {'id': f'local_ai_smoke_{args.seconds}s', 'title': 'LOCAL AI VIDEO', 'fps': 30, 'backend': 'illustrated',
                'narration': narration,
                'scenes': [{'duration': half, 'heading': 'One idea. A clear story.', 'body': 'Plan the message before generating the visuals.'},
                           {'duration': half, 'heading': 'Built locally. Rendered clearly.', 'body': 'Narration, motion and captions share one timeline.', 'accent': '#ffbe80'}]}
        render(spec, benchmark=True); return
    if args.spec is None:
        parser.error('A storyboard JSON file is required')
    spec = read_spec(args.spec)
    if args.command == 'plan':
        print(json.dumps(plan(spec), indent=2))
    else:
        render(spec)


if __name__ == '__main__':
    main()
