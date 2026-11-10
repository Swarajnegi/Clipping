"""LAYER: Reviewer. THE BIG PICTURE: inspect actual output and expose QA coverage.
THE FLOW: all frames CUDA-decoded -> face/caption checks -> every-phrase visual sheets.
"""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,require_guard,probe
import cv2,numpy as np
from PIL import Image,ImageDraw
require_guard(gpu=True);cv2.setNumThreads(2)
decisions=json.loads((P/'edit-decisions.json').read_text(encoding='utf-8'))
geometry=json.loads((P/'qa/caption-geometry.json').read_text(encoding='utf-8'))
assert not geometry['failures'] and not geometry['collisions']
reports=[]
for d in decisions:
    slug=d['slug'];video=P/'drafts'/f'{slug}-music-free.mp4';qa=P/'qa'/slug
    props=json.loads((qa/'props.json').read_text(encoding='utf-8'));layers=props['referenceEdit']['layers']
    assert all(l.get('surface')=='difference' for l in layers)
    pages=json.loads((P/'authoring'/slug/'caption-pages.json').read_text(encoding='utf-8'))
    boxes=[r for r in geometry['measurements'] if r['clip']==slug]
    samples={}
    for page in pages:
        visible=[l for l in layers if page['start']-.001<=l['t']<page['end']-.001]
        at=min(page['end']-.04,max(max(l['wordTimes']) for l in visible)+.12)
        samples[round(at*25)]=' / '.join(page['rows'])
    for shot in props['shots']:
        for delta in [0,.12]:samples[min(d['frames']-1,round((shot['t']+delta)*25))]='CAMERA CUT'
    samples[0]='OPEN';samples[d['frames']-1]='END'
    width,height=432,768;stride=width*height*3
    command=ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-hwaccel_output_format','cuda','-i',str(video),
        '-an','-vf',f'scale_cuda={width}:{height},hwdownload,format=nv12,format=bgr24','-f','rawvideo','-pix_fmt','bgr24','-'])
    detector=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),'',(width,height),.7,.3,5000)
    tiles=[];overlaps=[];missing=[];i=0;faces_seen=0
    with (qa/'qa-decode.stderr.log').open('wb') as errors:
        process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=errors)
        while True:
            buf=process.stdout.read(stride)
            if not buf:break
            if len(buf)!=stride:raise RuntimeError('Incomplete decoded frame')
            im=np.frombuffer(buf,np.uint8).reshape(height,width,3).copy();t=i/25
            _,faces=detector.detect(im)
            if faces is None:missing.append(i)
            else:
                faces_seen+=1
                active=[b for b in boxes if b['t']<=t<b['t']+b['dur']]
                for face in faces:
                    x,y,w,h=[float(v)/.4 for v in face[:4]]
                    for layer in active:
                        if any(b['x']<x+w and x<b['x']+b['w'] and b['y']<y+h and y<b['y']+b['h']+12 for b in layer['boxes']):
                            overlaps.append({'frame':i,'caption':layer['text'],'face':[x,y,w,h]})
            if i in samples:
                tile=Image.new('RGB',(432,808),'#101418');tile.paste(Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB)),(0,40))
                ImageDraw.Draw(tile).text((8,5),f'{t:.2f}s  {samples[i][:64]}',fill='white');tiles.append(tile)
            i+=1
        if process.wait():raise RuntimeError('Final full decode failed')
    assert i==d['frames'],(slug,i,d['frames'])
    assert not (qa/'qa-decode.stderr.log').read_text().strip()
    for sheet_index,start in enumerate(range(0,len(tiles),9)):
        sheet=Image.new('RGB',(1296,2424),'#101418')
        for j,tile in enumerate(tiles[start:start+9]):sheet.paste(tile,((j%3)*432,(j//3)*808))
        sheet.save(qa/f'phrases-{sheet_index+1:02d}.jpg',quality=95)
    stats=subprocess.run(ffmpeg_command([FFMPEG,'-v','info','-i',str(video),'-vn','-af','ebur128=peak=true','-f','null','-']),capture_output=True,text=True,check=True)
    (qa/'audio-loudness.log').write_text(stats.stderr,encoding='utf-8')
    # A review-only proxy preserves the full picture/timing/dialogue for playback.
    proxy=qa/'review-720.mp4'
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(video),'-vf','scale=720:1280',
        '-c:v','h264_nvenc','-preset','p4','-b:v','1800k','-c:a','copy',str(proxy)]),check=True)
    report={'clip':slug,'frames_decoded':i,'face_frames':faces_seen,'missing_face_frames':missing,
        'caption_face_overlaps':overlaps,'sampled_frames':len(tiles),'caption_words':d['caption_words'],
        'difference_layers':len(layers),'source_fps':25,'proxy':str(proxy),
        'coverage':'All frames decoded and face-tested; every caption composition/camera cut sampled for assistant inspection. Does not establish continuous human listening.'}
    (qa/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8');reports.append(report)
    print(slug,i,'frames',len(overlaps),'overlaps',len(missing),'missing faces',flush=True)
(P/'qa/automated.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
if any(r['caption_face_overlaps'] for r in reports):raise RuntimeError('Inspect/fix detected caption/face overlaps before delivery')
