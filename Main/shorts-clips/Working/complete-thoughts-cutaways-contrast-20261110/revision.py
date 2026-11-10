"""Build the second private movie-cutaway review from the approved frame clocks."""
import os
import math
import shutil
import sys
from fractions import Fraction
from pathlib import Path

WORK = Path(__file__).resolve().parent
OLD = WORK.parent / "complete-thoughts-movie-cutaways-20261110"
G = WORK.parent / "movie-cutaway-test-20261109"
sys.path.insert(0, str(OLD))
import edit as prior
from edit import P, ROOT, PROOFS, NODE, REMOTION, audio_packets, cool, ff, read, require_guard, run, save, video_clock
from build import validate_reference_edit

PUBLIC = WORK / "public"
QA = WORK / "qa"
OUT = WORK / "review"
BUNDLE = WORK / "clean-caption-bundle"
prior.PUBLIC = PUBLIC
prior.QA = QA

# Group bounds, excerpt, excerpt offset, crop centre, caption centre and meaning.
ADDITIONS = {
    "01": [
        (2, 3, "empty-office-corridor", .08, .36, (610, 1080, 690),
         "The narrowing office corridor gives diminishing choices a physical image."),
        (9, 13, "figure-walking-through-sparks", .2, .48, (540, 690, 760),
         "The figure keeps walking into the industrial light as Hollis describes the cost and reward of growth."),
    ],
    "02": [
        (6, 7, "tony-reclines-with-the-reactor", .22, .59, (540, 1137, 790),
         "Tony's vulnerable recovery gives the imagined objection a concrete low point."),
        (14, 16, "jon-gets-back-up-in-training", .04, .46, (355, 710, 560),
         "Jon bends and rises under pressure as Goggins describes failing repeatedly."),
    ],
    "03": [
        (19, 22, "two-figures-in-the-workshop", .12, .46, (540, 1135, 790),
         "Two people working together show the process behind differing performance."),
        (25, 27, "prototype-suit-stands-in-the-workshop", .3, .52, (540, 1210, 770),
         "The tangible prototype makes the desired outcome concrete before the edit returns to the work behind it."),
    ],
    "04": [
        (2, 3, "pepper-and-tony-in-quiet-conversation", .1, .65, (540, 1300, 810),
         "Pepper holds her composure in a tense exchange as Robbins addresses being underestimated."),
        (20, 23, "tony-alone-in-a-wide-workshop", .12, .62, (485, 655, 760),
         "Workshop action illustrates showing up and doing the work to build a life."),
    ],
    "05": [
        (4, 6, "tommy-alone-in-the-office", .3, .43, (555, 1115, 760),
         "Tommy at a table away from an audience introduces the work other people rarely see."),
        (16, 18, "light-over-a-crowd", .25, .58, (540, 905, 780),
         "The view past the performer into the lights contrasts the public reward with the work that follows."),
    ],
}

ACCENTS = {
    "01": {"diminish": (83, "cormorant", 700), "take": (83, "inter", 850), "give": (87, "cormorant", 700)},
    "02": {"depressing": (85, "cormorant", 700), "fail": (91, "inter", 850)},
    "03": {"performance": (77, "inter", 850), "else": (85, "cormorant", 700), "outcome": (84, "inter", 850)},
    "04": {"underestimate": (80, "inter", 850), "showing": (78, "inter", 830), "building": (84, "cormorant", 700)},
    "05": {"jealous": (80, "cormorant", 700), "dont": (83, "inter", 850)},
}

# The first emphasized phrase motivates a small picture push before the first film beat.
OPENINGS = {"01": (.48, 2.0), "02": (1.25, 1.32), "03": (.7, 1.48),
            "04": (1.28, 1.3), "05": (.54, 1.75)}

def link(source, dest):
    if not dest.exists():
        os.link(source, dest)

def grouped_words(props, groups):
    cursor = 0
    result = []
    for group in groups:
        words = group["text"].split()
        layers = props["referenceEdit"]["layers"][cursor:cursor+len(words)]
        assert list(map(prior.token, words)) == [prior.token(layer["text"]) for layer in layers]
        result.append(layers)
        cursor += len(words)
    assert cursor == len(props["referenceEdit"]["layers"])
    return result

def trim(layer, a, b, offset=0):
    t = layer["t"] + offset
    lo = max(a, t)
    hi = min(b, t + layer["dur"])
    if hi - lo < 1e-6:
        return None
    return dict(layer, t=lo, dur=hi-lo)

