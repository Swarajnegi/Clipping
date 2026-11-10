"""Materialize the three assistant-selected music-free edits from inspected evidence."""
import json
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
DECISIONS={
 'confidence':{
   'title':'You can doubt yourself and still be a champion',
   'pieces':[[7.28,9.70],[10.60,28.30],[29.45,36.24]],
   'payoff':'He has performed at world-champion level with doubt still present.',
   'reason':'Direct admission opens the clip; remove two long hesitations without changing the thought.',
   'cues':[
     {'source_time':7.88,'dur':0.95,'text':'FULL OF\nDOUBT.','x':75,'y':985,'size':70},
     {'source_time':30.64,'dur':1.08,'text':'BEST IN\nTHE WORLD.','x':75,'y':980,'size':65}
   ]},
 'pursuit':{
   'title':'More than my mind understands',
   'pieces':[[7.14,10.34],[11.52,34.56]],
   'payoff':'A specific difficult preparation becomes evidence that his assumed limit was wrong.',
   'reason':'Keep the injury context and complete personal realization; tighten one hesitant pause.',
   'cues':[
     {'source_time':21.40,'dur':0.82,'text':'IMPOSSIBLE.','x':70,'y':1020,'size':65},
     {'source_time':32.94,'dur':1.50,'text':'MORE THAN\nMY MIND\nUNDERSTANDS.','x':70,'y':955,'size':56,'italic':True}
   ]},
 'parenthood':{
   'title':'Your children see the real you',
   'pieces':[[7.16,28.22],[33.84,40.82],[42.80,48.56]],
   'payoff':'Public presentation cannot hide the person your children live with.',
   'reason':'Preserve hero-to-human context and responsibility; remove a hesitant clause and repeated sentence; finish at a complete sentence before the next thought.',
   'cues':[
     {'source_time':24.68,'dur':1.15,'text':'THEY SEE\nTHROUGH IT ALL.','x':70,'y':985,'size':53},
     {'source_time':39.18,'dur':0.75,'text':'FIX THEM.','x':70,'y':1020,'size':65},
     {'source_time':47.32,'dur':1.04,'text':'NO HIDING.','x':70,'y':1020,'size':68,'italic':True}
   ]}
}

def position(t,pieces):
    offset=0
    for a,b in pieces:
        if a<=t<b:return round(offset+t-a,3)
        offset+=b-a
    raise ValueError('Cue outside selected footage')

def main():
    manifest=[]
    for name,decision in DECISIONS.items():
        target=ROOT/'work'/('bumstead_20261101_'+name)
        if target.exists():raise RuntimeError('Project already staged: '+str(target))
        metadata=json.loads((HERE/'source'/(name+'.json')).read_text())
        raw=json.loads((HERE/'source'/(name+'-transcript.json')).read_text())
        corrections=[]
        for row in raw:
            for word in row['words']:
                before=word['w']
                if name=='confidence' and 34.8<=word['s']<35.1 and 'debt' in word['w']:
                    word['w']=word['w'].replace('debt','doubt')
                if name=='pursuit' and 15.4<=word['s']<15.9 and 'lab' in word['w']:
                    word['w']=word['w'].replace('lab','lat')
                if name=='parenthood' and 14<=word['s']<17.7 and word['w'].strip().lower()=='is':
                    word['w']=' as'
                if word['w']!=before:
                    corrections.append({'time':word['s'],'raw':before,'caption':word['w'],
                       'basis':'doubt: surrounding argument and repeated doubt statements; lat: original YouTube auto-caption; as perfect: visible owner reference frame f59b86fe347f/frames/0009.jpg'})
                if word['w'].rstrip().endswith(('.', '?', '!')):
                    word['pageBreakAfter']=True
        target.mkdir(parents=True)
        metadata.update(id=target.name,title=decision['title'],url=None,
                        original_url='https://www.youtube.com/watch?v=DHWEqlG7DI0',
                        source_key='Youtube:DHWEqlG7DI0',source_kind='bounded original passage')
        (target/'source.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        (target/'transcript.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
        (target/'caption-corrections.json').write_text(json.dumps(corrections,indent=2),encoding='utf-8')
        cues=[]
        for cue in decision['cues']:
            cues.append({k:v for k,v in cue.items() if k!='source_time'}|{'t':position(cue['source_time'],decision['pieces'])})
        spec={'id':target.name,'pairedExports':False,'brand':{'music':None},
              'footage_reuse_basis':metadata['reuse_basis'],
              'clips':[{'n':1,'type':'talk','segments':decision['pieces'],'trimSilence':False,
                        'intro':None,'hook':'','captions':True,'music':None,'sourceAudioDb':-2,
                        'shots':[{'t':0,'x':0.5,'w':1,'lock':True}],
                        'style':'letterbox','referenceEdit':{'profile':'kinetic','bandHeight':540,
                         'captionY':1120,'captionSize':34,'emphasis':cues},
                        'title':decision['title'],
                        'description':'Chris Bumstead in conversation with Chris Williamson, Modern Wisdom 851. '+decision['payoff'],
                        'why':decision['reason']}]}
        (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        manifest.append({'work_id':target.name,'title':decision['title'],
                         'duration':round(sum(b-a for a,b in decision['pieces']),3),
                         'source_start':metadata['source_start'],'local_segments':decision['pieces'],
                         'original_segments_approx':[[round(metadata['source_start']+a,3),round(metadata['source_start']+b,3)] for a,b in decision['pieces']],
                         'payoff':decision['payoff'],'caption_corrections':corrections})
    (HERE/'edit-decisions.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
