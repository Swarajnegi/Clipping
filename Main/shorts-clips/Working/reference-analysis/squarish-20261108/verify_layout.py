"""Native-4K synthetic still check; never a finished channel clip."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, FFMPEG, NODE, REMOTION, ffmpeg_command, encoder, probe
from PIL import Image

require_guard(gpu=True)
out = Path(__file__).resolve().parent
public = ROOT / 'public/clips/framing-qa-20261108'
public.mkdir(parents=True, exist_ok=True)
source = public / 'synthetic-4k.mp4'
subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-f', 'lavfi', '-i',
    'testsrc2=size=3840x2160:rate=25', '-t', '1', '-an', *encoder(18), str(source)]), check=True)
media = probe(source)
assert (media.width, media.height, media.fps) == (3840, 2160, 25)
props = dict(src='clips/framing-qa-20261108/synthetic-4k.mp4', bgSrc=None, fps=25,
    durationSec=1, srcWidth=3840, srcHeight=2160, widthFrac=1,
    shots=[{'t': 0, 'x': .5}], track=[], yAnchor=.5, hook='', hookPersist=False,
    hookDurationSec=0, captions=[], punchIns=[{'t': 0, 'dur': .8, 'scale': 1.1}],
    watermark=None, loopFadeSec=0, style='bold', grade={'brightness': 1, 'contrast': 1, 'saturate': 1},
    accent='#ffffff', intro=None, music=None,
    referenceEdit={'profile': 'restrained', 'frame': {'x': 50, 'y': 470, 'width': 980, 'height': 980, 'radius': 48}},
    cutaways=[{'t': .5, 'dur': .5, 'src': 'clips/framing-qa-20261108/synthetic-4k.mp4'}])
propfile = out / 'layout-test-props.json'
propfile.write_text(json.dumps(props), encoding='utf-8')
for name, frame in [('speaker-square-4k', 5), ('cutaway-square-4k', 18)]:
    dest = out / (name + '.png')
    subprocess.run([str(NODE), str(REMOTION), 'still', 'src/index.ts', 'ViralShort', str(dest),
        f'--props={propfile}', f'--frame={frame}', '--scale=2', '--gl=angle',
        '--offthreadvideo-video-threads=2', '--offthreadvideo-cache-size-in-bytes=134217728'], cwd=ROOT, check=True)
    im = Image.open(dest).convert('RGB')
    assert im.size == (2160, 3840)
    assert im.getpixel((1080, 500)) == (0, 0, 0)
    assert im.getpixel((100, 940)) == (0, 0, 0)  # Rounded corner.
    assert im.getpixel((1080, 1920)) != (0, 0, 0)
    im.thumbnail((360, 640))
    im.save(out / (name + '-phone.png'))
print('Both native-4K layout stills passed size, black surround, rounded corner and picture-centre checks.')
