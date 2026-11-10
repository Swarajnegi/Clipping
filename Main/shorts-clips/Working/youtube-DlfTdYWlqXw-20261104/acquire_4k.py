"""Acquire the seven selected original 2160p windows, sequentially under the guard."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
here=Path(__file__).resolve().parent
windows=[('01-happiness-freedom','00:40:15','00:41:50'),('02-your-success','00:36:53','00:38:12'),
 ('03-self-reflection','00:45:01','00:46:07'),('04-family','00:54:14','00:54:58'),
 ('05-three-relationships','01:01:16','01:02:16'),('06-fisherman','01:08:09','01:09:00'),
 ('07-silver-thread','01:11:20','01:14:13')]
for name,start,end in windows:
 dest=here/'production-source'/f'{name}.mp4';dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():continue
 print('ACQUIRE 2160p',name,start,end,flush=True)
 subprocess.run([str(ROOT/'.venv/Scripts/yt-dlp.exe'),'--no-playlist','--ffmpeg-location',str(ROOT/'.runtime/ffmpeg/bin'),
  '-f','313+251','--download-sections',f'*{start}-{end}','--merge-output-format','mp4','-o',str(dest),
  'https://www.youtube.com/watch?v=DlfTdYWlqXw'],cwd=ROOT,check=True)
(here/'production-windows.json').write_text(json.dumps(windows,indent=2),encoding='utf-8')
