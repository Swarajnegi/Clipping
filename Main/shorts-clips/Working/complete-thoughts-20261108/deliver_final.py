"""Promote one manually inspected, technically checked video/cover without overwrite."""
import hashlib,json,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];F=P/'finish-v1'
id=sys.argv[1];E=ROOT/'Main/shorts-clips/Exports/01 Finished Edits/2026-11-08 - Complete Thoughts';E.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
qa=read(F/'qa'/(id+'-full-qa.json'));assert qa['caption_face_intersections']==[]
assert qa['audio_packet_payload_and_timestamps_identical_to_approved_assembly'] and qa['full_audio_decode']
visual=read(F/'qa/visual-approval.json');assert id in visual['approved_ids']
cover=next(r for r in read(F/'thumbnails/provenance.json') if r['id']==id)
cover['review_status']='Assistant inspected phone-size and centred-square previews; accepted for delivery.'
row=next(r for r in read(P/'proofs.json') if r['id']==id)
source=read(P/'sources'/(id+'-source.json'))
files=[]
for src in [F/'finished'/(id+'-music-free.mp4'),Path(cover['file'])]:
 dest=E/src.name
 if dest.exists():assert digest(dest)==digest(src),'Preserve different existing export'
 else:shutil.copy2(src,dest)
 assert digest(src)==digest(dest)
 files.append({'file':str(dest),'sha256':digest(dest),'bytes':dest.stat().st_size})
manifest=read(E/'DELIVERY_MANIFEST.json') if (E/'DELIVERY_MANIFEST.json').exists() else {'project':P.name,'clips':[]}
manifest['clips']=[r for r in manifest['clips'] if r['id']!=id]
manifest['clips'].append({'id':id,'duration':row['duration'],'frames':row['frames'],'rate':row['rate'],
 'dimensions':[2160,3840],'source':source['canonical_url'],'source_dimensions':[3840,2160],
 'permission_basis':source.get('reuse_basis',read(P/'brief.json')['permissions'][source['id']]),
 'files':files,'thumbnail':cover,'qa':qa})
manifest['clips'].sort(key=lambda r:r['id']);manifest['status']='complete' if len(manifest['clips'])==5 else 'partial: remaining approved clips still finishing'
(E/'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
copy=read(F/'posting-copy.json');delivered={r['id'][:2] for r in manifest['clips']}
lines=['# thought.palace — complete thoughts','',f'Delivery status: {manifest["status"]}.','',
 '4K vertical masters, native source FPS, music-free, no added narration/SFX/channel symbol.',
 'Every video has a matching 4K cover. Originals and all earlier roughs remain in Working.', '']
for item in copy:
 if item['number'] not in delivered:continue
 clip=next(c for c in manifest['clips'] if c['id'].startswith(item['number']))
 lines += [f'## {item["number"]}. {item["title"]}','',item['description'],'',item['hashtags'],'',
 f'Duration: {clip["duration"]:.2f}s. Source: {clip["source"]}',
 f'Suggested related upload after publication: {item["related_clip"]}.','']
(E/'POSTING_COPY.md').write_text('\n'.join(lines),encoding='utf-8')
(E/'QA_COVERAGE.md').write_text('''# QA coverage

Each delivered video completely decodes at the expected native frame count and
regular source frame rate. Audio fully decodes; dialogue packet payloads and
timestamps are identical to the approved clean assembly. Source cuts, runtime and
normal speed are preserved. No music, SFX, narration or channel symbol was added.

Every caption word uses white Difference; font faces are bundled licensed Inter
Bold and occasional true Cormorant Garamond italics. Every final frame was analysed
for detected-face/caption intersections, with no intersections in delivered files.
Detection coverage is recorded per clip; absence of a detection is not proof that
no face exists. The assistant inspected the first-three-second/phrase/camera-cut
contact sheets and cover previews at phone size and a centred square crop.

Goggins is reframed to the right with captions on dark empty space to his left
because Difference text was too weak over his grey hoodie. Other captions start
from central compositions and move below faces where close-ups require it.

All 4K originals are 3840x2160. Their square crop retains up to 2160-square detail;
Robbins uses a 1920-square crop to exclude the original side text panel. The final
picture window is 1960-square on a 2160x3840 canvas. These are separate dimensions;
canvas resolution is not a claim of additional camera detail.

Continuous final audiovisual listening was not independently performed. Owner
approved all five content cuts; unchanged audio, decoding, ASR and sampled-image
review do not establish a new continuous listening pass. Most word timing is CUDA
aligned and frame-quantized. Missing fast Goggins words use the official source
transcript with interpolated onsets; exact one-frame manual certification is not
claimed. See the working caption-corrections record for this specific limitation.

Cover text is original editorial headline copy, not a fabricated speaker quote.
Covers use clean source frames, programmatic typography/shading and cleared fonts.
No reference graphics, notifications, footage, music or foreign overlay were copied.
Physical microphone/clothing labels in the original photographed scene remain.

Full per-file hashes, source permissions, timing and QA receipts are in
DELIVERY_MANIFEST.json. Guard receipts and detailed phrase sheets remain in Working.
''',encoding='utf-8')
print('DELIVERED',id,str(E))
