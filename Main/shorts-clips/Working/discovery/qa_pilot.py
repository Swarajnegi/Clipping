"""Guarded full-decode, speech-correlation and sampled-visual evidence for pilot 1."""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard

def main():
    require_guard()
    import numpy as np
    from PIL import Image,ImageDraw
    source=ROOT/'out/referencepilot_20261101_parents'
    output=Path(__file__).parent/'drafts'
    frames=Path(__file__).parent/'qa/pilot-01-frames'
    frames.mkdir(parents=True,exist_ok=True)
    clean=source/'clip_01_music-free.mp4'
    mixed=source/'clip_01.mp4'
    decoded=[]
    levels=[]
    for path in (clean,mixed):
        check=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-f','null','-']),capture_output=True,text=True,check=True)
        audio=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
        decoded.append(np.frombuffer(audio,dtype=np.float32))
        levels.append(float(np.max(np.abs(decoded[-1]))))
    count=min(map(len,decoded))
    correlation=float(np.corrcoef(decoded[0][:count],decoded[1][:count])[0,1])
    if correlation<0.90 or max(levels)>=1.0:
        raise RuntimeError(f'Audio needs review: correlation={correlation}, peaks={levels}')
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(clean),'-vf','fps=1/2,scale=540:960',str(frames/'%03d.png')]),check=True)
    files=sorted(frames.glob('*.png'))
    sheet=Image.new('RGB',(1620,326*((len(files)+2)//3)),'#171717')
    draw=ImageDraw.Draw(sheet)
    for index,file in enumerate(files):
        x,y=index%3*540,index//3*326
        with Image.open(file) as im:sheet.paste(im.crop((0,328,540,632)),(x,y+22))
        draw.text((x+5,y+5),f'{index*2+1}s — cropped content band',fill='white')
    sheet.save(frames.parent/'pilot-01-content-sheet.jpg')
    receipt={'full_decode_passed':True,'audio_correlation':correlation,'audio_peak_linear':levels,
             'pair':json.loads((source/'clip_01_pair.json').read_text()),
             'status':'review draft; continuous listening and editorial acceptance pending',
             'source_quality':'640x360 discovery sample upscaled inside a 1080x1920 master',
             'music':'original-minor-bed-v1.wav; original oscillators, no reference song used',
             'cutaways':'none in this draft; first reference anime montage not yet reproduced'}
    output.mkdir(exist_ok=True)
    shutil.copy2(mixed,output/'pilot-01-mixed.mp4')
    shutil.copy2(clean,output/'pilot-01-music-free.mp4')
    (output/'pilot-01-qa.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
