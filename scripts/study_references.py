"""LAYER: Engineer. Preserve evidence and inspection coverage for editing references.

THE BIG PICTURE: distinguish inventory, provider review and direct frame/transcript evidence.
THE FLOW: inventory unchanged originals -> selected cloud or guarded local evidence -> receipt.
Cloud mode only probes metadata and uploads full files; it does not process media locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import ROOT, FFMPEG, ffmpeg_command, probe, require_guard

BASE = ROOT / "Main/shorts-clips"
QUESTION = """Study this entire reference edit, including its audio. Return timestamped observations covering
the complete duration. Transcribe all intelligible speech verbatim with time ranges, flag uncertainty.
Record visible speakers, exact on-screen captions and watermark/account text, opening hook, setup,
payoff, ending, shot changes, framing, typography, grade, motion, effects and approximate cut rhythm.
Describe music mood, instruments, beat changes and relation to speech and cuts. Name a song only
when confidently recognisable; give evidence and confidence, otherwise say unidentified. Separate
what is observed from estimated settings. Identify the emotional appeal and topic. Do not infer
view counts, permissions, retention or virality. Give practical editing rules with timestamp examples.
State any part of the video/audio you could not inspect."""


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cloud_review(path: Path, folder: Path) -> dict:
    helper = ROOT / ".runtime/claude-video/skills/watch/scripts"
    sys.path.insert(0, str(helper))
    import config
    import gemini
    config.CONFIG_DIR = ROOT / ".runtime/watch"
    config.CONFIG_FILE = config.CONFIG_DIR / ".env"
    cfg = config.get_config()
    key = config.load_gemini_key()
    readiness = json.loads((config.CONFIG_DIR / "readiness.json").read_text(encoding="utf-8"))
    if (not key or config.read_env_file().get("WATCH_FREE_TIER_CONFIRMED") != "1"
            or readiness.get("key_fingerprint") != hashlib.sha256(key.encode()).hexdigest()
            or not readiness.get("model_list_verified") or readiness.get("model") != cfg["gemini_model"]):
        raise RuntimeError("Cloud review needs the existing verified model and confirmed free-tier configuration")
    uploaded = None
    receipt = {"route": "gemini_full_file", "model": cfg["gemini_model"], "status": "failed",
               "local_frames_inspected": False, "local_transcript_verified": False}
    try:
        uploaded = gemini.upload_file(path, key, max_wait=180)
        receipt["upload_name"] = uploaded["name"]
        answer = gemini.ask({"uri": uploaded["uri"], "mime_type": uploaded["mime_type"]},
                            QUESTION, model=cfg["gemini_model"], key=key, timeout=240)
        (folder / "provider-review.txt").write_text(answer["text"], encoding="utf-8")
        receipt.update(status="provider_review_complete", total_tokens=answer.get("total_tokens"),
                       coverage="Full file submitted; timestamped provider assessment, not direct assistant playback")
    finally:
        if uploaded:
            warning = gemini.delete_file(uploaded["name"], key)
            receipt["deletion_confirmed"] = warning is None
            receipt["deletion_warning"] = warning
        save(folder / "cloud-receipt.json", receipt)
    return receipt


def local_evidence(path: Path, folder: Path, duration: float) -> dict:
    require_guard(gpu=True)
    from prep import transcribe
    transcript_path = folder / "transcript.json"
    if not transcript_path.exists():
        segments = transcribe(probe(path), "small", "en")
        save(transcript_path, segments)
    frames = folder / "frames"
    frames.mkdir(exist_ok=True)
    subprocess.run(ffmpeg_command([FFMPEG, "-v", "error", "-y", "-i", str(path),
                    "-vf", "fps=1,scale=270:-2", str(frames / "%04d.jpg")]), check=True)
    from PIL import Image, ImageDraw
    files = sorted(frames.glob("*.jpg"))
    for start in range(0, len(files), 24):
        chunk = files[start:start + 24]
        sheet = Image.new("RGB", (1080, 6 * 505), "#171717")
        draw = ImageDraw.Draw(sheet)
        for index, file in enumerate(chunk):
            x, y = (index % 4) * 270, (index // 4) * 505
            with Image.open(file) as frame:
                sheet.paste(frame, (x, y + 22))
            draw.text((x + 5, y + 4), f"{start + index + 0.5:.1f}s", fill="white")
        sheet.save(folder / f"sheet-{start // 24 + 1:02d}.jpg")
    receipt = {"route": "guarded_local", "status": "evidence_prepared", "duration": duration,
               "frame_cadence_seconds": 1, "frames": len(files), "assistant_inspected": False,
               "audio_playback_inspected": False, "transcript": "CUDA faster-whisper small"}
    save(folder / "local-receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["inventory", "cloud", "local"], default="inventory")
    parser.add_argument("--only", help="Exact reference filename")
    args = parser.parse_args()
    if args.mode == "local":
        require_guard(gpu=True)
    output = BASE / "Working/reference-analysis"
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in sorted((BASE / "Reference").rglob("*.mp4")):
        if args.only and path.name != args.only:
            continue
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        folder = output / digest[:12]
        folder.mkdir(exist_ok=True)
        media = probe(path)
        stat = path.stat()
        record = {"file": str(path.relative_to(BASE / "Reference")), "sha256": digest,
                  "size": stat.st_size, "modified_ns": stat.st_mtime_ns, "duration": media.duration,
                  "width": media.width, "height": media.height, "rate": media.rate,
                  "role": "editing_target" if path.name in (
                      "WhatsApp Video 2026-11-01 at 11.54.55 AM.mp4",
                      "WhatsApp Video 2026-11-01 at 11.58.27 AM.mp4") else "taste_reference"}
        save(folder / "identity.json", record)
        entries.append({**record, "evidence_dir": str(folder.relative_to(output))})
        print(f"{args.mode}: {path.name} ({media.duration:.2f}s)", flush=True)
        if args.mode == "cloud" and not (folder / "provider-review.txt").exists():
            try:
                cloud_review(path, folder)
            except (SystemExit, Exception) as exc:
                save(output / "last-failure.json", {"file": path.name, "mode": args.mode, "error": str(exc)})
                print(str(exc), file=sys.stderr)
                return 2
        elif args.mode == "local":
            local_evidence(path, folder, media.duration)
    if not entries:
        raise SystemExit("No matching reference videos found")
    save(output / "inventory.json", {"generated_at": datetime.now(timezone.utc).isoformat(), "files": entries})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
