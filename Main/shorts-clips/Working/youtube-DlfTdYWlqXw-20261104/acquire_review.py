"""Acquire only candidate review windows; keep 4K production acquisition separate."""
from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard(gpu=True)
here=Path(__file__).resolve().parent
windows=[('02-success','00:36:45','00:38:15'),('03-reactions','00:44:55','00:46:12'),
 ('04-progressive-self','00:49:15','00:50:25'),('05-abundance-family','00:53:10','00:54:58'),
 ('06-relationships','01:01:10','01:02:18'),('07-fisherman','01:07:58','01:09:02'),
 ('08-progress-story','01:10:35','01:14:15'),('09-busy','00:28:35','00:29:55')]
for name,start,end in windows:
 dest=here/'source'/f'{name}.mp4'
 if dest.exists():continue
 print('ACQUIRE',name,start,end,flush=True)
 subprocess.run([str(ROOT/'.venv/Scripts/yt-dlp.exe'),'--no-playlist','--ffmpeg-location',str(ROOT/'.runtime/ffmpeg/bin'),
  '-f','137+251','--download-sections',f'*{start}-{end}','--merge-output-format','mp4','-o',str(dest),
  'https://www.youtube.com/watch?v=DlfTdYWlqXw'],cwd=ROOT,check=True)
(here/'review-windows.json').write_text(json.dumps(windows,indent=2),encoding='utf-8')
