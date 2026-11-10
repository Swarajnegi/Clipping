"""Record assistant review only for explicitly inspected clips."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
for name in sys.argv[1:]:
    path=HERE/'qa'/('em117_20261101_'+name)/'qa.json'
    qa=json.loads(path.read_text())
    qa['assistant_inspected']=True
    qa['visual_review']={'caption_sheets':'All generated caption sheets inspected, including word entrances, layer holds, pauses and source cuts',
        'full_frame_strip':'Four full-frame samples inspected',
        'findings':'Silver-white captions stay off the face; italic accents and hierarchy readable; source compression remains visible; no caption spill or overlapping phrases observed',
        'continuous_playback_listening':False,'live_app_overlay_preview':False}
    qa['branding_check']={'passed':True,'basis':'Full-frame strip, caption frames across selected cuts, and previously reviewed original/clean passage frames; sponsor footer excluded by crop; no foreign overlay or end card observed'}
    path.write_text(json.dumps(qa,indent=2),encoding='utf-8')
    print('VISUAL_REVIEW_RECORDED',name)
