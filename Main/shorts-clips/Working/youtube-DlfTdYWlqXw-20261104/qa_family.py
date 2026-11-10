"""Sequential typography checks and first finished-clip inspection."""
import subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,require_guard
require_guard(gpu=True)
subprocess.run([str(NODE),str(PROJECT/'check_caption_geometry.cjs')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(PROJECT/'qa_clip.py'),'04-family'],cwd=ROOT,check=True)
