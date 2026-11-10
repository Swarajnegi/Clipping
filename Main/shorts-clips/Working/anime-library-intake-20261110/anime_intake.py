"""Guarded intake for local 10-bit H.264 anime scenepacks."""
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
LIBRARY = WORK.parents[1] / "Anime Clips"
PACKS = {
    "sukuna": ("Sukuna All Scenes - Jujutsu Kaisen S02 (English) - [REMUX 1080p h264] - Petereditzx7.mp4",
               "Jujutsu Kaisen - Sukuna S02"),
    "toji": ("Toji Fushiguro All Scenes - Jujutsu Kaisen S02 (English) - [REMUX 1080p h264] - Petereditzx7.mp4",
             "Jujutsu Kaisen - Toji Fushiguro S02"),
    "gojo": ("Satoru Gojo All Scenes - Jujutsu Kaisen S02 (Japanese) - [REMUX 1080p h264] - Petereditzx7.mp4",
             "Jujutsu Kaisen - Satoru Gojo S02"),
    "eren": ("Eren Jaeger - Part A - Attack On Titan S04 (2023) - (1080p REMUX H264) - sill7rr.mp4",
             "Attack on Titan - Eren Jaeger S04A"),
}
sys.path.insert(0, str(WORK.parent / "movie-library-intake-20261109"))
import pack_intake as base
base.WORK = WORK
base.MOVIES = LIBRARY
import screen_packs as screen
from common import FFMPEG, FFPROBE, ffmpeg_command, require_guard
from movie_library import CUES, inventory

WIDTH, HEIGHT, SPAN = 128, 72, 180
DISK_RESERVE = 4 * 1024**3

def ensure_space():
    if shutil.disk_usage(LIBRARY).free < DISK_RESERVE:
        raise RuntimeError("The four GiB disk reserve is unavailable")

def ff(*args):
    cmd=ffmpeg_command([FFMPEG,"-hide_banner","-nostats","-xerror",*map(str,args)])
    p=subprocess.run(cmd,capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-4000:])
    return p

def identify(name):
    source=LIBRARY/PACKS[name][0]
    st=source.stat()
    v=base.source_stream(source)
    assert v["codec_name"]=="h264" and v["pix_fmt"]=="yuv420p10le"
    assert v["r_frame_rate"]==v["avg_frame_rate"] and float(v["start_time"])==0
    return source,dict(name=source.name,bytes=st.st_size,mtime_ns=st.st_mtime_ns,
                       video_seconds=float(v["duration"]),width=v["width"],height=v["height"],
                       rate=v["r_frame_rate"],pixel_format=v["pix_fmt"],codec=v["codec_name"],
                       block_seconds=SPAN,scan_mode="Source keyframes, guarded software decode")

def frames(source,start,length,keys=True):
    discard=("-discard:v","nokey") if keys else ()
    scale=f"scale={WIDTH}:{HEIGHT}:flags=area,format=rgb24"
    filt=f"{scale},showinfo" if keys else f"fps=3,{scale},showinfo"
    p=ff("-v","info","-ss",f"{start:.6f}",*discard,"-i",source,
         "-t",f"{length:.6f}","-map","0:v:0","-an","-sn","-dn","-vf",filt,
         "-fps_mode","passthrough","-f","rawvideo","-")
    rgb=np.frombuffer(p.stdout,np.uint8).reshape(-1,HEIGHT,WIDTH,3)
    seconds=[start+float(x) for x in base.SHOW.findall(p.stderr.decode(errors="replace"))][:len(rgb)]
    if not len(rgb) or len(seconds)!=len(rgb):
        raise RuntimeError(f"No matching frames at {source.name} {start:.3f}")
    return np.array(seconds),rgb

def boards(name):
    w=WORK/name
    packet=base.load(w/"candidates.json")
    candidates=packet["candidates"]
    # Spread human review across the full pack, with short and long scenes represented.
    bins={}
    for row in candidates:
        window=int(row["sample_time"]//32)
        # Prefer a usable 3–8 second beat over a thin or low-detail flash.
        value=row["score"] + min(row["motion_score"],12)*.075
        if window not in bins or value>bins[window][0]:
            bins[window]=(value,row)
    selected=[item[1] for _,item in sorted(bins.items())]
    indices={row["sample_index"]:row["id"] for row in selected}
    images={}
    offset=0
    for p in sorted(w.glob("block-*.npz")):
        with np.load(p) as b:
            rgb=b["frames"]
        for i,im in enumerate(rgb,offset):
            if i in indices:
                images[indices[i]]=Image.fromarray(im)
        offset+=len(rgb)
    assert len(images)==len(selected)
    for n in range(0,len(selected),48):
        page=selected[n:n+48]
        sheet=Image.new("RGB",(8*160,math.ceil(len(page)/8)*108),"#14171a")
        draw=ImageDraw.Draw(sheet)
        for i,row in enumerate(page):
            x,y=i%8*160,i//8*108
            draw.text((x+3,y+1),f"{row['id']:04} {row['sample_time']:.1f}s",fill="white")
            sheet.paste(images[row["id"]].resize((160,90),Image.Resampling.LANCZOS),(x,y+17))
        sheet.save(w/f"review-{n//48+1:02}.jpg",quality=92)
    base.save(w/"review-bank.json",selected)
    print("REVIEW_BANK",name,len(selected),"/",len(candidates),flush=True)

def scan(name):
    ensure_space()
    source,rec=identify(name)
    w=WORK/name
    w.mkdir(exist_ok=True)
    meta=w/"source.json"
    if meta.exists() and base.load(meta)!=rec:
        raise ValueError(f"Source changed: {source}")
    base.save(meta,rec)
    count=math.ceil(rec["video_seconds"]/SPAN)
    for i in range(count):
        out=w/f"block-{i:04}.npz"
        if out.exists():
            continue
        ensure_space()
        start=i*SPAN
        t,rgb=frames(source,start,min(SPAN,rec["video_seconds"]-start))
        assert t[0]-start<3 and np.all(np.diff(t)>0), (name,i,t[:4])
        with out.with_suffix(".tmp").open("wb") as f:
            np.savez_compressed(f,times=t,frames=rgb)
        out.with_suffix(".tmp").replace(out)
        if i==0 or (i+1)%5==0 or i+1==count:
            print("SCAN",name,i+1,count,len(t),flush=True)
    screen.candidates(name)
    boards(name)

if __name__=="__main__":
    require_guard()
    for name in sys.argv[1:] or PACKS:
        scan(name)
