"""Create consistent close vertical framing, excluding the source sponsor ticker."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import FFMPEG, encoder, ffmpeg_command, probe, require_guard


def audio_hash(path):
    return subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-i', str(path),
                                          '-map', '0:a:0', '-c', 'copy', '-f', 'hash',
                                          '-hash', 'sha256', '-']), capture_output=True,
                          text=True, check=True).stdout.strip()


def main():
    require_guard(gpu=True)
    from PIL import Image, ImageDraw
    output = HERE / 'source-clean'
    output.mkdir(exist_ok=True)
    receipts = []
    for name in ('opinions', 'process', 'opponent', 'regenerate', 'silver'):
        raw = HERE / 'source' / (name + '.mp4')
        clean = output / (name + '.mp4')
        if clean.exists():
            raise RuntimeError('Clean source exists; inspect before replacing')
        subprocess.run(ffmpeg_command([
            FFMPEG, '-v', 'error', '-nostdin', '-i', str(raw), '-map', '0:v:0',
            '-map', '0:a:0', '-vf', 'crop=720:1000:480:0', *encoder(18),
            '-r', '30', '-fps_mode', 'cfr', '-c:a', 'copy', '-movflags', '+faststart', str(clean),
        ]), check=True)
        before, after = audio_hash(raw), audio_hash(clean)
        if before != after:
            raise RuntimeError('Reframing changed the encoded source audio')
        media = probe(clean)
        metadata = json.loads((HERE / 'source' / (name + '.json')).read_text())
        metadata.update(path=str(clean), original_path=str(raw), width=media.width,
                        height=media.height, duration=media.duration, fps=media.fps,
                        rate=media.rate, source_crop={'x': 480, 'y': 0, 'width': 720,
                        'height': 1000, 'original_width': 1920, 'original_height': 1080},
                        branding='No added symbol. Moving original sponsor ticker excluded from the frame.',
                        encoded_source_audio_preserved=True, source_audio_payload_sha256=after)
        (output / (name + '.json')).write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        folder = HERE / 'clean-source-frames' / name
        folder.mkdir(parents=True, exist_ok=True)
        times = sorted(set([0.5, max(0.5, media.duration - .2)] + list(range(4, int(media.duration), 8))))
        for i, t in enumerate(times):
            subprocess.run(ffmpeg_command([FFMPEG, '-v', 'error', '-nostdin', '-ss', str(t),
                                          '-i', str(clean), '-frames:v', '1', '-vf', 'scale=360:500',
                                          str(folder / f'{i:03d}.jpg')]), check=True)
        for number, offset in enumerate(range(0, len(times), 8), 1):
            group = times[offset:offset + 8]
            sheet = Image.new('RGB', (1440, 525 * ((len(group) + 3) // 4)), '#151515')
            draw = ImageDraw.Draw(sheet)
            for j, t in enumerate(group):
                x, y = (j % 4) * 360, (j // 4) * 525
                with Image.open(folder / f'{offset+j:03d}.jpg') as image:
                    sheet.paste(image, (x, y + 25))
                draw.text((x + 5, y + 5), f'{t:.2f}s', fill='white')
            sheet.save(folder / f'sheet-{number:02d}.jpg')
        receipts.append(metadata)
        print('CLEAN_SOURCE_READY', name, json.dumps({'width':media.width,'height':media.height,'duration':media.duration,'audio_preserved':True}), flush=True)
    (HERE / 'source-reframing.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
