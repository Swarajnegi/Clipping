"""Align the higher-quality passages, render selected edits, and prepare QA."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard, wait_headroom
from build import picture_signature, matching_pictures


def decode(path, duration=30):
    import numpy as np
    out = subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', str(path),
                         '-t', str(duration), '-vn', '-ac', '1', '-ar', '8000', '-f', 'f32le', '-']),
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32)


def stage(name):
    import numpy as np
    previous = ROOT / 'work' / ('referencepilot_20261101_' + name)
    target = ROOT / 'work' / ('referenceclips_20261101_' + name)
    if target.exists():
        raise RuntimeError('Production work folder already exists; inspect before rerunning')
    high = HERE / 'production-source-hq' / (name + '.json')
    source_receipt = high if high.exists() else HERE / 'production-source' / (name + '.json')
    metadata = json.loads(source_receipt.read_text())
    if metadata['height'] < 720:
        metadata['quality_limit'] = '720p-or-higher extraction unavailable on this host; original 640x360 source retained without AI enhancement'
    old = json.loads((previous / 'source.json').read_text())
    left, right = decode(Path(old['path'])), decode(Path(metadata['path']))
    fft_size = 1 << (len(left) + len(right) - 2).bit_length()
    circular = np.fft.irfft(np.fft.rfft(left,fft_size)*np.conj(np.fft.rfft(right,fft_size)),fft_size)
    cross = np.concatenate((circular[-(len(right)-1):],circular[:len(left)]))
    lag = int(np.argmax(cross) - (len(right)-1))
    if abs(lag) > 800:
        raise RuntimeError(f'Source clock requires a manual check: {lag/8000:.3f}s')
    if lag >= 0:
        a, b = left[lag:], right[:len(left)-lag]
    else:
        a, b = left[:len(right)+lag], right[-lag:]
    count = min(len(a), len(b))
    confidence = float(np.corrcoef(a[:count], b[:count])[0, 1])
    if confidence < 0.95:
        raise RuntimeError(f'Source alignment insufficient: {confidence}')
    # right/production sample begins lag/8000 later than the discovery clock.
    shift = -lag / 8000
    transcript = json.loads((previous / 'transcript.json').read_text())
    for row in transcript:
        row['start'] += shift
        row['end'] += shift
        words = row['words']
        for index, word in enumerate(words):
            word['s'] += shift
            word['e'] += shift
            if name == 'self_check' and word['w'].strip() == '20' and index + 1 < len(words) and words[index+1]['w'].strip() == ',000':
                word['w'] = ' 20,000'
                word['e'] = words[index+1]['e'] + shift
                words[index+1]['omit_number_fragment'] = True
        row['words'] = [w for w in words if not w.get('omit_number_fragment')]
    target.mkdir(parents=True)
    metadata.update(id=target.name, title='Who checks your thinking?' if name == 'self_check' else 'What do you have to prove?',
                    source_kind='bounded original production passage', url=None,
                    alignment={'lag_seconds':lag/8000,'correlation':confidence,'transcript_shift':shift})
    (target/'source.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    (target/'transcript.json').write_text(json.dumps(transcript, indent=2), encoding='utf-8')
    spec = json.loads((previous/'music-free-draft.json').read_text())
    spec.update(id=target.name, pairedExports=True, review_status='Owner requested production, 2026-11-01',
                brand={'music':{'file':str(ROOT/'music/original-minor-bed-v1.wav'),'db':-19 if name=='self_check' else -17,'fadeOutSec':1.2}})
    clip = spec['clips'][0]
    clip.pop('music', None)
    clip.update(sourceAudioDb=-3, shots=[{'t':0,'x':0.5,'w':1,'lock':True}],
                description=metadata['title'] + ' — Andrew Tate in conversation with Rob Moore.',
                why='Original-speaker opening; reference-led selective emphasis; no added narration.')
    if name == 'self_check':
        # Remove the hesitant sentence; preserve the complete surrounding statements.
        ranges=[(45.03,53.20),(56.85,69.19)]
        emphasis=[{'t':5.72,'dur':1.85,'text':'CHECK MY\nTHINKING','x':565,'y':990,'size':65},
                  {'t':14.50,'dur':0.85,'text':'I WAS WRONG.','x':565,'y':1000,'size':58},
                  {'t':19.53,'dur':0.88,'text':'MORE CAREFULLY','x':555,'y':1010,'size':52,'italic':True}]
    else:
        # Keep the question and its answer together; remove the redundant clause
        # whose ASR is unreliable, at complete phrase boundaries.
        ranges=[(4.08,5.65),(6.22,17.52),(19.38,28.64)]
        emphasis=[{'t':0,'dur':1.5,'text':'SOMETHING\nTO PROVE?','x':555,'y':975,'size':65},
                  {'t':13.4,'dur':1.1,'text':'PROVE YOURSELF','x':555,'y':1005,'size':58},
                  {'t':20.57,'dur':1.2,'text':'THE LAZY.','x':570,'y':1000,'size':70}]
    clip['segments']=[[round(a+shift,5),round(b+shift,5)] for a,b in ranges]
    clip.pop('start',None)
    clip.pop('end',None)
    clip['title']=metadata['title']
    clip['referenceEdit']['emphasis']=emphasis
    clip['referenceEdit']['captionY']=1090
    clip['referenceEdit']['captionSize']=34
    (target/'clips.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    print('STAGED',name,metadata['width'],metadata['height'],metadata['alignment'],flush=True)
    return target


def qa(target):
    import numpy as np
    from PIL import Image, ImageDraw
    source=ROOT/'out'/target.name
    clean,mixed=source/'clip_01_music-free.mp4',source/'clip_01.mp4'
    for path in (clean,mixed):
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(path),'-f','null','-']),capture_output=True,check=True)
    signatures=[picture_signature(p) for p in (clean,mixed)]
    if not matching_pictures(*signatures):
        raise RuntimeError('Pair picture check failed')
    wave=[decode(p,90) for p in (clean,mixed)]
    count=min(map(len,wave))
    peaks=[float(np.max(np.abs(x))) for x in wave]
    correlation=float(np.corrcoef(wave[0][:count],wave[1][:count])[0,1])
    if max(peaks)>=1 or correlation<0.9:
        raise RuntimeError(f'Audio QA failed: {peaks} / {correlation}')
    folder=HERE/'production-qa'/target.name
    folder.mkdir(parents=True,exist_ok=True)
    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-i',str(mixed),'-vf','fps=2,scale=540:960',str(folder/'%04d.jpg')]),check=True)
    files=sorted(folder.glob('[0-9][0-9][0-9][0-9].jpg'))
    for page,begin in enumerate(range(0,len(files),12),1):
        group=files[begin:begin+12]
        sheet=Image.new('RGB',(1620,330*((len(group)+2)//3)),'#151515')
        draw=ImageDraw.Draw(sheet)
        for i,file in enumerate(group):
            x,y=i%3*540,i//3*330
            with Image.open(file) as im:
                sheet.paste(im.crop((0,328,540,632)),(x,y+23))
            draw.text((x+6,y+5),f'{(begin+i)*0.5+0.25:.2f}s',fill='white')
        sheet.save(folder/f'content-sheet-{page:02d}.jpg')
    receipt={'complete_decode':True,'picture_match':True,'picture':signatures[0],
             'audio_peaks':peaks,'audio_correlation':correlation,
             'source':json.loads((target/'source.json').read_text()),
             'coverage':'All 0.5-second frames prepared for inspection; continuous listening not claimed'}
    (folder/'qa.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('QA',target.name,json.dumps(receipt),flush=True)


def main():
    require_guard(gpu=True)
    for index,name in enumerate(('self_check','prove_yourself')):
        if index:
            wait_headroom(gpu=True)
        target=stage(name)
        subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(target/'clips.json')],cwd=ROOT,check=True)
        qa(target)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
