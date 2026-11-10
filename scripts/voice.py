"""
voice.py -- free local voiceover for the transformative intro.

THE BIG PICTURE
    A raw clip with captions is "reused content" on YouTube and TikTok: it does not get
    monetized and collects unoriginal-content strikes. The minimum all three studied
    creators converge on is a short scripted voiceover that gives context before the clip
    rolls. Kokoro-82M (Apache-2.0, ONNX, CPU) renders that voice for free; faster-whisper
    then re-transcribes the rendered audio so the intro's captions are word-exact.

THE FLOW
    1. Kokoro synthesizes the script -> 24 kHz wav.
    2. faster-whisper (already used by prep.py) returns word timestamps for that wav.
    3. Write <out>.wav + <out>.json ({durationSec, words:[{w,s,e}]}).

Usage: python scripts/voice.py "script text" --out work/<id>/intro_01 [--voice am_michael] [--speed 1.1]
       python scripts/voice.py --list-voices
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, require_guard  # noqa: E402

MODEL = ROOT / "models" / "kokoro-v1.0.onnx"
VOICES = ROOT / "models" / "voices-v1.0.bin"


def synth(text: str, out: Path, voice: str, speed: float) -> dict:
    require_guard()
    from common import wait_headroom
    wait_headroom()
    import onnxruntime as ort
    import soundfile as sf
    from kokoro_onnx import Kokoro

    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(MODEL), sess_options=options, providers=["CPUExecutionProvider"])
    kokoro = Kokoro.from_session(session, str(VOICES))
    samples, sr = kokoro.create(text, voice=voice, speed=speed, lang="en-us")
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    sf.write(wav, samples, sr)

    from prep import _load_whisper

    model, _ = _load_whisper("small")
    segments, _ = model.transcribe(str(wav), word_timestamps=True, language="en")
    words = [{"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3)}
             for seg in segments for w in (seg.words or [])]
    meta = {"text": text, "voice": voice, "speed": speed,
            "durationSec": round(len(samples) / sr, 3), "words": words,
            "transcription_device": model.model.device,
            "voice_backend": "onnxruntime CPUExecutionProvider", "voice_threads": 2}
    out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--out", default="work/_voice/test")
    ap.add_argument("--voice", default="am_michael")
    ap.add_argument("--speed", type=float, default=1.1)
    ap.add_argument("--list-voices", action="store_true")
    args = ap.parse_args()

    if args.list_voices:
        import numpy as np
        with np.load(VOICES) as voices:
            print(" ".join(sorted(voices.files)))
        return 0
    if not args.text:
        ap.error("text required")
    meta = synth(args.text, ROOT / args.out, args.voice, args.speed)
    print(f"{meta['durationSec']:.2f}s, {len(meta['words'])} words -> {ROOT / args.out}.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
