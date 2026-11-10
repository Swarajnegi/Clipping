"""Archive the reviewed draft and improve its final caption hierarchy."""
import copy
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
vid='em117_20261101_process'
spec_path=ROOT/'work'/vid/'clips.json'
spec=json.loads(spec_path.read_text())
layers=spec['clips'][0]['referenceEdit']['layers']
old=next(layer for layer in layers if layer['text']=='THE PROCESS')
first=copy.deepcopy(old)
first.update(text='THE',size=50,wordTimes=[old['wordTimes'][0]])
second=copy.deepcopy(old)
second.update(text='PROCESS',t=old['wordTimes'][1],dur=round(old['t']+old['dur']-old['wordTimes'][1],6),
              y=1086,size=92,wordTimes=[old['wordTimes'][1]],z=43)
layers[layers.index(old):layers.index(old)+1]=[first,second]
tail=next(layer for layer in layers if layer['text']=='of going through that year.')
tail.update(y=1190,size=46)
layers.sort(key=lambda layer:(layer['t'],layer['z']))
for source,dest in [(HERE/'qa'/vid,HERE/'qa-superseded'/(vid+'-before-payoff-layout')),
                    (ROOT/'out'/vid/'clip_01.mp4',ROOT/'out'/vid/'clip_01.before-payoff-layout.mp4')]:
    for path in (source,dest):
        if not path.resolve().is_relative_to(ROOT):raise RuntimeError('Archive path outside workspace')
    if dest.exists():raise RuntimeError('Archive already exists')
    dest.parent.mkdir(parents=True,exist_ok=True)
    source.rename(dest)
spec_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
choices=json.loads((HERE/'edit-decisions.json').read_text())
next(c for c in choices if c['name']=='process')['caption_layers']=len(layers)
(HERE/'edit-decisions.json').write_text(json.dumps(choices,indent=2),encoding='utf-8')
print('Process payoff revised:',len(layers),'layers; prior draft archived')
