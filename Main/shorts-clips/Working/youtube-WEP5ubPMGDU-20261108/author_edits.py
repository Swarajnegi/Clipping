"""LAYER: Editor. THE BIG PICTURE: author four owner-specific, complete short moments.
THE FLOW: reviewed speech -> exact edit spans -> individually timed caption compositions.
"""
import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit

D=[dict(slug='01-small-steps',segments=[[10.08,37.84]],
 title='Make the Next Step Small Enough to Take',
 description='You do not have to become your ideal self today. Make the next step small enough to take—and let that count.\n#JordanPeterson #PersonalGrowth #SmallSteps',
 why='A concrete response to the gap between ambition and present ability; direct practical hope without a promise of instant change.',
 views=[(0,.66,.34,'Jordan medium')],
 beats="""If you're comparing | yourself to someone / or even | to a future self, / and the gap | is so painful / that it | ^paralyzes you, / then you've | created a dragon / that you don't have | the tools to master. / And so | what you have to do / is you have to | scale the dragon / ^down to size. / And you want | to scale the dragon / down to size / until it's a size / that you are willing | ^@to move toward. / ^@However small | that is."""),
 dict(slug='02-your-own-comparison',segments=[[8.56,12.20],[21.04,45.84]],
 title='Your Fairest Comparison Is Yesterday’s You',
 description='Someone else’s progress comes with a life you have never lived. Notice where you are growing from your own starting point.\n#JordanPeterson #SelfWorth #PersonalGrowth',
 why='Self-worth and agency: preserve the explanation about unique talents, limitations and opportunities; omit a redundant, disfluent control-group aside.',
 views=[(0,.66,.34,'Jordan medium'),(3.64,.81,.34,'Jordan in wide shot'),(15.12,.66,.34,'Jordan medium')],
 beats="""The proper | ^comparison group / for you | is you / ^@yesterday. / Because you have | a certain set / of talents | and possibilities / and limitations | and tragedies / that are | ^@truly unique to you. / And so, / you might be | comparing yourself / to someone else | on some dimension, / but it's not | a reasonable comparison, / because you don't know / what talents | they were blessed with, / and you also | don't know / what opportunities | they had / that you didn't, | etc. / It's just not | ^a reasonable comparison."""),
 dict(slug='03-choose-courage',segments=[[14.00,36.84]],
 title='You Can Be Hurt and Still Choose Hope',
 description='You do not have to pretend the hurt never happened. Hope can be the courage to keep going with your eyes open.\n#JordanPeterson #Hope #Resilience',
 why='Rebuilding optimism after disappointment; the full question and answer stay together, ending before the political discussion.',
 views=[(0,.66,.34,'Jordan medium')],
 beats="""Once you've been | ^bitten hard / and you're | no longer naive, / well, that is | very hard / on your optimism, / let's say. / So then | the question is, / how do you | ^restore that / without reverting | to the naivety, / which you can't do, / anyways, / without blinding yourself / once you've | been bitten? / And the answer | to that is / you substitute | ^@courage / for naivety / and you regain | ^your optimism / as a | ^@moral imperative."""),
 dict(slug='04-unmade-decisions',segments=[[6.64,19.36],[24.48,40.16]],
 title='The Decision You Keep Avoiding Still Has a Cost',
 description='You do not need to solve your whole life today. Name one decision you have been avoiding, and take one honest step toward it.\n#ChrisWilliamson #JordanPeterson #PersonalGrowth',
 why='Chris retains his attribution to friend Alex; Peterson supplies the cost-of-avoidance payoff. Repeated agreement between turns is omitted.',
 views=[(0,.35,.34,'Chris medium'),(.48,.44,.42,'Chris close-up'),(12.72,.66,.34,'Jordan medium')],
 beats="""Right, one of | my friends Alex / has got this quote, / which I love, / and he says: / The heaviest things | in life / aren't iron and gold, / but | ^@unmade decisions. / The reason | you are stressed / is that | you have decisions / to make / and you're | ^not making them. / There's no | ^indecision, / right? / There's only... / Because you age, / like you pay | for your... / You pay | for your indecision. / It's a decision. / It's a decision | ^@to avoid, / fundamentally."""),
]

