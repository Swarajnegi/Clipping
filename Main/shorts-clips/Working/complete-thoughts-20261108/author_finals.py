"""Author approved native-rate cuts: centred, face-aware Difference word layers."""
import json,re,sys,os,shutil
from pathlib import Path
from functools import lru_cache
from PIL import ImageFont
P=Path(__file__).resolve().parent;ROOT=P.parents[3];F=P/'finish-v1'
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(t):return re.sub('[^a-z0-9]','',t.lower())
groups={
'01':['Ask does this path','enlarge me psychospiritually','Or does it diminish me',
 'And you usually know','the answer to that','If you choose','the larger path',
 "you're going to",'grow and develop it',"It's going to take",'something out of you',
 "but it'll give",'something to you',"If you don't",'your life gets','narrower and narrower',
 'and narrower','And something inside of you','knows the difference'],
'02':["I didn't teach myself",'victory first','I taught myself failure','I taught myself',
 'how to fail','And people like',"that's so depressing",'is it',"When you're 300 pounds",
 "and you can't",'read and write',"and you're fucked up",'you know how many times',
 "you're going to",'fucking fail','on that process',"So if you don't",'know how to fail',
 'there is no victory','I never talked about winning','because I knew','the path to winning',
 'was gonna be','years of failing first','So I taught myself','how to fail properly'],
'03':['winners and losers','have the same goals','You look at','the Olympic Games',
 'presumably any event',"everybody who's competing",'has the goal of winning',
 'the Olympic medal','right of winning the gold','So the goal is not','the thing that',
 'makes the difference','So again','winners and losers','have the same goals',
 'So if they have','the same goals','they cannot be the thing','that makes the difference',
 'in their performance','It has to be','something else','Maybe having a goal','is part of it',
 "Maybe it's necessary","but it's not sufficient",'for the outcome','that you want',
 'And for that','what you need','is a system','You need a collection of habits',
 'that are going to','make the difference','and accumulate','into a bigger outcome'],
'04':['You are not responsible','for proving your worth','Let them underestimate you',
 'I know you think','well Mel','but if everybody likes me','and sees my value',"then I'm good",
 'Like me',"you've been getting it",'all backwards','You think self-worth comes',
 'from everybody else liking you',"It's actually the opposite",'Self-worth comes from you',
 'liking who you already are',"That's the real success",'in life liking yourself',
 'Being okay with yourself','is the key to','showing up getting things done',
 'and building the life','that you want',"It's everything"],
'05':["But they're jealous",'of what you\'ve got',"They're not jealous",'of how you got it',
 'No comedians are jealous','of how I got it','No one sits there','and goes oh',
 'I wish I could sit','for 10 hours a day','and write jokes','Oh','They think',
 'I want to play that venue',"or I'd love to have",'that Netflix special',
 "But they don't sit there",'going well','what pathology would you need','in your head',
 'to write that many one-liners','and to care that much','about it',
 'Who would you have to be','to do that']}
accents={'01':{'larger','difference'},'02':{'failure','properly'},'03':{'same','habits'},
 '04':{'worth','yourself'},'05':{'jealous','care'}}
fonts=ROOT/'.agents/skills/viral-shorts/assets/fonts'
for a,b in [('InterVariable.woff2','InterVariable.woff2'),('LICENSE.txt','Inter-LICENSE.txt'),
 ('CormorantGaramond-Italic.ttf','CormorantGaramond-Italic.ttf'),('Cormorant-OFL.txt','Cormorant-OFL.txt')]:
 shutil.copy2(fonts/a,ROOT/'public/fonts'/b)
@lru_cache(maxsize=128)
def facefont(name,size):
 f=ImageFont.truetype(str(fonts/('InterVariable.woff2' if name=='inter' else 'CormorantGaramond-Italic.ttf')),round(size*10))
 try:
  f.set_variation_by_axes([700 if a['name']==b'Weight' else min(32,a['maximum']) if a['name']==b'Optical Size' else a['default'] for a in f.get_variation_axes()])
 except OSError:pass
 return f
def width(text,size,font):return facefont(font,size).getlength(text)/10-max(0,len(text)-1)*.035*size+12
def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])

