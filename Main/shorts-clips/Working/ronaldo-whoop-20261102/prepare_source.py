"""Acquire the official master, then study shortlisted passages under separate guards."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,probe,require_guard
WINDOWS=[('map',605,638),('gym',690,785),('home',355,411),('lions',410,484),
         ('talent',250,331),('breath',1065,1111),('visualize',997,1072)]


def acquire():
    require_guard()
    import yt_dlp
    brief=json.loads((HERE/'brief.json').read_text())
    if brief.get('permission_confirmed') is not True:raise RuntimeError('Reuse basis required')
    folder=HERE/'source'
    folder.mkdir(exist_ok=True)
    path=folder/'original.mp4'
    if path.exists():raise RuntimeError('Original already exists; inspect before replacement')
    opts={'outtmpl':str(folder/'original.%(ext)s'),
          'format':'bv*[width<=1920][height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[width<=1920][height<=1080]+ba/b[width<=1920]',
          'merge_output_format':'mp4','ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),
          'cachedir':str(ROOT/'.runtime/downloads/yt-dlp'),'remote_components':['ejs:github'],
          'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
          'retries':0,'fragment_retries':0,'extractor_retries':0,'socket_timeout':20,
          'postprocessor_args':{'Merger+ffmpeg_o':['-threads','2','-filter_threads','2','-filter_complex_threads','2']}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info=ydl.extract_info(brief['source_url'],download=True)
    media=probe(path)
    if not media.has_audio or media.height<720:raise RuntimeError('Source quality/audio not suitable')
    receipt={'id':'ronaldo_whoop_20261102','path':str(path),'original_url':info['webpage_url'],
             'platform_id':info['id'],'source_key':'youtube:'+info['id'],'title':info['title'],
             'uploader':info.get('uploader'),'source_start':0,'duration':media.duration,
             'width':media.width,'height':media.height,'fps':media.fps,'rate':media.rate,
             'has_audio':media.has_audio,'format':info.get('format_id'),'reuse_basis':brief['reuse_basis']}
    (folder/'original.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('ACQUIRED',json.dumps(receipt),flush=True)


def frames():
    require_guard(gpu=True)
    from PIL import Image,ImageDraw
    path=HERE/'source/original.mp4'
    for name,start,end in WINDOWS:
        folder=HERE/'source-frames'/name
        folder.mkdir(parents=True,exist_ok=True)
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-hwaccel','cuda','-hwaccel_output_format','cuda',
            '-ss',str(start),'-i',str(path),'-t',str(end-start),
            '-vf','scale_cuda=480:270:format=nv12,hwdownload,format=nv12,fps=1/2',
            '-start_number','0',str(folder/'%04d.jpg')]),check=True)
        images=sorted(folder.glob('[0-9]*.jpg'))
        for number,offset in enumerate(range(0,len(images),12),1):
            group=images[offset:offset+12]
            sheet=Image.new('RGB',(1440,300*((len(group)+2)//3)),'#111111')
            draw=ImageDraw.Draw(sheet)
            for index,file in enumerate(group):
                x,y=(index%3)*480,(index//3)*300
                with Image.open(file) as im:sheet.paste(im,(x,y+24))
                draw.text((x+5,y+5),f'{name}: original approx {start+(offset+index)*2:.1f}s',fill='white')
            sheet.save(folder/f'sheet-{number:02d}.jpg')
        print('SOURCE_FRAMES',name,len(images),flush=True)


def transcribe():
    require_guard(gpu=True)
    from prep import _load_whisper
    model,device=_load_whisper('small')
    output=HERE/'source/transcript.json'
    if output.exists():raise RuntimeError('Transcript already exists')
    segments,info=model.transcribe(str(HERE/'source/original.mp4'),word_timestamps=True,
                                  vad_filter=True,language='en',beam_size=5)
    rows=[]
    with (HERE/'source/transcript.partial.jsonl').open('x',encoding='utf-8') as stream:
        for seg in segments:
            row={'start':round(seg.start,3),'end':round(seg.end,3),'text':seg.text.strip(),
                 'words':[{'w':w.word,'s':round(w.start,3),'e':round(w.end,3),'p':round(w.probability,3)} for w in seg.words or []]}
            rows.append(row)
            stream.write(json.dumps(row)+'\n');stream.flush()
            print(round(seg.start,2),seg.text.strip(),flush=True)
    output.write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (HERE/'source/transcription-receipt.json').write_text(json.dumps({'backend':device,'model':'small',
        'compute_type':'int8_float16','segments':len(rows),'language':info.language,
        'language_probability':info.language_probability},indent=2),encoding='utf-8')


def complete_transcript():
    """Continue only the uncovered tail after a documented thermal stop."""
    require_guard(gpu=True)
    from prep import _load_whisper
    previous=[json.loads(line) for line in (HERE/'source/transcript.partial.jsonl').read_text().splitlines()]
    # Re-align the final partial clause with context, replacing overlapping journal rows.
    start=next(row['start'] for row in reversed(previous) if row['start']<940)
    kept=[row for row in previous if row['end']<=start]
    output=HERE/'source/transcript.json'
    if output.exists():raise RuntimeError('Completed transcript already exists')
    model,device=_load_whisper('small')
    segments,info=model.transcribe(str(HERE/'source/original.mp4'),word_timestamps=True,
        vad_filter=True,language='en',beam_size=5,clip_timestamps=[start,1245.146848])
    tail=[]
    with (HERE/'source/transcript-tail.partial.jsonl').open('x',encoding='utf-8') as stream:
        for seg in segments:
            row={'start':round(seg.start,3),'end':round(seg.end,3),'text':seg.text.strip(),
                 'words':[{'w':w.word,'s':round(w.start,3),'e':round(w.end,3),'p':round(w.probability,3)} for w in seg.words or []]}
            tail.append(row)
            stream.write(json.dumps(row)+'\n');stream.flush()
            print(round(seg.start,2),seg.text.strip(),flush=True)
    if not tail or tail[-1]['end']<1220:raise RuntimeError('Tail coverage incomplete')
    output.write_text(json.dumps(kept+tail,indent=2),encoding='utf-8')
    (HERE/'source/transcription-receipt.json').write_text(json.dumps({'backend':device,'model':'small',
        'compute_type':'int8_float16','segments':len(kept+tail),'language':info.language,
        'thermal_stop_guard':'78f4f270224c43b18774285b679735f3','preserved_partial_rows':len(kept),
        'remaining_original_range':[start,1245.146848],'coverage':'Full original with overlapping tail clause realigned'},indent=2),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['acquire','frames','transcribe','complete_transcript'])
    args=parser.parse_args()
    globals()[args.stage]()