def norm(s):return re.sub(r"[^a-z0-9']",'',s.lower().replace('’',"'"))
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
records=[]
for d in D:
    slug=d['slug'];source=P/'source'/f'{slug}.mp4';work=ROOT/'work'/('peterson_20261108_'+slug);work.mkdir(parents=True,exist_ok=True)
    raw=json.loads((P/'review'/slug/'transcript.json').read_text(encoding='utf-8'))
    words=[dict(w) for s in raw for w in s['words']]
    if slug=='04-unmade-decisions':
        # ASR split the compound noun; the original YouTube captions corroborate it.
        for i in range(len(words)-1):
            if norm(words[i]['w'])=='in' and norm(words[i+1]['w'])=='decision':
                words[i]['w']='indecision,';words[i]['e']=words[i+1]['e'];words[i+1]['drop']=True
        words=[w for w in words if not w.get('drop')]
    rebased=[];off=0
    for a,b in d['segments']:
        for w in words:
            if a<=w['s']<b:rebased.append(dict(w,s=round(w['s']-a+off,3),e=round(min(w['e'],b)-a+off,3)))
        off+=b-a
    duration=round(off,3);assert 20<=duration<=40
    pages=[];cursor=0;layers=[]
    for beat in d['beats'].split('/'):
        entries=[]
        for text in beat.split('|'):
            text=text.strip();emphasis=text.startswith('^');italic='@' in text[:2];text=text.lstrip('^@')
            tokens=text.split();g=rebased[cursor:cursor+len(tokens)]
            assert [norm(x) for x in tokens]==[norm(w['w']) for w in g],(slug,text,[w['w'] for w in g],cursor)
            entries.append((text,emphasis,italic,g));cursor+=len(tokens)
        pages.append(entries)
    assert cursor==len(rebased),(slug,cursor,len(rebased))
    manifest=[]
    for pi,page in enumerate(pages):
        start=page[0][3][0]['s'];last=page[-1][3][-1]['e']
        next_start=pages[pi+1][0][3][0]['s'] if pi+1<len(pages) else duration
        end=min(duration,next_start,max(last+.24,start+.45))
        end=max(end,page[-1][3][-1]['s']+.04)
        for ri,(text,strong,italic,g) in enumerate(page):
            size=116 if strong else (86 if len(page)==2 else 98)
            if italic:size+=6
            size=min(size,int(830/max(.55*len(text)-.035*max(0,len(text)-1),1)))
            size=max(58,size)
            y=([1208,1340][ri] if len(page)==2 else 1284)
            if slug=='02-your-own-comparison':
                # One stable lower-torso zone across the medium/wide switches avoids
                # Difference's weak contrast on the mid-gray floor under the chair.
                y=([1000,1132][ri] if len(page)==2 else 1064)
            at=g[0]['s'];times=[w['s'] for w in g]
            layers.append(dict(t=at,dur=round(end-at,3),text=text,x=96,y=y,width=864,size=size,
                align='center',font='cormorant' if italic else 'inter',italic=italic,weight=700 if italic or not strong else 800,
                tracking=-.025 if italic else -.04,lineHeight=.98,wordTimes=times,surface='difference',
                color='#ffffff',blend='difference',fillOpacity=1,shadow='none',glow=0,
                motion=dict(inSec=.09,outSec=.04,rise=7,scaleFrom=.985,blur=1.2,easing='cubic')))
        manifest.append({'page':pi,'start':start,'end':end,'rows':[x[0] for x in page]})
    edit=dict(profile='editorial',bandHeight=1920,layeredOnly=True,layers=layers)
    validate_reference_edit(edit,duration)
    shots=[dict(t=t,x=x,w=w,lock=True) for t,x,w,_ in d['views']]
    clip=dict(n=1,type='talk',segments=d['segments'],trimSilence=False,shots=shots,captions=True,
        hook='',intro=None,music=None,punchIns=[],loopFadeSec=0,style='bold',referenceEdit=edit,
        title=d['title'],description=d['description'],why=d['why'])
    spec=dict(id=work.name,watermark=None,footage_reuse_basis='Owner confirmed episode covered, 8 November 2026',
        source_url='https://www.youtube.com/watch?v=WEP5ubPMGDU',brand={'music':None},clips=[clip])
    save(work/'clips.json',spec);save(work/'transcript.json',raw)
    save(work/'source.json',dict(id=work.name,path=str(source),title=d['title'],fps=25,rate='25/1',width=3840,height=1920,
        has_audio=True,duration=json.loads((P/'source-inspection.json').read_text())[int(slug[:2])-1]['duration'],
        original_url=spec['source_url'],reuse_basis=spec['footage_reuse_basis']))
    save(work/'signals.json',{'cuts':json.loads((P/'review'/slug/'cuts.json').read_text()),'seconds':[]})
    save(P/'authoring'/slug/'clips.json',spec);save(P/'authoring'/slug/'caption-pages.json',manifest)
    save(P/'authoring'/slug/'words.json',rebased)
    records.append({k:v for k,v in d.items() if k!='beats'}|{'work_id':work.name,'duration':duration,'frames':round(duration*25),
        'caption_words':len(rebased),'caption_layers':len(layers),'difference_layers':len(layers),'italic_layers':sum(l['italic'] for l in layers)})
    print(slug,duration,len(rebased),len(layers),flush=True)
save(P/'edit-decisions.json',records)
