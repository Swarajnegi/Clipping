"""LAYER: Engineer. Resume the exact saved scene in owner-authorized cooling batches.
THE FLOW: verify scene identity -> GPU only -> cool/admit -> at most two frames -> release load.
The outer job retains all existing pressure aborts; another resource abort ends this attempt.
"""
from __future__ import annotations
import bpy,sys,json,time,subprocess,hashlib,struct,zlib
from pathlib import Path
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(PROJECT))
from common import require_guard,wait_headroom
from scene import setup_gpu
COOLING_TARGET_C=73

def valid_png(path:Path)->bool:
    if not path.is_file():return False
    try:
        with path.open('rb') as stream:
            if stream.read(8)!=b'\x89PNG\r\n\x1a\n':return False
            header=False
            while True:
                raw=stream.read(8)
                if len(raw)!=8:return False
                length,kind=struct.unpack('>I4s',raw)
                if length>32*1024*1024:return False
                data=stream.read(length);check=stream.read(4)
                if len(data)!=length or len(check)!=4 or zlib.crc32(kind+data)&0xffffffff!=struct.unpack('>I',check)[0]:return False
                if kind==b'IHDR':header=struct.unpack('>II',data[:8])==(1080,1920)
                if kind==b'IEND':return header
    except (OSError,ValueError,struct.error):return False

def temperature()->float:
    result=subprocess.run(['nvidia-smi.exe','--id=0','--query-gpu=temperature.gpu','--format=csv,noheader,nounits'],
                          capture_output=True,text=True,timeout=8,check=True)
    value=float(result.stdout.strip())
    if not 0<=value<=110:raise RuntimeError('GPU temperature telemetry unavailable')
    return value

def cool()->dict:
    start=time.monotonic();last_report=-60;stable=None
    while True:
        now=time.monotonic();value=temperature()
        stable=(stable if stable is not None else now) if value<=COOLING_TARGET_C else None
        if stable is not None and now-stable>=10:
            wait_headroom(gpu=True)
            value=temperature()
            if value<=COOLING_TARGET_C:return {'wait_seconds':time.monotonic()-start,'admission_temperature_c':value}
            stable=None
        if now-start-last_report>=60:
            print(f'COOLING waiting for <={COOLING_TARGET_C} C for 10s; current {value:.0f} C',flush=True);last_report=now-start
        if now-start>=600:raise RuntimeError('Deferred: GPU did not reach the cooling target within 10 minutes')
        time.sleep(5)

def main():
    require_guard(gpu=True)
    marker=json.loads((PROJECT/'frames/render-source.json').read_text())
    current=hashlib.sha256((PROJECT/'scene.py').read_bytes()).hexdigest()
    if marker['sha256']!=current:raise RuntimeError('Saved frames do not match the scene source')
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'touchscreen.blend'))
    devices=setup_gpu();scene=bpy.context.scene
    if scene.render.engine!='CYCLES' or scene.cycles.samples!=32:raise RuntimeError('Unexpected saved render settings')
    scene.cycles.device='GPU';scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
    remaining=[frame for frame in range(1,241) if not valid_png(PROJECT/'frames'/f'{frame:04d}.png')]
    records=[];events=[]
    (PROJECT/'cooling-policy.json').write_text(json.dumps({'owner_authorized':True,'maximum_frames_per_batch':2,
        'temperature_before_batch_c':COOLING_TARGET_C,'stable_cooling_seconds':10,'maximum_wait_seconds':600,
        'existing_guard_limits_unchanged':True,'devices':devices,'source_sha256':current},indent=2))
    for offset in range(0,len(remaining),2):
        events.append(cool())
        (PROJECT/'cooling-events.json').write_text(json.dumps(events,indent=2))
        for frame in remaining[offset:offset+2]:
            path=PROJECT/'frames'/f'{frame:04d}.png'
            if path.exists():
                interrupted=PROJECT/'interrupted';interrupted.mkdir(exist_ok=True)
                path.replace(interrupted/f'{frame:04d}-{time.time_ns()}.png')
            scene.frame_set(frame);scene.render.filepath=str(path);start=time.monotonic()
            bpy.ops.render.render(write_still=True)
            if not valid_png(path):raise RuntimeError(f'Frame {frame} failed validation')
            records.append({'frame':frame,'seconds':time.monotonic()-start,'temperature_after_frame_c':temperature()})
            (PROJECT/'cooled-animation-timings.json').write_text(json.dumps(records,indent=2))
            print(f'CLIPPING_COOLED_FRAME_DONE {frame}',flush=True)

if __name__=='__main__':main()
