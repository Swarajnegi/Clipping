"""Assemble authored source cuts, original SFX, proof crops and reusable render props."""
import json
import math
import shutil
import subprocess
import sys
import wave
import hashlib
from pathlib import Path
import numpy as np
import cv2

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command, probe
from build import assemble
from prep import scene_cuts
from motion_edit import audio_packets

require_guard(gpu=True)
cv2.setNumThreads(2)
edits = json.loads((P / 'edits.json').read_text(encoding='utf-8'))
for folder in ('drafts', 'qa', 'props', 'assets'):
    (P / folder).mkdir(exist_ok=True)

# Original, deterministic mechanical transient. No sampled recording or music.
sr = 48000
rng = np.random.default_rng(20261108)
t = np.arange(round(.13 * sr)) / sr
noise = rng.standard_normal(len(t))
click = .4 * noise * np.exp(-t * 160)
click += .18 * np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 120)
for onset, strength in ((.028, .28), (.049, .13)):
    local = np.maximum(0, t - onset)
    click += strength * rng.standard_normal(len(t)) * np.exp(-local * 200) * (t >= onset)
click /= max(1, np.max(np.abs(click)))
sfx = P / 'assets/original-camera-click.wav'
with wave.open(str(sfx), 'wb') as wav:
    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr)
    wav.writeframes((click * 32767).astype('<i2').tobytes())
(P / 'assets/provenance.json').write_text(json.dumps({'file': str(sfx),
    'basis': 'Original programmatic noise/oscillator synthesis; fixed seed 20261108; no external sample',
    'sha256': hashlib.sha256(sfx.read_bytes()).hexdigest()}, indent=2), encoding='utf-8')

