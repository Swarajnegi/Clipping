"""One bounded acquisition attempt to verify the target-A original source clock."""
import json
import sys
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from common import FFMPEG, ffmpeg_command, probe, require_guard

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--start',type=float,default=3080)
    parser.add_argument('--end',type=float,default=3140)
    parser.add_argument('--name',default='rob-moore')
    args=parser.parse_args()
    require_guard(gpu=True)
    import yt_dlp
    from yt_dlp.utils import download_range_func
    from prep import transcribe
    folder = Path(__file__).parent / "original-check"
    folder.mkdir(exist_ok=True)
    url = "https://www.youtube.com/watch?v=Tvqz9_aHhoQ"
    receipt = {"url":url,"requested_source_range":[args.start,args.end],"status":"failed","reuse_permission":"unknown"}
    try:
        opts = {"outtmpl":str(folder / (args.name+'.%(ext)s')), "format":"b[height<=720][ext=mp4]/bv*[height<=720]+ba/b",
                "merge_output_format":"mp4", "ffmpeg_location":str(ROOT / ".runtime/ffmpeg/bin"),
                "cachedir":False,"retries":0,"fragment_retries":0,"extractor_retries":0,"socket_timeout":20,
                "js_runtimes":{"node":{"path":str(ROOT / ".runtime/node/node.exe")}},
                "download_ranges":download_range_func(None,[(args.start,args.end)]),
                "external_downloader_args":{"ffmpeg":["-threads","2","-filter_threads","2","-filter_complex_threads","2"]}}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(url,download=True)
        path=folder / (args.name+'.mp4')
        media=probe(path)
        receipt.update(status="sample_downloaded",duration=media.duration,source_start=info.get("section_start"),
                       note="Source-clock alignment must be checked against the transcript; this is discovery evidence, not a deliverable.")
        transcript=transcribe(media,"small","en")
        (folder / (args.name+'-transcript.json')).write_text(json.dumps(transcript,indent=2),encoding="utf-8")
        subprocess.run(ffmpeg_command([FFMPEG,"-v","error","-y","-ss","25","-i",str(path),"-frames:v","1",str(folder / (args.name+'-frame.jpg'))]),check=True)
        receipt["status"]="evidence_prepared"
    except Exception as exc:
        receipt["error"]=str(exc)
        print(str(exc),flush=True)
    finally:
        (folder / (args.name+'-receipt.json')).write_text(json.dumps(receipt,indent=2),encoding="utf-8")
    return 0 if receipt["status"]=="evidence_prepared" else 2

if __name__=="__main__":
    raise SystemExit(main())
