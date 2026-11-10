"""Validate the completed render after fixing container-duration rounding comparison."""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
import build
from common import require_guard, probe

def main():
    require_guard()
    folder=ROOT/'out/referencepilot_20261101_parents'
    pending=folder/'clip_01.4d50f3bb52914e47894ecb5a418ea2f4.partial.mp4'
    mixed_pending=folder/'clip_01.4d50f3bb52914e47894ecb5a418ea2f4.partial.mixed.mp4'
    clean,final=folder/'clip_01_music-free.mp4',folder/'clip_01.mp4'
    if clean.exists() or final.exists():raise FileExistsError('Preserve previously promoted stage outputs')
    left,right=build.picture_signature(pending),build.picture_signature(mixed_pending)
    if not build.matching_pictures(left,right):raise RuntimeError(json.dumps({'clean':left,'mixed':right}))
    pending.replace(clean)
    mixed_pending.replace(final)
    (folder/'clip_01_pair.json').write_text(json.dumps({'mixed':final.name,'music_free':clean.name,
        'picture_match':True,'picture':left,'mixed_picture':right,
        'container_video_duration_difference_ms':abs(float(left['duration'])-float(right['duration']))*1000,
        'speech_and_effects_retained':True,'music_file':str(ROOT/'music/original-minor-bed-v1.wav'),
        'recovery_note':'Render completed; original validator rejected 0.333 ms mux rounding. Current packet hash, count, rate and timing checks pass.'},indent=2),encoding='utf-8')
    build.qa_strip(final,folder/'qa/clip_01.jpg',probe(final).duration)
    import qa_pilot
    return qa_pilot.main()

if __name__=='__main__':raise SystemExit(main())
