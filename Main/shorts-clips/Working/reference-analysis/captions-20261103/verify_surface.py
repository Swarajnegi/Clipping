"""Render and pixel-check the caption blend against known colour fields."""
from pathlib import Path
import json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,require_guard
HERE=Path(__file__).resolve().parent
require_guard(gpu=True)
assets=HERE/'render-public';(assets/'fonts').mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/'public/fonts/InterVariable.woff2',assets/'fonts/InterVariable.woff2')
output=HERE/'surface-proof.png'
subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','CaptionSurfaceTest',str(output),
 '--frame=15',f'--public-dir={assets}','--gl=angle','--offthreadvideo-video-threads=2',
 '--offthreadvideo-cache-size-in-bytes=134217728'],cwd=ROOT,check=True)
from PIL import Image
import numpy as np
image=Image.open(output).convert('RGB');data=np.array(image)
green=np.array([36,108,56]);leaf=np.array([68,126,53]);pale=np.array([238,238,238])
def count(area,rgb): return int(np.all(abs(area.astype('int16')-rgb)<=3,axis=2).sum())
region=data[820:1030]
checks={'green_to_pink_pixels':count(region,255-green),
 'leaf_to_complement_pixels':count(region,255-leaf),
 'pale_to_dark_pixels':count(region,255-pale)}
assert all(value>100 for value in checks.values()),checks
checks['difference_blend_verified']=True
checks['font']='Bundled Inter; reference-only fonts not activated'
checks['ronaldo_render']='remains on owner hold'
(HERE/'surface-verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
image.resize((360,640),Image.Resampling.LANCZOS).save(HERE/'surface-proof-phone.png')
print(json.dumps(checks,indent=2))
