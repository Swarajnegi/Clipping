"""Actual-footage 4K proof before batch production, using the existing clean edit."""
import copy,json,os,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,require_guard
require_guard(gpu=True)
slug='04-family'
props_path=PROJECT/'authoring'/slug/'props.json'
props=json.loads(props_path.read_text())
public=PROJECT/'render-public'/slug
for relative in [props['src'],'fonts/InterVariable.woff2','fonts/InterVariable-Italic.woff2',
                 'fonts/CormorantGaramond-Italic.ttf','fonts/Cormorant-OFL.txt','fonts/Inter-LICENSE.txt']:
    target=public/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():os.link(ROOT/'public'/relative,target)
qa=PROJECT/'qa/style-preview';qa.mkdir(parents=True,exist_ok=True)
for at in [2.7,10.75,24.78,27.5,31.65]:
    subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(qa/f'{at:05.2f}.png'),
        f'--props={props_path}',f'--frame={round(at*25)}','--scale=2',f'--public-dir={public}',
        '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728','--gl=angle','--log=error'],cwd=ROOT,check=True)
subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(qa/'family-contrast-preview.mp4'),
    f'--props={props_path}',f'--public-dir={public}','--frames=215-274','--concurrency=1',
    '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728',
    '--hardware-acceleration=required','--gl=angle','--scale=2','--video-bitrate=40M','--image-format=png','--log=error'],cwd=ROOT,check=True)
print('Five real-footage 4K stills and 2.4s motion preview ready',flush=True)
