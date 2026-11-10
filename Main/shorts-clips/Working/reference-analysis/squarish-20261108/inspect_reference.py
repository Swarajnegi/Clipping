"""Bounded visual study of the owner's framing reference, not production footage."""
import json
import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command
from PIL import Image, ImageDraw
import numpy as np

require_guard(gpu=True)
out = Path(__file__).resolve().parent
source = ROOT / '.codex-attachments/0a783b30-83b8-4b92-bde2-80c3c2888844/ed6414d2-795c-43ed-aa42-f274c4ba8ffd/chriswillx2026_11_08_16_54_187e9fb175-56bf-4d3c-b649-b70f90d123ce.mp4'
times = [1, 10, 20, 30, 40, 50, 60, 65]
sheet = Image.new('RGB', (4 * 360, 2 * 660), '#202020')
records = []
for index, at in enumerate(times):
    dest = out / f'frame-{at:02}.png'
    subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-y', '-hwaccel', 'cuda', '-ss', str(at), '-i', str(source), '-frames:v', '1', str(dest)]), check=True)
    im = Image.open(dest).convert('RGB')
    arr = np.asarray(im)
    # Report central rows only; captions/logos can also produce nonblack pixels.
    brightness = arr[:, 60:660].mean(axis=(1, 2))
    rows = np.flatnonzero(brightness > 12)
    records.append({'seconds': at, 'nonblack_central_rows': [int(rows.min()), int(rows.max())] if len(rows) else None})
    im.thumbnail((360, 640))
    x, y = index % 4 * 360, index // 4 * 660
    sheet.paste(im, (x, y + 20))
    ImageDraw.Draw(sheet).text((x + 8, y + 3), f'{at}s', fill='white')
sheet.save(out / 'contact-sheet.jpg', quality=92)
(out / 'frame-inspection.json').write_text(json.dumps({'source': str(source), 'samples': records, 'coverage': 'Eight sampled frames across 66.57 seconds; visual framing study only, no audio review'}, indent=2), encoding='utf-8')
print(json.dumps(records))
