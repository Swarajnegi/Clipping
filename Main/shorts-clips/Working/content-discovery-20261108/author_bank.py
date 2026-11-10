"""Assistant-authored discovery decisions. Caption cue bounds are not frame-final edits."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from moment_research import read,save,validate_bank
C=read(P/'catalogue.json');E={e['video_id']:e for e in C['episodes']}
if (P/'candidate-bank.json').exists():raise FileExistsError('Preserve the reviewed bank; author a new revision instead of resetting its review findings.')
items=[
 ('01-cost-of-saying-no','QMzxNfX-uAg',[[6136.08,6183.1]],'This offer comes in for this action comedy',
 'The $14.5 million test of a decision',
 'McConaughey had stopped accepting familiar roles and feared his Hollywood career was over. The escalating offers test whether that decision is real.',
 'The higher price makes the same script feel better, but he still declines.',
 'Start at the action-comedy offer; retain the 8/10/12/14.5 million escalation, the second reading joke and the final no. End before his unproven theory about Hollywood reacting.',
 'eMnyT7e1F_8 — concrete stakes, escalation and personal choice',
 ['Align exact word onsets; opening cue contains the preceding word Hollywood.','Do not imply every viewer can afford to reject work.','This is DOAC; existing Modern Wisdom permission is not transferred.']),
 ('02-dads-unexpected-answer','QMzxNfX-uAg',[[1643.36,1648.72],[1682.16,1749.36]],"my dad's paying for school",
 'He expected his father to say no',
 'He wants to leave the expected law-school route for film school. His father pays for school; he anticipates opposition before the call.',
 'His father gives support through a blunt demand to commit fully.',
 'Use the paying-for-school stakes, then the call and feared response. Keep the meaningful pauses before the answer. Stop after the encouragement to own the choice, before the longer explanation.',
 'eMnyT7e1F_8 — feared rejection becomes reassurance; personal story instead of a general lesson',
 ['Two source spans; verify a natural join.','Keep father quotation intact; do not remove the uncertainty before the answer.','Profanity and the dramatic pause need listening.']),
 ('03-winning-someone-elses-game','M4PzOjM5BJQ',[[3952.84,3969.84],[3983.72,3998.5]],
 'the main point there was that I wanted',
 'He out-earned his father—and questioned the game',
 'Hormozi describes years trying to prove himself to his father. Earlier he describes an apology and his own regret about reacting badly; the relationship is not presented as wholly hostile.',
 'Winning his father’s status game makes him ask whether he chose that game himself.',
 'Tighten the connective opening to the genuine line about wanting to make as much as his father; retain the increasing ambition and final question. Omit the intervening cultural generalisation, not the admission that it was his own goal.',
 'z7URpe7QlCQ — a personal reversal challenges achievement-as-happiness',
 ['Opening needs word-level tightening before approval; no invented I-beat-my-dad quote.','Preserve personal responsibility and avoid an anti-parent message.','This excerpt is from a different Hormozi episode than the benchmark friend clip.']),
 ('04-choose-your-regret','M4PzOjM5BJQ',[[2111.96,2159.8]],'regrets are inevitable',
 'The regret of leaving versus the regret of staying',
 'The speakers are discussing hard decisions, not promising that resigning is always correct. They compare an uncomfortable conversation with years in a hated job.',
 'Avoiding a painful conversation also creates a regret; choose which cost you can live with.',
 'Bring the genuine question which regret could I live with forward if the opening needs it. Keep both alternatives in the job example and the choose-your-regrets conclusion. Omit the later fear-engine explanation.',
 'Owner’s preferred 13 seconds of Peterson clip 04 — a sharp decision insight with a concrete cost',
 ['Source wording has a restarted sentence; hearing determines whether it can be tightened fluently.','Do not turn a decision frame into financial advice to quit.']),
 ('05-married-to-different-people','xNwYaTf7Zn8',[[871.92,883.92],[866.8,871.92],[887.76,936]],
 "I've been married to three or four different women all with her name",
 'The same marriage, different people',
 'Hudson says he has been married to the same wife for 27 years; he means that both people change. He describes how fear of losing her can make him abandon his principles.',
 'He describes feeling the feared loss, then showing up honestly so both partners can decide how to be together.',
 'Lead with the different-women/same-name line, immediately restore the 27-year same-wife context, then the difficulty and response. Keep his wife’s equal agency. End before the death-visualisation tangent.',
 '2uzoCtRc0gQ — surprising relationship detail earns its clarifying answer',
 ['Ranges deliberately reorder the opening; align word onsets and avoid duplicated clauses.','This is his personal process, not a universal prescription for unsafe relationships.','Do not imply infidelity, multiple actual wives or that the marriage ended.']),
 ('06-not-a-bucket-list','TJZVvgNPg_E',[[2706.16,2736.24]],"I've always hated the idea of a bucket list",
 'I am not dead: choosing life after diagnosis',
 'Moody is discussing a serious diagnosis and his wife Annie’s support. He rejects a bucket-list framing and describes her alternative phrase.',
 'A darkly humorous change in wording gives him a sense of choosing life rather than waiting for death.',
 'Keep diagnosis context, his rejection, his wife’s alternative and the line about looking at life differently. Stop before the unfinished list of destinations.',
 'c2Q1h3I8GxM — difficult family experience with a humane comic release',
 ['Strong language is integral; decide treatment with the production brief.','Handle the diagnosis respectfully; no recovery or medical efficacy claim.','Opening starts after an um at the subtitle cue; align from audio.']),
 ('07-i-think-im-lonely','rR_14L2RI2A',[[4690,4725.64]],"I've got in my journal on my phone",
 'The journal entry behind the public persona',
 'Asked about loneliness, Williamson describes repeated journal entries in his twenties despite working around people in nightclubs. He recognises he was not showing his true interests.',
 'Being around people did not ensure connection when he hid the person he actually was.',
 'Start at the journal disclosure, preserve the short lonely entry and his own responsibility; keep the nightclub/aliens contrast if it flows. End at not putting that version of himself out there.',
 'eIsIpzQkp3c — specific vulnerability rather than abstract advice',
 ['Fermi is mistranscribed fmy; verify sound before captioning.','Do not caption this as a clinical diagnosis or a universal cause of loneliness.','Shorten the initial connective words at actual speech boundaries.']),
 ('08-childhood-on-the-road','NaC2aFh4s90',[[519.2,575.5]],'We lived out of the car',
 'The childhood he left—and the road he chose',
 'Caleb Followill describes travelling with his preacher father and brothers. Making friends meant leaving them; the brothers had one another.',
 'He recognises that he later chose a career that kept him on the road.',
 'Keep the lived-out-of-the-car opening, losing friends, brothers staying together and the career reversal. Remove conversational repetitions only where audio joins naturally; no arbitrary time target.',
 'eMnyT7e1F_8 — personal circumstance, emotional cost, then a changed perspective',
 ['Delivery contains hesitations; this is lower priority until heard.','Do not romanticise poverty or imply no hardship because he says it was good.','This is a reflective reserve, not assumed to outperform a punchier story.'])]
bank=[]
for id,video,segments,opening,title,context,payoff,cut,benchmark,risks in items:
 e=E[video];record=read(P/'transcripts'/('youtube_'+video+'.json'))
 excerpt=[s for s in record['segments'] if any(s['end']>a-20 and s['start']<b+20 for a,b in segments)]
 item=dict(id=id,title=title,source_key=e['key'],source_url=e['canonical_url'],source_title=e['title'],source_family=e['source_family'],
  source_verification=e['source_verification'],segments=segments,approximate_duration=sum(b-a for a,b in segments),
  boundary_precision='published caption cues; word/frame alignment still required',opening=opening,context=context,payoff=payoff,cut_proposal=cut,benchmark=benchmark,risks=risks,
  checks=dict(opening='pending' if id.startswith(('03','04','07')) else 'pass',progression='pass',delivery='pending',payoff='pass',channel_fit='pass'),
  status='transcript_shortlist',reuse_basis='unknown',av_review={'audio':False,'full_passage':False,'method':None,'evidence':None},context_transcript=excerpt)
 bank.append(item)
errors=validate_bank(bank,C,[read(p) for p in (P/'transcripts').glob('*.json')]);assert not errors,errors
save(P/'candidate-bank.json',bank)
print('AUTHORED',len(bank),'transcript candidates; none falsely approved for production')
