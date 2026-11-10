"""Preserve the diagnosed dub and restore only the original English audio track."""
import json
import subprocess
import sys
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command, probe
require_guard(gpu=True)
folder = P / 'sources'
name = '05-keep-your-own-promises'
opts = dict(quiet=True, cachedir=str(ROOT / '.runtime/yt-dlp-cache'), remote_components={'ejs:github'},
    js_runtimes={'node': {'path': str(ROOT / '.runtime/node/node.exe')}},
    format='bestaudio[ext=m4a][language=en][format_note*=original]',
    ffmpeg_location=str(ROOT / '.runtime/ffmpeg/bin'),
    outtmpl=str(folder / (name + '-original-english.m4a')),
    download_ranges=download_range_func(None, [[6163,6221]]),
    retries=0, fragment_retries=0, extractor_retries=0, socket_timeout=30)
with YoutubeDL(opts) as ydl:
    info = ydl.extract_info('https://www.youtube.com/watch?v=uHLAazKUU68', download=True)
assert info['language'] == 'en' and 'original' in info.get('format_note', '')
for suffix in ('.mp4', '-words.json', '-sheet.jpg', '-source.json'):
    src = folder / (name + suffix)
    unused = folder / (name + '-dubbed-UNUSED' + suffix)
    if unused.exists(): raise FileExistsError('Preserve repair revision')
    src.rename(unused)
dest = folder / (name + '.mp4')
subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-i', str(folder / (name + '-dubbed-UNUSED.mp4')),
    '-i', str(folder / (name + '-original-english.m4a')), '-map', '0:v:0', '-map', '1:a:0',
    '-c', 'copy', '-shortest', '-movflags', '+faststart', str(dest)]), check=True)
old = json.loads((folder / (name + '-dubbed-UNUSED-source.json')).read_text())
old['audio_repair'] = {'reason': 'Original force-sort put bitrate ahead of language; dubbed track rejected before production.',
    'format_id': info['format_id'], 'language': info['language'], 'format_note': info['format_note'],
    'preserved_rejected_asset': str(folder / (name + '-dubbed-UNUSED.mp4'))}
old['path'] = str(dest)
old['duration'] = probe(dest).duration
(folder / (name + '-source.json')).write_text(json.dumps(old, indent=2), encoding='utf-8')
print('Restored original English audio without reencoding the 4K picture.')
