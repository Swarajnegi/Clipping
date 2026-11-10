"""LAYER: Engineer. Guarded synthetic paired-export integration check.

THE BIG PICTURE: prove identical picture and retained source audio without private footage.
THE FLOW: generate tones/test picture -> normal builder -> packet/audio checks -> receipt.
The 440 Hz tone stands in for dialogue; this is technical QA, not editorial acceptance.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import build
from common import ROOT, WORK, OUT, FFMPEG, encoder, ffmpeg_command, probe, require_guard, run


def tone_level(path: Path, frequency: float) -> float:
    import numpy as np
    raw = subprocess.run(ffmpeg_command([FFMPEG, "-v", "error", "-i", str(path), "-vn", "-ac", "1",
                         "-ar", "16000", "-f", "f32le", "-"]), capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, dtype=np.float32)[4000:20000]
    phase = np.arange(len(audio)) / 16000
    return float(abs(np.sum(audio * np.exp(-2j * np.pi * frequency * phase))) / len(audio))


def main() -> int:
    require_guard(gpu=True)
    folder = WORK / "reference-pair-smoke"
    folder.mkdir(parents=True, exist_ok=True)
    master, bed = folder / "source.mp4", folder / "bed.wav"
    run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
         "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "2",
         *encoder(22), "-c:a", "aac", "-shortest", str(master)])
    run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=880:sample_rate=48000",
         "-t", "2", str(bed)])
    (folder / "source.json").write_text(json.dumps({"path": str(master), "title": "Synthetic paired-export QA"}), encoding="utf-8")
    (folder / "transcript.json").write_text(json.dumps([{"start":0,"end":2,"text":"Reference layout test",
       "words":[{"w":"Reference","s":0,"e":0.5},{"w":"layout","s":0.5,"e":1.2},{"w":"test","s":1.2,"e":2}]}]),encoding="utf-8")
    spec = {"id": folder.name, "pairedExports": True,
            "brand": {"music": {"file": str(bed), "db": -12, "fadeOutSec": 0.25}},
            "clips": [{"n": 1, "type": "gaming", "start": 0, "end": 2,
                       "referenceEdit":{"profile":"restrained"},
                       "cutaways":[{"file":str(master),"start":0.5,"end":1,"t":0.8}],
                       "captions": True, "hook": "SYNTHETIC EXPORT CHECK"},
                      {"n": 2, "type": "gaming", "start":0,"end":2,"captions":True,
                       "referenceEdit":{"profile":"kinetic","emphasis":[{"t":0.5,"dur":1,"text":"100%", "size":100}]}}]}
    spec_path = folder / "clips.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    sys.argv = ["build.py", str(spec_path)]
    build.main()
    clean, mixed = OUT / folder.name / "clip_01_music-free.mp4", OUT / folder.name / "clip_01.mp4"
    levels = {"clean_source": tone_level(clean, 440), "mixed_source": tone_level(mixed, 440),
              "clean_bed": tone_level(clean, 880), "mixed_bed": tone_level(mixed, 880)}
    assert 0.055 < levels["clean_source"] < 0.07 and levels["mixed_source"] > 0.02, levels
    assert levels["mixed_bed"] > 0.005 and levels["clean_bed"] < 0.002, levels
    assert abs(levels["mixed_source"] - levels["clean_source"]) < 0.005, levels
    for number in (1,2):
        pair=json.loads((OUT/folder.name/f"clip_{number:02d}_pair.json").read_text())
        assert pair['picture_match']
    receipt = {"technical_qa_passed": True, "editorial_qa": "synthetic only", "audio_levels": levels,
               "picture_match": build.matching_pictures(build.picture_signature(clean), build.picture_signature(mixed)),
               "duration": probe(clean).duration}
    (OUT / folder.name / "verification.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
