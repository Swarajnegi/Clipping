"""Download three bounded, owner-authorized original source passages."""
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,ffmpeg_command,probe,require_guard

WINDOWS=[('confidence',1560,1610),('pursuit',2450,2505),('parenthood',2909,2968)]

def main():
    require_guard(gpu=True)
    import yt_dlp
    from yt_dlp.utils import download_range_func
    folder=HERE/'source'
    folder.mkdir(exist_ok=True)
    for name,start,end in WINDOWS:
        path=folder/(name+'.mp4')
        if path.exists():raise RuntimeError('Source exists; inspect before replacing: '+str(path))
        opts={'outtmpl':str(folder/(name+'.%(ext)s')),
              'format':'bv*[width<=1920][height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[width<=1920][height<=1080]+ba/b[width<=1920]',
              'merge_output_format':'mp4','ffmpeg_location':str(ROOT/'.runtime/ffmpeg/bin'),
              'cachedir':str(ROOT/'.runtime/downloads/yt-dlp'),'remote_components':['ejs:github'],
              'js_runtimes':{'node':{'path':str(ROOT/'.runtime/node/node.exe')}},
              'retries':0,'fragment_retries':0,'extractor_retries':0,'socket_timeout':20,
              'download_ranges':download_range_func(None,[(start,end)]),
              'external_downloader_args':{'ffmpeg':['-threads','2','-filter_threads','2','-filter_complex_threads','2','-hide_banner','-loglevel','error']}}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info('https://www.youtube.com/watch?v=DHWEqlG7DI0',download=True)
        media=probe(path)
        receipt={'id':name,'path':str(path),'original_url':info['webpage_url'],'platform_id':info['id'],
                 'source_start':start,'source_end':end,'duration':media.duration,'width':media.width,
                 'height':media.height,'fps':media.fps,'rate':media.rate,'has_audio':media.has_audio,
                 'format':info.get('format_id'),'reuse_basis':json.loads((HERE/'brief.json').read_text())['reuse_basis']}
        (folder/(name+'.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        images=HERE/'source-frames'/name
        images.mkdir(parents=True,exist_ok=True)
        for index,t in enumerate([0.5,10,25,40,min(55,media.duration-0.2)]):
            subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(path),'-frames:v','1','-vf','scale=960:-2',str(images/f'{index:02d}.jpg')]),check=True)
        print('ACQUIRED',json.dumps(receipt),flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
