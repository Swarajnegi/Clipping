"""LAYER: Engineer. THE BIG PICTURE: deliver measured evidence with the original 3D pilot.
THE FLOW: validate completed stages -> summarize guard telemetry -> extrapolate render time -> save receipts.
"""
from pathlib import Path
from datetime import datetime,timezone
from typing import Any
import argparse,json,sys,hashlib,re,statistics,shutil

PROJECT=Path(__file__).resolve().parent
ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard


def read(path:Path)->dict[str,Any]:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path:Path,value:dict[str,Any])->None:
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2))
    temporary.replace(path)


def guard_evidence(identity:str,role:str)->dict[str,Any]:
    if not re.fullmatch('[a-f0-9]{32}',identity):raise ValueError('Invalid guard identity')
    folder=ROOT/'.runtime/guard'/identity
    result=read(folder/'result.json')
    samples=[]
    with (folder/'samples.jsonl').open(encoding='utf-8-sig') as stream:
        for line in stream:
            if line.strip():samples.append(json.loads(line))
    def values(key):return [s[key] for s in samples if isinstance(s.get(key),(int,float))]
    return {'role':role,'id':identity,'result':result,
            'wall_seconds_including_admission':max(0,(folder/'result.json').stat().st_mtime-folder.stat().st_ctime),
            'sample_count':len(samples),'peak_gpu_c':max(values('Temperature'),default=None),
            'minimum_system_available_ram_gib':min(values('RamGiB'),default=None),
            'minimum_free_gpu_memory_gib':min(values('VramGiB'),default=None),
            'peak_system_cpu_percent':max(values('Cpu'),default=None),
            'telemetry_interval_seconds':5,'memory_scope':'System-wide; not isolated Blender allocations'}


