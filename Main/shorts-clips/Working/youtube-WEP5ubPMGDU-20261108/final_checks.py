"""LAYER: Reviewer. THE BIG PICTURE: bind final delivery checks to the reviewed files.
THE FLOW: matching hashes/props and reviewed flags -> full decode/audio signatures -> receipt.
"""
import json,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
from motion_edit import digest,decode,audio_packets,validate_picture_clock
from build import picture_signature
require_guard(gpu=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
decisions=read(P/'edit-decisions.json');review=read(P/'qa/assistant-review.json');auto=read(P/'qa/automated.json')
assert review['issues']==[] and review['all_phrase_sheets_inspected']
geometry=read(P/'qa/caption-geometry.json');assert not geometry['failures'] and not geometry['collisions']
outputs=[]
for d in decisions:
    slug=d['slug'];receipt=read(P/'qa'/slug/'render.json');video=Path(receipt['file'])
    assert receipt['sha256']==digest(video)==review['render_sha256'][slug]
    props_path=ROOT/'work'/d['work_id']/'props/clip_01.json';assert digest(props_path)==receipt['props_sha256']
    props=read(props_path)
    assert all(l['surface']=='difference' and l['blend']=='difference' and l['color']=='#ffffff' and not l.get('gradient') for l in props['referenceEdit']['layers'])
    assert audio_packets(video)==audio_packets(Path(receipt['source_master']))
    validate_picture_clock(picture_signature(video),d['frames'],25)
    decode(video,d['frames'])
    report=next(r for r in auto if r['clip']==slug)
    for flag in report['caption_face_overlaps']:
        decision=review['detector_flag_review'][slug][str(flag['frame'])]
        assert decision['visible_face_overlap'] is False and Path(decision['evidence']).is_file()
    outputs.append({'clip':slug,'sha256':receipt['sha256'],'frames':d['frames'],'status':'passed with recorded review coverage'})
result={'passed':True,'guard_job':os.environ['CLIPPING_GUARD_JOB'],'outputs':outputs,
    'frames':sum(d['frames'] for d in decisions),'caption_words':sum(d['caption_words'] for d in decisions),
    'difference_layers':sum(d['caption_layers'] for d in decisions),'review':str(P/'qa/assistant-review.json')}
(P/'qa/final-checks.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2),flush=True)
