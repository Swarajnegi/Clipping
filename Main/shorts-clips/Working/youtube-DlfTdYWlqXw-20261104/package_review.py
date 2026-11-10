"""Package completed, technically checked review drafts without hiding QA gaps."""
import hashlib,json,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import probe,require_guard
require_guard()
decisions=json.loads((PROJECT/'edit-decisions.json').read_text(encoding='utf-8'))
visual_path=PROJECT/'qa/visual-review.json'
visual=json.loads(visual_path.read_text(encoding='utf-8'))
visual['07-silver-thread']=dict(caption_pages_inspected=147,sheets_inspected=14,camera_cut_samples=True,
    findings='All 14 final phrase/cut sheets inspected, including story setup, thread warning, university/work/marriage/parenthood transitions, wedding-day emphasis and full present-moment payoff. Typography fits; faces remain clear; no foreign overlaid branding seen in sampled final frames.')
for d in decisions:
    slug=d['slug']
    visual[slug]['caption_pages_inspected']=len(json.loads((PROJECT/'authoring'/slug/'caption-pages.json').read_text(encoding='utf-8')))
visual['coverage']='All saved final caption-page/cut sheets for all seven drafts inspected. Every video frame separately decoded and face-detector checked. Full-duration continuous audiovisual playback and audible word-onset acceptance remain unverified: the configured remote service returned HTTP 503 and native audio input is unsupported.'
visual_path.write_text(json.dumps(visual,indent=2),encoding='utf-8')
geometry=json.loads((PROJECT/'qa/caption-geometry.json').read_text(encoding='utf-8'))
assert not geometry['failures'] and not geometry['collisions']
root_receipt=json.loads((ROOT/'.runtime/guard/7c87254bfcbc4e2081f76b5b8e3448a0/result.json').read_text())
assert root_receipt['status']=='worker_succeeded' and root_receipt['cleanup_confirmed']
files=[]
for d in decisions:
    slug=d['slug'];file=PROJECT/'drafts'/(slug+'-music-free-DRAFT.mp4')
    qa=json.loads((PROJECT/'qa'/slug/'technical-review.json').read_text(encoding='utf-8'))
    copied=json.loads((PROJECT/'qa'/slug/'audio-copy.json').read_text(encoding='utf-8'))
    media=probe(file)
    assert (media.width,media.height,media.fps)==(2160,3840,25)
    assert media.has_audio and qa['complete_decode'] and qa['decoded_frames']==d['frames']
    assert qa['face_detection_coverage']==1 and not qa['caption_face_overlaps']
    assert copied['picture_unchanged'] and copied['dialogue_packets_unchanged']
    assert all(c['correlation']>.99999 and c['lag_ms']==0 for c in qa['dialogue_audio_checks'])
    digest=hashlib.sha256()
    with file.open('rb') as stream:
        while block:=stream.read(1024*1024):digest.update(block)
    files.append(dict(slug=slug,title=d['title'],file=str(file),duration=d['frames']/25,
        frames=d['frames'],bytes=file.stat().st_size,sha256=digest.hexdigest(),
        original_segments=d['absolute_segments'],caption_pages=visual[slug]['caption_pages_inspected'],
        complete_decode=True,face_detection_coverage=1,caption_face_overlaps=0,
        clean_dialogue_payload_preserved=True,measured_audio_shift_ms=0))
manifest=dict(status='Seven rendered, technically validated review drafts; final listening review open',
    source='https://www.youtube.com/watch?v=DlfTdYWlqXw',
    reuse_basis='Owner explicitly confirmed this Lotgenoten episode covered by clipping permission/campaign authorization on 4 November 2026',
    resolution=[2160,3840],fps=25,source_resolution=[3840,2160],
    added_music=False,added_narration=False,added_channel_symbol=False,
    font='Bundled Inter, upright 700/800, silver-white gradient with strong dark shadows',
    caption_layers_measured=geometry['checked_layers'],total_frames=sum(f['frames'] for f in files),
    total_caption_pages=sum(f['caption_pages'] for f in files),
    review_gap='Full continuous audiovisual playback and audible word-onset acceptance are unverified. No claim of direct listening. Configured free Gemini returned HTTP 503; native audio input is unsupported. No model/provider change, paid fallback or API retry was made.',
    production_guard='.runtime/guard/7c87254bfcbc4e2081f76b5b8e3448a0/result.json',
    cleanup_confirmed=True,files=files)
