"""One metadata and caption-body attempt; never download episode video."""
import json
from pathlib import Path
import yt_dlp

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
opts={'skip_download':True,'quiet':True,'retries':0,'fragment_retries':0,'extractor_retries':0,
      'ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),
      'socket_timeout':20,'cachedir':str(ROOT/'.runtime/downloads/yt-dlp'),
      'remote_components':['ejs:github'],
      'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
      'writesubtitles':True,'writeautomaticsub':True,'subtitleslangs':['en'],
      'subtitlesformat':'json3','outtmpl':str(HERE/'captions/source.%(ext)s')}
HERE.joinpath('captions').mkdir(exist_ok=True)
receipt={'metadata':'not_checked','caption_body':'not_checked','video_downloaded':False}
try:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info('https://www.youtube.com/watch?v=DHWEqlG7DI0',download=True)
    receipt.update(metadata='success',title=info['title'],uploader=info.get('uploader'),
                   caption_languages=list(info.get('subtitles',{})),
                   automatic_caption_languages=list(info.get('automatic_captions',{})),
                   chapters=info.get('chapters',[]),
                   picture_formats=[{'id':f['format_id'],'width':f.get('width'),'height':f.get('height'),'vcodec':f.get('vcodec')} for f in info.get('formats',[]) if f.get('vcodec') not in (None,'none')])
    files=list((HERE/'captions').glob('*.json3'))
    receipt['caption_body']='retrieved' if files else 'none_retrieved'
    for path in files:
        raw=json.loads(path.read_text(encoding='utf-8'))
        rows=[]
        for event in raw.get('events',[]):
            text=''.join(s.get('utf8','') for s in event.get('segs',[])).strip()
            if text:
                start=event.get('tStartMs',0)/1000
                rows.append({'start':start,'end':start+event.get('dDurationMs',0)/1000,'text':text})
        (HERE/'captions/transcript.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
except Exception as exc:
    receipt['caption_body']='retrieval_failed'
    receipt['error']=str(exc)
finally:
    (HERE/'captions/receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('automatic_caption_languages','picture_formats','chapters')},indent=2))
