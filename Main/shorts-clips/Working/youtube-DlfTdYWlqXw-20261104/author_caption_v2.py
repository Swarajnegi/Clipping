"""Owner-requested caption-only revision; original edits and dialogue stay intact."""
import copy, hashlib, json, shutil, sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
REV=PROJECT/'caption-v2'
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit

# Selective editorial accents, authored against the existing words, not randomized.
ACCENTS={
 '01-happiness-freedom': {
  'italic': ['happiness','be sad','the heartbreaks,','without sorrow.','of life.'],
  'difference': ['Happiness','unachievable goal.','freedom,','happiness?','happiness','pleasure','neglect life.','of life.']},
 '02-your-success': {
  'italic': ['to you?','your own dreams,','your own ambitions,','to yourself.'],
  'difference': ['success','success.','symphony of success?','for me.','stop listening','listening','to yourself.']},
 '03-self-reflection': {
  'italic': ['do that?','jealous?','happening inside,'],
  'difference': ['do that?','jealous?','reflecting','who you are.','change',"what's inside."]},
 '04-family': {
  'italic': ['husband','a good man.','abundance.'],
  'difference': ['20,000 hours','family skills.','important?','husband','a good father','abundance.']},
 '05-three-relationships': {
  'italic': ['a mentor,','a peer,','a mentee,','accountable.'],
  'difference': ['three relationships','three relationships.','a mentor,','a peer,','a mentee,','accountable.','with authenticity','and honesty']},
 '06-fisherman': {
  'italic': ['with very little,','enjoying himself.','a better life?'],
  'difference': ['more joyful','with very little,','smile,','enjoying himself.','feeling anxious','a better life?','that love you.','and an extra.']},
 '07-silver-thread': {
  'italic': ['silver thread.','summertime.','my wedding day.','fast forward','in the present','time,'],
  'difference': ['silver thread.','never go back.','only go forward.','summertime.','University.','married.','my wedding day.','fast forward','in the present','fucking alive','have the chance','pursue your goal.']},
}

def main():
    REV.mkdir(exist_ok=True)
    assets=ROOT/'.agents/skills/viral-shorts/assets/fonts'
    provenance=json.loads((assets/'provenance.json').read_text())
    sources={
      'InterVariable-Italic.woff2':'https://raw.githubusercontent.com/rsms/inter/master/docs/font-files/InterVariable-Italic.woff2',
      'CormorantGaramond-Italic.ttf':'https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/CormorantGaramond-Italic%5Bwght%5D.ttf',
      'Cormorant-OFL.txt':'https://raw.githubusercontent.com/google/fonts/main/ofl/cormorantgaramond/OFL.txt'}
    for name,url in sources.items():
        data=(assets/name).read_bytes()
        provenance[name]=dict(url=url,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    (assets/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    for name in ['InterVariable.woff2','InterVariable-Italic.woff2','CormorantGaramond-Italic.ttf','Cormorant-OFL.txt']:
        shutil.copy2(assets/name,ROOT/'public/fonts'/name)
    decisions=json.loads((PROJECT/'edit-decisions.json').read_text(encoding='utf-8'))
    records=[]
    for decision in decisions:
        slug=decision['slug'];target=REV/'authoring'/slug;target.mkdir(parents=True,exist_ok=True)
        old=json.loads((ROOT/'work'/decision['work_id']/'props/clip_01.json').read_text(encoding='utf-8'))
        props=copy.deepcopy(old);changes=[]
        for i,layer in enumerate(props['referenceEdit']['layers']):
            italic=layer['text'] in ACCENTS[slug]['italic']
            difference=layer['text'] in ACCENTS[slug]['difference']
            if italic:
                layer.update(font='cormorant',italic=True,weight=700,tracking=-.025)
            if difference:
                for key in ['gradient','color','blend']: layer.pop(key,None)
                layer.update(surface='difference',fillOpacity=1,shadow='none',glow=0)
            if italic or difference:
                changes.append(dict(index=i,text=layer['text'],t=layer['t'],dur=layer['dur'],italic=italic,difference=difference))
        validate_reference_edit(props['referenceEdit'],props['durationSec'])
        # Only the text-layer styling is authorized to change.
        assert {k:v for k,v in old.items() if k!='referenceEdit'}=={k:v for k,v in props.items() if k!='referenceEdit'}
        for before,after in zip(old['referenceEdit']['layers'],props['referenceEdit']['layers']):
            for key in ['t','dur','text','wordTimes','x','y','width','size','motion','depth']:
                assert before.get(key)==after.get(key),(slug,key)
        (target/'props.json').write_text(json.dumps(props,indent=2),encoding='utf-8')
        shutil.copy2(PROJECT/'authoring'/slug/'caption-pages.json',target/'caption-pages.json')
        spec=json.loads((ROOT/'work'/decision['work_id']/'clips.json').read_text(encoding='utf-8'))
        spec['clips'][0]['referenceEdit']=props['referenceEdit']
        (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        records.append(dict(slug=slug,changes=changes,italic_layers=sum(c['italic'] for c in changes),
                            difference_layers=sum(c['difference'] for c in changes)))
    (REV/'edit-decisions.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')
    (REV/'caption-changes.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    (REV/'qa').mkdir(exist_ok=True)
    print(json.dumps([{k:v for k,v in r.items() if k!='changes'} for r in records],indent=2))
if __name__=='__main__':main()
