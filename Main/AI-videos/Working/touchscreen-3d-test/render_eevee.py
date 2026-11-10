"""LAYER: Engineer. Compare a real-time GPU render of the same original 3D scene.
THE FLOW: load unchanged geometry -> enable supported ray tracing -> render -> verify GPU vendor.
"""
from pathlib import Path
import sys,time,json,subprocess,hashlib
import bpy,gpu
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(PROJECT))
from common import require_guard
from render_cooled import valid_png
FRAME_ADMISSION_BELOW_C=80

def temperature():
    value=subprocess.run(['nvidia-smi.exe','--id=0','--query-gpu=temperature.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=8)
    return float(value.stdout.strip())

def main():
    require_guard(gpu=True)
    mode=sys.argv[sys.argv.index('--')+1]
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'touchscreen.blend'))
    scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
    settings=scene.eevee
    settings.taa_render_samples=32
    if hasattr(settings,'use_raytracing'):settings.use_raytracing=True
    if hasattr(settings,'ray_tracing_method'):settings.ray_tracing_method='SCREEN'
    glass=bpy.data.materials['Optical cover glass']
    glass.surface_render_method='DITHERED'
    glass.use_raytrace_refraction=True
    glass.thickness_mode='SLAB'
    bpy.data.objects['Protective glass'].visible_shadow=False
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    animation=mode=='eevee-animation'
    folder=PROJECT/('eevee-frames' if animation else 'eevee-preview');folder.mkdir(exist_ok=True)
    identity={'sha256':hashlib.sha256((PROJECT/'scene.py').read_bytes()).hexdigest(),
              'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'renderer':'BLENDER_EEVEE_NEXT',
              'samples':32,'cpu_rendering_enabled':False,'threads':2}
    if animation:
        marker=folder/'render-source.json'
        if marker.exists() and json.loads(marker.read_text())!=identity:raise RuntimeError('EEVEE frame source changed')
        marker.write_text(json.dumps(identity,indent=2))
    frames=range(1,241) if animation else [1,105,210]
    records=[];device=None
    started_stage=time.monotonic();cooling_seconds=0.0
    for frame in frames:
        if animation and valid_png(folder/f'{frame:04d}.png'):continue
        if animation:
            start_cool=time.monotonic()
            while temperature()>=FRAME_ADMISSION_BELOW_C:
                print('EEVEE cooling before next frame',flush=True)
                if time.monotonic()-start_cool>600:raise RuntimeError('GPU failed to cool within ten minutes')
                time.sleep(5)
            cooling_seconds+=time.monotonic()-start_cool
            old=folder/f'{frame:04d}.png'
            if old.exists():
                interrupted=PROJECT/'interrupted';interrupted.mkdir(exist_ok=True)
                old.replace(interrupted/f'eevee-{frame:04d}-{time.time_ns()}.png')
        scene.frame_set(frame);scene.render.filepath=str(folder/f'{frame:04d}.png');started=time.monotonic()
        bpy.ops.render.render(write_still=True)
        if not valid_png(folder/f'{frame:04d}.png'):raise RuntimeError(f'Invalid EEVEE frame {frame}')
        device={'vendor':gpu.platform.vendor_get(),'renderer':gpu.platform.renderer_get(),'backend':gpu.platform.backend_type_get()}
        print('EEVEE_GPU '+json.dumps(device),flush=True)
        if 'NVIDIA' not in str(device['vendor']).upper() or '2060' not in str(device['renderer']):
            raise RuntimeError('The RTX 2060 graphics renderer was not verified; no CPU/integrated GPU fallback permitted')
        records.append({'frame':frame,'seconds':time.monotonic()-started,'device':device})
        (PROJECT/f'{mode}-timings.json').write_text(json.dumps(records,indent=2))
        print(f'EEVEE_FRAME_DONE {frame}',flush=True)
    if animation:
        if device is None:
            previous=json.loads((PROJECT/'eevee-animation-timings.json').read_text())
            device=previous[-1]['device']
        bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT/'touchscreen-eevee.blend'))
        (PROJECT/'eevee-animation-receipt.json').write_text(json.dumps({**identity,'device':device,
            'rendered_frames_this_attempt':len(records),'requested_frames':240,'wall_seconds':time.monotonic()-started_stage,
            'cooling_seconds':cooling_seconds,'frame_admission_below_c':FRAME_ADMISSION_BELOW_C,'frame_timings':records},indent=2))

if __name__=='__main__':main()
