"""Original 4K covers from clean source frames and licensed bundled type."""
import argparse,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
P=Path(__file__).resolve().parent;ROOT=P.parents[3];F=P/'finish-v1'
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command
require_guard(gpu=True)
parser=argparse.ArgumentParser();parser.add_argument('--id');args=parser.parse_args()
fonts=ROOT/'.agents/skills/viral-shorts/assets/fonts'
designs={
'01':(10.2,'JAMES HOLLIS',[('CHOOSE A','inter',138),('larger life.','italic',202)]),
'02':(21.8,'DAVID GOGGINS',[('LEARN TO','inter',150),('FAIL.','inter',230)]),
'03':(12.7,'JAMES CLEAR',[('SAME GOAL.','inter',148),('DIFFERENT RESULT.','inter',112)]),
'04':(22.0,'MEL ROBBINS',[('STOP PROVING','inter',142),('your worth.','italic',200)]),
'05':(.9,'JIMMY CARR',[('THE WORK','inter',154),("YOU DON'T SEE.",'inter',142)])}
def font(name,size):
 f=ImageFont.truetype(str(fonts/('InterVariable.woff2' if name=='inter' else 'CormorantGaramond-Italic.ttf')),size)
 if name=='inter':
  try:f.set_variation_by_axes([800 if a['name']==b'Weight' else min(32,a['maximum']) if a['name']==b'Optical Size' else a['default'] for a in f.get_variation_axes()])
  except OSError:pass
 return f
def tracked(draw,text,y,face,color,tracking):
 spans=[face.getlength(c) for c in text];w=sum(spans)+tracking*(len(text)-1);x=(2160-w)/2
 for c,span in zip(text,spans):draw.text((x,y),c,font=face,fill=color,stroke_width=0);x+=span+tracking
records=json.loads((F/'thumbnails/provenance.json').read_text()) if (F/'thumbnails/provenance.json').exists() else []
for r in json.loads((P/'proofs.json').read_text()):
 id=r['id'];number=id[:2];time,name,lines=designs[number]
 if args.id and id!=args.id:continue
 props=json.loads((F/'props'/(id+'.json')).read_text(encoding='utf-8'))
 shot=next(s for s in reversed(props['shots']) if s['t']<=time)
 cw=round(shot['w']*3840);left=round(max(0,min(3840-cw,shot['x']*3840-cw/2))/2)*2
 raw=F/'thumbnails'/(id+'-source-frame.png')
 subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-ss',str(time),
  '-i',str(ROOT/'public'/props['src']),'-frames:v','1','-vf',f'crop={cw}:{cw}:{left}:(ih-oh)/2,scale=1960:1960',str(raw)]),check=True)
 square=Image.open(raw).convert('RGBA')
 # Local lower-image shade supports cover text; it is not a spoken-caption layer.
 shade=Image.new('RGBA',square.size,(0,0,0,0));sd=ImageDraw.Draw(shade)
 for y in range(1960):
  a=round((230 if number=='04' else 210)*max(0,min(1,(y-(900 if number=='04' else 1000))/(600 if number=='04' else 850)))**.85)
  sd.line((0,y,1959,y),fill=(0,0,0,a))
 square=Image.alpha_composite(square,shade)
 mask=Image.new('L',(1960,1960),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,1959,1959),radius=96,fill=255)
 canvas=Image.new('RGB',(2160,3840),'black');canvas.paste(square.convert('RGB'),(100,940),mask)
 d=ImageDraw.Draw(canvas)
 tracked(d,name,847,font('inter',48),(170,177,185),5)
 y=2180
 for text,kind,size in lines:
  face=font(kind,size)
  while face.getlength(text)>1740:size-=2;face=font(kind,size)
  tracked(d,text,y,face,(244,246,247),-size*.025)
  y+=round(size*1.15)
 dest=F/'thumbnails'/(id+'-thumbnail.jpg')
 if dest.exists() and number=='04':
  old=dest.with_name(id+'-thumbnail-draft-v0.jpg')
  if not old.exists():dest.rename(old)
 canvas.save(dest,quality=97,subsampling=0)
 canvas.resize((360,640)).save(F/'qa'/(id+'-thumbnail-phone.jpg'),quality=95)
 canvas.crop((0,840,2160,3000)).resize((600,600)).save(F/'qa'/(id+'-thumbnail-square.jpg'),quality=95)
 records=[record for record in records if record['id']!=id]
 records.append({'id':id,'file':str(dest),'dimensions':[2160,3840],'source':props['src'],
  'source_assembly_time':time,'source_frame':round(time*r['fps']),'headline':' / '.join(t for t,_,_ in lines),
  'fonts':'Bundled Inter variable and Cormorant Garamond Italic; OFL files retained',
  'assets':'Clean source frame plus original programmatic typography/gradient; no borrowed graphic assets',
  'editorial_headline_not_spoken_quote':True,'review_status':'Phone and centred-square previews prepared; assistant inspection pending'})
 print('COVER',id,flush=True)
(F/'thumbnails/provenance.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if len(records)==5:
 gallery=Image.new('RGB',(1800,640),'black')
 for i,record in enumerate(sorted(records,key=lambda r:r['id'])):
  gallery.paste(Image.open(record['file']).resize((360,640)),(i*360,0))
 gallery.save(F/'qa/thumbnail-gallery.jpg',quality=96)
