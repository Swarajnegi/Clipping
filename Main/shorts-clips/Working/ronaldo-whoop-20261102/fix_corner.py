"""Repair the complete original corner mark before cropping, avoiding edge color bleed."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,encoder,ffmpeg_command,probe,require_guard
require_guard(gpu=True)
parser=argparse.ArgumentParser()
parser.add_argument('mode',choices=['proof','master'])
args=parser.parse_args()
original=HERE/'source/original.mp4'
output=HERE/'source'/('corner-proof.mp4' if args.mode=='proof' else 'clean-final.mp4')
reuse_proof=output.exists() and args.mode=='proof'
if output.exists() and not reuse_proof:raise RuntimeError('Preserve existing output')
if args.mode=='master' and not (HERE/'corner-proof-approved.json').exists():raise RuntimeError('Visual proof approval required')
command=[FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda']
if args.mode=='proof':command+=['-ss','365']
command+=['-i',str(original)]
if args.mode=='proof':command+=['-t','2']
command+=['-map','0:v:0','-map','0:a:0','-vf',
    'hwdownload,format=nv12,delogo=x=40:y=40:w=300:h=150,crop=1480:1080:250:0',
    *encoder(18),'-c:a','copy','-movflags','+faststart',str(output)]
if not reuse_proof:subprocess.run(ffmpeg_command(command),check=True)
media=probe(output)
if (media.width,media.height)!=(1480,1080) or abs(media.fps-25)>.001:raise RuntimeError('Picture contract failed')
if args.mode=='proof':
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
        '-ss','0.5','-i',str(output),'-frames:v','1',
        '-vf','scale_cuda=740:540:format=nv12,hwdownload,format=nv12',str(HERE/'corner-proof.jpg')]),check=True)
    print('CORNER_PROOF_READY',flush=True)
else:
    def audio_hash(path):
        return subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-map','0:a:0',
            '-c','copy','-f','hash','-hash','sha256','-']),capture_output=True,text=True,check=True).stdout.strip()
    if audio_hash(original)!=audio_hash(output):raise RuntimeError('Original encoded audio changed')
    metadata=json.loads((HERE/'source/clean.json').read_text())
    metadata.update(path=str(output),edge_repair={'filter':'delogo','coordinates':'original before crop',
        'x':40,'y':40,'width':300,'height':150},gpu_processing='CUDA decode, bounded CPU corner repair/crop, NVENC encode')
    (HERE/'source/clean-final.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    for choice in json.loads((HERE/'edit-decisions.json').read_text()):
        path=ROOT/'work'/choice['work_id']/'source.json'
        old=json.loads(path.read_text())
        old.update(metadata)
        old.update(id=choice['work_id'],title=choice['title'],url=None)
        path.write_text(json.dumps(old,indent=2),encoding='utf-8')
    folder=HERE/'clean-final-proof'
    folder.mkdir(exist_ok=True)
    for index,t in enumerate((265.2,365.5,405.8,438.4,621.0,702.0,744.5,1005.0,1048.7,1094.2)):
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
            '-ss',str(t),'-i',str(output),'-frames:v','1',
            '-vf','scale_cuda=740:540:format=nv12,hwdownload,format=nv12',str(folder/f'{index:02d}.jpg')]),check=True)
    print('FINAL_CLEAN_SOURCE_READY',flush=True)
