"""Full local CUDA word alignment and sampled picture study, in a separate GPU stage."""
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parent
ROOT = P.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command, probe
from prep import _load_whisper, scene_cuts

require_guard(gpu=True)
model, device = _load_whisper('small')
targets = sys.argv[1:] or [c['id'] for c in json.loads((P / 'batch.json').read_text())['candidates']]
for source in [P / 'sources' / (id + '.mp4') for id in targets]:
    output = source.with_name(source.stem + '-words.json')
    if output.exists():
        raise FileExistsError('Preserve word-alignment revisions')
    raw = subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', str(source), '-vn',
        '-ac', '1', '-ar', '16000', '-f', 'f32le', '-']), capture_output=True, check=True).stdout
    segments, info = model.transcribe(np.frombuffer(raw, np.float32), word_timestamps=True,
        vad_filter=True, language='en', beam_size=5)
    rows = [{'start': s.start, 'end': s.end, 'text': s.text.strip(), 'words':
        [{'w': w.word.strip(), 's': w.start, 'e': w.end, 'p': w.probability} for w in s.words or []]} for s in segments]
    media = probe(source)
    cuts = scene_cuts(media)
    output.write_text(json.dumps({'source': str(source), 'device': device,
        'segments': rows, 'cuts': cuts, 'duration': media.duration, 'fps': media.fps}, indent=2), encoding='utf-8')
    count = int(media.duration // 3) + 1
    subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-hwaccel', 'cuda', '-i', str(source),
        '-vf', f'fps=1/3,scale=320:180,tile=5x{(count + 4) // 5}:padding=4:margin=4',
        '-frames:v', '1', str(source.with_name(source.stem + '-sheet.jpg'))]), check=True)
    print(source.stem, ' '.join(s['text'] for s in rows), flush=True)
