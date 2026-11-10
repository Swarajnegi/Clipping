"""Bounded metadata and caption-body retrieval; no episode video download."""
import json
import sys
from pathlib import Path
import yt_dlp
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from discover import episode,safe_error,error_status
URL='https://www.youtube.com/watch?v=kbKldiDOgEE'
folder=HERE/'captions'
folder.mkdir(exist_ok=True)
opts={'skip_download':True,'quiet':True,'retries':0,'fragment_retries':0,'extractor_retries':0,
      'ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),
      'socket_timeout':20,'cachedir':str(ROOT/'.runtime/downloads/yt-dlp'),
      'remote_components':['ejs:github'],
      'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
      'writesubtitles':True,'writeautomaticsub':True,'subtitleslangs':['en'],
      'subtitlesformat':'json3','outtmpl':str(folder/'source.%(ext)s')}
receipt={'metadata':'not_checked','caption_body':'not_checked','video_downloaded':False}
try:
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info(URL,download=False)
        (HERE/'catalogue.json').write_text(json.dumps(episode(info,URL),indent=2),encoding='utf-8')
        receipt.update(metadata='success',title=info['title'],uploader=info.get('uploader'),
                       chapters=info.get('chapters',[]),
                       picture_formats=[{'id':f['format_id'],'width':f.get('width'),'height':f.get('height'),
                           'fps':f.get('fps'),'vcodec':f.get('vcodec')} for f in info.get('formats',[]) if f.get('vcodec') not in (None,'none')])
        ydl.process_ie_result(info,download=True)
    files=list(folder.glob('*.json3'))
    receipt['caption_body']='retrieved' if files else 'none_retrieved'
    for path in files:
        raw=json.loads(path.read_text(encoding='utf-8'))
        rows=[]
        for event in raw.get('events',[]):
            text=''.join(s.get('utf8','') for s in event.get('segs',[])).strip()
            if text:
                start=event.get('tStartMs',0)/1000
                rows.append({'start':start,'end':start+event.get('dDurationMs',0)/1000,'text':text})
        (folder/'transcript.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
        (folder/'transcript.txt').write_text('\n'.join(f"{r['start']:.3f} - {r['end']:.3f}: {r['text']}" for r in rows),encoding='utf-8')
except Exception as exc:
    receipt.update(caption_body='retrieval_failed',error=safe_error(exc),access_status=error_status(str(exc)))
finally:
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('picture_formats','chapters')},indent=2))
