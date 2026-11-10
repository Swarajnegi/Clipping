"""One guarded CUDA transcription process for the three bounded source passages."""
import json
import sys
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
from prep import _load_whisper

def main():
    require_guard(gpu=True)
    model,device=_load_whisper('small')
    for name in ('confidence','pursuit','parenthood'):
        source=HERE/'source'/(name+'.mp4')
        segments,info=model.transcribe(str(source),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
        rows=[]
        for seg in segments:
            rows.append({'start':round(seg.start,3),'end':round(seg.end,3),'text':seg.text.strip(),
                         'words':[{'w':w.word,'s':round(w.start,3),'e':round(w.end,3),'p':round(w.probability,3)} for w in seg.words or []]})
            print(name,round(seg.start,2),seg.text.strip(),flush=True)
        (HERE/'source'/(name+'-transcript.json')).write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (HERE/'transcription.json').write_text(json.dumps({'backend':device,'model':'small','compute_type':'int8_float16','sources':3},indent=2),encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
