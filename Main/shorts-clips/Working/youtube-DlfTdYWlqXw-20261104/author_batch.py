"""Owner-specific edit decisions. Creates reproducible, word-timed 4K caption specs.

This is project authoring, not an automatic editorial-selection rule.
Beat divisions below were authored against the exact production transcripts.
"""
import json, re, sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import validate_reference_edit

def norm(s):
    return re.sub(r"[^a-z0-9']", '', s.lower().replace('’', "'"))

# / changes composition; | stacks supporting and emphasis rows; ^ marks emphasis.
DECISIONS = [
dict(slug='01-happiness-freedom', start=2415, segments=[[4.68,33.40],[43.40,92.48]],
 title='You Don’t Have to Feel Happy to Be Free',
 description='A difficult day doesn’t erase your freedom to choose how you live. There is room for every part of being human.\n#LukeBelmar #SelfWorth #PersonalGrowth',
 why='Owner-selected lead. Separates a passing emotion from agency, then makes room for sorrow as well as joy. Repeated good-luck aside omitted; argument and conclusion retained.',
 beats='''^Happiness | is an emotion, / so it comes | and goes, / so anybody | that's pursuing / something | that's fleeting / will not be able | to hold onto it. / Why? / Because you cannot | be a happy person / all the time. / So to pursue | happiness / is an | ^unachievable goal. / But to pursue | ^freedom, / freedom is | a state of mind, / right? / Freedom is | a state of being. / It's not | an emotion. / I can still | be sad / and be free. / I can still | be happy / and be free. / This idea | of being happy / is this concept / that people | have been sold, / right? / That life | is about happiness. / But what if life | wasn't about / ^happiness? / What if life | is about experiencing / every aspect / and every emotion | that life has? / Wouldn't you want | to experience / the full set / and range | of emotions / that life has | to offer you? / The sadness, / the heartbreaks, / the joy, | right? / You can't have | ^happiness / without sorrow. / You can't have | ^pleasure / without pain. / And to neglect | one thing / is to | ^neglect life. / So why would you | neglect these things? / And in order | for you / to achieve | ^freedom, / you need to be able | to understand / that you need | to be / unwaveringly | decided / to enjoy | every aspect / of the experience | ^of life.'''),
dict(slug='02-your-success', start=2213, segments=[[5.92,76.08]],
 title='Whose Definition of Success Are You Chasing?',
 description='Your life can mean more than meeting someone else’s expectations. Give yourself permission to decide what a meaningful life looks like.\n#LukeBelmar #Success #SelfGrowth',
 why='A direct personal question, specific alternatives and a complete agency-led payoff. Ends before the next, separate claim about psychologists.',
 beats='''What does | ^success / sound like | ^to you? / Not what success | means to me. / Not what success | means to your parents, / to your friends, / to the system. / What does | success sound / like to you? / What is your | symphony of success? / When you hear | successful, / living a | successful life, / what comes | to mind? / For a musician, / it may be | really good / playing | an instrument. / For me, / it may be | developing / a phenomenal | business. / For an athlete, / it may be | developing / a great | athletic career. / What is your | symphony of success? / It really depends | on the individual. / That's why | there is / no one spectrum | of success. / There isn't | one number / to achieve | that defines / ^success. / That is | my definition / of success, / but that is | ^for me. / Why? / Because | every person / beautifully | has been created / to have | their own / specificity. / So you have | your own dreams, / you have | your own ambitions, / you have | your own / symphony of success. / You need | to find that. / And how | do you find it? / From deprogramming, / from the bullshit / that everybody else | has told you / of what it means | to be successful. / You need to | ^stop listening / to others / and start | ^listening / ^to yourself.'''),
dict(slug='03-self-reflection', start=2701, segments=[[17.28,64.00]],
 title='Your Reaction Is Trying to Tell You Something',
 description='Before you judge yourself for a reaction, get curious about it. Understanding where it began gives you a chance to respond differently.\n#SelfAwareness #LukeBelmar #PersonalGrowth',
 why='Opens with a concrete lapse, asks why, and ends with the possibility of changing oneself. This is a speaker perspective, not a medical treatment claim.',
 beats='''You talk bad | to an employee. / You yell | at the employee. / Hmm. / Why did I | ^do that? / Where did | that come from? / Oh, I lost money | on a trade. / Why do I | feel anxious? / Why did I | feel like / I had to | place that trade? / You see somebody | driving in / a nice car. / You get | a little bit / jealous. / Why am I | ^jealous? / Where is, / where is | this feeling / coming from? / So you can | either meditate / upon things / or you can live | in a state / of meditation / whereby | you are always / ^reflecting / on who you are / and what is | being displayed / because the world | shows you / ^who you are. / If you watch | and pay attention, / why? / Because you are | a reflection of it. / So what you see | in the exterior / is a reflection / of what's | happening inside, / but you can | ^change / ^what's inside.'''),
dict(slug='04-family', start=3254, segments=[[2.80,13.84],[15.24,18.28],[18.92,27.52],[28.28,37.60]],
 title='Your Family Deserves the Person You’re Becoming',
 description='The people closest to you deserve your effort too. Being a good partner or parent is something you can keep learning.\n#Family #PersonalGrowth #LukeBelmar',
 why='Strongest match to the approved Bumstead character-at-home clip. Keeps “he said” so the quoted friend is not presented as Luke’s own biography. Only long conversational pauses are shortened.',
 beats='''And he said, / people spend | ^20,000 hours / developing their | business skills, / but they don't | spend a single hour / developing their | ^family skills. / And he's like, / isn't that | ^important? / And I'm like, / yeah, bro, / it's fucking | important. / He's like, | yeah, / so I already | put in my / ^20,000 hours / in business, / I'm gonna spend | ^20,000 hours / with my family / to develop | how to be / a good | ^husband / and how to be | a good father / and how to be | a good man. / Why? / Because he | understands / what wealth | means, / ^abundance.'''),
dict(slug='05-three-relationships', start=3676, segments=[[1.40,59.96]],
 title='Three Relationships That Keep You Growing',
 description='Find someone to learn from, someone to grow beside, and someone you can help. You don’t have to build yourself alone.\n#Mentorship #PersonalGrowth #LukeBelmar',
 why='Clear three-part practical framework. Keeps the unexpected mentee/accountability payoff and closing summary, stops before promotion.',
 beats='''I often | tell people / that every man | needs / ^three relationships / in their life. / In order | for you / to have | balanced life / as a man, / you need | three relationships. / First, / you need | ^a mentor, / somebody that | has gone the path / that you | want to go, / that can | instruct you / and take you | down the road, / avoiding | the pitfalls / and avoiding | the mistakes / and avoiding | the troubles / that come | that way. / You need | ^a peer, / somebody that is | at your level, / at your equal, / that you can | mastermind with, / that you can | build a think tank, / that you can go | back and forth / and discuss | and argue / and develop | business. / And then you need | ^a mentee, / whether it's | your young brother / or somebody | that you bring / into your business / or an employee, / somebody that | you pour / yourself into. / Why? / Because those people | keep you / ^accountable. / Those people | are the ones / that check you. / You know, / you often have | your little sibling, / he'll ask you | questions / and he'll | check you / with authenticity | and honesty / and ask you shit. / You're like, / oh, whoa, / like this kid's | paying attention, / right? / So every man | in his life / needs | ^three relationships.'''),
dict(slug='06-fisherman', start=4089, segments=[[2.16,49.48]],
 title='The Fisherman Who Already Had Enough',
 description='Ambition can move you forward. Remember to notice the love, peace and ordinary moments you already have along the way.\n#LukeBelmar #Perspective #Gratitude',
 why='Concrete fisherman/mansion contrast. Human, relatable and complete; avoids turning money into the definition of worth.',
 beats='''I have met people | that are more joyful / and enjoying life | with very little, / you know, / they go out / and they fish | for their food / every day. / I remember | in Bali, / the guy | didn't know anything / about money, / but the guy | would go, / fish his own stuff / on his little boat, / come back, / smile, / have a good time, / time pass slow, / would hang out | in the hammock. / Some people | would be like, / oh, this guy's | a bum. / He's | ^enjoying himself. / So if he's | enjoying himself / and the guy | at the mansion, / the skyscraper | is out here / scrolling | on Twitter, / feeling anxious | and bitter / and upset, / who's living | ^a better life? / Honestly speaking, / because at | some point / you have a roof | over your head, / you have food | in your mouth, / you have shelter, / you have people | ^that love you. / Everything else | is a commodity / ^and an extra.'''),
dict(slug='07-silver-thread', start=4280, segments=[[3.12,170.08]],
 title='Don’t Fast-Forward the Life You’re Building',
 description='You can want a better future without wishing today away. Even slow progress is part of a life worth being present for.\n#LukeBelmar #PersonalGrowth #BePresent',
 why='Full cautionary story earns a longer edit: school, work, marriage and parenthood lead to a present-focused payoff. No arbitrary short-runtime cut breaks the story.',
 beats=None),
]

