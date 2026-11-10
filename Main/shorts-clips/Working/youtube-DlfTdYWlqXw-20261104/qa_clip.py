"""Decode every output frame on CUDA; check faces, caption geometry and dialogue.

Produces inspectable per-phrase contact sheets. Does not claim human playback.
"""
import argparse,json,math,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard,probe
require_guard(gpu=True)
import cv2,numpy as np
from PIL import Image,ImageDraw
cv2.setNumThreads(2)
parser=argparse.ArgumentParser();parser.add_argument('slug');args=parser.parse_args()
slug=args.slug;work_id='belmar_20261104_4k_'+slug
decision=next(d for d in json.loads((PROJECT/'edit-decisions.json').read_text(encoding='utf-8')) if d['slug']==slug)
props=json.loads((ROOT/'work'/work_id/'props/clip_01.json').read_text(encoding='utf-8'))
video=PROJECT/'drafts'/(slug+'-music-free-DRAFT.mp4')
source=ROOT/'public'/props['src'];media=probe(video)
qa=PROJECT/'qa'/slug;qa.mkdir(parents=True,exist_ok=True)
geometry=json.loads((PROJECT/'qa/caption-geometry.json').read_text(encoding='utf-8'))
measurements=[m for m in geometry['measurements'] if m['clip']==slug]
assert not any(m['wrapped'] or not m['safe'] for m in measurements)
assert not any(c[0]==slug for c in geometry['collisions'])
manifest=json.loads((PROJECT/'authoring'/slug/'caption-pages.json').read_text(encoding='utf-8'))
layers=props['referenceEdit']['layers']
sample_frames={}
for page in manifest:
    same=[l for l in layers if page['start']-.001<=l['t']<page['end']]
    last=max(max(l['wordTimes']) for l in same)
    at=min(page['end']-.04,max(page['start'],last+.16))
    frame=min(round(media.duration*25)-1,max(0,round(at*25)))
    sample_frames.setdefault(frame,[]).append(page)
for shot in decision['shots']:
    for at in [shot['t'],shot['t']+.12]:
        frame=min(round(media.duration*25)-1,max(0,round(at*25)))
        sample_frames.setdefault(frame,[]).append(dict(page='cut',rows=[shot['view']],start=at,end=at))

W,H=432,768
command=ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-hwaccel_output_format','cuda','-i',str(video),
    '-map','0:v:0','-an','-vf',f'scale_cuda={W}:{H},hwdownload,format=nv12,format=bgr24','-f','rawvideo','-pix_fmt','bgr24','-'])
stderr_path=qa/'decode.stderr.log'
tiles=[];face_missing=[];overlaps=[];face_frames=0;max_face_bottom=0;i=0
with stderr_path.open('wb') as err:
    proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=err)
    detector=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),'',(W,H),score_threshold=.75)
    size=W*H*3
    try:
        while True:
            buf=proc.stdout.read(size)
            if not buf:break
            if len(buf)!=size:raise RuntimeError(f'Incomplete decoded frame {i}')
            frame=np.frombuffer(buf,np.uint8).reshape(H,W,3)
            _,faces=detector.detect(frame)
            t=i/25
            active=[m for m in measurements if m['t']<=t<m['t']+m['dur']]
            if faces is None:face_missing.append(i)
            else:
                face_frames+=1
                for face in faces:
                    x,y,w,h=map(float,face[:4]);max_face_bottom=max(max_face_bottom,(y+h)*2.5)
                    # Face plus a conservative 25-logical-pixel margin.
                    fx,fy,fw,fh=x*2.5-25,y*2.5-25,w*2.5+50,h*2.5+50
                    for m in active:
                        for b in m['boxes']:
                            if fx<b['x']+b['w'] and b['x']<fx+fw and fy<b['y']+b['h']+12 and b['y']<fy+fh:
                                overlaps.append(dict(frame=i,t=t,layer=m['index'],text=m['text'],face=[fx,fy,fw,fh]))
            if i in sample_frames:
                # Head through caption block. Full-frame overview is saved separately.
                tile=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).crop((0,140,W,600)).resize((324,345))
                panel=Image.new('RGB',(324,385),'#151515');panel.paste(tile,(0,20))
                draw=ImageDraw.Draw(panel)
                draw.text((6,3),f'{t:.2f}s | '+','.join(str(p['page']) for p in sample_frames[i]),fill='white')
                # Audio wording lives in caption-pages.json; image retains actual burned-in words.
                tiles.append(panel)
            i+=1
    finally:
        proc.stdout.close()
        code=proc.wait()
    if code:raise RuntimeError(f'CUDA decode failed ({code}): {stderr_path.read_text()}')
for start in range(0,len(tiles),12):
    subset=tiles[start:start+12];sheet=Image.new('RGB',(324*3,385*4),'#151515')
    for j,tile in enumerate(subset):sheet.paste(tile,((j%3)*324,(j//3)*385))
    sheet.save(qa/f'phrases-{start//12+1:02d}.jpg',quality=95)

def audio(path):
    result=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True)
    return np.frombuffer(result.stdout,dtype=np.float32)
original=audio(source);rendered=audio(video)
audio_checks=[]
for start in range(8000,min(len(original),len(rendered))-16000,64000):
    a=original[start:start+16000].astype(np.float64);b=rendered[start:start+16000].astype(np.float64)
    if np.mean(a*a)<1e-7:continue
    best=(-1,None)
    # Check shifts through +/-40 ms, sampled at 1 ms; zero shift is expected.
    for lag in range(-640,641,16):
        x=a[max(0,lag):min(len(a),len(a)+lag)]
        y=b[max(0,-lag):min(len(b),len(b)-lag)]
        score=float(np.dot(x,y)/(np.linalg.norm(x)*np.linalg.norm(y)+1e-20))
        if score>best[0]:best=(score,lag)
    audio_checks.append(dict(at=start/16000,correlation=best[0],lag_ms=best[1]/16))
expected=round(props['durationSec']*25)
receipt=dict(file=str(video),size=[media.width,media.height],fps=media.fps,
             decoded_frames=i,expected_frames=expected,complete_decode=i==expected,
             face_detection_frames=face_frames,face_detection_coverage=face_frames/max(i,1),
             face_missing_frames=face_missing,caption_face_overlaps=overlaps,max_face_bottom_logical=max_face_bottom,
             caption_geometry_checked=True,phrase_samples=len(tiles),
             dialogue_audio_checks=audio_checks,audio_peak=float(np.max(np.abs(rendered))),
             audio_samples=len(rendered),source_audio_samples=len(original),
             scope='Every frame decoded and face-detector checked; every caption page sampled. Audio waveform compared to clean assembled source. Direct listening not claimed.')
(qa/'technical-review.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
summary={k:v for k,v in receipt.items() if k not in ['face_missing_frames','dialogue_audio_checks','caption_face_overlaps','scope']}
summary['overlaps']=len(overlaps);summary['worst_audio_correlation']=min(c['correlation'] for c in audio_checks)
summary['max_audio_lag_ms']=max(abs(c['lag_ms']) for c in audio_checks)
print(json.dumps(summary),flush=True)
assert i==expected and not overlaps
assert all(c['correlation']>.98 and abs(c['lag_ms'])<=40 for c in audio_checks)
