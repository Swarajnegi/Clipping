"""Check clean dialogue against the assembled source and prepare caption/transition QA."""
import json
import hashlib
import math
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,NODE,ffmpeg_command,probe,require_guard
from build import picture_signature

def audio(path):
    import numpy as np
    raw=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','f32le','-']),capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype=np.float32)

def inspect(vid):
    require_guard()
    import numpy as np
    from PIL import Image,ImageDraw
    work=ROOT/'work'/vid
    final=ROOT/'out'/vid/'clip_01.mp4'
    snippet=ROOT/'public/clips'/vid/'clip_01.mp4'
    props=json.loads((work/'props/clip_01.json').read_text())
    spec=json.loads((work/'clips.json').read_text())
    clip=spec['clips'][0]
    if spec.get('pairedExports') or props.get('music') is not None or clip.get('music') is not None:
        raise RuntimeError('Music-free-only contract violated')
    media=probe(final)
    expected_frames=max(1,math.floor(props['durationSec']*props['fps']+0.5))
    picture=picture_signature(final)
    if int(picture['nb_read_packets'])!=expected_frames or (media.width,media.height)!=(1080,1920) or abs(media.fps-25)>0.001:
        raise RuntimeError('Picture contract failed')
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(final),'-f','null','-']),capture_output=True,check=True)
    source,rendered=audio(snippet),audio(final)
    size=1<<(len(source)+len(rendered)-2).bit_length()
    circular=np.fft.irfft(np.fft.rfft(source,size)*np.conj(np.fft.rfft(rendered,size)),size)
    cross=np.concatenate((circular[-(len(rendered)-1):],circular[:len(source)]))
    lag=int(np.argmax(cross)-(len(rendered)-1))
    if abs(lag)>800:raise RuntimeError('Audio alignment needs review')
    if lag>=0:a,b=source[lag:],rendered[:len(source)-lag]
    else:a,b=source[:len(rendered)+lag],rendered[-lag:]
    length=min(len(a),len(b))
    a,b=a[:length],b[:length]
    correlation=float(np.corrcoef(a,b)[0,1])
    gain=float(np.sqrt(np.mean(b*b)/np.mean(a*a)))
    stereo_bytes=subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(final),'-vn','-ac','2','-ar','48000','-f','f32le','-']),capture_output=True,check=True).stdout
    peak=float(np.max(np.abs(np.frombuffer(stereo_bytes,dtype=np.float32))))
    analysis_downmix_peak=float(np.max(np.abs(rendered)))
    expected_gain=10**(float(clip['sourceAudioDb'])/20)
    if correlation<0.97 or not expected_gain*0.90<gain<expected_gain*1.10 or peak>=1:
        raise RuntimeError(f'Dialogue/gain check failed: correlation={correlation}, gain={gain}, peak={peak}')
    measure=subprocess.run(ffmpeg_command([FFMPEG,'-v','info','-i',str(final),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-']),capture_output=True,text=True,check=True)
    tail=measure.stderr[measure.stderr.rfind('{'):]
    loudness=json.JSONDecoder().raw_decode(tail)[0]
    if not -26<float(loudness['input_i'])<-10:raise RuntimeError('Dialogue loudness needs review')
    if float(loudness['input_tp'])>-1.0:raise RuntimeError('Stereo true peak needs headroom')
    code="const fs=require('fs');const {createTikTokStyleCaptions}=require('@remotion/captions');const captions=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(createTikTokStyleCaptions({captions,combineTokensWithinMilliseconds:850,breakOnSilenceAfterMilliseconds:350}).pages.map(p=>({start:p.startMs/1000,end:(p.startMs+p.durationMs)/1000,text:p.text}))));"
    result=subprocess.run([str(NODE),'-e',code],input=json.dumps(props['captions']),text=True,capture_output=True,cwd=ROOT,check=True)
    pages=json.loads(result.stdout)
    frames={0,expected_frames-1}
    def add(t):frames.add(min(expected_frames-1,max(0,round(t*25))))
    for page in pages:
        add((page['start']+page['end'])/2)
        add(max(page['start'],page['end']-0.04))
    for cue in clip['referenceEdit'].get('emphasis',[]):
        for t in (cue['t']+0.08,cue['t']+cue['dur']/2,cue['t']+cue['dur']+0.04):add(t)
    for layer in clip['referenceEdit'].get('layers',[]):
        add(layer['t']+0.12)
        add(layer['t']+layer['dur']-0.10)
        for t in layer.get('wordTimes',[]):add(t+0.08)
    elapsed=0
    for start,end in clip['segments'][:-1]:
        elapsed+=end-start
        for t in (elapsed-0.04,elapsed,elapsed+0.04):add(t)
    folder=HERE/'qa'/vid
    folder.mkdir(parents=True,exist_ok=True)
    ordered=sorted(frames)
    for frame in ordered:
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',f'{frame/25:.5f}','-i',str(final),'-frames:v','1','-vf','scale=540:960',str(folder/f'frame-{frame:05d}.jpg')]),check=True)
    for number,start in enumerate(range(0,len(ordered),12),1):
        group=ordered[start:start+12]
        sheet=Image.new('RGB',(1620,340*((len(group)+2)//3)),'#151515')
        draw=ImageDraw.Draw(sheet)
        for index,frame in enumerate(group):
            x,y=index%3*540,index//3*340
            with Image.open(folder/f'frame-{frame:05d}.jpg') as im:sheet.paste(im.crop((0,325,540,635)),(x,y+24))
            draw.text((x+5,y+5),f'{frame/25:.2f}s / frame {frame}',fill='white')
        sheet.save(folder/f'caption-sheet-{number:02d}.jpg')
    source_metadata=json.loads((work/'source.json').read_text())
    receipt={'complete_decode':True,'music_added':False,'speech_retained_correlation':correlation,
             'source_gain_linear':gain,'source_gain_db':clip['sourceAudioDb'],'audio_alignment_seconds':lag/8000,
             'audio_peak_linear':peak,'loudness':loudness,'picture':picture,
             'mono_analysis_peak_linear':analysis_downmix_peak,
             'source_resolution':[source_metadata['width'],source_metadata['height']],'output_resolution':[1080,1920],'fps':25,
             'branding':source_metadata.get('branding'),'source_crop':source_metadata.get('source_crop'),
             'caption_pages':pages,'visual_review_frames':ordered,'assistant_inspected':False,
             'continuous_playback_listening':False,'source_embedded_music':'No provider assessment obtained; original dialogue retained; no music added'}
    receipt['caption_style']={'palette':clip['referenceEdit'].get('palette'),'layer_count':len(clip['referenceEdit'].get('layers',[])),
                             'word_synchronous_reveal':clip['referenceEdit'].get('wordReveal',False)}
    receipt['spec_sha256']=hashlib.sha256((work/'clips.json').read_bytes()).hexdigest()
    with final.open('rb') as stream:receipt['output_sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
    (folder/'qa.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('QA_OK',vid,json.dumps({k:receipt[k] for k in ('speech_retained_correlation','source_gain_linear','audio_peak_linear','picture')}),flush=True)
    return receipt
