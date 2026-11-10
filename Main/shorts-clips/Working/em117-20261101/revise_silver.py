"""Keep the prior draft and regenerate the one corrected opening seam."""
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
vid='em117_20261101_silver'
archive=HERE/'edit-revisions/silver-before-opening-seam'
for source,label in [(ROOT/'work'/vid,'work'),(ROOT/'out'/vid,'out'),(HERE/'qa'/vid,'qa')]:
    dest=archive/label
    if not source.resolve().is_relative_to(ROOT) or not dest.resolve().is_relative_to(ROOT):
        raise RuntimeError('Archive outside workspace')
    if dest.exists():raise RuntimeError('Archive exists')
    dest.parent.mkdir(parents=True,exist_ok=True)
    source.rename(dest)
subprocess.run([sys.executable,str(HERE/'stage_edits.py'),'--only','silver'],check=True,cwd=ROOT)
choices=json.loads((HERE/'edit-decisions.json').read_text())
record=next(c for c in choices if c['name']=='silver')
with (HERE/'EDIT_PLAN.md').open('a',encoding='utf-8') as stream:
    stream.write('\n## Final silver opening seam\n\nSecond piece now starts at local 35.32s, after the repeated me and before I am tired. '
                 'All subsequent caption times are regenerated from original word timestamps. '
                 'Updated speech duration: '+str(record['duration'])+' seconds. Updated approximate source ranges: '+str(record['original_segments_approx'])+'.\n')
print('SILVER_SEAM_REVISED',record['duration'],record['caption_text'])
