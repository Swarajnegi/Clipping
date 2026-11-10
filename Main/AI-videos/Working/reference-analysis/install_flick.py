"""LAYER: Engineer. Install pinned Flick guidance, not its alternate Python runtime.
THE FLOW: guarded official installer -> local storage/guard note -> provenance receipt.
"""
from pathlib import Path
import sys,subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
from common import require_guard

def main():
    require_guard()
    revision='4442fe355644317aafbe15c55ea3fbcd0217cd8d'
    destination=ROOT/'.agents/skills'
    installer=Path.home()/'.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py'
    subprocess.run([sys.executable,str(installer),'--repo','Creatorberry/flick','--ref',revision,'--path','skills/flick','--dest',str(destination),'--method','download'],check=True)
    path=destination/'flick/SKILL.md'
    original=path.read_text(encoding='utf-8')
    note='''\n## Local Clipping integration\n\nOn this host, use `D:\\J.A.R.V.I.S\\Clipping` and read the adjacent\n`ai-video/SKILL.md` plus its stage-routing guide before local media work.\nUse the existing Clipping Python, Node, FFmpeg and CUDA faster-whisper runtime.\nDo not run Flick bootstrap: its `pip --user` installation violates the owner\nstorage policy. All installation, transcription and rendering use the shared\nviral-shorts resource guard, one operation at a time, with its existing limits.\nKeep generated work under `Main/AI-videos/Working/<project-id>` and reviewed\nfinished videos under `Main/AI-videos/Exports/<project-id>`.\nThe owner prefers one final rendering batch. Separate authored scene components\nare useful; mandatory separate scene exports are not required for this workflow.\nUse reference-appropriate visuals: these templates are not a 3D asset generator.\nUse known brief details rather than asking for aspect ratio or direction again.\nDo not add promotional messages or auto-start Studio solely for technical checks.\n\n'''
    path.write_text(original.replace('# /flick\n','# /flick\n'+note,1),encoding='utf-8')
    receipt=destination/'video-skill-sources.json'
    sources=json.loads(receipt.read_text())
    sources.append({'repo':'Creatorberry/flick','revision':revision,'path':'skills/flick','skill':'flick','upstream_skill_sha256':hashlib.sha256(original.encode()).hexdigest(),'local_adaptation':'D-drive storage, existing runtime, shared guard, conditional scene exports, no promotion'})
    receipt.write_text(json.dumps(sources,indent=2),encoding='utf-8')
    print('Flick guidance installed; bootstrap not executed.',flush=True)

if __name__=='__main__':main()
