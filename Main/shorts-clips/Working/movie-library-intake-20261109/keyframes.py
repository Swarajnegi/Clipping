import json
import subprocess
from pathlib import Path
from statistics import quantiles

work = Path(__file__).resolve().parent
movies = work.parents[1] / "Movie Clips"
ffprobe = work.parents[3] / ".runtime/ffmpeg/bin/ffprobe.exe"
for source in sorted(movies.glob("*.mp4")):
    command = [str(ffprobe), "-v", "error", "-select_streams", "v:0",
               "-show_packets", "-show_entries", "packet=pts_time,flags",
               "-of", "csv=p=0", str(source)]
    keys = []
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True) as proc:
        for row in proc.stdout:
            fields = row.strip().split(",")
            if len(fields) >= 2 and "K" in fields[1]:
                keys.append(float(fields[0]))
        if proc.wait():
            raise RuntimeError(source.name)
    gaps = [b-a for a,b in zip(keys, keys[1:])]
    (work / f"{source.stem}-keys.json").write_text(json.dumps(keys), encoding="utf-8")
    print(source.name, len(keys), "keyframe gap quartiles", [round(g,2) for g in quantiles(gaps, n=4)],
          "max", round(max(gaps),2), flush=True)
