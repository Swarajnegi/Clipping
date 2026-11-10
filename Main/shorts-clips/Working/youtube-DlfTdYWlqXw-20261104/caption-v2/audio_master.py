"""Keep the exact clean assembled dialogue, avoiding a second AAC encode."""
import json,subprocess,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard
from build import picture_signature,matching_pictures

def audio_hash(path):
    cmd=ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'])
    return subprocess.run(cmd,capture_output=True,text=True,check=True).stdout.strip()

def mux_dialogue(picture,clean_audio,destination,receipt):
    require_guard()
    before=picture_signature(picture);original_audio=audio_hash(clean_audio)
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(picture),'-i',str(clean_audio),
        '-map','0:v:0','-map','1:a:0','-c','copy','-map_metadata','-1','-movflags','+faststart',str(destination)]),check=True)
    after=picture_signature(destination);final_audio=audio_hash(destination)
    assert matching_pictures(before,after)
    assert original_audio==final_audio
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(dict(picture_unchanged=True,dialogue_packets_unchanged=True,
        clean_audio_source=str(clean_audio),audio_hash=original_audio,picture=after),indent=2),encoding='utf-8')

if __name__=='__main__':
    slug='04-family';video=PROJECT/'drafts'/(slug+'-music-free-DRAFT.mp4')
    clean=ROOT/'public/clips'/('belmar_20261104_4k_'+slug)/'clip_01.mp4'
    qa=PROJECT/'qa'/slug
    destination=video.with_suffix('.audio-fixed.mp4')
    mux_dialogue(video,clean,destination,qa/'audio-copy.json')
    prior=qa/'renderer-audio-before-copy.mp4'
    assert not prior.exists()
    video.replace(prior);destination.replace(video)
    subprocess.run([sys.executable,str(PROJECT/'qa_clip.py'),slug],cwd=ROOT,check=True)
