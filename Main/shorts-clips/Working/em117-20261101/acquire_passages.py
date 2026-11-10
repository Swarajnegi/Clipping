"""Acquire only selected HLS segment windows; preserve the original stream payload."""
import json
import subprocess
import sys
import shutil
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import FFMPEG, ffmpeg_command, probe, require_guard


def main():
    require_guard()
    from PIL import Image, ImageDraw
    brief = json.loads((HERE / 'brief.json').read_text())
    base = brief['source_access']['observed_full_stream_url']
    lines = (HERE / 'source/observed-chunklist.m3u8').read_text().splitlines()
    segments = []
    current = 0.0
    duration = None
    for line in lines:
        if line.startswith('#EXTINF:'):
            duration = float(line.split(':', 1)[1].split(',')[0])
        elif line and not line.startswith('#'):
            if duration is None:
                raise RuntimeError('Missing HLS segment duration')
            segments.append({'start': current, 'end': current + duration,
                             'duration': duration, 'url': urljoin(base, line)})
            current += duration
            duration = None
    chunks = HERE / 'source/chunks'
    chunks.mkdir(exist_ok=True)
    if any(line.startswith('#EXT-X-KEY') for line in lines):
        raise RuntimeError('Encrypted stream needs a separate access review')
    for candidate in json.loads((HERE / 'candidates.json').read_text()):
        if not candidate['selected_for_review']:
            continue
        name = candidate['name']
        start, end = candidate['source_window']
        chosen = [s for s in segments if s['start'] < end and s['end'] > start]
        if not chosen or chosen[0]['start'] < 7860:
            raise RuntimeError('Passage violates the requested source boundary')
        out = HERE / 'source' / (name + '.mp4')
        if out.exists():
            raise RuntimeError(f'Passage already exists; inspect before replacing: {out}')
        manifest = HERE / 'source' / (name + '.m3u8')
        body = ['#EXTM3U', '#EXT-X-VERSION:3', '#EXT-X-TARGETDURATION:12',
                '#EXT-X-PLAYLIST-TYPE:VOD', '#EXT-X-MEDIA-SEQUENCE:0']
        for segment in chosen:
            body.extend([f"#EXTINF:{segment['duration']:.6f},", segment['url']])
        body.append('#EXT-X-ENDLIST')
        manifest.write_text('\n'.join(body) + '\n', encoding='utf-8')
        concat = HERE / 'source' / (name + '.ffconcat')
        files = []
        for segment in chosen:
            index = segments.index(segment)
            local = chunks / f'{index:04d}.ts'
            if not local.exists():
                pending = local.with_suffix('.download')
                with urllib.request.urlopen(segment['url'], timeout=30) as response, pending.open('wb') as stream:
                    shutil.copyfileobj(response, stream, length=512 * 1024)
                pending.replace(local)
                print('CHUNK_DOWNLOADED', name, index, local.stat().st_size, flush=True)
            files.append(local)
        concat.write_text('ffconcat version 1.0\n' + ''.join(f"file '{p.resolve().as_posix()}'\n" for p in files), encoding='utf-8')
        subprocess.run(ffmpeg_command([
            FFMPEG, '-v', 'error', '-nostdin', '-f', 'concat', '-safe', '0', '-i', str(concat),
            '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy', '-bsf:a', 'aac_adtstoasc',
            '-movflags', '+faststart', str(out),
        ]), check=True)
        media = probe(out)
        if not media.has_audio or media.width < 720:
            raise RuntimeError('Acquired passage is not the full stream')
        receipt = {'id': name, 'path': str(out), 'original_url': brief['source_url'],
                   'source_start': round(chosen[0]['start'], 6),
                   'source_end': round(chosen[-1]['end'], 6),
                   'requested_context': [start, end], 'duration': media.duration,
                   'width': media.width, 'height': media.height,
                   'fps': media.fps, 'rate': media.rate, 'has_audio': media.has_audio,
                   'reuse_basis': brief['reuse_basis'],
                   'provenance': 'Only the selected public HLS segments; stream-copy payload, no earlier episode download'}
        (HERE / 'source' / (name + '.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        frame_folder = HERE / 'source-frames' / name
        frame_folder.mkdir(parents=True, exist_ok=True)
        times = sorted(set([0.5, max(0.5, media.duration - 0.25)] + list(range(4, int(media.duration), 8))))
        images = []
        for i, t in enumerate(times):
            image = frame_folder / f'{i:03d}.jpg'
            subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-nostdin', '-ss', str(t),
                                          '-i', str(out), '-frames:v', '1', '-vf', 'scale=640:-2', str(image)]), check=True)
            images.append(image)
        for page, offset in enumerate(range(0, len(images), 6), 1):
            group = images[offset:offset + 6]
            sheet = Image.new('RGB', (1280, 385 * ((len(group) + 1) // 2)), '#151515')
            draw = ImageDraw.Draw(sheet)
            for i, image in enumerate(group):
                x, y = i % 2 * 640, i // 2 * 385
                with Image.open(image) as im:
                    sheet.paste(im, (x, y + 25))
                draw.text((x + 5, y + 5), f"local {times[offset+i]:.2f}s / original {receipt['source_start']+times[offset+i]:.2f}s", fill='white')
            sheet.save(frame_folder / f'sheet-{page:02d}.jpg')
        print('PASSAGE_ACQUIRED', json.dumps(receipt), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
