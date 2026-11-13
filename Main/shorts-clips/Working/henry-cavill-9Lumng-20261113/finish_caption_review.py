from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(root / 'scripts'))
from common import FFMPEG, FFPROBE, ffmpeg_command, require_guard

require_guard(gpu=True)
work = Path(__file__).resolve().parent
frames = work / 'caption-review-frames-v4-DRAFT'
source = work / 'caption-free-v2-PRIVATE-REVIEW.mp4'
output = work / 'henry-cavill-final-captioned.mp4'
temporary = output.with_suffix('.partial.mp4')
fps = Fraction(30000, 1001)
expected = {f'element-{frame:03}.png' for frame in range(496)}
if {path.name for path in frames.glob('element-*.png')} != expected:
    raise ValueError('Expected exactly the 496 numbered frames from the approved review')

subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-xerror', '-y',
    '-framerate', str(fps), '-start_number', '0', '-i', str(frames / 'element-%03d.png'),
    '-i', str(source), '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'h264_nvenc',
    '-vf', 'crop=720:1280:0:0,setsar=1', '-preset', 'p5', '-b:v', '8M',
    '-pix_fmt', 'yuv420p', '-c:a', 'copy',
    '-movflags', '+faststart', str(temporary)]), check=True)


def probe(path, *args):
    return json.loads(subprocess.check_output([FFPROBE, '-v', 'error', '-of', 'json', *args, str(path)]))


streams = probe(temporary, '-show_streams')['streams']
video = streams[0]
if (video['codec_name'] != 'h264' or int(video['nb_frames']) != 496
        or Fraction(video['avg_frame_rate']) != fps
        or (video['width'], video['height']) != (720, 1280)):
    raise ValueError('Final video does not match the approved frame sequence')

audio_fields = ('-select_streams', 'a:0', '-show_packets', '-show_data_hash', 'sha256',
                '-show_entries', 'packet=pts_time,dts_time,duration_time,data_hash')
if probe(temporary, *audio_fields) != probe(source, *audio_fields):
    raise ValueError('Final audio packets or timestamps differ from the approved edit')

subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-xerror', '-i', str(temporary),
                              '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-']), check=True)
temporary.replace(output)
print(f'{output}: 496 frames, {fps} fps, 720 × 1280. Audio packets and timestamps match.')
