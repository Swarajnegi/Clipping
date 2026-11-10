"""Guarded full-duration sheets and dense leaf-effect inspection."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG, run, require_guard
HERE=Path(__file__).resolve().parent
require_guard()
items=json.loads((HERE/'inventory.json').read_text())
for item in items:
    n=item['n'];folder=HERE/f'video-{n}';folder.mkdir(exist_ok=True)
    run([FFMPEG,'-v','error','-y','-i',item['path'],'-vf','fps=2,scale=480:-1',str(folder/'frame-%03d.jpg')])
    run([FFMPEG,'-v','error','-y','-i',item['path'],'-vf','fps=2,scale=320:-1,tile=5x5',str(folder/'sheet-%02d.jpg')])
    if n==2:
        run([FFMPEG,'-v','error','-y','-ss','10','-t','3.2','-i',item['path'],'-vf','fps=10,scale=640:-1',str(folder/'leaves-%03d.jpg')])
print('Prepared both references across their full durations; leaf interval at 10 fps.')
