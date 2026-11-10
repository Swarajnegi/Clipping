"""Compare maximum-quality JPEG frame capture with the completed PNG route."""
import json,subprocess,sys,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,FFMPEG,run,require_guard
require_guard(gpu=True)
slug='belmar_20261104_4k_04-family';props=ROOT/'work'/slug/'props/clip_01.json'
public=PROJECT/'preview-public';qa=PROJECT/'qa/frame-capture-test';qa.mkdir(parents=True,exist_ok=True)
output=qa/'jpeg100-4k-2seconds.mp4';started=time.monotonic()
subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(output),
    f'--props={props}',f'--public-dir={public}','--frames=0-49','--concurrency=1',
    '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728',
    '--hardware-acceleration=required','--gl=angle','--scale=2','--video-bitrate=40M',
    '--image-format=jpeg','--jpeg-quality=100','--log=error'],cwd=ROOT,check=True)
elapsed=time.monotonic()-started
for file,name in [(output,'jpeg100'),(PROJECT/'drafts/04-family-music-free-DRAFT.mp4','png')]:
    run([FFMPEG,'-v','error','-y','-ss','1.6','-i',str(file),'-frames:v','1',str(qa/(name+'.png'))])
(qa/'timing.json').write_text(json.dumps(dict(frames=50,elapsed_seconds=elapsed,capture='JPEG100',output='2160x3840, 25fps, 40Mbps'),indent=2))
print('CAPTURE BENCHMARK',elapsed,'seconds for 50 frames',flush=True)
