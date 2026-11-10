"""Summarise completed technical proofs, preserving the owner editorial gate."""
import hashlib,json
from pathlib import Path

P=Path(__file__).resolve().parent;ROOT=P.parents[3]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
proofs=read(P/'proofs.json')
assert len(proofs)==5 and len({r['id'] for r in proofs})==5
rows=[];manifest=[]
lines=['# Five complete-thought rough cuts', '',
 'These are caption-free 1080×1920 editorial proofs WITH SOUND from native 4K originals.',
 'Please watch each whole passage and choose **keep** or **replace**. The question is whether',
 'the spoken opening, progression and ending work together for thought.palace.',
 'Final 4K captions, effects, thumbnails and posting copy follow only for approved cuts.', '',
 '| # | Speaker / proposed title | Duration | Review video |',
 '|---|---|---:|---|']
for index,row in enumerate(proofs,1):
 r=read(P/'drafts'/(row['id']+'-rough.json'));source=read(P/'sources'/(row['id']+'-source.json'))
 path=Path(row['proof']);assert path.is_file() and 'INTERRUPTED' not in path.name
 assert r['technical']['full_audio_decode'] and r['technical']['audio_packet_identity_to_clean_assembly']
 assert r['technical']['full_cuda_decode']['frames']==r['frames']
 assert 20<=r['duration']<=40 and r['rate']==source['rate']
 assert source['actual']['native_4k']
 proof_guard=None
 for directory in sorted((ROOT/'.runtime/guard').iterdir(),key=lambda f:f.stat().st_mtime,reverse=True)[:15]:
  output=directory/'stdout.log';result=directory/'result.json'
  if output.exists() and result.exists() and ('PROOF '+row['id']+' ') in output.read_text(encoding='utf-8',errors='replace'):
   status=read(result)
   assert status['status']=='worker_succeeded' and status['cleanup_confirmed']
   proof_guard=directory.name;break
 assert proof_guard, 'No successful guard receipt for '+row['id']
 lines.append(f"| {index} | {r['speaker']} — {r['title']} | {r['duration']:.2f}s | [{path.name}](<{path.as_posix()}>) |")
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 manifest.append({**row,'sha256':digest,'guard':proof_guard,
   'canonical_url':source['canonical_url'],'source_4k':[3840,2160],
   'source_pieces_local_frame_quantized':r['pieces'],'source_pieces_approx_episode':
      [[r['source_context_start']+a,r['source_context_start']+b] for a,b in r['pieces']],
   'technical':r['technical'],'owner_decision':'pending',
   'continuous_listening_review':'Pending owner; no assistant or cloud full audiovisual review claimed.'})
 rows.append(r)
lines += ['', '## Cut notes', '',
 'Episode coordinates are approximate, based on the requested source window; local frame-quantized cuts in each edit record are authoritative.', '']
for index,r in enumerate(rows,1):
 ranges=', '.join(f'{r["source_context_start"]+a:.2f}–{r["source_context_start"]+b:.2f}s' for a,b in r['pieces'])
 lines += [f'### {index}. {r["title"]}', '',
   f'- **Original:** [{r["speaker"]}](https://www.youtube.com/watch?v={r["video_id"]}) — {ranges}.',
   f'- **Opening:** {r["opening"]}',f'- **Development:** {r["development"]}',
   f'- **Conclusion:** {r["conclusion"]}',f'- **Cuts:** {r["cut_note"]}',
   f'- **Why it fits:** {r["channel_fit"]}',
   f'- **First three seconds:** {r["first_three_seconds"]}',
   f'- **Review risk:** {r.get("risk","Full spoken fluency and whether the ending lands remain for owner listening review.")}', '']
lines += ['## Technical QA and coverage', '',
 '- All five are 1080×1920 roughs from actual 3840×2160 originals, preserving native FPS.',
 '- Every proof fully decodes at its expected frame count. Every dialogue track fully decodes.',
 '- Dialogue packet payloads/timestamps match each clean assembly. Exact source cuts require one AAC encode, with 15ms boundary fades; no speed change or voice replacement.',
 '- Rounded-square picture: x50, y470, 980×980, radius48 on black. No added captions, effects, narration, music or logo.',
 '- Original context captions and five-second source contact sheets inspected; local candidate word alignment checked. One-second rough contact sheets are the visual-QA evidence.',
 '- Full continuous audiovisual listening and owner editorial acceptance are PENDING. Sampled frames and ASR cannot establish complete fluency, music absence or a satisfying finish.',
 '- Earlier rejected videos and the interrupted first rough are preserved and excluded from these five review links.',
 '- Final caption timing, Difference blending, italics, centred layout, transitions, interface clearance and thumbnail quality will be checked after owner selection.', '',
 'The five roughs intentionally remain in Working; they are not final upload files. Approved, validated finished videos and thumbnails will be physically copied to a new Exports folder.', '']
(P/'REVIEW.md').write_text('\n'.join(lines),encoding='utf-8')
(P/'REVIEW_MANIFEST.json').write_text(json.dumps({'stage':'owner_editorial_review',
 'final_finish_authorized_by_selection_only':True,'proofs':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print('Five review links and technical receipts written; owner listening choices pending.')
