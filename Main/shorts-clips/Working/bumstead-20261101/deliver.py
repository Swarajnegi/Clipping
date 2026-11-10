"""Promote only the three reviewed clean music-free outputs and record provenance."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[3]
DEST = HERE.parents[1] / 'Exports' / '01 Finished Edits/2026-11-01 - Chris Bumstead'
NAMES = [
    '01-doubt-and-being-a-champion-music-free.mp4',
    '02-more-than-my-mind-understands-music-free.mp4',
    '03-your-children-see-the-real-you-music-free.mp4',
]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    choices = json.loads((HERE / 'edit-decisions.json').read_text())
    if len(choices) != 3:
        raise RuntimeError('Expected exactly three selected clips from the authorized episode')
    guards = ['75e07068fd56467cae4f8d0b994c3345', 'fb07b3c0499f43be9b850375798922d4']
    for run in guards:
        result = json.loads((ROOT / '.runtime/guard' / run / 'result.json').read_text(encoding='utf-8-sig'))
        if result.get('status') != 'worker_succeeded' or not result.get('cleanup_confirmed'):
            raise RuntimeError(f'Guard not finished successfully: {run}')
    clips = []
    for choice, filename in zip(choices, NAMES):
        vid = choice['work_id']
        source = ROOT / 'out' / vid / 'clip_01.mp4'
        qa_path = HERE / 'qa' / vid / 'qa.json'
        qa = json.loads(qa_path.read_text())
        spec_path = ROOT / 'work' / vid / 'clips.json'
        spec = json.loads(spec_path.read_text())
        clip = spec['clips'][0]
        if (not qa.get('complete_decode') or not qa.get('assistant_inspected') or
                not qa.get('branding_check', {}).get('passed') or qa.get('music_added')):
            raise RuntimeError(f'Review incomplete: {vid}')
        if (spec.get('pairedExports') or spec['brand'].get('music') or clip.get('music') or
                clip.get('watermark') or spec['brand'].get('watermark')):
            raise RuntimeError(f'Music-free/unbranded delivery contract failed: {vid}')
        if qa['spec_sha256'] != digest(spec_path) or qa['output_sha256'] != digest(source):
            raise RuntimeError(f'Reviewed artifact changed: {vid}')
        if qa.get('visual_review_status', '').startswith('pending'):
            raise RuntimeError(f'Caption repair pending: {vid}')
        output = DEST / filename
        if output.exists() and digest(output) != qa['output_sha256']:
            raise RuntimeError(f'Existing delivery differs; inspect before overwriting: {output}')
        clips.append({
            'title': choice['title'], 'filename': filename, 'work_id': vid,
            'sha256': qa['output_sha256'], 'frame_count': int(qa['picture']['nb_read_packets']),
            'video_duration_seconds': float(qa['picture']['duration']), 'resolution': [1080, 1920],
            'fps': 25, 'source_segments_approx': choice['original_segments_approx'],
            'payoff': choice['payoff'], 'music_added': False, 'symbol_added': False,
            'dialogue_correlation': qa['speech_retained_correlation'],
            'dialogue_lufs': float(qa['loudness']['input_i']),
            'true_peak_dbtp': float(qa['loudness']['input_tp']),
            'qa_receipt': str(qa_path.resolve()),
        })
    DEST.mkdir(parents=True, exist_ok=True)
    for record in clips:
        source = ROOT / 'out' / record['work_id'] / 'clip_01.mp4'
        output = DEST / record['filename']
        if not output.exists():
            shutil.copy2(source, output)
        if digest(output) != record['sha256']:
            raise RuntimeError(f'Delivery copy hash mismatch: {output}')
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'project': 'bumstead-20261101',
        'source_url': 'https://www.youtube.com/watch?v=DHWEqlG7DI0',
        'source': 'Chris Bumstead with Chris Williamson - Modern Wisdom 851',
        'reuse_basis': 'Owner explicitly confirmed clipping permission/campaign authorization for this episode in chat on 2026-11-01',
        'branding': 'No channel symbol. Original bottom publisher overlay excluded by clean source framing.',
        'source_crop': {'x': 90, 'y': 0, 'width': 1740, 'height': 816, 'original_resolution': [1920, 960]},
        'source_reframing_preserved_encoded_audio_payload': True,
        'caption_style': 'Silver-white word-synchronous text; condensed keywords, selected italic serif phrases, independently timed overlapping layers',
        'caption_layering': 'Text layers only; no person matte',
        'guard_runs': guards,
        'actual_encoder': 'h264_nvenc; hardware accelerated, verified in render logs',
        'delivery': 'Three music-free clips only; no mixed companions',
        'review_gaps': ['Continuous playback/listening not performed', 'Live Reels/Shorts interface overlay preview not performed', 'Optional provider review timed out; upload deletion confirmed; no provider assessment returned'],
        'clips': clips,
    }
    (DEST / 'DELIVERY.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    notes = '''# Bumstead - three music-free clips

1080x1920 vertical masters, 25 FPS. No added music, narration or channel symbol.
Silvery-white captions follow the speaker, with italic phrases and layered emphasis.
The original publisher overlay is excluded by framing; no reference branding is used.

Source: Chris Bumstead with Chris Williamson, Modern Wisdom 851.
Original episode: https://www.youtube.com/watch?v=DHWEqlG7DI0
Reuse basis: owner-confirmed clipping permission/campaign authorization for this episode.
Keep source attribution in posting text as appropriate to that authorization.

'''
    for record in clips:
        notes += f"- **{record['title']}** - {record['video_duration_seconds']:.2f}s. `{record['filename']}`\n"
    notes += '''
Suggested posting text:

1. Doubt does not have to disappear before you perform. Chris Bumstead on being a champion while still questioning himself.
2. Your assumed limit can be wrong. Chris Bumstead on discovering he had more in him than he understood.
3. Your children see the person behind the public image. Chris Bumstead on becoming someone worth learning from.

Suggested tags: #ChrisBumstead #CBum #Mindset. For clip 3, #Fatherhood.
Clips 1 and 3 retain the speaker's original profanity.

Watch on your phone before posting, including sound, cuts and the Reels/Shorts interface overlay.
Captions sit in the central picture band; live app-interface validation remains outstanding.
Technical checks passed: complete decode, expected frame count, original dialogue correlation,
stereo clipping/true peak and loudness. Final caption and branding frames were inspected.
Continuous playback/listening was not performed. No background music was added;
source audio was retained with level adjustment. Post one or two per day and compare retention.

No uploads or posting were performed. Detailed provenance, hashes and review coverage are in DELIVERY.json.
'''
    (DEST / 'UPLOAD.md').write_text(notes, encoding='utf-8')
    status_path = HERE / 'status.json'
    status = json.loads(status_path.read_text())
    status.update(active_guard_run=None, exec_session=None, rendered_final_clips=3,
                  visually_reviewed_clips=3, branding_checked_clips=3,
                  state='delivered', exports=str(DEST.resolve()))
    status.pop('pending_caption_fit', None)
    status['final_caption_fit'] = {'work_id': choices[1]['work_id'], 'guard': guards[1], 'reviewed': True}
    status_path.write_text(json.dumps(status, indent=2), encoding='utf-8')
    brief_path = HERE / 'brief.json'
    brief = json.loads(brief_path.read_text())
    brief['caption_style_update']['status'] = 'Implemented, final caption-fit correction reviewed; three clean exports delivered'
    brief_path.write_text(json.dumps(brief, indent=2), encoding='utf-8')
    print(json.dumps({'exports': str(DEST.resolve()), 'clips': clips}, indent=2))


if __name__ == '__main__':
    main()
