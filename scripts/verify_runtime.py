"""Verify the restored runtime with synthetic media, never a user's private footage.

LAYER: Engineer. THE BIG PICTURE: executable evidence distinguishes detection from GPU use.
THE FLOW: inspect modules -> synthesize speech -> NVENC source -> prep/sheet/build -> receipt.
Run through the resource guard; --smoke additionally exercises models and the renderer.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import FFMPEG, ROOT, WORK, OUT, encoder, probe, require_guard, run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    require_guard(gpu=args.smoke)
    versions = {name: importlib.metadata.version(name) for name in (
        "yt-dlp", "faster-whisper", "ctranslate2", "kokoro-onnx", "onnxruntime", "opencv-python-headless")}
    sources = [*ROOT.glob('scripts/*.py'), *ROOT.glob('src/*'), ROOT / 'remotion.config.ts',
               ROOT / 'package-lock.json', ROOT / 'requirements.lock.txt']
    receipt = {"versions": versions, "python": sys.executable, "synthetic_only": True,
               "verified_at": datetime.now(timezone.utc).isoformat(),
               "guard_job": os.environ['CLIPPING_GUARD_JOB'], "cpu_limit_percent": 25,
               "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sources if p.is_file()}}
    import numpy as np
    import cv2
    cv2.setNumThreads(2)
    detector = cv2.FaceDetectorYN.create(str(ROOT / "models/face_detection_yunet_2023mar.onnx"), "", (320, 180))
    detector.detect(np.zeros((180, 320, 3), dtype=np.uint8))
    receipt["face_detector_loaded"] = True
    print(json.dumps(receipt, indent=2), flush=True)
    if not args.smoke:
        return 0
    vid = "restoration_smoke"
    work = WORK / vid
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "scripts/voice.py", "Choose a moment. Keep the story clear.",
                    "--out", str(work / "source_voice")], cwd=ROOT, check=True)
    voice = json.loads((work / "source_voice.json").read_text(encoding="utf-8"))
    if voice["transcription_device"] != "cuda" or not voice["words"]:
        raise RuntimeError("CUDA transcription did not produce timestamped words")
    receipt["voice"] = voice
    source = ROOT / ".runtime/pipeline-restore/restoration_smoke.mp4"
    run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30000/1001",
         "-i", str(work / "source_voice.wav"), "-t", "4", "-af", "apad", *encoder(),
         "-c:a", "aac", "-r", "30000/1001", str(source)])
    receipt["source_rate"] = probe(source).rate
    subprocess.run([sys.executable, "scripts/prep.py", str(source), "--lang", "en"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/sheet.py", vid, "0-3.5", "--frames", "3", "--name", "runtime_check"], cwd=ROOT, check=True)
    spec = {"id": vid, "brand": {"style": "bold"}, "clips": [{"n": 1, "start": 0, "end": 2,
        "type": "talk", "trackMode": "group", "hook": "GPU runtime check", "intro": "Here is the test.", "introFrameAt": 0.5,
        "title": "Synthetic restoration check", "description": "Generated test media, not an upload candidate."}]}
    spec_path = work / "clips.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    render_log = ROOT / ".runtime/pipeline-restore/render-smoke.log"
    with render_log.open("w", encoding="utf-8") as output_log:
        subprocess.run([sys.executable, "scripts/build.py", str(spec_path)], cwd=ROOT,
                       stdout=output_log, stderr=subprocess.STDOUT, check=True)
    if "h264_nvenc" not in render_log.read_text(encoding="utf-8").lower():
        raise RuntimeError("Rendered output exists but the render log does not establish NVENC use")
    video = OUT / vid / "clip_01.mp4"
    output = probe(video)
    receipt.update({"output": str(video), "output_rate": output.rate, "width": output.width, "height": output.height,
                    "duration": output.duration, "has_audio": output.has_audio,
                    "qa_strip": str(OUT / vid / "qa/clip_01.jpg"), "gpu_transcription_verified": True,
                    "nvenc_required": True, "actual_encoder": "h264_nvenc", "encoder_log": str(render_log),
                    "renderer_concurrency": 1})
    if not output.has_audio or output.rate != "30000/1001":
        raise RuntimeError("Audio or exact source frame rate was not preserved")
    path = ROOT / ".runtime/pipeline-restore/verification.json"
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("Runtime smoke passed:", path, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
