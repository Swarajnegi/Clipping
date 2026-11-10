"""Guarded review proxies, CUDA word times and scene evidence; no editorial approval."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,probe,run,FFMPEG
from prep import _load_whisper,scene_cuts
require_guard(gpu=True)
home=Path(__file__).resolve().parent
model,device=_load_whisper('small')
production='--production' in sys.argv
for source in sorted((home/('production-source' if production else 'source')).glob('*.mp4')):
 work=ROOT/'work'/('belmar_20261104_'+('4k_' if production else '')+source.stem);work.mkdir(parents=True,exist_ok=True)
 media=probe(source)
 meta={'id':work.name,'path':str(source),'title':source.stem,'fps':media.fps,'rate':media.rate,
  'width':media.width,'height':media.height,'duration':media.duration,'has_audio':media.has_audio,
  'original_url':'https://www.youtube.com/watch?v=DlfTdYWlqXw',
  'reuse_basis':'Owner confirmed episode covered, 4 November 2026','purpose':'2160p original production excerpt' if production else '1080p inspection proxy; acquire shortlisted 2160p originals for production'}
 (work/'source.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
 if not (work/'transcript.json').exists():
  segments,_=model.transcribe(str(source),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
  rows=[{'start':round(s.start,3),'end':round(s.end,3),'text':s.text.strip(),
    'words':[{'w':w.word,'s':round(w.start,3),'e':round(w.end,3),'p':round(w.probability,3)} for w in (s.words or [])]} for s in segments]
  (work/'transcript.json').write_text(json.dumps(rows),encoding='utf-8')
  (work/'transcript.txt').write_text('\n'.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in rows),encoding='utf-8')
 (work/'signals.json').write_text(json.dumps({'cuts':scene_cuts(media),'seconds':[]}),encoding='utf-8')
 qa=home/'qa'/('production' if production else 'review')/source.stem;qa.mkdir(parents=True,exist_ok=True)
 run([FFMPEG,'-v','error','-y','-i',str(source),'-vf','fps=1/3,scale=480:-1,tile=4x4',str(qa/'source-%02d.jpg')])
 print(source.stem,media.duration,device,flush=True)
