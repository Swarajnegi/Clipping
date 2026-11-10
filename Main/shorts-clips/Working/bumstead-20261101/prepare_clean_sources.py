"""Reframe the authorized original to exclude publisher overlays, retaining copied audio."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,encoder,ffmpeg_command,probe,require_guard

def audio_hash(path):
    return subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-map','0:a:0','-c','copy','-f','hash','-hash','sha256','-']),capture_output=True,text=True,check=True).stdout.strip()

def main():
    require_guard(gpu=True)
    folder=HERE/'source-clean'
    folder.mkdir(exist_ok=True)
    decisions=json.loads((HERE/'edit-decisions.json').read_text())
    backup=HERE/'edit-decisions.with-source-branding.json'
    if not backup.exists():shutil.copy2(HERE/'edit-decisions.json',backup)
    for decision in decisions:
        name=decision['work_id'].split('_')[-1]
        old=ROOT/'work'/decision['work_id']
        source=HERE/'source'/(name+'.mp4')
        cleaned=folder/(name+'.mp4')
        if cleaned.exists():raise RuntimeError('Clean source already exists; inspect before replacing')
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(source),
                       '-map','0:v:0','-map','0:a:0','-vf','crop=1740:816:90:0',
                       *encoder(18),'-r','25','-fps_mode','cfr','-c:a','copy','-movflags','+faststart',str(cleaned)]),check=True)
        if audio_hash(source)!=audio_hash(cleaned):raise RuntimeError('Reframing changed encoded source audio')
        media=probe(cleaned)
        target=ROOT/'work'/('bumstead_clean_20261101_'+name)
        if target.exists():raise RuntimeError('Clean work folder already exists')
        target.mkdir(parents=True)
        metadata=json.loads((old/'source.json').read_text())
        metadata.update(id=target.name,path=str(cleaned),original_path=str(source),
                        width=media.width,height=media.height,duration=media.duration,
                        fps=media.fps,rate=media.rate,
                        source_crop={'x':90,'y':0,'width':1740,'height':816,'original_width':1920,'original_height':960},
                        branding='No overlaid channel symbol; bottom publisher mark excluded by reframing',
                        encoded_source_audio_preserved=True)
        (target/'source.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
        shutil.copy2(old/'transcript.json',target/'transcript.json')
        shutil.copy2(old/'caption-corrections.json',target/'caption-corrections.json')
        spec=json.loads((old/'clips.json').read_text())
        spec['id']=target.name
        spec['clips'][0]['referenceEdit']['bandHeight']=506
        spec['branding']='No channel symbol. Foreign publisher overlay excluded from the source frame.'
        (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
        frames=HERE/'clean-source-frames'/name
        frames.mkdir(parents=True,exist_ok=True)
        for i,t in enumerate((0.5,2.2,10,25,40,min(55,media.duration-0.2))):
            subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(cleaned),'-frames:v','1','-vf','scale=870:408',str(frames/f'{i:02d}.jpg')]),check=True)
        decision.update(work_id=target.name,branding='No symbol; original publisher overlay excluded by a top-aligned crop',
                        source_resolution=[1740,816],acquired_source_resolution=[1920,960])
        print('CLEAN_SOURCE',name,json.dumps(metadata),flush=True)
    (HERE/'edit-decisions.json').write_text(json.dumps(decisions,indent=2),encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
