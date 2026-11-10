"""Render only the film inserts, then restore the exact approved dialogue."""
import os
import sys
from fractions import Fraction
from pathlib import Path

import cv2

from cutaway_plan import CUTS
from finish import P, ROOT, F, FONT_DIR, NODE, REMOTION, audio_packets, cool, decode, ff, preferred_position, probe, read
from finish import require_guard, roughs, samples, save, video_clock

WORK = P / "movie-cutaways"
PUBLIC = WORK / "public"
QA = WORK / "qa"
REVIEW = WORK / "review"
PARTS = WORK / "parts"
BUNDLE = WORK / "bundle"
sys.path.insert(0,str(WORK.parent.parent/"complete-thoughts-movie-cutaways-20261110"))
import edit as prior
from build import validate_reference_edit

prior.QA = QA

def join_list(parts, fps, listing):
    listing.write_text("\n".join(f"file '{path.as_posix()}'\nduration {n/fps:.9f}"
                                 for path,n in parts)+"\n",encoding="utf-8")

def normalize(source, first, count, item, dest, *, square=False, shot=None):
    if dest.exists():
        return
    cool()
    fps = item["fps"]
    pts = shot["offset"] if shot else max(0,first/fps-.000001)
    temp = dest.with_name(dest.stem+".partial.mp4")
    filters = "scale_cuda=format=nv12,hwdownload,format=nv12"
    if shot:
        filters += (f",crop={shot['side']}:{shot['side']}:{shot['left']}:{shot['top']},"
                    f"scale=980:980:flags=lanczos,setsar=1,fps={item['rate']},"
                    f"tpad=stop_mode=clone:stop=1")
    ff("-y","-hwaccel","cuda","-hwaccel_output_format","cuda","-ss",f"{pts:.7f}","-i",source,
       "-map","0:v:0","-an","-sn","-vf",filters,"-frames:v",count,
       "-c:v","h264_nvenc","-preset","p4","-profile:v","high","-rc","vbr","-cq",17,"-b:v",0,
       "-maxrate","32M","-bufsize","64M","-bf",0,"-pix_fmt","nv12","-fps_mode","passthrough",
       "-video_track_timescale",Fraction(item["rate"]).numerator,temp)
    info = probe(temp)
    assert (info.width,info.height)==((980,980) if square else (1080,1920)),temp
    assert abs(info.duration-count/fps)<.002 and info.rate==item["rate"], (temp,info.duration,count)
    temp.replace(dest)

def bind_layers(placement, layers):
    cursor = 0
    bound = []
    for group in placement:
        words = []
        phrase = ""
        while phrase != group["text"]:
            layer = layers[cursor]
            words.append(layer)
            cursor += 1
            phrase = " ".join(w["text"] for w in words)
            assert group["text"].startswith(phrase), (group["text"],phrase)
        bound.append((group,words))
    assert cursor==len(layers)
    return bound

def caption_patch(placement, shot, segment, fps):
    start,stop = shot["start_frame"]/fps,shot["end_frame"]/fps
    offset = shot["montage_frame"]/fps
    views = [(t+start,img,faces) for t,img,faces in samples(segment)]
    result = []
    for group,words in placement:
        a,b = max(start,group["start"]),min(stop,group["end"])
        if b-a < .001:
            continue
        rows = [[]]
        top = words[0]["y"]
        for layer in words:
            if layer["y"]-top>48:
                rows.append([])
                top = layer["y"]
            rows[-1].append((layer,layer["size"],layer["font"],layer["weight"],layer["width"]))
        x,y,_,overlaps = preferred_position(rows,views,a,b,[])
        old_x,old_y = group["centre"]
        shot["caption_placements"].append(dict(text=group["text"],centre=[x,y],face_intersections=overlaps))
        for layer in words:
            lo,hi = max(start,layer["t"]),min(stop,layer["t"]+layer["dur"])
            if hi-lo>.001:
                result.append(dict(layer,t=lo-start+offset,dur=hi-lo,
                                   x=round(layer["x"]+x-old_x,2),y=round(layer["y"]+y-old_y,2)))
    return result

