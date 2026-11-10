import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
import discover
p=P/'catalogue.json';x=json.loads(p.read_text(encoding='utf-8'))
ids=['5pk8HLcAAT0','tf_PeAjICmo','ANbwozhBYuE','ZRZ7J6SIVZs']
data=discover.collect(['https://www.youtube.com/watch?v='+v for v in ids],1)
identity=next(s for s in x['sources'] if s['family']=='iced-coffee-hour')['channel_id']
for e in data['episodes']:
 e.update(source_family='iced-coffee-hour',channel_identity_matches_listing=e['channel_id']==identity)
 e['source_verification']='original_channel_metadata_verified' if e['channel_identity_matches_listing'] else 'channel_mismatch_requires_review'
x['episodes']=list({e['key']:e for e in x['episodes']+data['episodes']}.values());x['listings']+=data['listings']
for listing in x['listings']:
 for error in listing.get('errors',[]):
  if "channel's members" in error.get('reason',''):
   error['status']='blocked';listing['status']='blocked'
x['scope']='50 public original episodes across six shows; four members-only attempts recorded separately; no full back-catalogue coverage'
discover.write_catalogue(p,x);print('PUBLIC ORIGINALS',len(x['episodes']))
