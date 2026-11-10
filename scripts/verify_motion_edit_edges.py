"""LAYER: Engineer. THE BIG PICTURE: bound audio/master and clock edge cases.
THE FLOW: owned fixtures -> guarded staging/render -> packet and timestamp checks.
"""
from pathlib import Path
from uuid import uuid4
import argparse
import subprocess
import motion_edit as m
from common import FFMPEG, ffmpeg_command, require_guard, wait_headroom


def main():
    require_guard(gpu=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-root',type=Path,required=True)
    args=parser.parse_args()
    smoke=m.read(m.under_d(args.smoke_root)/'receipt.json')
    root=m.ROOT/'.runtime/tmp'/('motion-edge-'+uuid4().hex[:8]);root.mkdir(parents=True)
    base=Path(m.read(Path(smoke['cases'][0]['project']))['source']['path'])
    assert base.is_file(),'Run the main owned-media smoke first'
    wait_headroom(gpu=True)
    pcm=root/'owned-pcm.mov'
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(base),'-t','0.64',
        '-c:v','h264_nvenc','-preset','p4','-c:a','pcm_s16le',str(pcm)]),check=True)
    path=m.prepare(str(pcm),'validation_pcm_'+uuid4().hex[:8],True)
    spec=m.read(path)
    assert spec['transcript']['segments']==[] and (path.parent/'transcript.json').is_file()
    spec.update(synthetic=True,sourceMusic=False,reuseBasis='Owned colour/tone diagnostic')
    m.save(path,spec)
    wait_headroom(gpu=True)
    output=m.render(path,scale=1)
    receipt=m.read(path.parent/'last-render.json')
    assert receipt['audio']['mode']=='one-time AAC master'
    assert receipt['audio']['packets_identical'] and receipt['audio']['timing_identical']
    assert m.audio_packets(output)==m.audio_packets(Path(receipt['audio']['compared_to']))
    # Preserve the original irregular clock; check only the normalized staging result.
    vfr=root/'owned-vfr.mp4'
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(base),
        '-vf',"select='not(eq(mod(n,3),1))'",'-fps_mode','vfr','-an','-c:v','h264_nvenc','-preset','p4',str(vfr)]),check=True)
    original=m.video_clock(vfr);assert original['regular'] is False
    vpath=m.prepare(str(vfr),'validation_vfr_'+uuid4().hex[:8],True)
    vspec=m.read(vpath)
    assert vspec['source']['normalization'] and m.video_clock(Path(vspec['source']['path']))['regular']
    normalized_clock=m.video_clock(Path(vspec['source']['path']))
    assert abs(original['duration']-normalized_clock['duration'])<=1/original['fps']+.000001
    # Recheck current duration/start invariants on both existing full smoke renders.
    clocks=[]
    for case in smoke['cases']:
        project=Path(case['project']);count=case['frames'];fps=float(m.Fraction(case['rate']))
        r=m.read(project.parent/'last-render.json')
        sig=m.picture_signature(Path(r['file']));m.validate_picture_clock(sig,count,fps)
        clocks.append({'project':str(project),'frames':count,'fps':fps,'duration':float(sig['duration']),'start_time':float(sig.get('start_time',0))})
    result={'status':'passed','pcm_project':str(path),'pcm_audio':receipt['audio'],
        'vfr_project':str(vpath),'original_clock':original,'normalized_clock':normalized_clock,
        'picture_clocks':clocks,'scope':'Owned diagnostic files only; no transcription or real-speaker playback claim'}
    m.save(m.HOME/'Working/setup-validation/edge-cases.json',result)
    print(result,flush=True)


if __name__=='__main__':main()
