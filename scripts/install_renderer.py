"""Install the recovered renderer manifest and its browser inside the guarded D-drive project."""
from __future__ import annotations

import subprocess
import argparse
import os
from common import NODE, ROOT, REMOTION, require_guard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--lock-only', action='store_true')
    args = parser.parse_args()
    require_guard()
    npm = ROOT / ".runtime/node/node_modules/npm/bin/npm-cli.js"
    if args.lock_only or not (ROOT / 'package-lock.json').exists():
        environment = {**os.environ, 'UV_THREADPOOL_SIZE': '1'}
        subprocess.run([str(NODE), str(npm), 'install', "--ignore-scripts", "--no-audit", "--no-fund", "--maxsockets=1",
                        '--package-lock-only'], cwd=ROOT, env=environment, check=True)
    if args.lock_only:
        return
    from install_locked_packages import install
    install()
    subprocess.run([str(NODE), str(REMOTION), "browser", "ensure", "--log=verbose"], cwd=ROOT, check=True)
    subprocess.run([str(NODE), "node_modules/typescript/bin/tsc", "--noEmit", "-p", "."], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
