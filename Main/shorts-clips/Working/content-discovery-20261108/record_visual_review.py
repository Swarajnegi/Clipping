"""Record only source-frame inspection actually performed by the assistant."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
bank=read(P/'candidate-bank.json');receipts=read(P/'source-review/receipts.json')
notes={
 'matthew-offer':'All 11 populated five-second samples inspected. Matthew is visible in medium/close shots with hand gestures and two wide two-shots; no intrusive overlaid channel mark visible in sampled frames. Facial expressions change during the offer story. Crop planning must follow actual shot changes; not a full moving-edge/branding review.',
 'matthew-father':'All 23 populated five-second samples inspected. Multiple medium/close and side-angle shots; strong gestural change near the father’s reply. Preserve the reveal/reaction. Avoid one fixed crop that cuts raised hands; no whole-passage listening claim.',
 'hormozi-father':'All 11 populated five-second samples inspected. Wide shot then medium/close speaker shots. Modern Wisdom overlay changes to M|W at bottom-left and must be excluded in production. Keep face and microphone framing across cuts; source headwear is part of the original picture, not an added owner symbol.',
 'hudson-marriage':'All 15 populated five-second samples inspected. Medium front shot changes to side close-up. Modern Wisdom/M|W overlay at bottom-left needs clean exclusion. Bright shirt and moving hands require the existing Difference-caption placement/readability checks; do not place text across the face.'}
mapping={'01-cost-of-saying-no':'matthew-offer','02-dads-unexpected-answer':'matthew-father','03-winning-someone-elses-game':'hormozi-father','05-married-to-different-people':'hudson-marriage'}
for r in receipts:
 r['assistant_visual_review']=notes[r['slug']];r['file_sha256']=hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()
 r['direct_continuous_listening']=False;r['production_master']=False
for b in bank:
 if b['id'] in mapping:
  r=next(r for r in receipts if r['slug']==mapping[b['id']])
  b['visual_review']={'method':'assistant inspection of five-second source contact sheet','evidence':r['sheet'],'finding':r['assistant_visual_review'],'full_continuous_playback':False}
(P/'source-review/visual-review.json').write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(P/'candidate-bank.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded four inspected source sheets; direct listening remains unclaimed.')
