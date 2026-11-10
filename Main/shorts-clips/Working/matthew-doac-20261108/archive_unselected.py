"""Preserve the owner-requested unselected proof in Exports without promotion as a final."""
import json,hashlib,shutil,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from moment_research import read,save,validate_bank
import results
source=P/'drafts/01-the-offer-content-proof.mp4';record=read(P/'content-proof.json')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source)==record['sha256']
for job in ['db94516bd2794846a2719f0f7a765c04','b456b84ba30643db8d514a9b756f5808']:
 r=read(ROOT/'.runtime/guard'/job/'result.json');assert r['status']=='worker_succeeded' and r['cleanup_confirmed']
folder=ROOT/'Main/shorts-clips/Exports/03 Archive/2026-11-08 - McConaughey Offer Story - Unselected';folder.mkdir(parents=True,exist_ok=True)
target=folder/'01-the-offer-content-proof-UNSELECTED.mp4'
if target.exists():assert digest(target)==record['sha256'],'Do not overwrite an earlier different archive'
else:shutil.copy2(source,target)
assert digest(target)==record['sha256']
archive={'file':str(target),'sha256':digest(target),'source_url':record['source_url'],'original_source_pieces':record['original_source_pieces'],
 'duration':record['duration'],'frames':record['frames'],'fps':record['fps'],'dimensions':record['dimensions'],
 'status':'Owner-requested archive; rejected for thought.palace channel fit; not selected for posting',
 'reuse_basis':record['reuse_basis'],'owner_feedback':'No, I do not think videos like these will fit into our thought.palace account. Keep this stored in exports.',
 'added_captions':False,'added_music':False,'added_branding':False,'production_finish':False,
 'technical_qa':'Full CUDA decode and 759-frame native-clock check passed; audio packets equal to clean assembly. Full-proof CUDA ASR confirms opening Eight and ending no; no And I think tail.',
 'review_coverage':'Assistant inspected complete two-second composition sheet; owner rejected fit after receiving sound-review prompt. Do not infer independently verified full owner playback or assistant continuous listening.',
 'working_records':str(P)}
save(P/'archive-delivery.json',archive);save(folder/'ARCHIVE_MANIFEST.json',archive)
(folder/'ARCHIVE_NOTE.md').write_text('''# Unselected content proof — retained at owner request

The owner rejected this McConaughey pay-offer story for thought.palace and requested
keeping the file in Exports. **UNSELECTED: do not include in upload recommendations.**

This is the unchanged 30.36-second, 720×1280 content proof, with original dialogue,
no added music, captions or channel symbol. It is an archive, not a 4K finished master.
The original draft and QA remain in Working. Source permission for this DOAC episode
was confirmed; editorial channel fit was rejected. See ARCHIVE_MANIFEST.json for source
ranges, hashes and review coverage. No further finishing of this proof is queued.
''',encoding='utf-8')
key=('matthew-doac-20261108','01-the-offer-content-proof')
if not any((r.get('project'),r.get('clip'))==key and r.get('decision')=='rejected' for r in results.load(results.SELECTION_LOG)):
 results.append(results.SELECTION_LOG,{'project':key[0],'clip':key[1],'decision':'rejected','reason':'Owner: pay-offer story does not fit thought.palace; retain in Exports as unselected archive.','production_minutes':None,'logged':'2026-11-08','evidence':'Owner reply to content-proof review in this chat.'})
BASE=P.parent/'content-discovery-20261108';bank=read(BASE/'candidate-bank.json')
for b in bank:
 if b['source_url']==record['source_url']:b['reuse_basis']=record['reuse_basis']
 if b['id']=='01-cost-of-saying-no':
  b['status']='rejected';b['priority']='rejected_owner_fit';b['checks']['channel_fit']='reject'
  b['owner_review']={'decision':'rejected_channel_fit','evidence':'Owner response in this chat, 8 November 2026','archived_file':str(target),'full_playback_completion':'not independently established'}
  b['review_findings']='Owner rejected fit for thought.palace after reviewing the content-proof prompt. Rising celebrity pay dominated the personal audience connection. Preserve as unselected archive; no finishing or upload recommendation.'
  b['content_proof']=archive
errors=validate_bank(bank,read(BASE/'catalogue.json'),[read(p) for p in (BASE/'transcripts').glob('*.json')]);assert not errors,errors
save(BASE/'candidate-bank.json',bank)
save(BASE/'review-v2/candidate-bank.json',bank)
print(json.dumps({'archive':str(target),'sha256_verified':True,'decision':'unselected; no finishing queued'},indent=2))
