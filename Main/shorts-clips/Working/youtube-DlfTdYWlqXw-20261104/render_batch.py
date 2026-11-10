"""Monitored sequential renders; preserve every success and stop on any failure."""
import json,subprocess,sys,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,wait_headroom
require_guard(gpu=True)
state=dict(started=time.time(),renderer='established OffthreadVideo; PNG frames at 4K; NVENC',completed=[],current=None)
status=PROJECT/'batch-status.json'
def save():status.write_text(json.dumps(state,indent=2),encoding='utf-8')
for slug in ['01-happiness-freedom','02-your-success','03-self-reflection','05-three-relationships','06-fisherman','07-silver-thread']:
    state['current']=slug;state['stage']='waiting for render admission';save()
    wait_headroom(gpu=True)
    state['stage']='rendering';save();print('RENDER_BEGIN',slug,flush=True)
    subprocess.run([sys.executable,str(PROJECT/'render_prepared.py'),slug],cwd=ROOT,check=True)
    state['stage']='waiting for QA admission';save();print('RENDER_DONE',slug,flush=True)
    wait_headroom(gpu=True)
    state['stage']='technical QA';save()
    subprocess.run([sys.executable,str(PROJECT/'qa_clip.py'),slug],cwd=ROOT,check=True)
    state['completed'].append(slug);state['stage']='technical QA passed; visual sheet review pending';save()
    print('QA_DONE',slug,flush=True)
state['current']=None;state['stage']='all renders and technical checks completed';state['finished']=time.time();save()
print('BATCH_TECHNICAL_COMPLETE',flush=True)
