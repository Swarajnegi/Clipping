"""Owner-requested continuation; one attempt per source, stop on provider failure."""
import json,subprocess,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard()
bank=json.loads((BASE/'candidate-bank.json').read_text(encoding='utf-8'))
targets=[('02-dads-unexpected-answer',1640,1755),('05-married-to-different-people',863,939),('03-winning-someone-elses-game',3948,4002),('04-choose-your-regret',2104,2164),('06-not-a-bucket-list',2700,2740),('07-i-think-im-lonely',4684,4731),('08-childhood-on-the-road',512,580)]
records=[]
for id,start,end in targets:
 b=next(b for b in bank if b['id']==id);report=P/(id+'-provider.md')
 if report.exists():raise FileExistsError('Preserve earlier review '+str(report))
 question=(f'Critically review the ACTUAL audio and moving footage in the specified original source window for a compelling reflective podcast Short. '
  f'Opening proposed: {b["opening"]}. Cut proposal: {b["cut_proposal"]}. '
  'Judge opening, progression, spoken fluency, payoff and channel fit. Identify dull setup, repetitions, false starts, meaningful pauses, misleading reorders, and where interest stops. '
  'The proposal is not an edited proof: source fluency does not verify new joins. Be selective; reject generic advice or a story that does not earn its length. '
  'Cite observed original times, label estimates/unknowns, and avoid invented metrics or claims of virality. Under 350 words.')
 env=os.environ.copy();env['WATCH_GEMINI_TIMEOUT']='120'
 r=subprocess.run([sys.executable,str(ROOT/'scripts/watch_review.py'),'--engine','gemini',b['source_url'],'--start',str(start),'--end',str(end),'--question',question],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=155)
 report.write_text(r.stdout,encoding='utf-8');(P/(id+'-provider.stderr.log')).write_text(r.stderr,encoding='utf-8')
 records.append({'candidate':id,'source_url':b['source_url'],'start':start,'end':end,'returncode':r.returncode,'report':str(report),'method':'configured confirmed-free-tier Gemini public-URL audiovisual second opinion; no direct assistant listening','retries':0})
 (P/'provider-receipts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
 print('REVIEW',id,r.returncode,flush=True)
 if r.returncode:break
raise SystemExit(records[-1]['returncode'] if records else 0)
