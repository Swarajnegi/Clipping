"""Finish the five approved proofs, retaining their exact dialogue and cadence."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from finish_design import DESIGNS

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(P.parent / "movie-cutaway-test-20261109"))
from build import validate_reference_edit
from common import FFMPEG, NODE, REMOTION, encoder, ffmpeg_command, probe, require_guard
from cooling import cool
from motion_edit import audio_packets, decode, video_clock

F = P / "finish-v1"
PUBLIC = F / "public"
BUNDLE = F / "bundle"
FONT_DIR = ROOT / "public/fonts"
BOX = dict(x=50, y=470, width=980, height=980, radius=48)
TRACKING = -.028

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

def ff(*args, capture=False):
    return subprocess.run(ffmpeg_command([FFMPEG, "-hide_banner", "-v", "error", "-xerror", *map(str,args)]),
                          check=True, stdout=subprocess.PIPE if capture else None).stdout

def roughs():
    return [read(path) for path in sorted((P / "drafts").glob("*-rough.json"))]

@lru_cache(maxsize=128)
def font(face, size, weight):
    f = ImageFont.truetype(FONT_DIR / ("InterVariable.woff2" if face == "inter" else "CormorantGaramond-Italic.ttf"), size)
    if face == "inter":
        f.set_variation_by_axes([min(32,size),weight])
    return f

def samples(source):
    detector = cv2.FaceDetectorYN.create(str(ROOT / "models/face_detection_yunet_2023mar.onnx"),
                                         "", (320,320), score_threshold=.76)
    raw = ff("-hwaccel","cuda","-hwaccel_output_format","cuda","-i",source,"-an",
             "-vf","fps=5,scale_cuda=320:320:format=nv12,hwdownload,format=nv12,format=bgr24",
             "-f","rawvideo","-",capture=True)
    frames = np.frombuffer(raw,np.uint8).reshape(-1,320,320,3)
    data = []
    for i, frame in enumerate(frames):
        frame = np.ascontiguousarray(frame)
        _, hits = detector.detect(frame)
        faces = [] if hits is None else [tuple(float(x)*980/320 for x in f[:4]) for f in hits]
        data.append((i/5, cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY), faces))
    return data

def words_for(rough):
    fps = rough["clock"]["fps"]
    original = [w for seg in read(P / "sources" / (rough["id"]+"-words.json"))["segments"] for w in seg["words"]]
    result, offset = [], 0
    for span in rough["cuts"]:
        a, b = (round(span[key]*fps)/fps for key in ("start","end"))
        result.extend(dict(text=w["w"], start=max(0,w["s"]-a)+offset, end=min(b,w["e"])-a+offset)
                      for w in original if w["e"] > a+.025 and w["s"] < b-.025)
        offset += b-a
    return result

def preferred_position(rows, frame_samples, start, end, punches):
    w = max(sum(word[4] for word in row)+10*(len(row)-1) for row in rows)
    h = sum(max(word[1] for word in row)+8 for row in rows)
    matching = [(t,luma,faces) for t,luma,faces in frame_samples if start-.18<=t<=end+.18]
    candidates = [(540,970),(540,1060),(540,1160),(540,1230),(540,1310),(540,650),(540,570),
                  (390,1050),(670,1050),(390,1210),(670,1210)]
    if any(len(faces) for _,_,faces in matching):
        candidates.extend((x,y) for y in (1350,1370,545,520,1270,1190) for x in (540,420,660,340,740))
    ranked = []
    for i,(x,y) in enumerate(candidates):
        x0,x1 = x-w/2,x+w/2
        y0,y1 = y-h/2,y+h/2
        if x0 < 86 or x1 > 994 or y0 < 494 or y1 > 1412:
            continue
        overlaps, contrast = 0, []
        for t,luma,faces in matching:
            z = max([1,*[p["scale"]+.015 for p in punches if p["t"]-.15<=t<=p["t"]+p["dur"]+.5]])
            for fx,fy,fw,fh in faces:
                l = 540+(fx-490)*z-16
                r = 540+(fx+fw-490)*z+16
                top = 960+(fy-490)*z-18
                bot = 960+(fy+fh-490)*z+24
                overlaps += int(min(x1,r)>max(x0,l) and min(y1,bot)>max(y0,top))
            region = luma[round((y0-470)*320/980):round((y1-470)*320/980),
                          round((x0-50)*320/980):round((x1-50)*320/980)]
            contrast.append(float(np.mean(np.abs(255-2*region.astype(np.int16)))))
        ranked.append((overlaps, i*4 - (min(contrast) if contrast else 0)*.28, x, y))
    if not ranked:
        raise ValueError("No caption position within the picture")
    overlaps, _, x, y = min(ranked)
    return x,y,h,overlaps

def compose(rough, design, frame_samples, punches):
    words = words_for(rough)
    fps = rough["clock"]["fps"]
    duration = rough["clock"]["duration"]
    groups = design["groups"]
    layers, placements = [], []
    for start, stop in zip(groups, [*groups[1:],len(words)]):
        span = []
        for i in range(start, stop):
            if i-1 in design.get("merge", []):
                continue
            w = dict(words[i])
            w["text"] = design.get("replace", {}).get(i, w["text"])
            if i in design.get("merge", []):
                w["text"] += words[i+1]["text"]
                w["end"] = words[i+1]["end"]
            accent = design["accents"].get(i)
            size = 88 if accent == "large" else 84 if accent == "italic" else 63 if start<6 else 58
            face = "cormorant" if accent == "italic" else "inter"
            weight = 820 if accent == "large" else 700
            width = font(face,size*8,weight).getlength(w["text"])/8 + TRACKING*size*max(0,len(w["text"])-1) + 8
            span.append((w,size,face,weight,width))
        if not span:
            continue
        def line_width(line):
            return sum(word[4] for word in line)+10*(len(line)-1)
        rows = [span]
        if line_width(span)>750 and len(span)>1:
            split = min(range(1,len(span)), key=lambda i:max(line_width(span[:i]),line_width(span[i:])))
            rows = [span[:split],span[split:]]
        shrink = min(1,750/max(map(line_width,rows)))
        rows = [[(w,s*shrink,f,k,b*shrink) for w,s,f,k,b in row] for row in rows]
        a = span[0][0]["start"]
        next_start = words[stop]["start"] if stop<len(words) else duration
        end = min(next_start,span[-1][0]["end"]+.49,duration)
        xc,yc,height,overlaps = preferred_position(rows,frame_samples,a,end,punches)
        top = yc-height/2
        for row in rows:
            line_height = max(item[1] for item in row)+8
            left = xc-line_width(row)/2
            for word,size,face,weight,width in row:
                at = round(word["start"]*fps)/fps
                at = min(at,duration-1/fps)
                hold = min(duration-at,max(1/fps,end-at))
                layers.append(dict(t=at,dur=hold,text=word["text"],x=round(left,2),
                                   y=round(top+(line_height-size)*.52,2),width=round(width,2),
                                   size=round(size,2),font=face,italic=face=="cormorant",weight=weight,
                                   align="center",tracking=TRACKING,lineHeight=1,surface="difference",
                                   color="#ffffff",blend="difference",fillOpacity=1,shadow="none",depth="front",
                                   motion=dict(inSec=.075,outSec=.035,rise=4,scaleFrom=.98,blur=.9,easing="cubic")))
                left += width+10
            top += line_height
        placements.append(dict(start=a,end=end,centre=[xc,yc],face_intersections=overlaps,
                               text=" ".join(w[0]["text"] for w in span)))
    return layers, placements

def prepare():
    for path in (F,PUBLIC,F/"props",F/"qa",F/"videos",F/"covers"):
        path.mkdir(exist_ok=True)
    shutil.copytree(FONT_DIR, PUBLIC/"fonts",dirs_exist_ok=True)
    cv2.setNumThreads(2)
    for rough in roughs():
        ident = rough["id"]
        if len(sys.argv)>2 and not ident.startswith(sys.argv[2]):
            continue
        design = DESIGNS[ident[:2]]
        src = PUBLIC/(ident+".mp4")
        if not src.exists():
            cool()
            temp = src.with_name(src.stem+".partial.mp4")
            ff("-y","-hwaccel","cuda","-i",rough["proof"],"-map","0:v:0","-an",
               "-vf","crop=980:980:50:470,setsar=1",*encoder(16),
               "-fps_mode","passthrough","-movflags","+faststart",temp)
            assert video_clock(temp)==rough["clock"], (ident,video_clock(temp),rough["clock"])
            temp.replace(src)
        punch = [dict(t=t,dur=duration,scale=scale) for t,duration,scale in design["pushes"]]
        layers, placement = compose(rough,design,samples(src),punch)
        edit = dict(profile="editorial",frame=BOX,layeredOnly=True,layers=layers)
        validate_reference_edit(edit,rough["clock"]["duration"])
        props = dict(src=src.name,bgSrc=None,fps=rough["clock"]["fps"],durationSec=rough["clock"]["duration"],
                     srcWidth=980,srcHeight=980,widthFrac=1,shots=[dict(t=0,x=.5,w=1)],track=[],
                     yAnchor=.5,hook=design.get("headline",""),hookPersist=False,hookDurationSec=2.78,
                     captions=[],punchIns=punch,watermark=None,loopFadeSec=0,style="clean",
                     grade=dict(brightness=1,contrast=1,saturate=1),accent="#ffffff",intro=None,music=None,
                     referenceEdit=edit,cutaways=[])
        save(F/"props"/(ident+".json"),props)
        save(F/"qa"/(ident+"-placement.json"),placement)
        print("PREPARED",ident,len(layers),"words",sum(p["face_intersections"] for p in placement),"sampled intersections",flush=True)
    if not BUNDLE.exists():
        subprocess.run([NODE,REMOTION,"bundle","src/index.ts",f"--public-dir={PUBLIC}",f"--out-dir={BUNDLE}"],cwd=ROOT,check=True)

def still(source, when):
    raw = ff("-hwaccel","cuda","-ss",when,"-i",source,"-frames:v","1","-f","image2pipe","-c:v","png","-",capture=True)
    import io
    return Image.open(io.BytesIO(raw)).convert("RGB")

def cover(ident, design):
    picture = still(PUBLIC/(ident+".mp4"),design["cover_at"])
    shade = Image.new("RGBA",picture.size)
    draw = ImageDraw.Draw(shade)
    for y in range(980):
        alpha = round(204*max(0,min(1,(y-430)/430)))
        draw.line((0,y,979,y),fill=(0,0,0,alpha))
    picture = Image.alpha_composite(picture.convert("RGBA"),shade).convert("RGB")
    mask = Image.new("L",(980,980))
    ImageDraw.Draw(mask).rounded_rectangle((0,0,979,979),radius=48,fill=255)
    canvas = Image.new("RGB",(1080,1920),"black")
    canvas.paste(picture,(50,470),mask)
    draw = ImageDraw.Draw(canvas)
    draw.text((540,432),design["speaker"],font=font("inter",33,700),fill="#d3d8db",anchor="ms")
    for i,(line,face) in enumerate(zip(design["cover"],("inter","cormorant"))):
        size = 87 if i==0 else 122
        while font(face,size,820).getlength(line)>870:
            size -= 2
        draw.text((540,1235+111*i),line,font=font(face,size,820),fill="#f4f3ec",anchor="ms")
    canvas.save(F/"covers"/(ident+"-thumbnail.jpg"),quality=96,subsampling=0)

def options(ident):
    return [f"--props={F/'props'/(ident+'.json')}","--gl=angle","--offthreadvideo-video-threads=2",
            "--offthreadvideo-cache-size-in-bytes=134217728"]

def preview():
    for rough in roughs():
        ident = rough["id"]
        design = DESIGNS[ident[:2]]
        cover(ident,design)
        frame = round((design["pushes"][0][0]+.7)*rough["clock"]["fps"])
        dest = F/"qa"/(ident+"-opening.jpg")
        cool()
        subprocess.run([NODE,REMOTION,"still",BUNDLE,"ViralShort",dest,f"--frame={frame}",*options(ident)],
                       cwd=ROOT,check=True)

def review(ident, path, fps, frames):
    opening = [round(t*fps) for t in (.2,.7,1.35,1.95,2.55,2.92)]
    later = [round((frames-1)*f) for f in (.23,.37,.49,.64,.78,.93,.99)]
    cue_frames = [round((t+offset)*fps) for t,_,_ in DESIGNS[ident[:2]]["pushes"]
                  for offset in (-1/fps,.36)]
    if ident.startswith("05"):
        cue_frames.extend([round(4.36*fps),round(4.44*fps)])
    wanted = sorted({*opening,*later,*cue_frames} & set(range(frames)))
    choice = "+".join(f"eq(n\\,{f})" for f in wanted)
    raw = ff("-hwaccel","cuda","-hwaccel_output_format","cuda","-i",path,"-an",
             "-vf",f"select={choice},scale_cuda=216:384:format=nv12,hwdownload,format=nv12,format=rgb24",
             "-fps_mode","passthrough","-f","rawvideo","-",capture=True)
    grid = Image.new("RGB",(216*5,404*((len(wanted)+4)//5)),"#17191b")
    draw = ImageDraw.Draw(grid)
    for i,(frame,rgb) in enumerate(zip(wanted,np.frombuffer(raw,np.uint8).reshape(-1,384,216,3),strict=True)):
        x,y = (i%5)*216,(i//5)*404
        grid.paste(Image.fromarray(rgb),(x,y+20))
        draw.text((x+5,y+4),f"{frame/fps:.2f}s",fill="white")
    grid.save(F/"qa"/(ident+"-frame-review.jpg"),quality=94)
    return wanted

def render():
    for rough in roughs():
        ident = rough["id"]
        final = F/"videos"/(ident+"-music-free.mp4")
        receipt = F/"qa"/(ident+"-technical.json")
        if receipt.exists():
            assert final.exists()
            continue
        cool()
        raw = F/(ident+"-picture.mp4")
        if not raw.exists():
            partial = raw.with_name(raw.stem+".partial.mp4")
            subprocess.run([NODE,REMOTION,"render",BUNDLE,"ViralShort",partial,"--concurrency=1",
                           "--hardware-acceleration=required","--video-bitrate=13M","--image-format=jpeg",
                           "--jpeg-quality=99","--muted",*options(ident)],cwd=ROOT,check=True)
            partial.replace(raw)
        ff("-y","-i",raw,"-i",rough["proof"],"-map","0:v:0","-map","1:a:0","-c","copy",
           "-map_metadata","-1","-movflags","+faststart",final)
        clock = video_clock(final)
        expected = rough["clock"]
        assert clock["regular"] and clock["frames"] == expected["frames"] and clock["rate"] == expected["rate"], (ident,clock,expected)
        # Encoders can choose different MP4 track time bases for the same cadence.
        assert all(abs(clock[key]-expected[key]) <= .00005 for key in
                   ("first_pts","last_pts","last_frame_duration","duration")), (ident,clock,expected)
        meta = probe(final)
        assert (meta.width,meta.height)==(1080,1920)
        assert audio_packets(final)==audio_packets(Path(rough["proof"]))
        decode(final,clock["frames"])
        ff("-i",final,"-map","0:a:0","-f","null","-")
        frames = review(ident,final,clock["fps"],clock["frames"])
        save(receipt,dict(file=str(final),clock=clock,video_decode=True,audio_decode=True,
                          dialogue_matches_rough=True,review_frames=frames))
        print("VERIFIED",ident,clock["frames"],flush=True)

def render_batch():
    prepare()
    render()

def deliver():
    dest = ROOT/"Main/shorts-clips/Exports/01 Finished Edits/2026-11-10 - Speeches and Podcasts - Original Footage"
    if dest.exists():
        raise FileExistsError(dest)
    selected = []
    for rough in roughs():
        ident = rough["id"]
        video = F/"videos"/(ident+"-music-free.mp4")
        thumb = F/"covers"/(ident+"-thumbnail.jpg")
        receipt = read(F/"qa"/(ident+"-technical.json"))
        assert video.is_file() and thumb.is_file() and receipt["dialogue_matches_rough"]
        selected.append((rough,video,thumb,receipt))
    assert len(selected)==5
    dest.mkdir()
    notes = ["# Thought Palace · five speech and podcast edits",
             "Music-free 1080×1920 exports from the approved 1920×1080 source uploads. "
             "Original source cadence and the approved rough-cut dialogue are preserved. "
             "The owner confirmed reuse permission for each original on 10 November 2026.",
             "The edits use cleared original picture and programmatic typography. "
             "The covers use original frames and bundled OFL Inter and Cormorant Garamond. "
             "Titles and cover lines are editorial wording.",
             "QA covered complete picture and audio decode, frame count, cadence, dialogue packet identity, "
             "and sampled phone-size openings, transitions and covers. Continuous listening remains unverified."]
    manifest = []
    for rough,video,thumb,receipt in selected:
        ident = rough["id"]
        style = DESIGNS[ident[:2]]
        source = read(P/"sources"/(ident+".json"))
        for media in (video,thumb):
            os.link(media,dest/media.name)
        note = (
            f"## {style['title']}\n\n"
            f"{style['description']}\n\n{style['tags']}\n\n"
            f"[Video]({video.name}) · [Cover]({thumb.name}) · "
            f"[Original upload]({source['canonical_url']})\n\n"
            f"Opening words — {style['opening']}\n\n"
            f"First picture transition — {style['pushes'][0][0]:.2f}s. {style['transition']}"
        )
        notes.append(note)
        files = {}
        for media in (video,thumb):
            with (dest/media.name).open("rb") as f:
                files[media.name] = hashlib.file_digest(f,"sha256").hexdigest()
        manifest.append(dict(id=ident,files=files,source=source["canonical_url"],
                             reuse_basis=source["reuse_basis"],source_dimensions=[1920,1080],
                             output_dimensions=[1080,1920],technical_qa=receipt,opening=style["opening"],
                             first_transition=style["pushes"][0][0],treatment=style["transition"]))
    (dest/"UPLOAD.md").write_text("\n\n".join(notes)+"\n",encoding="utf-8")
    save(dest/"DELIVERY_MANIFEST.json",manifest)
    print(dest)

if __name__ == "__main__":
    action = sys.argv[1]
    if action != "deliver":
        require_guard(gpu=True)
    {"prepare":prepare,"preview":preview,"render":render,"batch":render_batch,"deliver":deliver}[action]()
