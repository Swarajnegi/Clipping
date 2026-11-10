"""Word-timed, overlapping silver/italic caption choreography for this batch."""
import json
import re
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]

def main():
    decisions=json.loads((HERE/'edit-decisions.json').read_text())
    for decision in decisions:
        work=ROOT/'work'/decision['work_id']
        path=work/'clips.json'
        spec=json.loads(path.read_text())
        clip=spec['clips'][0]
        name=decision['work_id'].split('_')[-1]
        if name=='confidence':
            clip['segments'][0][0]=7.36
            clip['segments'][-1][1]=36.10
        if name=='parenthood':
            clip['segments'][0][0]=7.24
            clip['segments'][1][1]=40.74
            clip['segments'][2][0]=42.86
        pieces=clip['segments']
        words=[w for row in json.loads((work/'transcript.json').read_text()) for w in row['words']]
        def timeline(t):
            offset=0
            for a,b in pieces:
                if a<=t<=b:return round(offset+t-a,3)
                offset+=b-a
            raise ValueError(f'Time {t} outside {name} cut')
        def phrase(text,after=0):
            target=re.findall(r"[a-z0-9']+",text.lower())
            tokens=[re.sub(r"[^a-z0-9']",'',w['w'].lower()) for w in words]
            for i in range(len(words)-len(target)+1):
                if words[i]['s']>=after and tokens[i:i+len(target)]==target:
                    return words[i]['s'],words[i+len(target)-1]['e']
            raise ValueError('Phrase not found: '+text)
        layers=[]
        def add(source,until,text,x,y,size,font='condensed',italic=False,z=1,width=470,rotate=0):
            start=timeline(source)
            end=timeline(until)
            needle=re.findall(r"[a-z0-9']+",text.lower())
            normalized=[re.sub(r"[^a-z0-9']",'',w['w'].lower()) for w in words]
            word_times=None
            for i in range(len(words)-len(needle)+1):
                if source-0.50<=words[i]['s']<until and normalized[i:i+len(needle)]==needle:
                    word_times=[timeline(w['s']) for w in words[i:i+len(needle)]]
                    start=word_times[0]
                    break
            if word_times is None:raise ValueError('Unaligned caption layer: '+text)
            layers.append(dict(t=start,dur=round(end-start,3),text=text,x=x,y=y,size=size,font=font,
                               italic=italic,z=z,width=width,rotate=rotate,wordTimes=word_times))
        if name=='confidence':
            add(7.36,8.86,'I still am',110,902,40,'serif',True,3)
            add(7.88,8.86,'FULL OF',70,948,76,z=1)
            add(8.12,8.86,'DOUBT.',82,1008,124,z=2)
            add(8.22,8.86,'all the time',260,1114,33,'serif',True,4)
            start,end=phrase("what if you can't",after=20)
            add(start,end+0.12,'what if',108,954,44,'serif',True,3)
            you,_=phrase("you can't",after=start)
            add(you,end+0.12,"YOU CAN'T?",70,1007,88,z=2)
            add(30.38,31.58,'be the',104,946,42,'serif',True,3)
            add(30.64,31.58,'BEST',70,986,126,z=1)
            add(31.00,31.58,'in the world',208,1104,43,'serif',True,4)
        elif name=='pursuit':
            add(11.72,13.42,'way too far',100,954,44,'serif',True,3)
            add(12.46,13.42,'BEHIND',70,1002,102,z=1)
            add(12.74,13.42,'to win',296,1091,45,'serif',True,4)
            add(21.40,22.16,"it's",110,967,45,'serif',True,3)
            add(21.40,22.16,'IMPOSSIBLE.',70,1011,83,z=1)
            add(31.74,34.50,"I'm capable of",100,909,37,'serif',True,3)
            add(32.62,34.50,'SO MUCH',70,951,68,z=1)
            add(32.94,34.50,'MORE',80,1003,121,z=2)
            add(33.10,34.50,'than my mind',97,1123,34,'serif',True,4)
            add(33.70,34.50,'understands.',284,1125,31,'serif',True,5,width=270)
        elif name=='parenthood':
            add(7.24,11.12,'your',110,910,48,'serif',True,3)
            add(7.48,11.12,'CHILDREN',70,958,89,z=1)
            add(8.76,11.12,'eventually',260,1041,36,'serif',True,4)
            add(9.16,11.12,'will know',94,1082,39,'serif',True,3)
            add(9.70,11.12,'EXACTLY',70,1123,58,z=2)
            add(10.18,11.12,'who you are',291,1150,33,'serif',True,5,width=270)
            start,end=phrase('they see through it all',after=23)
            add(start,end+0.15,'THEY SEE',70,980,78,z=1)
            through,_=phrase('through it all',after=start)
            add(through,end+0.15,'through it all',139,1056,44,'serif',True,4)
            add(33.94,35.02,'SOLVE',70,981,97,z=1)
            add(34.34,35.02,'your problems',144,1072,42,'serif',True,4)
            add(46.62,48.52,'but at home',100,948,44,'serif',True,3)
            add(47.86,48.52,'NO',70,1003,95,z=1,width=125)
            add(47.96,48.52,'HIDING',182,1003,110,z=2,width=360)
            add(48.20,48.52,'anything.',283,1113,42,'serif',True,4,width=270)
        edit=clip['referenceEdit']
        edit.update(palette='silver',wordReveal=True,layers=layers,emphasis=[],captionY=1120,captionSize=34)
        path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
        decision.update(duration=round(sum(b-a for a,b in pieces),3),local_segments=pieces,
                        caption_treatment='Layered silver-white condensed keywords and italic serif connectors; independent word-timed entrances and overlapping retained lines')
        decision['original_segments_approx']=[[round(decision['source_start']+a,3),round(decision['source_start']+b,3)] for a,b in pieces]
        print(name,len(layers),'layers',decision['duration'],'seconds')
    (HERE/'edit-decisions.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')

if __name__=='__main__':main()
