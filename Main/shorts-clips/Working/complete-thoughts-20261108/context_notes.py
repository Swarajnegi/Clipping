"""Write complete surrounding published-cue context for assistant inspection."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
out=[]
for candidate in json.loads((P/'candidates.json').read_text()):
    out += ['# '+candidate['id'],'']
    record=json.loads((P/'transcripts'/(candidate['video_id']+'.json')).read_text())
    assert record['status']=='available'
    a,b=candidate['context']
    rows=[s for s in record['segments'] if s['start']<b and s['end']>a]
    out += [f"{s['start']:.2f}–{s['end']:.2f} {s['text']}" for s in rows]+['']
(P/'CONTEXT_TRANSCRIPTS.txt').write_text('\n'.join(out),encoding='utf-8')
print('Saved all five complete context windows; published captions are not a listening review.')
