"""
prep.py -- turn a URL or local file into everything Claude needs to pick viral moments.

THE BIG PICTURE
    Claude is the editor, but it cannot hear a waveform or feel motion. This script
    does the mechanical perception so the judgment step reads compact evidence:
    a word-timestamped transcript, an audio energy/onset timeline, scene-cut
    positions and -- for YouTube sources -- the "most replayed" heatmap, which is
    real viewer behaviour and the single strongest free virality signal available.

    Lesson from the failed MW4 run: raw onset density rewards monotony (firing
    ranges, killcam replays scored highest and were worthless). The timeline
    therefore reports energy VARIANCE alongside onsets, and never picks clips on
    its own -- it ranks, Claude looks.

THE FLOW
    1. Resolve input: native 4K preferred (supported non-AV1 codec), or copy-free local path.
    2. ffprobe metadata.
    3. faster-whisper word timestamps (CUDA int8_float16; fail visibly if unavailable).
    4. 8 kHz audio envelope -> per-second loudness, onsets, variance.
    5. ffmpeg scene detection on a 320px proxy.
    6. Write work/<id>/{source.json, transcript.json, transcript.txt, signals.json, timeline.txt}.

Usage: python scripts/prep.py <url|file> [--model small] [--no-transcribe] [--lang en]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterator

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FFMPEG, ROOT, WORK, Media, ffmpeg_command, mmss, probe, require_guard, slug  # noqa: E402

SR = 8000
from source_quality import PRODUCTION_FORMAT, PRODUCTION_SORT, compatible_4k_available, quality_record


def fetch(target: str, work_id: str | None = None) -> tuple[str, Path, dict]:
    if work_id and (slug(work_id) != work_id or len(work_id) > 60):
        raise ValueError("--work-id must be a safe 1–60 character filename (letters, digits, _ or -)")
    if re.match(r"https?://", target):
        import yt_dlp

        probe_opts = {"quiet": True, "skip_download": True, "cachedir": str(ROOT / ".runtime/yt-dlp-cache"),
                      "remote_components": {"ejs:github"},
                      "js_runtimes": {"node": {"path": str(ROOT / ".runtime/node/node.exe")}}}
        with yt_dlp.YoutubeDL(probe_opts) as ydl:
            info = ydl.extract_info(target, download=False)
        vid = work_id or slug(info.get("id") or info.get("title", "video"))
        work = WORK / vid
        work.mkdir(parents=True, exist_ok=True)
        dest = work / "source.mp4"
        existing = work / "source.json"
        identity = f"{info.get('extractor_key') or info.get('extractor')}:{info.get('id')}"
        if existing.exists():
            previous = json.loads(existing.read_text(encoding="utf-8"))
            if previous.get("source_key") != identity and previous.get("url") != target:
                raise ValueError(f"Staging ID {vid} belongs to another source; use a unique --work-id")
        elif dest.exists():
            raise ValueError(f"Unverified cached master at {dest}; preserve it and choose another --work-id")
        if dest.exists() and compatible_4k_available(info):
            cached = probe(dest)
            if not quality_record(cached.width, cached.height, True)['native_4k']:
                raise ValueError(f"Cached source is {cached.width}x{cached.height}, but compatible native 4K is available. "
                                 "Preserve this revision and use a new --work-id to acquire the 4K master.")
        if not dest.exists():
            opts = {
                **probe_opts,
                "quiet": True,
                "skip_download": False,
                "format": PRODUCTION_FORMAT,
                "format_sort": PRODUCTION_SORT,
                "format_sort_force": True,
                "merge_output_format": "mp4",
                "outtmpl": str(work / "source.%(ext)s"),
                "ffmpeg_location": str(Path(FFMPEG).parent) if Path(FFMPEG).exists() else None,
            }
            with yt_dlp.YoutubeDL({k: v for k, v in opts.items() if v is not None}) as ydl:
                ydl.download([target])
        meta = {
            "source_key": identity,
            "url": target,
            "title": info.get("title"),
            "channel": info.get("channel") or info.get("uploader"),
            "view_count": info.get("view_count"),
            "duration": info.get("duration"),
            "chapters": info.get("chapters") or [],
            "heatmap": info.get("heatmap") or [],
            "description": (info.get("description") or "")[:2000],
            "compatible_4k_available": compatible_4k_available(info),
        }
        return vid, dest, meta

    path = Path(target).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"not found: {path}")
    vid = work_id or slug(path.stem)
    existing = WORK / vid / "source.json"
    if existing.exists() and Path(json.loads(existing.read_text(encoding="utf-8"))["path"]).resolve() != path:
        raise ValueError(f"Staging ID {vid} belongs to another local file; use a unique --work-id")
    (WORK / vid).mkdir(parents=True, exist_ok=True)
    return vid, path, {"url": None, "title": path.stem, "heatmap": [], "chapters": []}


def _cuda_dll_dirs() -> Iterator[Path]:
    # CTranslate2 loads cuBLAS/cuDNN lazily at the first encode, not at model load, so a
    # missing DLL surfaces mid-transcription. A cu12x torch install already ships both.
    yield from (Path(sys.prefix) / "Lib/site-packages/nvidia").glob("*/bin")
    yield ROOT / ".runtime/cuda/bin"


_CUDA_HANDLES: list = []


def _load_whisper(model_name: str):
    import os
    require_guard(gpu=True)
    from common import wait_headroom
    wait_headroom(gpu=True)
    for d in _cuda_dll_dirs():
        if d.is_dir():
            _CUDA_HANDLES.append(os.add_dll_directory(str(d)))
            os.environ["PATH"] = f"{d};{os.environ['PATH']}"
    from faster_whisper import WhisperModel
    try:
        local = ROOT / 'models' / f'whisper-{model_name}'
        selected = str(local) if (local / 'restoration.json').is_file() else model_name
        model = WhisperModel(selected, device="cuda", compute_type="int8_float16",
                             cpu_threads=2, num_workers=1, download_root=str(ROOT / "models/whisper"))
        for _ in model.transcribe(np.zeros(16000, dtype=np.float32), language="en")[0]:
            pass
        return model, "cuda"
    except Exception as exc:
        raise RuntimeError(f"CUDA transcription unavailable; no CPU fallback: {exc}") from exc


def transcribe(media: Media, model_name: str, lang: str | None) -> list[dict]:
    model, device = _load_whisper(model_name)
    segments, info = model.transcribe(
        str(media.path), word_timestamps=True, vad_filter=True, language=lang, beam_size=5,
    )
    print(f"  whisper {model_name} on {device}, language={info.language} p={info.language_probability:.2f}")
    out: list[dict] = []
    for seg in segments:
        out.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": [
                {"w": w.word, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)}
                for w in (seg.words or [])
            ],
        })
        print(f"  [{mmss(seg.start)}] {seg.text.strip()[:90]}", flush=True)
    return out


def audio_envelope(media: Media) -> np.ndarray:
    raw = subprocess.run(
        ffmpeg_command([FFMPEG, "-v", "error", "-i", str(media.path), "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]),
        capture_output=True, check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = SR // 20
    n = len(pcm) // hop
    rms = np.sqrt((pcm[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    return 20 * np.log10(rms)


def scene_cuts(media: Media) -> list[float]:
    # A global threshold misses same-palette cuts (TED close-up -> close-up scored 0.10-0.14
    # while real cuts elsewhere hit 1.0). A cut is a LOCAL spike: > 0.06 and >= 4x the
    # median score of the surrounding ~0.8s.
    err = subprocess.run(
        ffmpeg_command([FFMPEG, "-hide_banner", "-i", str(media.path), "-an",
         "-vf", "scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score",
         "-f", "null", "-"]),
        capture_output=True, text=True,
    ).stderr
    rows: list[tuple[float, float]] = []
    t = None
    for line in err.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            t = float(m[1])
            continue
        m = re.search(r"scene_score=([\d.]+)", line)
        if m and t is not None:
            rows.append((t, float(m[1])))
    if not rows:
        return []
    scores = np.array([r[1] for r in rows])
    half = max(int(round(0.4 * media.fps)), 3)
    cuts: list[float] = []
    for i, (ts, sc) in enumerate(rows):
        if sc <= 0.06:
            continue
        nb = np.concatenate([scores[max(0, i - half) : i], scores[i + 1 : i + 1 + half]])
        if nb.size and sc >= 4 * float(np.median(nb)) and (not cuts or ts - cuts[-1] > 0.3):
            cuts.append(round(ts, 2))
    return cuts


def per_second(db: np.ndarray, duration: float) -> Iterator[dict]:
    onset = np.maximum(np.diff(db, prepend=db[0]), 0.0)
    gate = np.percentile(onset, 92)
    median = float(np.median(db))
    for sec in range(int(duration)):
        seg = db[sec * 20 : (sec + 1) * 20]
        if len(seg) == 0:
            break
        yield {
            "t": sec,
            "loud": round(float(seg.mean()) - median, 1),
            "onsets": int((onset[sec * 20 : (sec + 1) * 20] > gate).sum()),
            "var": round(float(seg.std()), 1),
        }


def heat_at(heatmap: list[dict], t: float) -> float | None:
    for h in heatmap:
        if h["start_time"] <= t < h["end_time"]:
            return round(h["value"], 3)
    return None


def write_timeline(path: Path, seconds: list[dict], cuts: list[float], words: list[dict],
                   heatmap: list[dict], bucket: int = 5) -> None:
    lines = [
        f"# per-{bucket}s timeline. loud = dB vs file median, onsets = transient count, var = loudness spread,",
        "# cuts = scene cuts, wps = spoken words/sec, heat = YouTube most-replayed (0-1, blank if none).",
        f"{'time':>8}  {'loud':>5}  {'ons':>3}  {'var':>4}  {'cuts':>4}  {'wps':>4}  {'heat':>5}",
    ]
    for start in range(0, len(seconds), bucket):
        chunk = seconds[start : start + bucket]
        end = start + len(chunk)
        loud = np.mean([c["loud"] for c in chunk])
        ons = sum(c["onsets"] for c in chunk)
        var = np.mean([c["var"] for c in chunk])
        nc = sum(1 for c in cuts if start <= c < end)
        wps = sum(1 for w in words if start <= w["s"] < end) / max(len(chunk), 1)
        heat = heat_at(heatmap, start + bucket / 2)
        lines.append(
            f"{mmss(start):>8}  {loud:5.1f}  {ons:3d}  {var:4.1f}  {nc:4d}  {wps:4.1f}  "
            f"{'' if heat is None else f'{heat:5.2f}':>5}"
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--model", default="small")
    ap.add_argument("--lang", default=None)
    ap.add_argument("--no-transcribe", action="store_true")
    ap.add_argument("--work-id", help="Unique staging ID, e.g. youtube_ngvOyccUzzY")
    args = ap.parse_args()
    require_guard()

    vid, src, meta = fetch(args.target, args.work_id)
    work = WORK / vid
    media = probe(src)
    meta.update({"id": vid, "path": str(src), "fps": media.fps, "rate": media.rate, "width": media.width,
                 "height": media.height, "duration": media.duration, "has_audio": media.has_audio})
    meta['source_quality'] = quality_record(media.width, media.height, meta.get('compatible_4k_available'))
    (work / "source.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    if meta.get('compatible_4k_available') and not meta['source_quality']['native_4k']:
        raise ValueError('The downloaded media is below native 4K despite compatible 4K in the listing. '
                         'Preserve its quality receipt and inspect the selected format before continuing.')
    print(f"[{vid}] {media.width}x{media.height} @{media.fps} {mmss(media.duration)} "
          f"heatmap={'yes' if meta.get('heatmap') else 'no'}")
    if not meta['source_quality']['native_4k']:
        print(f"  SOURCE QUALITY: {media.width}x{media.height}; not native 4K. A 4K export would include upscaling.")

    transcript: list[dict] = []
    tpath = work / "transcript.json"
    if tpath.exists():
        transcript = json.loads(tpath.read_text(encoding="utf-8"))
        print(f"  transcript cached ({len(transcript)} segments)")
    elif media.has_audio and not args.no_transcribe:
        transcript = transcribe(media, args.model, args.lang)
        tpath.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")
    (work / "transcript.txt").write_text(
        "\n".join(f"[{mmss(s['start'])}-{mmss(s['end'])}] {s['text']}" for s in transcript),
        encoding="utf-8",
    )

    seconds = list(per_second(audio_envelope(media), media.duration)) if media.has_audio else []
    cuts = scene_cuts(media)
    words = [w for s in transcript for w in s["words"]]
    (work / "signals.json").write_text(json.dumps({"seconds": seconds, "cuts": cuts}), encoding="utf-8")
    write_timeline(work / "timeline.txt", seconds, cuts, words, meta.get("heatmap") or [])

    print(f"  {len(transcript)} segments, {len(words)} words, {len(cuts)} scene cuts")
    print(f"  wrote {work}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
