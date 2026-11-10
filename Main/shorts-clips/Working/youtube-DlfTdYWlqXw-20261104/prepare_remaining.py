"""Sequential bounded preparation of the six remaining authored clips."""
import json,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
for d in json.loads((PROJECT/'edit-decisions.json').read_text(encoding='utf-8')):
    if d['slug']=='04-family':continue
    print('PREPARE',d['slug'],flush=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(ROOT/'work'/d['work_id']/'clips.json'),'--no-render'],cwd=ROOT,check=True)
