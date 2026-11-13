from pathlib import Path
import json, shutil

root = Path(r'D:\J.A.R.V.I.S\Clipping')
work = Path(__file__).parent
public = root / 'public/clips/henry-cavill-caption-review'
public.mkdir(parents=True, exist_ok=True)
shutil.copy2(work / 'caption-free-v2-PRIVATE-REVIEW.mp4', public / 'picture.mp4')
words = json.loads((work / 'caption-word-timing-draft.json').read_text(encoding='utf-8'))['word_timing']
phrases = [
 ('a friend',0,2), ('of mine',2,4), ('sent me',4,6), ('this text',6,8),
 ('a long',8,10), ('time ago',10,12), ('and it’s',12,14), ('stuck',14,15),
 ('with me',15,17), ('ever since',17,19), ('it’s a',19,21),
 ('choose your',21,23), ('life’s mate',23,25), ('carefully',25,26),
 ('from this',26,28), ('one decision',28,30), ('will come',30,32),
 ('90%',32,34), ('of all your',34,37), ('happiness',37,38), ('or misery',38,40),
 ('never deprive',40,42), ('someone of hope',42,45), ('it might be',45,48),
 ('all that they have',48,52), ('don’t expect',53,55), ('life',55,56),
 ('to be',56,58), ('Fair',58,59),
]
fps = 30000 / 1001
# Reveal each line in place and hold it until the next group starts.
opening_groups = [
    (0, 2, 95, (498, 580)),
    (2, 4, 696, (498, 592)),
    (4, 6, 90, (498, 598)),
    (6, 9, 90, (498, 600, 728)),
    (9, 11, 90, (498, 604)),
]
opening_layouts = {}
for first, end, x, rows in opening_groups:
    group_stop = words[phrases[end][1]]['start'] if end < 11 else 140 / fps
    for index, y in zip(range(first, end), rows):
        opening_layouts[index] = (x, y, group_stop)

layers=[]
for index, (text, first, end) in enumerate(phrases):
    ws=words[first:end]
    if not ws: continue
    start=ws[0]['start']; stop=min(16.55,max(ws[-1]['end']+0.12,start+0.25))
    if 13.0 < start < 14.58: continue
    opening=start<4.65
    final=start>=15.78
    emphasis=text.lower() in {'stuck','carefully','one decision','90%','happiness','or misery','life','to be fair'}
    if final:
        stop=16.52
    if not final and index + 1 < len(phrases):
        stop = min(stop, words[phrases[index + 1][1]]['start'])
    if text == 'all that they have':
        stop = min(stop, 396 / fps)
    size = 144 if text.lower() in {'carefully','happiness','90%'} else 116 if emphasis else 89 if opening else 80
    layer={'t':start,'dur':round(stop-start,3),'text':text,'x':590 if final else 75 if opening else 125,
           'y':900 if final else 720 if opening else 1000,'width':390 if final else 430 if opening else 830,'size':size,
           'font':'inter','weight':700,'align':'left' if opening else 'center','surface':'difference',
           'motion':{'inSec':0.09,'outSec':0.08,'rise':7,'scaleFrom':0.96},
           'depth':'behind' if opening else 'front'}
    if final:
        layer.update({'x':612 if text=='to be' else 710, 'y':880 if text=='to be' else 861,
                      'width':136 if text=='to be' else 300, 'size':83 if text=='to be' else 140,
                      'align':'left', 'surface':'solid', 'color':'#ffffff', 'blend':'normal', 'shadow':'none'})
    if len(ws)==len(text.split()): layer['wordTimes']=[w['start'] for w in ws]
    if opening:
        x, y, group_stop = opening_layouts[index]
        layer.update(x=x, y=y, width=1010-x, depth='front', dur=round(group_stop-start,3))
    layers.append(layer)
props={'src':'clips/henry-cavill-caption-review/picture.mp4','bgSrc':None,'fps':30000/1001,
       'durationSec':496*1001/30000,'srcWidth':720,'srcHeight':1280,'widthFrac':1,
       'shots':[{'t':0,'x':0.5}],'track':[],'yAnchor':0.5,'hook':'','hookPersist':False,
       'hookDurationSec':0,'captions':[],'punchIns':[],'watermark':None,'loopFadeSec':0,
       'style':'frame','grade':{'brightness':1,'contrast':1,'saturate':1},'accent':'#ffffff',
       'intro':None,'music':None,
       'cutaways':[{'src':'clips/henry-cavill-caption-review/large-and-lastly.mp4', 't':397/fps, 'dur':40/fps}],
       'referenceEdit':{'profile':'editorial','frame':{'x':0,'y':0,'width':1080,'height':1920},
       'layeredOnly':True,'layers':layers,'foregroundMasks':[{'t':0,'dur':4.65,'keyframes':[
        {'t':0,'points':[[330,650],[390,500],[570,470],[690,560],[720,850],[890,1350],[180,1350],[280,850]]},
        {'t':3.8,'points':[[330,650],[390,500],[570,470],[690,560],[720,850],[890,1350],[180,1350],[280,850]]},
        {'t':3.85,'points':[[400,800],[440,650],[560,620],[650,690],[690,1050],[740,1410],[250,1410],[310,1050]]},
        {'t':4.65,'points':[[400,800],[440,650],[560,620],[650,690],[690,1050],[740,1410],[250,1410],[310,1050]]}]}]}}
(work/'caption-review-props-v4-DRAFT.json').write_text(json.dumps(props,indent=2,ensure_ascii=False),encoding='utf-8')
print('Draft composition written. Mask geometry and word timing require review.')