def production_words(work):
    transcript=json.loads((work/'transcript.json').read_text(encoding='utf-8'))
    words=[]
    for seg in transcript:
        for raw in seg['words']:
            w=dict(raw);w['w']=w['w'].strip()
            # Whisper splits a written number into two tokens; keep one complete glyph run.
            if re.fullmatch(r',\d+',w['w']) and words and words[-1]['w'].isdigit():
                words[-1]['w']+=w['w'];words[-1]['e']=w['e']
            else: words.append(w)
    # Independently corroborated by source YouTube captions at 01:08:33.
    for w in words:
        if w['w'].lower()=="sky's":w['w']="guy's"
    if work.name.endswith('06-fisherman'):
        for i in range(1,len(words)):
            if words[i]['w']=="guy's" and words[i-1]['w']=='the':words[i-1]['w']='this'
    return words

def rebase(words,segments):
    result=[];off=0
    for a,b in segments:
        for w in words:
            if a<=w['s']<b:
                result.append(dict(w,w=w['w'],s=round(w['s']-a+off,3),e=round(min(w['e'],b)-a+off,3),source_s=w['s']))
        off+=b-a
    return result

def story_beats(words):
    # Narrative stays restrained between independently emphasized story turning points.
    special=['you can never go back','you can only go forward','I missed my wedding day',
             'to live in the future','live in the present','the progress that you\'ve made',
             'you have the chance','present moment','time energy and attention','pursue your goal']
    tokens=[norm(w['w']) for w in words]
    starts={}
    for phrase in special:
        seq=[norm(x) for x in phrase.split()]
        for i in range(len(tokens)-len(seq)+1):
            if tokens[i:i+len(seq)]==seq:starts[i]=len(seq)
    pages=[];i=0
    while i<len(words):
        if i in starts:
            n=starts[i];g=words[i:i+n]
            # Long key lines get a supporting row and an emphasized final row.
            split=max(1,n-3) if n>3 else 0
            rows=[(' '.join(w['w'] for w in g[:split]),False),(' '.join(w['w'] for w in g[split:]),True)] if split else [(' '.join(w['w'] for w in g),True)]
            pages.append(rows);i+=n;continue
        g=[]
        while i<len(words):
            if g and (i in starts or len(g)>=5 or len(' '.join(w['w'] for w in g)+words[i]['w'])>34):break
            g.append(words[i]);i+=1
            if re.search(r'[.!?,]$',g[-1]['w']) or (i<len(words) and words[i]['s']-g[-1]['e']>.55):break
        if len(' '.join(w['w'] for w in g))>19 and len(g)>2:
            split=min(range(1,len(g)),key=lambda j:abs(len(' '.join(w['w'] for w in g[:j]))-len(' '.join(w['w'] for w in g[j:]))))
            pages.append([(' '.join(w['w'] for w in g[:split]),False),(' '.join(w['w'] for w in g[split:]),False)])
        else:pages.append([(' '.join(w['w'] for w in g),False)])
    return pages

