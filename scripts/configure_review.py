"""LAYER: Engineer. THE BIG PICTURE: configure review without exposing credentials.
THE FLOW: read the owner's file -> atomic D-drive config -> metadata-only API probe.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from common import ROOT


def configure(source: Path, confirm_free_tier: bool = False) -> dict:
    raw = source.read_bytes()
    text = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
    keys = set(re.findall(r'AIza[A-Za-z0-9_-]{35}', text))
    if len(keys) == 1:
        key = keys.pop()
    else:
        candidate = text.strip().strip('\"\'`')
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{20,512}', candidate):
            raise ValueError('Expected one plain credential or Google API key; contents were not logged.')
        key = candidate
    sys.path.insert(0, str(ROOT / '.runtime/claude-video/skills/watch/scripts'))
    import config
    config.CONFIG_DIR = ROOT / '.runtime/watch'
    config.CONFIG_FILE = config.CONFIG_DIR / '.env'
    config.write_settings({'GEMINI_API_KEY': key, 'WATCH_ENGINE': 'gemini', 'WATCH_WHISPER_BACKEND': 'none'})
    if confirm_free_tier:
        config.write_settings({'WATCH_FREE_TIER_CONFIRMED': '1'})
    receipt = {'checked_at': datetime.now(timezone.utc).isoformat(), 'key_present': True,
               'key_fingerprint': hashlib.sha256(key.encode()).hexdigest(), 'model_list_verified': False,
               'cloud_review_verified': False, 'free_tier_confirmed': confirm_free_tier, 'generation_request_sent': False}
    try:
        request = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models?pageSize=1000',
                                         headers={'x-goog-api-key': key})
        with urllib.request.urlopen(request, timeout=25) as response:
            models = json.load(response).get('models', [])
        available = {m['name'].removeprefix('models/') for m in models if 'generateContent' in m.get('supportedGenerationMethods', [])}
        selected = next((name for name in ('gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-2.5-flash') if name in available), None)
        receipt.update(model_list_verified=True, model=selected)
        if selected:
            config.write_settings({'WATCH_GEMINI_MODEL': selected})
    except urllib.error.HTTPError as error:
        receipt['reason'] = f'Model listing rejected with HTTP {error.code}; local review is available.'
    except (OSError, ValueError):
        receipt['reason'] = 'Model listing unavailable; local review is available.'
    (config.CONFIG_DIR / 'readiness.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    return {k: v for k, v in receipt.items() if k != 'key_fingerprint'}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--key-file', type=Path, required=True)
    parser.add_argument('--confirm-free-tier', action='store_true')
    args = parser.parse_args()
    print(json.dumps(await asyncio.to_thread(configure, args.key_file, args.confirm_free_tier), indent=2))


if __name__ == '__main__':
    asyncio.run(main())
