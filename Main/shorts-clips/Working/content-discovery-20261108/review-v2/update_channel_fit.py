"""Apply the owner's posted-channel correction without approving unreviewed edits."""
import json
from pathlib import Path

P = Path(__file__).resolve().parent
BASE = P.parent
notes = {
    '04-choose-your-regret': (1, 'study_channel_fit', ['nD6p-qYd728', 'EdMJXSF8-xw'],
        'Avoiding a difficult decision has a cost too. Closest current lead to the posted unmade-decisions and commitment insights; spoken opening and restarted phrasing still need listening.'),
    '07-i-think-im-lonely': (2, 'study_channel_fit', ['RUlpjXk9Y-o', 'MYDuCsVF6yw'],
        'Being surrounded by people while hiding your real self is a recognisable private conflict. Inspect the authentic-personality turn; a lonely-journal disclosure alone is insufficient.'),
    '03-winning-someone-elses-game': (3, 'secondary_fit', ['RUlpjXk9Y-o'],
        'Can expose pursuing someone else\'s definition of success. Hold unless the genuine opening foregrounds that conflict and the payoff stands independently of income figures.'),
    '05-married-to-different-people': (4, 'hold_fit', ['gPXNhU9t848', 'RUlpjXk9Y-o'],
        'Private authenticity and principles could fit, but the multiple-women opening risks curiosity dominating the human point. Needs a more direct, faithful editorial proposal.'),
    '02-dads-unexpected-answer': (5, 'hold_fit', ['EdMJXSF8-xw', 'RUlpjXk9Y-o'],
        'Parental approval and committing to one\'s own path could fit. Not the automatic next proof: extended career-story setup must earn a recognisable viewer connection.'),
    '06-not-a-bucket-list': (6, 'hold_fit', ['MYDuCsVF6yw'],
        'Emotional acceptance could fit, but diagnosis and a humorous list label alone are not enough. Hold pending a stronger complete personal insight.'),
    '08-childhood-on-the-road': (7, 'hold_fit', [],
        'Interesting biography, but the present proposal lacks a sufficiently immediate viewer-facing reframe. Keep as a lead; do not spend on a proof now.'),
}

for path in (BASE / 'candidate-bank.json', P / 'candidate-bank.json'):
    bank = json.loads(path.read_text(encoding='utf-8'))
    for item in bank:
        if item['id'] not in notes:
            continue  # Preserve the owner's explicit rejection and archive record.
        rank, priority, matches, reason = notes[item['id']]
        if 'channel_fit_review_before_owner_correction' not in item:
            item['channel_fit_review_before_owner_correction'] = {
                'priority': item.get('priority'), 'gate': item['checks']['channel_fit']}
        item['priority'] = priority
        item['checks']['channel_fit'] = 'pending'
        item['channel_match_review'] = {
            'date': '2026-11-08', 'rank_for_study': rank,
            'primary_benchmark_ids': matches, 'reason': reason,
            'status': 'editorial hypothesis; not owner approval or full audiovisual acceptance'}
    path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

