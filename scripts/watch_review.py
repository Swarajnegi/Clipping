"""Run the restored Gemini watch helper with all configuration and temp files on D:.

THE BIG PICTURE: upstream hardcodes ~/.config/watch; importing its config first allows
an explicit local adapter without changing HOME or copying any credentials.
THE FLOW: verify helper -> bind config paths -> require Gemini -> delegate actual CLI.
"""
from __future__ import annotations

import json
import argparse
import hashlib
import importlib.util
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / ".runtime/claude-video/skills/watch/scripts"
CONFIG = ROOT / ".runtime/watch"


def bound_helper_processes() -> None:
    """Keep upstream frame extraction inside the guard and apply our FFmpeg limits."""
    from common import FFMPEG, ffmpeg_command, require_guard
    require_guard()

    class Processes:
        def __getattr__(self, name):
            return getattr(subprocess, name)

        def run(self, cmd, **kwargs):
            probes = {'-h', '-help', '--help', '-version', '-encoders', '-decoders', '-filters', '-hwaccels'}
            if isinstance(cmd, (list, tuple)) and Path(str(cmd[0])).name.lower() in ('ffmpeg', 'ffmpeg.exe') and not probes.intersection(cmd[1:]):
                cmd = ffmpeg_command([FFMPEG, *cmd[1:]])
            return subprocess.run(cmd, **kwargs)

    import runtime
    import frames
    runtime.subprocess = Processes()
    frames.subprocess = runtime.subprocess


def main() -> int:
    if not (HELPER / "watch.py").is_file():
        raise SystemExit("Gemini watch helper is missing; restore portable assets first")
    sys.path.insert(0, str(HELPER))
    import config

    config.CONFIG_DIR = CONFIG
    config.CONFIG_FILE = CONFIG / ".env"
    if sys.argv[1:] == ["--check"]:
        cfg = config.get_config()
        key = config.load_gemini_key()
        receipt = json.loads((CONFIG / 'readiness.json').read_text()) if (CONFIG / 'readiness.json').exists() else {}
        matches = bool(key and receipt.get('key_fingerprint') == hashlib.sha256(key.encode()).hexdigest())
        print(json.dumps({"helper_present": True, "config_file": str(config.CONFIG_FILE),
                          "gemini_key_present": bool(key), "model": cfg["gemini_model"],
                          "model_verified_with_provider": bool(matches and receipt.get('model_list_verified') and receipt.get('model') == cfg['gemini_model']),
                          "free_tier_confirmed": config.read_env_file().get('WATCH_FREE_TIER_CONFIRMED') == '1',
                          "cloud_review_verified": bool(matches and receipt.get('cloud_review_verified')),
                          "local_fallback_available": True}, indent=2))
        return 0
    args = sys.argv[1:]
    if not any(x in ("-h", "--help") for x in args):
        bound_helper_processes()
        selector = argparse.ArgumentParser(add_help=False)
        selector.add_argument('--engine', choices=['auto', 'local', 'gemini'], default='auto')
        selected, args = selector.parse_known_args(args)
        free = config.read_env_file().get('WATCH_FREE_TIER_CONFIRMED') == '1'
        ready = bool(config.load_gemini_key() and free)
        engine = 'gemini' if selected.engine == 'gemini' or (selected.engine == 'auto' and ready) else 'local'
        if engine == 'gemini' and not ready:
            raise SystemExit('Gemini needs a configured key and confirmed free tier; use --engine local')
        if '--whisper' in args or any(x.startswith('--whisper=') for x in args):
            raise SystemExit('Use the guarded CUDA prep stage for local transcription')
        base = [*args, '--no-whisper', '--out-dir', str(CONFIG / 'work')]
        module_spec = importlib.util.spec_from_file_location('clipping_watch', HELPER / 'watch.py')
        assert module_spec and module_spec.loader
        helper = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(helper)
        def invoke(route: str) -> int:
            sys.argv = [str(HELPER / 'watch.py'), *base, '--engine', route]
            try:
                return helper.main() or 0
            except (SystemExit, OSError, ValueError):
                return 1
        result = invoke(engine)
        fallback = engine == 'gemini' and result != 0 and selected.engine == 'auto'
        if fallback:
            print('Gemini unavailable; preparing local evidence. Assistant review is still required.', file=sys.stderr)
            result = invoke('local')
        receipt_path = CONFIG / 'last-review.json'
        receipt_path.write_text(json.dumps({'requested': selected.engine, 'selected': engine,
            'gemini_succeeded': engine == 'gemini' and not fallback and result == 0,
            'local_preparation_only': engine == 'local' or fallback, 'fallback': fallback,
            'exit_code': result}, indent=2), encoding='utf-8')
        if engine == 'gemini' and not fallback and result == 0 and (CONFIG / 'readiness.json').exists():
            readiness = json.loads((CONFIG / 'readiness.json').read_text())
            readiness['cloud_review_verified'] = True
            (CONFIG / 'readiness.json').write_text(json.dumps(readiness, indent=2), encoding='utf-8')
        return result
    sys.argv = [str(HELPER / "watch.py"), *args]
    runpy.run_path(str(HELPER / "watch.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
