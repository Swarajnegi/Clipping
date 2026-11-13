from pathlib import Path
import io, json, subprocess, sys
from PIL import Image, ImageDraw
root=Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0,str(root/'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard
require_guard()
project=Path(__file__).parent
video=project/'caption-free-v2-PRIVATE-REVIEW.mp4'
times=[0.2,3.6,3.9,4.3,4.8,6.3,7.4,9.5,10.4,11.7,13.3,14.2,14.7,15.6,15.9,16.2]
sheet=Image.new('RGB',(4*180,4*345),'#181818')
d=ImageDraw.Draw(sheet)
for i,t in enumerate(times):
    cmd=ffmpeg_command([FFMPEG,'-v','error','-ss',str(t),'-i',str(video),'-frames:v','1','-vf','scale=180:320','-f','image2pipe','-vcodec','png','-'])
    img=Image.open(io.BytesIO(subprocess.run(cmd,stdout=subprocess.PIPE,check=True).stdout)).convert('RGB')
    x=(i%4)*180; y=(i//4)*345
    d.text((x+5,y+4),f'{t:.2f}s',fill='white');sheet.paste(img,(x,y+20))
sheet.save(project/'caption-free-v2-QA.jpg',quality=92)
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(video),'-map','0:v','-map','0:a','-f','null','-']),check=True)
print('Video and audio decode completed; sampled',times)
