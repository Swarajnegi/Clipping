"""Guarded CUDA transcripts and visual evidence for source excerpts."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,probe,FFMPEG,run
from prep import _load_whisper,scene_cuts
require_guard(gpu=True)
home=Path(__file__).resolve().parent
model,device=_load_whisper('small')
for n,name in enumerate(('01-opening','02-successes','03-endurance','04-relevance'),1):
 source=home/'source'/f'{name}.mp4';media=probe(source)
 wid=f'matthew_20261103_{n:02d}';work=ROOT/'work'/wid;work.mkdir(parents=True,exist_ok=True)
 meta={'id':wid,'path':str(source),'title':name,'fps':media.fps,'rate':media.rate,'width':media.width,'height':media.height,
       'duration':media.duration,'has_audio':media.has_audio,'original_url':'https://www.youtube.com/watch?v=Eu1kHIztT24',
       'reuse_basis':'Owner confirmed permission or campaign authorization for this episode in chat, 3 November 2026'}
 (work/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 segments,_=model.transcribe(str(source),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
 result=[]
 for seg in segments:
  result.append({'start':round(seg.start,3),'end':round(seg.end,3),'text':seg.text.strip(),
   'words':[{'w':w.word,'s':round(w.start,3),'e':round(w.end,3),'p':round(w.probability,3)} for w in (seg.words or [])]})
 (work/'transcript.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
 (work/'transcript.txt').write_text('\n'.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in result),encoding='utf-8')
 (work/'signals.json').write_text(json.dumps({'cuts':scene_cuts(media),'seconds':[]}),encoding='utf-8')
 evidence=home/'qa'/name;evidence.mkdir(parents=True,exist_ok=True)
 run([FFMPEG,'-v','error','-y','-i',str(source),'-vf','fps=1/4,scale=640:-1,tile=4x4',str(evidence/'source-%02d.jpg')])
 print(f'{name}: {media.duration:.2f}s, {len(result)} transcript segments, CUDA {device}',flush=True)
