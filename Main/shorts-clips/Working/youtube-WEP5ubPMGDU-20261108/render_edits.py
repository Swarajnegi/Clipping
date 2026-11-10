"""LAYER: Engineer. THE BIG PICTURE: render the authored clips with verified source audio.
THE FLOW: staged props -> representative 4K stills/full NVENC picture -> audio copy/decode QA.
"""
import argparse,json,os,shutil,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from common import NODE,REMOTION,FFMPEG,ffmpeg_command,require_guard,wait_headroom,probe
from build import picture_signature,matching_pictures,validate_reference_edit
from motion_edit import digest,audio_packets,decode,validate_picture_clock
require_guard(gpu=True)
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['proof','render']);parser.add_argument('--only',default='')
parser.add_argument('--proof-frame',type=int)
parser.add_argument('--resume-picture',action='store_true',help='Revalidate an existing complete picture/audio mux after a QA-only failure')
args=parser.parse_args();decisions=json.loads((P/'edit-decisions.json').read_text(encoding='utf-8'))
if args.only:decisions=[d for d in decisions if d['slug'].startswith(args.only)]
for d in decisions:
    slug=d['slug'];qa=P/'qa'/slug;qa.mkdir(parents=True,exist_ok=True)
    props_path=ROOT/'work'/d['work_id']/'props/clip_01.json';props=json.loads(props_path.read_text(encoding='utf-8'))
    validate_reference_edit(props['referenceEdit'],props['durationSec'])
    assert all(l['surface']=='difference' and l['blend']=='difference' and l['color']=='#ffffff' and l['fillOpacity']>0 and not l.get('gradient') for l in props['referenceEdit']['layers'])
    assert props['music'] is None and props['intro'] is None and props['watermark'] is None
    public=P/'render-public'/slug
    files=[props['src'],'fonts/InterVariable.woff2','fonts/InterVariable-Italic.woff2','fonts/CormorantGaramond-Italic.ttf','fonts/Inter-LICENSE.txt','fonts/Cormorant-OFL.txt']
    asset_hashes={}
    for rel in files:
        source=ROOT/'public'/rel;target=public/rel;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():os.link(source,target)
        assert digest(source)==digest(target)
        asset_hashes[rel]=digest(target)
    partial_path=P/'drafts'/f'{slug}.partial.mp4'
    if args.resume_picture and partial_path.exists():
        assert json.loads((qa/'props.json').read_text(encoding='utf-8'))==props,'Recovered picture has different authored props'
    shutil.copy2(props_path,qa/'props.json')
    (qa/'asset-hashes.json').write_text(json.dumps(asset_hashes,indent=2),encoding='utf-8')
    common=[f'--props={props_path}',f'--public-dir={public}','--gl=angle','--offthreadvideo-video-threads=2','--offthreadvideo-cache-size-in-bytes=134217728']
    if args.mode=='proof':
        emphasis=next(l for l in props['referenceEdit']['layers'] if l.get('italic'))
        frame=round(min(emphasis['t']+emphasis['dur']-.08,max(emphasis['wordTimes'])+.14)*props['fps'])
        if args.proof_frame is not None:frame=args.proof_frame
        output=qa/('proof-4k.png' if args.proof_frame is None else f'proof-{frame:04d}-4k.png')
        if output.exists():raise FileExistsError('Preserve proof; version the revision')
        subprocess.run([str(NODE),str(REMOTION),'still','src/index.ts','ViralShort',str(output),*common,f'--frame={frame}','--scale=2'],cwd=ROOT,check=True)
        (qa/('proof.json' if args.proof_frame is None else f'proof-{frame:04d}.json')).write_text(json.dumps({'frame':frame,'caption':emphasis['text'] if args.proof_frame is None else 'Targeted camera/placement proof','dimensions':[2160,3840],'props_sha256':digest(props_path)},indent=2))
        continue
    wait_headroom(gpu=True)
    drafts=P/'drafts';drafts.mkdir(exist_ok=True);output=drafts/f'{slug}-music-free.mp4'
    if output.exists():raise FileExistsError('Preserve finished draft; create a new revision before rerendering')
    partial=drafts/f'{slug}.partial.mp4';muxed=drafts/f'{slug}.dialogue.mp4'
    recover=partial.exists() or muxed.exists()
    if recover and not (args.resume_picture and partial.exists() and muxed.exists()):
        raise FileExistsError('Inspect existing incomplete output before continuing')
    log=qa/'render.log';started=time.monotonic()
    print('REVALIDATE_PICTURE' if recover else 'RENDER_START',slug,flush=True)
    if not recover:
        with log.open('w',encoding='utf-8') as stream:
            subprocess.run([str(NODE),str(REMOTION),'render','src/index.ts','ViralShort',str(partial),*common,
                '--muted','--concurrency=1','--hardware-acceleration=required','--scale=2','--video-bitrate=40M','--image-format=png','--log=verbose'],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    assert 'Encoder: h264_nvenc, hardware accelerated: true' in log.read_text(encoding='utf-8')
    before=picture_signature(partial);validate_picture_clock(before,d['frames'],props['fps'])
    source=public/props['src'];packets=audio_packets(source)
    if not recover:
        subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-i',str(partial),'-i',str(source),'-map','0:v:0','-map','1:a:0','-c','copy','-map_metadata','-1','-movflags','+faststart',str(muxed)]),check=True)
    assert matching_pictures(before,picture_signature(muxed))
    assert packets==audio_packets(muxed),'Assembled dialogue packets or timing changed'
    media=probe(muxed);assert (media.width,media.height,media.fps)==(2160,3840,25)
    complete=decode(muxed,d['frames'])
    partial.unlink();muxed.rename(output)
    receipt={'file':str(output),'sha256':digest(output),'duration':d['duration'],'frames':d['frames'],
        'dimensions':[media.width,media.height],'fps':media.fps,'source_master':str(source),'source_master_sha256':digest(source),
        'props_sha256':digest(props_path),'assets':asset_hashes,'encoder':'h264_nvenc','complete_decode':complete,
        'audio':'All assembled-dialogue AAC packet payloads and timestamps unchanged by final mux; assembly is a documented single AAC encode with 15ms edge fades.',
        'added_music':False,'added_narration':False,'added_branding':False,'difference_layers':len(props['referenceEdit']['layers']),
        'caption_words':d['caption_words'],'elapsed_current_stage_seconds':time.monotonic()-started,'picture_recovered_after_metadata_check':recover,'guard_job':os.environ['CLIPPING_GUARD_JOB'],
        'status':'Technical checks passed; editorial final review pending'}
    (qa/'render.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print('RENDER_COMPLETE',slug,json.dumps(receipt),flush=True)
