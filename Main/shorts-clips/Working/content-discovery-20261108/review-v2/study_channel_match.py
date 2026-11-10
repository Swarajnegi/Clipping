"""Inspect actual published cut with missing captions and one closer-fit source lead."""
import json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command
from prep import _load_whisper
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
import numpy as np
require_guard(gpu=True)
targets=[('posted-happiness','MYDuCsVF6yw',None),('having-trouble','QMzxNfX-uAg',(551,605))]
folder=P/'channel-match';folder.mkdir(exist_ok=True)
opts={'format':'bestvideo[height<=1280][vcodec^=avc1]+bestaudio[ext=m4a]','noplaylist':True,'merge_output_format':'mp4',
 'ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),'cachedir':False,'socket_timeout':25,'retries':0,'fragment_retries':0,'extractor_retries':0,
 'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},'external_downloader_args':{'ffmpeg_i':['-threads','2'],'ffmpeg_o':['-threads','2']},'postprocessor_args':{'ffmpeg':['-threads','2']}}
for name,id,span in targets:
 path=folder/(name+'.mp4')
 if path.exists():raise FileExistsError('Preserve prior source inspection')
 settings={**opts,'outtmpl':str(path)}
 if span:settings.update(format='bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]',download_ranges=download_range_func(None,[span]))
 with YoutubeDL(settings) as y:y.download(['https://www.youtube.com/watch?v='+id])
model,device=_load_whisper('small')
for name,id,span in targets:
 path=folder/(name+'.mp4')
 raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-vn','-ar','16000','-ac','1','-f','f32le','-']),capture_output=True,check=True).stdout
 segments,_=model.transcribe(np.frombuffer(raw,np.float32),language='en',word_timestamps=True,vad_filter=True,beam_size=5)
 rows=[{'start':s.start,'end':s.end,'text':s.text.strip(),'words':[{'w':w.word.strip(),'s':w.start,'e':w.end,'p':w.probability} for w in s.words or []]} for s in segments]
 (folder/(name+'-transcript.json')).write_text(json.dumps({'source_url':'https://www.youtube.com/watch?v='+id,'context_start':span[0] if span else 0,'device':device,'segments':rows,'coverage':'Full local CUDA transcription; no direct continuous listening claim'},ensure_ascii=False,indent=2),encoding='utf-8')
 subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-i',str(path),'-vf','fps=1/5,scale=320:-2,tile=4x3:padding=4:margin=4','-frames:v','1',str(folder/(name+'-sheet.jpg'))]),check=True)
 print(name,' '.join(s['text'] for s in rows),flush=True)
