"""Promote exactly five reviewed current renders, with provenance and copy hashes."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
DEST=HERE.parents[1]/'Exports/01 Finished Edits/2026-11-01 - Tate Emergency Meeting 117'
NAMES={
    'opinions':'01-opinions-and-your-worth-music-free.mp4',
    'process':'02-the-process-not-just-the-prize-music-free.mp4',
    'opponent':'03-respect-your-opponents-victory-music-free.mp4',
    'regenerate':'04-your-mind-has-to-move-forward-music-free.mp4',
    'silver':'05-find-the-silver-in-the-clouds-music-free.mp4',
}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    status=json.loads((HERE/'status.json').read_text())
    guards=status.get('final_guard_runs',[])
    if len(guards)<2:
        raise RuntimeError('Final corrected render receipts have not been recorded')
    encoders=0
    for run in guards:
        folder=ROOT/'.runtime/guard'/run
        result=json.loads((folder/'result.json').read_text(encoding='utf-8-sig'))
        if result['status']!='worker_succeeded' or not result['cleanup_confirmed']:
            raise RuntimeError('Final guard not successful/clean: '+run)
        encoders+=(folder/'stdout.log').read_text(encoding='utf-8',errors='replace').count('Encoder: h264_nvenc, hardware accelerated: true')
    recovered=status.get('rendered_then_audio_qa_failed_guard')
    if recovered:
        if recovered!='25b54d9cf9a0468696333948a9c4765a':raise RuntimeError('Unknown recovery receipt')
        folder=ROOT/'.runtime/guard'/recovered
        result=json.loads((folder/'result.json').read_text(encoding='utf-8-sig'))
        stdout=(folder/'stdout.log').read_text(encoding='utf-8',errors='replace')
        stderr=(folder/'stderr.log').read_text(encoding='utf-8',errors='replace')
        if result['status']!='failed' or not result['cleanup_confirmed'] or not stderr.rstrip().endswith('RuntimeError: Dialogue loudness needs review'):
            raise RuntimeError('Expected audio QA stop not established')
        if 'done -> '+str(ROOT/'out/em117_20261101_silver') not in stdout:
            raise RuntimeError('Fifth picture render did not finish')
        encoders+=stdout.count('Encoder: h264_nvenc, hardware accelerated: true')
    if encoders<5:
        raise RuntimeError('Actual hardware encoder evidence is incomplete')
    choices=json.loads((HERE/'edit-decisions.json').read_text())
    if len(choices)!=5 or {c['name'] for c in choices}!=set(NAMES):
        raise RuntimeError('Five-clip delivery contract failed')
    records=[]
    for choice in choices:
        vid=choice['work_id']
        final=ROOT/'out'/vid/'clip_01.mp4'
        spec_path=ROOT/'work'/vid/'clips.json'
        spec=json.loads(spec_path.read_text())
        clip=spec['clips'][0]
        qa_path=HERE/'qa'/vid/'qa.json'
        qa=json.loads(qa_path.read_text())
        if not (qa['complete_decode'] and qa['assistant_inspected'] and qa.get('branding_check',{}).get('passed')):
            raise RuntimeError('Review incomplete: '+vid)
        if (qa['music_added'] or spec.get('pairedExports') or spec['brand'].get('music') or clip.get('music')
                or spec.get('watermark') or not clip['referenceEdit'].get('layeredOnly')):
            raise RuntimeError('Music-free/unbranded/caption-pause contract failed: '+vid)
        if qa['spec_sha256']!=digest(spec_path) or qa['output_sha256']!=digest(final):
            raise RuntimeError('Reviewed artifact changed: '+vid)
        record={'title':choice['title'],'filename':NAMES[choice['name']],'work_id':vid,
                'sha256':qa['output_sha256'],'video_duration_seconds':float(qa['picture']['duration']),
                'frame_count':int(qa['picture']['nb_read_packets']),'fps':30,'resolution':[1080,1920],
                'original_segments_approx':choice['original_segments_approx'],'payoff':choice['payoff'],
                'music_added':False,'symbol_added':False,
                'dialogue_correlation':qa['speech_retained_correlation'],
                'dialogue_lufs':float(qa['loudness']['input_i']),
                'true_peak_dbtp':float(qa['loudness']['input_tp']),
                'audio_finish':qa.get('audio_finish'),
                'qa_receipt':str(qa_path.resolve())}
        output=DEST/record['filename']
        if output.exists() and digest(output)!=record['sha256']:
            raise RuntimeError('Different existing delivery; inspect before overwriting')
        records.append(record)
    DEST.mkdir(parents=True,exist_ok=True)
    for record in records:
        final=ROOT/'out'/record['work_id']/'clip_01.mp4'
        output=DEST/record['filename']
        if not output.exists():shutil.copy2(final,output)
        if digest(output)!=record['sha256']:raise RuntimeError('Delivery copy mismatch')
    brief=json.loads((HERE/'brief.json').read_text())
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'project':brief['project'],
              'source_url':brief['source_url'],'source_title':brief['title'],
              'eligible_start_seconds':7860,'reuse_basis':brief['reuse_basis'],
              'count_authorization':brief['count_authorization'],
              'caption_reference':brief['caption_reference'],
              'caption_treatment':'Silver-white bold sans-serif short units, italic accents and layered key phrases; source-native word timestamps; fallback captions suppressed during intentional pauses',
              'branding':'No symbol added. Original sponsor ticker excluded by reframing. No branded outro or reference assets used.',
              'original_resolution':[1920,1080],'clean_source_crop':{'x':480,'y':0,'width':720,'height':1000},
              'encoded_audio_payload_preserved_during_reframe':True,
              'guard_runs':guards,'actual_nvenc_encoder_count':encoders,
              'rendered_then_audio_qa_failed_guard':recovered,
              'audio_qa_recovery':'All picture renders completed; fifth dialogue was below the loudness gate. Static dialogue gain and fresh complete QA resolved it under a separate CPU guard; failed root receipt retained.',
              'final_silver_revision':'Removed the repeated me at the opening seam; rebuilt word-timed captions, rendered and repeated static dialogue finishing plus complete QA under the final guard.',
              'validation':'43 unit tests and TypeScript noEmit passed after caption pause correction; final MP4 full decode, frame count, audio correlation, loudness and stereo true peak passed',
              'review_gaps':['Continuous playback/listening not performed','Live Instagram Reels/YouTube Shorts interface overlay preview not performed','Optional configured-free provider review timed out; uploaded file deletion confirmed; no provider assessment returned'],
              'source_limitations':'Original live-stream compression remains visible at close framing. The conspicuous glitch around opinions local 36s is excluded.',
              'clips':records}
    (DEST/'DELIVERY.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    notes=['# Emergency Meeting 117 - five music-free clips','',
           'Five 1080x1920 vertical masters at 30 FPS. No added music, narration or channel symbol.',
           'Silver-white short caption units, selected italic phrases and larger layered payoffs.',
           'Only source footage after 02:11:00 is used. Native source compression is retained; a conspicuous glitch was excluded.',
           '', 'Original episode: '+brief['source_url'],
           'Reuse basis: owner-confirmed clipping permission/campaign authorization for this episode.',
           'Preserve source attribution in posting text as appropriate to that authorization.', '']
    for record in records:
        notes.append(f"- **{record['title']}** - {record['video_duration_seconds']:.2f}s. `{record['filename']}`")
    notes += ['', 'Suggested posting text:', '',
              '1. Other people can have opinions. They do not get to decide your worth. Andrew Tate on independence from praise and criticism.',
              '2. What if the process matters more than the prize? Andrew Tate on committing to one goal.',
              "3. Respect the person who beat you. Andrew Tate on acknowledging an opponent's victory.",
              '4. Take the lesson and move forward. Andrew Tate uses a healing analogy to talk about recovering from setbacks.',
              "5. You deserve a sunny day. A conversation with his brother becomes a story about finding silver linings.",
              '', 'Suggested tags: #AndrewTate #EmergencyMeeting #Mindset. Clip 5 retains original profanity.',
              '', 'Watch on your phone with sound before posting, including cuts and the Reels/Shorts interface overlay.',
              'Continuous playback/listening and live app-overlay checks remain outstanding. No background music was added; original source audio is retained with measured level adjustment.',
              'Caption/branding frames and the final pause fix were reviewed. Detailed technical QA, source segments and file hashes are in DELIVERY.json.',
              'No uploads or posting were performed. Consider posting one or two per day and comparing actual retention.', '']
    (DEST/'UPLOAD.md').write_text('\n'.join(notes),encoding='utf-8')
    status.update(state='delivered',active_guard_run=None,exec_session=None,rendered_clips=5,
                  reviewed_clips=5,exports=str(DEST.resolve()))
    (HERE/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    print(json.dumps({'exports':str(DEST.resolve()),'clips':records},indent=2))


if __name__=='__main__':
    main()
