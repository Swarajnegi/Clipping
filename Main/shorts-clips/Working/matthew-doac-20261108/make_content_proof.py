"""Inexpensive content proof. Original dialogue, no captions/music/branding; not final master."""
import json,subprocess,sys,hashlib,math
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command,probe,encoder
from build import assemble
from prep import scene_cuts
from motion_edit import audio_packets,decode
import numpy as np
import cv2
require_guard(gpu=True);cv2.setNumThreads(2)
BASE=P.parent/'content-discovery-20261108'
source=BASE/'source-review/matthew-offer-h264.mp4'
permission=json.loads((BASE/'review-v2/permission.json').read_text(encoding='utf-8'))
assert permission['source_url']=='https://www.youtube.com/watch?v=QMzxNfX-uAg' and permission['reuse_basis']
pieces=[(9.44,10.72),(11.44,16.88),(17.44,27.72),(31.72,34.12),(34.56,43.68),(48.24,50.08)]
frames=round(sum(b-a for a,b in pieces)*25);assert frames==759
drafts=P/'drafts';drafts.mkdir(exist_ok=True);qa=P/'qa';qa.mkdir(exist_ok=True)
clean=P/'offer-clean-assembly.mp4';output=drafts/'01-the-offer-content-proof.mp4'
if clean.exists() or output.exists():raise FileExistsError('Preserve earlier proof; version revisions')
spans=assemble(source,pieces,clean,'25/1');media=probe(clean)
assert media.fps==25
cuts=scene_cuts(media);bounds=[0]+cuts+[media.duration]
tw=640;th=round(tw*media.height/media.width/2)*2
det=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),'',(tw,th),score_threshold=.75)
cmd=ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(clean),'-an','-vf',f'fps=5,scale={tw}:{th}','-pix_fmt','bgr24','-f','rawvideo','-'])
process=subprocess.Popen(cmd,stdout=subprocess.PIPE);samples=[];i=0
while True:
 buf=process.stdout.read(tw*th*3)
 if len(buf)!=tw*th*3:break
 frame=np.frombuffer(buf,np.uint8).reshape(th,tw,3);_,faces=det.detect(frame)
 chosen=None
 if faces is not None:
  faces=faces[(faces[:,1]+faces[:,3]/2)<th*.72]
  if len(faces):
   areas=faces[:,2]*faces[:,3];big=faces[areas>=areas.max()*.35]
   # Source sheets establish Matthew as the LEFT speaker in this episode's two-shots.
   chosen=big[np.argmin(big[:,0])] if len(big)>1 and np.ptp(big[:,0])>tw*.2 else faces[np.argmax(areas)]
 samples.append({'t':i/5,'box':chosen[:4].tolist() if chosen is not None else None});i+=1
assert process.wait()==0
shots=[];cropw=int(media.height*9/16)//2*2
for a,b in zip(bounds,bounds[1:]):
 faces=[s['box'] for s in samples if a<=s['t']<b and s['box']]
 x=float(np.median([(f[0]+f[2]/2)/tw for f in faces])) if faces else .5
 left=max(0,min(media.width-cropw,round(x*media.width-cropw/2)))//2*2
 shots.append({'start':a,'end':b,'x':left,'face_samples':len(faces)})
expr=str(shots[-1]['x'])
for shot in reversed(shots[:-1]):expr=f'if(lt(t,{shot["end"]:.3f}),{shot["x"]},{expr})'
vf=f"crop={cropw}:{media.height}:'{expr}':0,scale=720:1280"
with (qa/'content-proof-render.log').open('w',encoding='utf-8') as log:
 subprocess.run(ffmpeg_command([FFMPEG,'-y','-hwaccel','cuda','-i',str(clean),'-vf',vf,'-c:v','h264_nvenc','-preset','p4','-b:v','5M','-r','25','-c:a','copy','-map_metadata','-1','-movflags','+faststart',str(output)]),check=True,stdout=log,stderr=log)
assert audio_packets(clean)==audio_packets(output)
result=decode(output,frames)
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-i',str(output),'-an','-vf','fps=1/2,scale=216:384,tile=5x3:padding=4:margin=4','-frames:v','1',str(qa/'content-proof-sheet.jpg')]),check=True)
record={'source_url':permission['source_url'],'reuse_basis':permission['reuse_basis'],'source_context_start':6132,'local_source_pieces':pieces,
 'original_source_pieces':[[6132+a,6132+b] for a,b in pieces],'assembled_spans':spans,'duration':frames/25,'frames':frames,'fps':25,
 'dimensions':[720,1280],'source_resolution':[media.width,media.height],'file':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
 'shots':shots,'decode':result,'audio_packets_equal_to_clean_assembly':True,'added_music':False,'added_captions':False,'added_branding':False,
 'meaning':'Chronological price escalation and final refusal. Removed the I said setup, long gaps and the abandoned This could be/I could make this work aside; retained the joke/reaction beat.',
 'status':'content proof only; source reviewed by provider, assembled proof continuous listening pending. Not an upload-ready master.'}
(P/'content-proof.json').write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record,indent=2),flush=True)
