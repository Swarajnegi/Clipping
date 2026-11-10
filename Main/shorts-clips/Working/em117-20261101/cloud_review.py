"""Two optional configured-free full-file reviews, with no local media processing."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import study_references as reviewer

ITEMS = [
    ('caption-reference', HERE / 'caption-reference/reference.mp4',
     'Watch and listen to this entire 21-second caption reference. Describe observed caption typography, phrase sizes, placement, italic use, animation and timing with local timestamps. Distinguish exact evidence from estimates; do not guess exact proprietary font names. Transcribe the speech. Is there background music? This is inspiration only; no assets or branding are to be copied.'),
    ('opinions', HERE / 'source/opinions.mp4',
     'Watch and listen to this entire original podcast passage. Use local file seconds. Rate cold-hook and standalone clarity, identify payoff and exact first/last spoken words for a focused short. Is any background music audible under speech? Distinguish music, room tone and microphone sounds. Flag source compression or corrupt-looking frames, source logos/ticker, speech errors and weak cuts. Do not rewrite speech, infer reuse permission or predict virality.'),
]

for name, path, question in ITEMS:
    folder = HERE / 'provider-review' / name
    folder.mkdir(parents=True, exist_ok=True)
    reviewer.QUESTION = question
    try:
        receipt = reviewer.cloud_review(path, folder)
        print('PROVIDER_REVIEW', name, json.dumps(receipt), flush=True)
    except (Exception, SystemExit) as error:
        (HERE / 'provider-review/failure.json').write_text(json.dumps({
            'source': name, 'error': str(error), 'automatic_retry': False,
            'fallback': 'Prepared local frames and CUDA word alignment; assistant review',
        }, indent=2), encoding='utf-8')
        print('Provider unavailable; no retry:', str(error), flush=True)
        raise SystemExit(2)
