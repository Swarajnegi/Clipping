"""Audience snapshots and owner selection. Legacy --avd is percentage viewed, not seconds."""
from __future__ import annotations
import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT, WORK
LOG=ROOT/'results.jsonl'
SELECTION_LOG=ROOT/'selection-results.jsonl'

def number(value):
    value=float(value)
    if not math.isfinite(value) or value<0:raise argparse.ArgumentTypeError('Expected finite nonnegative number')
    return value

def percentage(value):
    value=number(value)
    if value>100:raise argparse.ArgumentTypeError('Expected 0–100 percent')
    return value

def count(value):
    value=int(value)
    if value<0:raise argparse.ArgumentTypeError('Count must be nonnegative')
    return value

def clip_facts(ref):
    if not re.fullmatch(r'[A-Za-z0-9_-]+/clip_\d+',ref):return {}
    vid,name=ref.split('/');props=WORK/vid/'props'/(name+'.json');spec=WORK/vid/'clips.json';facts={}
    if props.exists():
        p=json.loads(props.read_text(encoding='utf-8'))
        facts.update(length=p.get('durationSec'),style=p.get('style'),hook=p.get('hook'),intro=bool(p.get('intro')),music=bool(p.get('music')))
    if spec.exists():
        n=int(name.split('_')[1]);c=next((c for c in json.loads(spec.read_text(encoding='utf-8'))['clips'] if c.get('n')==n),{})
        facts.update(type=c.get('type'),title=c.get('title'))
    return facts

def append(path,row):
    with path.open('a+b') as f:
        if os.name=='nt':
            import msvcrt
            f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(f,fcntl.LOCK_EX)
        try:
            f.seek(0,2)
            if f.tell():
                f.seek(-1,2)
                if f.read(1)!=b'\n':f.seek(0,2);f.write(b'\n')
            f.seek(0,2);f.write((json.dumps(row,ensure_ascii=False)+'\n').encode('utf-8'));f.flush()
        finally:
            if os.name=='nt':f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f,fcntl.LOCK_UN)

def audience_row(args):
    legacy=getattr(args,'avd',None);explicit=getattr(args,'average_percentage_viewed',None)
    if legacy is not None and explicit is not None and legacy!=explicit:raise ValueError('--avd and --average-percentage-viewed conflict')
    pct=explicit if explicit is not None else legacy
    return {'url':args.url,'clip':args.clip,'stayed':args.stayed,'avd':pct,'average_percentage_viewed':pct,
      'avg_view_duration_seconds':getattr(args,'avg_view_duration_seconds',None),'views':args.views,'hours':args.hours,
      'engaged_views':getattr(args,'engaged_views',None),'shares':getattr(args,'shares',None),
      'subscribers_gained':getattr(args,'subscribers',None),'logged':datetime.now(timezone.utc).isoformat(timespec='seconds'),**clip_facts(args.clip)}

def load(path):
    if not path.exists():return []
    result=[]
    for n,line in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        try:result.append(json.loads(line))
        except json.JSONDecodeError:print(f'Invalid result record {path.name}:{n}; omitted',file=sys.stderr)
    return result

def snapshots(rows,hours=None,tolerance=6):
    chosen={}
    for row in rows:
        if not row.get('url'):continue
        age=row.get('hours')
        if hours is not None:
            if age is None or abs(age-hours)>tolerance:continue
            key=row['url'];old=chosen.get(key)
            if old and abs(old['hours']-hours)<abs(age-hours):continue
        else:key=(row['url'],age)
        chosen[key]=row
    return list(chosen.values())

def selection_summary(rows):
    latest={}
    for row in rows:latest[(row.get('project'),row['clip'])]=row
    decided=[r for r in latest.values() if r['decision']!='pending'];accepted=[r for r in decided if r['decision']=='accepted'];excerpts=[r for r in decided if r['decision']=='excerpt_only']
    timed=bool(decided) and all(r.get('production_minutes') is not None for r in decided)
    minutes=sum(r['production_minutes'] for r in decided) if timed else None
    return {'decided':len(decided),'accepted':len(accepted),'excerpt_only':len(excerpts),
      'acceptance_rate':len(accepted)/len(decided) if decided else None,'production_minutes':minutes,
      'minutes_per_accepted_clip':minutes/len(accepted) if minutes is not None and accepted else None}

def fmt(value,digits=1):return 'N/A' if value is None else f'{value:,.{digits}f}'

def report(hours=None,tolerance=6):
    rows=snapshots(load(LOG),hours,tolerance)
    if not rows:print('No audience snapshots in this publication-age window.')
    for age in sorted({r.get('hours') for r in rows},key=lambda x:-1 if x is None else x):
        print(f'\nPublication age: {fmt(age)} hours (no universal pass threshold)')
        print('views | stayed % | avg seconds | viewed % | clip')
        for r in sorted((r for r in rows if r.get('hours')==age),key=lambda x:-(x.get('views') or 0)):
            pct=r.get('average_percentage_viewed',r.get('avd'))
            print(f"{fmt(r.get('views'),0)} | {fmt(r.get('stayed'))} | {fmt(r.get('avg_view_duration_seconds'))} | {fmt(pct)} | {r['clip']}")
    print('\nOwner selection (separate from audience performance):')
    print(json.dumps(selection_summary(load(SELECTION_LOG)),indent=2))

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add');a.add_argument('url');a.add_argument('--clip',required=True)
    a.add_argument('--stayed',type=percentage);a.add_argument('--avd',type=number,help='Legacy average percentage viewed; may exceed 100')
    a.add_argument('--average-percentage-viewed',type=number);a.add_argument('--avg-view-duration-seconds',type=number)
    a.add_argument('--views',type=count);a.add_argument('--engaged-views',type=count);a.add_argument('--shares',type=count);a.add_argument('--subscribers',type=count)
    a.add_argument('--hours',type=number,default=48)
    s=sub.add_parser('selection');s.add_argument('--clip',required=True);s.add_argument('--project',required=True)
    s.add_argument('--decision',choices=('accepted','rejected','excerpt_only','pending'),required=True)
    s.add_argument('--reason',required=True);s.add_argument('--production-minutes',type=number)
    r=sub.add_parser('report');r.add_argument('--hours',type=number);r.add_argument('--tolerance-hours',type=number,default=6)
    args=ap.parse_args()
    if args.cmd=='add':
        try:row=audience_row(args)
        except ValueError as exc:ap.error(str(exc))
        append(LOG,row);print('Logged audience snapshot; legacy avd is percentage viewed.')
    elif args.cmd=='selection':
        append(SELECTION_LOG,{'project':args.project,'clip':args.clip,'decision':args.decision,'reason':args.reason,
         'production_minutes':args.production_minutes,'logged':datetime.now(timezone.utc).isoformat(timespec='seconds')})
        print('Logged owner selection; no audience metrics inferred.')
    else:report(args.hours,args.tolerance_hours)
    return 0

if __name__=='__main__':raise SystemExit(main())
