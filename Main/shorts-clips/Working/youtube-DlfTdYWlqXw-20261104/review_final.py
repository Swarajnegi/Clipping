"""One remote-only review of a newly finished artifact on the configured free route.

No local frames/models, provider changes, paid fallback, or API retries.
"""
import argparse,json,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'.runtime/claude-video/skills/watch/scripts'))
import config,gemini
config.CONFIG_DIR=ROOT/'.runtime/watch';config.CONFIG_FILE=config.CONFIG_DIR/'.env'
parser=argparse.ArgumentParser();parser.add_argument('slug');args=parser.parse_args()
cfg=config.get_config();key=config.load_gemini_key()
if not key or config.read_env_file().get('WATCH_FREE_TIER_CONFIRMED')!='1':raise SystemExit('Free route unavailable')
video=PROJECT/'drafts'/(args.slug+'-music-free-DRAFT.mp4')
receipt=PROJECT/'qa'/args.slug/'audiovisual-review.json'
if receipt.exists():raise SystemExit('One request per finished artifact; inspect existing receipt')
question='''Review this finished short video across its FULL duration, both picture and audio.
Check the exact audible spoken wording against the burned-in captions, sentence openings/endings,
caption timing and readability, accidental word omission, face overlap, camera-cut problems,
audible glitches and any added/background music. Report specific timestamped problems only when
observed. Distinguish a printed microphone equipment mark from a separately overlaid channel watermark.
Quote any incorrect caption next to the word actually heard. Do not assume the captions are right.
Do not mistake a word appearing progressively for a missing word unless it never appears.
Give PASS or REVISE with concrete reasons; explicitly state any audio or timing checks you cannot perform.
The intended result is a complete, music-free conversation excerpt with subtle word-synchronous
silver-white typography and no separately overlaid channel branding.'''
record=dict(file=str(video),model=cfg['gemini_model'],free_tier_confirmed=True,
            purpose='First review of this newly rendered artifact; no API retry',question=question,
            succeeded=False,uploaded=False,deletion_error=None)
upload=None
try:
    upload=gemini.upload_file(video,key);record['uploaded']=True;record['upload_name']=upload['name']
    answer=gemini.ask({'uri':upload['uri'],'mime_type':upload['mime_type']},question,model=cfg['gemini_model'],key=key)
    record.update(succeeded=True,answer=answer)
except (SystemExit,Exception) as exc:
    record['error']=str(exc).replace(key,'[redacted]')
finally:
    if upload:record['deletion_error']=gemini.delete_file(upload['name'],key)
    receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=True),flush=True)