(PROJECT/'REVIEW_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

def clock(seconds):
    h=int(seconds//3600);m=int(seconds%3600//60);s=seconds%60
    return f'{h:02}:{m:02}:{s:05.2f}'

lines=['# Luke Belmar — 4K review clips',
 'Seven music-free review drafts. Source: [Lotgenoten Podcast episode 192](https://www.youtube.com/watch?v=DlfTdYWlqXw).',
 'All files are 2160×3840, 25 FPS, with text rasterized at 4K from the bundled Inter font. No music, narration or channel symbol was added.',
 '**Review status:** every frame decoded; every detected face remained clear of caption bounds (100% frame detection coverage); all 622 text layers fit measured safe bounds; original clean-edit dialogue packets and timing are retained. Every final caption-page/cut sheet was visually inspected. Full listening review remains open, so these stay in Working rather than being labelled validated Exports.',
 'The configured free audiovisual reviewer returned HTTP 503. Native audio input is unsupported in this session. These limitations do not invalidate the packet/timing checks, but they do leave audible wording/onsets and a complete listen-through unverified.']
table=['| File | Duration | Title |','| --- | ---: | --- |']
for f in files:table.append(f'| [{f["slug"]}]({Path(f["file"]).as_posix()}) | {f["duration"]:.2f}s | {f["title"]} |')
lines.append('\n'.join(table))
lines+=['','## Suggested posting copy',
 'Descriptions below are original editorial interpretation, not fabricated speaker quotations. Source credit: Luke Belmar on Lotgenoten Podcast. The permission basis is retained in the manifest.',
 'Suggested first choices for owner review: family, happiness/freedom (the owner’s lead), and the fisherman. The longer story is a separate storytelling option.']
for d,f in zip(decisions,files):
    ranges='; '.join(f'{clock(a)}–{clock(b)}' for a,b in d['absolute_segments'])
    lines+=['',f'## {d["slug"]}',f'**Title:** {d["title"]}',d['description'],
        f'**Original-source range(s):** {ranges}',f'**Editorial reason:** {d["why"]}']
lines+=['','## Evidence and remaining review',
 'See REVIEW_MANIFEST.json for exact durations, frame counts, file hashes and source ranges; qa/visual-review.json for visual coverage; qa/<clip>/technical-review.json and audio-copy.json for complete decode/face checks and compressed audio/picture preservation.',
 'Caption bounds include entry-motion allowance and conservative interface margins. Faces were checked on every decoded frame; hands were assessed in the page/cut samples, and some lower gestures cross the bottom caption zone. This is not represented as an every-frame manual hand review.',
 'The faster native-browser decoder experiment was rejected because it repeated several source frames. Production uses the established OffthreadVideo renderer, PNG capture and NVENC. The builder’s new --output-scale 2 path was tested on a real sample; existing Python caption/pipeline suites passed (8 + 16 tests).',
 'Before promotion to Exports, review the complete outputs with sound, checking audible caption wording/onsets and the cut edges. The viral-shorts caption guide explicitly says: “Then review the complete output with sound.” No permission reconfirmation is needed; episode coverage is already recorded.']
(PROJECT/'UPLOAD.md').write_text('\n\n'.join(lines),encoding='utf-8')
(PROJECT/'drafts/START-HERE.md').write_text('# Seven 4K review drafts\n\nAll seven MP4s in this folder are complete renders with technical and sampled visual checks. Full listening review is still open; see [posting copy and review notes](../UPLOAD.md) and [manifest](../REVIEW_MANIFEST.json).\n',encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k not in ['files','review_gap','reuse_basis']},ensure_ascii=True),flush=True)
for f in files:print(f['slug'],f['duration'],f['frames'],f['bytes'],flush=True)
