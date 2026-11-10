"""Download the original pipeline's portable tools and models, exclusively on D:."""
from __future__ import annotations

import hashlib
import argparse
import json
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / ".runtime/downloads"
DOWNLOADS.mkdir(parents=True, exist_ok=True)
RECEIPTS = []


def digest_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_json(url: str):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Clipping-Restoration"}), timeout=60) as response:
        return json.load(response)


def download(url: str, target: Path, sha256: str | None = None) -> Path:
    if target.exists() and (not sha256 or digest_file(target) == sha256):
        print("cached", target.name, flush=True)
    else:
        print("download", target.name, flush=True)
        part = target.with_suffix(target.suffix + ".part")
        position = part.stat().st_size if part.exists() else 0
        while True:
            request = urllib.request.Request(url, headers={"User-Agent": "Clipping-Restoration",
                "Range": f"bytes={position}-{position + 8 * 1024 * 1024 - 1}"})
            with urllib.request.urlopen(request, timeout=30) as response:
                content_range = response.headers.get("Content-Range", "")
                if response.status == 206:
                    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
                    if not match or int(match[1]) != position:
                        raise ValueError("Unexpected download range")
                    total = int(match[3])
                elif response.status == 200 and position == 0:
                    total = int(response.headers["Content-Length"]) if response.headers.get("Content-Length") else None
                else:
                    raise ValueError("Server cannot safely resume this download")
                before = position
                with part.open("ab" if position else "wb") as dest:
                    while chunk := response.read1(64 * 1024):
                        dest.write(chunk)
                        position += len(chunk)
                if position == before:
                    raise ValueError("Download made no progress")
            print(f"  {target.name}: {position / 1048576:.1f} MiB", flush=True)
            if total is None or position == total:
                break
            if position > total:
                raise ValueError("Download exceeded the declared file size")
        with part.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if sha256 and digest != sha256:
            raise ValueError("Checksum mismatch for " + target.name)
        part.replace(target)
    with target.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    RECEIPTS.append({"url": url, "path": str(target), "sha256": digest, "bytes": target.stat().st_size,
                     "upstream_checksum_verified": bool(sha256)})
    return target


def extract(archive: Path, target: Path, keep=None) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            if entry.is_dir():
                continue
            relative = Path(*Path(entry.filename).parts[1:])
            if keep and not keep(relative):
                continue
            dest = (target / relative).resolve()
            if not dest.is_relative_to(target.resolve()):
                raise ValueError("Archive path escapes destination")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(entry) as src, dest.open("wb") as output:
                shutil.copyfileobj(src, output, length=1024 * 1024)


def restore_ffmpeg() -> None:
    # FFmpeg 9's NVENC API 13.1 requires driver 610; this host exposes API 13.0.
    version = '8.0.1'
    ff_release = read_json(f"https://api.github.com/repos/GyanD/codexffmpeg/releases/tags/{version}")
    ff_asset = next(x for x in ff_release["assets"] if x["name"] == f"ffmpeg-{version}-essentials_build.zip")
    checksum = ff_asset["digest"].removeprefix("sha256:")
    ff = download(ff_asset['browser_download_url'], DOWNLOADS / f"ffmpeg-{version}-essentials.zip", checksum)
    extract(ff, ROOT / ".runtime/ffmpeg")


def main() -> None:
    from common import require_guard
    require_guard()
    parser = argparse.ArgumentParser()
    parser.add_argument('--ffmpeg-only', action='store_true')
    args = parser.parse_args()
    if args.ffmpeg_only:
        restore_ffmpeg()
        receipt = ROOT / '.runtime/pipeline-restore/assets.json'
        previous = json.loads(receipt.read_text(encoding='utf-8')) if receipt.exists() else []
        receipt.write_text(json.dumps(previous + RECEIPTS, indent=2), encoding='utf-8')
        return
    version = "v24.22.1"
    node_file = f"node-{version}-win-x64.zip"
    with urllib.request.urlopen(f"https://nodejs.org/dist/{version}/SHASUMS256.txt", timeout=60) as response:
        checksums = response.read().decode()
    checksum = next(line.split()[0] for line in checksums.splitlines() if line.endswith(node_file))
    node = download(f"https://nodejs.org/dist/{version}/{node_file}", DOWNLOADS / node_file, checksum)
    extract(node, ROOT / ".runtime/node")
    restore_ffmpeg()
    release = read_json("https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.1")
    for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
        item = next(x for x in release["assets"] if x["name"] == name)
        digest = item.get("digest") or ""
        download(item["browser_download_url"], ROOT / "models" / name, digest.removeprefix("sha256:") or None)
    pointer_url = "https://raw.githubusercontent.com/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
    with urllib.request.urlopen(pointer_url, timeout=60) as response:
        pointer = response.read().decode()
    checksum = next(line.split("sha256:")[1] for line in pointer.splitlines() if line.startswith("oid sha256:"))
    download("https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
             ROOT / "models/face_detection_yunet_2023mar.onnx", checksum)
    commit = '03ceb42f7fa2c4439aca01752118044baabffb8f'
    helper = download(f"https://codeload.github.com/bradautomates/claude-video/zip/{commit}", DOWNLOADS / f"claude-video-{commit}.zip")
    extract(helper, ROOT / ".runtime/claude-video")
    receipt = ROOT / ".runtime/pipeline-restore/assets.json"
    receipt.write_text(json.dumps(RECEIPTS, indent=2), encoding="utf-8")
    print("Portable assets restored:", len(RECEIPTS), "receipt:", receipt, flush=True)


if __name__ == "__main__":
    main()
