"""Promote technically validated edits, with posting copy and explicit review coverage."""
import hashlib
import json
import shutil
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
destination=ROOT/'Main/shorts-clips/Exports/03 Archive/2026-11-08 - First Thought Palace Batch - Unselected'
validated=json.loads((P/'qa/final-validation.json').read_text())
assert len(validated)==5 and all(not r['caption_face_intersections'] and r['all_word_difference'] and r['decode']['complete'] for r in validated)
batch=json.loads((P/'batch.json').read_text())
assert batch['permission']['confirmed']
posting={
'01-actions-not-thoughts':('You Are More Than Your Worst Thought',
    'A difficult thought is not your character. Give yourself credit for the actions you choose.',
    '#ThoughtPalace #SelfWorth #PersonalGrowth #ChrisWilliamson'),
'02-permission-to-change':('You Are Allowed to Outgrow the Plan',
    'The years were not wasted. They helped you understand what mattered then—and what matters now.',
    '#ThoughtPalace #LifeChoices #PersonalGrowth #AlexHormozi'),
'03-hiding-your-real-self':('Being Accepted Is Not the Same as Being Known',
    'Being liked can still feel lonely when you are hiding yourself. Leave room for the real you.',
    '#ThoughtPalace #Authenticity #SelfWorth #ChrisWilliamson'),
'04-choose-your-regret':('Choose the Regret You Can Live With',
    'Avoiding a decision has a cost too. Choose the discomfort that leaves room for the life you want.',
    '#ThoughtPalace #Decisions #SelfGrowth #Mindset'),
'05-keep-your-own-promises':('Build Confidence You Can Trust',
    'Keep one small promise to yourself today. Let your actions give you a reason to trust yourself.',
    '#ThoughtPalace #Confidence #SelfTrust #JimmyCarr')}
related={
    '01-actions-not-thoughts':('Your Children Will Know Who You Really Are','gPXNhU9t848'),
    '02-permission-to-change':('Whose Dream Are You Actually Chasing?','RUlpjXk9Y-o'),
    '03-hiding-your-real-self':('Whose Dream Are You Actually Chasing?','RUlpjXk9Y-o'),
    '04-choose-your-regret':("The REAL Reason You're Stressed",'nD6p-qYd728'),
    '05-keep-your-own-promises':('Give Yourself the Chance to Find Out','EdMJXSF8-xw')}

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

destination.mkdir(parents=True,exist_ok=True)
manifest=[]
notes=['# thought.palace — five Shorts, 8 November 2026','',
    '2160×3840 vertical delivery; rounded-square picture; native source FPS; all-word Difference captions and selective true italics. No added music, narration or channel symbol. Original procedural camera clicks are included quietly on 01,03,05 at the owner’s request.','',
    '**Review coverage:** Full decoding, every-frame automated face/caption checks, full local CUDA ASR and audio-packet preservation checks passed. Representative rendered frames and phrase sheets were visually inspected. The bounded cloud audiovisual reviewer timed out; independent continuous listening was not completed. Give each file a final phone playback with sound before posting. Technical checks are not a guarantee of engagement or editorial acceptance.','',
    'The owner confirmed permission for all four source episodes. This batch continues as agreed; subsequent discovery prioritises shows and speakers beyond Chris Williamson / Modern Wisdom.','']
for result in validated:
    id=result['id']
    file=id+'-music-free.mp4'
    source=P/'finished'/file
    target=destination/file
    if target.exists():raise FileExistsError('Preserve previous delivery revision: '+str(target))
    shutil.copy2(source,target)
    sha=digest(source)
    assert digest(target)==sha
    origin=json.loads((P/'sources'/(id+'-source.json')).read_text())
    edit=json.loads((P/'drafts'/(id+'-edit.json')).read_text())
    title,caption,tags=posting[id]
    next_title,next_id=related[id]
    notes += [f'## {id} — {result["duration"]:.2f}s','',f'**File:** `{file}`',
        f'**Title:** {title}','',caption,'',tags,'',
        f'**Speaker:** {edit["speaker"]}. **Original:** {origin["canonical_url"]}',
        f'**Opening:** {edit["opening"]}',f'**Payoff:** {edit["payoff"]}',
        f'**Source resolution:** {origin["actual"]["downloaded_width"]}×{origin["actual"]["downloaded_height"]}; export FPS {result["fps"]:.8g}.',
        'For wider 3840×1920 originals, the square retains up to 1920×1920 before the subtle punch; the delivered picture window is 1960×1960 within a 2160×3840 canvas. 3840×2160 originals retain up to 2160×2160 before framing. Output size does not imply recovered camera detail.','',
        f'**Optional next watch on our channel:** [{next_title}](https://www.youtube.com/shorts/{next_id}). Use Related Video if available; this clip already supplies its own payoff.','']
    manifest.append({'id':id,'file':str(target),'sha256':sha,'duration':result['duration'],
        'fps':result['fps'],'frames':result['frames'],'source_url':origin['canonical_url'],
        'source_quality':origin['actual'],'reuse_basis':batch['permission'],
        'source_context_requested':origin['requested_context'],
        'local_source_pieces':[[a,b] for a,b,off in edit['spans']], 'assembled_spans':edit['spans'],
        'meaning_and_reordering':edit['meaning'],'qa':str(P/'qa'/(id+'-full-qa.json')),
        'status':'Technically validated delivery; owner selection and continuous phone listening outstanding.'})
(destination/'POSTING_COPY.md').write_text('\n'.join(notes),encoding='utf-8')
(destination/'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(destination/'QA_COVERAGE.md').write_text(
    '# QA coverage\n\nFull local QA records and phrase sheets: '+str(P/'qa')+
    '\n\nAll final frames decoded; native FPS and expected frame counts checked. Every frame received an automated face/caption intersection check. '
    'Face-detection gaps and ASR similarities are retained per clip; detection is not proof of recognising every face. '
    'Every caption word uses white Difference and bundled licensed fonts. First-three-second and phrase samples were inspected. '
    'Final audio packet payloads/timestamps equal the intentionally leveled dialogue/SFX master. '
    'No full independent continuous listening certification: the sole bounded Gemini review attempt timed out. '
    'Owner phone review with sound remains necessary. No private retention or guaranteed-viral claim.\n',encoding='utf-8')
shutil.copy2(P/'assets/provenance.json',destination/'SFX_PROVENANCE.json')
(P/'delivery.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Delivered five hash-verified files to',destination)
