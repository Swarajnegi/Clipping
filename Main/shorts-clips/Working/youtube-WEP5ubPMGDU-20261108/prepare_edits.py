"""LAYER: Engineer. THE BIG PICTURE: stage the approved spans through the existing builder.
THE FLOW: authored JSON -> bounded NVENC assembly -> unchanged caption/shot props.
"""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
for d in json.loads((P/'edit-decisions.json').read_text(encoding='utf-8')):
    path=ROOT/'work'/d['work_id']/'clips.json'
    if (ROOT/'work'/d['work_id']/'props/clip_01.json').exists():raise FileExistsError('Preserve completed preparation '+d['slug'])
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(path),'--no-render'],cwd=ROOT,check=True)
from common import NODE
subprocess.run([str(NODE),str(P/'check_geometry.cjs')],cwd=ROOT,check=True)
print('ALL_FOUR_EDITS_PREPARED',flush=True)
