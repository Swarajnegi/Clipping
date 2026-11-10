"""Timing analysis of preserved original context, not a claim of human listening."""
import json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command
from prep import _load_whisper
import numpy as np
require_guard(gpu=True)
model,device=_load_whisper('small')
records=[]
for name,start in [('matthew-offer',6132),('matthew-father',1640)]:
 source=BASE/'source-review'/(name+'-h264.mp4');output=P/(name+'-words.json')
 if output.exists():raise FileExistsError('Preserve existing timing analysis')
 raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(source),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
 segments,info=model.transcribe(np.frombuffer(raw,np.float32),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
 rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),'words':[{'w':w.word.strip(),'s':w.start,'e':w.end,'p':w.probability} for w in s.words or []]} for s in segments]
 output.write_text(json.dumps({'source_url':'https://www.youtube.com/watch?v=QMzxNfX-uAg','file':str(source),'context_start':start,'device':device,'segments':rows},ensure_ascii=False,indent=2),encoding='utf-8')
 records.append({'name':name,'device':device,'words':sum(len(s['words']) for s in rows),'output':str(output)})
 print(name,' '.join(s['text'] for s in rows),flush=True)
(P/'alignment-receipt.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
