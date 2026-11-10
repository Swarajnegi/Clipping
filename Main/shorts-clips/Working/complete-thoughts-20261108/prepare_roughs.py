"""Project-only guarded native-rate assemblies and caption-free editorial proofs.

No final captions, added SFX, music, speed changes or invented speech. Sources stay
intact. The edit list is authored after inspecting word timing and context sheets.
"""
import argparse, json, math, subprocess, sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command, probe, encoder
from motion_edit import audio_packets, decode

require_guard(gpu=True)
parser=argparse.ArgumentParser()
parser.add_argument('--id',required=True)
parser.add_argument('--reuse-assembly',action='store_true')
args=parser.parse_args()
cv2.setNumThreads(2)
for name in ('drafts','qa','assets'):(P/name).mkdir(exist_ok=True)
mask=P/'assets/rounded-square-mask.png'
image=Image.new('L',(980,980),0)
ImageDraw.Draw(image).rounded_rectangle((0,0,979,979),radius=48,fill=255)
image.save(mask)

def run(args):
    subprocess.run(ffmpeg_command(args),check=True)

def assemble(source,pieces,dest,rate):
    """GPU decode/encode, one AAC encode and 15ms boundary fades only."""
    inputs=[];chains=[];labels=[];spans=[];offset=0
    for i,(a,b) in enumerate(pieces):
        d=b-a
        inputs += ['-readrate','2','-hwaccel','cuda','-ss',f'{a:.9f}','-t',f'{d:.9f}','-i',str(source)]
        chains += [f'[{i}:v]setpts=PTS-STARTPTS[v{i}]',
          f'[{i}:a]asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=0.015,'
          f'afade=t=out:st={d-.015:.9f}:d=0.015[a{i}]']
        labels.append(f'[v{i}][a{i}]');spans.append([a,b,offset]);offset+=d
    chains.append(''.join(labels)+f'concat=n={len(pieces)}:v=1:a=1[v][a]')
    run([FFMPEG,'-v','error','-y',*inputs,'-filter_complex',';'.join(chains),
       '-map','[v]','-map','[a]',*encoder(19),'-fps_mode','cfr','-r',rate,
       '-c:a','aac','-b:a','192k','-ar','48000','-map_metadata','-1',
       '-movflags','+faststart',str(dest)])
    return spans

