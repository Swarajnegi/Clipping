"""Sequential production after reviewing the first complete clip."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
first=HERE/'qa/ronaldo_whoop_20261102_map/qa.json'
if not first.exists() or not json.loads(first.read_text()).get('assistant_inspected'):
    raise RuntimeError('Review first completed clip before the batch')
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
for choice in json.loads((HERE/'edit-decisions.json').read_text()):
    vid=choice['work_id']
    qa_path=HERE/'qa'/vid/'qa.json'
    final=ROOT/'out'/vid/'clip_01.mp4'
    spec=ROOT/'work'/vid/'clips.json'
    if qa_path.exists() and final.exists():
        qa=json.loads(qa_path.read_text())
        if qa['spec_sha256']!=digest(spec) or qa['output_sha256']!=digest(final):
            raise RuntimeError('Existing validated artifact changed')
        print('REUSE_TECHNICALLY_VALIDATED',vid,flush=True)
        continue
    subprocess.run([sys.executable,str(HERE/'render_one.py'),choice['name']],cwd=ROOT,check=True)
