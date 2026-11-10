"""Authored phrase compositions, source-word timing and bundled licensed type."""
import json
import re
import shutil
import sys
from pathlib import Path
from PIL import ImageFont
from functools import lru_cache

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import validate_reference_edit

phrases = {
'01-actions-not-thoughts': ['Judge yourself','by your actions','not by your thoughts','I became significantly',
    'less disappointed in myself','when I started judging myself','only on the actions I took','not the thoughts I had'],
'02-permission-to-change': ['Do I have your permission','to change what I want','and I think we should all',
    'have permission to change','what we want','in any given moment','and not having basically','sunk life bias',
    'of like I put 10 years','into this thing',"and that's okay","and that's what I needed to do",'at that time',
    "and today I'm gonna change everything"],
'03-hiding-your-real-self': ["I think I'm lonely","Like I've got in my journal",'on my phone',
    'multiple entries throughout my 20s','That was all I put',"because I just didn't really understand",
    "but I wasn't resonating with people",'and that was almost exclusively my fault',
    "because I wasn't being my true self right"],
'04-choose-your-regret': ['If regrets are inevitable',"if they're going to happen",'no matter what',
    'an easy way to look','at the decision is','rather than which do I want to do','which regret could I live with'],
'05-keep-your-own-promises': ['Are you who you say you are','confidence in yourself is just',
    'a combination and a culmination','of the commitments you kept to yourself','and what you proved to yourself',
    'about yourself','And to build it up in small ways',"You're talking about building character",
    "I'm going to make that promise to myself","and then I'm going to do it",'Pick something that you can do','Pick something small']}
accent = {'01-actions-not-thoughts':'thoughts','02-permission-to-change':'want',
          '03-hiding-your-real-self':'lonely','04-choose-your-regret':'inevitable',
          '05-keep-your-own-promises':'small'}
fonts = ROOT / '.agents/skills/viral-shorts/assets/fonts'
public = ROOT / 'public/fonts'
public.mkdir(exist_ok=True)
for src, dest in [('InterVariable.woff2','InterVariable.woff2'), ('LICENSE.txt','Inter-LICENSE.txt'),
                  ('CormorantGaramond-Italic.ttf','CormorantGaramond-Italic.ttf'),('Cormorant-OFL.txt','Cormorant-OFL.txt')]:
    shutil.copy2(fonts / src, public / dest)
@lru_cache(maxsize=64)
def font_at(name,size):
    file = 'InterVariable.woff2' if name=='inter' else 'CormorantGaramond-Italic.ttf'
    f = ImageFont.truetype(str(fonts/file),round(size*10))
    try:
        axes=f.get_variation_axes()
        f.set_variation_by_axes([700 if axis['name']==b'Weight' else min(32,axis['maximum'])
            if axis['name']==b'Optical Size' else axis['default'] for axis in axes])
    except OSError: pass
    return f

def norm(text): return re.sub(r'[^a-z0-9]', '', text.lower())
def width(text, size, font):
    return font_at(font,size).getlength(text)/10 - max(0,len(text)-1)*.035*size

for id, groups in phrases.items():
    record = json.loads((P / 'drafts' / (id + '-edit.json')).read_text())
    props = json.loads((P / 'props' / (id + '-base.json')).read_text())
    words = record['words']
    authored = []
    cursor = 0
    accented = False
    for group_index, text in enumerate(groups):
        tokens = text.split()
        group = words[cursor:cursor+len(tokens)]
        if [norm(t) for t in tokens] != [norm(w['w']) for w in group]:
            raise ValueError(f'{id} phrase mismatch at {cursor}: {tokens} / {[w["w"] for w in group]}')
        cursor += len(tokens)
        end = min(record['duration'], words[cursor]['s'] if cursor < len(words) else record['duration'])
        # Reserve the final word positions before any word arrives.
        sizes = [64 if group_index == 0 else 57] * len(group)
        faces = ['inter'] * len(group)
        for i,w in enumerate(group):
            if not accented and norm(w['w']) == accent[id]:
                faces[i] = 'cormorant'; sizes[i] += 12; accented = True
        widths = [width(w['w'], sizes[i], faces[i])+8 for i,w in enumerate(group)]
        # Balanced two-line composition where a phrase is long; short clauses remain one line.
        if sum(widths) + 14*(len(group)-1) <= 810 and len(group)<=4:
            lines = [list(range(len(group)))]
        else:
            split = min(range(1,len(group)), key=lambda k:abs(sum(widths[:k])-sum(widths[k:])))
            lines = [list(range(split)),list(range(split,len(group)))]
        for line_index, line in enumerate(lines):
            gap = 12
            total = sum(widths[i] for i in line) + gap*(len(line)-1)
            factor = min(1, 840/total)
            total *= factor
            x = (1080-total)/2
            y = 1274 if len(lines)==1 else 1236+line_index*74
            for i in line:
                word = group[i]
                font = faces[i]
                size = sizes[i]*factor
                span = widths[i]*factor
                at = max(0,word['s'] - min(.02, .5/record['fps']))
                authored.append(dict(t=at, dur=max(.04,end-at), text=word['w'], x=round(x,2), y=y,
                    width=round(span,2), size=round(size,2), font=font, italic=font=='cormorant',
                    weight=700, tracking=-.035, lineHeight=1, align='center', surface='difference',
                    color='#ffffff', blend='difference', fillOpacity=1, shadow='none', depth='front',
                    motion={'inSec':.11,'outSec':.035,'rise':8,'scaleFrom':.965,'blur':3,'easing':'cubic'}))
                x += span + gap*factor
    if cursor != len(words):raise ValueError(f'{id}: {len(words)-cursor} uncaptained words')
    props['referenceEdit'].update(profile='editorial', palette='silver', layeredOnly=True, layers=authored)
    validate_reference_edit(props['referenceEdit'], record['duration'])
    assert all(l['surface']=='difference' and l['color']=='#ffffff' and l['blend']=='difference' for l in authored)
    assert all(80<=l['x'] and l['x']+l['width']<=1000 and l['y']+l['size']*1.25<=1408 for l in authored)
    (P / 'props' / (id + '.json')).write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
    print(id,len(authored),'source words; one true-italic accent; white Difference on all layers')