corrections=[]
for proof in read(P/'proofs.json'):
 id=proof['id'];number=id[:2];r=read(P/'drafts'/(id+'-rough.json'));words=[dict(w) for w in r['words']]
 if number=='01':
  words[6:8]=[{'w':'psychospiritually,','s':words[6]['s'],'e':words[7]['e'],'p':None}]
  corrections.append({'id':id,'change':'Merged misrecognised Cycle spiritually into official source wording psychospiritually; retained its original combined interval.'})
 if number=='02':
  refined=[w for s in read(F/'goggins-focused-alignment.json')['segments'] for w in s['words']]
  words=[w for w in words if w['s']<10.94]+refined+[w for w in words if w['s']>=20.6]
  for w in words:
   if norm(w['w'])=='are' and 10.7<w['s']<11.1:w['w']='like,'
   if norm(w['w'])=='i' and 4.7<w['s']<5:w['s']=6.42;w['e']=6.61
  i=next(i for i,w in enumerate(words) if norm(w['w'])=='therell')
  words[i:i+2]=[{'w':t,'s':a,'e':b,'p':None} for t,a,b in
   [('you',16.94,17.08),('know',17.08,17.24),('how',17.24,17.42),('many',17.42,17.76)]]
  corrections.append({'id':id,'change':'Focused ASR repaired question/300/going-to timings. Official Huberman captions correct like and you know how many times; missing-word timings are manually interpolated within the source phrase, not certified to one-frame precision.'})
 if number=='04':
  for w in words:
   if norm(w['w'])=='mal':w['w']='Mel,'
 # Compounds reserve one stable word layer, not a leading-hyphen orphan.
 merged=[]
 for w in words:
  if w['w'].startswith('-') and merged:
   merged[-1]['w']+=w['w'];merged[-1]['e']=w['e']
  else:merged.append(w)
 words=merged
 for w in words:
  w['s']=max(0,w['s']);w['e']=min(r['duration'],w['e'])
 # Stage clean source without re-encoding its approved dialogue or changing cuts.
 pub=ROOT/'public/clips'/('complete_thoughts_20261108_'+number);pub.mkdir(exist_ok=True)
 master=pub/'master.mp4'
 if not master.exists():os.link(r['assembly'],master)
 cw=r.get('crop_size',2160);shots=[]
 for shot in r['shots']:
  t=round(shot['t']*r['fps'])/r['fps'];new={'t':t,'x':shot['x'],'w':cw/3840,'lock':True}
  if shots and abs(shots[-1]['t']-t)<1e-7:shots[-1]=new
  else:shots.append(new)
 if number=='02':
  shots=[{'t':0,'x':(1080+128)/3840,'w':2160/3840,'lock':True}]
 def face_boxes(a,b):
  boxes=[]
  for sample in r['face_samples']:
   if not a-.05<=sample['t']<=b+.05:continue
   shot=next((s for s in reversed(shots) if s['t']<=sample['t']),shots[0])
   left=max(0,min(3840-cw,shot['x']*3840-cw/2));top=(2160-cw)/2;scale=980/cw
   for f in sample['faces']:
    x=50+(f[0]*6-left)*scale;y=470+(f[1]*6-top)*scale
    w=f[2]*6*scale;h=f[3]*6*scale
    # Conservative expansion for brief opening push and detection tolerance.
    box=[x-18,y-18,x+w+18,y+h+22]
    if box[2]>50 and box[0]<1030 and box[3]>470 and box[1]<1450:boxes.append(box)
  return boxes
 layers=[];cursor=0;used=set();placement=[]
 for gi,text in enumerate(groups[number]):
  tokens=text.split();chunk=words[cursor:cursor+len(tokens)]
  assert [norm(t) for t in tokens]==[norm(w['w']) for w in chunk],(id,cursor,tokens,chunk)
  cursor+=len(chunk);start=chunk[0]['s']
  end=min(r['duration'],words[cursor]['s'] if cursor<len(words) else r['duration'])
  # Hold a complete thought briefly through a pause, but clear long dead holds.
  end=min(end,chunk[-1]['e']+.55)
  sizes=[68 if gi<2 else 61]*len(chunk);faces=['inter']*len(chunk)
  for i,w in enumerate(chunk):
   if norm(w['w']) in accents[number] and norm(w['w']) not in used:
    faces[i]='cormorant';sizes[i]+=10;used.add(norm(w['w']))
  widths=[width(w['w'],sizes[i],faces[i]) for i,w in enumerate(chunk)]
  maxwidth=350 if number=='02' else 820
  if sum(widths)+12*(len(chunk)-1)<=maxwidth and len(chunk)<=4:lines=[list(range(len(chunk)))]
  else:
   split=min(range(1,len(chunk)),key=lambda k:abs(sum(widths[:k])-sum(widths[k:])))
   lines=[list(range(split)),list(range(split,len(chunk)))]
  rowheight=82;totalheight=len(lines)*rowheight;boxes=face_boxes(start,end)
  yc=725 if number=='02' else 960
  xc=275 if number=='02' else 540
  # Preserve central composition unless the actual shot's face conflicts.
  candidate=[xc-maxwidth/2,yc-totalheight/2-12,xc+maxwidth/2,yc+totalheight/2+18]
  if any(intersects(candidate,box) for box in boxes):
   yc=max(960,max(box[3] for box in boxes)+34+totalheight/2)
  assert yc+totalheight/2+22<1410,(id,gi,'No safe caption space',yc)
  for row,line in enumerate(lines):
   gap=12;total=sum(widths[i] for i in line)+gap*(len(line)-1);factor=min(1,maxwidth/total)
   total*=factor;x=xc-total/2;y=yc-totalheight/2+row*rowheight
   for i in line:
    word=chunk[i];size=sizes[i]*factor;span=widths[i]*factor
    at=round(word['s']*r['fps'])/r['fps']
    layers.append(dict(t=at,dur=max(1/r['fps'],end-at),text=word['w'],x=round(x,2),y=round(y,2),
     width=round(span,2),size=round(size,2),font=faces[i],italic=faces[i]=='cormorant',
     weight=700,tracking=-.035,lineHeight=1,align='center',surface='difference',
     color='#ffffff',blend='difference',fillOpacity=1,shadow='none',depth='front',
     motion={'inSec':.10,'outSec':.035,'rise':7,'scaleFrom':.975,'blur':2,'easing':'cubic'}))
    x+=span+gap*factor
  placement.append({'text':text,'start':start,'end':end,'centre':[xc,yc],'faces_considered':len(boxes)})
 assert cursor==len(words),(id,'Uncaptioned words',cursor,len(words))
 props=dict(src=f'clips/{pub.name}/master.mp4',bgSrc=None,fps=r['fps'],durationSec=r['duration'],
  srcWidth=3840,srcHeight=2160,widthFrac=cw/3840,shots=shots,track=[],yAnchor=.5,
  hook='',hookPersist=False,hookDurationSec=0,captions=[],punchIns=[{'t':0,'dur':1.3,'scale':1.022}],
  watermark=None,loopFadeSec=0,style='bold',grade={'brightness':.98,'contrast':1.035,'saturate':1.0},
  accent='#ffffff',intro=None,music=None,referenceEdit={'profile':'editorial','palette':'silver',
   'layeredOnly':True,'frame':{'x':50,'y':470,'width':980,'height':980,'radius':48},'layers':layers})
 if number=='03':props['punchIns']=[{'t':1.84,'dur':1.15,'scale':1.022}]
 validate_reference_edit(props['referenceEdit'],r['duration'])
 (F/'props'/(id+'.json')).write_text(json.dumps(props,ensure_ascii=False,indent=2),encoding='utf-8')
 (F/'props'/(id+'-caption-plan.json')).write_text(json.dumps({'id':id,'words':words,'groups':placement,
  'approved_source_cuts_preserved':True,'framing_adjustment':'Goggins reframed right to place captions on dark negative space' if number=='02' else 'Preserved rough shot framing, with small opening push',
  'opening':'Gentle 2.2% push with authentic spoken premise and timed typography; no fabricated card, added narration, music or SFX.',
  'approval':'All five approved by owner for finishing 8 November 2026'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(id,len(words),'caption words; centre range',min(p['centre'][1] for p in placement),max(p['centre'][1] for p in placement))
(F/'caption-corrections.json').write_text(json.dumps(corrections,indent=2),encoding='utf-8')