records = []
for edit in edits:
    id = edit['id']
    source = P / 'sources' / (id + '.mp4')
    media = probe(source)
    pieces = [(round(a * media.fps) / media.fps, round(b * media.fps) / media.fps) for a, b in edit['pieces']]
    clean = P / 'drafts' / (id + '-assembly.mp4')
    public = ROOT / 'public/clips' / ('thought_palace_20261108_' + id[:2])
    public.mkdir(parents=True, exist_ok=True)
    master = public / 'master.mp4'
    if clean.exists() and master.exists():
        spans = []
        offset = 0
        for a, b in pieces:
            spans.append((a, b, offset)); offset += b-a
        assert probe(master).width == media.width and probe(master).rate == media.rate
    elif clean.exists() or master.exists():
        raise FileExistsError('Incomplete assembly requires explicit inspection: ' + id)
    else:
        spans = assemble(source, pieces, clean, media.rate)
    # One final dialogue encode for leveling and the deliberately quiet original click.
    args = [FFMPEG, '-v', 'error', '-y', '-i', str(clean)]
    if edit.get('click'):
        args += ['-i', str(sfx), '-filter_complex',
            '[0:a]loudnorm=I=-16:TP=-2:LRA=9,aresample=48000[a];'
            '[1:a]volume=0.08,adelay=40[s];[a][s]amix=inputs=2:duration=first:normalize=0,'
            'alimiter=limit=0.891:level=0:latency=1[out]', '-map', '0:v:0', '-map', '[out]']
    else:
        args += ['-map', '0:v:0', '-map', '0:a:0', '-af', 'loudnorm=I=-16:TP=-2:LRA=9,aresample=48000']
    args += ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-map_metadata', '-1', '-movflags', '+faststart', str(master)]
    if not master.exists():
        subprocess.run(ffmpeg_command(args), check=True)
    assembled = probe(master)
    frame_count = round(sum(b-a for a,b in pieces) * media.fps)
    picture_duration = frame_count / media.fps
    cuts = scene_cuts(assembled)
    bounds = sorted(set([0, *cuts, *[off for a, b, off in spans], assembled.duration]))
    # Small GPU-decoded samples support shot-aware crop choices and caption exclusion.
    tw = 640
    th = round(tw * assembled.height / assembled.width / 2) * 2
    det = cv2.FaceDetectorYN.create(str(ROOT / 'models/face_detection_yunet_2023mar.onnx'), '', (tw, th), score_threshold=.75)
    command = ffmpeg_command([FFMPEG, '-v', 'error', '-hwaccel', 'cuda', '-i', str(master), '-an',
        '-vf', f'fps=5,scale={tw}:{th}', '-pix_fmt', 'bgr24', '-f', 'rawvideo', '-'])
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    samples = []
    index = 0
    while True:
        buf = process.stdout.read(tw * th * 3)
        if len(buf) != tw * th * 3: break
        frame = np.frombuffer(buf, np.uint8).reshape(th, tw, 3)
        _, faces = det.detect(frame)
        hits = [] if faces is None else [f[:4].tolist() for f in faces if f[1] + f[3] / 2 < th * .82]
        samples.append({'t': index / 5, 'faces': hits})
        index += 1
    assert process.wait() == 0
    shots = []
    for a, b in zip(bounds, bounds[1:]):
        faces = []
        for sample in samples:
            if not (a <= sample['t'] < b) or not sample['faces']: continue
            boxes = sorted(sample['faces'], key=lambda f: f[2] * f[3], reverse=True)
            if len(boxes) > 1 and boxes[1][2] * boxes[1][3] > boxes[0][2] * boxes[0][3] * .6:
                box = sorted(boxes[:2], key=lambda f: f[0])[edit.get('wide_speaker', 0)]
            else: box = boxes[0]
            faces.append(box)
        x = float(np.median([(f[0] + f[2] / 2) / tw for f in faces])) if faces else edit.get('fallback_x', .5)
        shots.append({'t': a, 'x': x, 'lock': True})
    # Rebase actual word times onto the authored order; never generate new speech.
    transcript = json.loads((P / 'sources' / (id + '-words.json')).read_text(encoding='utf-8'))
    words = [w for s in transcript['segments'] for w in s['words']]
    output_words = []
    for a, b, off in spans:
        for w in words:
            if a <= (w['s'] + w['e']) / 2 < b:
                output_words.append({**w, 's': max(off, w['s'] - a + off), 'e': min(off + b - a, w['e'] - a + off)})
    props = dict(src=f'clips/{public.name}/master.mp4', bgSrc=None, fps=media.fps,
        durationSec=picture_duration, srcWidth=assembled.width, srcHeight=assembled.height,
        widthFrac=1, shots=shots, track=[], yAnchor=.5, hook='', hookPersist=False,
        hookDurationSec=0, captions=[], punchIns=[{'t':0, 'dur':1.7, 'scale':1.025}],
        watermark=None, loopFadeSec=0, style='bold', grade={'brightness':1, 'contrast':1.03, 'saturate':1},
        accent='#ffffff', intro=None, music=None, referenceEdit={'profile':'restrained',
        'frame':{'x':50,'y':470,'width':980,'height':980,'radius':48}})
    (P / 'props' / (id + '-base.json')).write_text(json.dumps(props, indent=2), encoding='utf-8')
    # Cheap full-duration proof uses the exact source assembly/audio and square crop.
    cropw = min(assembled.width, assembled.height)
    coords = [(s['t'], max(0, min(assembled.width - cropw, s['x'] * assembled.width - cropw / 2))) for s in shots]
    expression = str(coords[-1][1])
    for (_, left), (end, _) in reversed(list(zip(coords[:-1], coords[1:]))):
        expression = f'if(lt(t,{end:.6f}),{left},{expression})'
    vf = f"crop={cropw}:{cropw}:'{expression}':(ih-oh)/2,scale=654:654,pad=720:1280:33:313:black"
    proof = P / 'drafts' / (id + '-content-proof.mp4')
    if proof.exists():
        proof.rename(proof.with_name(proof.stem + '-truncated-audio-UNUSED.mp4'))
    subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-hwaccel', 'cuda', '-i', str(master),
        '-vf', vf, '-c:v', 'h264_nvenc', '-preset', 'p4', '-b:v', '4M', '-c:a', 'copy',
        '-r', media.rate, '-movflags', '+faststart', str(proof)]), check=True)
    assert audio_packets(master) == audio_packets(proof)
    subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-hwaccel', 'cuda', '-i', str(proof),
        '-vf', f'fps=1,scale=180:320,tile=8x{math.ceil(assembled.duration/8)}:padding=2:margin=2',
        '-frames:v', '1', str(P / 'qa' / (id + '-proof-sheet.jpg'))]), check=True)
    record = {**edit, 'source': str(source), 'master': str(master), 'proof': str(proof), 'spans': spans,
        'words': output_words, 'shots': shots, 'face_samples': samples, 'fps': media.fps,
        'rate':media.rate, 'duration': picture_duration, 'frames': frame_count,
        'review_status':'Full proof listening pending; ASR and sampled frames alone are insufficient.'}
    (P / 'drafts' / (id + '-edit.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    records.append({k:record[k] for k in ('id','proof','duration','fps','frames')})
    print(id, assembled.duration, ' '.join(w['w'] for w in output_words), flush=True)
(P / 'proofs.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
