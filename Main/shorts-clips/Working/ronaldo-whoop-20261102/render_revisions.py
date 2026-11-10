"""Replace only the two caption drafts rejected during actual frame review."""
import subprocess
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
for name in ('gym', 'talent'):
    subprocess.run([sys.executable, str(HERE/'render_one.py'), name], cwd=ROOT, check=True)
