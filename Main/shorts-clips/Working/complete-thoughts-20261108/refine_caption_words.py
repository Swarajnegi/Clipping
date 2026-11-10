"""Focused correction evidence for the fast Goggins sentence; no cut changes."""
import json,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
from prep import _load_whisper
require_guard(gpu=True)
model,device=_load_whisper('small')
source=P/'drafts/02-goggins-learning-to-fail-clean-assembly.mp4'
a,b=9.6,20.6
raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-ss',str(a),'-i',str(source),'-t',str(b-a),
 '-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
segments,info=model.transcribe(np.frombuffer(raw,np.float32),language='en',word_timestamps=True,
 vad_filter=False,beam_size=5,initial_prompt="Personal account: learning to fail before victory.")
rows=[{'text':s.text,'words':[{'w':w.word.strip(),'s':w.start+a,'e':w.end+a,'p':w.probability} for w in s.words or []]} for s in segments]
(P/'finish-v1/goggins-focused-alignment.json').write_text(json.dumps({'device':device,'window':[a,b],'segments':rows},indent=2),encoding='utf-8')
print(json.dumps(rows),flush=True)
