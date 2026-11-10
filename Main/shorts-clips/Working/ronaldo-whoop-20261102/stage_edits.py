"""Seven source-verified arguments, exact word timing and authored silver captions."""
import copy
import json
import re
from pathlib import Path
from PIL import ImageFont
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DECISIONS={
 'map':{'title':'Everyone wants to be Cristiano','pieces':[[620.52,633.44]],
  'payoff':'Discipline is the difficult part, in sport and in life.',
  'why':'Direct challenge matching the Ronaldo taste reference; keep the complete map question and conclusion.'},
 'gym':{'title':'You will not feel like doing it every day',
  'pieces':[[698.08,702.52],[704.48,714.24],[718.64,729.44],[730.40,738.72],[739.28,754.56],[755.52,764.80],[768.00,778.88]],
  'payoff':'Starting can be hard; after finishing you feel better.',
  'why':'Keep the low-motivation question, honest admission, challenge and gym example; remove an unclear repeated clause, long pauses and redundant ending.'},
 'home':{'title':'Leaving home at eleven','pieces':[[364.16,368.84],[369.72,400.20],[400.68,405.44]],
  'payoff':'He now imagines how hard it would be to let his own son leave.',
  'why':'Concrete sacrifice and the present-day parent perspective form a complete personal story.'},
 'lions':{'title':'The young lions are coming',
  'pieces':[[416.84,421.20],[421.76,429.12],[429.96,435.20],[435.84,465.80],[466.92,475.32],[476.28,478.80]],
  'payoff':'Preparing physically and mentally keeps him motivated to compete.',
  'why':'Keep the younger challengers, preparation and longevity payoff; remove empty pauses and one repeated it is.'},
 'talent':{'title':'Talent without work is nothing',
  'pieces':[[265.04,272.84],[273.68,281.76],[282.40,284.40],[285.24,294.80],[295.28,306.48],[307.20,320.56],[321.04,325.88]],
  'payoff':'His argument is for both talent and work ethic, sustained over twenty years.',
  'why':'Preserve both halves of the argument and his complete motivation; avoid presenting a false talent-versus-work choice.'},
 'breath':{'title':'The breath before the penalty',
  'pieces':[[1068.24,1084.40],[1086.00,1091.72],[1091.92,1101.28],[1102.48,1105.44]],
  'payoff':'He rehearses the routine in training so it becomes a habit.',
  'why':'Retain the host question to establish the ritual, then Ronaldo explains his own practiced routine.'},
 'visualize':{'title':'Be ready before the moment arrives',
  'pieces':[[1001.44,1008.68],[1009.24,1018.56],[1019.56,1033.56],[1040.36,1066.32]],
  'payoff':'Visualizing the moment makes him feel more prepared.',
  'why':'Keep the visualization question, examples and preparation payoff. Remove the host suggestion that seeing events makes them come true; preserve Ronaldo personal account.'}
}


def normal(text):return re.sub(r"[^a-z0-9']",'',text.lower())


