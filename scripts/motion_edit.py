"""LAYER: Engineer. THE BIG PICTURE: enhance real footage while retaining its dialogue.
THE FLOW: prepare -> author/validate cues -> guarded render -> review -> verified delivery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any
from uuid import uuid4

from common import FFMPEG, FFPROBE, NODE, REMOTION, ROOT, ffmpeg_command, probe, require_guard
from build import matching_pictures, picture_signature, validate_reference_edit

HOME = ROOT / 'Main/motion-edits'
KINDS = {'speaker', 'emphasis', 'illustration', 'comparison', 'badges'}
PALETTE = {'light': '#f5f4f0', 'dark': '#101114', 'accent': '#c8f45d'}
FONT_ROOT = ROOT / '.agents/skills/viral-shorts/assets/fonts'
FONT_FILES = {'InterVariable.woff2': 'InterVariable.woff2',
              'InterVariable-Italic.woff2': 'InterVariable-Italic.woff2',
              'CormorantGaramond-Italic.ttf': 'CormorantGaramond-Italic.ttf',
              'LICENSE.txt': 'Inter-LICENSE.txt', 'Cormorant-OFL.txt': 'Cormorant-OFL.txt'}


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def under_d(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.parent.resolve()):
        raise ValueError('Staged assets and outputs must stay under D:\\J.A.R.V.I.S')
    return resolved


def video_clock(path: Path) -> dict:
    """Inspect decoded presentation timestamps without retaining an unbounded frame list."""
    media = probe(path)
    command = [FFPROBE, '-v', 'error', '-threads', '2', '-select_streams', 'v:0',
               '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time,duration_time,pkt_duration_time',
               '-of', 'compact=p=0:nk=0', str(path)]
    first = last = None
    last_duration = 1 / media.fps
    count, regular = 0, True
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            fields = dict(part.split('=', 1) for part in line.strip().split('|') if '=' in part)
            try:
                moment = float(fields['best_effort_timestamp_time'])
            except (ValueError, KeyError):
                continue
            try:
                last_duration = float(fields.get('duration_time') or fields.get('pkt_duration_time') or 1 / media.fps)
            except ValueError:
                last_duration = 1 / media.fps
            if first is None:
                first = moment
            regular &= abs(moment - first - count / media.fps) <= max(.0005, .02 / media.fps)
            count += 1
            last = moment
        error = proc.stderr.read() if proc.stderr else ''
        if proc.wait():
            raise RuntimeError(error)
    if not count:
        raise ValueError('Source has no decodable video frames')
    return {'frames': count, 'rate': media.rate, 'fps': media.fps, 'regular': regular,
            'first_pts': first, 'last_pts': last,
            'last_frame_duration': last_duration,
            'duration': count / media.fps if regular else last - first + last_duration}


def audio_packets(path: Path) -> dict:
    command = [FFPROBE, '-v', 'error', '-select_streams', 'a:0', '-show_streams', '-show_packets',
               '-show_data_hash', 'sha256', '-show_entries',
               'stream=codec_name,time_base,sample_rate,channels,channel_layout,extradata_hash:packet=pts,dts,duration,size,data_hash', '-of', 'json', str(path)]
    data = json.loads(subprocess.run(command, capture_output=True, text=True, check=True).stdout)
    # FFprobe includes container tags/dispositions even with show_entries. A mux
    # deliberately clearing Google/handler/language tags must not fail audio QA.
    # Keep decoder configuration, priming side data and every packet timestamp/hash.
    fields = ('codec_name', 'time_base', 'sample_rate', 'channels', 'channel_layout', 'extradata_hash')
    return {'streams': [{key: stream[key] for key in fields if key in stream} for stream in data.get('streams', [])],
            'packets': data.get('packets', [])}


def prepare(target: str, identifier: str, no_transcribe: bool) -> Path:
    require_guard(gpu=True)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', identifier):
        raise ValueError('Use a unique 1-60 character project id: letters, digits, hyphen, underscore')
    project = HOME / 'Working' / identifier
    if project.exists():
        raise FileExistsError('Project already exists; preserve it and choose a new id')
    from prep import fetch
    _, original, metadata = fetch(target, work_id=f'motion_{identifier}'[:60])
    original_hash = digest(original)
    project.mkdir(parents=True)
    source = project / ('source' + original.suffix.lower())
    shutil.copy2(original, source)
    clock = video_clock(source)
    normalization = None
    if not clock['regular'] or abs(clock['first_pts']) > .001:
        normalized = project / 'source-cfr.mp4'
        subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', str(source), '-map', '0:v:0', '-map', '0:a:0?',
            '-vf', f"fps={clock['rate']}", '-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', '20M',
            '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', str(normalized)]), check=True)
        normalization = {'reason': 'Variable presentation timestamps or nonzero video start', 'original_clock': clock}
        source = normalized
        clock = video_clock(source)
        if not clock['regular'] or abs(clock['first_pts']) > .001:
            raise ValueError('CFR staging did not produce a zero-origin regular timeline; inspect before proceeding')
    media = probe(source)
    transcript = []
    language = None
    if media.has_audio and not no_transcribe:
        # The installed PyAV path may reject metadata_errors; raw PCM avoids that decoder interface.
        import numpy as np
        from prep import _load_whisper
        pcm = subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', str(source), '-vn', '-ac', '1',
            '-ar', '16000', '-f', 'f32le', '-']), capture_output=True, check=True).stdout
        model, _ = _load_whisper('small')
        segments, info = model.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, vad_filter=True)
        language = info.language
        for segment in segments:
            transcript.append({'start': segment.start, 'end': segment.end, 'text': segment.text.strip(),
                'words': [{'w': w.word, 's': w.start, 'e': w.end} for w in (segment.words or [])]})
    transcript_record = {'language': language, 'segments': transcript,
        'status': 'transcribed; verify wording/onsets against speech' if transcript else 'not transcribed; inspect speech before authoring captions'}
    save(project / 'transcript.json', transcript_record)
    crop = min(1, media.height * 1080 / (1920 * media.width))
    spec = {'id': identifier, 'source': {'path': str(source), 'sha256': digest(source),
        'original': str(original), 'original_sha256': original_hash, 'metadata': metadata,
        'rate': media.rate, 'fps': media.fps, 'frames': clock['frames'], 'duration': clock['duration'],
        'width': media.width, 'height': media.height, 'has_audio': media.has_audio, 'normalization': normalization},
        'outputScale': 2, 'palette': dict(PALETTE), 'reuseBasis': '', 'assets': {},
        'sourceMusic': None if media.has_audio else False,
        'shots': [{'t': 0, 'x': .5, 'w': crop}], 'captionLayers': [],
        'scenes': [{'kind': 'speaker', 'start': 0, 'end': clock['duration']}],
        'posting': {'title': '', 'description': ''}, 'synthetic': False,
        'transcript': transcript_record,
        'transcription': 'prepared' if transcript else 'not transcribed; inspect speech before authoring captions'}
    path = project / 'project.json'
    save(path, spec)
    save(project / 'review.json', {'render_sha256': '', 'reviewed_by': '', 'reviewed_at': '',
        'visual_complete': False, 'caption_timing_checked': False, 'branding_checked': False,
        'continuous_playback_with_sound': False, 'issues': [], 'coverage': ''})
    print(path, flush=True)
    return path


def finite(value: Any, low: float, high: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name} must be finite and between {low} and {high}')
    return float(value)


def intersects(a: dict, b: dict) -> bool:
    return a['x'] < b['x'] + b['width'] and b['x'] < a['x'] + a['width'] and a['y'] < b['y'] + b['height'] and b['y'] < a['y'] + a['height']


def validate(spec: dict, *, require_ready: bool = False) -> dict:
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,60}', spec.get('id', '')):
        raise ValueError('Invalid project id')
    source = spec['source']
    path = under_d(Path(source['path']))
    if not path.is_file():
        raise ValueError('Source file is missing')
    rate = Fraction(source['rate'])
    fps = finite(source['fps'], 1, 120, 'fps')
    if abs(float(rate) - fps) > 1e-8:
        raise ValueError('Exact native rate and fps disagree')
    frames = source['frames']
    if type(frames) is not int or frames < 1:
        raise ValueError('Source frame count must be a positive integer')
    duration = frames / fps
    finite(source['duration'], 0, 86400, 'source duration')
    if abs(source['duration'] - duration) > .001:
        raise ValueError('Source duration and frame count disagree')
    for key in ('width', 'height'):
        finite(source[key], 1, 32768, f'source {key}')
    if type(source.get('has_audio')) is not bool:
        raise ValueError('Source has_audio must be boolean')
    if spec.get('sourceMusic') is not None and type(spec['sourceMusic']) is not bool:
        raise ValueError('sourceMusic is true, false or null until inspected')
    if type(spec.get('outputScale', 2)) is not int or spec.get('outputScale', 2) not in (1, 2):
        raise ValueError('outputScale must be 1 or 2')
    if spec.get('music') or spec.get('narration') or spec.get('soundEffects') or spec.get('watermark'):
        raise ValueError('This runner retains original dialogue only; author an explicitly requested, separately verified audio/branding extension')
    for key in PALETTE:
        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', spec.get('palette', PALETTE)[key]):
            raise ValueError('Palette requires six-digit hex colours')
    for key, asset in spec.get('assets', {}).items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key):
            raise ValueError('Invalid asset id')
        file = under_d(Path(asset['path']))
        if not file.is_file() or file.suffix.lower() not in ('.svg', '.png', '.jpg', '.jpeg', '.webp'):
            raise ValueError(f'Missing or unsupported still asset: {key}')
        if require_ready and not str(asset.get('reuseBasis', '')).strip():
            raise ValueError(f'Asset {key} needs a reuse basis')
    if require_ready and not str(spec.get('reuseBasis', '')).strip():
        raise ValueError('Record the source reuse basis before rendering')
    previous = 0
    scenes = spec.get('scenes', [])
    if not scenes:
        raise ValueError('Author at least one scene')
    layers = list(spec.get('captionLayers', []))
    boxes = []
    for scene in scenes:
        if scene.get('kind') not in KINDS:
            raise ValueError('Unsupported scene kind')
        start = round(finite(scene['start'], 0, duration, 'scene start') * fps)
        end = round(finite(scene['end'], 0, duration + 1e-7, 'scene end') * fps)
        if start != previous or end <= start or end > frames:
            raise ValueError('Scenes must cover the source exactly with no frame gaps or overlaps')
        previous = end
        for key in ('title', 'subtitle', 'eyebrow'):
            if key in scene and (not isinstance(scene[key], str) or len(scene[key]) > 180):
                raise ValueError('Scene text must be concise strings; split long explanations into authored layers')
        if scene['kind'] in ('emphasis', 'illustration', 'comparison') and not str(scene.get('title', '')).strip():
            raise ValueError('Graphic scenes require a title')
        asset_ids = [scene['asset']] if scene.get('asset') else []
        if scene['kind'] == 'illustration' and not scene.get('asset'):
            raise ValueError('Illustration scene requires an authored asset')
        if scene['kind'] == 'comparison':
            for side in ('left', 'right'):
                item = scene.get(side, {})
                if not str(item.get('title', '')).strip() or len(item['title']) > 40 or len(item.get('detail', '')) > 120:
                    raise ValueError('Comparison sides need short titles and details')
                if item.get('asset'):
                    asset_ids.append(item['asset'])
        for asset_id in asset_ids:
            if asset_id not in spec.get('assets', {}):
                raise ValueError(f'Unknown scene asset: {asset_id}')
        for layer in scene.get('captionLayers', []):
            if layer['t'] < scene['start'] or layer['t'] + layer['dur'] > scene['end'] + .001:
                raise ValueError('Scene caption layers must fit their scene')
            layers.append(layer)
        if scene['kind'] == 'badges' and not scene.get('badges'):
            raise ValueError('Badge scene requires badges')
        for badge in scene.get('badges', []):
            finite(badge['at'], scene['start'], scene['end'] - 1 / fps, 'badge onset')
            width = finite(badge['width'], 100, 500, 'badge width')
            x = finite(badge['x'], 72, 1008 - width, 'badge x')
            y = finite(badge['y'], 220, 1380, 'badge y')
            if not isinstance(badge['text'], str) or not badge['text'].strip() or len(badge['text']) > 28:
                raise ValueError('Badge text must be short')
            boxes.append({'x': x, 'y': y, 'width': width, 'height': 100, 't': badge['at'], 'dur': scene['end'] - badge['at']})
    if previous != frames:
        raise ValueError('Scenes must cover the complete source')
    if layers:
        validate_reference_edit({'profile': 'editorial', 'layers': layers}, duration)
    for layer in layers:
        if layer.get('depth', 'front') != 'front':
            raise ValueError('Subject-depth masks belong in an explicitly authored extension; this composition uses front layers')
        width = layer.get('width', 900)
        height = layer['size'] * layer.get('lineHeight', .94) * (layer['text'].count('\n') + 1) + 16
        if layer['x'] < 72 or layer['x'] + width > 1008 or layer['y'] < 220 or layer['y'] + height > 1500:
            raise ValueError('Caption box is outside the phone-safe bounds')
        boxes.append({**layer, 'width': width, 'height': height})
    for protected in spec.get('protectedRegions', []):
        finite(protected['start'], 0, duration, 'protected interval start')
        finite(protected['end'], protected['start'], duration, 'protected interval end')
        for key, maximum in (('x', 1080), ('y', 1920), ('width', 1080), ('height', 1920)):
            finite(protected[key], 0, maximum, f'protected {key}')
        for box in boxes:
            active = max(box['t'], protected['start']) < min(box['t'] + box['dur'], protected['end'])
            if active and intersects(box, protected):
                raise ValueError('Caption/badge overlaps an authored protected face/UI region')
    last = -1
    for shot in spec.get('shots', []):
        moment = finite(shot['t'], 0, duration, 'shot time')
        if moment <= last:
            raise ValueError('Shots must have increasing times')
        last = moment
        finite(shot['x'], 0, 1, 'shot centre')
        finite(shot['w'], .05, 1, 'shot width')
    return {'id': spec['id'], 'frames': frames, 'fps': fps, 'duration': duration,
            'scene_count': len(scenes), 'caption_layers': len(layers), 'ready': bool(spec.get('reuseBasis', '').strip())}


def stage(spec: dict, project: Path, qa: Path) -> tuple[Path, Path, dict]:
    source = Path(spec['source']['path'])
    source_sha = digest(source)
    if source_sha != spec['source']['sha256']:
        raise ValueError('Source identity changed; do not render against stale timing')
    asset_provenance = {key: {**a, 'sha256': digest(Path(a['path']))} for key, a in spec.get('assets', {}).items()}
    font_provenance = {name: digest(FONT_ROOT / name) for name in FONT_FILES}
    identity = {'source': source_sha, 'assets': asset_provenance, 'fonts': font_provenance}
    snapshot = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    public = project / 'render-public' / snapshot
    public.mkdir(parents=True, exist_ok=True)
    def publish(original: Path, relative: str) -> str:
        target = public / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if digest(target) != digest(original):
                raise ValueError('Immutable render snapshot changed; inspect before proceeding')
            else:
                return relative
        # Copies isolate earlier project assets from subsequent authoring changes.
        shutil.copy2(original, target)
        if digest(target) != digest(original):
            raise ValueError('Render asset snapshot failed integrity check')
        return relative
    src = publish(source, 'source' + source.suffix)
    for name, target in FONT_FILES.items():
        publish(FONT_ROOT / name, f'fonts/{target}')
    assets = {key: publish(Path(a['path']), f"assets/{key}{Path(a['path']).suffix}") for key, a in spec.get('assets', {}).items()}
    scenes = json.loads(json.dumps(spec['scenes']))
    for scene in scenes:
        if scene.get('asset'):
            scene['asset'] = assets[scene['asset']]
        for side in ('left', 'right'):
            if scene.get(side, {}).get('asset'):
                scene[side]['asset'] = assets[scene[side]['asset']]
    source_meta = spec['source']
    props = {'src': src, 'fps': source_meta['fps'], 'durationInFrames': source_meta['frames'],
        'sourceWidth': source_meta['width'], 'sourceHeight': source_meta['height'], 'hasAudio': source_meta['has_audio'],
        'shots': spec.get('shots', []), 'palette': spec.get('palette', PALETTE), 'scenes': scenes,
        'captionLayers': spec.get('captionLayers', [])}
    props_path = qa / 'render-props.json'
    save(props_path, props)
    save(qa / 'project.json', spec)
    return props_path, public, {'snapshot': str(public), 'assets': asset_provenance, 'fonts': font_provenance}


def record_render(project: Path, qa: Path, receipt: dict) -> None:
    save(qa / 'technical.json', receipt)
    # A later preview must not replace the resumable pointer to a completed full render.
    save(project / ('last-preview.json' if receipt['preview'] else 'last-render.json'), receipt)


def decode(path: Path, expected_frames: int) -> dict:
    command = ffmpeg_command([FFMPEG, '-v', 'error', '-hwaccel', 'cuda', '-i', str(path),
        '-map', '0:v:0', '-an', '-progress', 'pipe:1', '-f', 'null', '-'])
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    frames = [int(line.split('=')[1]) for line in result.stdout.splitlines() if line.startswith('frame=')]
    if not frames or frames[-1] != expected_frames or result.stderr.strip():
        raise RuntimeError('Complete CUDA decode/frame-count check failed: ' + result.stderr)
    return {'complete': True, 'frames': frames[-1], 'decoder': 'cuda'}


def validate_picture_clock(signature: dict, frames: int, fps: float) -> None:
    if (int(signature['nb_read_packets']) != frames or abs(float(Fraction(signature['r_frame_rate'])) - fps) > 1e-7
            or abs(float(signature['duration']) - frames / fps) > .001
            or abs(float(signature.get('start_time', 0))) > .001):
        raise RuntimeError('Picture timestamps, duration or frame count differ from the native-frame contract')


def render(spec_path: Path, *, preview: str | None = None, still: float | None = None, scale: int | None = None) -> Path:
    require_guard(gpu=True)
    spec = read(spec_path)
    checked = validate(spec, require_ready=True)
    project = under_d(spec_path.parent)
    drafts = project / 'drafts'
    drafts.mkdir(exist_ok=True)
    token = uuid4().hex[:12]
    qa = project / 'qa' / token
    qa.mkdir(parents=True)
    props, public, provenance = stage(spec, project, qa)
    command = [str(NODE), str(REMOTION)]
    shared = [f'--props={props}', f'--public-dir={public}', '--gl=angle',
              '--offthreadvideo-video-threads=2', '--offthreadvideo-cache-size-in-bytes=134217728']
    if still is not None:
        finite(still, 0, checked['duration'] - 1 / checked['fps'], 'still time')
        output = qa / f'frame-{round(still * checked["fps"]):06d}.png'
        subprocess.run(command + ['still', 'src/index.ts', 'MotionEdit', str(output),
            f'--frame={round(still * checked["fps"])}', f'--scale={scale or spec.get("outputScale", 2)}', *shared], cwd=ROOT, check=True)
        return output
    first, last = 0, checked['frames'] - 1
    if preview:
        try:
            start, end = map(float, preview.split(':'))
        except ValueError as exc:
            raise ValueError('Preview range must be START:END seconds') from exc
        finite(start, 0, checked['duration'], 'preview start')
        finite(end, 0, checked['duration'], 'preview end')
        first, last = round(start * checked['fps']), round(end * checked['fps']) - 1
        if last < first or last >= checked['frames']:
            raise ValueError('Preview range contains no frames or exceeds source')
    selected_scale = scale or (1 if preview else spec.get('outputScale', 2))
    partial = drafts / f'{token}.partial.mp4'
    log = qa / 'render.log'
    with log.open('w', encoding='utf-8') as stream:
        subprocess.run(command + ['render', 'src/index.ts', 'MotionEdit', str(partial), *shared,
            '--muted', '--concurrency=1', '--hardware-acceleration=required', '--image-format=png',
            f'--scale={selected_scale}', f'--video-bitrate={40 if selected_scale == 2 else 10}M',
            f'--frames={first}-{last}', '--log=verbose'], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, check=True)
    if 'Encoder: h264_nvenc, hardware accelerated: true' not in log.read_text(encoding='utf-8'):
        raise RuntimeError('Actual NVENC execution was not established')
    original_picture = picture_signature(partial)
    validate_picture_clock(original_picture, last - first + 1, checked['fps'])
    clean = Path(spec['source']['path'])
    audio_receipt = {'mode': 'silent source', 'packets_identical': True, 'timing_identical': True}
    if spec['source']['has_audio']:
        packet_source = audio_packets(clean)
        if not preview and packet_source['streams'][0]['codec_name'] != 'aac':
            clean = qa / 'dialogue-master.m4a'
            subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', spec['source']['path'],
                '-vn', '-c:a', 'aac', '-b:a', '192k', str(clean)]), check=True)
            packet_source = audio_packets(clean)
        muxed = partial.with_name(f'{token}.dialogue.mp4')
        args = [FFMPEG, '-v', 'error', '-i', str(partial), '-i', str(clean), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy']
        if preview:
            args += ['-af', f'atrim=start={first/checked["fps"]}:end={(last+1)/checked["fps"]},asetpts=PTS-STARTPTS', '-c:a', 'aac', '-b:a', '192k']
        else:
            args += ['-c:a', 'copy']
        subprocess.run(ffmpeg_command(args + ['-map_metadata', '-1', '-movflags', '+faststart', str(muxed)]), check=True)
        if not matching_pictures(original_picture, picture_signature(muxed)):
            raise RuntimeError('Audio mux changed picture packets')
        if not preview:
            after = audio_packets(muxed)
            if packet_source != after:
                raise RuntimeError('Dialogue packet payloads or timestamps changed')
        audio_receipt = {'mode': 'preview AAC excerpt' if preview else ('source stream copy' if clean == Path(spec['source']['path']) else 'one-time AAC master'),
                         'packets_identical': not bool(preview), 'timing_identical': not bool(preview), 'compared_to': str(clean)}
        partial.unlink()
        muxed.replace(partial)
    media = probe(partial)
    if (media.width, media.height) != (1080 * selected_scale, 1920 * selected_scale) or abs(media.fps - checked['fps']) > 1e-7:
        raise RuntimeError('Output dimensions or frame rate differ from the authored contract')
    decoded = decode(partial, last - first + 1)
    music_free = not spec['source']['has_audio'] or spec.get('sourceMusic') is False
    output = drafts / (f'{token}-PREVIEW.mp4' if preview else f'{token}-{"music-free" if music_free else "no-added-music"}.mp4')
    partial.rename(output)
    receipt = {'file': str(output), 'sha256': digest(output), 'project_sha256': digest(spec_path),
        'source_sha256': spec['source']['sha256'], 'dimensions': [media.width, media.height], 'fps': media.fps,
        'frames': last - first + 1, 'range': [first, last], 'preview': bool(preview), 'audio': audio_receipt,
        'decode': decoded, 'encoder': 'h264_nvenc', 'passed': True, 'synthetic': spec.get('synthetic', False),
        'guard_job': os.environ.get('CLIPPING_GUARD_JOB'), 'review_pending': True, 'music_free': music_free,
        'completed_at': datetime.now(timezone.utc).isoformat()}
    receipt['picture_clock'] = {key: original_picture[key] for key in ('r_frame_rate', 'nb_read_packets', 'duration', 'start_time') if key in original_picture}
    receipt['asset_provenance'] = provenance['assets']
    receipt['font_provenance'] = provenance['fonts']
    receipt['asset_snapshot'] = provenance['snapshot']
    record_render(project, qa, receipt)
    print(json.dumps(receipt, indent=2), flush=True)
    return output


def deliver(spec_path: Path, review_path: Path | None = None) -> Path:
    spec = read(spec_path)
    validate(spec, require_ready=True)
    if spec['source']['has_audio'] and spec.get('sourceMusic') is not False:
        raise ValueError('A music-free final needs inspected clean dialogue; embedded source music is not removed by copying')
    project = under_d(spec_path.parent)
    receipt = read(project / 'last-render.json')
    if receipt.get('preview') or receipt.get('synthetic') or spec.get('synthetic'):
        raise ValueError('Previews and synthetic validation fixtures are not finished channel exports')
    if not receipt.get('passed') or receipt['project_sha256'] != digest(spec_path):
        raise ValueError('Render is missing, failed or stale relative to the project')
    source = under_d(Path(receipt['file']))
    if digest(source) != receipt['sha256']:
        raise ValueError('Rendered file changed after technical validation')
    review = read(review_path or project / 'review.json')
    required = ('visual_complete', 'caption_timing_checked', 'branding_checked', 'continuous_playback_with_sound')
    if (review.get('render_sha256') != receipt['sha256'] or not all(review.get(key) is True for key in required)
            or review.get('issues') != [] or not all(str(review.get(key, '')).strip() for key in ('reviewed_by', 'reviewed_at', 'coverage'))):
        raise ValueError('Record actual visual/caption/branding/playback coverage for this render before final delivery')
    posting = spec.get('posting', {})
    if not all(isinstance(posting.get(key), str) and posting[key].strip() for key in ('title', 'description')):
        raise ValueError('Author a brief posting title and description before delivery')
    directory = HOME / 'Exports' / spec['id']
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / source.name
    if destination.exists():
        raise FileExistsError('Preserve the earlier export; use a new revision id')
    pending = destination.with_suffix('.partial.mp4')
    if pending.exists():
        raise FileExistsError('Inspect the existing incomplete delivery copy')
    shutil.copy2(source, pending)
    if digest(pending) != receipt['sha256']:
        raise RuntimeError('Delivery copy failed integrity validation')
    pending.rename(destination)
    save(directory / f'{destination.stem}-delivery.json', {**receipt, 'file': str(destination),
        'review_pending': False, 'review': review, 'reuseBasis': spec['reuseBasis'], 'assets': receipt.get('asset_provenance', {}),
        'source_provenance': spec['source']})
    (directory / f'{destination.stem}-POSTING.md').write_text(
        f"# {posting.get('title', spec['id'])}\n\n{posting.get('description', '')}\n", encoding='utf-8')
    print(destination, flush=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('input'); prep.add_argument('--id', required=True)
    prep.add_argument('--no-transcribe', action='store_true')
    check = sub.add_parser('validate'); check.add_argument('project', type=Path)
    run = sub.add_parser('render'); run.add_argument('project', type=Path)
    ranges = run.add_mutually_exclusive_group(); ranges.add_argument('--preview', metavar='START:END'); ranges.add_argument('--still', type=float)
    run.add_argument('--scale', type=int, choices=(1, 2))
    export = sub.add_parser('deliver'); export.add_argument('project', type=Path); export.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.input, args.id, args.no_transcribe)
    elif args.command == 'validate':
        print(json.dumps(validate(read(args.project), require_ready=True), indent=2))
    elif args.command == 'render':
        render(args.project, preview=args.preview, still=args.still, scale=args.scale)
    else:
        deliver(args.project, args.review)


if __name__ == '__main__':
    main()
