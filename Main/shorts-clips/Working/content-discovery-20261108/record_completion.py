"""Bind the research handoff to real coverage and completed checks, not provider availability."""
import json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from moment_research import read,save,validate_bank
bank=read(P/'candidate-bank.json');catalogue=read(P/'catalogue.json')
provider=P/'source-review/01-cost-of-saying-no-provider.md'
assert 'Answer (from Gemini)' in provider.read_text(encoding='utf-8')
for b in bank:
 b['priority']='A' if b['id'].startswith(('01','02','05')) else ('B' if b['id'].startswith(('06','08')) else 'revise_opening')
 if b['id'].startswith('01'):
  b['av_review']={'audio':True,'full_passage':True,'method':'Gemini audiovisual second opinion on original seconds 6132–6187; assistant independently inspected five-second source frames; no direct assistant continuous listening',
   'evidence':str(provider),'source_url':b['source_url'],'focus_start':6132,'focus_end':6187,'reviewed_picture':'original context, not an assembled final edit'}
  b['checks']['delivery']='pass';b['checks']['payoff']='pending'
  b['review_findings']='Provider supports spoken escalation/comic timing but judges proposed edit pending: 6183.10 includes And I think; align the out-point immediately after the final no (provider estimates around 6182, not frame-exact). The book visible in his hands is a memoir, not a film script.'
  if 'Provider-detected tail overhang must be removed at the final no before approval.' not in b['risks']:b['risks'].append('Provider-detected tail overhang must be removed at the final no before approval.')
 if b['id'].startswith('02'):
  b['av_review']['attempt']='Gemini HTTP 503; no completed audiovisual evidence. Batch stopped; no retry or alternative provider.'
  b['av_review']['failed_report']=str(P/'source-review/02-dads-unexpected-answer-provider.md')
save(P/'candidate-bank.json',bank)
errors=validate_bank(bank,catalogue,[read(p) for p in (P/'transcripts').glob('*.json')]);assert not errors,errors
assert len(catalogue['episodes'])==50 and len({e['key'] for e in catalogue['episodes']})==50
assert all(e['source_verification']=='original_channel_metadata_verified' and e['channel_identity_matches_listing'] and e['channel_id'] for e in catalogue['episodes'])
protected={'.agents/skills/viral-shorts/scripts/run_guarded.ps1':'bd1dfbdee7d682a12f5212f904dd6e8d0153c27762749de09814a19cf2e646f3',
 '.agents/skills/viral-shorts/scripts/guard_native.cs':'46a1bd58192a5a2d0c50c84b4f2851ea1130841847c13176d8819490efebc9b5',
 '.agents/skills/viral-shorts/references/editorial-captions.md':'64fdb165f446a5b007fe868ad56ad4bfc8975ba406dec0ed4c4cfa0fd4e09329'}
for path,digest in protected.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
guard=read(ROOT/'.runtime/guard/b827673f1fbb4d2fa95a2716f69980f9/result.json')
assert guard['status']=='worker_succeeded' and guard['cleanup_confirmed']
visual=read(P/'source-review/visual-review.json');assert len(visual)==4
for r in visual:assert hashlib.sha256(Path(r['file']).read_bytes()).hexdigest()==r['file_sha256']
tests=[('test_moment_research.py',13),('test_discovery.py',17),('test_motion_edit.py',10),('test_editorial_captions.py',9)]
validation={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':True,'episodes':50,'show_families':6,'transcripts':14,
 'benchmark_shorts':14,'candidate_records':8,'candidate_bank_valid':True,'source_sheets_inspected':4,'successful_provider_av_reviews':1,
 'provider_failures':1,'further_provider_calls_after_failure':0,'unresolved_delivery_checks':7,'unresolved_openings':3,
 'production_ready':0,'reviewed_finished_edits':0,'python_tests':{'passed':sum(n for _,n in tests),'groups':tests,'evidence':'Executed with project .venv via unittest; command outcomes retained in this Codex chat.'},
 'javascript_caption_motion_mask_italic_checks':'passed','typescript_no_emit':'passed','skill_quick_validate':'passed',
 'protected_files_unchanged_since_observed_baseline':protected,'source_gpu_guard':guard,
 'provider_guard_ids':['29a19c08f5414980ae5c46787748e270','a41a88cc1d20459899be6cfb3a0ca17d'],
 'provider_batch_note':'Second batch wrapper handled HTTP 503 and stopped. Outer worker exited zero in that run, but provider-receipts.json correctly records failure; runner subsequently corrected to propagate failure in future. No rerun made.',
 'scope':'Research and workflow implementation. No final clips, scheduler, service, new dependency/model/provider or delegation.'}
save(P/'validation.json',validation)
coverage='''# Research coverage and remaining gates

- 50 public original episodes across six shows catalogued; four members-only attempts recorded as blocked, with four public replacements.
- 14 selected published-caption transcripts cached and indexed; selected passages/context studied, not complete audiovisual review of 50 episodes.
- 14 benchmark Shorts have dated live metadata and transcript-level study. Private retention/binge data unavailable.
- Eight candidate records: five initially workable openings, three requiring opening revision. Every record has original identity, surrounding transcript, payoff, proposed cuts, benchmark and risks.
- Four original context windows acquired in H.264 and inspected through five-second source sheets. They retain original channel marks and are research media, never production masters.
- One successful existing-free-tier Gemini audiovisual review, for McConaughey's offer story. It supports delivery and catches a tail overhang after the final refusal; ending alignment remains pending. This is attributed provider evidence, not direct assistant continuous listening.
- A further provider attempt returned HTTP 503. The batch stopped; no retry, paid fallback or alternate provider. Remaining seven delivery checks remain pending.
- Initial automatic download selected AV1 and CUDA extraction stopped. Diagnostics and the original AV1 excerpt were preserved; a deliberate H.264 source-selection correction passed the guard. No CPU decoding fallback was used.
- No assembled final edits were reviewed or produced. Reuse permission is unknown for these new original episodes; permission from a guest's different interview is not transferred.
- Caption guide and guard files match their recorded hashes. Forty-nine Python checks, JavaScript caption/mask/italic checks, TypeScript noEmit and skill validation passed.

Candidate ranges are caption-cue proposals, not frame-final executable edit instructions. Word boundaries, joins, full proof with sound, rights and final visual/audio QA still precede 4K finishing/delivery.
'''
(P/'QA_COVERAGE.md').write_text(coverage,encoding='utf-8')
lines=['# Fifty original episodes — discovery catalogue','','Metadata and identity verified; not a production-approval list. Fourteen selected caption records are cached; others remain metadata-only.','']
cached={p.stem for p in (P/'transcripts').glob('*.json')}
for family in dict.fromkeys(e['source_family'] for e in catalogue['episodes']):
 lines += ['## '+family,'','| Original episode | Minutes | Study |','| --- | ---: | --- |']
 for e in catalogue['episodes']:
  if e['source_family']==family:
   title=e['title'].replace('|','–');study='captions cached; selective passage study' if e['key'].replace(':','_') in cached else 'metadata only'
   lines.append(f'| [{title}]({e["canonical_url"]}) | {e["duration"]/60:.0f} | {study} |')
 lines+=['']
(P/'EPISODES.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({k:validation[k] for k in ['passed','episodes','transcripts','candidate_records','source_sheets_inspected','successful_provider_av_reviews','production_ready']},indent=2))
