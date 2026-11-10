"""Render reviewed project edits sequentially and validate their actual outputs."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from common import FFMPEG, ffmpeg_command, require_guard
from finish_audio import finish
from qa_exports import inspect


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    require_guard(gpu=True)
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',default='')
    args=parser.parse_args()
    choices=json.loads((HERE/'edit-decisions.json').read_text())
    if len(choices)!=5:
        raise RuntimeError('Owner requested five clips from this episode')
    for choice in choices:
        if args.only and choice['name']!=args.only:
            continue
        vid=choice['work_id']
        spec=ROOT/'work'/vid/'clips.json'
        final=ROOT/'out'/vid/'clip_01.mp4'
        qa_path=HERE/'qa'/vid/'qa.json'
        if qa_path.exists() and final.exists():
            qa=json.loads(qa_path.read_text())
            if qa['spec_sha256']!=digest(spec) or qa['output_sha256']!=digest(final):
                raise RuntimeError('Previously reviewed artifact changed; inspect before continuing')
            if choice['name']=='opinions' and not args.only:
                proof=HERE/'caption-fix-proof'
                proof.mkdir(exist_ok=True)
                for time in (16.43,18.70,18.87):
                    subprocess.run(ffmpeg_command([FFMPEG,'-v','error','-y','-ss',str(time),
                                                  '-i',str(final),'-frames:v','1','-vf','scale=540:960',
                                                  str(proof/f'pause-{time:.2f}.jpg')]),check=True)
            print('REUSE_VALIDATED',vid,flush=True)
            continue
        subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),str(spec)],cwd=ROOT,check=True)
        finish(vid)
        inspect(vid)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
