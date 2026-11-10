"""LAYER: Engineer. THE BIG PICTURE: verify motion editing on owned diagnostic media.
THE FLOW: synthetic CFR fixtures -> prepared projects -> renders -> continuity/audio checks.
This never edits reference footage or publishes a channel video.
"""
from __future__ import annotations
import json
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import numpy as np
from PIL import Image, ImageDraw
from common import FFMPEG, ROOT, ffmpeg_command, require_guard, wait_headroom
import motion_edit as motion


def frame(path: Path, index: int, size: tuple[int, int] = (1080, 1920)) -> Image.Image:
    from io import BytesIO
    command = ffmpeg_command([FFMPEG, '-v', 'error', '-hwaccel', 'cuda', '-i', str(path),
        '-vf', f"select='eq(n,{index})',scale={size[0]}:{size[1]}:flags=bilinear", '-fps_mode', 'vfr',
        '-frames:v', '1', '-f', 'image2pipe', '-c:v', 'png', '-'])
    data = subprocess.run(command, capture_output=True, check=True).stdout
    return Image.open(BytesIO(data)).convert('RGB')


def source_codes(path: Path) -> np.ndarray:
    """Read one RGB colour code per solid fixture frame, not a colour-fidelity test."""
    command = ffmpeg_command([FFMPEG, '-v', 'error', '-hwaccel', 'cuda', '-i', str(path),
        '-vf', 'scale=2:2:flags=bilinear', '-fps_mode', 'passthrough',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    data = subprocess.run(command, capture_output=True, check=True).stdout
    return np.frombuffer(data, np.uint8).reshape(-1, 2, 2, 3).mean(axis=(1,2))


def main() -> None:
    require_guard(gpu=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-root',type=Path,help='Recheck existing owned diagnostic renders without rerendering picture')
    args=parser.parse_args()
    root = motion.under_d(args.resume_root) if args.resume_root else ROOT / '.runtime/tmp' / ('motion-edit-smoke-' + uuid4().hex[:10])
    root.mkdir(parents=True,exist_ok=bool(args.resume_root))
    (root / 'asset.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
      <ellipse cx="300" cy="483" rx="180" ry="30" fill="#101114" opacity=".10"/>
      <path d="M130 190L300 100L470 190V395L300 485L130 395Z" fill="#27382a"/>
      <path d="M130 190L300 280L470 190L300 100Z" fill="#c8f45d"/>
      <path d="M300 280L470 190V395L300 485Z" fill="#608038"/>
      <path d="M185 195L300 135L415 195L300 255Z" fill="#eef7d8"/>
      <path d="M205 325L265 356M205 365L265 397M335 355L395 323M335 395L395 363" stroke="#dbeab9" stroke-width="12"/>
      </svg>''', encoding='utf-8')
    reports = []
    for label, rate, fps, count in [('25', '25/1', 25, 85), ('2997', '30000/1001', 30000/1001, 102)]:
        if not args.resume_root:wait_headroom(gpu=True)
        source = root / f'synthetic-{label}.mp4'
        colour = f"color=s=540x960:r={rate},format=gbrp,geq=r='40+mod(N*53,170)':g='45+mod(N*97,160)':b='50+mod(N*151,150)'"
        if not args.resume_root:
            subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', colour,
                '-f', 'lavfi', '-i', 'sine=frequency=523:sample_rate=48000', '-frames:v', str(count),
                '-t', str(count/fps), '-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', '4M',
                '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', str(source)]), check=True)
            project = motion.prepare(str(source), f'validation_{label}_{uuid4().hex[:8]}', True)
        else:
            matches=[p for p in (motion.HOME/'Working').glob(f'validation_{label}_*/project.json')
                if motion.read(p).get('assets',{}).get('chip',{}).get('path')==str(root/'asset.svg')]
            assert len(matches)==1,matches
            project=matches[0]
        spec = motion.read(project)
        assert spec['source']['frames'] == count
        assert abs(spec['source']['fps']-fps) < 1e-8
        def caption(text, at, duration, word_times):
            return {'t': at, 'dur': duration, 'text': text, 'wordTimes': word_times,
                    'x': 90, 'y': 1400, 'width': 900, 'size': 72, 'align': 'center',
                    'font': 'inter', 'weight': 700, 'shadow': 'strong',
                    'motion': {'inSec': .12, 'outSec': .04, 'rise': 7, 'blur': 2}}
        spec.update(synthetic=True, sourceMusic=False, reuseBasis='Original diagnostic colour frames and generated test tone; no real speaker',
            assets={'chip': {'path': str(root/'asset.svg'), 'reuseBasis': 'Original programmatic test illustration'}},
            captionLayers=[caption('Keep your voice.',0,.6,[0,.15,.3]),
                           caption('One idea at a time.',2.4,.6,[2.4,2.5,2.6,2.7,2.8]),
                           caption('Keep the meaning.',3,spec['source']['duration']-3,[3,3.1,3.2])],
            scenes=[{'kind':'speaker','start':0,'end':.6},
                    {'kind':'emphasis','start':.6,'end':1.2,'eyebrow':'A SYNTHETIC CHECK','title':'MAKE IT','subtitle':'understandable'},
                    {'kind':'illustration','start':1.2,'end':1.8,'eyebrow':'ONE CLEAR IDEA','title':'Bring it to life','asset':'chip','subtitle':'with a purpose'},
                    {'kind':'comparison','start':1.8,'end':2.4,'title':'Choose the meaning',
                     'left':{'title':'Noise','detail':'Decorative movement'},'right':{'title':'Clarity','detail':'Graphics that explain'}},
                    {'kind':'badges','start':2.4,'end':3,'badges':[
                        {'text':'Plan','at':2.4,'x':85,'y':930,'width':280},
                        {'text':'Animate','at':2.56,'x':650,'y':1070,'width':340},
                        {'text':'Review','at':2.72,'x':85,'y':1210,'width':310}]},
                    {'kind':'speaker','start':3,'end':spec['source']['duration']}])
        motion.save(project, spec)
        motion.validate(spec, require_ready=True)
        if not args.resume_root:wait_headroom(gpu=True)
        if args.resume_root:
            existing=motion.read(project.parent/'last-render.json')
            assert existing['project_sha256']==motion.digest(project)
            assert existing['source_sha256']==motion.digest(Path(spec['source']['path']))
            output=Path(existing['file'])
            assert existing['sha256']==motion.digest(output)
            motion.decode(output,count)
            assert motion.audio_packets(output)==motion.audio_packets(Path(spec['source']['path']))
        else:
            output = motion.render(project, scale=1)
        receipt = motion.read(project.parent/'last-render.json')
        assert receipt['audio']['mode']=='source stream copy'
        assert receipt['audio']['packets_identical'] and receipt['audio']['timing_identical']
        assert receipt['frames']==count
        signature=motion.picture_signature(output)
        motion.validate_picture_clock(signature,count,fps)
        continuity=[]
        codes=source_codes(Path(spec['source']['path']))
        assert len(codes)==count
        for moment in [.4,3.28]:
            index=round(moment*fps)
            a=np.asarray(frame(output,index)).astype(np.int16)
            b=np.asarray(frame(Path(spec['source']['path']),index)).astype(np.int16)
            wrong=np.asarray(frame(Path(spec['source']['path']),index-1)).astype(np.int16)
            roi=np.s_[240:1200,120:960,:]
            expected=float(np.mean(np.abs(a[roi]-b[roi])))
            previous=float(np.mean(np.abs(a[roi]-wrong[roi])))
            # Browser/FFmpeg colour conversion is lossy. Identify the source frame
            # against EVERY diagnostic colour, rather than imposing a colour-error
            # threshold unrelated to playback continuity. A shifted/restarted frame
            # must lose. Record the actual nearest/runner-up distances; an arbitrary
            # RGB error ratio measures this fixture's colour spacing, not timing.
            distances=np.mean(np.abs(codes-a[roi].mean(axis=(0,1))),axis=1)
            ranked=np.argsort(distances)
            assert ranked[0]==index and distances[ranked[1]]>distances[index],(label,index,ranked[:2],distances[ranked[:2]])
            assert np.argmin(np.mean(np.abs(codes-codes[index-1]),axis=1))!=index
            continuity.append({'frame':index,'correct_source_mae':expected,'previous_source_mae':previous,
                'nearest_source_frame':int(ranked[0]),'runner_up_frame':int(ranked[1]),
                'runner_up_mae':float(distances[ranked[1]]),'tested_against_frames':count})
        times=[.4,.92,1.5,2.1,2.82,3.28]
        sheet=Image.new('RGB',(1080,1328),'#151515');draw=ImageDraw.Draw(sheet)
        for i,t in enumerate(times):
            im=frame(output,round(t*fps));im.save(root/f'{label}-{i}.png')
            x=(i%3)*360;y=(i//3)*664
            sheet.paste(im.resize((360,640)),(x,y+24));draw.text((x+8,y+5),f'{t:.2f}s',fill='white')
        sheet.save(root/f'{label}-treatments.jpg',quality=95)
        if label=='25':
            existing_stills=[p for p in project.parent.glob('qa/*/frame-000038.png')
                if motion.digest(p.parent/'project.json')==motion.digest(project)] if args.resume_root else []
            if len(existing_stills)>=2:still_a,still_b=existing_stills[:2]
            else:
                wait_headroom(gpu=True)
                still_a=motion.render(project,still=1.5,scale=2)
                still_b=motion.render(project,still=1.5,scale=2)
            with Image.open(still_a) as a, Image.open(still_b) as b:
                assert a.size==(2160,3840) and np.array_equal(np.asarray(a),np.asarray(b))
            shutil.copy2(still_a,root/'native-4k.png')
            # Exercise native-frame preview ranges and prevent their promotion.
            if args.resume_root and (project.parent/'last-preview.json').is_file():
                pr=motion.read(project.parent/'last-preview.json');preview=Path(pr['file'])
                assert pr['range']==[15,29] and pr['sha256']==motion.digest(preview)
                motion.decode(preview,15)
            else:preview=motion.render(project,preview='0.6:1.2',scale=1)
            assert motion.read(project.parent/'last-preview.json')['preview']
            assert motion.read(project.parent/'last-render.json')['sha256']==receipt['sha256']
            try:motion.deliver(project)
            except ValueError:pass
            else:raise AssertionError('Preview/synthetic export was not blocked')
            preview_note={'file':str(preview),'repeat_stills':[str(still_a),str(still_b)],'repeat_pixels_identical':True}
        else:preview_note=None
        reports.append({'rate':rate,'frames':count,'duration':float(signature['duration']),'start_time':float(signature.get('start_time',0)),
            'project':str(project),'video':str(output),
            'audio':receipt['audio'],'continuity':continuity,'preview':preview_note,
            'coverage':'All frames decoded; correct source frames sampled before/after graphic inserts. Known test-tone packets compared; no real-speaker listening claim.'})
    result={'status':'technical smoke passed','root':str(root),'cases':reports,
            'synthetic_only':True,'real_footage_edited':False,'exported_channel_videos':False}
    motion.save(root/'receipt.json',result)
    print('MOTION_EDIT_SMOKE_COMPLETE '+json.dumps(result),flush=True)


if __name__=='__main__':main()
