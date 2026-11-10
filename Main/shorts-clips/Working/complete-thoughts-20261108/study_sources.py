"""Bounded original metadata and published-caption study; no media/model download."""
import json
import sys
import hashlib
from pathlib import Path
from urllib.request import Request,urlopen
from datetime import datetime,timezone
from yt_dlp import YoutubeDL

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from moment_research import json3_segments,safe_error
from source_quality import PRODUCTION_FORMAT,PRODUCTION_SORT,compatible_4k_available

brief=json.loads((P/'brief.json').read_text(encoding='utf-8'))
for folder in ('metadata','transcripts','sources','drafts','qa'):(P/folder).mkdir(exist_ok=True)
for source in brief['sources']:
    id=source['id'];url='https://www.youtube.com/watch?v='+id
    metadata=P/'metadata'/(id+'.json');transcript=P/'transcripts'/(id+'.json')
    if metadata.exists() or transcript.exists():raise FileExistsError('Preserve study revisions: '+id)
    options=dict(quiet=True,no_warnings=True,skip_download=True,noplaylist=True,
        cachedir=str(ROOT/'.runtime/yt-dlp-cache'),remote_components={'ejs:github'},
        js_runtimes={'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
        ffmpeg_location=str(ROOT/'.runtime/ffmpeg/bin'),format=PRODUCTION_FORMAT,
        format_sort=PRODUCTION_SORT,format_sort_force=True,retries=0,extractor_retries=0,socket_timeout=25)
    with YoutubeDL(options) as ydl:info=ydl.extract_info(url,download=False)
    assert info['id']==id
    record={**source,'canonical_url':url,'title':info['title'],'channel':info.get('channel'),
        'channel_id':info.get('channel_id'),'duration':info.get('duration'),'chapters':info.get('chapters',[]),
        'compatible_4k_available':compatible_4k_available(info),
        'selected_formats':[{k:f.get(k) for k in ('format_id','width','height','fps','vcodec','acodec','language','format_note')}
                            for f in info.get('requested_formats',[])],
        'retrieved_at':datetime.now(timezone.utc).isoformat(),'reuse_basis':brief['permissions'][id]}
    metadata.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    captions={'key':'youtube:'+id,'canonical_url':url,'status':'not_checked','segments':[]}
    chosen=None
    for kind in ('subtitles','automatic_captions'):
        for language in ('en-orig','en','en-US','en-GB'):
            matches=[f for f in (info.get(kind) or {}).get(language,[]) if f.get('ext')=='json3']
            if matches:chosen=(kind,language,matches[0]);break
        if chosen:break
    if chosen:
        try:
            kind,language,item=chosen
            with urlopen(Request(item['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response:data=response.read(8_000_001)
            if len(data)>8_000_000:raise ValueError('Caption response exceeds bound')
            rows=json3_segments(json.loads(data))
            captions.update(status='available' if rows else 'empty_response',segments=rows,
                            kind=kind,language=language,sha256=hashlib.sha256(data).hexdigest())
        except Exception as e:captions.update(status='retrieval_failed',error=safe_error(e))
    else:captions['status']='none_reported' if not (info.get('subtitles') or info.get('automatic_captions')) else 'no_english_json3'
    transcript.write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
    print(id,record['channel'],'4K',record['compatible_4k_available'],captions['status'],len(captions['segments']),flush=True)
