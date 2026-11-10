"""Compare every decoded proof frame with the accepted offthread reference."""
import json,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
require_guard(gpu=True)
import numpy as np,cv2
cv2.setNumThreads(2)
def structural_similarity(a,b,**_):
    a=a.astype(np.float32);b=b.astype(np.float32)
    blur=lambda x:cv2.GaussianBlur(x,(7,7),1.5)
    ma,mb=blur(a),blur(b)
    va,vb=blur(a*a)-ma*ma,blur(b*b)-mb*mb
    cov=blur(a*b)-ma*mb
    return np.mean(((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225)))
qa=PROJECT/'qa/frame-capture-test'
def frames(path):
    cmd=ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-hwaccel_output_format','cuda','-i',str(path),
      '-frames:v','50','-an','-vf','scale_cuda=432:768,hwdownload,format=nv12,format=rgb24','-f','rawvideo','-pix_fmt','rgb24','-'])
    return np.frombuffer(subprocess.run(cmd,capture_output=True,check=True).stdout,dtype=np.uint8).reshape(-1,768,432,3)
baseline=frames(PROJECT/'drafts/04-family-music-free-DRAFT.mp4')
candidate=frames(qa/'native-png-4k-2seconds.mp4')
records=[]
for i,(a,b) in enumerate(zip(baseline,candidate)):
    face=b[135:360,130:315].astype(np.float32)
    distances=[]
    for j in range(max(0,i-2),min(len(baseline),i+3)):
        ref=baseline[j,135:360,130:315].astype(np.float32)
        distances.append((float(np.mean(np.abs(face-ref))),j-i))
    best=min(distances)
    records.append(dict(frame=i,best_shift=best[1],face_mae=best[0],
        ssim=float(structural_similarity(a,b,channel_axis=2,data_range=255))))
receipt=dict(frames=len(records),minimum_ssim=min(r['ssim'] for r in records),
             nonzero_best_shifts=[r for r in records if r['best_shift']],frames_compared=records)
(qa/'native-comparison.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k!='frames_compared'}),flush=True)
assert len(records)==50 and receipt['minimum_ssim']>.99 and not receipt['nonzero_best_shifts']