def author():
    for directory in (PUBLIC, QA, OUT, WORK / "props", WORK / "render"):
        directory.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "public/fonts", PUBLIC / "fonts", dirs_exist_ok=True)
    inventory = read(WORK / "candidate-review/inventory.json")
    past = {item["id"]: item["inserts"] for item in read(OLD / "shot-map.json")}
    manifest = []
    for ident, item in PROOFS.items():
        number = ident[:2]
        fps = item["fps"]
        original = read(P / f"finish-v1/props/{ident}.json")
        groups = read(P / f"finish-v1/props/{ident}-caption-plan.json")["groups"]
        words = grouped_words(original, groups)
        props = read(G / "review-props-clean-joins.json") if number == "02" else original
        start, duration = OPENINGS[number]
        opening = dict(t=start, dur=duration, scale=1.075)
        props["punchIns"] = [opening, *(p for p in props.get("punchIns", []) if p["t"] >= 3)]
        source = G / "public" / props["src"] if number == "02" else P / f"drafts/{ident}-clean-assembly.mp4"
        props["src"] = f"{number}-speaker.mp4"
        link(source, PUBLIC / props["src"])
        base = props["referenceEdit"]["layers"]
        previous = []
        if number == "02":
            for cut in props["cutaways"]:
                link(G / "public" / cut["src"], PUBLIC / cut["src"])
                previous.append(dict(id=Path(cut["src"]).stem, start_frame=round(cut["t"]*fps),
                                     end_frame=round((cut["t"]+cut["dur"])*fps), captions_from_base=True))
        else:
            for cut in past[ident]:
                link(OLD / "public" / f"{cut['id']}.mp4", PUBLIC / f"{cut['id']}.mp4")
                previous.append(cut)
        new = []
        for n, (first, last, slug, offset, crop_x, caption, why) in enumerate(ADDITIONS[number], 1):
            a = round(groups[first]["start"]*fps)
            b = min(item["frames"], math.ceil(groups[last-1]["end"]*fps-1e-7))
            for old in previous:
                if old["start_frame"] < a < old["end_frame"]:
                    assert old["end_frame"] - a <= 1
                    a = old["end_frame"]
                elif a < old["start_frame"] < b:
                    assert b - old["start_frame"] <= 1
                    b = old["start_frame"]
            asset = inventory[slug]
            assert offset + (b-a)/fps <= asset["clip_seconds"]+.01
            w, h = asset["dimensions"]
            top = 120 if asset["title"].endswith("S06") else 0
            side = min(w, h - top*2)
            crop_left = max(0, min(w-side, round((crop_x*w-side/2)/2)*2))
            insert = dict(asset, id=f"{number}-extra-{n}", slug=slug, offset=offset,
                          start_frame=a, end_frame=b, why=why, crop_left=crop_left,
                          crop_top=top, square_side=side, staged_side=min(side,1960),
                          spoken=" ".join(g["text"] for g in groups[first:last]))
            new.append(insert)
            layers = prior.patch_layers(range(first,last), words, caption, ACCENTS[number], a,b,fps)
            save(WORK / f"{insert['id']}-layers.json", layers)
        shots = sorted(previous + new, key=lambda s:s["start_frame"])
        assert all(a["end_frame"] <= b["start_frame"] for a,b in zip(shots,shots[1:]))
        props["cutaways"] = [dict(src=s["id"]+".mp4", t=s["start_frame"]/fps,
                                  dur=(s["end_frame"]-s["start_frame"])/fps) for s in shots]
        replaced = [s for s in shots if not s.get("captions_from_base")]
        layers = []
        lo = 0
        for cut in replaced:
            a,b = cut["start_frame"]/fps,cut["end_frame"]/fps
            layers.extend(result for layer in base if (result := trim(layer,lo,a)))
            if cut in new:
                patch_layers = read(WORK / f"{cut['id']}-layers.json")
            else:
                patch_layers = read(OLD / f"{cut['id']}.json")["referenceEdit"]["layers"]
            layers.extend(result for layer in patch_layers if (result := trim(layer,a,b,a)))
            lo = b
        layers.extend(result for layer in base if (result := trim(layer,lo,item["frames"]/fps)))
        props["referenceEdit"]["layers"] = layers
        props["durationSec"] = item["frames"]/fps
        validate_reference_edit(props["referenceEdit"],props["durationSec"])
        assert all(layer.get("shadow", "none") == "none" and layer.get("surface") == "difference" for layer in layers)
        save(WORK / f"props/{ident}.json", props)
        manifest.append(dict(item, inserts=shots, new_inserts=new, opening=opening,
                             resolution=[1080,1920] if number=="02" else [2160,3840]))
    save(WORK / "shot-map.json", manifest)

def opts(ident, scale):
    return [f"--props={WORK / f'props/{ident}.json'}",f"--scale={scale}","--gl=angle",
            "--offthreadvideo-video-threads=2","--offthreadvideo-cache-size-in-bytes=134217728"]

def preview():
    for item in read(WORK / "shot-map.json"):
        ident = item["id"]
        for shot in item["new_inserts"]:
            dest = PUBLIC / (shot["id"]+".mp4")
            if not dest.exists():
                prior.stage(item, shot)
    if not BUNDLE.exists():
        run(NODE, REMOTION, "bundle", "src/index.ts", f"--public-dir={PUBLIC}", f"--out-dir={BUNDLE}")
    for item in read(WORK / "shot-map.json"):
        ident = item["id"]
        for shot in item["new_inserts"]:
            if shot["id"] not in {"02-extra-1","04-extra-1","04-extra-2","05-extra-2"}:
                continue
            dest = QA / f"{shot['id']}-clean.png"
            if dest.exists():
                continue
            cool()
            frame = shot["start_frame"] + round(.7*(shot["end_frame"]-shot["start_frame"]-1))
            run(NODE, REMOTION, "still", BUNDLE, "ViralShort", dest, f"--frame={frame}", *opts(ident,1))

