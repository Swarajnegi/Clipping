"""Optional configured-free full-file review; stop on the first provider failure."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import study_references as reviewer

reviewer.QUESTION='''Watch and listen to this entire original podcast passage. Use local file seconds.
Identify speakers and camera cuts. Is any music audible under the dialogue? Distinguish music,
room tone and ordinary microphone sounds; state uncertainty. Suggest one self-contained 25-55s
short with an immediate original-speaker opening and complete payoff. Give first and last spoken
words and local start/end times. Flag transcription pitfalls, incomplete clauses, speech overlaps,
source music, distracting sounds and any coverage limitation. Do not infer rights or performance.
Do not rewrite speech. Focus on actual audiovisual evidence; timestamps must be local file time.'''
for name in ('parenthood','confidence','pursuit'):
    folder=HERE/'provider-review'/name
    folder.mkdir(parents=True,exist_ok=True)
    try:
        receipt=reviewer.cloud_review(HERE/'source'/(name+'.mp4'),folder)
        print(name,json.dumps(receipt),flush=True)
    except (Exception,SystemExit) as exc:
        (HERE/'provider-review/failure.json').write_text(json.dumps({'source':name,'error':str(exc),'automatic_retry':False},indent=2),encoding='utf-8')
        print('Provider unavailable; no retry:',str(exc),flush=True)
        raise SystemExit(2)
