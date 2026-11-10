"""LAYER: Delivery. THE BIG PICTURE: put validated owner clips in the actual Exports folder.
THE FLOW: technical + recorded visual coverage -> preserved copies -> hashes and posting notes.
"""
import json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from motion_edit import digest
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
decisions=read(P/'edit-decisions.json');visual=read(P/'qa/assistant-review.json')
assert read(P/'qa/final-checks.json')['passed']
assert visual['all_phrase_sheets_inspected'] and visual['issues']==[]
auto=read(P/'qa/automated.json');geometry=read(P/'qa/caption-geometry.json')
assert not geometry['failures'] and not geometry['collisions']
for report in auto:
    for flag in report['caption_face_overlaps']:
        review=visual['detector_flag_review'][report['clip']][str(flag['frame'])]
        assert review['visible_face_overlap'] is False and review['reason'].strip()
        assert Path(review['evidence']).is_file()
folder=ROOT/'Main/shorts-clips/Exports/03 Archive/2026-11-08 - Jordan Peterson - Selection Review';folder.mkdir(parents=True,exist_ok=True)
outputs=[];copy=['# Jordan Peterson × Chris Williamson — posting copy','']
for d in decisions:
    slug=d['slug'];receipt=read(P/'qa'/slug/'render.json');source=Path(receipt['file'])
    assert digest(source)==receipt['sha256'] and receipt['complete_decode']['frames']==d['frames']
    assert receipt['encoder']=='h264_nvenc' and receipt['difference_layers']==d['caption_layers']
    assert visual['render_sha256'][slug]==receipt['sha256']
    destination=folder/source.name
    if destination.exists():raise FileExistsError('Preserve earlier delivery '+str(destination))
    partial=destination.with_suffix('.partial.mp4');assert not partial.exists()
    shutil.copy2(source,partial);assert digest(partial)==receipt['sha256'];partial.rename(destination)
    outputs.append({'file':str(destination),'sha256':receipt['sha256'],'title':d['title'],'duration':d['duration'],
        'frames':d['frames'],'source_url':'https://www.youtube.com/watch?v=WEP5ubPMGDU',
        'source_excerpts':d['segments'],'coverage':visual['coverage'],'technical_receipt':str(P/'qa'/slug/'render.json')})
    copy.extend([f"## {slug} — {d['duration']:.2f}s",'',f"**Title:** {d['title']}",'',d['description'],''])
(folder/'UPLOAD.md').write_text('\n'.join(copy)+'\n',encoding='utf-8')
provenance={'delivered_at':datetime.now(timezone.utc).isoformat(),
    'source_title':'How to Find the Meaning You’ve Been Looking For - Jordan Peterson (4K)',
    'source_uploader':'Chris Williamson','source_url':'https://www.youtube.com/watch?v=WEP5ubPMGDU',
    'reuse_basis':'Owner confirmed this episode covered by clipping permission/campaign authorization, 8 November 2026',
    'source_windows':read(P/'source-inspection.json'),'font_provenance':str(ROOT/'.agents/skills/viral-shorts/assets/fonts/provenance.json'),
    'output':'2160x3840 at native 25 FPS; 3840x1920 landscape originals reframed vertically. New typography rendered at 4K; source detail is not restored by scaling.',
    'added_music':False,'added_narration':False,'added_channel_symbol':False,'caption_rule':'Every authored word/layer uses white Difference blending, including italic accents',
    'outputs':outputs}
(folder/'PROVENANCE.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
note='''# QA coverage

All four videos have full CUDA decode/frame-count checks, actual NVENC confirmation,
native frame-rate/duration checks, measured font bounds, and unchanged assembled-dialogue
AAC payloads/timestamps after picture rendering. Audio assembly uses one documented
AAC encode with short edge fades. No music, narration or channel symbol was added.

The assistant inspected native 4K proofs and every caption composition/camera-cut
sample in the finished files. All decoded frames were tested for face/caption overlap.
Nine raw detector flags were retained and visually resolved: one hand/microphone
false detection, and eight close-up boxes extending below the chin beyond the face.
The painted caption glyphs stay below the visible face. Exact-frame evidence and
adjudications remain in Working; raw automated results have not been overwritten.
Difference settings were checked on all words/layers. Posting copy and source reuse
confirmation are included. Earlier drafts/originals remain in Working.

The optional Gemini second opinion returned HTTP 503 and fell back to local evidence;
there is no successful cloud review or new continuous listening claim. Sound checks
are transcript alignment, audio-packet/timestamp preservation and loudness/peak measurement.
Please preview the full clips with sound on your phone before posting.

Detailed evidence: '''+str(P/'qa')+'\n'
(folder/'QA_COVERAGE.md').write_text(note,encoding='utf-8')
(P/'DELIVERY.json').write_text(json.dumps({'folder':str(folder),'outputs':outputs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'folder':str(folder),'clips':len(outputs),'outputs':outputs},ensure_ascii=False,indent=2))
