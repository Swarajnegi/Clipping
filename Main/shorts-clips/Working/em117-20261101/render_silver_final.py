"""Render the corrected opening seam and finish measured dialogue before QA."""
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
from finish_audio import finish
require_guard(gpu=True)
vid='em117_20261101_silver'
subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(ROOT/'work'/vid/'clips.json')],cwd=ROOT,check=True)
finish(vid)
subprocess.run([sys.executable,str(HERE/'level_dialogue.py'),'--only','silver'],cwd=ROOT,check=True)
