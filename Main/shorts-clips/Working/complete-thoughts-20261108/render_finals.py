"""Guarded 4K stills, bounded picture chunks and packet-preserving final mux."""
import argparse,json,subprocess,sys
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parent;ROOT=P.parents[3];F=P/'finish-v1'
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard,NODE,REMOTION,FFMPEG,ffmpeg_command,probe
from motion_edit import audio_packets,decode
require_guard(gpu=True)
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['bundle','stills','chunk','mux'])
parser.add_argument('--id');parser.add_argument('--start',type=int);parser.add_argument('--end',type=int)
args=parser.parse_args()
if args.mode=='bundle':
 subprocess.run([str(NODE),str(REMOTION),'bundle','src/index.ts',f'--out-dir={F/"bundle"}'],cwd=ROOT,check=True)
 print('BUNDLE_READY',flush=True);sys.exit(0)
entry=str(F/'bundle') if (F/'bundle/index.html').exists() else 'src/index.ts'
proofs=json.loads((P/'proofs.json').read_text(encoding='utf-8'))
for r in proofs:
 id=r['id']
 if args.id and id!=args.id:continue
 path=F/'props'/(id+'.json');props=json.loads(path.read_text(encoding='utf-8'))
 shared=[f'--props={path}','--scale=2','--gl=angle','--offthreadvideo-video-threads=2',
  '--offthreadvideo-cache-size-in-bytes=134217728']
 if args.mode=='stills':
  moments={'01':3.8,'02':4.7,'03':1.6,'04':2.5,'05':2.7}
  dest=F/'qa'/(id+'-representative-4k.png')
  subprocess.run([str(NODE),str(REMOTION),'still',entry,'ViralShort',str(dest),
   f'--frame={round(moments[id[:2]]*r["fps"])}',*shared],cwd=ROOT,check=True)
  im=Image.open(dest);assert im.size==(2160,3840);im.resize((360,640)).save(F/'qa'/(id+'-representative-phone.png'))
  print('STILL',id,flush=True)
 elif args.mode=='chunk':
  a=args.start;b=min(args.end,r['frames']-1);assert 0<=a<=b<r['frames']
  dest=F/'finished'/(id+f'-part-{a:04d}-{b:04d}.mp4')
  if dest.exists():raise FileExistsError('Preserve existing chunk revision '+str(dest))
  subprocess.run([str(NODE),str(REMOTION),'render',entry,'ViralShort',str(dest),
   f'--frames={a}-{b}','--concurrency=1','--hardware-acceleration=required',
   '--video-bitrate=40M','--image-format=jpeg','--jpeg-quality=100','--muted',*shared],cwd=ROOT,check=True)
  decode(dest,b-a+1)
  (dest.with_suffix('.json')).write_text(json.dumps({'start':a,'end':b,'frames':b-a+1,'rate':r['rate'],
    'original_timeline_frame_range':True,'decoded':True},indent=2),encoding='utf-8')
  print('CHUNK',id,a,b,flush=True)
 elif args.mode=='mux':
  parts=sorted((F/'finished').glob(id+'-part-*.mp4'));cursor=0
  for part in parts:
   receipt=json.loads(part.with_suffix('.json').read_text());assert receipt['start']==cursor and receipt['decoded']
   cursor=receipt['end']+1
  assert cursor==r['frames']
  listing=F/'finished'/(id+'-concat.txt')
  listing.write_text('\n'.join("file '"+str(p.resolve()).replace('\\','/')+"'" for p in parts),encoding='utf-8')
  dest=F/'finished'/(id+'-music-free.mp4');master=ROOT/'public'/props['src']
  if dest.exists():raise FileExistsError('Preserve existing final revision '+id)
  subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-f','concat','-safe','0','-i',str(listing),
   '-i',str(master),'-map','0:v:0','-map','1:a:0','-c','copy','-map_metadata','-1',
   '-movflags','+faststart',str(dest)]),check=True)
  assert audio_packets(master)==audio_packets(dest)
  d=decode(dest,r['frames']);m=probe(dest);assert (m.width,m.height)==(2160,3840) and m.rate==r['rate']
  (F/'qa'/(id+'-technical.json')).write_text(json.dumps({'file':str(dest),'decode':d,'frames':r['frames'],
   'rate':r['rate'],'duration':r['duration'],'dimensions':[2160,3840],
   'audio_payload_and_packet_timestamps_equal_to_approved_clean_assembly':True,'music_added':False,
   'sfx_added':False,'narration_added':False,'channel_symbol':None},indent=2),encoding='utf-8')
  print('FINAL',id,flush=True)
  subprocess.run([sys.executable,str(P/'qa_finished.py'),'--id',id],check=True)
  subprocess.run([sys.executable,str(P/'make_thumbnails.py'),'--id',id],check=True)
  if id.startswith('05'):
   subprocess.run([sys.executable,str(P/'make_thumbnails.py'),'--id','04-robbins-proving-your-worth'],check=True)
  print('FINAL_QA_AND_COVER',id,flush=True)
