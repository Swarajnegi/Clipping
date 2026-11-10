"""Guarded technical checks and visual samples; not an audio review."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFPROBE,FFMPEG,require_guard,run
require_guard(gpu=False)
home=Path(__file__).resolve().parent;qa=home/'qa'/'rendered';qa.mkdir(parents=True,exist_ok=True)
result=[]
for n in (1,2,4):
 p=ROOT/'out'/f'matthew_20261103_{n:02d}'/'clip_01.mp4'
 data=json.loads(subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True).stdout)
 v=next(x for x in data['streams'] if x['codec_type']=='video'); a=next(x for x in data['streams'] if x['codec_type']=='audio')
 assert (v['width'],v['height'],v['r_frame_rate'])==(1080,1920,'25/1')
 assert float(data['format']['duration'])<=80.1
 run([FFMPEG,'-v','error','-i',str(p),'-f','null','-'])
 run([FFMPEG,'-v','error','-y','-i',str(p),'-vf','fps=1/2,scale=270:480,tile=4x4',str(qa/f'{n:02d}-%02d.jpg')])
 result.append({'clip':n,'duration':data['format']['duration'],'frames':v.get('nb_frames'),'fps':v['r_frame_rate'],'audio_codec':a['codec_name'],'full_decode':'passed','image_samples':'one frame per two seconds'})
(qa/'technical-checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
