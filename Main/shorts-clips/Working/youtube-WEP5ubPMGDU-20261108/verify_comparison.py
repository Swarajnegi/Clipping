"""LAYER: Reviewer. THE BIG PICTURE: verify the wide-shot readability correction.
THE FLOW: measured font/phone bounds -> revised medium and wide native 4K proofs.
"""
import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,NODE
require_guard(gpu=True)
subprocess.run([str(NODE),str(P/'check_geometry.cjs')],cwd=ROOT,check=True)
for frame in [72,330]:
    subprocess.run([sys.executable,str(P/'render_edits.py'),'proof','--only','02','--proof-frame',str(frame)],cwd=ROOT,check=True)