def main():
    metadata=json.loads((HERE/'source/clean-final.json').read_text())
    original=json.loads((HERE/'source/transcript.json').read_text())
    brief=json.loads((HERE/'brief.json').read_text())
    if not brief.get('permission_confirmed'):raise RuntimeError('Reuse basis not confirmed')
    manifests=[]
    for name,decision in DECISIONS.items():
        target=ROOT/'work'/('ronaldo_whoop_20261102_'+name)
        if target.exists():raise RuntimeError('Preserve existing staged edit: '+name)
        raw=copy.deepcopy(original)
        corrections=[]
        for row in raw:
            for word in row['words']:
                if 416.8<=word['s']<417.5 and word['w'].strip().lower()=='live':
                    corrections.append({'source_time':word['s'],'from':word['w'],'to':' Life',
                        'basis':'Original English automatic captions read life; noun in the complete box of surprises phrase.'})
                    word['w']=' Life'
                if word['s']==390.68 and word['w'].strip()=="Can't":
                    corrections.append({'source_time':390.68,'from':word['w'],'to':' can',
                        'basis':'Original English captions: I can see now my kids; CUDA negation is a recognition error.'})
                    word['w']=' can'
                if word['s']==276.38 and word['w'].strip()=='too':
                    corrections.append({'source_time':276.38,'from':word['w'],'to':' two',
                        'basis':'Original English captions say two; he refers to having both talent and work ethic.'})
                    word['w']=' two'
        words=[w for row in raw for w in row['words']]
        selected=[]
        elapsed=0
        for piece,(a,b) in enumerate(decision['pieces']):
            if not 0<=a<b<=metadata['duration']:raise RuntimeError('Invalid source range')
            for w in words:
                if w['e']<=a or w['s']>=b:continue
                # Preserve full positive short words; reject tiny seam overlaps
                # from a word whose main duration lies outside the selection.
                overlap=min(w['e'],b)-max(w['s'],a)
                if overlap<=0 or (overlap<.025 and not a<=w['s']<w['e']<=b):continue
                selected.append({**w,'piece_index':piece,'t':round(max(a,w['s'])-a+elapsed,6),
                                 'end':round(min(b,w['e'])-a+elapsed,6)})
            elapsed+=b-a
        duration=round(elapsed,6)
        if not 10<=duration<=100:raise RuntimeError('Duration outside project contract')
        # Do not normalize the speaker's vocabulary or grammar.
        if selected[-1]['w'].strip()[-1] not in '.?!':
            selected[-1]['w']+='.'
            for row in raw:
                for w in row['words']:
                    if w['s']==selected[-1]['s'] and w['e']==selected[-1]['e']:w['w']=selected[-1]['w']
        normalized=[normal(w['w']) for w in selected]
        layers=[]
        blocked=set()

        def line(items,text,y,size,italic=False,weight=700,end=None):
            font='C:/Windows/Fonts/'+('arialbi.ttf' if italic and weight>=700 else 'ariali.ttf' if italic else 'arialbd.ttf')
            while ImageFont.truetype(font,size).getlength(text)>820:size-=1
            at=items[0]['t']
            until=end if end is not None else min(duration,items[-1]['end']+.2)
            if until<=items[-1]['t']:raise RuntimeError('Invalid caption interval')
            layers.append({'t':at,'dur':round(until-at,6),'text':text,'x':100,'y':y,'width':840,
                'size':size,'font':'sans','italic':italic,'weight':weight,'align':'center','z':len(layers)+1,
                'wordTimes':[w['t'] for w in items]})

        def cue(phrase,designs,after=0):
            needle=[normal(x) for x in phrase.split()]
            found=next((i for i in range(len(selected)-len(needle)+1)
                if selected[i]['s']>=after and normalized[i:i+len(needle)]==needle
                and selected[i]['piece_index']==selected[i+len(needle)-1]['piece_index']),None)
            if found is None:raise RuntimeError('Unaligned emphasis: '+name+' / '+phrase)
            indices=set(range(found,found+len(needle)))
            if indices&blocked:raise RuntimeError('Overlapping emphasis')
            blocked.update(indices)
            group=selected[found:found+len(needle)]
            end=min(duration,group[-1]['end']+.24)
            if found+len(needle)<len(selected):end=min(end,selected[found+len(needle)]['t'])
            cursor=0
            for text,y,size,italic,weight in designs:
                count=len(text.split())
                items=group[cursor:cursor+count]
                if [normal(x) for x in text.split()]!=[normal(w['w']) for w in items]:raise RuntimeError('Caption text mismatch')
                line(items,text,y,size,italic,weight,end)
                cursor+=count
            if cursor!=len(group):raise RuntimeError('Incomplete emphasis phrase')

        if name=='map':
            cue('everyone wants to be Cristiano',[('everyone wants',1410,54,True,400),('to be CRISTIANO',1490,84,False,700)])
            cue('the discipline is the most difficult thing',[('the discipline',1410,62,True,400),('is the most difficult thing',1490,64,False,700)])
        elif name=='gym':
            cue('I fight against my mind',[('I fight against',1410,54,True,400),('MY MIND',1490,96,False,700)])
            cue('you have to do it',[('you have to',1410,56,False,700),('DO IT.',1490,102,False,700)])
            cue('mental strength',[('MENTAL STRENGTH',1450,84,False,700)])
            cue('you will feel better',[('you will',1410,54,True,400),('FEEL BETTER.',1490,90,False,700)])
        elif name=='home':
            cue('11 years old',[('11',1410,100,False,700),('years old',1520,60,True,400)])
            cue('follow my dream',[('follow',1410,56,True,400),('MY DREAM',1490,92,False,700)])
            cue('tough',[('TOUGH.',1450,96,False,700)])
        elif name=='lions':
            cue('Young Lions',[('Young',1410,56,True,400),('LIONS',1490,100,False,700)])
            cue('physically but mentally too',[('physically',1410,64,False,700),('but mentally too',1490,72,True,400)])
            cue('motivation to carry on',[('motivation to',1410,56,True,400),('CARRY ON.',1490,94,False,700)])
        elif name=='talent':
            cue('Talent without work is nothing',[('Talent without work',1410,54,True,400),('IS NOTHING',1490,92,False,700)])
            cue('work without talent is nothing too',[('work without talent',1410,54,False,700),('is nothing too.',1490,80,True,400)])
            cue('top for 20 years',[('top for',1410,54,True,400),('20 YEARS',1490,96,False,700)])
            cue('both talent and work ethic',[('both talent',1410,66,False,700),('and work ethic.',1490,72,True,400)])
        elif name=='breath':
            cue('calm',[('CALM.',1450,96,False,700)])
            cue('I do it even in a training',[('I do it even',1410,56,True,400),('in a training.',1490,76,False,700)])
            cue('become a habit',[('become',1410,54,True,400),('A HABIT',1490,96,False,700)])
        elif name=='visualize':
            cue('visualize a few points',[('visualize',1410,62,True,400),('a few points',1490,86,False,700)])
            cue('you will be more prepared for that moment',[('you will be more',1410,54,True,400),('prepared for that moment.',1490,74,False,700)])
        i=0
        while i<len(selected):
            if i in blocked:i+=1;continue
            group=[selected[i]]
            j=i+1
            while j<len(selected) and j not in blocked and len(group)<3:
                prev,nxt=group[-1],selected[j]
                if (nxt['piece_index']!=prev['piece_index'] or nxt['t']-prev['end']>.35
                    or prev['w'].rstrip().endswith(('.','?','!')) or nxt['end']-group[0]['t']>1.2
                    or len(' '.join(w['w'].strip() for w in group+[nxt]))>26):break
                group.append(nxt);j+=1
            end=min(duration,group[-1]['end']+.2)
            if j<len(selected):end=min(end,selected[j]['t'])
            line(group,' '.join(w['w'].strip() for w in group),1460,62,end=end)
            i=j
        layers.sort(key=lambda layer:(layer['t'],layer['z']))
        target.mkdir(parents=True)
        meta={**metadata,'id':target.name,'title':decision['title'],'url':None}
        (target/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        (target/'transcript.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
        (target/'caption-corrections.json').write_text(json.dumps(corrections,indent=2),encoding='utf-8')
        clip={'n':1,'type':'talk','segments':decision['pieces'],'trimSilence':False,'intro':None,'hook':'',
              'captions':True,'music':None,'sourceAudioDb':-2,'style':'letterbox',
              'shots':[{'t':0,'x':.5,'w':1,'lock':True}],
              'referenceEdit':{'profile':'kinetic','bandHeight':846,'captionY':1460,'captionSize':62,
                 'palette':'silver','wordReveal':True,'layeredOnly':True,'layers':layers,'emphasis':[]},
              'title':decision['title'],'description':'Cristiano Ronaldo with Will Ahmed, WHOOP Podcast 272. '+decision['payoff'],
              'why':decision['why']}
        spec={'id':target.name,'pairedExports':False,'brand':{'music':None},
              'footage_reuse_basis':brief['reuse_basis'],'branding':'Own channel; no overlaid symbol or reference assets.',
              'clips':[clip]}
        (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        manifests.append({'name':name,'work_id':target.name,**decision,'duration':duration,'caption_layers':len(layers),
            'caption_text':' '.join(w['w'].strip() for w in selected),'source_fps':25,'source_crop':metadata['source_crop']})
        print('STAGED',name,duration,len(layers),flush=True)
    (HERE/'edit-decisions.json').write_text(json.dumps(manifests,indent=2),encoding='utf-8')


if __name__=='__main__':main()