def normalize(item, source, start, count, dest):
    cool()
    ff("-y","-hwaccel","cuda","-hwaccel_output_format","cuda",
       "-ss",f"{max(0,start/item['fps']-.000001):.6f}","-i",source,"-map","0:v:0","-an","-frames:v",count,
       "-c:v","h264_nvenc","-preset","p4","-profile:v","high","-rc","vbr","-cq",17,"-b:v",0,
       "-maxrate","55M","-bufsize","110M","-bf",0,"-vf","scale_cuda=format=nv12,hwdownload,format=nv12",
       "-pix_fmt","nv12","-fps_mode","passthrough","-video_track_timescale",Fraction(item["rate"]).numerator,dest)
    media = prior.probe(dest)
    assert [media.width,media.height] == item["resolution"] and media.rate == item["rate"]
    assert abs(media.duration-count/item["fps"]) < .002

def render():
    for item in read(WORK / "shot-map.json"):
        ident = item["id"]
        if len(sys.argv) > 2 and not ident.startswith(sys.argv[2]):
            continue
        scale = item["resolution"][0]//1080
        final = OUT / f"{ident}-expanded-cutaways-REVIEW.mp4"
        receipt = QA / f"{ident[:2]}-technical.json"
        if receipt.exists():
            assert final.is_file()
            continue
        number = ident[:2]
        base = (G / "02-goggins-learning-to-fail-movie-cutaways-REVIEW-v2.mp4") if number == "02" else (
            OLD / f"review/{ident}-movie-cutaways-REVIEW.mp4")
        changed = [(0,math.ceil(3*item["fps"]))]
        changed.extend((s["start_frame"],s["end_frame"]) for s in item["new_inserts"])
        cursor = 0
        parts = []
        for a,b in changed+[(item["frames"],item["frames"])]:
            if cursor < a:
                dest = WORK / "render" / f"{number}-base-{cursor:04d}.mp4"
                if not dest.exists():
                    normalize(item,base,cursor,a-cursor,dest)
                parts.append((dest,a-cursor))
            if a == b:
                break
            dest = WORK / "render" / f"{number}-changed-{a:04d}.mp4"
            raw = dest.with_name(dest.stem+".raw.mp4")
            if not raw.exists():
                cool()
                temp = raw.with_name(raw.stem+".partial.mp4")
                run(NODE, REMOTION, "render", BUNDLE, "ViralShort", temp, f"--frames={a}-{b-1}",
                    "--concurrency=1", "--hardware-acceleration=required", "--video-bitrate=34M" if scale==2 else "--video-bitrate=14M",
                    "--image-format=jpeg", "--jpeg-quality=100", "--muted", *opts(ident,scale))
                assert video_clock(temp)["frames"] == b-a
                temp.replace(raw)
            if not dest.exists():
                normalize(item,raw,0,b-a,dest)
            parts.append((dest,b-a))
            cursor=b
        listing = WORK / "render" / f"{ident[:2]}-concat.txt"
        listing.write_text("\n".join(f"file '{file.as_posix()}'\nduration {n/item['fps']:.9f}"
                                      for file,n in parts)+"\n", encoding="utf-8")
        clean = P / f"drafts/{ident}-clean-assembly.mp4"
        approved = P / f"finish-v1/finished/{ident}-music-free.mp4"
        ff("-y","-f","concat","-safe",0,"-i",listing,"-i",clean,"-map","0:v:0","-map","1:a:0",
           "-c","copy","-map_metadata",-1,"-video_track_timescale",Fraction(item["rate"]).numerator,
           "-movflags","+faststart",final)
        clock = video_clock(final)
        media = prior.probe(final)
        assert [media.width, media.height] == item["resolution"]
        assert clock["frames"] == item["frames"] and clock["regular"] and clock["rate"] == item["rate"],clock
        assert abs(clock["duration"]-item["duration"]) < .001
        assert audio_packets(final) == audio_packets(approved) == audio_packets(clean)
        ff("-i",final,"-map","0:a:0","-f","null","-")
        reviewed = prior.review_frames(item,final)
        save(receipt, dict(file=str(final),clock=clock,dialogue_packet_equal=True,audio_decoded=True,
                           all_frames_cuda_decoded=True,review_frames=reviewed,
                           posting_reuse="Unresolved for film and TV inserts. Private owner review."))
        print("VERIFIED",ident,clock["frames"],flush=True)

if __name__ == "__main__":
    action = sys.argv[1]
    if action != "author":
        require_guard(gpu=True)
    {"author": author, "preview": preview, "render": render}[action]()
