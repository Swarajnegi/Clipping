"""Restore genuine short-aligned caption tokens without changing source cuts."""
import json
from pathlib import Path
from PIL import ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def revise(name):
    path = ROOT / 'work' / ('ronaldo_whoop_20261102_' + name) / 'clips.json'
    spec = json.loads(path.read_text())
    if name == 'gym':
        replacements = {
            'Do ever wake': ('Do you ever wake', [0.02, .34, .36, .48], None),
            'against that,': ('Fight against that,', [14.22, 14.24, 14.66], 14.22),
            'in beginning you': ('in the beginning you', [59.0, 59.18, 59.2, 59.44], None),
        }
    elif name == 'visualize':
        # Native English captions independently retain "sometimes". CUDA gives
        # it a zero-length boundary at the following I; reveal the phrase together.
        replacements = {'I do it': ('Sometimes I do it', None, None)}
    else:
        raise ValueError(name)
    layers = spec['clips'][0]['referenceEdit']['layers']
    for old, (new, times, start) in replacements.items():
        matches = [l for l in layers if l['text'] == old]
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one layer: ' + old)
        layer = matches[0]
        if times is None:
            times = [layer['wordTimes'][0]] + layer['wordTimes']
        end = layer['t'] + layer['dur']
        layer.update(text=new, wordTimes=times)
        if start is not None:
            layer.update(t=start, dur=round(end-start, 6))
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', layer['size'])
        if font.getlength(new) > 820:
            raise RuntimeError('Revised caption exceeds layout')
    spec['clips'][0].pop('audioFinishDb', None)
    path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    record = {'basis': 'Original CUDA word rows plus native English caption evidence. Three positive 20 ms alignments in gym, and zero-duration sometimes in visualization were lost by the staging overlap filter.',
              'replacements': {k: v[0] for k,v in replacements.items()},
              'picture_timing_unchanged': True}
    (path.parent/'short-token-corrections.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    decisions = json.loads((HERE/'edit-decisions.json').read_text())
    for choice in decisions:
        if choice['name'] != name:
            continue
        for old, (new, _, _) in replacements.items():
            if old not in choice['caption_text']:
                raise RuntimeError('Decision caption differs')
            choice['caption_text'] = choice['caption_text'].replace(old, new, 1)
    (HERE/'edit-decisions.json').write_text(json.dumps(decisions, indent=2), encoding='utf-8')
    print('SHORT_TOKENS_RESTORED', name)


if __name__ == '__main__':
    import sys
    for name in sys.argv[1:]:
        revise(name)
