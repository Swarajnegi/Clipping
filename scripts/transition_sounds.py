"""Validate clip-body transition cues and add licensed, frame-aligned one-shots."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from common import FFMPEG, ROOT, probe, require_guard, run

LIBRARY = ROOT / "Main/shorts-clips/SFX"
MANIFEST = ROOT / ".agents/skills/viral-shorts/assets/transition-sounds.json"
PRESETS = {"inversion-flicker", "bw-inverted-shock", "blu-ray-scanning", "retro-exposure"}
SAMPLE_RATE = 48000


def resolve_cues(cues: list[dict], frame_count: int, fps: float, reference_edit: dict | None) -> dict:
    """Check the authored edit and return the local audio records that its cues use."""
    if not isinstance(cues, list):
        raise ValueError("transitionCues must be an array")
    if not cues:
        return {}
    if not (reference_edit or {}).get("frame"):
        raise ValueError("transitionCues require an explicit referenceEdit.frame")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["sounds"]
    assets = {}
    previous = -math.ceil(fps)
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError("Each transition cue must be an object")
        frame = cue.get("frame")
        if type(frame) is not int or not 0 <= frame < frame_count:
            raise ValueError("Transition frame must be a zero-based frame inside the clip body")
        if frame - previous < math.ceil(fps):
            raise ValueError("Transition frames must be in order and at least one second apart")
        previous = frame
        preset = cue.get("preset")
        if not isinstance(preset, str) or preset not in PRESETS:
            raise ValueError(f"Unknown transition preset: {preset!r}")
        sound_id = cue.get("soundId")
        if sound_id is None:
            continue
        if not isinstance(sound_id, str) or sound_id not in manifest:
            raise ValueError(f"Unknown transition sound: {sound_id!r}")
        if sound_id in assets:
            continue
        file = LIBRARY / f"{sound_id}.wav"
        record = manifest[sound_id]
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"Missing or mismatched transition sound: {file}. See {MANIFEST}.")
        assets[sound_id] = {**record, "file": file}
    return assets


def mix_transition_sounds(source: Path, destination: Path, cues: list[dict], assets: dict,
                          fps: float, frame_count: int, *, intro_frames: int = 0,
                          source_gain_db: float = 0, dialogue: Path | None = None,
                          intro_audio: Path | None = None) -> None:
    """Retain rendered picture packets and align audio accents on the same frame clock."""
    require_guard()
    if not probe(dialogue or source).has_audio:
        raise ValueError("Transition sounds require an existing dialogue stream")
    if not math.isfinite(source_gain_db) or not -30 <= source_gain_db <= 0:
        raise ValueError("sourceAudioDb must be finite and between -30 and 0 dB")
    if (intro_audio and not dialogue) or (dialogue and bool(intro_frames) != bool(intro_audio)):
        raise ValueError("When mixing separate dialogue, supply separate audio for any intro")
    command = [FFMPEG, "-v", "error", "-y", "-i", str(source)]
    filters = []
    audio_index = 0
    if dialogue:
        command += ["-i", str(dialogue)]
        audio_index = 1
    speech = f"[{audio_index}:a:0]"
    if intro_audio:
        command += ["-i", str(intro_audio)]
        audio_index += 1
        intro_samples = round(intro_frames * SAMPLE_RATE / fps)
        format_audio = f"aresample={SAMPLE_RATE},aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS"
        filters.extend([
            f"[{audio_index}:a:0]{format_audio},apad=whole_len={intro_samples},"
            f"atrim=end_sample={intro_samples}[intro]",
            f"{speech}{format_audio}[body]",
            "[intro][body]concat=n=2:v=0:a=1[speech]",
        ])
        speech = "[speech]"
    filters.append(f"{speech}aresample={SAMPLE_RATE},volume={source_gain_db}dB[dialogue]")
    inputs = ["[dialogue]"]
    for cue in cues:
        sound_id = cue.get("soundId")
        if sound_id is None:
            continue
        audio_index += 1
        asset = assets[sound_id]
        start_ms = asset["startMs"]
        end_ms = asset["endMs"]
        # Retain a sweep's lead-in except where it would start before the clip body.
        body_ms = (cue["frame"] / fps) * 1000
        start_ms = max(start_ms, asset["accentMs"] - body_ms)
        delay_ms = intro_frames / fps * 1000 + body_ms + start_ms - asset["accentMs"]
        delay_samples = max(0, round(delay_ms * SAMPLE_RATE / 1000))
        duration = (end_ms - start_ms) / 1000
        fade = min(0.035, duration / 2)
        command += ["-i", str(asset["file"])]
        filters.append(
            f"[{audio_index}:a:0]aresample={SAMPLE_RATE},"
            f"atrim=start={start_ms/1000:.8f}:end={end_ms/1000:.8f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d=0.003,afade=t=out:st={duration-fade:.8f}:d={fade},"
            f"volume={asset['gainDb']}dB,adelay={delay_samples}S:all=1[s{audio_index}]"
        )
        inputs.append(f"[s{audio_index}]")
    end_sample = round(frame_count * SAMPLE_RATE / fps)
    filters.append(
        f"{''.join(inputs)}amix=inputs={len(inputs)}:duration=first:normalize=0,"
        f"alimiter=limit=0.95:level=0:latency=1,atrim=end_sample={end_sample}[a]"
    )
    run(command + ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[a]",
                   "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                   str(destination)])
