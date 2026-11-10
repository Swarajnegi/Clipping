"""Isolated intake of two newly supplied live-action packs using the library workflow."""
import sys
import math
import shutil
import subprocess
import time
from bisect import bisect_left
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(WORK.parent / "movie-library-intake-20261109"))
import pack_intake

pack_intake.WORK = WORK
pack_intake.PACKS = {
    "luke": ("Luke Glanton Badass [4K].mp4", "Luke Glanton - The Place Beyond the Pines", False),
    "officer-key": ("Officer K - Blade Runner 2049 (2017) [Remux 4K h265] - thomas.mp4",
                  "Blade Runner 2049 - Officer K", False),
}

import export_batches
import publish_library
import screen_packs

def keyframe_scan(name):
    """Cover the long pack with source keyframes before selecting tighter shots."""
    original, _, _ = pack_intake.PACKS[name]
    source = pack_intake.MOVIES / original
    media = pack_intake.probe(source)
    stream = pack_intake.source_stream(source)
    stat = source.stat()
    duration = float(stream.get("duration") or media.duration)
    block_size = 180
    work = WORK / name
    work.mkdir(exist_ok=True)
    record = dict(name=original, bytes=stat.st_size, mtime_ns=stat.st_mtime_ns,
                  video_seconds=duration, width=media.width, height=media.height, rate=media.rate,
                  average_rate=stream.get("avg_frame_rate"),pixel_format=stream["pix_fmt"],
                  codec=stream["codec_name"],color_space=stream.get("color_space"),
                  scan_mode="Source keyframes throughout the timeline",block_seconds=block_size)
    path = work / "source.json"
    if path.exists() and pack_intake.load(path)!=record:
        raise ValueError(f"Different scan recipe or source identity in {work}")
    pack_intake.save(path,record)
    count = math.ceil(duration/block_size)
    for index in range(count):
        block = work / f"block-{index:04d}.npz"
        if block.exists():
            continue
        start = index * block_size
        pack_intake.cool(76)
        times, frames = pack_intake.scan_block(source,start,min(block_size,duration-start),True)
        if times[0]-start>9.0:
            raise ValueError(f"Unexpected keyframe gap at {start}s")
        temp = block.with_suffix(".tmp")
        with temp.open("wb") as handle:
            np.savez_compressed(handle,times=times,frames=frames)
        temp.replace(block)
        if index % 4 == 0 or index == count-1:
            print("KEYFRAME_SCAN",name,index+1,count,len(times),flush=True)

