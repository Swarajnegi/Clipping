"""Acquire and inspect the caption reference under the guard."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import FFMPEG, ffmpeg_command, probe, require_guard


def main():
    require_guard()
    import yt_dlp
    brief = json.loads((HERE / 'brief.json').read_text())
    source = HERE / 'source'
    reference = HERE / 'caption-reference'
    source.mkdir(exist_ok=True)
    reference.mkdir(exist_ok=True)
    options = {
        'outtmpl': str(reference / 'reference.%(ext)s'),
        'format': 'bestvideo[height<=1920]+bestaudio/best',
        'merge_output_format': 'mp4',
        'ffmpeg_location': str(ROOT / '.runtime/ffmpeg/bin'),
        'cachedir': False, 'retries': 0, 'fragment_retries': 0,
        'extractor_retries': 0, 'socket_timeout': 20,
        'external_downloader_args': {'ffmpeg': ['-threads', '2', '-filter_threads', '2', '-filter_complex_threads', '2']},
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(brief['caption_reference'], download=True)
    path = reference / 'reference.mp4'
    if not path.exists():
        files = [p for p in reference.iterdir() if p.suffix in ('.mp4', '.webm', '.mkv')]
        if len(files) != 1:
            raise RuntimeError('Reference download not unambiguous')
        path = files[0]
    media = probe(path)
    (reference / 'metadata.json').write_text(json.dumps({
        'canonical_url': info['webpage_url'], 'uploader': info.get('uploader'),
        'id': info['id'], 'description': info.get('description'),
        'file': str(path), 'duration': media.duration, 'fps': media.fps,
        'width': media.width, 'height': media.height,
        'use': 'Caption reference inspection only; no assets copied into production',
    }, indent=2), encoding='utf-8')
    frames = reference / 'frames'
    frames.mkdir(exist_ok=True)
    subprocess.run(ffmpeg_command([
        FFMPEG, '-v', 'error', '-nostdin', '-i', str(path), '-vf', 'fps=4,scale=360:-2',
        str(frames / '%04d.jpg'),
    ]), check=True)
    from PIL import Image, ImageDraw
    images = sorted(frames.glob('*.jpg'))
    for number, start in enumerate(range(0, len(images), 12), 1):
        group = images[start:start + 12]
        sheet = Image.new('RGB', (1440, 666 * ((len(group) + 3) // 4)), '#151515')
        draw = ImageDraw.Draw(sheet)
        for i, frame in enumerate(group):
            x, y = (i % 4) * 360, (i // 4) * 666
            with Image.open(frame) as im:
                sheet.paste(im, (x, y + 25))
            draw.text((x + 5, y + 5), f'{(start + i) / 4:.2f}s', fill='white')
        sheet.save(reference / f'sheet-{number:02d}.jpg')
    print('REFERENCE_READY', media.duration, len(images), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
