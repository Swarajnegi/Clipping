"""Research source windows only. Preserve original context/marks; not upload deliverables."""
import json,sys,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,FFPROBE,ffmpeg_command
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
require_guard(gpu=True)
windows=[('matthew-offer','QMzxNfX-uAg',6132,6187),('matthew-father','QMzxNfX-uAg',1640,1755),
 ('hormozi-father','M4PzOjM5BJQ',3948,4002),('hudson-marriage','xNwYaTf7Zn8',863,939)]
receipts=[]
for slug,video,start,end in windows:
 folder=P/'source-review';folder.mkdir(exist_ok=True);target=folder/(slug+'-h264.mp4')
 if not target.exists():
  opts={'format':'bestvideo[height<=720][vcodec^=avc1]+bestaudio[ext=m4a]',
   'download_ranges':download_range_func(None,[(start,end)]),'outtmpl':str(target),'merge_output_format':'mp4',
   'noplaylist':True,'ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),'cachedir':False,
   'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},'retries':0,'fragment_retries':0,'extractor_retries':0,'socket_timeout':25,
   'external_downloader_args':{'ffmpeg_i':['-threads','2'],'ffmpeg_o':['-threads','2']},'postprocessor_args':{'ffmpeg':['-threads','2']}}
  with YoutubeDL(opts) as y:y.download(['https://www.youtube.com/watch?v='+video])
 info=json.loads(subprocess.check_output([str(FFPROBE),'-v','error','-select_streams','v:0','-show_entries','stream=codec_name','-of','json',str(target)]))
 if info['streams'][0]['codec_name']!='h264':raise ValueError('Unexpected research codec; stop before CUDA decoding')
 image=folder/(slug+'-h264-sheet.jpg')
 cmd=ffmpeg_command([FFMPEG,'-y','-hwaccel','cuda','-i',str(target),'-an','-vf','fps=1/5,scale=384:-1,tile=4x6:padding=4:margin=4','-frames:v','1',str(image)])
 with (folder/(slug+'-frame-extraction.log')).open('w',encoding='utf-8') as log:
  subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=log)
 receipts.append({'slug':slug,'source_url':'https://www.youtube.com/watch?v='+video,'context_start':start,'context_end':end,'file':str(target),'sheet':str(image),'coverage':'source context window, five-second visual samples; no direct listening claim'})
 (P/'source-review/receipts.json').write_text(json.dumps(receipts,indent=2),encoding='utf-8')
 print('INSPECTABLE',slug,flush=True)
