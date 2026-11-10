"""Bounded public metadata research; no video, models, provider uploads or services."""
import json, sys, re
from pathlib import Path
from datetime import datetime, timezone
P=Path(__file__).resolve().parent; ROOT=P.parents[3]; sys.path.insert(0,str(ROOT/'scripts'))
import discover
from yt_dlp import YoutubeDL
SOURCES=[('modern-wisdom','@ChrisWillx',9),('diary-of-a-ceo','@TheDiaryOfACEO',9),
 ('joe-rogan','@joerogan',8),('iced-coffee-hour','@TheIcedCoffeeHour',8),
 ('high-performance','@HighPerformancePodcast',8),('this-past-weekend','@TheoVon',8)]
EVERGREEN={
 'modern-wisdom':['https://www.youtube.com/watch?v=ky1oHHJ5Ne8','https://www.youtube.com/watch?v=M4PzOjM5BJQ','https://www.youtube.com/watch?v=Eu1kHIztT24'],
 'diary-of-a-ceo':['https://www.youtube.com/watch?v=QMzxNfX-uAg','https://www.youtube.com/watch?v=uHLAazKUU68'],
 'joe-rogan':[], 'iced-coffee-hour':['https://www.youtube.com/watch?v=rR_14L2RI2A'],
 'high-performance':['https://www.youtube.com/watch?v=CotzNJNLEkE'], 'this-past-weekend':[]}
opts={'quiet':True,'no_warnings':True,'cachedir':False,'skip_download':True,'socket_timeout':15,
 'retries':0,'extractor_retries':0,'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}}}
manifest=[]; episodes=[]; listings=[]
for family,handle,quota in SOURCES:
 checkpoint=P/(family+'-catalogue.json')
 if checkpoint.exists():
  saved=json.loads(checkpoint.read_text(encoding='utf-8')); episodes.extend(saved['episodes']); listings.extend(saved['listings']); manifest.append(saved['source']); continue
 url='https://www.youtube.com/'+handle+'/videos'
 try:
  with YoutubeDL({**opts,'extract_flat':True,'playlistend':60}) as y: listing=y.extract_info(url,download=False)
  raw=[e for e in listing.get('entries',[]) if e]
  (P/(family+'-listing.json')).write_text(json.dumps({'channel':url,'channel_id':listing.get('channel_id'), 'entries':raw},ensure_ascii=False,indent=2),encoding='utf-8')
  candidates=[e for e in raw if (e.get('duration') or 0)>=2400 and not re.search(r'\b(MMA Show|Fight Companion|live stream)\b',e.get('title',''),re.I)]
  seeds=list(EVERGREEN[family])
  # Selection across subjects, not a guarantee that these episodes contain usable shorts.
  preference=re.compile(r'Carr|Hudson|Greene|Hormozi|Manson|Neumann|McConaughey|Smith|parent|life|friend|family|confidence|regret|Caleb|Robbins|Sutherland|Bumstead',re.I)
  ranked=sorted(enumerate(candidates),key=lambda z:(not bool(preference.search(z[1].get('title',''))),z[0]))
  for _,e in ranked:
   target='https://www.youtube.com/watch?v='+e['id']
   if target not in seeds: seeds.append(target)
   if len(seeds)>=quota:break
  data=discover.collect(seeds[:quota],1)
  identity={'family':family,'channel_url':url,'channel_id':listing.get('channel_id'),'title':listing.get('title'),'listing_limit':60,'chosen_limit':quota,'ownership':'creator channel identity; website corroboration recorded separately'}
  for e in data['episodes']:
   e['source_family']=family
   e['channel_identity_matches_listing']=e.get('channel_id')==listing.get('channel_id')
   if not e['channel_identity_matches_listing']: e['source_verification']='channel_mismatch_requires_review'
   else:e['source_verification']='original_channel_metadata_verified'
  saved={**data,'source':identity}; checkpoint.write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
  episodes.extend(data['episodes']); listings.extend(data['listings']); manifest.append(identity)
  print(f'{family}: {len(data["episodes"])} originals catalogued',flush=True)
 except Exception as exc:
  listings.append({'url':url,'status':discover.error_status(str(exc)),'errors':[{'reason':discover.safe_error(exc)}]})
  print(f'{family}: {type(exc).__name__}',flush=True)
 result={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'media_downloaded':False,
  'sources':manifest,'listings':listings,'episodes':list({e['key']:e for e in episodes}.values()),'scope':'50 selected episodes; bounded channel listings, not full back-catalogue coverage'}
 discover.write_catalogue(P/'catalogue.json',result)
print('TOTAL',len(episodes),flush=True)
