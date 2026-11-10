"""Render two guarded layout tests using the existing clean source snippet."""
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,require_guard
require_guard(gpu=True)
here=Path(__file__).resolve().parent
wid='matthew_20261103_04'
props=json.loads((ROOT/'work'/wid/'props/clip_01.json').read_text(encoding='utf-8'))
props['shots']=[dict(t=s['t'],x=.65,w=.40) for s in props['shots']]
for l in props['referenceEdit']['layers']:
    l.update(x=45,width=450,align='left',size=74,y=800 if l['y'] in (1050,1370) else 1050)
target=here/'test-left-props.json';target.write_text(json.dumps(props),encoding='utf-8')
assets=here/'preview-public';(assets/'clips'/wid).mkdir(parents=True,exist_ok=True);(assets/'fonts').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'public/clips'/wid/'clip_01.mp4',assets/'clips'/wid/'clip_01.mp4')
shutil.copy2(ROOT/'public/fonts/InterVariable.woff2',assets/'fonts/InterVariable.woff2')
for frame in (55,695):
    dest=here/f'left-space-frame-{frame}.png'
    cmd=[str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(dest),f'--props={target}',f'--frame={frame}',
      '--concurrency=1','--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728',
      '--hardware-acceleration=required','--gl=angle',f'--public-dir={assets}']
    subprocess.run(cmd,cwd=ROOT,check=True)