def authored_beats(text):
    return [[(row.strip().lstrip('^'),row.strip().startswith('^')) for row in page.split('|')] for page in text.split('/') if page.strip()]

def shots_for(decision,signals):
    # Explicit source-camera switches, individually checked in the production sheets.
    host={
     '01-happiness-freedom':[(4.56,6.04),(9.56,11.04),(30.04,31.56)],
     '02-your-success':[(0,2.56),(5.04,6.56),(71.56,72.80)],
     '03-self-reflection':[(40.04,41.56)],
     '04-family':[(14.36,15.84),(27.36,28.84)],
     '05-three-relationships':[(0,1.84),(56.84,58.36)],
     '06-fisherman':[],
     '07-silver-thread':[(84.36,85.84),(133.84,135.36),(169.84,173)]
    }[decision['slug']]
    result=[];off=0
    for a,b in decision['segments']:
        for t in [a]+[x for x in signals['cuts'] if a<x<b]:
            reaction=any(lo<=t+0.005<hi for lo,hi in host)
            result.append(dict(t=round(t-a+off,3),x=.5 if reaction else .58,w=.82 if reaction else .50,lock=True,view='hosts' if reaction else 'luke'))
        off+=b-a
    return result

def layers_for(words,pages,shots,duration):
    cursor=0;all_pages=[]
    for rows in pages:
        entries=[]
        for text,emphasis in rows:
            count=len(text.split());g=words[cursor:cursor+count]
            if [norm(w['w']) for w in g]!=[norm(x) for x in text.split()]:
                raise ValueError(f'Caption wording mismatch at {cursor}: expected {text!r}; got {[w["w"] for w in words[cursor:cursor+count+2]]}')
            entries.append((text,emphasis,g));cursor+=count
        all_pages.append(entries)
    assert cursor==len(words),(cursor,len(words),[w['w'] for w in words[cursor:]])
    layers=[];manifest=[]
    for pi,entries in enumerate(all_pages):
        first=entries[0][2][0]['s'];last=entries[-1][2][-1]['e']
        next_start=all_pages[pi+1][0][2][0]['s'] if pi+1<len(all_pages) else duration
        end=min(duration,next_start,max(last+.18,first+.42))
        end=max(end,entries[-1][2][-1]['s']+.04)
        # Split persistent word layers at camera changes; reserve the same phrase layout.
        # The caption zone changes with the camera, never crosses either face.
        # A phrase spanning a reaction cut uses the common lower safe area for its
        # entire hold. Its individual words must not jump position mid-phrase.
        switches=[first,end]
        for lo,hi in zip(switches,switches[1:]):
            view=next((s['view'] for s in reversed(shots) if s['t']<=lo+.001),'luke')
            if any(s['view']=='hosts' and lo<s['t']<hi for s in shots):view='hosts'
            ys=([1102,1210] if view=='hosts' else [1228,1346]) if len(entries)==2 else ([1172] if view=='hosts' else [1292])
            for row,(text,emphasis,g) in enumerate(entries):
                at=max(lo,g[0]['s'])
                if at>=hi:continue
                size=((108 if row==0 and len(entries)==2 else 124) if emphasis else (84 if row==0 and len(entries)==2 else 96))
                # Conservative glyph-width bound; exact settled bounds checked in rendered previews.
                size=min(size,int(850/max(.55*len(text)-.04*max(len(text)-1,0),1)))
                size=max(58,size)
                times=[round(max(at,w['s']),3) for w in g]
                layer=dict(t=round(at,3),dur=round(hi-at,3),text=text,x=88,y=ys[row],width=872,size=size,
                    font='inter',weight=800 if emphasis else 700,tracking=-.035,align='center',shadow='strong',
                    wordTimes=times,motion=dict(inSec=.12,outSec=.04,rise=11 if emphasis else 7,scaleFrom=.98,blur=2,easing='cubic'))
                if emphasis:
                    layer['gradient']='linear-gradient(175deg, #ffffff 5%, #f1f2f5 52%, #aeb6c3 100%)'
                layers.append(layer)
        manifest.append(dict(page=pi,start=first,end=round(end,3),rows=[t for t,_,_ in entries]))
    return layers,manifest

