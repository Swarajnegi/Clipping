"""LAYER: Editor. THE BIG PICTURE: study existing episode captions before media work.
THE FLOW: original automatic captions -> timed reading chapters -> candidate judgement.
"""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
def save(name,value):(P/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
info=json.loads((P/'episode.info.json').read_text(encoding='utf-8'))
data=json.loads((P/'episode.en-orig.json3').read_text(encoding='utf-8'))
rows=[];words=[]
def clock(t):
    h=int(t)//3600;m=int(t)//60%60;s=int(t)%60
    return f'{h:02d}:{m:02d}:{s:02d}'
for event in data['events']:
    segs=event.get('segs',[]);text=''.join(s.get('utf8','') for s in segs).strip()
    if not text:continue
    start=event['tStartMs']/1000
    rows.append({'s':start,'text':text})
    for seg in segs:
        if seg.get('utf8','').strip():words.append({'s':start+seg.get('tOffsetMs',0)/1000,'w':seg['utf8'].strip()})
save('caption-lines.json',rows);save('caption-words.json',words)
(P/'transcript-readable.txt').write_text('\n'.join(f"[{clock(r['s'])}] {r['text']}" for r in rows),encoding='utf-8')
(P/'chapters').mkdir(exist_ok=True)
for i,ch in enumerate(info.get('chapters',[])):
    text='\n'.join(f"[{clock(r['s'])}] {r['text']}" for r in rows if ch['start_time']<=r['s']<ch['end_time'])
    (P/'chapters'/f'{i:02d}.txt').write_text(ch['title']+'\n'+text,encoding='utf-8')
save('brief.json',{'source_url':'https://www.youtube.com/watch?v=WEP5ubPMGDU','title':info['title'],
    'requested_clips':'Up to four strong moments, targeting 20–40 seconds each',
    'reuse_basis':'Owner confirmed this episode covered by clipping permission/campaign authorization, 8 November 2026',
    'output':'2160x3840 master, native source FPS, music-free, no added narration/effects/channel symbol',
    'captions':'Every word Difference white-fill; selective true italic; shot-aware placement off faces',
    'selection':'EDITORIAL_TASTE.md: self-worth, character, agency, commitment and relatable growth',
    'discovery_tool':'Existing YouTube captions; inspect original windows before approving cuts',
    'coverage':'Automatic captions prepared, not verified speech/visual review'})
print({'caption_lines':len(rows),'caption_words':len(words),'chapters':len(info.get('chapters',[])),
    'formats':[{k:f.get(k) for k in ['format_id','height','fps','vcodec','acodec','filesize_approx']} for f in info.get('formats',[]) if f.get('height',0)>=1080 and f.get('vcodec')!='none']})
