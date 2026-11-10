"""Materialize five editorial cuts with measured, word-timed caption typography."""
import json
import argparse
import re
from pathlib import Path
from PIL import ImageFont

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
DECISIONS = {
    'opinions': {'title': "Other people's opinions don't decide your worth",
                 'pieces': [[19.46, 24.58], [25.18, 33.12], [59.76, 63.10], [63.45, 67.65]],
                 'why': 'Direct cold opening, distinguish external judgement from personal worth. Omit the long cheating example and the source glitch around local 36s.',
                 'payoff': "They don't own me, and they don't decide my worth."},
    'process': {'title': 'The process is better than the prize',
                'pieces': [[15.06, 18.65], [19.03, 34.97], [35.54, 39.50], [40.10, 43.61], [44.00, 47.96]],
                'why': 'Keep the concrete one-year challenge and the reversal; remove empty pauses. End on the complete process-of-going-through-that-year payoff, before the incomplete downloaded next sentence.',
                'payoff': 'Even better than the actual payoff will be the process of going through that year.'},
    'opponent': {'title': "Respect your opponent's victory",
                 'pieces': [[10.42, 15.70], [44.45, 56.80], [62.45, 68.20]],
                 'why': 'Preserve the principle and the specific acknowledgement that Chase earned the victory. Omit the betting analogy and rematch tangent.',
                 'payoff': 'He won, he deserves it, and I always pay my debts.'},
    'regenerate': {'title': 'Your mind has to move forward',
                   'pieces': [[15.86, 24.45], [26.70, 34.80], [35.60, 41.50], [42.24, 54.30], [55.08, 59.13]],
                   'why': 'Preserve the healing analogy, the explicit bad-experiences context and the practical lesson. Exclude the earlier unrelated alcoholic generalization.',
                   'payoff': 'It happened. Here is the lesson. Move forward. Done.'},
    'silver': {'title': 'Find the silver in the clouds',
               'pieces': [[11.26, 12.45], [35.32, 43.10], [45.15, 50.72], [53.40, 61.40], [64.10, 69.20], [73.34, 74.35], [77.97, 81.30], [83.15, 85.05]],
               'why': "Keep Tristan's reported-speech attribution, the wish for a sunny day, and Andrew's silver reply. Remove intervening fight recap, empty pauses and the later wealth boast.",
               'payoff': "We've had so many clouds that we've got a lot of silver."},
}


def normal(text):
    return re.sub(r"[^a-z0-9']", '', text.lower())


