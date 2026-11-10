"""Reuse verified QA/audio helpers and apply this project's geometry and corrections."""
import json
import shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
base=HERE.parent/'em117-20261101'
for name in ('qa_exports.py','level_dialogue.py','record_visual_review.py'):
    shutil.copy2(base/name,HERE/name)
q=HERE/'qa_exports.py'
t=q.read_text()
t=t.replace("for t in layer.get('wordTimes',[]):add(t+0.08)",
            "if layer.get('y')!=1460:\n            for t in layer.get('wordTimes',[]):add(t+0.08)")
t=t.replace('340*((len(group)+2)//3)','240*((len(group)+2)//3)').replace('index//3*340','index//3*240')
t=t.replace('im.crop((0,325,540,635))','im.crop((0,650,540,860))')
q.write_text(t,encoding='utf-8')
r=HERE/'record_visual_review.py'
t=r.read_text().replace('em117_20261101_','ronaldo_whoop_20261102_')
t=t.replace('sponsor footer excluded by crop','corner publisher marks excluded by crop/edge repair')
t=t.replace('source compression remains visible','original interview framing preserved')
t=t.replace('Silver-white captions stay off the face','Silver-white captions sit below the picture on black and stay off the face')
r.write_text(t,encoding='utf-8')
metadata=json.loads((HERE/'source/clean-final.json').read_text())
choices=json.loads((HERE/'edit-decisions.json').read_text())
for c in choices:
    work=ROOT/'work'/c['work_id']
    old=json.loads((work/'source.json').read_text())
    old.update(metadata)
    old.update(id=c['work_id'],title=c['title'],url=None)
    (work/'source.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
    c['source_crop']=metadata['source_crop']
    raw=json.loads((work/'transcript.json').read_text())
    fixes=[]
    for row in raw:
        for word in row['words']:
            if word['s']==390.68 and word['w'].strip()=="Can't":
                fixes.append(dict(source_time=390.68,original=word['w'],corrected=' can',basis='Original English captions'))
                word['w']=' can'
            if word['s']==276.38 and word['w'].strip()=='too':
                fixes.append(dict(source_time=276.38,original=word['w'],corrected=' two',basis='Original English captions'))
                word['w']=' two'
    (work/'transcript.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    f=work/'caption-corrections.json'
    corrections=json.loads(f.read_text())
    corrections.extend(fixes)
    f.write_text(json.dumps(corrections,indent=2),encoding='utf-8')
    spec=json.loads((work/'clips.json').read_text())
    for layer in spec['clips'][0]['referenceEdit']['layers']:
        if c['name']=='home':layer['text']=layer['text'].replace("Can't",'can')
        if c['name']=='talent' and layer['text']=='have too' and 10<layer['t']<12:
            layer['text']=layer['text'].replace('too','two')
    if c['name']=='home':c['caption_text']=c['caption_text'].replace("Can't",'can')
    if c['name']=='talent':c['caption_text']=c['caption_text'].replace('I have I have too','I have I have two')
    (work/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
(HERE/'edit-decisions.json').write_text(json.dumps(choices,indent=2),encoding='utf-8')
print('Project helpers, geometry and caption corrections configured')
