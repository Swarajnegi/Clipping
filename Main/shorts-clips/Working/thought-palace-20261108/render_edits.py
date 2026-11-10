"""Guarded representative stills or full 4K picture render, then copy approved dialogue/SFX."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,NODE,REMOTION,FFMPEG,ffmpeg_command
from motion_edit import audio_packets,decode
require_guard(gpu=True)
mode=sys.argv[1]
ids=sys.argv[2:] or [r['id'] for r in json.loads((P/'proofs.json').read_text())]
moments={'01-actions-not-thoughts':3.15,'02-permission-to-change':1.75,
         '03-hiding-your-real-self':.96,'04-choose-your-regret':1.18,'05-keep-your-own-promises':1.44}
for id in ids:
    props_path=P/'props'/(id+'.json')
    props=json.loads(props_path.read_text())
    # Source-frame inspection found the animated Modern Wisdom long mark extending
    # into the left crop of 04. Reframe cleanly; do not conceal it with captions.
    if id in ('01-actions-not-thoughts','04-choose-your-regret'):
        for shot in props['shots']:shot['x']=max(shot['x'],.44)
        props_path.write_text(json.dumps(props,indent=2))
    shared=[f'--props={props_path}','--scale=2','--gl=angle',
            '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728']
    if mode=='stills':
        dest=P/'qa'/(id+'-caption-still-4k.png')
        subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(dest),
            f'--frame={round(moments[id]*props["fps"])}',*shared],cwd=ROOT,check=True)
        im=Image.open(dest);assert im.size==(2160,3840)
        im.thumbnail((360,640));im.save(P/'qa'/(id+'-caption-still-phone.png'))
        print('STILL',id,flush=True)
    elif mode=='finals':
        (P/'finished').mkdir(exist_ok=True)
        picture=P/'drafts'/(id+'-caption-picture-4k.mp4')
        final=P/'finished'/(id+'-music-free.mp4')
        if picture.exists() or final.exists():raise FileExistsError('Preserve render revisions: '+id)
        subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(picture),
            '--concurrency=1','--hardware-acceleration=required','--video-bitrate=40M','--image-format=png','--muted',
            *shared],cwd=ROOT,check=True)
        master=ROOT/'public'/props['src']
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(picture),'-i',str(master),
            '-map','0:v:0','-map','1:a:0','-c','copy','-map_metadata','-1','-movflags','+faststart',str(final)]),check=True)
        assert audio_packets(master)==audio_packets(final)
        result=decode(final,round(props['durationSec']*props['fps']))
        (P/'qa'/(id+'-render-qa.json')).write_text(json.dumps({'decode':result,
            'audio_packet_payload_and_timing_equal_to_master':True,'added_music':False,
            'sfx':'Quiet original procedural click on 01, 03, 05; none on 02,04',
            'dimensions':[2160,3840],'fps':props['fps'],'file':str(final)},indent=2))
        print('FINAL',id,flush=True)
    else:raise ValueError(mode)
