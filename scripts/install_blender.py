"""LAYER: Engineer. THE BIG PICTURE: reproducible D-drive-only portable 3D tooling.
THE FLOW: guard -> disk reserve -> official SHA256 -> archive -> verified extraction -> receipt.
"""
from __future__ import annotations
import hashlib,json,shutil,sys,urllib.request
from pathlib import Path
from common import ROOT,require_guard
from restore_assets import download,extract

def main() -> None:
    require_guard()
    version='4.5.15'
    filename=f'blender-{version}-windows-x64.zip'
    base='https://download.blender.org/release/Blender4.5/'
    target=ROOT/'.runtime/blender'/version
    if shutil.disk_usage(ROOT).free < 22*1024**3:
        raise RuntimeError('Blender setup requires at least 22 GiB free, including the 20 GiB reserve')
    request=urllib.request.Request(base+f'blender-{version}.sha256',headers={'User-Agent':'Clipping-3D-Test'})
    with urllib.request.urlopen(request,timeout=60) as response:
        checksums=response.read().decode()
    expected=next(line.split()[0] for line in checksums.splitlines() if line.split()[-1].lstrip('*')==filename)
    archive=download(base+filename,ROOT/'.runtime/downloads'/filename,expected)
    if not (target/'blender.exe').is_file():
        extract(archive,target)
    for name in ('config','scripts','datafiles','cache'):
        (ROOT/'.runtime/blender-user'/name).mkdir(parents=True,exist_ok=True)
    receipt={'version':version,'archive':str(archive),'official_url':base+filename,
             'sha256':expected,'checksum_verified':True,'executable':str(target/'blender.exe')}
    (target/'installation.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
