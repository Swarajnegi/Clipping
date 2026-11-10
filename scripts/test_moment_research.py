"""Identity, missing-data, search and editorial gate regressions; no network or media."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import moment_research as m
import results
import discover

class ResearchTests(unittest.TestCase):
 def setUp(self):
  self.episode={'key':'youtube:one','video_id':'one','canonical_url':'https://www.youtube.com/watch?v=one','title':'original','duration':200}
  self.catalogue={'episodes':[self.episode]}
  self.record={'key':'youtube:one','canonical_url':self.episode['canonical_url'],'status':'available','segments':[{'start':10,'end':15,'text':'My father taught me something.'},{'start':30,'end':35,'text':'I thought I lost everything.'},{'start':50,'end':55,'text':'But my wife stayed.'}]}
 def candidate(self):
  return {'id':'a','source_key':'youtube:one','source_url':self.episode['canonical_url'],'segments':[[10,55]],'opening':'My father taught me something','context':'context','payoff':'wife stayed','cut_proposal':'complete story','benchmark':'story reversal','risks':['ASR needs listening'],'checks':dict.fromkeys(['opening','progression','payoff','channel_fit'],'pass')|{'delivery':'pending'},'status':'transcript_shortlist','reuse_basis':'unknown','av_review':{'audio':False,'full_passage':False}}
 def test_json3_noise_entities_and_duplicate_event(self):
  event={'tStartMs':1000,'dDurationMs':2000,'segs':[{'utf8':'Tom &amp; Jerry'}]}
  self.assertEqual(m.json3_segments({'events':[event,event,{'tStartMs':1,'segs':[{'utf8':'\n'}]}]}),[{'start':1.0,'end':3.0,'text':'Tom & Jerry'}])
 def test_index_search_context_and_idempotency(self):
  with tempfile.TemporaryDirectory(dir=m.ROOT/'.runtime') as tmp:
   db=Path(tmp)/'index.sqlite'
   m.build_index(self.catalogue,[self.record],db);m.build_index(self.catalogue,[self.record],db)
   rows=m.search(db,'lost everything',phrase=True)
   self.assertEqual(len(rows),1);self.assertEqual(rows[0]['key'],'youtube:one');self.assertIn('wife stayed',' '.join(s['text'] for s in rows[0]['context']))
 def test_missing_captions_distinct_from_failure(self):
  with tempfile.TemporaryDirectory(dir=m.ROOT/'.runtime') as tmp:
   db=Path(tmp)/'index.sqlite'
   m.build_index(self.catalogue,[{**self.record,'segments':[],'status':'retrieval_failed'}],db)
   self.assertEqual(m.search(db,'anything'),[])
  self.assertEqual(discover.error_status("available to this channel's members"),'blocked')
 def test_wrong_identity_and_bad_timestamps(self):
  with tempfile.TemporaryDirectory(dir=m.ROOT/'.runtime') as tmp:
   for row in [{**self.record,'canonical_url':'https://example.com/wrong'},{**self.record,'segments':[{'start':float('nan'),'end':2,'text':'bad'}]}]:
    with self.assertRaises(ValueError):m.build_index(self.catalogue,[row],Path(tmp)/'index.sqlite')
 def test_provisional_bank_is_valid_without_false_audio_claim(self):
  self.assertEqual(m.validate_bank([self.candidate()],self.catalogue,[self.record]),[])
 def test_fluency_and_ready_status_need_evidence_and_rights(self):
  item=self.candidate();item['checks']['delivery']='pass';item['status']='production_ready'
  errors=m.validate_bank([item],self.catalogue,[self.record])
  self.assertTrue(any('fluency' in x for x in errors));self.assertTrue(any('reuse' in x for x in errors))
 def test_duplicate_unknown_quote_and_range_rejected(self):
  a=self.candidate();b=copy.deepcopy(a);b['id']='b'
  self.assertTrue(any('duplicate' in x for x in m.validate_bank([a,b],self.catalogue,[self.record])))
  b['segments']=[[11,54]]
  self.assertTrue(any('near-duplicate' in x for x in m.validate_bank([a,b],self.catalogue,[self.record])))
  for changes in ({'opening':'Never spoken'},{'source_url':'wrong'},{'segments':[[10,999]]}):
   self.assertTrue(m.validate_bank([a|changes],self.catalogue,[self.record]))

class ResultsTests(unittest.TestCase):
 def args(self,**changes):
  return SimpleNamespace(url='https://youtube.com/shorts/one',clip='unknown',stayed=None,avd=None,average_percentage_viewed=None,views=None,hours=48,**changes)
 def test_legacy_avd_percentage_is_not_seconds(self):
  a=self.args(avg_view_duration_seconds=27);a.avd=92
  row=results.audience_row(a);self.assertEqual(row['avd'],92);self.assertEqual(row['average_percentage_viewed'],92);self.assertEqual(row['avg_view_duration_seconds'],27)
 def test_conflicting_percentage_alias_rejected(self):
  a=self.args();a.avd=92;a.average_percentage_viewed=80
  with self.assertRaises(ValueError):results.audience_row(a)
 def test_unknown_not_zero_and_loop_percentage_allowed(self):
  row=results.audience_row(self.args());self.assertIsNone(row['views']);self.assertIsNone(row['avd']);self.assertEqual(results.number('115'),115)
  for x in ('nan','inf','-1'):
   with self.assertRaises(Exception):results.number(x)
 def test_age_windows_and_legacy_snapshots(self):
  rows=[{'url':'x','hours':24,'avd':95},{'url':'x','hours':48,'avd':90},{'url':'x','hours':168,'avd':70}]
  self.assertEqual(len(results.snapshots(rows)),3);self.assertEqual(results.snapshots(rows,48)[0]['avd'],90)
 def test_selection_counts_wasted_cost_and_excerpt_separately(self):
  rows=[{'project':'p','clip':'a','decision':'accepted','production_minutes':10},{'project':'p','clip':'b','decision':'rejected','production_minutes':20},{'project':'p','clip':'c','decision':'excerpt_only','production_minutes':5}]
  r=results.selection_summary(rows);self.assertEqual(r['accepted'],1);self.assertEqual(r['excerpt_only'],1);self.assertEqual(r['minutes_per_accepted_clip'],35)
  rows[-1]['production_minutes']=None;self.assertIsNone(results.selection_summary(rows)['minutes_per_accepted_clip'])
 def test_append_empty_file_and_missing_newline(self):
  with tempfile.TemporaryDirectory(dir=m.ROOT/'.runtime') as tmp:
   p=Path(tmp)/'rows.jsonl';results.append(p,{'clip':'a'});p.write_text(p.read_text().strip(),encoding='utf-8');results.append(p,{'clip':'b'})
   self.assertEqual(len(results.load(p)),2)

if __name__=='__main__':unittest.main()