report = '''# thought.palace: posted content comes first

Owner direction, 8 November 2026: target content like the videos already posted.
This revises discovery priorities; it does not approve another production batch.

## Primary examples and inspection coverage

Verified official owner channel: @thought.palace, UCF5cZszysRZZGaW0CGgz0Fw.
See owner-channel-identity.json, owner-channel-listing.json and posted-current/.

| Actual posted cut | Duration | Editorial reference |
| --- | ---: | --- |
| [The REAL Reason You're Stressed](https://www.youtube.com/shorts/nD6p-qYd728) | 12s | Unmade decisions as a recognisable emotional burden. |
| [Whose Dream Are You Actually Chasing?](https://www.youtube.com/shorts/RUlpjXk9Y-o) | 24s | Your own ambition versus other people's expectations. |
| [You Don't Have to Be Happy All the Time](https://www.youtube.com/shorts/MYDuCsVF6yw) | 35s | Permission to experience the full range of life. |
| [Give Yourself the Chance to Find Out](https://www.youtube.com/shorts/EdMJXSF8-xw) | 37s | Commitment resolves the regret of never really finding out. |
| [Your Children Will Know Who You Really Are](https://www.youtube.com/shorts/gPXNhU9t848) | 34s | Character in private and responsibility for what children inherit. |

Four posts supplied published captions. Happiness metadata succeeded with no captions;
its actual posted file was downloaded and fully transcribed through CUDA. Seven
five-second picture samples inspected. The happiness passage starts “This idea of
being happy...” and ends “to neglect life”; the 77.8s local master is not the posted
35s cut. No new continuous playback/listening of all five posts is claimed. The
Peterson caption retrieval ends mid-thought; that alone does not prove an audio-cut fault.
Published captions and ASR are not error-free word alignment.

Public counts are dated reach snapshots, not retention evidence. The earlier owner
selections about worth/opinions and process/prize remain positive references; their
absence from this bounded channel listing does not establish why or whether a post
was removed. Older unrelated gaming/car uploads are not current style benchmarks.

## Selection rule for this channel

Identify the viewer's recognisable feeling or dilemma, the spoken reframe and the
specific landing. Name a posted example it resembles in meaning, independently of
the speaker's fame. A gripping anecdote or large money figure cannot supply missing
personal relevance. Full listening, context and the five editorial gates still apply.
These are channel-specific priorities, not universal claims about viral content.

## Current research order

1. **Choose your regret** — Hormozi, Modern Wisdom, 35:11–35:59.
   Closest to unmade decisions/commitment. Listen for a fluent opening before a proof.
2. **Hiding yourself while feeling lonely** — Williamson, Iced Coffee Hour,
   1:18:10–1:18:45. Closest to authenticity/emotional permission. Needs an earned
   insight beyond the disclosure itself.
3. **Winning someone else's game** — Hormozi, Modern Wisdom, 1:05:52–1:06:38,
   with the bank's two selected spans. Secondary: only worthwhile if the borrowed
   ambition matters more than income escalation.

Other initial leads are held for fit review. The father/film-school story is not
automatically next just because that source is authorised. The offer proof remains
owner-rejected and archived UNSELECTED in Exports/03 Archive/2026-11-08 - McConaughey Offer Story - Unselected.
Permission for the two other episodes above is unknown; no production is approved
by this report. The DOAC episode QMzxNfX-uAg has explicit owner permission.

## Additional authorised lead inspected, not selected

DOAC McConaughey 9:11–10:05: “I can't” versus “you're just having trouble”.
The ordinary difficulty/ability distinction could fit the commitment reference.
The 54s context file was fully CUDA-transcribed and all eleven five-second samples
inspected under guard 7c9c1c9c5a874b78b713d55e0fb56a79 (success; cleanup confirmed).
The mower story contains a long walk-through-the-house setup. Do not render that
whole story just to use an authorised source. The end starts the separate “I hate
you” story; exclude it. ASR has obvious uncertain words; no frame-exact cut or
spoken-fluency approval is claimed. Study the direct reflection at 10:49–11:00
with context before deciding whether it earns a concise complete edit.

Captions, all-word Difference, selective italics, music-free/unbranded defaults and
resource safeguards are unchanged. No new finished edit was made for this correction.
'''
(P / 'CHANNEL_FIT.md').write_text(report, encoding='utf-8')

# Keep regeneration from resurrecting rejected recommendations or unknown DOAC rights.
path = BASE / 'write_reports.py'
text = path.read_text(encoding='utf-8')
start = text.index(" 'The bank deliberately contains eight candidates")
end = text.index("','',", start) + len("','',")
text = text[:start] + " 'The initial bank contains eight screened leads. The owner rejected the offer-story proof for channel fit; it is archived UNSELECTED, not recommended for upload. Seven other leads remain unapproved. The posted-channel correction changes their research order; see review-v2/CHANNEL_FIT.md for primary examples, exact inspection limits and current ranking. Local word/frame evidence is not full listening. Provider review subsequently failed with HTTP 503 and then a bounded timeout; no automatic retries or paid fallback were used. None is production_ready.',''," + text[end:]
text = text.replace('No new clips have been delivered from this research. Original-source permission is unknown for these new episode selections and will be established before production, without transferring permission merely because a guest appeared on another approved show.',
    'A 30.36-second offer-story content proof was archived in Exports at the owner\u2019s request, explicitly UNSELECTED after rejection. No new upload-ready clip is approved. Owner permission is confirmed for DOAC episode QMzxNfX-uAg; other new-source permissions remain unknown. Permission never substitutes for channel fit.')
text = text.replace('Eight selected transcript leads; do not fill the bank to 20.', 'Eight screened leads, including one explicit owner rejection; do not fill the bank to 20. Primary channel-fit review and current study order: review-v2/CHANNEL_FIT.md.')
text = text.replace("{'A':0,'B':1,'revise_opening':2}", "{'study_channel_fit':0,'secondary_fit':1,'hold_fit':2,'rejected_owner_fit':3}")
text = text.replace('(A: study first; B: secondary; revise_opening: hold for revision).', '(study_channel_fit: inspect first, not approved; secondary_fit: conditional; hold_fit: no proof yet; rejected_owner_fit: archive only).')
needle = " if b.get('review_findings'):"
addition = " if b.get('channel_match_review'):out += ['**Posted-channel match:** '+b['channel_match_review']['reason'],'']\n"
if addition not in text:
    text = text.replace(needle, addition + needle)
path.write_text(text, encoding='utf-8')
print('Updated both banks, channel-fit report and report generator; no edit approved.')
