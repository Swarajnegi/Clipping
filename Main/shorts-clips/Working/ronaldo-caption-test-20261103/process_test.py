"""Guarded preparation and verification for the 12.92s caption revision."""
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import FFMPEG, FFPROBE, NODE, REMOTION, require_guard, run

PROJECT = Path(__file__).resolve().parent
ID = 'ronaldo_whoop_20261103_caption_v2'
WORK = ROOT / 'work' / ID
ORIGINAL = ROOT / 'Main/shorts-clips/Exports/01 Finished Edits/2026-11-02 - Cristiano Ronaldo/01-everyone-wants-to-be-cristiano-music-free.mp4'

def prepare():
    source = ROOT / 'Main/shorts-clips/Working/ronaldo-whoop-20261102/source/clean-final.mp4'
    dest = ROOT / 'public/clips' / ID / 'clip_01.mp4'
    dest.parent.mkdir(parents=True, exist_ok=True)
    from build import cut
    cut(source, 620.52, 633.44, dest, '25/1')
    frames = PROJECT / 'source-frames'; frames.mkdir(exist_ok=True)
    run([FFMPEG, '-y', '-i', str(dest), '-vf', 'fps=2,scale=740:-1', str(frames/'%03d.jpg')])
    run([FFMPEG, '-y', '-i', str(dest), '-vf', 'fps=2,scale=370:-1,tile=5x6', '-frames:v', '1', str(PROJECT/'source-sheet.jpg')])
    run([FFMPEG, '-y', '-i', str(ORIGINAL), '-vn', '-c:a', 'pcm_s16le', str(PROJECT/'dialogue-review.wav')])

def render(frames):
    assets=PROJECT/'render-public'
    (assets/'clips'/ID).mkdir(parents=True,exist_ok=True)
    (assets/'fonts').mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'public/clips'/ID/'clip_01.mp4',assets/'clips'/ID/'clip_01.mp4')
    shutil.copy2(ROOT/'public/fonts/InterVariable.woff2',assets/'fonts/InterVariable.woff2')
    target = PROJECT / ('preview.mp4' if frames else 'picture.mp4')
    cmd = [str(NODE), str(REMOTION), 'render', 'src/index.ts', 'ViralShort', str(target),
           f'--props={WORK / "props/clip_01.json"}', '--concurrency=1', '--offthreadvideo-video-threads=2',
           '--offthreadvideo-cache-size-in-bytes=134217728', '--hardware-acceleration=required', '--gl=angle',
           f'--public-dir={assets}']
    if frames:
        target = PROJECT/'preview-frames'; target.mkdir(exist_ok=True)
        cmd[5] = str(target.relative_to(ROOT))
        cmd += ['--frames='+frames, '--image-format=png']
    subprocess.run(cmd, cwd=ROOT, check=True)

def signature(path, kind):
    info = subprocess.run([FFPROBE, '-v','error','-select_streams', kind,
        '-show_packets','-show_data_hash','sha256','-show_entries',
        'packet=pts_time,dts_time,duration_time,size,data_hash','-of','json',str(path)],
        capture_output=True,text=True,check=True)
    return json.loads(info.stdout)['packets']

def finish():
    output=PROJECT/'01-everyone-wants-to-be-cristiano-caption-v2-music-free.mp4'
    run([FFMPEG,'-y','-i',str(PROJECT/'picture.mp4'),'-i',str(ORIGINAL),
         '-map','0:v:0','-map','1:a:0','-c','copy','-map_metadata','-1','-movflags','+faststart',str(output)])
    before, after = signature(ORIGINAL,'a:0'), signature(output,'a:0')
    if before != after: raise RuntimeError('Audio packets or timing changed')
    info=json.loads(subprocess.run([FFPROBE,'-v','error','-show_streams','-show_format','-of','json',str(output)],capture_output=True,text=True,check=True).stdout)
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames'])) == (1080,1920,'25/1',323)
    assert abs(float(video['duration'])-12.92)<0.001
    run([FFMPEG,'-v','error','-i',str(output),'-f','null','-'])
    qa=PROJECT/'qa'; qa.mkdir(exist_ok=True)
    run([FFMPEG,'-v','error','-y','-i',str(output),'-vf','scale=270:480,tile=6x5',str(qa/'all-frames-%02d.jpg')])
    run([FFMPEG,'-v','error','-y','-i',str(output),'-vf',
      "select='between(n,207,248)',crop=400:260:620:510,tile=7x6",'-frames:v','1',str(qa/'depth-every-frame.jpg')])
    run([FFMPEG,'-v','error','-y','-i',str(output),'-vf',
      "select='eq(n,24)+eq(n,96)+eq(n,210)+eq(n,238)+eq(n,313)+eq(n,322)',scale=360:640,tile=3x2",
      '-frames:v','1',str(qa/'overview.jpg')])
    props=json.loads((WORK/'props/clip_01.json').read_text())
    import re
    def normal(word): return re.sub(r"[^a-z0-9']",'',word.lower())
    authored=sorted([(normal(word),moment) for layer in props['referenceEdit']['layers']
      for word,moment in zip(layer['text'].split(),layer.get('wordTimes',[layer['t']]))],key=lambda x:x[1])
    expected=[(normal(c['text']),c['startMs']/1000) for c in props['captions']]
    assert [w for w,t in authored]==[w for w,t in expected],(authored,expected)
    assert max(abs(a[1]-b[1]) for a,b in zip(authored,expected))<=1/25
    import cv2
    cv2.setNumThreads(2)
    capture=cv2.VideoCapture(str(ROOT/'public/clips'/ID/'clip_01.mp4'))
    previous=None; cuts=[]; n=0
    while True:
        ok,frame=capture.read()
        if not ok: break
        thumb=cv2.resize(frame,(64,36)).astype('float32')
        difference=0 if previous is None else float(abs(thumb-previous).mean())
        if difference>22: cuts.append({'frame':n,'time':n/25,'difference':difference})
        previous=thumb; n+=1
    capture.release()
    if len(cuts)!=1 or abs(props['shots'][1]['t']-cuts[0]['time'])>0.001:
        raise RuntimeError(f'Crop change does not match the detected source cut: {cuts}')
    receipt={'dimensions':[1080,1920],'frames':323,'fps':'25/1','video_duration':video['duration'],
      'audio_packets_and_timing_identical':True,'audio_packet_count':len(after),
      'original_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
      'revision_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'decode':'passed',
      'authored_words_match_transcript':True,'word_onsets_within_one_frame_of_transcript':True,
      'source_cut_candidates':cuts,'authored_shots':props['shots']}
    (PROJECT/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=['prepare','render','finish','complete']); parser.add_argument('--frames',default='')
    args=parser.parse_args(); require_guard(gpu=True)
    if args.stage=='prepare': prepare()
    elif args.stage=='render': render(args.frames)
    elif args.stage=='finish': finish()
    else:
        render('')
        from common import wait_headroom
        wait_headroom(gpu=True)
        finish()
