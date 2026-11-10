"""Prepare subsecond visual evidence of the owner's layered typography reference."""
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard

def main():
    require_guard()
    from PIL import Image,ImageDraw
    source=ROOT/'Main/shorts-clips/Reference/WhatsApp Video 2026-11-01 at 11.58.27 AM.mp4'
    folder=HERE/'caption-reference'
    folder.mkdir(exist_ok=True)
    times=[2.10,2.60,2.88,3.12,3.50,3.90,7.30,7.65,8.00,8.40,9.00,9.40,13.0,13.4,14.0,14.7,15.3,16.0,16.6,17.3,18.0,18.7,23.5,24.0,24.6,25.2,26.0]
    for i,t in enumerate(times):
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(source),'-frames:v','1','-vf','crop=720:430:0:425,scale=720:430',str(folder/f'{i:02d}.jpg')]),check=True)
    for page,start in enumerate(range(0,len(times),9),1):
        selected=times[start:start+9]
        sheet=Image.new('RGB',(2160,454*((len(selected)+2)//3)),'#121212')
        draw=ImageDraw.Draw(sheet)
        for j,t in enumerate(selected):
            x,y=j%3*720,j//3*454
            with Image.open(folder/f'{start+j:02d}.jpg') as im:sheet.paste(im,(x,y+23))
            draw.text((x+6,y+5),f'{t:.2f}s',fill='white')
        sheet.save(folder/f'sheet-{page:02d}.jpg')
    return 0

if __name__=='__main__':raise SystemExit(main())
