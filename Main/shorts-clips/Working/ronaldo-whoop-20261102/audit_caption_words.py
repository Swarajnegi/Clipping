"""Independently compare every authored word with its mapped source timestamp."""
import json
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def norm(word):
    return re.sub(r"[^a-z0-9']", '', word.lower())


def audit():
    records = []
    for choice in json.loads((HERE/'edit-decisions.json').read_text()):
        work = ROOT/'work'/choice['work_id']
        clip = json.loads((work/'clips.json').read_text())['clips'][0]
        words = [w for r in json.loads((work/'transcript.json').read_text()) for w in r['words']]
        mapped = {}
        elapsed = 0
        for start, end in clip['segments']:
            for word in words:
                if word['s'] >= end or word['e'] < start or (word['e'] == start and word['s'] < start):
                    continue
                time = round(max(start, word['s'])-start+elapsed, 6)
                mapped.setdefault(time, set()).add(norm(word['w']))
            elapsed += end-start
        count = 0
        for layer in clip['referenceEdit']['layers']:
            tokens = layer['text'].split()
            if len(tokens) != len(layer['wordTimes']):
                raise RuntimeError('Word count mismatch: '+choice['name'])
            for token, time in zip(tokens, layer['wordTimes']):
                expected = mapped.get(round(time, 6), set())
                if norm(token) not in expected:
                    raise RuntimeError(f"Caption/source mismatch: {choice['name']} {time} {token!r}, expected {expected}")
                count += 1
        records.append({'clip': choice['name'], 'authored_words_checked': count})
    return records


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
