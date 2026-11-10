"""Prepare editable drafts; machine captions still need human audio verification."""
from pathlib import Path
import json, re, sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit

PROJECT=Path(__file__).resolve().parent
CONFIG=[
 (1,17.08,63.60,'Commit fully',[(0,.70),(4.00,.56),(12.32,.70),(37.00,.83)]),
 (2,38.48,102.00,'Notice your successes',[(0,.70),(26.40,.70),(44.32,.37)]),
 (4,29.30,69.40,'Relevant for what?',[(0,.70),(14.86,.68),(34.14,.68)]),
]
for n,start,end,title,shots in CONFIG:
    wid=f'matthew_20261103_{n:02d}'; folder=ROOT/'work'/wid
    words=[w for seg in json.loads((folder/'transcript.json').read_text(encoding='utf-8')) for w in seg['words'] if w['s']>=start and w['e']<=end]
    # Both auto-caption sources remain provisional. The YouTube captions read
    # "win" here while local Whisper produced "when"; check against audio.
    if n == 4:
        words=[dict(w,w=' win') if w['w'].strip().lower()=='when' and 50 < w['s'] < 56 else w for w in words]
    if n == 2:
        words=[dict(w,w=' reason,') if w['w'].strip().lower()=='reasoning,' and 59 < w['s'] < 60 else w for w in words]
    if n == 1:
        # YouTube auto-captions say "would" where Whisper says "thought it".
        # This tentative substitution still requires listening before delivery.
        words=[dict(w,w=' would',e=33.25) if w['w'].strip()=='thought' and 32 < w['s'] < 34 else w
          for w in words if not (w['w'].strip()=='it' and 33.0 < w['s'] < 33.2)]
    groups=[]; current=[]
    for w in words:
        clean=w['w'].strip()
        if not clean: continue
        if clean.startswith('-') and current:
            current[-1]=dict(current[-1],w=current[-1]['w'].rstrip()+clean,e=w['e'])
            continue
        max_words,max_chars=(2,10) if n in (1,4) else (2,12)
        if current and (len(current)>=max_words or sum(len(v['w'].strip()) for v in current)+len(clean)>max_chars or w['s']-current[-1]['e']>.45 or re.search(r'[.!?]$',current[-1]['w'])):
            groups.append(current); current=[]
        current.append(w)
    if current: groups.append(current)
    layers=[]
    for i,g in enumerate(groups):
        t=max(0,round(g[0]['s']-start,3))
        pair_end=groups[i+1][-1]['e'] if i%2==0 and i+1<len(groups) and groups[i+1][0]['s']-g[-1]['e']<.5 else g[-1]['e']
        finish=min(end-start,round(pair_end-start+.10,3))
        next_pair=i+1 if i%2 else i+2
        if next_pair<len(groups): finish=min(finish,max(t+.04,round(groups[next_pair][0]['s']-start,3)))
        times=[max(t,round(w['s']-start,3)) for w in g]
        finish=max(finish,max(times)+.04)
        text=' '.join(w['w'].strip() for w in g)
        size=117 if len(text)<12 else 101
        close_up=(n==4 and 14.70 <= t < 34.20) or (n==1 and 3.85 <= t < 12.45) or n==2
        left_side=n in (1,4) and not close_up
        base_y=1300 if close_up else 810 if left_side else 1050
        left_size=min(76,max(48,int(740/max(len(text),1))))
        layers.append(dict(t=t,dur=round(finish-t,3),text=text,x=45 if left_side else 100,y=base_y+(0 if i%2==0 else 125),width=440 if left_side else 880,size=left_size if left_side else size,
          font='inter',weight=700,tracking=-.04,align='left' if left_side else 'center',shadow='strong',wordTimes=times,
          motion=dict(inSec=.08,outSec=.05,rise=12,scaleFrom=.97,blur=2,easing='cubic')))
    edit=dict(profile='editorial',bandHeight=1920,palette='silver',layeredOnly=True,wordReveal=True,layers=layers)
    validate_reference_edit(edit,end-start)
    spec=dict(id=wid,footage_reuse_basis='Owner confirmed clipping permission or campaign authorization for this episode, 3 November 2026',
      brand=dict(style='bold'),watermark=None,clips=[dict(n=1,type='talk',start=start,end=end,trimSilence=False,
      captions=True,shots=[dict(t=t,x=(.65 if n==4 else (.53 if 3.85<=t<12.30 else .75 if t>=12.30 else .65)) if n in (1,4) else x,w=.40) for t,x in shots],style='bold',referenceEdit=edit,
      title=title,description='',why='A self-contained passage about personal growth.')])
    (folder/'clips.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
    print(wid,title,round(end-start,2),len(layers),'machine-caption layers, unverified')
