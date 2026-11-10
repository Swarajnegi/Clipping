"""Guarded acquisition of five original 4K context windows, without whole episodes."""
import json,sys
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,probe
from source_quality import PRODUCTION_FORMAT,PRODUCTION_SORT,quality_record
require_guard(gpu=True)
brief=json.loads((P/'brief.json').read_text())
for c in json.loads((P/'candidates.json').read_text()):
    id=c['id'];video=c['video_id'];dest=P/'sources'/(id+'.mp4');receipt=P/'sources'/(id+'-source.json')
    if dest.exists() or receipt.exists():raise FileExistsError('Preserve existing source revision: '+id)
    meta=json.loads((P/'metadata'/(video+'.json')).read_text())
    assert meta['compatible_4k_available'] and brief['permissions'][video]
    opts=dict(quiet=True,cachedir=str(ROOT/'.runtime/yt-dlp-cache'),remote_components={'ejs:github'},
        js_runtimes={'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
        format=PRODUCTION_FORMAT,format_sort=PRODUCTION_SORT,format_sort_force=True,
        ffmpeg_location=str(ROOT/'.runtime/ffmpeg/bin'),outtmpl=str(dest),merge_output_format='mp4',
        download_ranges=download_range_func(None,[c['context']]),retries=0,fragment_retries=0,extractor_retries=0,
        socket_timeout=30,external_downloader_args={'ffmpeg_i':['-threads','2'],'ffmpeg_o':['-threads','2']},
        postprocessor_args={'ffmpeg':['-threads','2']})
    with YoutubeDL(opts) as ydl:info=ydl.extract_info(meta['canonical_url'],download=True)
    media=probe(dest)
    quality=quality_record(media.width,media.height,True)
    actual_audio=[f for f in info.get('requested_formats',[]) if f.get('vcodec')=='none']
    if actual_audio and actual_audio[0].get('language') not in (None,'en','en-US','en-GB','en-orig'):
        raise RuntimeError('Wrong original dialogue language: '+id)
    record={**meta,'requested_context':c['context'],'actual':quality,'fps':media.fps,'rate':media.rate,
        'duration':media.duration,'path':str(dest),'downloaded_audio':[{k:f.get(k) for k in ('format_id','language','format_note','acodec')} for f in actual_audio],
        'timestamp_note':'Source requested range recorded; frame/word-accurate local cuts are authored against the actual downloaded media.'}
    receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    if not quality['native_4k']:raise RuntimeError('Actual file below 4K: '+id)
    print('SOURCE',id,media.width,media.height,media.rate,media.duration,flush=True)
