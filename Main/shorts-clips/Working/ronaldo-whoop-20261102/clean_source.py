"""Preserve the wide-shot host, crop corners and repair the small remaining edge mark."""
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,encoder,ffmpeg_command,probe,require_guard


def audio_hash(path):
    return subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-map','0:a:0',
        '-c','copy','-f','hash','-hash','sha256','-']),capture_output=True,text=True,check=True).stdout.strip()


require_guard(gpu=True)
source=HERE/'source/original.mp4'
target=HERE/'source/clean.mp4'
if target.exists():raise RuntimeError('Clean source exists')
# CUVID decodes/crops on GPU; the small delogo edge repair explicitly needs
# software frames. NVENC still encodes; no unannounced CPU encoding fallback.
gpu_encoder=encoder(18)
repair=['-vf','hwdownload,format=nv12,delogo=x=1:y=50:w=100:h=140']
smoke=HERE/'source/gpu-crop-smoke.mp4'
if smoke.exists():raise RuntimeError('Inspect existing crop proof')
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
    '-c:v','h264_cuvid','-crop','0x0x250x190','-ss','365','-i',str(source),'-t','2',
    '-map','0:v:0','-an',*repair,*gpu_encoder,str(smoke)]),check=True)
check=probe(smoke)
if (check.width,check.height)!=(1480,1080):raise RuntimeError('GPU crop sample dimensions failed')
print('GPU_CROP_SAMPLE_PASSED',check.width,check.height,check.fps,flush=True)
subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
    '-c:v','h264_cuvid','-crop','0x0x250x190','-i',str(source),'-map','0:v:0','-map','0:a:0',
    *repair,*gpu_encoder,'-c:a','copy','-movflags','+faststart',str(target)]),check=True)
media=probe(target)
if (media.width,media.height)!=(1480,1080) or abs(media.fps-25)>.001:raise RuntimeError('Clean crop contract failed')
original_hash=audio_hash(source)
if original_hash!=audio_hash(target):raise RuntimeError('Audio payload changed during crop')
metadata=json.loads((HERE/'source/original.json').read_text())
metadata.update(path=str(target),width=1480,height=1080,original_path=str(source),
    source_crop={'x':250,'y':0,'width':1480,'height':1080,'original_width':1920,'original_height':1080},
    edge_repair={'filter':'delogo','x':1,'y':50,'width':100,'height':140,'reason':'Remove small left publisher mark remainder while preserving wide-shot host head'},
    branding='Corner publisher overlays excluded; original clothing/product marks remain part of photographed scene',
    encoded_source_audio_preserved=True,encoded_audio_sha256=original_hash,
    gpu_processing='h264_cuvid decoder crop and h264_nvenc encode; bounded CPU edge repair')
(HERE/'source/clean.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
folder=HERE/'clean-proof'
folder.mkdir(exist_ok=True)
for index,t in enumerate((265.2,365.5,405.8,438.4,621.0,702.0,744.5,1005.0,1048.7,1094.2)):
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
        '-ss',str(t),'-i',str(target),'-frames:v','1',
        '-vf','scale_cuda=740:540:format=nv12,hwdownload,format=nv12',str(folder/f'{index:02d}.jpg')]),check=True)
print('CLEAN_SOURCE',json.dumps(metadata),flush=True)
