from pathlib import Path
import subprocess, sys
root=Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0,str(root/'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard
from PIL import Image, ImageDraw, ImageFont
require_guard()
work=Path(__file__).parent
bundle=work/'caption-review-draft/bundle'
card = Image.new('RGB', (720, 1280), 'black')
draw = ImageDraw.Draw(card)
draw.rounded_rectangle((35, 315, 684, 964), radius=34, fill='white')
font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 68)
draw.text((360, 640), '“and lastly”', fill='black', font=font, anchor='mm')
card_png = work / 'large-and-lastly.png'
card.save(card_png)
card_video = bundle / 'public/clips/henry-cavill-caption-review/large-and-lastly.mp4'
subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-loop', '1', '-framerate',
    '30000/1001', '-i', str(card_png), '-frames:v', '40', '-c:v', 'h264_nvenc',
    '-b:v', '3M', '-pix_fmt', 'yuv420p', str(card_video)]), cwd=root, check=True)
output = (work / 'caption-review-frames-v4-DRAFT').relative_to(root)
output.mkdir(exist_ok=True)
cmd=[str(root/'.runtime/node/node.exe'),str(root/'node_modules/@remotion/cli/remotion-cli.js'),
     'render',str(bundle),'ViralShort',str(output),'--sequence','--image-format=png',
     '--frames=0-495',f'--props={work / "caption-review-props-v4-DRAFT.json"}',
     '--scale=0.667','--gl=angle','--concurrency=1','--offthreadvideo-video-threads=2',
     '--offthreadvideo-cache-size-in-bytes=134217728']
subprocess.run(cmd,cwd=root,check=True)
print('Review frame sequence complete.')
