"""Bounded existing free-tier second opinions; no retries, alternate providers or video uploads."""
import json,subprocess,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard()
bank=json.loads((P/'candidate-bank.json').read_text(encoding='utf-8'))
targets=[('02-dads-unexpected-answer',1640,1755),('03-winning-someone-elses-game',3948,4002),('05-married-to-different-people',863,939)]
records=[]
for id,start,end in targets:
 b=next(b for b in bank if b['id']==id)
 question=(f'Watch and HEAR only the specified original source window. Assess this source moment critically for a reflective human-story Short. '
  f'Proposed opening: {b["opening"]}. Proposed edits: {b["cut_proposal"]}. '
  'Evaluate opening, progression, actual spoken fluency, payoff, and channel fit. Call out necessary context, restarted speech, dead or meaningful pauses, misleading reorder risks and exact clean ending concerns. '
  'The candidate is not an edited proof yet. Distinguish source fluency from untested joins. Do not infer retention or guarantee virality. '
  'Use original source timestamps if observed; label estimates and unknowns. Return objections and pass/pending/reject judgments in under 350 words.')
 cmd=[sys.executable,str(ROOT/'scripts/watch_review.py'),'--engine','gemini',b['source_url'],'--start',str(start),'--end',str(end),'--question',question]
 env=os.environ.copy();env['WATCH_GEMINI_TIMEOUT']='120'
 result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=155)
 report=P/'source-review'/(id+'-provider.md');report.write_text(result.stdout,encoding='utf-8')
 (P/'source-review'/(id+'-provider.stderr.log')).write_text(result.stderr,encoding='utf-8')
 receipt={'candidate':id,'returncode':result.returncode,'source_url':b['source_url'],'focus_start':start,'focus_end':end,'report':str(report),'method':'existing confirmed-free-tier Gemini audiovisual analysis of public URL; attributed second opinion, not direct assistant listening','model':'configured model from existing watch helper; no override','retries':0,'local_file_uploaded':False}
 records.append(receipt);(P/'source-review/provider-receipts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('PROVIDER_REVIEW',id,result.returncode,flush=True)
 if result.returncode:break
raise SystemExit(records[-1]['returncode'] if records else 0)