def prepare():
    for directory in (PUBLIC, QA, REVIEW, PARTS):
        directory.mkdir(parents=True,exist_ok=True)
    if not (PUBLIC/"fonts").exists():
        import shutil
        shutil.copytree(FONT_DIR,PUBLIC/"fonts")
    inventory = read(WORK/"candidate-review/inventory.json")
    cv2.setNumThreads(2)
    records = []
    for rough in roughs():
        ident = rough["id"]
        number = ident[:2]
        item = dict(id=ident, **rough["clock"])
        item["resolution"] = [1080,1920]
        fps = item["fps"]
        props = read(F/"props"/(ident+".json"))
        placement = bind_layers(read(F/"qa"/(ident+"-placement.json")),props["referenceEdit"]["layers"])
        video = PUBLIC/(number+"-montage.mp4")
        patches, layers, parts = [], [], []
        cursor = 0
        for index,(start,end,title,slug,offset,crop,reason) in enumerate(CUTS[number],1):
            a,b = round(start*fps),round(end*fps)
            n = b-a
            asset = inventory[slug]
            assert offset+n/fps <= asset["clip_seconds"]+.025, (slug,n/fps,asset["clip_seconds"])
            assert not patches or patches[-1]["end_frame"]<=a
            w,h = asset["dimensions"]
            top = 120 if title.endswith("S06") else 24 if title.endswith("S04") else 0
            side = min(w,h-top*2)
            left = max(0,min(w-side,round((crop*w-side/2)/2)*2))
            patch = dict(asset,start_frame=a,end_frame=b,montage_frame=cursor,offset=offset,
                         source_in=asset["source_start"]+offset,source_out=asset["source_start"]+offset+n/fps,
                         side=side,top=top,left=left,reason=reason,caption_placements=[])
            segment = PARTS/f"{number}-insert-{index:02d}.mp4"
            normalize(asset["file"],0,n,item,segment,square=True,shot=patch)
            layers.extend(caption_patch(placement,patch,segment,fps))
            parts.append((segment,n))
            patches.append(patch)
            cursor += n
        assert len(patches) in (6,7)
        listing = PARTS/(number+"-montage.txt")
        join_list(parts,fps,listing)
        ff("-y","-f","concat","-safe",0,"-i",listing,"-map","0:v:0","-c","copy",
           "-video_track_timescale",Fraction(item["rate"]).numerator,video)
        clock = video_clock(video)
        assert clock["frames"]==cursor and clock["regular"] and clock["rate"]==item["rate"]
        edit = dict(props["referenceEdit"],layers=layers)
        validate_reference_edit(edit,cursor/fps)
        assert all(layer["surface"]=="difference" and layer["shadow"]=="none" for layer in layers)
        props.update(src=video.name,durationSec=cursor/fps,punchIns=[],hook="",referenceEdit=edit)
        save(WORK/(number+"-props.json"),props)
        records.append(dict(item,inserts=patches,montage_frames=cursor))
        print("STAGED",ident,len(patches),"inserts",cursor,"frames",flush=True)
    save(WORK/"shot-map.json",records)
    prior.run(NODE,REMOTION,"bundle","src/index.ts",f"--public-dir={PUBLIC}",f"--out-dir={BUNDLE}")