def font_path(font, italic, weight):
    if font == 'serif':
        return 'C:/Windows/Fonts/georgiai.ttf' if italic else 'C:/Windows/Fonts/georgia.ttf'
    if font == 'condensed':
        return 'C:/Windows/Fonts/impact.ttf'
    name = 'arialbi.ttf' if italic and weight >= 700 else 'ariali.ttf' if italic else 'arialbd.ttf' if weight >= 700 else 'arial.ttf'
    return 'C:/Windows/Fonts/' + name


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',choices=list(DECISIONS))
    args=parser.parse_args()
    brief = json.loads((HERE / 'brief.json').read_text())
    manifest = []
    for name, decision in DECISIONS.items():
        if args.only and name!=args.only:
            continue
        target = ROOT / 'work' / ('em117_20261101_' + name)
        if target.exists():
            raise RuntimeError('Existing edit must be inspected before replacing: ' + str(target))
        metadata = json.loads((HERE / 'source-clean' / (name + '.json')).read_text())
        raw = json.loads((HERE / 'source' / (name + '-transcript.json')).read_text())
        pieces = decision['pieces']
        duration = round(sum(b-a for a,b in pieces), 6)
        words = [dict(w) for row in raw for w in row['words']]
        selected = []
        offset = 0.0
        for piece_index, (a,b) in enumerate(pieces):
            if metadata['source_start'] + a < 7860 or b > metadata['duration'] + .05:
                raise RuntimeError('Cut violates source boundary')
            for i,w in enumerate(words):
                if w['e'] <= a or w['s'] >= b:
                    continue
                selected.append({**w, 'source_index':i, 'piece_index':piece_index,
                                 't':round(max(a,w['s'])-a+offset,6),
                                 'end':round(min(b,w['e'])-a+offset,6)})
            offset += b-a
        # Punctuation follows the preserved speech; final clause receives a full stop.
        if selected[-1]['w'].rstrip()[-1] not in '.?!':
            words[selected[-1]['source_index']]['w'] += '.'
            selected[-1]['w'] += '.'
        normalized = [normal(w['w']) for w in selected]
        blocked = set()
        layers = []

        def line(items, text, y, size, italic=False, weight=700, font='sans', end=None):
            if not items:
                raise RuntimeError('Empty caption line')
            size = int(size)
            while ImageFont.truetype(font_path(font,italic,weight),size).getlength(text) > 820:
                size -= 1
            at = items[0]['t']
            until = end if end is not None else min(duration, items[-1]['end']+.2)
            if until <= items[-1]['t']:
                raise RuntimeError('Invalid caption word interval')
            layer = {'t':at,'dur':round(until-at,6),'text':text,'x':110,'y':y,'width':860,
                     'size':size,'font':font,'italic':italic,'weight':weight,'align':'center',
                     'z':len(layers)+1,'wordTimes':[w['t'] for w in items]}
            layers.append(layer)

        def cue(phrase, designs, after=0, hold=.24):
            needle = [normal(x) for x in phrase.split()]
            found = None
            for i in range(len(selected)-len(needle)+1):
                if (selected[i]['s'] >= after and normalized[i:i+len(needle)] == needle
                        and selected[i]['piece_index'] == selected[i+len(needle)-1]['piece_index']):
                    found = i
                    break
            if found is None:
                raise RuntimeError('Unaligned emphasis phrase: '+phrase)
            indices = set(range(found,found+len(needle)))
            if blocked & indices:
                raise RuntimeError('Overlapping emphasis phrases')
            blocked.update(indices)
            group = selected[found:found+len(needle)]
            end = min(duration,group[-1]['end']+hold)
            if found+len(needle)<len(selected):
                end=min(end,selected[found+len(needle)]['t'])
            cursor=0
            for text,y,size,italic,weight,font in designs:
                count=len(text.split())
                items=group[cursor:cursor+count]
                if [normal(x) for x in text.split()] != [normal(w['w']) for w in items]:
                    raise RuntimeError('Caption text is not the aligned speech: '+text)
                line(items,text,y,size,italic,weight,font,end)
                cursor += count
            if cursor!=len(group):
                raise RuntimeError('Incomplete emphasis caption')

        if name == 'opinions':
            cue("other people's opinion of you", [("other people's",1024,54,True,400,'sans'),('OPINION OF YOU',1096,76,False,700,'sans')])
            cue('they already own you', [('they already',1024,50,True,400,'sans'),('OWN YOU.',1092,90,False,700,'sans')])
            cue("don't decide my worth", [("don't decide",1024,54,True,400,'sans'),('MY WORTH.',1094,90,False,700,'sans')])
        elif name == 'process':
            cue('dedicate yourself', [('Dedicate',1024,70,False,700,'sans'),('yourself',1108,78,True,400,'sans')])
            cue('one year', [('ONE YEAR.',1068,96,False,700,'sans')],after=30)
            cue('the process of going through that year', [('THE',1020,50,False,700,'sans'),('PROCESS',1086,92,False,700,'sans'),('of going through that year.',1190,46,True,400,'sans')])
        elif name == 'opponent':
            cue('never ever', [('NEVER',1020,88,False,700,'sans'),('ever',1112,76,True,400,'sans')],hold=.35)
            cue("your opponent's victory", [("your opponent's",1024,56,True,400,'sans'),('VICTORY.',1100,88,False,700,'sans')])
            cue('he earned it', [('HE EARNED IT.',1060,84,False,700,'sans')])
            cue('I always pay my debts', [('I always',1024,54,True,400,'sans'),('PAY MY DEBTS.',1100,78,False,700,'sans')])
        elif name == 'regenerate':
            cue('gave up on regeneration', [('gave up on',1024,50,True,400,'sans'),('REGENERATION.',1094,76,False,700,'sans')])
            cue('your mind', [('your mind',1060,76,True,400,'sans')],after=35)
            cue('move forward', [('MOVE',1020,86,False,700,'sans'),('FORWARD.',1112,94,False,700,'sans')],after=55)
            cue('done', [('DONE.',1070,100,False,700,'sans')])
        elif name == 'silver':
            cue('silver linings in all of the clouds', [('silver linings',1018,68,True,400,'serif'),('in all of the clouds.',1108,54,False,700,'sans')])
            cue('you deserve to have a sunny day', [('You deserve to have',1024,52,False,700,'sans'),('a sunny day.',1100,76,True,400,'sans')])
            cue('clouds', [('CLOUDS',1064,94,True,700,'sans')],after=77)
            cue("we've got a lot of fucking silver", [("we've got",994,48,False,700,'sans'),('a lot of fucking',1054,48,True,400,'sans'),('SILVER.',1120,98,False,700,'sans')],after=83,hold=.55)
        # Short units and predictable placement borrow the reference's reading rhythm.
        i=0
        while i<len(selected):
            if i in blocked:
                i+=1
                continue
            group=[selected[i]]
            j=i+1
            while j<len(selected) and j not in blocked and len(group)<3:
                prev,nxt=group[-1],selected[j]
                if (nxt['piece_index']!=prev['piece_index'] or nxt['t']-prev['end']>.35
                        or prev['w'].rstrip().endswith(('.', '?', '!'))
                        or nxt['end']-group[0]['t']>.95
                        or len(' '.join(w['w'].strip() for w in group+[nxt]))>23):
                    break
                group.append(nxt)
                j+=1
            end=min(duration,group[-1]['end']+.2)
            if j<len(selected):
                end=min(end,selected[j]['t'])
            text=' '.join(w['w'].strip() for w in group)
            line(group,text,1080,56,False,700,'sans',end)
            i=j
        layers.sort(key=lambda layer:(layer['t'],layer['z']))
        metadata.update(id=target.name,title=decision['title'],url=None,
                        source_key='rumble:v73b2wc',source_kind='bounded original passage')
        target.mkdir(parents=True)
        (target/'source.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        indexed={i:w for i,w in enumerate(words)}
        position=0
        for row in raw:
            for j in range(len(row['words'])):
                row['words'][j]=indexed[position]
                if row['words'][j]['w'].rstrip().endswith(('.', '?', '!')):
                    row['words'][j]['pageBreakAfter']=True
                position+=1
        (target/'transcript.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
        (target/'caption-corrections.json').write_text(json.dumps({'word_substitutions':[], 'punctuation':'Full stop at the selected final complete clause; preserve original vocabulary.'},indent=2),encoding='utf-8')
        spec={'id':target.name,'pairedExports':False,'brand':{'music':None},
              'footage_reuse_basis':brief['reuse_basis'],'branding':'Own channel; no symbol or reference assets.',
              'clips':[{'n':1,'type':'talk','segments':pieces,'trimSilence':False,'intro':None,'hook':'',
                        'captions':True,'music':None,'sourceAudioDb':-2,'style':'letterbox',
                        'shots':[{'t':0,'x':.5,'w':1,'lock':True}],
                        'referenceEdit':{'profile':'kinetic','bandHeight':1500,'captionY':1080,
                                         'captionSize':56,'palette':'silver','wordReveal':True,
                                         'layeredOnly':True,
                                         'layers':layers,'emphasis':[]},
                        'title':decision['title'],'description':'Andrew Tate, Emergency Meeting 117 - Risk and Reward. '+decision['payoff'],
                        'why':decision['why']}]}
        (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        manifest.append({'work_id':target.name,'name':name,'title':decision['title'],'duration':duration,
                         'source_start':metadata['source_start'],'local_segments':pieces,
                         'original_segments_approx':[[round(metadata['source_start']+a,3),round(metadata['source_start']+b,3)] for a,b in pieces],
                         'payoff':decision['payoff'],'why':decision['why'],'caption_layers':len(layers),
                         'caption_text':' '.join(w['w'].strip() for w in selected),
                         'source_frame_rate':30,'source_crop':metadata['source_crop']})
        print(name,duration,'seconds',len(layers),'caption layers')
    if args.only:
        previous=json.loads((HERE/'edit-decisions.json').read_text())
        revised={item['name']:item for item in manifest}
        manifest=[revised.get(item['name'],item) for item in previous]
    if len(manifest)!=5:
        raise RuntimeError('Expected exactly the five requested edits')
    (HERE/'edit-decisions.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
