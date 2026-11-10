"""Measured static dialogue matching; preserve every encoded picture packet."""
import hashlib
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
from build import picture_signature
from qa_exports import inspect


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    require_guard()
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',default='')
    args=parser.parse_args()
    records=[]
    for choice in json.loads((HERE/'edit-decisions.json').read_text()):
        if args.only and choice['name']!=args.only:continue
        vid=choice['work_id']
        final=ROOT/'out'/vid/'clip_01.mp4'
        spec_path=ROOT/'work'/vid/'clips.json'
        spec=json.loads(spec_path.read_text())
        clip=spec['clips'][0]
        qa_path=HERE/'qa'/vid/'qa.json'
        previous=json.loads(qa_path.read_text()) if qa_path.exists() else None
        if previous and (previous['output_sha256']!=digest(final) or previous['spec_sha256']!=digest(spec_path)):
            raise RuntimeError('Reviewed artifact changed')
        if clip.get('audioFinishDb') is not None:raise RuntimeError('Audio finishing already applied')
        before=picture_signature(final)
        if previous:
            measured=previous['loudness']
        else:
            measurement=subprocess.run(ffmpeg_command([FFMPEG,'-v','info','-i',str(final),'-vn','-af',
                'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-']),capture_output=True,text=True,check=True)
            measured=json.JSONDecoder().raw_decode(measurement.stderr[measurement.stderr.rfind('{'):])[0]
        gain=round(max(-8,min(8,-18-float(measured['input_i']),
                                 -3-float(measured['input_tp']))),2)
        if abs(gain)<.5:gain=0
        if gain:
            pending=final.with_name('clip_01.dialogue-level.pending.mp4')
            backup=final.with_name('clip_01.before-dialogue-level.mp4')
            if pending.exists() or backup.exists():raise RuntimeError('Audio stage artifact already exists')
            subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(final),
                '-map','0:v:0','-map','0:a:0','-c:v','copy','-af',f'volume={gain}dB',
                '-c:a','aac','-b:a','256k','-movflags','+faststart',str(pending)]),check=True)
            if picture_signature(pending)!=before:raise RuntimeError('Audio finishing changed picture')
            final.rename(backup)
            pending.rename(final)
        if previous:qa_path.with_name('qa.before-dialogue-level.json').write_text(json.dumps(previous,indent=2),encoding='utf-8')
        clip['audioFinishDb']=gain
        spec_path.write_text(json.dumps(spec,indent=2),encoding='utf-8')
        revised=inspect(vid)
        if revised['picture']!=before:raise RuntimeError('QA picture mismatch')
        for key in ('assistant_inspected','visual_review','branding_check','caption_pause_fix'):
            if previous and key in previous:revised[key]=previous[key]
        revised['audio_finish']={'static_gain_db':gain,'target_lufs':-18,'peak_ceiling_dbtp':-3,
                                'picture_packets_unchanged':True,
                                'visual_approval_retained_by_picture_hash':bool(previous and previous.get('assistant_inspected'))}
        qa_path.write_text(json.dumps(revised,indent=2),encoding='utf-8')
        record={'work_id':vid,'static_gain_db':gain,'lufs':float(revised['loudness']['input_i']),
                'true_peak_dbtp':float(revised['loudness']['input_tp']),
                'picture_packets_unchanged':True,'output_sha256':revised['output_sha256']}
        records.append(record)
        ledger=HERE/'dialogue-levels.json'
        if args.only and ledger.exists():
            old=json.loads(ledger.read_text())
            merged=[r for r in old if r['work_id']!=vid]+[record]
        else:merged=records
        ledger.write_text(json.dumps(merged,indent=2),encoding='utf-8')
        print('DIALOGUE_FINISHED',json.dumps(record),flush=True)


if __name__=='__main__':main()
