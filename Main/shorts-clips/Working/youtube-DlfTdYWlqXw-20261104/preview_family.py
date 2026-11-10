"""Inspect 4K font rasterization and actual shot layouts before a full render."""
import json,os,shutil,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,require_guard
require_guard(gpu=True)
slug='belmar_20261104_4k_04-family'
public=PROJECT/'preview-public'
dest=public/'clips'/slug;dest.mkdir(parents=True,exist_ok=True)
source=ROOT/'public/clips'/slug/'clip_01.mp4'
target=dest/source.name
if not target.exists():os.link(source,target)
(public/'fonts').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'public/fonts/InterVariable.woff2',public/'fonts/InterVariable.woff2')
props=ROOT/'work'/slug/'props/clip_01.json'
qa=PROJECT/'qa/style-preview';qa.mkdir(parents=True,exist_ok=True)
for at in [2.4,10.35,11.45,20.3,30.7]:
    subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(qa/f'{at:05.2f}.png'),
        f'--props={props}',f'--frame={round(at*25)}','--scale=2',f'--public-dir={public}',
        '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728','--gl=angle','--log=error'],cwd=ROOT,check=True)
print('Five 2160x3840 previews ready',flush=True)
