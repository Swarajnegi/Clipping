"""LAYER: Engineer. THE BIG PICTURE: finish this original touchscreen explainer locally.
THE FLOW: reuse verified narration -> align scenes -> guarded stills/render -> validate -> export.
Run through the shared GPU guard with prepare, stills, render, qa or publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import NODE, REMOTION, PUBLIC, FFMPEG, probe, require_guard, run, wait_headroom
from ai_video import plan, read_spec

STAGING = ROOT / 'out/ai-video/touchscreen-20261026'
ASSETS = PUBLIC / 'ai-video/touchscreen-20261026'
EXPORTS = ROOT / 'Main/AI-videos/Exports/touchscreen-20261026'


def token(value: str) -> str:
    return re.sub(r'[^a-z0-9]', '', value.lower())


def prepare() -> dict:
    import numpy as np
    import soundfile as sf

    spec = read_spec(PROJECT / 'storyboard.json')
    voice = json.loads((PROJECT / 'narration.json').read_text(encoding='utf-8'))
    if voice['text'] != spec['narration'] or voice['transcription_device'] != 'cuda':
        raise RuntimeError('Narration does not match the storyboard or CUDA alignment was not established')
    words = voice['words']
    clean = [token(w['w']) for w in words]
    markers = ['most modern', 'the controller sends', 'your finger conducts', 'the controller finds', 'track several', 'so you']
    starts = [0]
    previous = 0
    for marker in markers:
        tokens = marker.split()
        match = next(i for i in range(previous, len(clean) - len(tokens) + 1) if clean[i:i + len(tokens)] == tokens)
        starts.append(round(max(0, words[match]['s'] - .06) * spec['fps']))
        previous = match + len(tokens)
    frames = math.ceil((voice['durationSec'] + .6) * spec['fps'])
    if not 30 <= frames / spec['fps'] <= 60:
        raise RuntimeError('Narration does not fit the requested 30–60 second range')
    ends = starts[1:] + [frames]
    for scene, start, end in zip(spec['scenes'], starts, ends):
        scene['duration'] = (end - start) / spec['fps']
    decision = plan(spec)
    if decision['status'] != 'ready':
        raise RuntimeError(json.dumps(decision))
    (PROJECT / 'plan.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
    (PROJECT / 'storyboard-timed.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    ASSETS.mkdir(parents=True, exist_ok=True)
    speech, rate = sf.read(PROJECT / 'narration.wav', dtype='float32')
    mix = np.pad(speech, (0, max(0, math.ceil(frames / spec['fps'] * rate) - len(speech))))
    for index, frame in enumerate(starts):
        begin = round((frame / spec['fps'] + .1) * rate)
        t = np.arange(round(.12 * rate)) / rate
        sound = .018 * np.sin(2 * math.pi * (740 + index * 80) * t) * np.exp(-t * 44) * np.minimum(t / .006, 1)
        mix[begin:begin + len(sound)] += sound[:len(mix) - begin]
    sf.write(ASSETS / 'narration-mix.wav', mix, rate, subtype='PCM_16')
    caption_json = [{'text': ' ' + w['w'].strip(), 'startMs': round(w['s'] * 1000), 'endMs': round(w['e'] * 1000),
                     'timestampMs': round((w['s'] + w['e']) * 500), 'confidence': None} for w in words]
    (PROJECT / 'captions.json').write_text(json.dumps(caption_json, indent=2), encoding='utf-8')
    props = {'title': spec['title'], 'scenes': spec['scenes'], 'fps': spec['fps'],
             'audio': 'ai-video/touchscreen-20261026/narration-mix.wav', 'captions': words}
    (PROJECT / 'render-props.json').write_text(json.dumps(props, indent=2), encoding='utf-8')
    result = {'duration_seconds': frames / spec['fps'], 'scene_start_frames': starts,
              'peak_audio': float(np.max(np.abs(mix))), 'audio_samples': len(mix),
              'estimated_seconds': decision['estimated_seconds']}
    (PROJECT / 'timing.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result), flush=True)
    return result


def remotion_args() -> list[str]:
    return [str(NODE), str(REMOTION), 'render', 'src/index.ts', 'AIReel']


def stills() -> None:
    require_guard(gpu=True)
    timing = json.loads((PROJECT / 'timing.json').read_text())
    images = PROJECT / 'frames'
    images.mkdir(exist_ok=True)
    frames = [min(start + 60, (timing['scene_start_frames'][i + 1] - 1) if i + 1 < 7 else round(timing['duration_seconds'] * 30) - 1)
              for i, start in enumerate(timing['scene_start_frames'])]
    with (PROJECT / 'stills.log').open('w', encoding='utf-8') as log:
        subprocess.run(remotion_args() + [images.relative_to(ROOT).as_posix(), f'--props={PROJECT / "render-props.json"}',
                       '--frames=' + ','.join(map(str, frames)), '--image-format=png', '--scale=.5',
                       '--concurrency=1', '--gl=angle'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    from PIL import Image, ImageOps, ImageDraw
    files = sorted(images.glob('*.png'))
    if len(files) != 7:
        raise RuntimeError('Expected one image for each of seven scenes')
    sheet = Image.new('RGB', (4 * 270, 2 * 510), '#d9ddd5')
    for i, path in enumerate(files):
        with Image.open(path) as source:
            tile = ImageOps.contain(source.convert('RGB'), (270, 480))
            sheet.paste(tile, ((i % 4) * 270, (i // 4) * 510))
        ImageDraw.Draw(sheet).text(((i % 4) * 270 + 8, (i // 4) * 510 + 486), f'SCENE {i+1}', fill='#172c35')
    sheet.save(PROJECT / 'storyboard-preview.jpg', quality=92)


def render() -> None:
    require_guard(gpu=True)
    wait_headroom(gpu=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    pending = STAGING / 'touchscreen.partial.mp4'
    start = time.monotonic()
    with (PROJECT / 'render.log').open('w', encoding='utf-8') as log:
        subprocess.run(remotion_args() + [str(pending), f'--props={PROJECT / "render-props.json"}',
                       '--concurrency=1', '--offthreadvideo-video-threads=2', '--hardware-acceleration=required',
                       '--gl=angle', '--log=verbose'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    media = probe(pending)
    timing = json.loads((PROJECT / 'timing.json').read_text())
    if (media.width, media.height) != (1080, 1920) or abs(media.fps - 30) > .001 or not media.has_audio or abs(media.duration - timing['duration_seconds']) > .12:
        raise RuntimeError('Stream/duration validation failed; partial output preserved')
    if 'Encoder: h264_nvenc, hardware accelerated: true' not in (PROJECT / 'render.log').read_text(encoding='utf-8'):
        raise RuntimeError('NVENC was not verified')
    final = STAGING / 'touchscreen.mp4'
    pending.replace(final)
    receipt = {'created_at': datetime.now(timezone.utc).isoformat(), 'duration_seconds': media.duration,
               'width': media.width, 'height': media.height, 'fps': media.fps, 'audio': media.has_audio,
               'actual_encoder': 'h264_nvenc', 'concurrency': 1, 'render_strategy': 'single batch',
               'render_seconds': time.monotonic() - start, 'output': str(final),
               'props_sha256': hashlib.sha256((PROJECT / 'render-props.json').read_bytes()).hexdigest(),
               'cloud_used': False, 'visual_provenance': 'Original assistant-authored SVG/React motion graphics',
               'voice': 'Local Kokoro am_michael; CUDA faster-whisper alignment',
               'sound': 'Original low-level synthesized transition tones', 'editorial_review': 'pending'}
    (PROJECT / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt), flush=True)


def qa() -> None:
    require_guard()
    final = STAGING / 'touchscreen.mp4'
    from build import qa_strip
    qa_strip(final, PROJECT / 'qa.jpg', probe(final).duration)
    timing = json.loads((PROJECT / 'timing.json').read_text())
    boundary = PROJECT / 'boundary-frames'
    boundary.mkdir(exist_ok=True)
    for i, frame in enumerate(timing['scene_start_frames'][1:]):
        for offset in (-2, 2, 16):
            run([FFMPEG, '-y', '-ss', str((frame + offset) / 30), '-i', str(final), '-frames:v', '1',
                 '-vf', 'scale=270:480', str(boundary / f'{i+1:02d}_{offset:+03d}.jpg')])
    from PIL import Image, ImageOps, ImageDraw
    sheet = Image.new('RGB', (6 * 180, 3 * 350), '#d9ddd5')
    offsets = (-2, 2, 16)
    for column in range(6):
        for row, offset in enumerate(offsets):
            with Image.open(boundary / f'{column+1:02d}_{offset:+03d}.jpg') as source:
                sheet.paste(ImageOps.contain(source, (180, 320)), (column * 180, row * 350))
            ImageDraw.Draw(sheet).text((column * 180 + 6, row * 350 + 326), f'JOIN {column+1} {offset:+d}f', fill='#172c35')
    sheet.save(PROJECT / 'boundary-review.jpg', quality=92)
    run([FFMPEG, '-v', 'error', '-i', str(final), '-f', 'null', '-'])
    print('Full video/audio decode passed; inspect QA and boundary images.', flush=True)


def publish() -> None:
    receipt = json.loads((PROJECT / 'receipt.json').read_text())
    if receipt.get('editorial_review') != 'passed':
        raise RuntimeError('Record actual visual/timing review before exporting')
    EXPORTS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STAGING / 'touchscreen.mp4', EXPORTS / 'touchscreen.mp4')
    shutil.copy2(PROJECT / 'receipt.json', EXPORTS / 'receipt.json')
    print(str(EXPORTS / 'touchscreen.mp4'))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'preview', 'stills', 'render', 'qa', 'publish'])
    args = parser.parse_args()
    require_guard(gpu=args.stage in ('preview', 'stills', 'render'))
    if args.stage == 'preview':
        prepare()
        stills()
        return
    {'prepare': prepare, 'stills': stills, 'render': render, 'qa': qa, 'publish': publish}[args.stage]()


if __name__ == '__main__':
    main()
