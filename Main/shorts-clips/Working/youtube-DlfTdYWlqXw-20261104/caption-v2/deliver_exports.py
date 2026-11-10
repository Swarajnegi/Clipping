"""Copy the owner's six selected revisions to the expected delivery folder."""
import hashlib,json,shutil
from pathlib import Path

REV=Path(__file__).resolve().parent
EXPORTS=REV.parents[2]/'Exports'/'01 Finished Edits/2026-11-05 - Luke Belmar'
assert EXPORTS.resolve().is_relative_to(Path('D:/J.A.R.V.I.S/Clipping/Main/shorts-clips/Exports').resolve())
manifest=json.loads((REV/'REVIEW_MANIFEST.json').read_text(encoding='utf-8'))
assert len(manifest['files'])==6 and '07-silver-thread' in manifest['skipped']
EXPORTS.mkdir(parents=True,exist_ok=True)
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

posting=['# Luke Belmar — six music-free 4K clips\n',
         'Delivered 5 November 2026 at the owner’s request. Silver-thread is excluded.\n',
         'Selective colour-reactive captions and serif italic accents. Cuts, framing and dialogue are unchanged.\n',
         'Technical checks and caption-sample review passed. Full playback with sound has not been newly verified; dialogue packets and timing match the previous versions exactly.\n']
for entry in manifest['files']:
    source=Path(entry['file'])
    assert source.is_file() and sha(source)==entry['sha256']
    destination=EXPORTS/source.name.replace('-DRAFT.mp4','.mp4')
    if destination.exists():
        assert sha(destination)==entry['sha256'],'Refusing to overwrite a different export'
    else:
        pending=destination.with_suffix('.partial.mp4')
        assert not pending.exists(),'Existing incomplete copy needs inspection'
        shutil.copy2(source,pending)
        assert sha(pending)==entry['sha256'],'Export copy failed integrity check'
        pending.rename(destination)
    entry['working_file']=entry['file']
    entry['file']=str(destination)
    entry['export_copy_hash_verified']=True
    decision=next(d for d in json.loads((REV/'edit-decisions.json').read_text()) if d['slug']==entry['slug'])
    posting.extend([f"## {entry['title']}\n",
                    f"[Video — {entry['duration']:.2f}s]({destination.as_posix()})\n",
                    decision['description']+'\n'])
manifest['status']='Six export copies delivered at owner request; technical checks and caption-sample review passed'
manifest['delivery_date']='2026-11-05 Asia/Calcutta'
manifest['working_review_manifest']=str(REV/'REVIEW_MANIFEST.json')
(EXPORTS/'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
(EXPORTS/'POSTING_COPY.md').write_text('\n'.join(posting),encoding='utf-8')
receipt=dict(exports=str(EXPORTS),files=6,copy_hashes_verified=True,
             silver_thread_excluded=True,working_originals_preserved=True,
             review_gap=manifest['review_gap'])
(REV/'export-delivery.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    pass
