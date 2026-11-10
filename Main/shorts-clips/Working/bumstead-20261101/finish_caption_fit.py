"""Re-render the one reviewed caption collision; preserve the previous QA receipt."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import require_guard
from finish_audio import finish
from qa_exports import inspect


def main():
    require_guard(gpu=True)
    vid = 'bumstead_clean_20261101_pursuit'
    spec_path = ROOT / 'work' / vid / 'clips.json'
    spec = json.loads(spec_path.read_text())
    layers = spec['clips'][0]['referenceEdit']['layers']
    final_word = [layer for layer in layers if layer['text'] == 'understands.']
    if len(final_word) != 1 or final_word[0]['x'] != 100 or final_word[0]['y'] != 1158:
        raise RuntimeError('Expected the reviewed final-word line-fit correction')
    qa_path = HERE / 'qa' / vid / 'qa.json'
    old_receipt = HERE / 'qa' / vid / 'qa.before-caption-fit.json'
    if qa_path.exists() and not old_receipt.exists():
        old_receipt.write_bytes(qa_path.read_bytes())
    subprocess.run([sys.executable, str(ROOT / 'scripts/build.py'), str(spec_path)], cwd=ROOT, check=True)
    finish(vid)
    inspect(vid)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
