"""Author and preview a shot-aware caption-placement revision of clip one."""
import copy,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from build import validate_reference_edit
from common import NODE,REMOTION,require_guard
HOME=Path(__file__).resolve().parent
OLD='matthew_20261103_01'; NEW='matthew_20261104_01_placement_v2'
old=ROOT/'work'/OLD; new=ROOT/'work'/NEW

def author():
 new.mkdir(parents=True,exist_ok=True)
 for name in ('source.json','transcript.json','signals.json'):
  shutil.copy2(old/name,new/name)
 spec=json.loads((old/'clips.json').read_text(encoding='utf-8'));spec['id']=NEW
 for shot in spec['clips'][0]['shots']:
  if abs(shot['t']-12.32)<0.05: shot['x']=.72
 layers=spec['clips'][0]['referenceEdit']['layers']
 for i,layer in enumerate(layers):
  # Each two-line composition shares a placement. The interval 12.5–23.5s
  # follows the shot where Matthew sits left, leaving visible space on right.
  start=layers[i-i%2]['t']; right=12.5<=start<23.5; left=start>=37.0
  row=i%2
  if right:
   size=min(68,max(48,int(520/max(len(layer['text']),1))))
   layer.update(x=665,width=330,y=810+125*row,size=size,align='left')
  elif left:
   size=min(76,max(48,int(740/max(len(layer['text']),1))))
   layer.update(x=45,width=440,y=810+125*row,size=size,align='left')
  else:
   layer.update(x=100,width=880,y=1300+125*row,size=100,align='center')
 validate_reference_edit(spec['clips'][0]['referenceEdit'],46.52)
 (new/'clips.json').write_text(json.dumps(spec,indent=2,ensure_ascii=False),encoding='utf-8')
 props=json.loads((old/'props/clip_01.json').read_text(encoding='utf-8'))
 props['referenceEdit']=copy.deepcopy(spec['clips'][0]['referenceEdit'])
 props['shots']=copy.deepcopy(spec['clips'][0]['shots'])
 (HOME/'placement-v2-preview-props.json').write_text(json.dumps(props,ensure_ascii=False),encoding='utf-8')
 print('authored',new/'clips.json')

def preview():
 require_guard(gpu=True)
 props=HOME/'placement-v2-preview-props.json';assets=HOME/'preview-public'
 (assets/'clips'/OLD).mkdir(parents=True,exist_ok=True);(assets/'fonts').mkdir(parents=True,exist_ok=True)
 shutil.copy2(ROOT/'public/clips'/OLD/'clip_01.mp4',assets/'clips'/OLD/'clip_01.mp4')
 shutil.copy2(ROOT/'public/fonts/InterVariable.woff2',assets/'fonts/InterVariable.woff2')
 for frame in (375,475):
  dest=HOME/f'placement-v2-frame-{frame}.png'
  subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(dest),f'--props={props}',f'--frame={frame}',
   '--concurrency=1','--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728',
   '--hardware-acceleration=required','--gl=angle',f'--public-dir={assets}'],cwd=ROOT,check=True)

if __name__=='__main__':
 {'author':author,'preview':preview}[sys.argv[1]]()
