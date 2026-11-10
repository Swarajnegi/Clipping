"""Restore npm's resolved lock one archive at a time to avoid antivirus/file-creation bursts.

LAYER: Engineer. THE BIG PICTURE: npm's bulk unpacking caused sustained host CPU aborts.
THE FLOW: consume npm's lock -> validate SRI -> stream safe files at <=100 creations/s -> bin shims.
Dependency resolution remains npm's job. Lifecycle scripts are deliberately never executed.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import tarfile
import time
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from common import ROOT, NODE, require_guard
from restore_assets import download


def compatible(choices: list[str] | None, value: str) -> bool:
    if not choices:
        return True
    return f"!{value}" not in choices and (value in choices or not any(not x.startswith("!") for x in choices))


def sri(path: Path, algorithm: str, expected: str) -> bool:
    with path.open("rb") as stream:
        actual = base64.b64encode(hashlib.file_digest(stream, algorithm).digest()).decode()
    return hmac.compare_digest(actual, expected)


def install() -> None:
    require_guard()
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    top = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    for group in ("dependencies", "devDependencies"):
        if top.get(group, {}) != lock["packages"][""].get(group, {}):
            raise RuntimeError("Manifest and dependency lock differ; regenerate the lock first")
    modules = ROOT / "node_modules"
    modules.mkdir(exist_ok=True)
    cache = ROOT / ".runtime/npm-tarballs"
    cache.mkdir(parents=True, exist_ok=True)
    npm_cache = Path(os.environ["npm_config_cache"]) / "_cacache/content-v2"
    entries = []
    receipt = ROOT / ".runtime/pipeline-restore/node-packages.json"
    for relative, info in lock["packages"].items():
        if not relative:
            continue
        if not compatible(info.get("os"), "win32") or not compatible(info.get("cpu"), "x64"):
            if not info.get('optional'):
                raise RuntimeError('Required package does not support Windows x64: ' + relative)
            continue
        if info.get("link") or not relative.startswith("node_modules/"):
            raise RuntimeError("Unsupported non-registry lock entry: " + relative)
        target = (ROOT / relative).resolve()
        if not target.is_relative_to(modules.resolve()) or target.is_symlink():
            raise ValueError("Package destination escapes node_modules")
        url = info["resolved"]
        if urlparse(url).scheme != "https" or urlparse(url).hostname != "registry.npmjs.org":
            raise ValueError("Unexpected package registry")
        integrity = info["integrity"].split()[0]
        algorithm, expected = integrity.split("-", 1)
        if algorithm not in ("sha512", "sha256", "sha1"):
            raise ValueError("Unsupported package integrity algorithm")
        hex_digest = base64.b64decode(expected, validate=True).hex()
        cached = npm_cache / algorithm / hex_digest[:2] / hex_digest[2:4] / hex_digest[4:]
        if cached.is_file() and sri(cached, algorithm, expected):
            archive = cached
        else:
            archive = download(url, cache / (hex_digest + ".tgz"))
        if not sri(archive, algorithm, expected):
            raise ValueError("Package integrity mismatch: " + relative)
        print("install", relative, info["version"], flush=True)
        count = 0
        with tarfile.open(archive, mode="r|gz") as bundle:
            for item in bundle:
                parts = PurePosixPath(item.name).parts
                if len(parts) < 2 or item.isdir():
                    continue
                if not item.isfile() or ".." in parts or PurePosixPath(item.name).is_absolute():
                    raise ValueError("Unsafe package archive entry")
                dest = (target / Path(*parts[1:])).resolve()
                if not dest.is_relative_to(target):
                    raise ValueError("Package file escapes destination")
                dest.parent.mkdir(parents=True, exist_ok=True)
                incoming = bundle.extractfile(item)
                assert incoming is not None
                with incoming, dest.open("wb") as output:
                    while chunk := incoming.read(64 * 1024):
                        output.write(chunk)
                count += 1
                time.sleep(0.01)
        package = json.loads((target / "package.json").read_text(encoding="utf-8"))
        if package.get("version") != info["version"]:
            raise ValueError("Extracted package version differs from the lock")
        entries.append({"path": relative, "version": info["version"], "integrity_verified": True, "files": count})
        receipt.write_text(json.dumps({"packages": entries, "lifecycle_scripts": False, "complete": False}, indent=2), encoding="utf-8")
    script = ROOT / ".runtime/pipeline-restore/create-bin-shims.cjs"
    script.write_text('''const fs = require('node:fs');
const path = require('node:path');
const root = process.argv[2];
const shim = require(path.join(root, '.runtime/node/node_modules/npm/node_modules/cmd-shim'));
const receipt = JSON.parse(fs.readFileSync(path.join(root, '.runtime/pipeline-restore/node-packages.json'), 'utf8'));
(async () => {
  for (const entry of receipt.packages) {
    const directory = path.join(root, entry.path);
    const pkg = JSON.parse(fs.readFileSync(path.join(directory, 'package.json'), 'utf8'));
    const bins = typeof pkg.bin === 'string' ? {[pkg.name.split('/').pop()]:pkg.bin} : (pkg.bin || {});
    let parent = path.dirname(directory);
    while (path.basename(parent) !== 'node_modules') parent = path.dirname(parent);
    for (const [name, file] of Object.entries(bins)) {
      if (name.includes('/') || name.includes('\\\\') || name === '..') throw Error('Unsafe bin name');
      const source = path.resolve(directory, file);
      if (!source.startsWith(directory + path.sep)) throw Error('Unsafe bin target');
      await shim(source, path.join(parent, '.bin', name));
    }
  }
})().catch(error => { console.error(error); process.exitCode=1; });
''', encoding="utf-8")
    subprocess.run([str(NODE), str(script), str(ROOT)], check=True)
    receipt.write_text(json.dumps({"packages": entries, "lifecycle_scripts": False, "complete": True}, indent=2), encoding="utf-8")
    print("Installed", len(entries), "locked packages sequentially", flush=True)


if __name__ == "__main__":
    install()
