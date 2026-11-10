"""Render exactly the three chosen music-free edits, one at a time."""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
from qa_exports import inspect
from finish_audio import finish

def main():
    require_guard(gpu=True)
    choices=json.loads((HERE/'edit-decisions.json').read_text())
    if len(choices)>3:raise RuntimeError('Owner cap: at most three clips per source video')
    for choice in choices:
        vid=choice['work_id']
        qa_path=HERE/'qa'/vid/'qa.json'
        final=ROOT/'out'/vid/'clip_01.mp4'
        if qa_path.exists() and final.exists():
            receipt=json.loads(qa_path.read_text())
            spec_hash=hashlib.sha256((ROOT/'work'/vid/'clips.json').read_bytes()).hexdigest()
            with final.open('rb') as stream:output_hash=hashlib.file_digest(stream,'sha256').hexdigest()
            if receipt.get('spec_sha256')!=spec_hash or receipt.get('output_sha256')!=output_hash:
                raise RuntimeError('Completed clip changed; inspect it before resuming')
            print('REUSE_VALIDATED',vid,flush=True)
            continue
        subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(ROOT/'work'/vid/'clips.json')],cwd=ROOT,check=True)
        finish(vid)
        inspect(vid)
    return 0

if __name__=='__main__':raise SystemExit(main())
