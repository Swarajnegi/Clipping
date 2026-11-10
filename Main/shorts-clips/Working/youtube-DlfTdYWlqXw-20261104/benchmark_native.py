"""Isolated 50-frame experiment; never substitutes a path without comparison."""
import json,subprocess,sys,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,FFMPEG,run,require_guard
require_guard(gpu=True)
props=ROOT/'work/belmar_20261104_4k_04-family/props/clip_01.json'
qa=PROJECT/'qa/frame-capture-test';output=qa/'native-png-4k-2seconds.mp4'
started=time.monotonic()
subprocess.run([str(NODE),str(REMOTION),'render',str(PROJECT/'NativeProof.tsx'),'Native4K',str(output),
 f'--props={props}',f'--public-dir={PROJECT/"preview-public"}','--frames=0-49',
 '--concurrency=1','--hardware-acceleration=required','--gl=angle','--scale=2',
 '--video-bitrate=40M','--image-format=png','--log=verbose'],cwd=ROOT,check=True)
elapsed=time.monotonic()-started
run([FFMPEG,'-v','error','-y','-ss','1.6','-i',str(output),'-frames:v','1',str(qa/'native.png')])
(qa/'native-timing.json').write_text(json.dumps(dict(frames=50,elapsed_seconds=elapsed,capture='PNG',decoder='Html5Video',
 output='2160x3840, 25fps, 40Mbps'),indent=2))
print('NATIVE BENCHMARK',elapsed,'seconds for 50 frames',flush=True)
