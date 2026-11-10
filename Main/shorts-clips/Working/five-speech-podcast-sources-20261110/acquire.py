"""Check original identity and acquire bounded source windows for editorial review."""
import json
import sys
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from common import probe, require_guard
from source_quality import PRODUCTION_FORMAT, PRODUCTION_SORT, compatible_4k_available, quality_record

def read(name):
    return json.loads((WORK / name).read_text(encoding="utf-8-sig"))

def save(name, value):
    (WORK / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

def main(mode):
    if mode == "download":
        require_guard(gpu=True)
    catalogue = {row["video_id"]: row for row in read("catalogue.json")["episodes"]}
    brief = read("brief.json")
    for folder in ("metadata","sources"):
        (WORK / folder).mkdir(exist_ok=True)
    for row in read("candidates.json"):
        video = row["video_id"]
        name = row["id"]
        url = catalogue[video]["canonical_url"]
        assert brief["permissions"][video]
        opts = dict(quiet=True, no_warnings=True, noplaylist=True,
                    cachedir=str(ROOT / ".runtime/yt-dlp-cache"), remote_components={"ejs:github"},
                    js_runtimes={"node":{"path":str(ROOT / ".runtime/node/node.exe")}},
                    format=PRODUCTION_FORMAT, format_sort=PRODUCTION_SORT, format_sort_force=True,
                    ffmpeg_location=str(ROOT / ".runtime/ffmpeg/bin"), retries=0, fragment_retries=0,
                    extractor_retries=0, socket_timeout=25)
        dest = WORK / f"sources/{name}.mp4"
        if mode == "download":
            if (WORK / f"sources/{name}.json").exists():
                continue
            if dest.exists():
                raise FileExistsError(dest)
            opts.update(outtmpl=str(dest), merge_output_format="mp4",
                        download_ranges=download_range_func(None,[row["context"]]),
                        external_downloader_args={"ffmpeg_i":["-threads","2"],"ffmpeg_o":["-threads","2"]},
                        postprocessor_args={"ffmpeg":["-threads","2"]})
        try:
            with YoutubeDL(opts) as yt:
                info = yt.extract_info(url, download=mode == "download")
            if info["id"] != video or (catalogue[video]["channel_id"] and
                                      info.get("channel_id") != catalogue[video]["channel_id"]):
                raise ValueError("Source identity mismatch")
            available = compatible_4k_available(info)
            record = dict(row, canonical_url=url, title=info["title"], uploader=info.get("channel"),
                          compatible_4k_available=available, reuse_basis=brief["reuse_basis"],
                          selected_formats=[{k:f.get(k) for k in ("format_id","width","height","fps","language","vcodec","acodec")}
                                            for f in info.get("requested_formats",[])])
            if mode == "download":
                media = probe(dest)
                record.update(quality=quality_record(media.width,media.height,available),
                              duration=media.duration,rate=media.rate, fps=media.fps,file=str(dest))
                if available and not record["quality"]["native_4k"]:
                    raise ValueError("Download fell below available 4K")
                save(f"sources/{name}.json",record)
                print(name,media.width,media.height,media.rate,media.duration,flush=True)
            else:
                save(f"metadata/{video}.json",record)
                print(name,available,record["selected_formats"],flush=True)
        except Exception as error:
            from moment_research import safe_error
            save(f"{mode}-{video}-error.json",dict(canonical_url=url,error=safe_error(error)))
            print("FAILED",name,safe_error(error),flush=True)

if __name__ == "__main__":
    main(sys.argv[1])
