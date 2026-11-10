"""Align shortlisted source passages and the caption reference on verified CUDA."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard
from prep import _load_whisper


def transcribe(model, path, output, offset):
    if output.exists():
        raise RuntimeError('Transcript already exists; inspect before replacing')
    segments, info = model.transcribe(str(path), word_timestamps=True,
                                     vad_filter=True, language='en', beam_size=5)
    rows = []
    journal = output.with_suffix('.partial.jsonl')
    with journal.open('x', encoding='utf-8') as stream:
        for seg in segments:
            row = {'start': round(seg.start, 3), 'end': round(seg.end, 3),
                   'original_start': round(offset + seg.start, 3),
                   'original_end': round(offset + seg.end, 3),
                   'text': seg.text.strip(), 'words': [
                       {'w': w.word, 's': round(w.start, 3), 'e': round(w.end, 3),
                        'p': round(w.probability, 3)} for w in seg.words or []]}
            rows.append(row)
            stream.write(json.dumps(row) + '\n')
            stream.flush()
            print(round(offset + seg.start, 2), seg.text.strip(), flush=True)
    output.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return {'file': str(path), 'segments': len(rows), 'offset': offset,
            'language': info.language, 'language_probability': info.language_probability}


def main():
    require_guard(gpu=True)
    model, device = _load_whisper('small')
    reference = json.loads((HERE / 'caption-reference/metadata.json').read_text())
    receipts = [transcribe(model, Path(reference['file']), HERE / 'caption-reference/transcript.json', 0)]
    for candidate in json.loads((HERE / 'candidates.json').read_text()):
        if not candidate['selected_for_review']:
            continue
        name = candidate['name']
        metadata = json.loads((HERE / 'source' / (name + '.json')).read_text())
        receipts.append(transcribe(model, Path(metadata['path']),
                                   HERE / 'source' / (name + '-transcript.json'),
                                   metadata['source_start']))
    (HERE / 'transcription.json').write_text(json.dumps({
        'backend': device, 'model': 'small', 'compute_type': 'int8_float16',
        'receipts': receipts,
    }, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
