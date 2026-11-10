"""LAYER: Reviewer. THE BIG PICTURE: measure fonts before committing a production render.
THE FLOW: actual glyph bounds -> representative native-4K frames for assistant review.
"""
import subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,require_guard
require_guard(gpu=True)
subprocess.run([str(NODE),str(P/'check_geometry.cjs')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(P/'render_edits.py'),'proof'],cwd=ROOT,check=True)
