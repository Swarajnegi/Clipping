import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

W = Path(__file__).resolve().parent
ROOT = W.parents[3]
MOVIES = W.parents[1]/"Movie Clips"
sys.path.insert(0, str(ROOT/"scripts"))
from common import FFMPEG, ffmpeg_command, require_guard

SCANS = {"Avengers Endgame - Steve Rogers":"steve", "Breaking Bad - Walter White S05A":"walter",
         "Daredevil - Matt Murdock S02":"matt", "Peaky Blinders - Tommy Shelby S04":"tommy-s04",
         "Peaky Blinders - Tommy Shelby S06":"tommy-s06"}

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path, value):
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    temp.replace(path)

def board(cells, output, width=142, height=80, cols=8):
    n=(len(cells)+cols-1)//cols
    canvas=Image.new("RGB",(cols*width,n*(height+17)),"#15191c")
    draw=ImageDraw.Draw(canvas)
    for i,(label,image) in enumerate(cells):
        x,y=i%cols*width,i//cols*(height+17)
        draw.text((x+3,y+1),label,fill="white")
        if image:
            image.thumbnail((width,height), Image.Resampling.LANCZOS)
            canvas.paste(image,(x+(width-image.width)//2,y+17+(height-image.height)//2))
    canvas.save(output,quality=89)

def pilot():
    require_guard(gpu=True)
    rows=[]
    for p in sorted(MOVIES.glob("*/catalogue.json")):
        cat=read(p)
        clips=cat["clips"]
        generic=next((c for c in clips if c["file"].endswith(("-active-shot.mp4","-steady-shot.mp4"))),None)
        chosen=[clips[len(clips)//2],generic or clips[len(clips)//4]]
        samples=[]
        for i,c in enumerate(chosen, 1):
            file=p.parent/c["file"]
            times=[round(c["duration"]*f,3) for f in (.15,.5,.85)]
            width,height=176,round(176*cat["source_resolution"][1]/cat["source_resolution"][0]/2)*2
            for t in times:
                command=[FFMPEG,"-v","error","-xerror","-hwaccel","cuda","-hwaccel_output_format","cuda",
                         "-ss",str(t),"-i",str(file),"-map","0:v:0","-vf",
                         f"scale_cuda={width}:{height}:format=nv12,hwdownload,format=nv12,format=rgb24",
                         "-frames:v","1","-f","rawvideo","-"]
                raw=subprocess.check_output(ffmpeg_command(command))
                samples.append((f"{c.get('candidate_id', i):04} {t:.2f}s",Image.frombytes("RGB",(width,height),raw)))
            rows.append({"id":p.parent.name+"/"+c["file"],"excerpt_seconds":times,"sheet":f"pilot-{len(rows)//2:02}.jpg"})
        board(samples,W/rows[-1]["sheet"],width=190,height=110,cols=3)
        print("PILOT",p.parent.name,flush=True)
    save(W/"pilot.json",rows)

def cached():
    require_guard(gpu=True)
    import numpy as np
    for title,name in SCANS.items():
        pack=W.parent/"movie-library-intake-20261109"/name
        cat=read(MOVIES/title/"catalogue.json")
        scan=read(pack/"source.json")
        assert cat["source"]==scan["name"] and cat["source_bytes"]==scan["bytes"]
        rows=[c for c in cat["clips"] if c["file"].endswith(("-steady-shot.mp4","-active-shot.mp4"))]
        # Read existing small scan blocks once. A frame must lie inside the saved excerpt.
        with_times=[]
        for block in sorted(pack.glob("block-*.npz")):
            with np.load(block) as loaded:
                t=loaded["times"]
                with_times.append((t,loaded["frames"],block))
        cells=[]
        records=[]
        for c in rows:
            start,end=c["source_start"],c["source_end_exclusive"]
            best=None
            for t,frames,block in with_times:
                if t[-1]<start or t[0]>=end:
                    continue
                a,b=np.searchsorted(t,[start,end])
                if a>=b:
                    continue
                k=a+int(np.argmin(abs(t[a:b]-(start+end)/2)))
                distance=abs(float(t[k])-(start+end)/2)
                if best is None or distance<best[0]:
                    best=(distance,float(t[k]),frames[k],block.name)
            image=Image.fromarray(best[2]) if best else None
            if image:
                width,height=cat["source_resolution"]
                image=image.resize((142,round(142*height/width)),Image.Resampling.LANCZOS)
            ident=c["candidate_id"]
            cells.append((str(ident),image))
            records.append({"candidate":ident,"id":title+"/"+c["file"],
                            "source_second":round(best[1],6) if best else None,
                            "block":best[3] if best else None,
                            "sheet":f"{name}-{len(records)//48+1:02}.jpg"})
        for i in range(0,len(cells),48):
            board(cells[i:i+48],W/f"{name}-{i//48+1:02}.jpg")
        save(W/f"{name}-evidence.json",records)
        print(name,len(cells),sum(r["source_second"] is None for r in records),flush=True)


def sample_ranges(selections, output):
    require_guard(gpu=True)
    records=[]
    for title, suffixes in selections.items():
        cat=read(MOVIES/title/"catalogue.json")
        width=240
        height=round(width*cat["source_resolution"][1]/cat["source_resolution"][0]/2)*2
        for suffix in suffixes:
            clip,=[c for c in cat["clips"] if c["file"].endswith(suffix)]
            source=MOVIES/title/clip["file"]
            command=[FFMPEG,"-v","error","-xerror","-hwaccel","cuda","-hwaccel_output_format","cuda",
                     "-i",str(source),"-map","0:v:0","-vf",
                     f"fps=2,scale_cuda={width}:{height}:format=nv12,hwdownload,format=nv12,format=rgb24",
                     "-f","rawvideo","-"]
            raw=subprocess.check_output(ffmpeg_command(command))
            size=width*height*3
            assert raw and len(raw)%size==0
            times=[i/2 for i in range(len(raw)//size)]
            cells=[(f"{t:.1f}s",Image.frombytes("RGB",(width,height),raw[i*size:(i+1)*size]))
                   for i,t in enumerate(times)]
            sheet=f"{output}-{len(records)+1:02}.jpg"
            board(cells,W/sheet,width=244,height=136,cols=4)
            records.append({"id":title+"/"+clip["file"],"excerpt_seconds":times,"sheet":sheet})
            print("SAMPLED",title,suffix,len(times),flush=True)
    save(W/f"{output}.json",records)


def editorial_examples():
    sample_ranges({
        "Avengers Endgame - Steve Rogers":["two-people-on-a-bench-outside.mp4",
            "steve-leans-forward-with-a-hand-on-his-head.mp4","tony-touches-the-arc-reactor.mp4"],
        "Blade Runner 2049 - Officer K":["officer-k-on-the-floor.mp4","joi-reaches-toward-officer-k.mp4",
            "hands-at-an-amber-work-table.mp4","hands-hold-a-small-object-in-amber-light.mp4"],
        "Fight Club":["embrace-at-the-support-group.mp4"],
        "Iron Man":["armored-helmet-in-rubble.mp4","yinsen-works-at-the-bench.mp4"],
        "Jon Snow":["jon-gets-back-up-in-training.mp4"],
        "Luke Glanton - The Place Beyond the Pines":["luke-catches-his-breath-on-the-floor.mp4",
            "luke-works-at-a-motorcycle.mp4"],
    }, "examples")


if __name__=="__main__":
    for mode in sys.argv[1:]:
        {"pilot":pilot,"cached":cached,"examples":editorial_examples}[mode]()
