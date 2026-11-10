"""LAYER: Reviewer. THE BIG PICTURE: resolve detector flags against actual painted frames.
THE FLOW: retained raw detections -> exact-frame crops + overlay evidence, never automatic dismissal.
"""
import json,subprocess,sys
from pathlib import Path
from io import BytesIO
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
from PIL import Image,ImageDraw
require_guard(gpu=True)
reports=json.loads((P/'qa/automated.json').read_text(encoding='utf-8'))
geometry=json.loads((P/'qa/caption-geometry.json').read_text(encoding='utf-8'))['measurements']
for report in reports:
    flags=report['caption_face_overlaps']
    if not flags:continue
    slug=report['clip'];qa=P/'qa'/slug;tiles=[]
    for flag in flags:
        f=flag['frame'];data=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(P/'drafts'/f'{slug}-music-free.mp4'),
            '-vf',f"select='eq(n,{f})'",'-fps_mode','vfr','-frames:v','1','-f','image2pipe','-c:v','png','-']),capture_output=True,check=True).stdout
        im=Image.open(BytesIO(data)).convert('RGB');im.save(qa/f'flag-{f:04d}-4k.png')
        annotated=im.copy();draw=ImageDraw.Draw(annotated)
        x,y,w,h=[v*2 for v in flag['face']];draw.rectangle((x,y,x+w,y+h),outline='red',width=6)
        for layer in geometry:
            if layer['clip']==slug and layer['text']==flag['caption'] and layer['t']<=f/25<layer['t']+layer['dur']:
                for b in layer['boxes']:
                    draw.rectangle((b['x']*2,b['y']*2,(b['x']+b['w'])*2,(b['y']+b['h'])*2),outline='#00ff66',width=4)
        annotated.save(qa/f'flag-{f:04d}-annotated.png')
        crop=im.crop((0,1900,2160,2750)) if slug.startswith('04') else im
        crop.thumbnail((864,864))
        tile=Image.new('RGB',(864,914),'#101418');tile.paste(crop,(0,50));ImageDraw.Draw(tile).text((10,8),f"{f}: {flag['caption']}",fill='white');tiles.append(tile)
    sheet=Image.new('RGB',(1728,914*((len(tiles)+1)//2)),'#101418')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*864,(i//2)*914))
    sheet.save(qa/'flag-review.jpg',quality=98)
print('FLAG_FRAMES_READY',flush=True)
