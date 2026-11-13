from pathlib import Path
import io, subprocess, sys
from PIL import Image, ImageDraw

root = Path(r'D:\J.A.R.V.I.S\Clipping')
sys.path.insert(0, str(root / 'scripts'))
from common import require_guard, FFMPEG, ffmpeg_command
require_guard()
lib = root / 'Main/shorts-clips/Movie Clips'
shots = [
('About Time - Mary', '00892000-mary-and-tim-eat-together.mp4'),
('About Time - Mary', '00974000-couple-walk-at-night.mp4'),
('About Time - Mary', '01453000-mary-laughs-in-daylight.mp4'),
('About Time - Mary', '02030000-couple-sits-outside.mp4'),
('About Time - Mary', '01917000-parents-hold-newborn.mp4'),
('Good Will Hunting', '03282000-skylar-smiles-outdoors.mp4'),
('Good Will Hunting', '03330000-couple-talks-over-outdoor-table.mp4'),
('Good Will Hunting', '03393000-will-and-skylar-kiss.mp4'),
('Good Will Hunting', '03599000-will-reacts-in-room-argument.mp4'),
('Good Will Hunting', '03628000-skylar-reaches-for-will.mp4'),
('The Pursuit of Happyness', '01056000-father-and-son-at-basketball-court.mp4'),
('The Pursuit of Happyness', '01295000-father-talks-to-son-on-bench.mp4'),
('The Pursuit of Happyness', '01476000-son-and-father-lie-awake.mp4'),
('Fight Club', '00177516-embrace-at-the-support-group.mp4'),
('Blade Runner 2049 - Officer K', '00884467-joi-reaches-toward-officer-k.mp4'),
('Avengers Endgame - Steve Rogers', '00878294-two-people-on-a-bench-outside.mp4'),
]
if '--pines' in sys.argv:
    shots = [('Luke Glanton - The Place Beyond the Pines', name) for name in (
        '00077744-luke-at-a-diner-table.mp4',
        '00080289-quiet-exchange-at-night.mp4',
        '00084793-luke-looks-down-at-night.mp4',
        '00153320-luke-alone-on-a-church-bench.mp4',
        '00606815-luke-bends-toward-someone.mp4',
        '00614739-two-figures-close-together-indoors.mp4',
        '00617283-luke-looks-down-in-a-warm-room.mp4',
        '00863321-figure-down-on-pavement.mp4',
    )]
sample_times = (0.3, 0.8, 1.3) if '--pines' in sys.argv else (1, 3, 5)
out = Path(__file__).parent / 'b-roll-comparison'
out.mkdir(exist_ok=True)
for page in range((len(shots)+3)//4):
    im = Image.new('RGB', (960, 4*220), '#111111')
    draw = ImageDraw.Draw(im)
    for row, (title, name) in enumerate(shots[page*4:page*4+4]):
        draw.text((5,row*220+3), f'{page*4+row+1:02d} {title} / {name}', fill='white')
        for col, t in enumerate(sample_times):
            data = subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-ss',str(t),'-i',str(lib/title/name),'-frames:v','1','-vf','scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2','-f','image2pipe','-vcodec','png','-']), check=True, stdout=subprocess.PIPE).stdout
            img = Image.open(io.BytesIO(data)).convert('RGB')
            im.paste(img, (col*320,row*220+25))
            draw.text((col*320+5,row*220+205), f'{t}s', fill='white')
    prefix = 'pines' if '--pines' in sys.argv else 'candidates'
    im.save(out / f'{prefix}-{page+1}.jpg', quality=92)
print(f'Prepared {len(shots)} candidates; frames at {sample_times} seconds.')
