"""Package validated caption revisions honestly; no unobserved listening claim."""
import argparse,hashlib,json,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard
require_guard()
parser=argparse.ArgumentParser();parser.add_argument('--guard-id',required=True);args=parser.parse_args()
guard=ROOT/'.runtime/guard'/args.guard_id
guard_result=json.loads((guard/'result.json').read_text())
assert guard_result['status']=='worker_succeeded' and guard_result['cleanup_confirmed']
decisions=json.loads((PROJECT/'edit-decisions.json').read_text())
selection=json.loads((PROJECT/'selection.json').read_text())
decisions=[d for d in decisions if d['slug'] in selection['selected']]
for slug in selection['skipped']:
    assert not (PROJECT/'drafts'/(slug+'-caption-v2-music-free-DRAFT.mp4')).exists()
old=json.loads((PROJECT.parent/'REVIEW_MANIFEST.json').read_text())
changes={x['slug']:x for x in json.loads((PROJECT/'caption-changes.json').read_text())}
visual=json.loads((PROJECT/'qa/visual-review.json').read_text())
geometry=json.loads((PROJECT/'qa/caption-geometry.json').read_text())
assert not geometry['failures'] and not geometry['collisions']
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
files=[];copy=['# Revised 4K music-free clips\n',
 'Caption-only revision: selective colour-reactive Difference surfaces and true serif italic accents.\n',
 'Cuts, framing, dialogue packets/timing and word onsets are preserved. Earlier drafts remain intact.\n',
 'Every frame decoded and face-checked; every caption page/cut sample visually reviewed. The audio is byte-identical to the previous draft; no new direct listening or continuous audiovisual playback is claimed. These remain review drafts in Working.\n']
for d in decisions:
    slug=d['slug'];qa=PROJECT/'qa'/slug
    tech=json.loads((qa/'technical-review.json').read_text())
    invariant=json.loads((qa/'revision-invariants.json').read_text())
    assert slug in visual['reviewed']
    assert tech['complete_decode'] and tech['decoded_frames']==d['frames']
    assert not tech['caption_face_overlaps'] and tech['face_detection_coverage']==1
    assert invariant['audio_payload_and_packet_timing_identical']
    assert invariant['dimensions_fps_duration_identical']
    previous=next(f for f in old['files'] if f['slug']==slug)
    assert digest(Path(previous['file']))==previous['sha256'],'Earlier draft changed'
    path=PROJECT/'drafts'/(slug+'-caption-v2-music-free-DRAFT.mp4')
    file=dict(slug=slug,title=d['title'],file=str(path),duration=d['duration'],frames=d['frames'],
              bytes=path.stat().st_size,sha256=digest(path),previous_sha256=previous['sha256'],
              original_intact=True,italic_layers=changes[slug]['italic_layers'],
              difference_layers=changes[slug]['difference_layers'],
              audio_packets_identical=True,audio_timing_identical=True,
              visual_review=visual['reviewed'][slug],technical_review=str(qa/'technical-review.json'))
    files.append(file)
    copy.extend([f"## {d['title']}\n",f"[{slug} — {d['duration']:.2f}s]({path.as_posix()})\n",d['description']+'\n'])
samples=[json.loads(line) for line in (guard/'samples.jsonl').read_text().splitlines() if line.strip()]
manifest=dict(status='Six caption-v2 review drafts; silver-thread revision skipped by owner',
              source=old['source'],reuse_basis=old['reuse_basis'],resolution=[2160,3840],fps=25,
              total_frames=sum(f['frames'] for f in files),
              total_caption_pages=sum(len(json.loads((PROJECT/'authoring'/f['slug']/'caption-pages.json').read_text())) for f in files),
              caption_layers_measured=sum(1 for m in geometry['measurements'] if m['clip'] in selection['selected']),
              italic_layers=sum(f['italic_layers'] for f in files),difference_layers=sum(f['difference_layers'] for f in files),
              added_music=False,added_narration=False,added_channel_symbol=False,originals_preserved=True,
              fonts='Inter Bold base; selected Cormorant Garamond true italic 700; bundled OFL assets and provenance',
              audio='Approved previous dialogue stream-copied; every packet payload and timestamp compared equal',
              review_gap='No new direct listening or continuous audiovisual playback claimed. Owner approved other treatment after family preview, but approval of listening to every file is not inferred.',
              production_guard=str(guard/'result.json'),cleanup_confirmed=True,
              guard_thermal_profile=guard_result['thermal_profile'],
              observed_max_gpu_temperature=max(s['Temperature'] for s in samples if s.get('Temperature') is not None),
              skipped=selection['skipped'],files=files)
(PROJECT/'REVIEW_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(PROJECT/'UPLOAD.md').write_text('\n'.join(copy),encoding='utf-8')
status_path=PROJECT/'batch-status.json'
state=json.loads(status_path.read_text())
archive=PROJECT/'qa/batch-status-before-selection-normalization.json'
if not archive.exists():archive.write_text(json.dumps(state,indent=2))
state['processed_entries']=state['completed']
state['completed']=[f['slug'] for f in files]
state['skipped']=selection['skipped']
state['stage']='All six selected revisions rendered and technically checked; silver-thread skipped'
status_path.write_text(json.dumps(state,indent=2))
print(json.dumps(dict(clips=len(files),frames=manifest['total_frames'],
                     difference_layers=manifest['difference_layers'],italic_layers=manifest['italic_layers'],
                     originals_intact=True,review_gap=manifest['review_gap']),indent=2))
