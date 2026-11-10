"""
generate_transformer_audio.py -- Synthesize 60s transformer voiceover + word timestamps
"""
import json
import os
from pathlib import Path
import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx import Kokoro
from faster_whisper import WhisperModel

ROOT = Path("D:/J.A.R.V.I.S/Clipping")
MODEL = ROOT / "models" / "kokoro-v1.0.onnx"
VOICES = ROOT / "models" / "voices-v1.0.bin"
WHISPER_DIR = ROOT / "models" / "whisper"

SCRIPT = (
    "Your wall outlet pushes 240 Volts of raw electricity. "
    "If that touched your phone battery, it would explode instantly. "
    "So how does a transformer drop it down to just 5 Volts without a single moving part? "
    "Inside, two copper coils wrap around an iron core, but they never physically touch. "
    "When alternating current flows through the primary coil, it generates an invisible pulsating magnetic flux inside the core. "
    "Notice the core isn't a solid block. It is built from paper-thin laminated steel sheets. "
    "If it were solid, violent eddy currents would literally melt the iron from heat! "
    "As this magnetic field sweeps through the secondary coil, Faraday's Law forces electrons to move. "
    "Because the secondary coil has fewer turns, voltage drops from 240 Volts down to 60 Volts. "
    "Energy cannot be created or destroyed. As voltage drops, current surges four times higher! "
    "Flip the coils, and you get a step-up transformer, skyrocketing voltage to 480 Volts. "
    "That simple magnetic ratio powers our entire planet."
)

def main():
    print("[audio-gen] Loading Kokoro-82M ONNX model...")
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(MODEL), sess_options=options, providers=["CPUExecutionProvider"])
    kokoro = Kokoro.from_session(session, str(VOICES))

    voice = "am_michael"
    speed = 1.08
    print(f"[audio-gen] Synthesizing script with voice '{voice}' at speed {speed}x...")
    samples, sr = kokoro.create(SCRIPT, voice=voice, speed=speed, lang="en-us")

    out_dir = ROOT / "antigravity_anatomy" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / "transformer_voice.wav"
    sf.write(str(wav_path), samples, sr)
    duration = len(samples) / sr
    print(f"[audio-gen] Wrote {wav_path} ({duration:.2f} seconds)")

    print("[audio-gen] Loading faster-whisper on CPU for word timestamps...")
    whisper_local = ROOT / "models" / "whisper-small"
    model_path = str(whisper_local) if (whisper_local / "model.bin").is_file() else "small"
    whisper = WhisperModel(model_path, device="cpu", compute_type="int8", cpu_threads=2, download_root=str(WHISPER_DIR))

    print("[audio-gen] Transcribing word-level timestamps...")
    segments, _ = whisper.transcribe(str(wav_path), word_timestamps=True, language="en")

    words = []
    for seg in segments:
        for w in (seg.words or []):
            clean_word = w.word.strip().upper()
            words.append({
                "word": clean_word,
                "start": round(w.start, 3),
                "end": round(w.end, 3)
            })

    json_path = out_dir / "transformer_words.json"
    meta = {
        "text": SCRIPT,
        "durationSec": round(duration, 3),
        "wordCount": len(words),
        "words": words
    }
    json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"[audio-gen] Wrote {json_path} ({len(words)} aligned words)")

if __name__ == "__main__":
    main()
