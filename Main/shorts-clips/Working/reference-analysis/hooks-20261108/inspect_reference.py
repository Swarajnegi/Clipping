"""Bounded full-reference frame study and CUDA speech transcription."""
import json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;ROOT=P.parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
require_guard(gpu=True)
source=next((ROOT/'Main/shorts-clips/Reference/hooks-20261108').glob('*.mp4'))
frames=P/'frames';frames.mkdir(exist_ok=True)
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-readrate','2','-hwaccel','cuda',
 '-i',str(source),'-an','-vf','fps=2','-q:v','3',str(frames/'%03d.jpg')]),check=True)
files=sorted(frames.glob('*.jpg'))
for page in range((len(files)+17)//18):
 canvas=Image.new('RGB',(6*184,3*348),(17,20,22));draw=ImageDraw.Draw(canvas)
 for slot,f in enumerate(files[page*18:(page+1)*18]):
  i=page*18+slot;x=(slot%6)*184;y=(slot//6)*348
  canvas.paste(Image.open(f).resize((180,320)),(x,y+23))
  draw.text((x+4,y+4),f'{i/2:.2f}s',(255,255,255))
 canvas.save(P/f'sheet-{page+1}.jpg',quality=94)
print('FRAMES',len(files),flush=True)
from prep import _load_whisper
model,device=_load_whisper('small')
raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(source),'-vn','-ac','1',
 '-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
segments,info=model.transcribe(np.frombuffer(raw,np.float32),word_timestamps=True,vad_filter=True,beam_size=5)
rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),
 'words':[{'w':w.word,'s':w.start,'e':w.end} for w in s.words or []]} for s in segments]
(P/'transcript.json').write_text(json.dumps({'device':device,'language':info.language,
 'segments':rows,'coverage':'Full 27.11s source passed to CUDA ASR with VAD; frame samples at 0.5s across full duration. Not continuous playback/listening.'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True),flush=True)
