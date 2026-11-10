"""Preserve prior dialogue packets and make review evidence for the revision."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,FFPROBE,require_guard,run
require_guard(gpu=False)
HOME=Path(__file__).resolve().parent
old=HOME/'drafts/01-commit-fully-DRAFT.mp4'
new=ROOT/'out/matthew_20261104_01_placement_v2/clip_01.mp4'
dest=HOME/'drafts/01-commit-fully-placement-v2-DRAFT.mp4'
run([FFMPEG,'-v','error','-y','-i',str(new),'-i',str(old),'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',str(dest)])
def packets(path):
 out=subprocess.run([FFPROBE,'-v','error','-select_streams','a:0','-show_packets','-show_data_hash','sha256',
  '-show_entries','packet=pts_time,dts_time,duration_time,size,data_hash','-of','json',str(path)],capture_output=True,text=True,check=True)
 return json.loads(out.stdout)['packets']
assert packets(old)==packets(dest),'Source dialogue packets/timestamps changed'
info=json.loads(subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(dest)],capture_output=True,text=True,check=True).stdout)
v=next(s for s in info['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1080,1920,'25/1',1163)
run([FFMPEG,'-v','error','-i',str(dest),'-f','null','-'])
qa=HOME/'qa/placement-v2';qa.mkdir(parents=True,exist_ok=True)
run([FFMPEG,'-v','error','-y','-i',str(dest),'-vf','fps=2,scale=216:384,tile=5x5',str(qa/'samples-%02d.jpg')])
(qa/'checks.json').write_text(json.dumps({'frames':1163,'fps':'25/1','duration':info['format']['duration'],
 'dialogue_packet_payload_and_timing':'identical to prior draft','complete_decode':'passed',
 'visual_samples':'every 0.5 seconds; inspect images; not continuous playback',
 'transcript_accuracy':'previously noted uncertainties remain unverified'},indent=2),encoding='utf-8')
print(dest)
