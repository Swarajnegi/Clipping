"""Small native-audio review copy; does not change a production master."""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent;ROOT=PROJECT.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG,require_guard,run
require_guard()
run([FFMPEG,'-v','error','-y','-i',str(PROJECT/'drafts/04-family-music-free-DRAFT.mp4'),
    '-vn','-ac','1','-ar','16000','-c:a','libmp3lame','-b:a','32k',str(PROJECT/'qa/04-family/listening-copy.mp3')])
