"""Refresh the owner's current editorial reference set; public metadata/captions only."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;BASE=P.parent;ROOT=BASE.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from moment_research import fetch_caption,save,read
import discover
identity=read(P/'owner-channel-identity.json');listing=read(P/'owner-channel-listing.json')
ids=[r['id'] for r in listing['rows'][:5]]
folder=P/'posted-current';folder.mkdir(exist_ok=True)
catalogue=discover.collect(['https://www.youtube.com/watch?v='+id for id in ids],1)
for e in catalogue['episodes']:assert e['channel_id']==identity['channel_id']
save(folder/'catalogue.json',catalogue)
for e in catalogue['episodes']:
 target=folder/(e['video_id']+'-captions.json')
 if target.exists():raise FileExistsError('Preserve prior post study')
 record=fetch_caption(e);save(target,record)
 print(e['video_id'],e['title'],e['upload_date'],record['status'],flush=True)
 print(' '.join(s['text'] for s in record['segments']),flush=True)
