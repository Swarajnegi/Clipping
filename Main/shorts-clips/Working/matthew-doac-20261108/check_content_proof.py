"""Independent decode/transcription checks for the review proof; not human listening."""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command
from prep import _load_whisper
import numpy as np
require_guard(gpu=True)
proof=P/'drafts/01-the-offer-content-proof.mp4';qa=P/'qa'
raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(proof),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
model,device=_load_whisper('small')
segments,_=model.transcribe(np.frombuffer(raw,np.float32),language='en',word_timestamps=True,vad_filter=True,beam_size=5)
rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),'words':[{'w':w.word.strip(),'s':w.start,'e':w.end} for w in s.words or []]} for s in segments]
text=' '.join(s['text'] for s in rows)
assert text.lower().startswith('eight'),text
assert text.lower().rstrip('.! ').endswith('no'),text
assert 'and i think' not in text.lower(),text
(qa/'content-proof-transcript.json').write_text(json.dumps({'device':device,'text':text,'segments':rows,'coverage':'CUDA ASR on complete proof; no direct continuous listening claim'},ensure_ascii=False,indent=2),encoding='utf-8')
for label,time in [('opening',0.12),('ending',30.28)]:
 subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-ss',str(time),'-i',str(proof),'-frames:v','1',str(qa/(label+'.png'))]),check=True)
with (qa/'loudness.log').open('w',encoding='utf-8') as log:
 subprocess.run(ffmpeg_command([FFMPEG,'-hide_banner','-i',str(proof),'-vn','-af','ebur128=peak=true','-f','null','-']),stdout=subprocess.DEVNULL,stderr=log,check=True)
print(text,flush=True)
