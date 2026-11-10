"""Acquire only the two selected original passages at the best available <=1080p."""
import json
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import probe, require_guard


def main():
    require_guard(gpu=True)
    parser=argparse.ArgumentParser()
    parser.add_argument('--quality-upgrade',action='store_true')
    args=parser.parse_args()
    import yt_dlp
    from yt_dlp.utils import download_range_func
    folder = Path(__file__).parent / ('production-source-hq' if args.quality_upgrade else 'production-source')
    folder.mkdir(exist_ok=True)
    for name, start, end in [('self_check', 3000, 3075), ('prove_yourself', 3210, 3265)]:
        destination = folder / (name + '.mp4')
        if destination.exists():
            raise RuntimeError(f'Refusing to overwrite existing source: {destination.name}')
        opts = {
            'outtmpl': str(folder / (name + '.%(ext)s')),
            'format': ('bv*[height>=720][height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height>=720][height<=1080]+ba/b[height>=720][height<=1080]' if args.quality_upgrade else 'bv*[height<=1080]+ba/b[height<=1080]'),
            'merge_output_format': 'mp4',
            'ffmpeg_location': str(ROOT / '.runtime/ffmpeg/bin'),
            'cachedir': str(ROOT/'.runtime/downloads/yt-dlp'), 'retries': 0, 'fragment_retries': 0,
            'remote_components': ['ejs:github'] if args.quality_upgrade else [],
            'extractor_retries': 0, 'socket_timeout': 20,
            'js_runtimes': {'node': {'path': str(ROOT / '.runtime/node/node.exe')}},
            'download_ranges': download_range_func(None, [(start, end)]),
            'external_downloader_args': {'ffmpeg': ['-threads', '2', '-filter_threads', '2', '-filter_complex_threads', '2']},
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info('https://www.youtube.com/watch?v=Tvqz9_aHhoQ', download=True)
        media = probe(destination)
        receipt = dict(path=str(destination), original_url=info['webpage_url'],
                       platform_id=info['id'], uploader=info.get('uploader'),
                       requested_original_offset=start, requested_end=end,
                       width=media.width, height=media.height, duration=media.duration,
                       fps=media.fps, rate=media.rate, has_audio=media.has_audio,
                       format=info.get('format_id'),
                       reuse_permission='Owner-confirmed clipping permission/campaign authorization, 2026-11-01',
                       alignment_status='Compare against inspected discovery sample before staging')
        (folder / (name + '.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
        print(json.dumps(receipt), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
