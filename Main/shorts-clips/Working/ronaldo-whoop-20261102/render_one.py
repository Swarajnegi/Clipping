"""A single reviewed source edit, bounded cache, measured dialogue and complete QA."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
parser=argparse.ArgumentParser()
parser.add_argument('name')
args=parser.parse_args()
choices=json.loads((HERE/'edit-decisions.json').read_text())
choice=next(c for c in choices if c['name']==args.name)
if not 0<choice['duration']<=100:raise RuntimeError('Invalid duration')
vid=choice['work_id']
metadata=json.loads((ROOT/'work'/vid/'source.json').read_text())
if Path(metadata['path']).name!='clean-final.mp4':raise RuntimeError('Final reviewed source required')
if (HERE/'qa'/vid/'qa.json').exists():raise RuntimeError('Existing output requires review before replacement')
subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(ROOT/'work'/vid/'clips.json'),
                '--video-cache-mib','128'],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(HERE/'level_dialogue.py'),'--only',args.name],cwd=ROOT,check=True)
