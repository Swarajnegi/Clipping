"""Acquire only selected native-4K context windows; preserve source/permission records."""
import json
import sys
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, probe
from source_quality import PRODUCTION_FORMAT, PRODUCTION_SORT, compatible_4k_available, quality_record

require_guard(gpu=True)
batch = json.loads((P / 'batch.json').read_text(encoding='utf-8'))
assert batch['permission']['confirmed']
folder = P / 'sources'
folder.mkdir(exist_ok=True)
for candidate in batch['candidates']:
    id = candidate['video_id']
    assert id in batch['permission']['scope']
    name = candidate['id']
    dest = folder / (name + '.mp4')
    receipt = folder / (name + '-source.json')
    if dest.exists() or receipt.exists():
        raise FileExistsError('Preserve existing source revision: ' + name)
    url = 'https://www.youtube.com/watch?v=' + id
    settings = dict(format=PRODUCTION_FORMAT, format_sort=PRODUCTION_SORT, format_sort_force=True,
        outtmpl=str(dest), merge_output_format='mp4', cachedir=str(ROOT / '.runtime/yt-dlp-cache'), noplaylist=True,
        remote_components={'ejs:github'},
        quiet=True, socket_timeout=30, retries=0, fragment_retries=0, extractor_retries=0,
        ffmpeg_location=str(ROOT / '.runtime/ffmpeg/bin'),
        js_runtimes={'node': {'path': str(ROOT / '.runtime/node/node.exe')}},
        external_downloader_args={'ffmpeg_i': ['-threads', '2'], 'ffmpeg_o': ['-threads', '2']},
        postprocessor_args={'ffmpeg': ['-threads', '2']})
    with YoutubeDL(settings) as ydl:
        info = ydl.extract_info(url, download=False)
    if not compatible_4k_available(info):
        raise RuntimeError('Compatible native 4K not available: ' + url)
    metadata = dict(id=id, canonical_url=url, title=info.get('title'), uploader=info.get('uploader'),
        channel_id=info.get('channel_id'), requested_context=candidate['context'],
        selected_formats=[{k: f.get(k) for k in ('format_id', 'width', 'height', 'fps', 'vcodec', 'acodec', 'language', 'format_note')}
                          for f in info.get('requested_formats', [])], reuse_basis=batch['permission'],
        boundary_note='Requested context; final cuts use word alignment on actual downloaded media.')
    settings['download_ranges'] = download_range_func(None, [candidate['context']])
    with YoutubeDL(settings) as ydl:
        ydl.download([url])
    media = probe(dest)
    metadata.update(actual=quality_record(media.width, media.height, True),
        fps=media.fps, rate=media.rate, duration=media.duration, path=str(dest))
    receipt.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    if not metadata['actual']['native_4k']:
        raise RuntimeError('Actual downloaded file is not native 4K: ' + name)
    print(name, media.width, media.height, media.rate, media.duration, flush=True)
