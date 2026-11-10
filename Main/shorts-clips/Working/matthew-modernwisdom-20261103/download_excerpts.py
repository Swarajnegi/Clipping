"""Download only selected original episode passages with room for context."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard, probe
require_guard(gpu=True)
home=Path(__file__).resolve().parent
source=home/'source'
excerpts=[('02-successes','00:30:15','00:32:20'),('03-endurance','01:01:35','01:03:30'),('04-relevance','01:43:20','01:44:50')]
base=[str(ROOT/'.venv/Scripts/yt-dlp.exe'),'--no-playlist','--js-runtimes',f'node:{ROOT/".runtime/node/node.exe"}',
 '--ffmpeg-location',str(ROOT/'.runtime/ffmpeg/bin'),'--format','bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]',
 '--downloader-args','ffmpeg_i:-threads 2','--downloader-args','ffmpeg_o:-threads 2 -filter_threads 2 -filter_complex_threads 2']
records=[]
for name,start,end in excerpts:
 path=source/f'{name}.mp4'
 if not path.exists():
  subprocess.run([*base,'--download-sections',f'*{start}-{end}','--output',str(source/f'{name}.%(ext)s'),
    'https://www.youtube.com/watch?v=Eu1kHIztT24'],check=True)
 m=probe(path)
 records.append({'name':name,'requested_start':start,'requested_end':end,'path':str(path),'duration':m.duration,'fps':m.rate,'width':m.width,'height':m.height})
 print(json.dumps(records[-1]),flush=True)
(home/'source-excerpts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
