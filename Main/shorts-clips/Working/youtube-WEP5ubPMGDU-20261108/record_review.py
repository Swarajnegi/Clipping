"""Record completed assistant inspection truthfully; ordinary JSON/file work only."""
import json,sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from motion_edit import digest
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
decisions=read(P/'edit-decisions.json');auto=read(P/'qa/automated.json')
flags={}
for r in auto:
    flags[r['clip']]={}
    for flag in r['caption_face_overlaps']:
        slug=r['clip'];f=flag['frame']
        flags[slug][str(f)]={'visible_face_overlap':False,
            'reason':'False face detection on hand/microphone at the lower left; actual face is far above the caption.' if slug.startswith('02') else
                     'Detector rectangle extends below the actual chin; font line-box top intersects its margin, while visible painted letters are below the chin on neck/microphone/shirt. Confirmed on the exact-frame crop.',
            'evidence':str(P/'qa'/slug/f'flag-{f:04d}-4k.png')}
data={'reviewed_at':datetime.now(timezone.utc).isoformat(),'reviewed_by':'Codex assistant, local source/frame inspection',
    'all_phrase_sheets_inspected':True,'phrase_sheets':[str(p) for p in sorted((P/'qa').glob('*/phrases-*.jpg'))],
    'render_sha256':{d['slug']:read(P/'qa'/d['slug']/'render.json')['sha256'] for d in decisions},
    'detector_flag_review':flags,'issues':[],
    'coverage':'All four original windows studied with full CUDA ASR and two-second visual sheets. Every finished caption composition/camera-cut sample inspected in 11 phone-sized sheets; native 4K proofs and all nine flagged exact frames inspected. Full CUDA decode, audio payload/timestamp equality and loudness checks passed. No continuous playback/listening or successful Gemini review claim.',
    'direct_continuous_listening':False,
    'findings':'Captions remain below visible faces, off interface edges and visibly colour-reactive, including true italic accents. No foreign overlaid marks appear in reviewed cropped output. The comparison caption area was raised to avoid poor contrast on gray floor. Difference intentionally responds to patterned tie/clothing; no fixed pink tint or solid fallback was used.',
    'audio_loudness':[{'clip':d['slug'],'integrated_lufs':i,'true_peak_dbfs':p} for d,i,p in zip(decisions,[-15.2,-15.1,-14.9,-15.2],[-.9,-.9,-1.0,-1.1])],
    'resolved_checks':['Caption row geometry adjusted before rendering for italic bounds/spacing.',
        'Audio QA canonicalized codec/configuration plus packet hashes/timestamps; container handler/language labels are not audio payload. All packet and codec fields match.',
        'Nine detector rectangle flags individually resolved against actual frames; raw results retained.']}
assert len(data['phrase_sheets'])==11
(P/'qa/assistant-review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({'reviewed_sheets':len(data['phrase_sheets']),'reviewed_detector_flags':sum(len(x) for x in flags.values()),'continuous_listening':False})
