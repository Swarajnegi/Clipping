"""Author the approved source passage without altering previous exports."""
from pathlib import Path
import copy, json, shutil, sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit
PROJECT=Path(__file__).resolve().parent
ID='ronaldo_whoop_20261103_caption_v2'
work=ROOT/'work'/ID; (work/'props').mkdir(parents=True,exist_ok=True)
old=ROOT/'work/ronaldo_whoop_20261102_map'
props=json.loads((old/'props/clip_01.json').read_text(encoding='utf-8'))
props.update(src=f'clips/{ID}/clip_01.mp4',bgSrc=None,style='bold',
  shots=[{'t':0,'x':0.61,'w':0.55},{'t':2.36,'x':0.83,'w':0.55}],track=[],
  intro=None,hook='',watermark=None,music=None,punchIns=[])
# The cut includes only the final 20 ms of the preceding "because". It is not a
# complete word in this passage; retain the approved audio, omit that clipped label.
props['captions']=[c for c in props['captions'] if not (c['startMs']==0 and c['endMs']<=20)]
layers=[]

def line(text,t,end,y,size,times=None,**extra):
    layer=dict(t=t,dur=round(end-t,4),text=text,x=70,y=y,width=900,size=size,
      font='inter',weight=700,tracking=-0.05,align='center',shadow='strong',
      motion=dict(inSec=0.16,outSec=0.06,rise=22,scaleFrom=0.94,blur=7,easing='cubic'))
    if times is not None: layer['wordTimes']=times
    layer.update(extra); layers.append(layer)

line('everyone wants',0,1.22,1100,70,[0,0.32])
line('to be',0.62,1.22,1180,66,[0.62,0.72])
line('[CRISTIANO]',0.82,1.22,1260,124,glow=3,
  perspective=dict(distance=1400,rotateX=5,rotateY=-4))
line('But',1.22,1.54,1170,96)
line('I',1.54,4.0,970,96)
line('give you the',3.34,4.0,1060,72,[3.34,3.5,3.62])
line('[map]',3.72,4.64,1150,164,glow=2,
  perspective=dict(distance=1200,rotateX=8,rotateY=-10))
line('you think',4.0,4.82,1370,72,[4.0,4.64])
line('you will do it?',4.82,5.44,1260,82,[4.82,5.0,5.18,5.34])
line('That',5.44,5.68,1140,88)
line("it's",5.68,6.82,1070,68)
line('difficult.',6.5,6.82,1170,136)
line("It's the",6.82,7.76,1050,70,[6.82,7.14])
line('discipline.',7.26,7.76,1150,132,glow=3)
line('The',7.76,9.94,490,70)
line('discipline',8.28,9.94,580,148,depth='behind',
  perspective=dict(distance=1500,rotateX=4,rotateY=-7),glow=2)
line('is the most',8.7,9.94,1190,72,[8.7,8.94,9.08])
line('difficult thing.',9.24,9.94,1280,95,[9.24,9.56])
line('Not only in',9.94,11.54,1100,72,[9.94,10.6,10.98])
line('the',11.1,11.54,1180,64)
line('sports,',11.2,11.54,1260,140)
line('but',11.7,12.92,1100,72)
line('in the',12.2,12.92,1180,70,[12.2,12.34])
line('[life]',12.44,12.92,1270,170,
  motion=dict(inSec=0.16,outSec=0.01,rise=22,scaleFrom=0.94,blur=7,easing='cubic'))

# The head contour is authored on 740x540 inspection frames, then mapped through
# precisely the same crop as the renderer. Only its upper edge overlaps this text.
outline=[[610,170],[617,162],[630,158],[647,157],[661,160],[669,166],
 [674,179],[673,192],[678,199],[674,214],[667,230],[655,246],
 [646,257],[630,253],[619,240],[612,222],[606,204],[607,190]]
scale=1080/(0.55*1480)
left=1080-1480*scale; top=(1920-1080*scale)/2
def points(dx=0,dy=0):
    return [[round((x+dx)*2*scale+left,2),round((y+dy)*2*scale+top,2)] for x,y in outline]
mask=dict(t=8.28,dur=1.66,keyframes=[
 dict(t=8.28,points=points(-3,1)),dict(t=8.5,points=points()),
 dict(t=9.0,points=points(2,0)),dict(t=9.5,points=points(3,-1)),
 dict(t=9.94,points=points(2,0))])
props['referenceEdit']=dict(profile='editorial',bandHeight=1920,palette='silver',
  layeredOnly=True,wordReveal=True,layers=layers,foregroundMasks=[mask])
validate_reference_edit(props['referenceEdit'],12.92)
(work/'props/clip_01.json').write_text(json.dumps(props,indent=2),encoding='utf-8')
spec=json.loads((old/'clips.json').read_text(encoding='utf-8'))
spec['id']=ID; spec['clips']=copy.deepcopy(spec['clips'][:1])
clip=spec['clips'][0]
clip.update(referenceEdit=props['referenceEdit'],shots=props['shots'],style='bold',sourceAudioDb=0)
(work/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
shutil.copy2(old/'source.json',work/'source.json'); shutil.copy2(old/'transcript.json',work/'transcript.json')
for file in ('clips.json','props/clip_01.json'):
    shutil.copy2(work/file,PROJECT/Path(file).name)
(PROJECT/'edit-decisions.json').write_text(json.dumps({
 'source_url':'https://www.youtube.com/watch?v=kbKldiDOgEE','source_range':[620.52,633.44],
 'duration':12.92,'frames':323,'font_substitution':'Inter Bold for SF Pro Display Bold; owner approved',
 'reuse_basis':spec['footage_reuse_basis'],'source_frames':'clean-final.mp4; new guarded snippet',
 'audio':'Copy the approved finished audio packets; no music or new narration',
 'reference':'https://www.youtube.com/watch?v=uAga_kBywLM',
 'depth_interval':[8.28,9.94],'mask_scope':'Head silhouette; only the hairline overlaps background text',
 'caption_boundary_fragment':'Exclude only the 20 ms tail of preceding because; audio unchanged',
 'coverage':'Source 0.5-second sheet reviewed before authoring; validate exact cut and mask motion in rendered QA'
},indent=2),encoding='utf-8')
print(work/'props/clip_01.json')
