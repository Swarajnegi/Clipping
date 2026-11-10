"""Review available source windows and align speech to the local audio."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(WORK.parent / "movie-cutaway-test-20261109"))
from common import FFMPEG, ffmpeg_command, probe, require_guard
from cooling import cool
from prep import _load_whisper

def ff(*args):
    return subprocess.run(ffmpeg_command([FFMPEG, "-hide_banner", "-v", "error", "-xerror", *map(str,args)]),
                          capture_output=True, check=True).stdout

def main():
    require_guard(gpu=True)
    target = WORK / "qa"
    target.mkdir(exist_ok=True)
    model, device = _load_whisper("small")
    for entry in json.loads((WORK / "candidates.json").read_text()):
        name = entry["id"]
        src = WORK / f"sources/{name}.mp4"
        receipt = WORK / f"sources/{name}.json"
        if not receipt.exists():
            continue
        media = probe(src)
        aligned = WORK / f"sources/{name}-words.json"
        if not aligned.exists():
            cool()
            pcm = ff("-i",src,"-vn","-ac","1","-ar",16000,"-f","f32le","-")
            segments, _ = model.transcribe(np.frombuffer(pcm,np.float32),word_timestamps=True,
                                           vad_filter=True,language="en",beam_size=5)
            rows = [dict(start=s.start,end=s.end,text=s.text.strip(),
                         words=[dict(w=w.word.strip(),s=w.start,e=w.end,p=w.probability) for w in s.words or []])
                    for s in segments]
            aligned.write_text(json.dumps(dict(file=str(src),context_start=entry["context"][0],device=device,
                                               segments=rows),indent=2,ensure_ascii=False),encoding="utf-8")
            print("ALIGNED",name,len(rows),flush=True)
        sheet = target / f"{name}-context.jpg"
        if not sheet.exists():
            cool()
            count = int(media.duration // 4) + 1
            ff("-y","-hwaccel","cuda","-hwaccel_output_format","cuda","-i",src,"-an",
               "-vf",f"fps=1/4,scale_cuda=240:136:format=nv12,hwdownload,format=nv12,tile=5x{(count+4)//5}:padding=3:margin=3",
               "-frames:v",1,sheet)
            print("SAMPLED",name,flush=True)

if __name__ == "__main__":
    main()
