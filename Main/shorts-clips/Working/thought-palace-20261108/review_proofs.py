"""One bounded audiovisual review of five full proofs; no service/model/paid fallback."""
import json
import os
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command, probe
require_guard(gpu=True)
proofs=json.loads((P/'proofs.json').read_text())
inputs=[]; filters=[]; labels=[];offset=0;chapters=[]
for i,r in enumerate(proofs):
    inputs += ['-i',r['proof']]
    filters += [f'[{i}:v]fps=25,setpts=PTS-STARTPTS[v{i}]',f'[{i}:a]asetpts=PTS-STARTPTS[a{i}]']
    labels += [f'[v{i}][a{i}]']
    duration=probe(Path(r['proof'])).duration
    chapters.append({'id':r['id'],'start':offset,'end':offset+duration});offset+=duration
bundle=P/'qa/proof-review-bundle.mp4'
filters.append(''.join(labels)+'concat=n=5:v=1:a=1[v][a]')
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y',*inputs,'-filter_complex',';'.join(filters),
    '-map','[v]','-map','[a]','-c:v','h264_nvenc','-preset','p4','-b:v','3M','-c:a','aac','-b:a','160k',str(bundle)]),check=True)
(P/'qa/proof-review-chapters.json').write_text(json.dumps(chapters,indent=2))
question=('Review ALL FIVE complete edits with sound, not only transcript or thumbnails. Sections: '+json.dumps(chapters)+'. '
    'Audience: thought.palace, reflective self-worth, agency, authenticity, commitment and decisions. '
    'Each clip should deliver a direct spoken hook within its first 3 seconds and a complete personally relevant payoff. '
    'These are cheap uncaptained content proofs, not finished picture treatment. '
    'For EACH: report first spoken line, hook pass/revise, conversational fluency and every awkward jump/clipped syllable, '
    'whether its ending completes the thought, and whether the very quiet camera click obscures any word. '
    'Clip 3 intentionally leads with his own journal quote then immediately restores journal/twenties context; it must stay a personal account, not blame all lonely people. '
    'Clip 5 reorders authentic lines from the same confidence conversation. Be critical of manufactured continuity. '
    'Explicitly say which full sections you could actually see AND hear. No invented retention or virality ratings. Under 650 words.')
env=os.environ.copy();env['WATCH_GEMINI_TIMEOUT']='150'
result=subprocess.run([sys.executable,str(ROOT/'scripts/watch_review.py'),'--engine','gemini',str(bundle),'--question',question],
    capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=190)
(P/'qa/proof-provider-review.md').write_text(result.stdout,encoding='utf-8')
(P/'qa/proof-provider-review.stderr.log').write_text(result.stderr,encoding='utf-8')
(P/'qa/proof-provider-receipt.json').write_text(json.dumps({'returncode':result.returncode,'retries':0,
    'coverage':'Five full combined proofs submitted; actual audiovisual coverage depends on provider report',
    'method':'Existing configured confirmed-free-tier Gemini audiovisual second opinion',
    'report':str(P/'qa/proof-provider-review.md')},indent=2))
print('Bounded audiovisual review exit',result.returncode,flush=True)
raise SystemExit(result.returncode)
