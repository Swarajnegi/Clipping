"""Promote seven current, inspected renders with source and hardware receipts."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEST = HERE.parents[1] / 'Exports/01 Finished Edits/2026-11-02 - Cristiano Ronaldo'
NAMES = {
    'map': '01-everyone-wants-to-be-cristiano-music-free.mp4',
    'gym': '02-you-wont-feel-like-it-every-day-music-free.mp4',
    'home': '03-leaving-home-at-eleven-music-free.mp4',
    'lions': '04-the-young-lions-are-coming-music-free.mp4',
    'talent': '05-talent-and-work-ethic-music-free.mp4',
    'breath': '06-the-breath-before-the-penalty-music-free.mp4',
    'visualize': '07-be-ready-before-the-moment-music-free.mp4',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    from audit_caption_words import audit
    caption_audit = audit()
    status = read(HERE / 'status.json')
    guards = status.get('final_guard_runs', [])
    if len(set(guards)) < 2:
        raise RuntimeError('Final render receipts not recorded')
    encoders = 0
    finished_hashes = {}
    for run in guards:
        folder = ROOT / '.runtime/guard' / run
        result = read(folder / 'result.json')
        if result['status'] != 'worker_succeeded' or not result['cleanup_confirmed']:
            raise RuntimeError('Final guard unsuccessful or not clean: ' + run)
        stdout = (folder / 'stdout.log').read_text(errors='replace')
        encoders += stdout.count('Encoder: h264_nvenc, hardware accelerated: true')
        for line in stdout.splitlines():
            if line.startswith('DIALOGUE_FINISHED '):
                receipt = json.loads(line.removeprefix('DIALOGUE_FINISHED '))
                finished_hashes[receipt['work_id']] = receipt['output_sha256']
    if encoders < 7:
        raise RuntimeError('Actual NVENC evidence incomplete')
    choices = read(HERE / 'edit-decisions.json')
    if len(choices) != 7 or {c['name'] for c in choices} != set(NAMES):
        raise RuntimeError('Seven-clip contract failed')
    spans = sorted((a, b, c['name']) for c in choices for a,b in c['pieces'])
    for previous, following in zip(spans, spans[1:]):
        if following[0] < previous[1]:
            raise RuntimeError('Repeated source footage between selections')
    records = []
    for choice in choices:
        vid = choice['work_id']
        final = ROOT / 'out' / vid / 'clip_01.mp4'
        spec_path = ROOT / 'work' / vid / 'clips.json'
        spec = read(spec_path)
        clip = spec['clips'][0]
        qa_path = HERE / 'qa' / vid / 'qa.json'
        qa = read(qa_path)
        if not (qa['complete_decode'] and qa['assistant_inspected']
                and qa.get('branding_check', {}).get('passed')):
            raise RuntimeError('Review incomplete: ' + vid)
        if (qa['music_added'] or spec.get('pairedExports') or spec['brand'].get('music')
                or clip.get('music') or spec.get('watermark') or clip.get('watermark')
                or not clip['referenceEdit'].get('layeredOnly')):
            raise RuntimeError('Music/caption/branding contract failed: ' + vid)
        if qa['spec_sha256'] != digest(spec_path) or qa['output_sha256'] != digest(final):
            raise RuntimeError('Reviewed artifact changed: ' + vid)
        if finished_hashes.get(vid) != qa['output_sha256']:
            raise RuntimeError('Final file not tied to a successful production guard: '+vid)
        duration = float(qa['picture']['duration'])
        frames = int(qa['picture']['nb_read_packets'])
        if not (0 < duration <= 100 and qa['fps'] == 25
                and frames == round(duration * 25) and qa['output_resolution'] == [1080, 1920]):
            raise RuntimeError('Duration, FPS or dimensions failed: ' + vid)
        records.append({
            'title': choice['title'], 'filename': NAMES[choice['name']], 'work_id': vid,
            'sha256': qa['output_sha256'], 'video_duration_seconds': duration,
            'frame_count': frames, 'fps': 25, 'resolution': [1080, 1920],
            'original_segments_seconds': choice['pieces'], 'payoff': choice['payoff'],
            'music_added': False, 'symbol_added': False,
            'dialogue_correlation': qa['speech_retained_correlation'],
            'dialogue_lufs': float(qa['loudness']['input_i']),
            'true_peak_dbtp': float(qa['loudness']['input_tp']),
            'audio_finish': qa.get('audio_finish'), 'qa_receipt': str(qa_path),
        })
    # Inspect destination before copying; never overwrite a different delivery.
    for record in records:
        output = DEST / record['filename']
        if output.exists() and digest(output) != record['sha256']:
            raise RuntimeError('Different delivery already exists: ' + str(output))
    if DEST.exists() and {p.name for p in DEST.glob('*.mp4')} - set(NAMES.values()):
        raise RuntimeError('Unexpected video in delivery directory')
    DEST.mkdir(parents=True, exist_ok=True)
    for record in records:
        output = DEST / record['filename']
        if not output.exists():
            shutil.copy2(ROOT / 'out' / record['work_id'] / 'clip_01.mp4', output)
        if digest(output) != record['sha256']:
            raise RuntimeError('Delivery copy mismatch')
    brief = read(HERE / 'brief.json')
    clean = read(HERE / 'source/clean-final.json')
    gaps = ['Continuous playback/listening not performed',
            'Live Instagram Reels/YouTube Shorts interface overlay preview not performed']
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(), 'project': brief['project'],
        'source_url': brief['source_url'], 'source_title': brief['title'],
        'source_provenance': brief['source_provenance'], 'reuse_basis': brief['reuse_basis'],
        'count_authorization': brief['requested_count'], 'duration_contract': brief['duration'],
        'caption_treatment': 'Silver-white word-revealed short units below the picture on black, selected italic accents and layered payoffs. Original 25 FPS preserved.',
        'branding': clean['branding'], 'source_crop': clean['source_crop'],
        'source_corner_repair': clean['edge_repair'],
        'encoded_audio_payload_preserved_during_reframe': clean['encoded_source_audio_preserved'],
        'guard_runs': guards, 'actual_nvenc_encoder_count': encoders,
        'encoder_count_scope': 'Includes superseded caption drafts; only the seven currently reviewed matching files are delivered',
        'resource_strategy': 'CUDA transcription and source decode/resize, NVENC encoding; bounded CPU layout/corner repair/audio and I/O. Remotion cache 128 MiB, concurrency one. Guard thresholds unchanged.',
        'validation': '33 relevant unit tests passed; full final decode, frame counts, duration, dialogue correlation/alignment, loudness and true peak passed. All generated caption contact sheets and four-frame overview strips inspected.',
        'review_gaps': gaps,
        'caption_word_audit': caption_audit,
        'audio_scope': 'No background music added; original dialogue retained with measured static gain. No claim of source music separation or continuous listening.',
        'clips': records,
    }
    (DEST / 'DELIVERY.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    notes = ['# Cristiano Ronaldo x Will Ahmed - seven music-free clips', '',
             'Seven 1080x1920 vertical masters at the original 25 FPS. No added music, narration, channel symbol or branded end card.',
             'Silver-white word-synchronous captions, selected italic connectors and layered payoffs sit below the picture on black.',
             'Publisher corner overlays were excluded by reframing and background repair; photographed shirt/wearable product lettering remains part of the original scene.', '',
             'Original episode: ' + brief['source_url'],
             'Official provenance: ' + brief['source_provenance'],
             'Reuse basis: owner-confirmed clipping permission/campaign authorization for this episode. Preserve source attribution as appropriate to that authorization.', '']
    for record in records:
        notes.append(f"- **{record['title']}** — {record['video_duration_seconds']:.2f}s. `{record['filename']}`")
    notes += ['', 'Suggested captions:', '',
              '1. Everyone wants the result. Ronaldo on the discipline behind it.',
              '2. Even Ronaldo has days when he does not feel like training. What happens after he starts?',
              '3. Leaving home at eleven. Ronaldo reflects on the sacrifice through the eyes of a father.',
              '4. The young lions are coming. Ronaldo on preparing to keep competing.',
              '5. Talent and work ethic: Ronaldo explains why he needs both.',
              '6. That breath before the penalty is a habit practised in training.',
              '7. Be ready before the moment arrives. Ronaldo describes how he prepares mentally.', '',
              'Suggested source attribution: Cristiano Ronaldo with Will Ahmed, WHOOP Podcast 272. #CristianoRonaldo #Mindset #Football', '',
              'Watch one or two on your phone with sound before posting, checking cuts, caption timing and the actual Reels/Shorts interface overlays.',
              'Continuous playback/listening and live app-overlay checks remain outstanding. Technical checks and sampled caption/framing reviews passed.',
              'No uploading or posting was performed. Consider posting one or two per day and compare actual retention.', '']
    (DEST / 'UPLOAD.md').write_text('\n'.join(notes), encoding='utf-8')
    status.update(state='delivered', active_guard_run=None, exec_session=None,
                  rendered_clips=7, reviewed_clips=7, exports=str(DEST), next_steps=[],
                  pending_caption_rerenders=[], pending_caption_rerender=None)
    (HERE / 'status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
    brief.update(status='Seven reviewed music-free clips delivered')
    (HERE / 'brief.json').write_text(json.dumps(brief, indent=2), encoding='utf-8')
    print(json.dumps({'exports': str(DEST), 'clips': records}, indent=2))


if __name__ == '__main__':
    main()
