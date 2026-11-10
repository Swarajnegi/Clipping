"""Record the owner's explicit rejection without moving/deleting earlier videos."""
import json
import sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
import results
existing=results.load(results.SELECTION_LOG)
reason='Owner rejected all five for incomplete points; approved visual format/quality. New brief prefers complete 20-30s passages, up to 40s, centred captions and sound-reviewed rough cuts before finishing.'
manifest=json.loads((ROOT/'Main/shorts-clips/Exports/03 Archive/2026-11-08 - First Thought Palace Batch - Unselected/DELIVERY_MANIFEST.json').read_text())
for item in manifest:
    clip=item['file']
    if any(r.get('clip')==clip and r.get('reason')==reason for r in existing):continue
    results.append(results.SELECTION_LOG,dict(project='thought-palace-20261108',clip=clip,decision='rejected',
        reason=reason,production_minutes=None,logged=datetime.now(timezone.utc).isoformat(timespec='seconds')))
(P/'previous-batch-rejection.json').write_text(json.dumps({'owner_decision':'rejected','reason':reason,
    'files_preserved':[r['file'] for r in manifest]},indent=2),encoding='utf-8')
print('Five owner rejections recorded; previous files preserved; no audience metrics invented.')
