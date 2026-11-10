"""Render bounded music-free editorial proofs at the native source cadence."""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(WORK.parent/"movie-cutaway-test-20261109"))
from common import FFMPEG, encoder, ffmpeg_command, probe, require_guard
from cooling import cool
from motion_edit import decode, video_clock

def run(*args):
    subprocess.run(ffmpeg_command([FFMPEG,"-hide_banner","-v","error","-xerror",*map(str,args)]),check=True)

def main():
    require_guard(gpu=True)
    out = WORK / "drafts"
    out.mkdir(exist_ok=True)
    mask = out / "rounded-square-mask.png"
    image = Image.new("L",(980,980),0)
    ImageDraw.Draw(image).rounded_rectangle((0,0,979,979),radius=48,fill=255)
    image.save(mask)
    for entry in json.loads((WORK/"proof-cuts.json").read_text(encoding="utf-8")):
        name = entry["id"]
        source = WORK / f"sources/{name}.mp4"
        media = probe(source)
        proof = out / f"{name}-ROUGH.mp4"
        receipt = out / f"{name}-rough.json"
        if receipt.exists():
            assert proof.is_file()
            continue
        if proof.exists():
            raise FileExistsError(proof)
        cool()
        inputs = []
        graph = []
        joins = []
        frames = 0
        for i, span in enumerate(entry["cuts"]):
            a,b = [round(span[key]*media.fps) for key in ("start","end")]
            n = b-a
            assert 0 <= a < b <= round(media.duration*media.fps)
            seconds = n/media.fps
            frames += n
            inputs.extend(("-hwaccel","cuda","-hwaccel_output_format","cuda","-ss",f"{a/media.fps:.9f}","-i",source))
            size = min(media.width, media.height)//2*2
            left = round(max(0,min(media.width-size,span.get("x",.5)*media.width-size/2))/2)*2
            graph.extend((
                f"[{i}:v]scale_cuda=format=nv12,hwdownload,format=nv12,trim=end_frame={n},setpts=N/(({media.rate})*TB),"
                f"crop={size}:{size}:{left}:(ih-oh)/2,scale=980:980,setsar=1,format=rgb24[v{i}]",
                f"[{i}:a]atrim=duration={seconds:.9f},asetpts=PTS-STARTPTS,aresample=48000,"
                f"afade=t=in:d=0.012,afade=t=out:st={seconds-.012:.9f}:d=0.012[a{i}]",
            ))
            joins.append(f"[v{i}][a{i}]")
        count = len(joins)
        graph.extend((
            "".join(joins)+f"concat=n={count}:v=1:a=1[p][dialogue]",
            f"[p]fps={media.rate},tpad=stop_mode=clone:stop=2,trim=end_frame={frames}[timed]",
            f"[timed][{count}:v]alphamerge=shortest=1[fg]",
            f"color=c=black:s=1080x1920:r={media.rate}:d={(frames+2)/media.fps:.9f}[bg]",
            f"[bg][fg]overlay=50:470:shortest=1,format=yuv420p,trim=end_frame={frames},setpts=N/(({media.rate})*TB)[out]",
        ))
        run("-y",*inputs,"-loop",1,"-framerate",media.rate,"-i",mask,"-filter_complex",";".join(graph),
            "-map","[out]","-map","[dialogue]",*encoder(19),"-r",media.rate,"-fps_mode","cfr",
            "-c:a","aac","-b:a","192k","-map_metadata",-1,"-movflags","+faststart",proof)
        clock = video_clock(proof)
        assert clock["frames"] == frames and clock["rate"] == media.rate and clock["regular"],clock
        decode(proof,frames)
        run("-i",proof,"-map","0:a:0","-f","null","-")
        receipt.write_text(json.dumps(dict(entry,clock=clock,proof=str(proof),media_decode=True,
                                           source_dimensions=[media.width,media.height]),
                                      indent=2,ensure_ascii=False),encoding="utf-8")
        print("PROOF",name,clock["duration"],clock["rate"],flush=True)

if __name__ == "__main__":
    main()
