from pathlib import Path
import json, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

root = Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0, str(root / 'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard
from transition_sounds import resolve_cues, mix_transition_sounds
require_guard()

project = Path(__file__).parent
library = root / 'Main/shorts-clips/Movie Clips'
source = project / '01-source-proof.mp4'
out = project / 'caption-free-PRIVATE-REVIEW.mp4'
silent_effect = project / 'caption-free-picture-and-dialogue.mp4'
card = project / 'and-lastly-card.png'
mask = project / 'rounded-mask.png'

image = Image.new('RGB', (650,650), 'white')
draw = ImageDraw.Draw(image)
font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 53)
label = '“and lastly”'
draw.text((325,325), label, fill='black', font=font, anchor='mm')
image.save(card)
rounded = Image.new('L',(650,650),0)
ImageDraw.Draw(rounded).rounded_rectangle((0,0,649,649),radius=34,fill=255)
rounded.save(mask)

shots = [
 (4.65, 7.00, 'About Time - Mary/00892000-mary-and-tim-eat-together.mp4', 1.0),
 (7.00, 9.72, 'Good Will Hunting/03393000-will-and-skylar-kiss.mp4', 1.0),
 (9.72, 10.12, 'Good Will Hunting/03599000-will-reacts-in-room-argument.mp4', 1.0),
 (10.12, 11.60, 'The Pursuit of Happyness/01295000-father-talks-to-son-on-bench.mp4', 1.0),
 (11.60, 13.22, 'Fight Club/00177516-embrace-at-the-support-group.mp4', 0.3),
 (14.10, 15.20, 'Luke Glanton - The Place Beyond the Pines/00084793-luke-looks-down-at-night.mp4', 0.2),
]
cmd = [FFMPEG, '-v','warning','-y','-threads','2','-filter_complex_threads','2','-i',str(source)]
for start,end,path,offset in shots:
    cmd += ['-ss',str(offset),'-i',str(library / path)]
card_index = len(shots)+1
mask_index = card_index+1
cmd += ['-loop','1','-framerate','30000/1001','-i',str(card),'-loop','1','-framerate','30000/1001','-i',str(mask)]
filters = ['[0:v]crop=720:500:280:0,scale=650:650:force_original_aspect_ratio=increase,crop=650:650,setsar=1,fps=30000/1001,format=yuv420p[base0]']
for i,(start,end,path,offset) in enumerate(shots,1):
    source_crop = 'crop=ih:ih:iw*0.07:0,' if i == 6 else ''
    filters += [f'[{i}:v]trim=duration={end-start},setpts=PTS-STARTPTS+{start}/TB,{source_crop}scale=650:650:force_original_aspect_ratio=increase,crop=650:650,setsar=1,fps=30000/1001[shot{i}]',
                f'[base{i-1}][shot{i}]overlay=0:0:eof_action=pass:repeatlast=0:enable=\'between(t,{start},{end})\'[base{i}]']
filters += [f'[{card_index}:v]trim=duration=0.88,setpts=PTS-STARTPTS+13.22/TB[card]',
            f'[base{len(shots)}][card]overlay=0:0:eof_action=pass:repeatlast=0:enable=\'between(t,13.22,14.10)\'[picture]',
            f'[{mask_index}:v]format=gray,trim=duration=16.55,setpts=PTS-STARTPTS[mask]',
            "[picture]drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='between(t,13.213,13.246)'[flash]",
            '[flash]format=rgba[rgba]', '[rgba][mask]alphamerge[rounded]',
            'color=black:s=720x1280:r=30000/1001:d=16.55[background]',
            '[background][rounded]overlay=35:315:shortest=1:format=auto,format=yuv420p[v]']
cmd += ['-filter_complex',';'.join(filters),'-map','[v]','-map','0:a:0','-c:v','h264_nvenc','-b:v','6M','-c:a','copy','-frames:v','496','-movflags','+faststart',str(silent_effect)]
subprocess.run(ffmpeg_command(cmd),check=True)
fps = 30000/1001
cue = [{'frame':round(13.22*fps), 'preset':'retro-exposure', 'soundId':'camera-shutter-click'}]
assets = resolve_cues(cue,496,fps,{'frame':{'x':35,'y':315,'width':650,'height':650}})
mix_transition_sounds(silent_effect,out,cue,assets,fps,496)
(project / 'caption-free-shot-map.json').write_text(json.dumps({'source':str(source),'fps':'30000/1001','frames':496,'shots':[{'start':a,'end':b,'file':str(library / p),'offset':o} for a,b,p,o in shots],'card':{'start':13.22,'end':14.10,'text':'and lastly'},'shutter':cue,'status':'private review; temporary About Time substitute; movie reuse unresolved'},indent=2),encoding='utf8')
print('Built',out,flush=True)
