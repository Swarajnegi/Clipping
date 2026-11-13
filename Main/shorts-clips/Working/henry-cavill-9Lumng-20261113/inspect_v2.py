from pathlib import Path
import sys, subprocess, io
from PIL import Image, ImageDraw
root=Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0,str(root/'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard
require_guard()
p=Path(__file__).parent; lib=root/'Main/shorts-clips/Movie Clips'
items=[('cavill '+str(t),p/'01-source-proof.mp4',t) for t in (0.1,1,2,2.5,3,3.2,3.5,4.3,15.9)]
items += [('pines '+str(t),lib/'Luke Glanton - The Place Beyond the Pines/00222305-figure-alone-beside-open-water.mp4',t) for t in (0.1,0.7,1.4)]
items += [('happyness '+str(t),lib/'The Pursuit of Happyness/01452000-chris-checks-notes-on-steps.mp4',t) for t in (3.5,4.0,4.5)]
sheet=Image.new('RGB',(4*320,4*205),'#101010'); d=ImageDraw.Draw(sheet)
for i,(label,path,t) in enumerate(items):
 data=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2','-f','image2pipe','-vcodec','png','-']),stdout=subprocess.PIPE,check=True).stdout
 x=i%4*320;y=i//4*205;d.text((x+4,y+4),label,fill='white');sheet.paste(Image.open(io.BytesIO(data)).convert('RGB'),(x,y+20))
sheet.save(p/'v2-source-study.jpg',quality=93)
