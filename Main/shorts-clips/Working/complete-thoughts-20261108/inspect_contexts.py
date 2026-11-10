"""Guarded CUDA word alignment of candidate neighbourhoods and full-context frame sheets."""
import argparse,json,subprocess,sys,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command,probe
from prep import _load_whisper
require_guard(gpu=True)
parser=argparse.ArgumentParser()
parser.add_argument('--mode',choices=['words','frames'],required=True)
parser.add_argument('--ids',nargs='+',required=True)
args=parser.parse_args()
# Separate ASR and paced frame stages release CUDA model memory between jobs.
# One ASR candidate per invocation follows the first run's diagnosed thermal abort.
if args.mode=='words':
    assert len(args.ids)==1
    model,device=_load_whisper('small')
for c in json.loads((P/'candidates.json').read_text()):
    id=c['id'];source=P/'sources'/(id+'.mp4');out=P/'sources'/(id+'-words.json')
    if id not in args.ids:continue
    media=probe(source);base=c['context'][0]
    a=max(0,min(s for s,e in c['proposed_source_segments'])-base-8)
    b=min(media.duration,max(e for s,e in c['proposed_source_segments'])-base+8)
    if args.mode=='words':
      if out.exists():raise FileExistsError('Preserve prior word alignment')
      raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-ss',str(a),'-i',str(source),'-t',str(b-a),
        '-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
      seg,info=model.transcribe(np.frombuffer(raw,np.float32),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
      rows=[{'start':s.start+a,'end':s.end+a,'text':s.text.strip(),'words':
        [{'w':w.word.strip(),'s':w.start+a,'e':w.end+a,'p':w.probability} for w in s.words or []]} for s in seg]
      out.write_text(json.dumps({'file':str(source),'source_url':'https://www.youtube.com/watch?v='+c['video_id'],
        'requested_context_start':base,'local_alignment_window':[a,b],'device':device,'segments':rows,
        'coverage':'Candidate neighbourhood fully CUDA-transcribed; surrounding published captions separately inspected. No continuous listening claim.'},ensure_ascii=False,indent=2),encoding='utf-8')
      print('WORDS',id,' '.join(s['text'] for s in rows),flush=True)
    else:
      dest=P/'qa'/(id+'-context-sheet.jpg')
      if dest.exists():raise FileExistsError('Preserve prior context sheet')
      count=math.ceil(media.duration/5)
      subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-readrate','2','-hwaccel','cuda',
        '-hwaccel_output_format','cuda','-i',str(source),'-an',
        '-vf',f'scale_cuda=320:180:format=yuv420p,hwdownload,format=yuv420p,fps=1/5,tile=6x{math.ceil(count/6)}:padding=3:margin=3',
        '-frames:v','1',str(dest)]),check=True)
      print('CONTEXT_FRAMES',id,flush=True)
