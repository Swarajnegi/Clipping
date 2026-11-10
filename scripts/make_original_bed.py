"""LAYER: Engineer. Original quiet instrumental bed from oscillators, without samples.

THE BIG PICTURE: draft audio has explicit provenance instead of borrowing a reference song.
THE FLOW: synthesize a slow minor-key pad and pulse -> peak-limit -> PCM WAV + provenance.
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

from common import ROOT, require_guard


def main() -> int:
    require_guard()
    import numpy as np
    rate, duration = 48000, 36
    samples = int(rate * duration)
    audio = np.zeros((samples, 2), dtype=np.float64)
    chords = [(130.8128,155.5635,195.9977), (103.8262,130.8128,155.5635),
              (155.5635,195.9977,233.0819), (116.5409,146.8324,174.6141)]
    for index in range(6):
        start = index * 6
        length = min(7, duration - start)
        t = np.arange(int(length * rate)) / rate
        envelope = np.minimum(t / 0.8, 1) * np.minimum((length - t) / 1.2, 1)
        for note in chords[index % len(chords)]:
            left = np.sin(2 * np.pi * note * t) + 0.15 * np.sin(4 * np.pi * note * t)
            right = np.sin(2 * np.pi * (note * 1.0007) * t)
            audio[start*rate:start*rate+len(t), 0] += 0.06 * left * envelope
            audio[start*rate:start*rate+len(t), 1] += 0.06 * right * envelope
    for beat in np.arange(0, duration - 0.25, 0.75):
        t = np.arange(int(0.25 * rate)) / rate
        pulse = 0.035 * np.sin(2 * np.pi * (65 * t - 55 * t*t)) * np.exp(-20*t)
        begin = int(beat * rate)
        audio[begin:begin+len(t)] += pulse[:,None]
    audio *= 0.32 / max(0.32, float(np.max(np.abs(audio))))
    path = ROOT / "music/original-minor-bed-v1.wav"
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Preserve existing music asset: {path}")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes((audio * 32767).astype("<i2").tobytes())
    path.with_suffix(".provenance.json").write_text(json.dumps({
        "origin":"Original procedural composition made for the owner's clipping project",
        "external_samples":[],"reference_recordings_used":False,"voice_or_lyrics":False,
        "generator":"scripts/make_original_bed.py","duration":duration,"sample_rate":rate,
        "purpose":"Quiet draft bed; reference-song matching and listening acceptance remain open"},indent=2),encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
