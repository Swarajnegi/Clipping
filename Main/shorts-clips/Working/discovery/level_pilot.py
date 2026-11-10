"""Level the source track without changing the completed picture, then repeat audio QA."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
import build
from common import require_guard

def main():
    require_guard()
    folder=ROOT/'out/referencepilot_20261101_parents'
    clean,final=folder/'clip_01_music-free.mp4',folder/'clip_01.mp4'
    levelled,mixed=folder/'clip_01.levelled.mp4',folder/'clip_01.levelled-mixed.mp4'
    build.adjust_source_audio(clean,-3,levelled)
    build.mix_companion(levelled,{'file':str(ROOT/'music/original-minor-bed-v1.wav'),'db':-16,'fadeOutSec':1.5},mixed)
    left,right=build.picture_signature(levelled),build.picture_signature(mixed)
    if not build.matching_pictures(left,right):raise RuntimeError('Levelled picture mismatch')
    clean.replace(folder/'clip_01.before-level.music-free.mp4')
    final.replace(folder/'clip_01.before-level.mixed.mp4')
    levelled.replace(clean)
    mixed.replace(final)
    p=folder/'clip_01_pair.json'
    data=json.loads(p.read_text())
    data.update(picture=left,mixed_picture=right,source_audio_gain_db=-3,
                container_video_duration_difference_ms=abs(float(left['duration'])-float(right['duration']))*1000)
    p.write_text(json.dumps(data,indent=2),encoding='utf-8')
    import qa_pilot
    return qa_pilot.main()

if __name__=='__main__':raise SystemExit(main())
