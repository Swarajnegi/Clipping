"""Create a short real-footage 4K proof before committing a production batch."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit
old=ROOT/'work/belmar_20261104_01-owner-lead';new=ROOT/'work/belmar_20261104_4k_sample';new.mkdir(parents=True,exist_ok=True)
for name in ('source.json','transcript.json','signals.json'):shutil.copy2(old/name,new/name)
words=[w for s in json.loads((old/'transcript.json').read_text()) for w in s['words'] if 25.4<=w['s']<30.4]
layers=[]
for i in range(0,len(words),3):
 g=words[i:i+3];t=g[0]['s']-25.4;end=min(5,max(g[-1]['e']-25.4+.08,t+.08))
 if i+3<len(words):end=min(end,words[i+3]['s']-25.4)
 end=max(end,g[-1]['s']-25.4+.04)
 layers.append(dict(t=round(t,3),dur=round(end-t,3),text=' '.join(w['w'].strip() for w in g),
  x=100,y=1280,width=880,size=106,font='inter',weight=700,tracking=-.04,align='center',shadow='strong',
  wordTimes=[round(w['s']-25.4,3) for w in g],motion=dict(inSec=.1,outSec=.05,rise=10,blur=2)))
edit=dict(profile='editorial',bandHeight=1920,palette='silver',layeredOnly=True,layers=layers)
validate_reference_edit(edit,5)
spec=dict(id=new.name,footage_reuse_basis='Owner confirmed episode covered, 4 November 2026',watermark=None,
 clips=[dict(n=1,type='talk',start=25.4,end=30.4,trimSilence=False,shots=[dict(t=0,x=.62,w=.45)],
 title='4K typography proof — not a finished clip',captions=True,style='bold',referenceEdit=edit)])
(new/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print(new/'clips.json')
