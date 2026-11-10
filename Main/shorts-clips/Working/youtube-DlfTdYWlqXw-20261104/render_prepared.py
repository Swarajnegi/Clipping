"""Render one already-prepared clip, staging only its actual assets on D:."""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,require_guard,probe
from build import qa_strip
require_guard(gpu=True)
parser=argparse.ArgumentParser();parser.add_argument('slug');parser.add_argument('--jpeg-frames',action='store_true');args=parser.parse_args()
work_id='belmar_20261104_4k_'+args.slug
props_path=ROOT/'work'/work_id/'props/clip_01.json'
props=json.loads(props_path.read_text(encoding='utf-8'))
public=PROJECT/'render-public'/args.slug
for relative in [props['src'],'fonts/InterVariable.woff2','fonts/Inter-LICENSE.txt']:
    target=public/relative;target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():os.link(ROOT/'public'/relative,target)
drafts=PROJECT/'drafts';drafts.mkdir(parents=True,exist_ok=True)
output=drafts/(args.slug+'-music-free-DRAFT.mp4');pending=output.with_suffix('.partial.mp4')
if output.exists():raise SystemExit('Preserve completed draft; version the revision before rerendering')
started=time.monotonic()
subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(pending),
    f'--props={props_path}',f'--public-dir={public}','--concurrency=1',
    '--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728',
    '--hardware-acceleration=required','--gl=angle','--scale=2','--video-bitrate=40M',
    *(['--image-format=jpeg','--jpeg-quality=100'] if args.jpeg_frames else ['--image-format=png']),
    '--log=verbose'],cwd=ROOT,check=True)
from audio_master import mux_dialogue
copied=pending.with_name(pending.stem+'.dialogue.mp4')
mux_dialogue(pending,ROOT/'public'/props['src'],copied,PROJECT/'qa'/args.slug/'audio-copy.json')
pending.unlink();copied.replace(pending)
media=probe(pending)
assert (media.width,media.height,media.fps)==(2160,3840,25)
assert media.has_audio and abs(media.duration-props['durationSec'])<=.08
pending.replace(output)
qa_strip(output,PROJECT/'qa'/args.slug/'overview.jpg',media.duration)
receipt=dict(file=str(output),duration=media.duration,width=media.width,height=media.height,fps=media.fps,
             seconds=time.monotonic()-started,bytes=output.stat().st_size,source_music_added=False,
             frame_capture='JPEG 100' if args.jpeg_frames else 'PNG',
             status='rendered; final audiovisual review pending')
(PROJECT/'qa'/args.slug/'render.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt),flush=True)
