"""LAYER: Engineer. THE BIG PICTURE: render and measure a GPU-only 3D pilot.
THE FLOW: bind portable Blender paths -> GPU Blender stage -> inspect -> Remotion/NVENC export.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys,time,hashlib
from pathlib import Path
PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,NODE,REMOTION,PUBLIC,probe,run,FFMPEG

def validate_sequence(renderer):
    from PIL import Image
    frames=PROJECT/('eevee-frames' if renderer=='eevee' else 'frames')
    actual=sorted(frames.glob('*.png'))
    if [p.stem for p in actual]!=[f'{i:04d}' for i in range(1,241)]:
        raise RuntimeError('The 240-frame sequence is incomplete')
    source=json.loads((frames/'render-source.json').read_text())
    if source['sha256']!=hashlib.sha256((PROJECT/'scene.py').read_bytes()).hexdigest():
        raise RuntimeError('Frame source identity changed')
    if renderer=='eevee' and source['renderer_sha256']!=hashlib.sha256((PROJECT/'render_eevee.py').read_bytes()).hexdigest():
        raise RuntimeError('EEVEE settings source changed')
    for path in actual:
        with Image.open(path) as image:
            if image.size!=(1080,1920):raise RuntimeError(f'Unexpected frame dimensions: {path.name}')
            image.verify()
    (PROJECT/'frame-validation.json').write_text(json.dumps({'passed':True,'count':len(actual),
        'width':1080,'height':1920,'png_crc_verified':True,'source_sha256':source['sha256'],'renderer':renderer},indent=2))
    return actual


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['preview','benchmark','animation','cooled-animation','eevee-preview','eevee-animation','encode','qa'])
    parser.add_argument('--renderer',choices=['cycles','eevee'],default='cycles')
    args=parser.parse_args();require_guard(gpu=args.stage!='qa')
    if args.stage in ('preview','benchmark','animation','cooled-animation','eevee-preview','eevee-animation'):
        env=os.environ.copy()
        for variable,folder in [('BLENDER_USER_CONFIG','config'),('BLENDER_USER_SCRIPTS','scripts'),('BLENDER_USER_DATAFILES','datafiles'),('CUDA_CACHE_PATH','cuda-cache'),('OPTIX_CACHE_PATH','optix-cache')]:
            path=ROOT/'.runtime/blender-user'/folder;path.mkdir(parents=True,exist_ok=True);env[variable]=str(path)
        env['BLENDER_SYSTEM_PYTHON']=''
        gl_cache=ROOT/'.runtime/blender-user/gl-cache';gl_cache.mkdir(parents=True,exist_ok=True)
        env['__GL_SHADER_DISK_CACHE']='1';env['__GL_SHADER_DISK_CACHE_PATH']=str(gl_cache)
        script='render_eevee.py' if args.stage.startswith('eevee') else 'render_cooled.py' if args.stage=='cooled-animation' else 'scene.py'
        executable=ROOT/'.runtime/blender/4.5.15/blender.exe'
        with (PROJECT/f'{args.stage}.log').open('w',encoding='utf-8') as log:
            result=subprocess.run([str(executable),'--background','--factory-startup','--disable-autoexec','--threads','2',
                                   '--debug-cycles','--python-exit-code','1','--python',str(PROJECT/script),'--',args.stage],env=env,cwd=PROJECT,
                                   stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:raise SystemExit(result.returncode)
        if not (PROJECT/f'{args.stage}-timings.json').is_file():raise RuntimeError('Blender did not produce a render receipt; inspect its log')
        print((PROJECT/f'{args.stage}-timings.json').read_text(),flush=True)
    elif args.stage=='encode':
        actual=validate_sequence(args.renderer)
        frame_folder='touchscreen-3d-test-eevee' if args.renderer=='eevee' else 'touchscreen-3d-test'
        target=PUBLIC/frame_folder;target.mkdir(exist_ok=True)
        for p in actual:
            dest=target/p.name
            if dest.exists():
                if not os.path.samefile(p,dest):raise RuntimeError(f'Stale staged frame: {dest}')
            else:os.link(p,dest)
        output=ROOT/'Main/AI-videos/Exports/touchscreen-3d-test';output.mkdir(parents=True,exist_ok=True)
        pending=output/'touchscreen-3d-test.partial.mp4';start=time.monotonic()
        props=PROJECT/'composition-props.json';props.write_text(json.dumps({'frameFolder':frame_folder}))
        with (PROJECT/'encode.log').open('w',encoding='utf-8') as log:
            subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','Touchscreen3DTest',str(pending),
                           '--concurrency=1','--hardware-acceleration=required','--gl=angle','--log=verbose','--props',str(props)],
                           cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
        media=probe(pending)
        if (media.width,media.height)!=(1080,1920) or abs(media.fps-30)>.001 or abs(media.duration-8)>.08:raise RuntimeError('Output stream validation failed')
        if 'Encoder: h264_nvenc, hardware accelerated: true' not in (PROJECT/'encode.log').read_text():raise RuntimeError('NVENC execution was not verified')
        final=output/'touchscreen-3d-test.mp4';pending.replace(final)
        receipt={'output':str(final),'seconds':media.duration,'width':media.width,'height':media.height,'fps':media.fps,
                 'encode_seconds':time.monotonic()-start,'encoder':'h264_nvenc','hardware_acceleration_verified':True,
                 'concurrency':1,'renderer':args.renderer,'sha256':hashlib.sha256(final.read_bytes()).hexdigest()}
        (PROJECT/'encode-receipt.json').write_text(json.dumps(receipt,indent=2))
        print(json.dumps(receipt),flush=True)
    else:
        final=ROOT/'Main/AI-videos/Exports/touchscreen-3d-test/touchscreen-3d-test.mp4'
        from build import qa_strip
        qa_strip(final,PROJECT/'qa.jpg',probe(final).duration)
        run([FFMPEG,'-v','error','-i',str(final),'-f','null','-'])
        (PROJECT/'decode-validation.json').write_text(json.dumps({'passed':True,'full_decode':True,
            'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'audio_requested':False},indent=2))

if __name__=='__main__':main()