records=json.loads((P/'proofs.json').read_text(encoding='utf-8')) if (P/'proofs.json').exists() else []
for edit in json.loads((P/'rough_edits.json').read_text(encoding='utf-8')):
    if edit['id']!=args.id:continue
    identifier=edit['id'];source=P/'sources'/(identifier+'.mp4')
    media=probe(source);fps=media.fps
    pieces=[(round(a*fps)/fps,round(b*fps)/fps) for a,b in edit['pieces']]
    frames=sum(round((b-a)*fps) for a,b in pieces)
    assembly=P/'drafts'/(identifier+'-clean-assembly.mp4')
    proof=P/'drafts'/(identifier+'-ROUGH.mp4')
    receipt=P/'drafts'/(identifier+'-rough.json')
    if proof.exists() or receipt.exists() or (assembly.exists() and not args.reuse_assembly):
        raise FileExistsError('Inspect existing revision before rerunning '+identifier)
    if args.reuse_assembly:
        assert assembly.exists()
        decode(assembly,frames)
        offset=0;spans=[]
        for a,b in pieces:spans.append([a,b,offset]);offset+=b-a
    else:spans=assemble(source,pieces,assembly,media.rate)
    assembled=probe(assembly)
    assert assembled.width==3840 and assembled.height==2160 and assembled.rate==media.rate
    # Five samples per second guide stable per-shot framing, never accelerate speech.
    detector=cv2.FaceDetectorYN.create(str(ROOT/'models/face_detection_yunet_2023mar.onnx'),
       '',(640,360),score_threshold=.78)
    cmd=ffmpeg_command([FFMPEG,'-v','error','-readrate','2','-hwaccel','cuda',
       '-hwaccel_output_format','cuda','-i',str(assembly),'-an',
       '-vf','scale_cuda=640:360:format=yuv420p,hwdownload,format=yuv420p',
       '-pix_fmt','bgr24','-f','rawvideo','-'])
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE)
    samples=[];previous=None;idx=0
    while True:
        buf=proc.stdout.read(640*360*3)
        if len(buf)!=640*360*3:break
        frame=np.frombuffer(buf,np.uint8).reshape(360,640,3)
        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        difference=float(np.mean(cv2.absdiff(gray,previous))) if previous is not None else 0
        previous=gray
        # Check shot switches at native FPS; run the face model at about 5 FPS
        # and on every detected cut. This avoids late crop changes at camera cuts.
        if idx % max(1,round(fps/5)) and difference<=28:
            idx+=1;continue
        _,faces=detector.detect(frame)
        hits=[] if faces is None else [f[:4].tolist() for f in faces if f[1]+f[3]/2<310]
        boxes=sorted(hits,key=lambda f:f[2]*f[3],reverse=True)
        if len(boxes)>1 and boxes[1][2]*boxes[1][3] > boxes[0][2]*boxes[0][3]*.45:
            box=sorted(boxes[:2],key=lambda f:f[0])[edit.get('wide_speaker',0)]
        else:box=boxes[0] if boxes else None
        samples.append({'t':idx/fps,'faces':hits,'x':(box[0]+box[2]/2)/640 if box else None,
          'scene_difference':difference})
        idx+=1
    assert proc.wait()==0
    # Authored cuts override sampled boundaries when an exact switch is material.
    bounds=sorted(set([0,*[s[2] for s in spans],*edit.get('shot_cuts',[]),
       *[s['t'] for s in samples if s['scene_difference']>28],frames/fps]))
    shots=[]
    for a,b in zip(bounds,bounds[1:]):
        xs=[s['x'] for s in samples if a<=s['t']<b and s['x'] is not None]
        x=float(np.median(xs)) if xs else edit.get('fallback_x',.5)
        shots.append({'t':a,'end':b,'x':x})
    # GPU resize before the cheap proof crop, retaining full 4K assembly for later.
    cropw=edit.get('crop_size',2160)//2
    coords=[(s['t'],round(max(0,min(1920-cropw,s['x']*1920-cropw/2))/2)*2) for s in shots]
    expr=str(coords[-1][1])
    for (_,left),(end,_) in reversed(list(zip(coords[:-1],coords[1:]))):
        expr=f'if(lt(t,{end:.9f}),{left},{expr})'
    graph=(f"[0:v]scale_cuda=1920:1080:format=yuv420p,hwdownload,format=yuv420p,"
       f"crop={cropw}:{cropw}:'{expr}':(ih-oh)/2,scale=980:980,format=rgb24[p];"
       '[p][1:v]alphamerge=shortest=1[fg];'
       f'color=c=black:s=1080x1920:r={media.rate}:d={frames/fps:.9f}[bg];'
       f'[bg][fg]overlay=50:470:shortest=1,format=yuv420p,trim=end_frame={frames}[out]')
    run([FFMPEG,'-v','error','-y','-readrate','2','-hwaccel','cuda',
       '-hwaccel_output_format','cuda','-i',str(assembly),
       '-loop','1','-framerate',media.rate,'-i',str(mask),'-filter_complex',graph,
       '-map','[out]','-map','0:a:0','-c:v','h264_nvenc','-preset','p4','-b:v','6M',
       '-fps_mode','cfr','-r',media.rate,'-c:a','copy','-map_metadata','-1',
       '-movflags','+faststart',str(proof)])
    assert audio_packets(assembly)==audio_packets(proof),'Dialogue mux payload/timestamps differ'
    verified=decode(proof,frames)
    audio_decode=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(proof),
       '-map','0:a:0','-vn','-f','null','-']),capture_output=True,text=True,check=True)
    assert not audio_decode.stderr.strip(),'Audio decoding reported errors'
    actual=probe(proof)
    assert actual.width==1080 and actual.height==1920 and actual.rate==media.rate
    run([FFMPEG,'-v','error','-y','-hwaccel','cuda','-i',str(proof),
       '-vf',f'fps=1,scale=180:320,tile=8x{math.ceil(frames/fps/8)}:padding=2:margin=2',
       '-frames:v','1',str(P/'qa'/(identifier+'-rough-sheet.jpg'))])
    aligned=json.loads((P/'sources'/(identifier+'-words.json')).read_text(encoding='utf-8'))
    words=[]
    for a,b,off in spans:
        for segment in aligned['segments']:
            for word in segment['words']:
                if a<=(word['s']+word['e'])/2<b:
                    words.append({**word,'s':max(off,word['s']-a+off),
                       'e':min(off+b-a,word['e']-a+off)})
    record={**edit,'source':str(source),'assembly':str(assembly),'proof':str(proof),
       'pieces':pieces,'spans':spans,'frames':frames,'fps':fps,'rate':media.rate,
       'duration':frames/fps,'picture_frame':{'x':50,'y':470,'width':980,'height':980,'radius':48},
       'shots':shots,'face_samples':samples,'words':words,
       'technical':{'full_cuda_decode':verified,'full_audio_decode':True,'audio_packet_identity_to_clean_assembly':True,
         'audio_treatment':'Original English source dialogue; single AAC encode for exact cuts, 15ms edge fades. No music, SFX, narration, speed change or levelling.'},
       'editorial_status':'Pending owner full listening/flow review; transcript and sampled frames do not establish audiovisual acceptance.'}
    receipt.write_text(json.dumps(record,indent=2),encoding='utf-8')
    records.append({k:record[k] for k in ('id','title','proof','duration','frames','fps','rate')})
    (P/'proofs.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    print('PROOF',identifier,frames,frames/fps,' '.join(w['w'] for w in words),flush=True)
