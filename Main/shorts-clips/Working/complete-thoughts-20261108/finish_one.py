"""One guard-owned finishing stage; the renderer exits before lossless mux/QA."""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
id=sys.argv[1];start=int(sys.argv[2]);r=next(r for r in json.loads((P/'proofs.json').read_text()) if r['id']==id)
subprocess.run([sys.executable,str(P/'render_finals.py'),'chunk','--id',id,'--start',str(start),'--end',str(r['frames']-1)],check=True)
subprocess.run([sys.executable,str(P/'render_finals.py'),'mux','--id',id],check=True)