def main():
    records=[]
    for d in DECISIONS:
        work=ROOT/'work'/('belmar_20261104_4k_'+d['slug'])
        source_words=production_words(work);words=rebase(source_words,d['segments'])
        pages=authored_beats(d['beats']) if d['beats'] else story_beats(words)
        shots=shots_for(d,json.loads((work/'signals.json').read_text()))
        duration=round(sum(b-a for a,b in d['segments']),3)
        layers,manifest=layers_for(words,pages,shots,duration)
        edit=dict(profile='editorial',bandHeight=1920,palette='silver',layeredOnly=True,layers=layers)
        validate_reference_edit(edit,duration)
        clean_shots=[{k:v for k,v in s.items() if k!='view'} for s in shots]
        clip=dict(n=1,type='talk',segments=d['segments'],trimSilence=False,shots=clean_shots,
                  title=d['title'],description=d['description'],why=d['why'],captions=True,style='bold',referenceEdit=edit)
        spec=dict(id=work.name,watermark=None,footage_reuse_basis='Owner confirmed this episode covered, 4 November 2026',
                  source_url='https://www.youtube.com/watch?v=DlfTdYWlqXw',clips=[clip])
        (work/'clips.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
        author=PROJECT/'authoring'/d['slug'];author.mkdir(parents=True,exist_ok=True)
        (author/'clips.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
        (author/'caption-pages.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        record={k:v for k,v in d.items() if k!='beats'}
        record.update(duration=duration,frames=round(duration*25),work_id=work.name,shots=shots,
                      absolute_segments=[[round(d['start']+a,3),round(d['start']+b,3)] for a,b in d['segments']],
                      caption_words=len(words),caption_pages=len(manifest),output='2160x3840 @25fps; direct 4K typography')
        records.append(record)
        print(d['slug'],duration,len(words),len(layers),'layers')
    (PROJECT/'edit-decisions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
