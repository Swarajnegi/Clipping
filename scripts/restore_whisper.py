"""Restore pinned, checksum-verified Whisper files through bounded HTTP downloads."""
from __future__ import annotations

import json
from common import ROOT, require_guard
from restore_assets import download, read_json, RECEIPTS


def main() -> None:
    require_guard()
    repo = 'Systran/faster-whisper-small'
    metadata = read_json(f'https://huggingface.co/api/models/{repo}?blobs=true')
    revision = metadata['sha']
    target = ROOT / 'models/whisper-small'
    target.mkdir(parents=True, exist_ok=True)
    files = {entry['rfilename']: entry for entry in metadata['siblings']}
    for name in ('config.json', 'tokenizer.json', 'vocabulary.txt', 'model.bin'):
        checksum = files[name].get('lfs', {}).get('sha256')
        download(f'https://huggingface.co/{repo}/resolve/{revision}/{name}', target / name, checksum)
    receipt = {'repo': repo, 'revision': revision, 'complete': True, 'files': RECEIPTS}
    (target / 'restoration.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print('Whisper model restored:', target, flush=True)


if __name__ == '__main__':
    main()
