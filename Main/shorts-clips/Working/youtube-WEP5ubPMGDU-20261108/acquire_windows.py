"""LAYER: Engineer. THE BIG PICTURE: acquire only the editorially shortlisted originals.
THE FLOW: source windows -> bounded downloader/FFmpeg -> retained original excerpts.
"""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func
require_guard(gpu=True)
windows=[{'slug':'01-small-steps','start':1068,'end':1115,'lead':'Shrink the gap until you can move'},
 {'slug':'02-your-own-comparison','start':1555,'end':1608,'lead':'Compare yourself to you yesterday'},
 {'slug':'03-choose-courage','start':235,'end':275,'lead':'Rebuild optimism with courage, not naivety'},
 {'slug':'04-unmade-decisions','start':8228,'end':8276,'lead':'Avoidance is itself a decision'}]
(P/'windows.json').write_text(json.dumps(windows,indent=2),encoding='utf-8')
for w in windows:
    path=P/'source'/f"{w['slug']}.mp4";path.parent.mkdir(exist_ok=True)
    if path.exists():raise FileExistsError('Preserve existing original excerpt: '+str(path))
    print('ACQUIRE',w,flush=True)
    options={'format':'313+140','download_ranges':download_range_func(None,[(w['start'],w['end'])]),
        'outtmpl':str(path),'merge_output_format':'mp4','noplaylist':True,
        'ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),'cachedir':str(ROOT/'.runtime/yt-dlp-cache'),
        'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
        'retries':0,'fragment_retries':0,'extractor_retries':0,'socket_timeout':30,
        'external_downloader_args':{'ffmpeg_i':['-threads','2'],'ffmpeg_o':['-threads','2']},
        'postprocessor_args':{'ffmpeg':['-threads','2']}}
    with YoutubeDL(options) as ydl:ydl.download(['https://www.youtube.com/watch?v=WEP5ubPMGDU'])
print('SOURCE_WINDOWS_ACQUIRED',flush=True)
