"""Full local audio/transcript and every-frame face/caption checks, with honest coverage."""
import json
import subprocess
import sys
import math
import difflib
import re
from pathlib import Path
import numpy as np
import cv2
from PIL import Image, ImageDraw

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,FFMPEG,ffmpeg_command,probe
from prep import _load_whisper
from motion_edit import audio_packets,decode
require_guard(gpu=True)
cv2.setNumThreads(2)
model,device=_load_whisper('small')
results=[]
for proof in json.loads((P/'proofs.json').read_text()):
    id=proof['id']
    final=P/'finished'/(id+'-music-free.mp4')
    props=json.loads((P/'props'/(id+'.json')).read_text())
    edit=json.loads((P/'drafts'/(id+'-edit.json')).read_text())
    media=probe(final)
    assert (media.width,media.height)==(2160,3840) and abs(media.fps-proof['fps'])<1e-7
    decode_result=decode(final,proof['frames'])
    assert audio_packets(ROOT/'public'/props['src'])==audio_packets(final)
    raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(final),'-vn','-ac','1','-ar','16000','-f','f32le','-']),capture_output=True,check=True).stdout
    segments,info=model.transcribe(np.frombuffer(raw,np.float32),word_timestamps=True,vad_filter=True,language='en',beam_size=5)
    rows=[{'start':s.start,'end':s.end,'text':s.text.strip()} for s in segments]
    observed=' '.join(s['text'] for s in rows)
    expected=' '.join(w['w'] for w in edit['words'])
    norm=lambda text:re.sub(r'[^a-z0-9 ]','',text.lower()).split()
    ratio=difflib.SequenceMatcher(None,norm(expected),norm(observed)).ratio()
    (P/'qa'/(id+'-final-transcript.json')).write_text(json.dumps({'device':device,'segments':rows,
        'expected_source_words':expected,'observed':observed,'word_sequence_similarity':ratio},indent=2))
    if ratio<.82:raise RuntimeError('Final speech requires review: '+id+' '+observed)
    # Every final picture frame is decoded at phone dimensions; no visual gaps
    # are silently treated as detected faces.
    detector=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),'',(360,640),score_threshold=.7)
    process=subprocess.Popen(ffmpeg_command([FFMPEG,'-v','error','-hwaccel','cuda','-i',str(final),'-an',
        '-vf','scale=360:640','-pix_fmt','bgr24','-f','rawvideo','-']),stdout=subprocess.PIPE)
    detected=0;overlaps=[];count=0
    # One settled sample per complete authored phrase and opening-second samples.
    groups={}
    for layer in props['referenceEdit']['layers']:
        assert layer['surface']=='difference' and layer['blend']=='difference' and layer['color']=='#ffffff'
        end=round(layer['t']+layer['dur'],4)
        groups.setdefault(end,[]).append(layer)
    times=[0,.5,1,2,3]+[min(end-.04,max(l['t'] for l in group)+.13) for end,group in groups.items()]
    wanted={max(0,min(proof['frames']-1,round(t*media.fps))) for t in times}
    selected=[]
    while True:
        buf=process.stdout.read(360*640*3)
        if len(buf)!=360*640*3:break
        frame=np.frombuffer(buf,np.uint8).reshape(640,360,3)
        t=count/media.fps
        _,faces=detector.detect(frame)
        hits=[] if faces is None else [f[:4] for f in faces if 157<=f[1]+f[3]/2<=483 and f[3]>=24]
        detected+=bool(hits)
        layers=[l for l in props['referenceEdit']['layers'] if l['t']<=t<l['t']+l['dur']]
        for face in hits:
            fx,fy,fw,fh=face
            for layer in layers:
                x=layer['x']/3; y=layer['y']/3; w=layer['width']/3; h=layer['size']*1.25/3
                if min(fx+fw,x+w)>max(fx,x) and min(fy+fh,y+h)>max(fy,y):
                    overlaps.append({'frame':count,'seconds':t,'word':layer['text'],'face':face.tolist()})
        if count in wanted:
            selected.append((count,Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))))
        count+=1
    assert process.wait()==0 and count==proof['frames']
    sheet=Image.new('RGB',(6*360,math.ceil(len(selected)/6)*662),'#181818')
    for i,(number,im) in enumerate(selected):
        x=i%6*360;y=i//6*662
        sheet.paste(im,(x,y+22));ImageDraw.Draw(sheet).text((x+5,y+4),f'{number/media.fps:.2f}s / f{number}',fill='white')
    sheet.save(P/'qa'/(id+'-final-phrase-sheet.jpg'),quality=92)
    record={'id':id,'dimensions':[media.width,media.height],'fps':media.fps,'duration':proof['duration'],
        'frames':count,'decode':decode_result,'every_frame_face_check':True,'frames_with_detected_face':detected,
        'face_detection_coverage':detected/count,'caption_face_intersections':overlaps,
        'caption_words':len(props['referenceEdit']['layers']),'all_word_difference':True,
        'native_source':json.loads((P/'sources'/(id+'-source.json')).read_text())['actual'],
        'audio_payload_and_timing_unchanged_from_dialogue_sfx_master':True,'asr_sequence_similarity':ratio,
        'full_continuous_listening':'Not independently verified; bounded cloud reviewer timed out. Local full ASR, waveform/packet checks and frame analysis are not direct listening.'}
    (P/'qa'/(id+'-full-qa.json')).write_text(json.dumps(record,indent=2))
    results.append(record)
    print(id,ratio,detected,count,'caption/face overlaps',len(overlaps),flush=True)
    if overlaps:raise RuntimeError('Caption intersects detected face: '+id)
(P/'qa/final-validation.json').write_text(json.dumps(results,indent=2))
