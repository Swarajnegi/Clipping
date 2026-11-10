"""Full decode, native picture clock, identical audio and every-frame face checks."""
import argparse,json,math,subprocess,sys
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;ROOT=P.parents[3];F=P/'finish-v1';sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard,probe
from motion_edit import audio_packets,decode,video_clock
require_guard(gpu=True);cv2.setNumThreads(2)
parser=argparse.ArgumentParser();parser.add_argument('--id',required=True);args=parser.parse_args()
r=next(x for x in json.loads((P/'proofs.json').read_text()) if x['id']==args.id)
id=r['id'];path=F/'finished'/(id+'-music-free.mp4');props=json.loads((F/'props'/(id+'.json')).read_text(encoding='utf-8'))
layers=props['referenceEdit']['layers'];plan=json.loads((F/'props'/(id+'-caption-plan.json')).read_text(encoding='utf-8'))
assert len(layers)==len(plan['words'])
assert all(l['surface']=='difference' and l['blend']=='difference' and l['color']=='#ffffff' and l['fillOpacity']>0 for l in layers)
assert all(55<l['x'] and l['x']+l['width']<1025 and 490<l['y'] and l['y']+l['size']*1.25<1430 for l in layers)
clock=video_clock(path);assert clock['regular'] and clock['frames']==r['frames'] and clock['rate']==r['rate'],clock
assert abs(clock['first_pts'])<.001 and abs(clock['duration']-r['duration'])<.001
assert audio_packets(path)==audio_packets(ROOT/'public'/props['src'])
audio=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-vn','-f','null','-']),capture_output=True,text=True,check=True)
assert not audio.stderr.strip()
# Representative frames for EVERY phrase, first three seconds, all camera cuts and ending.
times=[0,.2,.6,1,1.5,2,2.5,2.95,r['duration']-.1]
times += [max(g['start']+.1,g['end']-.15) for g in plan['groups']]
times += [s['t']+.04 for s in props['shots']]
wanted={min(r['frames']-1,round(t*r['fps'])) for t in times}
det=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),'',(360,640),score_threshold=.75)
proc=subprocess.Popen(ffmpeg_command([FFMPEG,'-v','error','-readrate','2','-hwaccel','cuda','-hwaccel_output_format','cuda','-i',str(path),
 '-an','-vf','scale_cuda=360:640:format=yuv420p,hwdownload,format=yuv420p','-pix_fmt','bgr24','-f','rawvideo','-']),stdout=subprocess.PIPE)
count=0;detected=0;overlaps=[];frames=[]
while True:
 raw=proc.stdout.read(360*640*3)
 if len(raw)!=360*640*3:break
 frame=np.frombuffer(raw,np.uint8).reshape(640,360,3);t=count/r['fps'];_,faces=det.detect(frame)
 hits=[] if faces is None else [f[:4] for f in faces if 156<f[1]+f[3]/2<484 and f[3]>=22]
 detected+=bool(hits)
 for face in hits:
  fx,fy,fw,fh=face
  for l in layers:
   if not l['t']<=t<l['t']+l['dur']:continue
   x,y,w,h=l['x']/3,l['y']/3,l['width']/3,l['size']*1.12/3
   if min(x+w,fx+fw)>max(x,fx) and min(y+h,fy+fh)>max(y,fy):
    overlaps.append({'frame':count,'time':t,'word':l['text'],'face':face.tolist()})
 if count in wanted:frames.append((count,Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))))
 count+=1
assert proc.wait()==0 and count==r['frames']
# Keep sheets readable without emitting a single enormous image.
sheets=[]
for page in range(math.ceil(len(frames)/12)):
 selected=frames[page*12:(page+1)*12];sheet=Image.new('RGB',(4*240,math.ceil(len(selected)/4)*450),'#101214');d=ImageDraw.Draw(sheet)
 for i,(n,im) in enumerate(selected):
  x=(i%4)*240;y=(i//4)*450;sheet.paste(im.resize((240,427)),(x,y+22));d.text((x+5,y+4),f'{n/r["fps"]:.2f}s / f{n}',fill='white')
 dest=F/'qa'/(id+f'-phrase-sheet-{page+1}.jpg');sheet.save(dest,quality=94);sheets.append(str(dest))
record={'id':id,'file':str(path),'picture_clock':clock,'full_picture_decode_frames':count,'full_audio_decode':True,
 'audio_packet_payload_and_timestamps_identical_to_approved_assembly':True,
 'caption_words':len(layers),'all_words_white_difference':True,'every_frame_face_detection':True,
 'frames_with_detected_face':detected,'face_detection_coverage':detected/count,
 'caption_face_intersections':overlaps,'phrase_and_opening_sheets':sheets,
 'owner_content_approval':'All five approved for final exports by user message 8 November 2026',
 'continuous_final_listening':'Not independently performed; unchanged approved-cut audio, full decoding, word alignment and frame QA do not replace direct listening.',
 'caption_timing_limit':'Mostly CUDA word-aligned and frame-quantized. Goggins missing fast words interpolated from official transcript; exact one-frame manual certification not claimed.'}
(F/'qa'/(id+'-full-qa.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
print('QA',id,count,'face coverage',detected/count,'overlaps',len(overlaps),flush=True)
if overlaps:raise RuntimeError('Inspect caption/face intersections before delivery')