def candidate_sheets(name):
    """Show every candidate in chronological order, including small shots."""
    work = WORK / name
    packet = pack_intake.load(work / "candidates.json")
    rows = packet["candidates"]
    width, height, columns, page_size = 144, 60, 8, 64
    selected = {row["sample_index"]: i for i,row in enumerate(rows)}
    images = {}
    offset = 0
    for path in sorted(work.glob("block-*.npz")):
        with np.load(path) as block:
            frames = block["frames"]
            for index in range(len(frames)):
                page_index = selected.get(index+offset)
                if page_index is not None:
                    images[page_index] = Image.fromarray(frames[index]).resize((width,height),Image.Resampling.LANCZOS)
            offset += len(frames)
    assert len(images)==len(rows)
    for start in range(0,len(rows),page_size):
        page = rows[start:start+page_size]
        canvas = Image.new("RGB",(columns*width,((len(page)+columns-1)//columns)*(height+18)),pack_intake.BLACK)
        draw = ImageDraw.Draw(canvas)
        for index,row in enumerate(page):
            x,y = index%columns*width,index//columns*(height+18)
            draw.text((x+3,y+1),f"{row['id']:04d}  {row['sample_time']:.1f}",fill="white")
            canvas.paste(images[start+index],(x,y+18))
        canvas.save(work/f"all-{start//page_size+1:02d}.jpg",quality=92)

def selected_rows(name):
    work = WORK / name
    packet = pack_intake.load(work / "candidates.json")
    candidates = {row["id"]:row for row in packet["candidates"]}
    rows = []
    for line in (work/"reviewed.tsv").read_text(encoding="utf-8-sig").splitlines():
        if not line or line.startswith("#"):
            continue
        ident,slug,tags = line.split("|",2)
        rows.append(dict(candidates[int(ident)],slug=slug,tags=tags.split(", ")))
    assert rows and len({row["id"] for row in rows}) == len(rows)
    return packet,sorted(rows,key=lambda row:row["start"])

def plan(name, tight):
    work = WORK / name
    packet, rows = selected_rows(name)
    if not tight:
        pack_intake.save(work/"selection.json",rows)
        return
    original = pack_intake.MOVIES / packet["source"]["name"]
    records = []
    chosen = []
    for i,row in enumerate(rows):
        if i%7==0:
            pack_intake.cool(76)
        evidence = work/f"review-{row['id']:04d}.json"
        if evidence.exists():
            record = pack_intake.load(evidence)
        else:
            times,rgb = pack_intake.scan_block(original,row["start"],row["end"]-row["start"],False)
            rgb = rgb[:,6:-6:4,4:-4:4].astype(np.int16)
            cut_magnitude = np.abs(rgb[1:]-rgb[:-1]).mean(axis=3)
            cuts = (cut_magnitude.mean(axis=(1,2))>23)&((cut_magnitude>34).mean(axis=(1,2))>.31)
            marks = [row["start"],*times[1:][cuts],row["end"]]
            spans = [(float(a),float(b)) for a,b in zip(marks,marks[1:]) if b-a>=1.45]
            best = min(spans,key=lambda p:(not p[0]-.55<=row["sample_time"]<=p[1]+.2,-(p[1]-p[0]))) if spans else None
            record = dict(id=row["id"],samples=len(times),sample_step=.5,boundaries=marks,
                          chosen=best,first=float(times[0]),last=float(times[-1]))
            pack_intake.save(evidence,record)
        records.append(record)
        if record["chosen"]:
            start,end = record["chosen"]
            chosen.append(dict(row,start=start,end=end))
        if i==0 or (i+1)%16==0 or i+1==len(rows):
            print("TIGHT_REVIEW",name,i+1,len(rows),len(chosen),flush=True)
    assert chosen and all(a["end"]<=b["start"] for a,b in zip(chosen,chosen[1:]))
    pack_intake.save(work/"selection.json",chosen)
    pack_intake.save(work/"selection-evidence.json",records)

def copy_keyframe_ranges(name):
    """Reuse original video packets for ranges already bounded by nearby keyframes."""
    original,title,_ = pack_intake.PACKS[name]
    work = WORK / name
    source = pack_intake.MOVIES / original
    folder = pack_intake.MOVIES / title
    folder.mkdir(exist_ok=True)
    record = pack_intake.load(work/"source.json")
    rows = pack_intake.load(work/"selection.json")
    stat = source.stat()
    assert (stat.st_size,stat.st_mtime_ns)==(record["bytes"],record["mtime_ns"])
    manifest = folder/"catalogue.json"
    data = pack_intake.load(manifest) if manifest.exists() else dict(
        source=original,source_bytes=stat.st_size,source_mtime_ns=stat.st_mtime_ns,
        source_resolution=[record["width"],record["height"]],source_frame_rate=record["rate"],
        source_duration=record["video_seconds"],posting_reuse_basis="Unresolved. Local library.",
        time_basis="Source-relative seconds on the native frame clock. Packet copies snap to nearby keyframes.",
        clips=[])
    assert (data["source"],data["source_bytes"],data["source_mtime_ns"])==(original,stat.st_size,stat.st_mtime_ns)
    done = {clip["candidate_id"] for clip in data["clips"]}
    fps = float(Fraction(record["rate"]))
    # Decoder best-effort timestamps can differ from muxed packet PTS with B-frames.
    packets = subprocess.check_output([
        pack_intake.FFPROBE, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", str(source),
    ], text=True)
    keys = sorted({
        round(float(pts)*fps) for line in packets.splitlines()
        for pts, _, flags in [line.partition(",")] if flags.startswith("K")
    })
    def nearest(timecode):
        index = bisect_left(keys,timecode)
        nearby = keys[max(0,index-1):index+1]
        return min(nearby,key=lambda k:abs(k-timecode))
    candidates = []
    for index,row in enumerate(rows):
        if row["id"] in done:
            continue
        a,b = nearest(row["start"]*fps),nearest(row["end"]*fps)
        if (abs(a/fps-row["start"])>.55 or abs(b/fps-row["end"])>.55 or b-a<1.4*fps or
                (index and a/fps<rows[index-1]["end"]-.001) or
                (index+1<len(rows) and b/fps>rows[index+1]["start"]+.001)):
            continue
        candidates.append((row,a,b,0))
    print("PACKET_COPY_CANDIDATES",name,len(candidates),"/",len(rows),flush=True)
    for index in range(0,len(candidates),6):
        if shutil.disk_usage(folder).free < 4*1024**3:
            raise RuntimeError("Four GiB disk reserve reached")
        scratch = work/f"copy-{time.time_ns()}"
        scratch.mkdir()
        wanted, files = [], []
        for pos,(row,a,b,_) in enumerate(candidates[index:index+6]):
            tmp = scratch/f"{pos:02d}.mp4"
            export_batches.ff("-y","-ss",f"{max(0,a/fps-.000001):.6f}","-i",source,"-frames:v",b-a,
                              "-map","0:v:0","-an","-sn","-dn","-c:v","copy",
                              "-map_metadata",-1,"-movflags","+faststart",tmp)
            try:
                stream = export_batches.video_info(tmp)
            except (ValueError, IndexError):
                tmp.unlink()
                continue
            if (int(stream.get("nb_frames",0))!=b-a or abs(float(stream["start_time"]))>.001 or
                    abs(float(stream["duration"])-(b-a)/fps)>.002 or
                    Fraction(stream["r_frame_rate"])!=Fraction(record["rate"])):
                tmp.unlink()
                continue
            wanted.append((row,a,b,0))
            files.append(tmp)
        if wanted:
            pack_intake.cool(76)
            entries = export_batches.verify_and_save(wanted,files,record,folder,
                                                       method="Original video packets copied at source keyframes")
            data["clips"].extend(entries)
            data["clips"].sort(key=lambda row:row["source_start"])
            pack_intake.save(manifest,data)
        print("PACKET_COPY",name,min(index+6,len(candidates)),"/",len(candidates),
              "verified",len(data["clips"]),flush=True)


def publish():
    for name, (_, title, _) in pack_intake.PACKS.items():
        work = WORK / name
        path = pack_intake.MOVIES / title / "catalogue.json"
        if not path.exists():
            continue
        data = pack_intake.load(path)
        if not data.get("selection_complete"):
            continue
        packet, selected = selected_rows(name)
        scan = data["scan"]
        scan["representative_candidate_frames_reviewed"] = len(packet["candidates"])
        scan["editorial_leads"] = len(selected)
        scan["verified_excerpts"] = len(data["clips"])
        evidence = work / "selection-evidence.json"
        if evidence.exists():
            records = pack_intake.load(evidence)
            scan["local_boundary_checks"] = len(records)
            scan["local_boundary_sample_interval_seconds"] = .5
        scan["continuous_playback_reviewed"] = False
        pack_intake.save(path, data)
    publish_library.publish(complete_only=True)


def export_sparse_ranges(name):
    """Verify sparse precise trims together without decoding long gaps between them."""
    original_encode = export_batches.encode
    original_batches = export_batches.batches

    def groups(rows, _span):
        group, seconds = [], 0.0
        for row in rows:
            duration = row["end"] - row["start"]
            if group and (len(group) == 5 or seconds + duration > 27):
                yield group
                group, seconds = [], 0.0
            group.append(row)
            seconds += duration
        if group:
            yield group

    def encode(source, record, rows, scratch):
        scratch.mkdir(parents=True)
        wanted, files = [], []
        for index, cluster in enumerate(original_batches(rows, 24)):
            if index:
                pack_intake.cool(79)
            spans, paths = original_encode(source, record, cluster, scratch / str(index))
            for path in paths:
                target = scratch / f"{len(files):03d}.mp4"
                path.replace(target)
                files.append(target)
            wanted.extend(spans)
        pack_intake.cool(77)
        return wanted, files

    export_batches.batches = groups
    export_batches.encode = encode
    export_batches.cool = lambda _target: pack_intake.cool(77)
    export_batches.process(name)


if __name__ == "__main__":
    mode, *names = sys.argv[1:]
    if mode not in ("publish","plan"):
        pack_intake.require_guard(gpu=True)
    for name in names or pack_intake.PACKS:
        if mode == "scan":
            pack_intake.scan(name)
            screen_packs.candidates(name)
            candidate_sheets(name)
        elif mode == "scan-key":
            keyframe_scan(name)
            screen_packs.candidates(name)
            candidate_sheets(name)
        elif mode == "sheets":
            candidate_sheets(name)
        elif mode in ("plan","tight-review"):
            plan(name,tight=mode=="tight-review")
        elif mode == "tight-export":
            plan(name,tight=True)
            copy_keyframe_ranges(name)
            export_batches.process(name)
        elif mode == "export-reviewed":
            copy_keyframe_ranges(name)
            export_batches.process(name)
        elif mode == "export-sparse":
            export_sparse_ranges(name)
        elif mode == "export":
            export_batches.process(name)
        elif mode != "publish":
            raise ValueError(mode)
    if mode == "publish":
        publish()
