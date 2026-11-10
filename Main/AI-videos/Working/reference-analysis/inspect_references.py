"""LAYER: Engineer. Inspect complete reference transcripts and sampled visual timelines.
THE FLOW: metadata -> bounded frame extraction -> contact sheets -> CUDA transcription.
"""
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,probe,run,FFMPEG
from PIL import Image,ImageDraw

def main():
    require_guard(gpu=True)
    target=Path(__file__).resolve().parent
    sources=sorted((ROOT/'Main/AI-videos/Reference').glob('*.mp4'))
    for index,source in enumerate(sources,1):
        folder=target/f'ref-{index:02d}';folder.mkdir(exist_ok=True)
        media=probe(source)
        meta={'file':str(source),'bytes':source.stat().st_size,'modified':source.stat().st_mtime,'duration':media.duration,'width':media.width,'height':media.height}
        (folder/'metadata.json').write_text(json.dumps(meta,indent=2))
        if not (folder/'sheet.jpg').exists():
            run([FFMPEG,'-y','-i',str(source),'-vf','fps=1/3,scale=180:320','-q:v','3',str(folder/'frame-%03d.jpg')])
            frames=sorted(folder.glob('frame-*.jpg'))
            sheet=Image.new('RGB',(1260,4*350),'#20242c')
            for n,path in enumerate(frames):
                with Image.open(path) as image:sheet.paste(image,((n%7)*180,(n//7)*350))
                ImageDraw.Draw(sheet).text(((n%7)*180+5,(n//7)*350+324),f'{n*3:02d}s',fill='white')
            sheet.save(folder/'sheet.jpg',quality=92)
        if not (folder/'transcript.json').exists():
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'--transcribe',str(source),str(folder/'transcript.json')],check=True)
        print(json.dumps(meta),flush=True)

if __name__=='__main__':
    if '--transcribe' in sys.argv:
        require_guard(gpu=True)
        from prep import _load_whisper
        model,_=_load_whisper('small')
        segments,_=model.transcribe(sys.argv[2],word_timestamps=True)
        records=[{'start':s.start,'end':s.end,'text':s.text} for s in segments]
        Path(sys.argv[3]).write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding='utf-8')
    else:main()
