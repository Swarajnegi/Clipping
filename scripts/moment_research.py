"""Reusable transcript discovery, not automatic editorial selection.

Metadata/captions only: fetch -> identity-bound JSON -> SQLite search -> validate authored bank.
All writes stay inside Clipping. No video, models, providers or production renders.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from common import ROOT
from discover import error_status, safe_error

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save(path, value):
    path=Path(path).resolve(); path.relative_to(ROOT.resolve()); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp'); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); tmp.replace(path)

def normal(text):
    return ' '.join(re.findall(r"[\w']+",html.unescape(text).lower().replace('’',"'")))

def json3_segments(data):
    result=[]
    for event in data.get('events',[]):
        text=' '.join(html.unescape(''.join(s.get('utf8','') for s in event.get('segs',[]))).split())
        if not text:continue
        start=float(event.get('tStartMs',0))/1000
        end=start+float(event.get('dDurationMs',0))/1000
        if not (math.isfinite(start) and math.isfinite(end) and 0<=start<end):continue
        row={'start':start,'end':end,'text':text}
        if result and row==result[-1]:continue
        result.append(row)
    return sorted(result,key=lambda x:x['start'])

def fetch_caption(episode):
    """One bounded attempt. Signed caption URLs never enter the saved record."""
    from yt_dlp import YoutubeDL
    record={'key':episode['key'],'canonical_url':episode['canonical_url'],'video_id':episode['video_id'],
            'retrieved_at':datetime.now(timezone.utc).isoformat(),'status':'not_checked','segments':[]}
    opts={'quiet':True,'no_warnings':True,'skip_download':True,'cachedir':False,'noplaylist':True,
          'socket_timeout':20,'retries':0,'extractor_retries':0,
          'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}}}
    try:
        with YoutubeDL(opts) as y: info=y.extract_info(episode['canonical_url'],download=False)
        if str(info.get('id'))!=episode['video_id']:raise ValueError('Source identity mismatch')
        record['channel_id']=info.get('channel_id')
        if episode.get('channel_id') and record['channel_id']!=episode['channel_id']:raise ValueError('Channel identity mismatch')
        chosen=None
        for kind in ('subtitles','automatic_captions'):
            captions=info.get(kind) or {}
            for lang in ('en-orig','en','en-US','en-GB'):
                choices=[s for s in captions.get(lang,[]) if s.get('ext')=='json3']
                if choices:chosen=(kind,lang,choices[0]);break
            if chosen:break
        if not chosen:
            record['status']='none_reported' if not (info.get('subtitles') or info.get('automatic_captions')) else 'no_supported_english_json3'
            return record
        kind,lang,item=chosen
        request=Request(item['url'],headers={'User-Agent':'Mozilla/5.0'})
        with urlopen(request,timeout=20) as response: payload=response.read(8_000_001)
        if len(payload)>8_000_000:raise ValueError('Caption response exceeded 8 MB bound')
        record.update(status='available',caption_kind=kind,language=lang,
                      body_sha256=hashlib.sha256(payload).hexdigest(),segments=json3_segments(json.loads(payload)))
        if not record['segments']:record['status']='empty_response'
    except Exception as exc:
        record.update(status='retrieval_failed',access_status=error_status(str(exc)),error=safe_error(exc))
    return record

def build_index(catalogue, records, database):
    database=Path(database).resolve();database.relative_to(ROOT.resolve());database.parent.mkdir(parents=True,exist_ok=True)
    episodes={e['key']:e for e in catalogue['episodes']}
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS episodes (key TEXT PRIMARY KEY, url TEXT, title TEXT, status TEXT, segments TEXT)')
        db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5(key UNINDEXED, start UNINDEXED, end UNINDEXED, text)')
        for record in records:
            key=record['key'];episode=episodes[key]
            if record['canonical_url']!=episode['canonical_url']:raise ValueError('Transcript source URL mismatch')
            segments=record.get('segments',[])
            for row in segments:
                if not (math.isfinite(row['start']) and math.isfinite(row['end']) and 0<=row['start']<row['end']):raise ValueError('Invalid transcript timestamp')
                if episode.get('duration') and row['start']>episode['duration']+2:raise ValueError('Transcript outside source duration')
            db.execute('DELETE FROM passages WHERE key=?',(key,))
            db.execute('INSERT OR REPLACE INTO episodes VALUES (?,?,?,?,?)',(key,episode['canonical_url'],episode.get('title'),record['status'],json.dumps(segments)))
            # Non-overlapping ~25-second blocks; search returns surrounding context separately.
            group=[]
            for segment in sorted(segments,key=lambda x:x['start']):
                if group and segment['start']-group[0]['start']>=25:
                    db.execute('INSERT INTO passages VALUES (?,?,?,?)',(key,group[0]['start'],max(x['end'] for x in group),' '.join(x['text'] for x in group)));group=[]
                group.append(segment)
            if group:db.execute('INSERT INTO passages VALUES (?,?,?,?)',(key,group[0]['start'],max(x['end'] for x in group),' '.join(x['text'] for x in group)))

def search(database,query,limit=20,context=30,phrase=False):
    tokens=re.findall(r"[\w']+",query)
    if not tokens:return []
    expression='"'+' '.join(tokens)+'"' if phrase else ' OR '.join('"'+x+'"' for x in tokens[:30])
    result=[]
    with closing(sqlite3.connect(f'file:{Path(database).resolve().as_posix()}?mode=ro',uri=True)) as db:
        for key,start,end,text in db.execute('SELECT key,start,end,text FROM passages WHERE passages MATCH ? ORDER BY rank LIMIT ?',(expression,limit)):
            url,title,status,raw=db.execute('SELECT url,title,status,segments FROM episodes WHERE key=?',(key,)).fetchone()
            around=[s for s in json.loads(raw) if s['end']>=float(start)-context and s['start']<=float(end)+context]
            result.append(dict(key=key,url=url,title=title,start=float(start),end=float(end),text=text,context=around,caption_status=status))
    return result

def validate_bank(bank,catalogue,transcripts):
    episodes={e['key']:e for e in catalogue['episodes']}; records={r['key']:r for r in transcripts};errors=[]; seen={};prior=[]
    for item in bank:
        label=item.get('id','unnamed'); key=item.get('source_key'); episode=episodes.get(key)
        if not episode:errors.append(f'{label}: unknown source');continue
        if item.get('source_url')!=episode['canonical_url']:errors.append(f'{label}: source identity mismatch')
        spans=item.get('segments',[])
        if not spans:errors.append(f'{label}: missing cuts');continue
        duration=episode.get('duration')
        valid=isinstance(duration,(int,float)) and math.isfinite(duration) and all(isinstance(s,list) and len(s)==2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in s) and 0<=s[0]<s[1]<=duration for s in spans)
        if not valid:errors.append(f'{label}: invalid source range');continue
        fingerprint=(key,tuple(tuple(s) for s in spans))
        if fingerprint in seen:errors.append(f'{label}: duplicate moment of {seen[fingerprint]}')
        seen[fingerprint]=label
        for previous_key,previous_spans,previous_label in prior:
            overlap=sum(max(0,min(b,d)-max(a,c)) for a,b in spans for c,d in previous_spans)
            shorter=min(sum(b-a for a,b in spans),sum(d-c for c,d in previous_spans))
            if previous_key==key and overlap/shorter>=.8 and fingerprint!=(key,tuple(tuple(s) for s in previous_spans)):
                errors.append(f'{label}: near-duplicate moment of {previous_label}')
        prior.append((key,spans,label))
        record=records.get(key,{})
        wording=' '.join(s['text'] for a,b in spans for s in record.get('segments',[]) if s['start']<b and s['end']>a)
        hook=normal(item.get('opening',''))
        if not hook or hook not in normal(wording):errors.append(f'{label}: opening not supported by selected transcript')
        for field in ('context','payoff','cut_proposal','benchmark','risks'):
            if not item.get(field):errors.append(f'{label}: missing {field}')
        gates=item.get('checks',{})
        if set(gates)!={'opening','progression','delivery','payoff','channel_fit'} or any(v not in ('pass','reject','pending') for v in gates.values()):errors.append(f'{label}: incomplete editorial checks')
        review=item.get('av_review',{})
        covered=review.get('full_passage') is True and review.get('audio') is True and bool(review.get('method')) and bool(review.get('evidence'))
        if gates.get('delivery')=='pass' and not covered:errors.append(f'{label}: fluency claimed without audiovisual evidence')
        status=item.get('status')
        if status not in ('transcript_shortlist','reviewed','production_ready','rejected'):errors.append(f'{label}: invalid selection status')
        if status in ('reviewed','production_ready') and (not covered or any(v!='pass' for v in gates.values())):errors.append(f'{label}: approval before checks pass')
        if status=='production_ready' and item.get('reuse_basis') in (None,'','unknown'):errors.append(f'{label}: missing reuse basis')
    return errors

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    f=sub.add_parser('fetch');f.add_argument('--catalogue',type=Path,required=True);f.add_argument('--keys',nargs='+',required=True);f.add_argument('--output',type=Path,required=True)
    i=sub.add_parser('index');i.add_argument('--catalogue',type=Path,required=True);i.add_argument('--transcripts',type=Path,required=True);i.add_argument('--database',type=Path,required=True)
    s=sub.add_parser('search');s.add_argument('--database',type=Path,required=True);s.add_argument('--query',required=True);s.add_argument('--limit',type=int,default=20);s.add_argument('--context',type=float,default=30);s.add_argument('--phrase',action='store_true');s.add_argument('--output',type=Path)
    v=sub.add_parser('validate');v.add_argument('--catalogue',type=Path,required=True);v.add_argument('--transcripts',type=Path,required=True);v.add_argument('--bank',type=Path,required=True)
    args=ap.parse_args()
    if args.command=='fetch':
        if len(args.keys)>20:ap.error('Fetch at most 20 selected episodes per invocation')
        args.output.resolve().relative_to(ROOT.resolve())
        episodes={e['key']:e for e in read(args.catalogue)['episodes']}
        for key in dict.fromkeys(args.keys):
            if key not in episodes:ap.error('Unknown source '+key)
            path=args.output/(key.replace(':','_')+'.json')
            if path.exists():
                cached=read(path)
                if cached['key']!=key or cached['canonical_url']!=episodes[key]['canonical_url']:raise ValueError('Cache identity mismatch')
                print(key,cached['status'],'cached',flush=True);continue
            record=fetch_caption(episodes[key]);save(path,record);print(key,record['status'],len(record['segments']),flush=True)
    elif args.command=='index':
        records=[read(p) for p in args.transcripts.glob('*.json')];build_index(read(args.catalogue),records,args.database);print('Indexed records:',len(records))
    elif args.command=='search':
        if not 1<=args.limit<=100 or not 0<=args.context<=180:ap.error('Invalid search bounds')
        rows=search(args.database,args.query,args.limit,args.context,args.phrase)
        if args.output:save(args.output,rows)
        else:print(json.dumps(rows,ensure_ascii=False,indent=2))
    else:
        errors=validate_bank(read(args.bank),read(args.catalogue),[read(p) for p in args.transcripts.glob('*.json')])
        print(json.dumps({'passed':not errors,'errors':errors},indent=2));return 1 if errors else 0
    return 0

if __name__=='__main__':raise SystemExit(main())
