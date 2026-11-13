"""
build.py -- clips.json (written by Claude) -> rendered Shorts + QA strips + UPLOAD.md.

THE BIG PICTURE
    Claude decides WHAT to cut and HOW each clip should read; this script does the
    rest deterministically. Each clip is assembled from one or more source pieces with
    ffmpeg so Remotion decodes a 10-60s snippet instead of a multi-GB master, keeps the
    source frame rate, and receives captions, shots and face-track points rebased onto
    the assembled timeline.

    Lessons from the studied creators live here as defaults: go straight to the climax
    and cut dead air (opt-in silence trim for podcast/speech clips), compilations put the strongest piece
    first (segments order is respected), optional context narration follows the brief,
    and each channel uses a consistent brand style.

THE FLOW
    1. Load clips.json + source.json + transcript.json (+ signals.json cuts).
    2. Per clip: plan pieces (segments, then silence trim) -> ffmpeg cut each -> concat.
    3. Rebase captions / auto-shots / face track onto the assembled timeline.
    4. Optional intro: Kokoro voiceover (voice.py) + still frame of the clip.
    5. Remotion render -> out/<id>/clip_NN.mp4, 4-frame QA strip, UPLOAD.md.

clips.json schema:
{
  "id": "<work id>",
  "brand": {"style": "bold|clean|frame|letterbox", "accent": "#FFE14D",
            "grade": {"brightness": 0.95, "contrast": 1.05, "saturate": 1.0},
            "music": {"file": "D:/J.A.R.V.I.S/Clipping/music/x.mp3", "db": -12, "fadeOutSec": 2},
            "voice": "am_michael", "speed": 1.1},                    # all optional
  "watermark": {"file": "D:/J.A.R.V.I.S/Clipping/work/logo.png", "widthPx": 220, "corner": "tr", "opacity": 0.95} | null,
  "footer": "text appended to every description (campaign caption, #Ad line, tags)",
  "clips": [{
     "n": 1, "type": "gaming" | "talk",
     "start": 83.2, "end": 95.0,                 # or: "segments": [[83.2, 90.1], [120.4, 131.0]]
     "trimSilence": false,                       # true for podcast/speech: drop word gaps > 0.35s
     "intro": "Scripted 5-12s context line.",    # optional voiceover before the clip
     "introFrameAt": 3.0,                        # clip-relative second used as the intro still
     "hook": "HE DIDN'T SEE IT COMING", "hookPersist": true,
     "captions": true, "widthFrac": null, "yAnchor": null,
     "trackMode": "largest",                     # "group": centre all prominent faces (two-shots)
     "shots": [{"t": 0, "x": 0.5}, {"t": 7.2, "x": 0.64, "w": 1.0}],  # assembled-timeline seconds
     "punchIns": [{"t": 6.1, "dur": 0.6, "scale": 1.1}],
     "transitionCues": [{"frame": 45, "preset": "inversion-flicker", "soundId": "small-electric-glitch"}],
     "style": null, "music": null,               # per-clip overrides of brand
     "title": "...", "description": "...", "why": "..."
  }]
}

Usage: python scripts/build.py work/<id>/clips.json [--only 1,3] [--no-render]
    Add --paired-exports for a music-free master plus a stream-copied picture with music.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FFMPEG, NODE, REMOTION, OUT, PUBLIC, ROOT, WORK, encoder, mmss, probe, require_guard, run  # noqa: E402
from track import track as face_track  # noqa: E402
from transition_sounds import mix_transition_sounds, resolve_cues  # noqa: E402

TYPE_DEFAULTS = {
    # 0.42 of a 16:9 frame fills the width at 1.33x and leaves room for blurred bands.
    "gaming": {"widthFrac": 0.42, "yAnchor": 0.42},
    # Full-bleed 9:16 from 16:9: 1080/1920 * 1080/1920 of the width.
    "talk": {"widthFrac": 0.3164, "yAnchor": 0.5},
}
GAP_S = 0.35
PAD_S = 0.12
DEFAULT_GRADE = {"brightness": 1.0, "contrast": 1.0, "saturate": 1.0}

Piece = tuple[float, float]


def plan_pieces(clip: dict, transcript: list[dict]) -> list[Piece]:
    segs = clip.get("segments") or [[clip["start"], clip["end"]]]
    segs = [(float(a), float(b)) for a, b in segs]
    # Opt-in: dead air kills podcast/speech clips, but in reaction comedy the pause IS the
    # joke (a 1.2 s beat before "Wait." was trimmed away in testing).
    if not clip.get("trimSilence"):
        return segs
    words = sorted((w for s in transcript for w in s["words"]), key=lambda w: w["s"])
    pieces: list[Piece] = []
    for a, b in segs:
        inside = [w for w in words if w["s"] >= a and w["e"] <= b]
        cur = a
        for w1, w2 in zip(inside, inside[1:]):
            if w2["s"] - w1["e"] > GAP_S:
                pieces.append((cur, min(w1["e"] + PAD_S, b)))
                cur = max(w2["s"] - PAD_S, a)
        pieces.append((cur, b))
    return [(a, b) for a, b in pieces if b - a >= 0.25]


def cut(src: Path, start: float, end: float, dest: Path, rate: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dur = end - start
    fade = min(0.015, dur / 4)
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}",
         "-map", "0:v:0", "-map", "0:a:0?",
         "-af", f"afade=t=in:d={fade:.3f},afade=t=out:st={dur - fade:.3f}:d={fade:.3f}",
         *encoder(18),
         # constant frame rate: YouTube sources carry jittered timestamps (r_frame_rate
         # 7016500/234117 on a 29.97 file) and Remotion's exact-time seek then finds no frame.
         "-fps_mode", "cfr", "-r", rate, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-movflags", "+faststart", str(dest)])


def assemble(src: Path, pieces: list[Piece], dest: Path, rate: str) -> list[tuple[float, float, float]]:
    """Cut and join pieces in ONE encode; return (src_start, src_end, timeline_offset) per piece.

    Concatenating separately encoded AAC parts with -c copy adds ~21 ms of encoder priming
    per join -- twenty silence-trim joins would drift audio ~0.4 s out of sync. One seeked
    input per piece into the concat filter, encoded once, has no joins to drift.
    """
    if len(pieces) == 1:
        cut(src, *pieces[0], dest, rate)
        return [(pieces[0][0], pieces[0][1], 0.0)]
    dest.parent.mkdir(parents=True, exist_ok=True)
    has_audio = probe(src).has_audio
    inputs, chains, labels, spans, offset = [], [], [], [], 0.0
    for i, (a, b) in enumerate(pieces):
        d = b - a
        fade = min(0.015, d / 4)
        inputs += ["-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", str(src)]
        chains.append(f"[{i}:v:0]setpts=PTS-STARTPTS[v{i}]")
        if has_audio:
            chains.append(f"[{i}:a:0]asetpts=PTS-STARTPTS,aresample=48000,"
                          f"afade=t=in:d={fade:.3f},afade=t=out:st={d - fade:.3f}:d={fade:.3f}[a{i}]")
        labels.append(f"[v{i}][a{i}]" if has_audio else f"[v{i}]")
        spans.append((a, b, offset))
        offset += d
    graph = ";".join(chains) + ";" + "".join(labels) + f"concat=n={len(pieces)}:v=1:a={int(has_audio)}[v]" + ("[a]" if has_audio else "")
    run([FFMPEG, "-v", "error", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", *(["-map", "[a]"] if has_audio else []),
         *encoder(18),
         "-fps_mode", "cfr", "-r", rate,
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dest)])
    return spans


def blur_background(snippet: Path) -> Path:
    """Small pre-blurred 9:16 copy of the snippet for the background layer."""
    dest = snippet.with_name(snippet.stem + "_bg.mp4")
    run([FFMPEG, "-v", "error", "-y", "-i", str(snippet), "-an",
         "-vf", "scale=360:640:force_original_aspect_ratio=increase,crop=360:640,"
                "gblur=sigma=18,eq=brightness=-0.12:saturation=1.2",
         *encoder(30),
         "-movflags", "+faststart", str(dest)])
    return dest


def rebase_words(words: list[dict], spans: list[tuple[float, float, float]]) -> list[dict]:
    caps = []
    for a, b, off in spans:
        span_first = len(caps)
        for w in sorted(words, key=lambda word: word["s"]):
            if w["e"] <= a or w["s"] >= b:
                continue
            s = max(w["s"], a) - a + off
            e = min(w["e"], b) - a + off
            caps.append({"text": w["w"], "startMs": round(s * 1000), "endMs": round(e * 1000),
                         "timestampMs": round((s + e) * 500), "confidence": w.get("p")})
            if w.get("pageBreakAfter"):
                caps[-1]["pageBreakAfter"] = True
        if len(caps) > span_first:
            caps[-1]["pageBreakAfter"] = True
    return caps


def auto_shots(cuts: list[float], spans: list[tuple[float, float, float]]) -> list[dict]:
    shots = []
    for a, b, off in spans:
        shots.append({"t": round(off, 2), "x": 0.5})
        shots += [{"t": round(c - a + off, 2), "x": 0.5} for c in cuts if a + 0.3 < c < b - 0.3]
    return shots


def qa_strip(video: Path, dest: Path, duration: float) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    times = [0.4, duration * 0.35, duration * 0.7, max(duration - 0.3, 0)]
    tiles = []
    for i, t in enumerate(times):
        tile = dest.with_name(f"{dest.stem}_{i}.png")
        run([FFMPEG, "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
             "-vf", "scale=360:640", str(tile)])
        tiles.append(tile)
    inputs = sum([["-i", str(t)] for t in tiles], [])
    run([FFMPEG, "-v", "error", "-y", *inputs, "-filter_complex", f"hstack=inputs={len(tiles)}", str(dest)])
    for t in tiles:
        t.unlink(missing_ok=True)


def publish(file: str, pub_dir: Path, vid: str) -> str:
    srcf = Path(file)
    pub_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(srcf, pub_dir / srcf.name)
    return f"clips/{vid}/{srcf.name}"


def make_intro(clip: dict, brand: dict, name: str, snippet: Path, pub_dir: Path, vid: str) -> dict | None:
    script = clip.get("intro")
    if not script:
        return None
    base = WORK / vid / "intro" / name
    subprocess.run([sys.executable, str(ROOT / "scripts/voice.py"), script, "--out", str(base),
                    "--voice", brand.get("voice", "am_michael"), "--speed", str(brand.get("speed", 1.1))], check=True)
    meta = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
    still = base.with_suffix(".png")
    at = float(clip.get("introFrameAt", probe(snippet).duration / 3))
    run([FFMPEG, "-v", "error", "-y", "-ss", f"{at:.2f}", "-i", str(snippet), "-frames:v", "1", str(still)])
    caps = [{"text": w["w"], "startMs": round(w["s"] * 1000), "endMs": round(w["e"] * 1000),
             "timestampMs": round((w["s"] + w["e"]) * 500), "confidence": None} for w in meta["words"]]
    return {"audio": publish(str(base.with_suffix(".wav")), pub_dir, vid),
            "still": publish(str(still), pub_dir, vid),
            # a short beat of air before the clip rolls
            "durationSec": round(meta["durationSec"] + 0.25, 3),
            "captions": caps}


def mix_companion(clean: Path, music: dict, destination: Path) -> None:
    """Retain the exact clean picture and dialogue while adding a separate music bed."""
    media = probe(clean)
    if not media.has_audio:
        raise ValueError("Paired speech exports require an audio stream in the clean master")
    fade = max(0.0, min(float(music.get("fadeOutSec", 2)), media.duration))
    level = float(music.get("db", -12))
    filters = f"[1:a]volume={level}dB,atrim=duration={media.duration}"
    if fade:
        filters += f",afade=t=out:st={media.duration - fade}:d={fade}"
    filters += "[bed];[0:a][bed]amix=inputs=2:duration=first:normalize=0[a]"
    run([FFMPEG, "-v", "error", "-y", "-i", str(clean), "-stream_loop", "-1", "-i", music["file"],
         "-filter_complex", filters, "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destination)])


def adjust_source_audio(source: Path, gain_db: float, destination: Path) -> None:
    if not math.isfinite(gain_db) or not -30 <= gain_db <= 0:
        raise ValueError("sourceAudioDb must be finite and between -30 and 0 dB")
    run([FFMPEG, "-v", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0",
         "-c:v", "copy", "-af", f"volume={gain_db}dB", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(destination)])


def picture_signature(path: Path) -> dict:
    """Hash compressed picture packets independently of the MP4 container and audio."""
    from common import ffmpeg_command
    command = [FFMPEG, "-v", "error", "-i", str(path), "-map", "0:v:0", "-c:v", "copy",
               "-f", "hash", "-hash", "sha256", "-"]
    digest = subprocess.run(ffmpeg_command(command), capture_output=True, text=True, check=True).stdout.strip()
    from common import FFPROBE
    data = json.loads(subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_packets",
        "-show_entries", "stream=nb_read_packets,duration,r_frame_rate,start_time", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout)
    return {"sha256": digest, **data["streams"][0]}


def matching_pictures(left: dict, right: dict) -> bool:
    from fractions import Fraction
    return (left["sha256"] == right["sha256"]
            and int(left["nb_read_packets"]) == int(right["nb_read_packets"])
            and Fraction(left["r_frame_rate"]) == Fraction(right["r_frame_rate"])
            and abs(float(left["duration"]) - float(right["duration"])) <= 0.001
            and abs(float(left.get("start_time", 0)) - float(right.get("start_time", 0))) <= 0.001)


def validate_reference_edit(edit: dict | None, duration: float) -> None:
    if edit is None:
        return
    if edit.get("profile") not in ("restrained", "kinetic", "editorial"):
        raise ValueError("referenceEdit.profile must be restrained, kinetic or editorial")
    if edit.get("profile") == "editorial" and not edit.get("layers"):
        raise ValueError("Editorial captions require authored layers")
    if "layeredOnly" in edit and not isinstance(edit["layeredOnly"], bool):
        raise ValueError("referenceEdit.layeredOnly must be boolean")
    if edit.get("layeredOnly") and not edit.get("layers"):
        raise ValueError("Layered-only captions require authored text layers")
    if "frame" in edit:
        frame = edit["frame"]
        if not isinstance(frame, dict) or not all(k in frame for k in ("x", "y", "width", "height")):
            raise ValueError("referenceEdit.frame requires x, y, width and height")
        values = [frame[k] for k in ("x", "y", "width", "height")] + [frame.get("radius", 0)]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError("referenceEdit.frame requires finite numeric geometry")
        x, y, width, height, radius = values
        if not (x >= 0 and y >= 0 and width > 0 and height > 0 and x + width <= 1080 and y + height <= 1920
                and 0 <= radius <= min(width, height) / 2):
            raise ValueError("referenceEdit.frame is outside the canvas or has invalid radius")
    for key, low, high in (("bandHeight", 1, 1920), ("captionY", 0, 1850), ("captionSize", 10, 200)):
        if key in edit and not (math.isfinite(float(edit[key])) and low <= float(edit[key]) <= high):
            raise ValueError(f"referenceEdit.{key} is outside the output canvas")
    for cue in edit.get("emphasis") or []:
        at, length = float(cue["t"]), float(cue["dur"])
        if not (math.isfinite(at) and math.isfinite(length) and at >= 0 and length > 0 and at + length <= duration + 0.05):
            raise ValueError("Reference emphasis must fit inside the assembled clip timeline")
        if not str(cue.get("text", "")).strip():
            raise ValueError("Reference emphasis requires text")
    for layer in edit.get("layers") or []:
        at, length = float(layer["t"]), float(layer["dur"])
        if not (math.isfinite(at) and math.isfinite(length) and at >= 0 and length > 0 and at + length <= duration + 0.05):
            raise ValueError("Caption layers must fit inside the assembled clip timeline")
        if not str(layer.get("text", "")).strip():
            raise ValueError("Caption layers require text")
        for key, low, high in (("x", 0, 1080), ("y", 0, 1920), ("size", 10, 500), ("width", 1, 1080)):
            if key in layer and not (math.isfinite(float(layer[key])) and low <= float(layer[key]) <= high):
                raise ValueError(f"Caption layer {key} is outside the output canvas")
        if layer.get("font", "sans") not in ("sans", "serif", "condensed", "inter", "cormorant"):
            raise ValueError("Unsupported caption layer font")
        if layer.get("font") in ("inter", "cormorant") and edit.get("profile") != "editorial":
            raise ValueError("Bundled editorial fonts require the editorial profile")
        if "wordTimes" in layer:
            times = layer["wordTimes"]
            if (len(times) != len(str(layer["text"]).split()) or
                    any(not math.isfinite(float(t)) or not at <= float(t) < at + length for t in times) or
                    times != sorted(times)):
                raise ValueError("Caption layer word times must be ordered and fit its timeline")
        if edit.get("profile") == "editorial":
            if layer.get("font", "inter") not in ("inter", "cormorant"):
                raise ValueError("Editorial captions require a bundled editorial font")
            if not isinstance(layer.get("italic", False), bool):
                raise ValueError("Caption italic must be boolean")
            if layer.get("font") == "cormorant" and (not layer.get("italic") or
                    not 300 <= float(layer.get("weight", 700)) <= 700):
                raise ValueError("Cormorant accent requires italic and weight 300-700")
            for key, low, high in (("tracking", -0.12, 0.2), ("lineHeight", 0.7, 2),
                                   ("glow", 0, 40), ("rotate", -180, 180), ("weight", 100, 900), ("z", 0, 999)):
                if key in layer and not low <= float(layer[key]) <= high:
                    raise ValueError(f"Invalid editorial {key}")
            if layer.get("depth", "front") not in ("front", "behind"):
                raise ValueError("Invalid caption depth")
            if layer.get("blend", "normal") not in ("normal", "screen", "difference", "color-dodge"):
                raise ValueError("Invalid caption blend mode")
            if layer.get("shadow", "strong") not in ("none", "soft", "strong"):
                raise ValueError("Invalid caption shadow")
            if layer.get("surface", "solid") not in ("solid", "difference"):
                raise ValueError("Invalid caption surface")
            if "fillOpacity" in layer and not 0 <= float(layer["fillOpacity"]) <= 1:
                raise ValueError("Caption fillOpacity must be finite and between zero and one")
            motion = layer.get("motion") or {}
            for key, low, high in (("inSec", 0.01, 2), ("outSec", 0.01, 2),
                                   ("rise", -200, 200), ("scaleFrom", 0.1, 2), ("blur", 0, 40)):
                if key in motion and not low <= float(motion[key]) <= high:
                    raise ValueError(f"Invalid caption motion {key}")
            if motion.get("easing", "cubic") not in ("cubic", "expo", "linear"):
                raise ValueError("Invalid caption easing")
            perspective = layer.get("perspective")
            if perspective:
                for key, low, high in (("distance", 100, 5000), ("rotateX", -70, 70), ("rotateY", -70, 70)):
                    if not low <= float(perspective[key]) <= high:
                        raise ValueError(f"Invalid caption perspective {key}")
    masks = edit.get("foregroundMasks") or []
    for mask in masks:
        at, length = float(mask["t"]), float(mask["dur"])
        if not (math.isfinite(at) and math.isfinite(length) and at >= 0 and length > 0 and at + length <= duration + 0.05):
            raise ValueError("Foreground mask must fit the clip timeline")
        frames = mask.get("keyframes") or []
        if not frames or len(frames[0].get("points", [])) < 3:
            raise ValueError("Foreground mask requires polygon keyframes")
        count, previous = len(frames[0]["points"]), -1.0
        for keyframe in frames:
            moment = float(keyframe["t"])
            if not math.isfinite(moment) or not at <= moment <= at + length or moment <= previous:
                raise ValueError("Mask keyframes must be strictly ordered and fit its interval")
            previous = moment
            if len(keyframe["points"]) != count:
                raise ValueError("Mask polygon vertex count must remain stable")
            for x, y in keyframe["points"]:
                if not (0 <= float(x) <= 1080 and 0 <= float(y) <= 1920):
                    raise ValueError("Mask polygon is outside the output canvas")
    for layer in edit.get("layers") or []:
        if layer.get("depth") == "behind" and not any(
                m["t"] <= layer["t"] and m["t"] + m["dur"] >= layer["t"] + layer["dur"] - 0.001 for m in masks):
            raise ValueError("Behind-subject caption requires a foreground mask covering its interval")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("clips_json")
    ap.add_argument("--only", default="")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--output-scale", type=int, choices=(1, 2), default=2,
                    help="2160x3840 delivery by default; use 1 for a 1080x1920 proof. Source detail depends on the original and crop.")
    ap.add_argument("--paired-exports", action="store_true", help="Keep dialogue/effects; export with and without added music")
    ap.add_argument("--video-cache-mib", type=int, choices=(128, 256, 512), default=512,
                    help="Bound Remotion decoded-video cache; lower values trade speed for system RAM")
    args = ap.parse_args()
    require_guard(gpu=True)

    spec = json.loads(Path(args.clips_json).read_text(encoding="utf-8"))
    vid = spec["id"]
    brand = spec.get("brand") or {}
    paired = args.paired_exports or bool(spec.get("pairedExports", False))
    if paired:
        for candidate in spec["clips"]:
            if not candidate.get("music", brand.get("music")):
                raise ValueError("Paired exports need a cleared music file; no background track is configured")
    meta = json.loads((WORK / vid / "source.json").read_text(encoding="utf-8"))
    src = Path(meta["path"])
    media = probe(src)
    tpath = WORK / vid / "transcript.json"
    transcript = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else []
    words = [w for s in transcript for w in s["words"]]
    spath = WORK / vid / "signals.json"
    cuts = json.loads(spath.read_text(encoding="utf-8"))["cuts"] if spath.exists() else []
    only = {int(x) for x in args.only.split(",") if x.strip()}

    pub_dir = PUBLIC / "clips" / vid
    out_dir = OUT / vid
    props_dir = WORK / vid / "props"
    props_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    watermark = None
    if spec.get("watermark"):
        wm = spec["watermark"]
        watermark = {"src": publish(wm["file"], pub_dir, vid), "widthPx": wm.get("widthPx", 220),
                     "corner": wm.get("corner", "tr"), "opacity": wm.get("opacity", 0.95)}

    upload = [f"# Upload copy — {meta.get('title') or vid}\n"]
    for clip in spec["clips"]:
        n = int(clip["n"])
        if only and n not in only:
            continue
        name = f"clip_{n:02d}"
        ctype = clip.get("type", "gaming")
        defaults = TYPE_DEFAULTS.get(ctype, TYPE_DEFAULTS["gaming"])
        pieces = plan_pieces(clip, transcript)
        if not pieces or any(a < 0 or b <= a or b > media.duration + 0.05 for a, b in pieces):
            raise ValueError(f"Invalid clip boundaries for {name}")
        validate_reference_edit(clip.get("referenceEdit"), sum(b - a for a, b in pieces))
        if (clip.get("referenceEdit") or {}).get("profile") == "editorial":
            font_source = ROOT / ".agents/skills/viral-shorts/assets/fonts"
            font_public = PUBLIC / "fonts"
            font_public.mkdir(parents=True, exist_ok=True)
            shutil.copy2(font_source / "InterVariable.woff2", font_public / "InterVariable.woff2")
            shutil.copy2(font_source / "LICENSE.txt", font_public / "Inter-LICENSE.txt")
            if any(layer.get("italic") and layer.get("font", "inter") == "inter"
                   for layer in clip["referenceEdit"].get("layers", [])):
                shutil.copy2(font_source / "InterVariable-Italic.woff2", font_public / "InterVariable-Italic.woff2")
            if any(layer.get("font") == "cormorant" for layer in clip["referenceEdit"].get("layers", [])):
                shutil.copy2(font_source / "CormorantGaramond-Italic.ttf", font_public / "CormorantGaramond-Italic.ttf")
                shutil.copy2(font_source / "Cormorant-OFL.txt", font_public / "Cormorant-OFL.txt")
        raw = sum(b - a for a, b in (clip.get("segments") or [[clip["start"], clip["end"]]]))
        print(f"[{name}] {len(pieces)} piece(s), {raw:.1f}s -> {sum(b - a for a, b in pieces):.1f}s "
              f"{ctype} :: {clip.get('hook', '')}")

        snippet = pub_dir / f"{name}.mp4"
        from common import wait_headroom
        wait_headroom(gpu=True)
        spans = assemble(src, pieces, snippet, media.rate)
        clip_dur = probe(snippet).duration

        shots = clip.get("shots") or auto_shots(cuts, spans)
        track_pts: list[dict] = []
        # Close-up shots (no explicit w) in talk clips follow the face unless locked.
        if ctype == "talk":
            for sh in shots:
                if "w" not in sh and not sh.get("lock"):
                    sh["track"] = True
            if any(sh.get("track") for sh in shots):
                hits = []
                for a, b, off in spans:
                    rel = [sh["t"] - off for sh in shots if off <= sh["t"] < off + (b - a)]
                    pts, cov = face_track(src, a, b, rel, clip.get("trackMode", "largest"))
                    track_pts += [{"t": round(p["t"] + off, 2), "x": p["x"]} for p in pts]
                    hits.append(cov * (b - a))
                print(f"  face track: {sum(hits) / max(clip_dur, 1e-6):.0%} of samples had a face")

        intro = make_intro(clip, brand, name, snippet, pub_dir, vid)
        intro_duration = intro["durationSec"] if intro else 0
        duration_sec = round(clip_dur + intro_duration, 3)
        # Match Math.round in the composition for both clocks, including .5 ties.
        intro_frames = math.floor(intro_duration * media.fps + 0.5)
        total_frames = max(1, math.floor(duration_sec * media.fps + 0.5))
        transition_cues = clip.get("transitionCues", [])
        transition_assets = resolve_cues(
            transition_cues, total_frames - intro_frames, media.fps, clip.get("referenceEdit")
        )
        cutaways = []
        for index, item in enumerate(clip.get("cutaways") or []):
            at, duration = float(item["t"]), float(item["end"]) - float(item["start"])
            cutaway_source = Path(item["file"])
            if at < 0 or duration <= 0 or at + duration > clip_dur + 0.01:
                raise ValueError("Cutaway must fit inside the assembled clip timeline")
            if float(item["start"]) < 0 or float(item["end"]) > probe(cutaway_source).duration:
                raise ValueError("Cutaway source boundaries are invalid")
            if not clip.get("referenceEdit"):
                raise ValueError("Cutaways currently require referenceEdit band layout")
            cutaway_path = pub_dir / f"{name}_cutaway_{index:02d}.mp4"
            cut(cutaway_source, float(item["start"]), float(item["end"]), cutaway_path, media.rate)
            cutaways.append({"src": f"clips/{vid}/{cutaway_path.name}", "t": at, "dur": duration})
        music_cfg = clip.get("music", brand.get("music"))
        music = ({"src": publish(music_cfg["file"], pub_dir, vid), "db": float(music_cfg.get("db", -12)),
                  "fadeOutSec": float(music_cfg.get("fadeOutSec", 2))}
                 if music_cfg and not transition_assets else None)

        bg = snippet if clip.get("referenceEdit") else blur_background(snippet)
        props = {
            "src": f"clips/{vid}/{name}.mp4",
            "bgSrc": f"clips/{vid}/{bg.name}",
            "fps": media.fps,
            "durationSec": duration_sec,
            "srcWidth": media.width,
            "srcHeight": media.height,
            "widthFrac": clip.get("widthFrac") or defaults["widthFrac"],
            "shots": shots,
            "track": track_pts,
            "yAnchor": clip.get("yAnchor") if clip.get("yAnchor") is not None else defaults["yAnchor"],
            "hook": clip.get("hook", ""),
            "hookPersist": bool(clip.get("hookPersist", True)),
            "hookDurationSec": float(clip.get("hookDurationSec", 2.5)),
            "captions": rebase_words(words, spans) if clip.get("captions", True) else [],
            "punchIns": clip.get("punchIns", []),
            "watermark": watermark,
            "loopFadeSec": float(clip.get("loopFadeSec", 0)),
            "style": clip.get("style") or brand.get("style", "bold"),
            "grade": {**DEFAULT_GRADE, **brand.get("grade", {}), **clip.get("grade", {})},
            "accent": clip.get("accent") or brand.get("accent", "#FFE14D"),
            "intro": intro,
            "music": None if paired else music,
            "referenceEdit": clip.get("referenceEdit"),
            "cutaways": cutaways,
        }
        if transition_cues:
            props["transitionCues"] = transition_cues
        ppath = props_dir / f"{name}.json"
        ppath.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

        if not args.no_render:
            from common import wait_headroom
            wait_headroom(gpu=True)
            final = out_dir / f"{name}.mp4"
            from uuid import uuid4
            pending = out_dir / f"{name}.{uuid4().hex}.partial.mp4"
            cmd = [str(NODE), str(REMOTION), "render", "src/index.ts", "ViralShort", str(pending),
                   f"--props={ppath}", "--concurrency=1", "--offthreadvideo-video-threads=2",
                   f"--offthreadvideo-cache-size-in-bytes={args.video_cache_mib * 1024 * 1024}",
                   "--hardware-acceleration=required", "--gl=angle", "--log=verbose"]
            if args.output_scale == 2:
                cmd += ["--scale=2", "--video-bitrate=40M", "--image-format=png"]
            print("  render: NVENC required, concurrency=1, FFmpeg threads=2; no automatic retry", flush=True)
            subprocess.run(cmd, cwd=ROOT, check=True)
            m = probe(pending)
            if (m.width, m.height) != (1080 * args.output_scale, 1920 * args.output_scale) or abs(m.fps - media.fps) > 0.001:
                raise RuntimeError("Rendered dimensions/frame rate do not match the requested output")
            gain_db = float(clip.get("sourceAudioDb", 0))
            if transition_assets:
                with_effects = pending.with_name(pending.stem + ".effects.mp4")
                mix_transition_sounds(pending, with_effects, transition_cues, transition_assets,
                                      media.fps, total_frames, intro_frames=intro_frames,
                                      source_gain_db=gain_db, dialogue=snippet,
                                      intro_audio=PUBLIC / intro["audio"] if intro else None)
                pending.unlink()
                pending = with_effects
            elif gain_db:
                levelled = pending.with_name(pending.stem + ".levelled.mp4")
                adjust_source_audio(pending, gain_db, levelled)
                pending = levelled
            if paired:
                clean = out_dir / f"{name}_music-free.mp4"
                mixed_pending = pending.with_name(pending.stem + ".mixed.mp4")
                mix_companion(pending, music_cfg, mixed_pending)
                clean_picture = picture_signature(pending)
                mixed_picture = picture_signature(mixed_pending)
                if not matching_pictures(clean_picture, mixed_picture):
                    raise RuntimeError("Paired exports have different picture packets or timing")
                mixed_media = probe(mixed_pending)
                if not mixed_media.has_audio or abs(mixed_media.duration - m.duration) > 0.05:
                    raise RuntimeError("Paired exports have invalid audio/duration")
                pending.replace(clean)
                mixed_pending.replace(final)
                (out_dir / f"{name}_pair.json").write_text(json.dumps({
                    "mixed": final.name, "music_free": clean.name,
                    "picture_match": True, "picture": clean_picture,
                    "container_video_duration_difference_ms": abs(float(clean_picture["duration"]) - float(mixed_picture["duration"])) * 1000,
                    "music_file": music_cfg["file"], "speech_and_effects_retained": True,
                    "source_audio_gain_db": gain_db,
                    "note": "Only the separately added bed is removed; source-embedded music remains."}, indent=2), encoding="utf-8")
            else:
                if transition_assets and music_cfg:
                    mixed_pending = pending.with_name(pending.stem + ".mixed.mp4")
                    mix_companion(pending, music_cfg, mixed_pending)
                    pending.unlink()
                    pending = mixed_pending
                pending.replace(final)
            print(f"  -> {final.name} {m.width}x{m.height} @{m.fps} {m.duration:.2f}s "
                  f"{final.stat().st_size / 1e6:.1f} MB")
            qa_strip(final, out_dir / "qa" / f"{name}.jpg", m.duration)

        first, last = pieces[0][0], pieces[-1][1]
        upload.append(f"## {name} — {mmss(first)}–{mmss(last)} ({props['durationSec']:.0f}s)\n")
        if paired:
            upload.append(f"Files: `{name}.mp4` (mixed), `{name}_music-free.mp4` (speech/effects, no added bed).\n")
        upload.append(f"**Title:** {clip.get('title', '')}\n")
        desc = clip.get("description", "")
        if spec.get("footer"):
            desc = f"{desc}\n{spec['footer']}" if desc else spec["footer"]
        upload.append(f"**Description:**\n```text\n{desc}\n```\n")
        if clip.get("why"):
            upload.append(f"_Why this moment:_ {clip['why']}\n")

    if not only:
        (out_dir / "UPLOAD.md").write_text("\n".join(upload), encoding="utf-8")
    print(f"done -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
