# Podcast discovery and editorial selection

Read before source selection and before authoring final caption layers. Owner-specific
taste and corrections live in `EDITORIAL_TASTE.md`; the current brief wins.

## Discover broadly, inspect selectively

Use both routes: successful Shorts traced to original episodes, and overlooked original
transcript passages. Reposts are discovery leads. Verify canonical source identity and
surrounding context; a description or quoted repost timestamp alone is not verification.
Search for recognisable situations and distinctive phrases, not only topic nouns or fame.
Include evergreen catalogues. A show may supply no qualifying moments.

Use bounded `scripts/discover.py` catalogues (metadata only). `scripts/moment_research.py`
indexes selected timestamped transcripts for reuse without models or video downloads.
Prefer published captions; record unavailable/blocked/failed retrieval separately from
successful metadata reporting no captions. Heavy transcription or video inspection uses
the existing guard. Permission remains a separate production gate.

Metadata/caption commands (bind these paths to the current project under Working):

```powershell
& $ClipPython scripts/moment_research.py fetch --catalogue $Catalogue --keys youtube:VIDEO_ID --output $TranscriptDirectory
& $ClipPython scripts/moment_research.py index --catalogue $Catalogue --transcripts $TranscriptDirectory --database $Database
& $ClipPython scripts/moment_research.py search --database $Database --query 'lost everything' --phrase --context 30 --output $SearchResults
& $ClipPython scripts/moment_research.py validate --catalogue $Catalogue --transcripts $TranscriptDirectory --bank $CandidateBank
```

Fetch at most 20 deliberately selected episodes per invocation. Successful and failed
attempts are cached with source identity; do not repeatedly retry a failed source.
The index can be rebuilt from saved transcript records. No API keys or signed caption
URLs are stored. Search provides leads and context, never automatic cut approval.

## Five editorial checks

For every proposed moment record evidence for:

1. **Opening:** Exact spoken opening and why a stranger would stay. A title or caption
   cannot rescue weak speech. Check whether pronouns or assumptions need missing context.
2. **Progression:** Identify the developing example, revelation, disagreement, escalating
   story or emotional turn. Reject an unchanging sequence of familiar assertions.
3. **Delivery:** Check the whole passage/proof with sound for tangled speech, unnecessary
   repetition and natural rhythm. Transcript-only fluency is provisional.
4. **Payoff:** Identify the complete, specific thought or emotional resolution and where
   the clip should stop. Reject a promised answer that never arrives.
5. **Channel fit:** State why this audience would care or share it and its relation to
   the owner's confirmed taste. A generic positive message is insufficient evidence.

Use `pass`, `reject` or `pending`; scores cannot override a failed check. Distinguish
`transcript_shortlist`, `reviewed` and `production_ready`. Full audiovisual review and a
recorded reuse basis are needed for production_ready. Retain exact reviewer, method,
coverage and source identity; an unavailable provider is not a completed second opinion.

Useful format hypotheses: story with a reversal; familiar struggle with an unexpected
explanation; revealing question/answer; sharp conversational exchange; compact insight
with a concrete example. These are leads to test, not guaranteed viral templates.

## Cut and proof before polishing

For each candidate preserve source URL/key, surrounding context, source ranges, exact
opening, payoff, editorial cut proposal, benchmark match, risks and inspection gaps.
Remove redundant setup, abandoned sentences and repeated agreement. Keep meaningful
breaths, reactions and pauses. Do not automatically delete every gap over 0.35 seconds.
When the brief permits, move a genuine later line forward, retaining logical context
and attribution. Never splice statements into a new claim or fabricate speaker quotes.

Create an inexpensive full-length editorial proof before expensive 4K caption finishing.
Judge the whole listening experience, not only the opening or technical quality. Every
extra sentence must add interest or necessary meaning. Stop when the thought lands; a
complete 13-second moment does not need padding. No fixed per-episode yield or daily quota.
Keep the current caption treatment and all media guard requirements intact.

## Benchmarks and the learning loop

Record public views, dates, runtime and observation time; distinguish indexed snapshots
from live metadata. Compare weaker examples too, preferably same channel, format and
similar publication age. Missing view counts are unknown, not zero. Do not infer retention,
rewatches or causality from public reach. Replay heatmaps and model ratings supply leads.

Deliver complete Shorts around recurring viewer concerns. Suggest a related upload on
our own channel in posting notes; YouTube's Related Video needs advanced feature access.
Avoid forced cliffhangers, unnecessary end cards or an invented channel mark.

`results.py add --avd` remains a legacy percentage alias. Use
`--avg-view-duration-seconds` for seconds and `--average-percentage-viewed` for percentages.
Use `selection` to log owner acceptance/rejection and actual production minutes separately.
Compare audience snapshots at similar elapsed hours; do not collapse 24h and 7d results.
Owner acceptance and production minutes per accepted clip measure editorial yield.
Returning-viewer changes are longer-term loyalty evidence, not direct binge-session proof.

## Source guidance

- [YouTube Shorts recommendations](https://support.google.com/youtube/answer/11914225?co=YOUTUBE._YTVideoType%3Dshorts&hl=en): no favoured format or minimum posting cadence; viewer choice, duration, percentage viewed and satisfaction matter.
- [YouTube's Shorts discussion](https://blog.youtube/creator-and-artist-stories/youtube-shorts-deep-dive/): immediate interest and compact stories; creator advice, not a guarantee.
- [Anthony Smith interview](https://becauseofmarketing.com/anthony-smith-the-diary-of-a-ceo/): choose impactful moments and build an emotional story. Trailer mystery does not excuse an incomplete Short.
- [Related Video documentation](https://support.google.com/youtube/answer/14075157?hl=en) and [audience guidance](https://support.google.com/youtube/answer/10246996?hl=en).

Owner's dated benchmark study: `Main/shorts-clips/Working/content-discovery-20261108`.
