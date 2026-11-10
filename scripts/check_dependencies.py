"""Read installed distribution metadata without importing models or changing the environment."""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path


def main() -> int:
    lock = Path(__file__).resolve().parents[1] / 'requirements.lock.txt'
    issues = []
    checked = 0
    for line in lock.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        name, expected = line.split('==', 1)
        checked += 1
        try:
            found = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            issues.append({'package': name, 'expected': expected, 'found': None})
            continue
        if found != expected:
            issues.append({'package': name, 'expected': expected, 'found': found})
    print(json.dumps({'ready': not issues, 'checked': checked, 'issues': issues,
                      'metadata_only': True, 'native_imports_verified': False}))
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
