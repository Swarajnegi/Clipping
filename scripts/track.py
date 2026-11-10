"""
track.py -- per-frame face centre for talk clips, so full-bleed crops follow the speaker.

THE BIG PICTURE
    The TED test showed one frame per shot is not enough: the speaker walks inside a
    shot, and a static x cut his face in half at t=0.4s. Commercial clippers solve this
    with face tracking; YuNet (OpenCV, 230 KB ONNX, CPU) does it here at ~5 samples/s.
    Tracking only drives shots with no explicit `w` (close-ups); wide/slide shots keep
    Claude's static framing, and Claude's x stays the fallback when no face is found.

THE FLOW
    1. ffmpeg decodes the window at 5 fps, 640 px wide, raw BGR to a pipe.
    2. YuNet detects faces; pick the largest confident face, preferring continuity.
    3. Within each shot: median-filter, then EMA-smooth, so the virtual camera glides.
    4. Return clip-relative [{t, x}] points (x as a fraction of source width).

Usage (debug): python scripts/track.py <id> <start> <end>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FFMPEG, ROOT, WORK, ffmpeg_command, probe, require_guard  # noqa: E402

MODEL = ROOT / "models" / "face_detection_yunet_2023mar.onnx"
SAMPLE_FPS = 5
TW = 640


def raw_faces(src: Path, start: float, end: float, mode: str = "largest") -> list[tuple[float, float | None]]:
    require_guard()
    from common import wait_headroom
    wait_headroom()
    import cv2
    cv2.setNumThreads(2)

    m = probe(src)
    th = int(round(TW * m.height / m.width / 2) * 2)
    proc = subprocess.Popen(
        ffmpeg_command([FFMPEG, "-v", "error", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{end - start:.3f}",
         "-vf", f"fps={SAMPLE_FPS},scale={TW}:{th}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]),
        stdout=subprocess.PIPE,
    )
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (TW, th), score_threshold=0.7)
    size = TW * th * 3
    out: list[tuple[float, float | None]] = []
    prev: float | None = None
    i = 0
    assert proc.stdout is not None
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(th, TW, 3)
        _, faces = det.detect(frame)
        x = None
        if faces is not None and len(faces):
            areas = faces[:, 2] * faces[:, 3]
            if mode == "group":
                # two-person conversations: frame the midpoint of every prominent face, so the
                # person delivering the punchline is not cropped out for being the smaller face
                big = faces[areas >= 0.3 * areas.max()]
                centres = (big[:, 0] + big[:, 2] / 2) / TW
                x = float((centres.min() + centres.max()) / 2)
            else:
                big = faces[areas >= 0.5 * areas.max()]
                centres = (big[:, 0] + big[:, 2] / 2) / TW
                x = float(centres[np.argmin(np.abs(centres - prev))] if prev is not None else
                          centres[np.argmax(big[:, 2] * big[:, 3])])
            prev = x
        out.append((i / SAMPLE_FPS, x))
        i += 1
    proc.wait()
    return out


def smooth_track(samples: list[tuple[float, float | None]], cut_times: list[float]) -> list[dict]:
    bounds = [0.0] + sorted(cut_times) + [float("inf")]
    points: list[dict] = []
    for a, b in zip(bounds, bounds[1:]):
        seg = [(t, x) for t, x in samples if a <= t < b and x is not None]
        if len(seg) < 2:
            continue
        xs = np.array([x for _, x in seg])
        k = 5
        pad = np.pad(xs, (k // 2, k // 2), mode="edge")
        med = np.array([np.median(pad[j : j + k]) for j in range(len(xs))])
        ema = np.empty_like(med)
        ema[0] = med[0]
        for j in range(1, len(med)):
            ema[j] = 0.75 * ema[j - 1] + 0.25 * med[j]
        for (t, _), x in zip(seg, ema):
            points.append({"t": round(t, 2), "x": round(float(x), 4)})
    return points


def track(src: Path, start: float, end: float, shot_times: list[float],
          mode: str = "largest") -> tuple[list[dict], float]:
    samples = raw_faces(src, start, end, mode)
    hit = sum(1 for _, x in samples if x is not None) / max(len(samples), 1)
    return smooth_track(samples, [t for t in shot_times if t > 0]), hit


if __name__ == "__main__":
    vid, s, e = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    meta = json.loads((WORK / vid / "source.json").read_text(encoding="utf-8"))
    cuts = json.loads((WORK / vid / "signals.json").read_text(encoding="utf-8"))["cuts"]
    pts, coverage = track(Path(meta["path"]), s, e, [c - s for c in cuts if s < c < e])
    print(f"face coverage {coverage:.0%}, {len(pts)} points")
    for p in pts[:: max(len(pts) // 20, 1)]:
        print(p)
