"""LAYER: Engineer. THE BIG PICTURE: inspect source passages before approving edits.
THE FLOW: original excerpts -> CUDA speech/frames -> bounded evidence for editorial review.
"""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard,probe
from prep import _load_whisper,scene_cuts
import numpy as np
require_guard(gpu=True)
model,device=_load_whisper('small')
records=[]
for window in json.loads((P/'windows.json').read_text()):
    slug=window['slug'];source=P/'source'/f'{slug}.mp4';qa=P/'review'/slug;qa.mkdir(parents=True,exist_ok=True)
    media=probe(source)
    raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(source),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
    segments,info=model.transcribe(np.frombuffer(raw,np.float32),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
    rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),'words':[{'w':w.word.strip(),'s':w.start,'e':w.end,'p':w.probability} for w in (s.words or [])]} for s in segments]
    (qa/'transcript.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (qa/'transcript.txt').write_text('\n'.join(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}" for s in rows),encoding='utf-8')
    cuts=scene_cuts(media)
    (qa/'cuts.json').write_text(json.dumps(cuts),encoding='utf-8')
    # A visual sample every two seconds across each whole source passage.
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(source),
        '-vf','fps=1/2,scale=640:-1,tile=4x3','-q:v','2',str(qa/'sheet-%02d.jpg')]),check=True)
    records.append({**window,'path':str(source),'width':media.width,'height':media.height,'fps':media.fps,'rate':media.rate,
        'duration':media.duration,'cuts':cuts,'transcription_device':device,'coverage':'Full excerpt CUDA ASR and two-second image samples; assistant review pending'})
    print(slug,' '.join(s['text'] for s in rows),flush=True)
(P/'source-inspection.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