def main()->None:
    require_guard()
    parser=argparse.ArgumentParser()
    for stage in ('render','encode','qa'):parser.add_argument('--'+stage+'-guard',required=True)
    args=parser.parse_args()
    stages=[guard_evidence(getattr(args,stage+'_guard'),stage) for stage in ('render','encode','qa')]
    for stage in stages:
        result=stage['result']
        if result['status']!='worker_succeeded' or not result['cleanup_confirmed']:
            raise RuntimeError('A required stage has not completed with confirmed cleanup')
    encoding=read(PROJECT/'encode-receipt.json');decode=read(PROJECT/'decode-validation.json')
    encoding_log=(PROJECT/'encode.log').read_text(encoding='utf-8')
    nvenc_commands=[line for line in encoding_log.splitlines() if line.startswith('[prespawnFfmpeg()]') and '-c:v,h264_nvenc' in line]
    copy_commands=[line for line in encoding_log.splitlines() if line.startswith('[stitchFramesToVideo()] -threads') and '-c:v copy' in line]
    if not nvenc_commands or not copy_commands:raise RuntimeError('GPU encoding followed by stream-copy finalization was not verified')
    frames=read(PROJECT/'frame-validation.json');animation=read(PROJECT/'eevee-animation-receipt.json')
    output=Path(encoding['output'])
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    if not decode['passed'] or digest!=decode['sha256'] or digest!=encoding['sha256']:
        raise RuntimeError('Validated output identity mismatch')
    if frames['count']!=240 or not frames['passed'] or frames['renderer']!='eevee':raise RuntimeError('Frame validation incomplete')
    attempts=[
        ('977d9c764c27439f9324c73cf946a3d8','initial Cycles thermal abort'),
        ('275e7cbb74774d6a8344df33240c7dfb','maximum-fan Cycles thermal abort'),
        ('ed33941d99de4c8aaf9732938779aec4','cooled Cycles; deliberately checkpointed for new policy'),
        ('7fddbcb2fa054dc0a1a6ae3b72d3b2c7','continuous Cycles; software thermal regulation flag at 86 C'),
        ('a7aeefc4332c4a8bbebff5c337f81ae1','cooled Cycles; deliberately checkpointed for EEVEE comparison'),
        ('3dfb03bda74c4ae491e245a775cc6850','cooled Cycles; deliberately checkpointed to adjust cooling target'),
        ('7ddf873f307c45ac8267f5031c9781b2','cooled Cycles; deliberately checkpointed after 100 frames'),
        ('bf17a75fc289405ba13d2fdf6348e627','initial EEVEE comparison; rejected material setup'),
        ('15e4b3a29c2e4d8bb4144c109ba52508','EEVEE transmission comparison; opaque-shadow issue'),
        ('959bdf55a7124a0fbc38ebd4799666d9','EEVEE material validation; three native-resolution stills'),
        ('a67e9ae6d6fb497b87153e2fde0be921','EEVEE; deliberately checkpointed to adjust frame cooling from 78 to 80 C'),
        ('6b3d69877adf42ed9b534f07e64f5030','First encoded sample; retained before footer contrast correction'),
        ('affe8c25b743447996ac18029a2b873b','First encoded sample decode and QA')]
    history=[guard_evidence(identity,role) for identity,role in attempts]
    if not all(item['result']['cleanup_confirmed'] for item in history):raise RuntimeError('Historical tree cleanup is unconfirmed')
    measured=animation['wall_seconds']*240/max(1,animation['rendered_frames_this_attempt'])
    forecast={'profile':'Same scene complexity, 1080x1920, 30 fps, EEVEE 32 samples, temperature-paced GPU rendering',
              'measured_output_seconds_this_attempt':animation['rendered_frames_this_attempt']/30,
              'measured_stage_wall_seconds':animation['wall_seconds'],'normalized_240_frame_wall_seconds':measured,
              'measured_frame_render_median_seconds':statistics.median(row['seconds'] for row in animation['frame_timings']),
              'cooling_seconds':animation['cooling_seconds'],'retry_margin_factor':1.5,
              'whole_reel_forecast_complete':False,
              'estimated_30_second_render_hours':round(measured/8*30*1.5/3600,2),
              'estimated_60_second_render_hours':round(measured/8*60*1.5/3600,2),
              'excludes':'New geometry, shot design, animation authoring, narration, music, editorial revisions and additional scene startup',
              'limit':'A measured pilot extrapolation, not a certified 30-60 second continuous load or complete production schedule'}
    receipt={'status':'validated_sample','complete':True,'created_at':datetime.now(timezone.utc).isoformat(),
             'output':encoding,'frame_validation':frames,'decode_validation':decode,'guard_stages':stages,'attempt_history':history,
             'encoder_command_evidence':{'gpu_video_encode':nvenc_commands,'finalization_without_reencoding':copy_commands,
                 'note':'Remotion logs libx264 as the finalizer default, but the actual final command uses stream copy; it does not encode video on CPU.'},
             'renderer':animation,'scene':str(PROJECT/'touchscreen-eevee.blend'),'original_cycles_scene':str(PROJECT/'touchscreen.blend'),
             'retained_cycles_frames':len(list((PROJECT/'frames').glob('*.png'))),
             'visual_review':'Three representative native-resolution EEVEE stills and final QA strip inspected; no narration or avatar requested',
             'asset_provenance':'Original assistant-authored procedural geometry, materials and animation; no reference footage reused',
             'eevee_material_adaptation':'Raytraced slab transmission; glass opaque shadow disabled to approximate light transmission',
             'pacing_change':read(PROJECT/'eevee-pacing-change.json'),
             'thermal_policy':{'scope':'Owner-authorized touchscreen pilot only','warn_c':85,'stop_c':90,'stop_seconds':10,
                               'stop_on_hardware_or_software_thermal_throttling':True,'other_runs_default_stop_c':85},
             'quality_limit':'32-sample glass retains visible grain; this is a visual pilot, not a claimed photorealistic final reel',
             'installer':read(ROOT/'.runtime/blender/4.5.15/installation.json'),
             'guard_verification':{'checks_passed':79,'evidence':str(ROOT/'.runtime/ai-video/thermal-profile-tests.log'),
                 'launcher_sha256':hashlib.sha256((ROOT/'.agents/skills/viral-shorts/scripts/run_guarded.ps1').read_bytes()).hexdigest(),
                 'native_sha256':hashlib.sha256((ROOT/'.agents/skills/viral-shorts/scripts/guard_native.cs').read_bytes()).hexdigest()},
             'sustained_cycles_profile_certified':False,'forecast':forecast}
    write_json(PROJECT/'forecast.json',forecast)
    prior=PROJECT/'test-receipt.json'
    archive=PROJECT/'first-thermal-test-receipt.json'
    if prior.exists() and not archive.exists():shutil.copy2(prior,archive)
    write_json(prior,receipt)
    for source,name in ((prior,'receipt.json'),(PROJECT/'forecast.json','forecast.json')):
        temporary=output.parent/(name+'.tmp')
        shutil.copy2(source,temporary)
        temporary.replace(output.parent/name)
    print(json.dumps({'receipt':str(prior),'forecast':forecast},indent=2),flush=True)


if __name__=='__main__':main()