def render():
    for item in read(WORK/"shot-map.json"):
        ident = item["id"]
        number = ident[:2]
        fps = item["fps"]
        receipt = QA/(number+"-technical.json")
        final = REVIEW/(ident+"-movie-cutaways-PRIVATE-REVIEW.mp4")
        if receipt.exists():
            assert final.is_file()
            continue
        raw = PARTS/(number+"-montage-render.mp4")
        if not raw.exists():
            cool()
            temp = raw.with_name(raw.stem+".partial.mp4")
            prior.run(NODE,REMOTION,"render",BUNDLE,"ViralShort",temp,
                      f"--props={WORK/(number+'-props.json')}","--gl=angle","--concurrency=1",
                      "--hardware-acceleration=required","--video-bitrate=13M","--image-format=jpeg",
                      "--jpeg-quality=99","--muted","--offthreadvideo-video-threads=2",
                      "--offthreadvideo-cache-size-in-bytes=134217728")
            assert video_clock(temp)["frames"]==item["montage_frames"]
            temp.replace(raw)
        base = F/"videos"/(ident+"-music-free.mp4")
        parts, cursor = [],0
        for index,shot in enumerate([*item["inserts"],dict(start_frame=item["frames"],end_frame=item["frames"])],1):
            a,b = shot["start_frame"],shot["end_frame"]
            if cursor<a:
                segment = PARTS/f"{number}-base-{index:02d}.mp4"
                normalize(base,cursor,a-cursor,item,segment)
                parts.append((segment,a-cursor))
            if a==b:
                break
            segment = PARTS/f"{number}-overlay-{index:02d}.mp4"
            normalize(raw,shot["montage_frame"],b-a,item,segment)
            parts.append((segment,b-a))
            cursor=b
        assert sum(n for _,n in parts)==item["frames"]
        listing = PARTS/(number+"-timeline.txt")
        join_list(parts,fps,listing)
        ff("-y","-f","concat","-safe",0,"-i",listing,"-i",base,"-map","0:v:0","-map","1:a:0","-c","copy",
           "-map_metadata","-1","-video_track_timescale",Fraction(item["rate"]).numerator,"-movflags","+faststart",final)
        clock = video_clock(final)
        assert clock["regular"] and clock["frames"]==item["frames"] and clock["rate"]==item["rate"],clock
        assert abs(clock["duration"]-item["duration"])<.001
        assert audio_packets(final)==audio_packets(base)
        decode(final,item["frames"])
        ff("-i",final,"-map","0:a:0","-f","null","-")
        checked = prior.review_frames(item,final)
        save(receipt,dict(video=str(final),clock=clock,inserts=len(item["inserts"]),checked_frames=checked,
                          original_dialogue_packet_match=True,full_decode=True,posting_reuse="unresolved"))
        print("VERIFIED",ident,len(item["inserts"]),flush=True)

def deliver():
    out = ROOT/"Main/shorts-clips/Exports"/"03 Archive/2026-11-10 - Speeches and Podcasts - Earlier Cutaway Review"
    if out.exists():
        raise FileExistsError(out)
    items = read(WORK/"shot-map.json")
    receipts = [read(QA/(item["id"][:2]+"-technical.json")) for item in items]
    assert len(receipts)==5
    out.mkdir()
    notes = ["# New five with movie cutaways", "",
             "Private review. Posting reuse for the film and TV footage remains unresolved.",
             "Each copy has six cutaways. Original dialogue packets and frame counts passed comparison.",
             "I inspected sampled opening and cut-boundary frames. Continuous listening remains unverified.",""]
    for item,receipt in zip(items,receipts):
        video = Path(receipt["video"])
        os.link(video,out/video.name)
        notes.extend((f"## [{item['id'][3:].replace('-',' ').title()}]({video.name})",""))
        for shot in item["inserts"]:
            notes.append(f"- {shot['start_frame']/item['fps']:.2f}s — {shot['title']}. {shot['reason']}")
        notes.append("")
    (out/"REVIEW.md").write_text("\n".join(notes),encoding="utf-8")
    save(out/"QA.json",receipts)
    print(out)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode != "deliver":
        require_guard(gpu=True)
    if mode == "batch":
        prepare()
        render()
    else:
        {"prepare":prepare,"render":render,"deliver":deliver}[mode]()
