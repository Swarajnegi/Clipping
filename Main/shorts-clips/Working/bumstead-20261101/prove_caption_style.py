"""Render two seconds of the actual revised caption treatment before the batch."""
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,NODE,REMOTION,ffmpeg_command,require_guard,wait_headroom

def main():
    require_guard(gpu=True)
    vid='bumstead_20261101_confidence'
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(ROOT/'work'/vid/'clips.json'),'--no-render'],cwd=ROOT,check=True)
    folder=HERE/'caption-proof'
    folder.mkdir(exist_ok=True)
    wait_headroom(gpu=True)
    subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(folder/'style-proof.mp4'),
                    '--props='+str(ROOT/'work'/vid/'props/clip_01.json'),'--frames=0-49','--concurrency=1',
                    '--offthreadvideo-video-threads=2','--hardware-acceleration=required','--gl=angle','--log=error'],cwd=ROOT,check=True)
    from PIL import Image,ImageDraw
    sheet=Image.new('RGB',(2160,1128),'#121212')
    draw=ImageDraw.Draw(sheet)
    for i,t in enumerate((0.16,0.64,1.24,1.80)):
        path=folder/f'{i}.jpg'
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(folder/'style-proof.mp4'),'-frames:v','1','-vf','crop=1080:540:0:690',str(path)]),check=True)
        x,y=(i%2)*1080,(i//2)*564
        with Image.open(path) as im:sheet.paste(im,(x,y+23))
        draw.text((x+6,y+5),str(t)+'s',fill='white')
    sheet.save(folder/'style-proof-sheet.jpg')
    return 0

if __name__=='__main__':raise SystemExit(main())
