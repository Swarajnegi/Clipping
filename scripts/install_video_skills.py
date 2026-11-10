"""LAYER: Engineer. THE BIG PICTURE: use pinned specialist guidance stored on D:.
THE FLOW: official installer -> project skills -> source receipt. No model downloads.
"""
from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
from pathlib import Path

from common import ROOT, require_guard

SOURCES = [
    ('remotion-dev/skills', '6c67adcd9cdbe6eb84d76342da89b225f9161cb2', 'skills/remotion-best-practices', 'remotion-best-practices'),
    ('remotion-dev/skills', '6c67adcd9cdbe6eb84d76342da89b225f9161cb2', 'skills/remotion-captions', 'remotion-captions'),
    ('remotion-dev/skills', '6c67adcd9cdbe6eb84d76342da89b225f9161cb2', 'skills/remotion-render', 'remotion-render'),
    ('wheresryan22/anatomy', '1482e8469b0a9e0d8cc18ea2740a01423d29ae80', '.', 'anatomy'),
]


def normalize_metadata(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    digest = hashlib.sha256(text.encode()).hexdigest()
    _, header, body = text.split('---', 2)
    adapted = {}
    for name in ('version', 'compatibility'):
        match = re.search(rf'(?m)^{name}: (.+)\n', header)
        if match:
            adapted['upstream_' + name] = match[1]
            header = header[:match.start()] + header[match.end():]
    if adapted:
        rows = ''.join(f'  {name}: {json.dumps(value)}\n' for name, value in adapted.items())
        if '\nmetadata:\n' in header:
            header = header.replace('\nmetadata:\n', '\nmetadata:\n' + rows, 1)
        else:
            header += 'metadata:\n' + rows
        path.write_text('---' + header + '---' + body, encoding='utf-8')
    return {'upstream_skill_sha256': digest, 'frontmatter_adaptation': adapted}


def main() -> None:
    require_guard()
    installer = Path.home() / '.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py'
    destination = ROOT / '.agents/skills'
    records = []
    for repo, revision, path, name in SOURCES:
        if (destination / name).exists():
            raise RuntimeError(f'{name} already exists; inspect its source before replacing it.')
        subprocess.run([sys.executable, str(installer), '--repo', repo, '--ref', revision, '--path', path,
                        '--name', name, '--dest', str(destination), '--method', 'download'], check=True)
        records.append({'repo': repo, 'revision': revision, 'path': path, 'skill': name,
                        **normalize_metadata(destination / name / 'SKILL.md')})
    (destination / 'video-skill-sources.json').write_text(json.dumps(records, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
