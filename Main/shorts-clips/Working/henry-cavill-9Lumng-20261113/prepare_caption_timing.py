from pathlib import Path
import json

root = Path(r'D:\J.A.R.V.I.S\Clipping')
project = Path(__file__).parent
segments = json.loads((root / 'work/henry-cavill-9Lumng-20261113/transcript.json').read_text(encoding='utf-8'))
cuts = [(386.38, 391.03), (416.48, 421.95), (424.35, 427.45), (452.55, 455.85)]
timeline = []
offset = 0.0
for start, end in cuts:
    for segment in segments:
        for word in segment['words']:
            if start <= word['s'] < end:
                timeline.append({'word': word['w'].strip(), 'start': round(offset + word['s'] - start, 3),
                                 'end': round(offset + min(word['e'], end) - start, 3),
                                 'confidence': word.get('p'), 'source_start': word['s']})
    offset += end - start
out = {'status': 'ASR draft; audio alignment and rendered appearance not verified',
       'fps': '30000/1001', 'word_timing': timeline}
(project / 'caption-word-timing-draft.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
print('Drafted', len(timeline), 'word timings.')
