"""Measured true-peak headroom for the original dialogue; never alter the picture."""
import json
import math
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
from build import adjust_source_audio,picture_signature,matching_pictures

def finish(vid):
    require_guard()
    folder=ROOT/'out'/vid
    path=folder/'clip_01.mp4'
    work=ROOT/'work'/vid
    measurement=subprocess.run(ffmpeg_command([FFMPEG,'-v','info','-i',str(path),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-']),capture_output=True,text=True,check=True)
    data=json.JSONDecoder().raw_decode(measurement.stderr[measurement.stderr.rfind('{'):])[0]
    peak=float(data['input_tp'])
    if not math.isfinite(peak):raise RuntimeError('True-peak measurement unavailable')
    receipt={'before':data,'additional_gain_db':0,'picture_preserved':True}
    if peak>-2.0:
        gain=round(-2.5-peak,2)
        spec_path=work/'clips.json'
        spec=json.loads(spec_path.read_text())
        total=round(float(spec['clips'][0].get('sourceAudioDb',0))+gain,2)
        if not -30<=total<=0:raise RuntimeError('Required dialogue attenuation is outside the allowed range')
        pending=folder/'clip_01.peak-levelled.mp4'
        before=picture_signature(path)
        adjust_source_audio(path,gain,pending)
        after=picture_signature(pending)
        if not matching_pictures(before,after):raise RuntimeError('Audio finish changed the picture')
        backup=folder/'clip_01.before-peak-level.mp4'
        if backup.exists():raise RuntimeError('Inspect previous audio finish before replacing it')
        path.replace(backup)
        pending.replace(path)
        spec['clips'][0]['sourceAudioDb']=total
        spec_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
        receipt.update(additional_gain_db=gain,total_source_gain_db=total,picture=after)
    qa=HERE/'qa'/vid
    qa.mkdir(parents=True,exist_ok=True)
    (qa/'audio-finish.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('AUDIO_FINISHED',vid,json.dumps(receipt),flush=True)
    return receipt

if __name__=='__main__':
    vid=sys.argv[1]
    finish(vid)
    from qa_exports import inspect
    inspect(vid)
