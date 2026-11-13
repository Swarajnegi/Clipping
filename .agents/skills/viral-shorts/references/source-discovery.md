# Find original footage from editing references

Use this workflow when the brief describes a taste or supplies edited references rather
than an original episode. The existing resource guard applies to media work; metadata-only
discovery and cloud-only review do not load local models or process frames.

## Reference evidence before search

Standing owner rule: the finished clips are for our own channel. References supply
content/music taste, discovery leads and editing/font inspiration, not production assets
or another channel's visual identity. Never carry their overlaid watermark, symbol,
handle or end card into exports. Also inspect the acquired original for baked-in publisher
branding; choose a clean authorized source or reframe cleanly. The default is no symbol
unless the owner supplies and approves their own. Preserve source provenance in records.

Study all supplied examples using the stage-routing reference-study procedure. Record file
hashes and inspection coverage. Distinguish editing targets from content/music examples.
Save actual quotes, visible account names, speakers, topics, emotional appeal, payoff and
music cues with timestamps. Label provider assessments, direct inspection and estimates.
Keep unknown songs unknown; a provider naming a track is a lead until corroborated.

For the November 2026 brief, both designated targets control style; all other examples
inform taste. Do not assume generic motivation, a particular political stance, or a fixed
creator ratio from the presence of a creator in the references.

## Discovery and acquisition

For current podcast selection, also read [moment selection](moment-selection.md).
Its five editorial checks and proof-before-polish workflow govern approval; discovery
signals, view outliers and replay heatmaps never override a failed editorial check.

1. Search distinctive quotes first, then speaker + topic or guest + episode. Reposts are
   leads for finding original uploads, not default production masters.
2. Seed Tate's Emergency Meeting/Tate Confidential on Rumble, official JRE distribution,
   and Chris Williamson's Modern Wisdom. Verify channels through creator-controlled links.
   Expand by matching content and delivery, not by fame alone. Search evergreen back catalogues.
3. Catalogue bounded episode metadata, chapters and reported subtitle languages. Example:
   `& $ClipPython scripts/discover.py $OriginalUrl --limit 25 --output Main/shorts-clips/Working/discovery/catalogue.json`.
   Multiple URLs are positional. Each listing is complete, limited, partial, blocked,
   unavailable or failed. Exit 2 means inspect partial results; never call it full coverage.
4. Review available caption text and surrounding context before downloading long videos.
   `none_reported` means metadata succeeded but reported no captions; `not_checked` on an
   error is not evidence that captions do not exist. Do not claim transcript inspection
   from a language list. Fetch caption bodies only for selected promising episodes.
5. Rank moments by reference fit, cold opening, standalone meaning, payoff and viable picture.
   Outlier views are supporting evidence, not proof of taste or future performance. Never
   fabricate numerical performance data or exact source timecodes from a repost alone.
6. Download shortlisted original sources through guarded prep. Use guarded CUDA transcription
   when captions are absent/unreliable. Inspect visuals and context before approving an edit.

Rumble has yt-dlp extractors, but test an episode and channel on this host. A failed listing
does not prove individual videos are inaccessible. On access denial, record the error and
use public creator links or owner-supplied originals; do not bypass authentication or paywalls.
Use one bounded request sequence with no automatic API retries or paid fallback.

## Catalogue and staging

`discover.py` records platform+video-ID keys, canonical URL, uploader/channel, title, date,
duration, chapters, full available description, caption-language availability, access status,
discovery provenance and unknown reuse permission. It stores no media or credential fields.
Its output is a dated snapshot, not an automatically refreshed service.

Pass the catalogue's `prep.work_id` as prep's `--work-id` argument. This namespaces new
staging folders by platform and video ID while preserving existing projects. Prep rejects
cached masters belonging to another source or masters whose provenance is missing. Record
the actual staging ID alongside the catalogue key; never reuse unrelated cached transcripts.

## Shortlist and production handoff

### Reference composition data

The owner's current default is `referenceEdit.profile: "editorial"`; read
[editorial captions](editorial-captions.md) for its font, motion and foreground-mask
schema. The following describes the retained legacy alternatives.

Optional per-clip `referenceEdit` selects `profile: "restrained"` or `"kinetic"`.
Both place the original video in a centred horizontal band on black. `bandHeight`
defaults to 608 output pixels; `captionY` defaults to 1000 and `captionSize` to 34
on the 1080×1920 output. These are starting settings, not measured original font metrics.
Restrained captions are small uppercase phrases. Kinetic captions allow timed emphasis:
`emphasis: [{t: 4.2, dur: 1.1, text: "100%", x: 600, y: 960, size: 84, italic: false}]`.
Times are assembled clip seconds, excluding an optional intro. Emphasis temporarily
replaces the base caption; choose text actually supported by the source speech.

For a legacy silver/italic treatment explicitly requested for a clip, set `palette: "silver"` and
`wordReveal: true`. Optional `layers` is a list of independently timed text elements:
`{t, dur, text, x, y, size, width?, font: "condensed"|"serif"|"sans", italic?, z?,
rotate?, wordTimes?}`. `wordTimes` contains one assembled-timeline entry per displayed
word. Use actual source word timestamps, keep related layers visible as a phrase builds,
and mix condensed keywords with selected italic connectors. Layers overlap one another;
this does not generate a foreground-person matte. Inspect typography and placement in
actual rendered frames before the batch. Keep the palette and choreography specific to
the owner's brief rather than applying them to unrelated projects.

When authored layers cover every spoken word, set `layeredOnly: true` in
`referenceEdit`. This keeps the standard caption page suppressed during gaps between
layers, so earlier words cannot flash again during an intentional pause. It requires
nonempty authored layers; the default remains the existing base-plus-emphasis behavior.

Optional `cutaways: [{file: "D:/.../cleared-master.mp4", start: 2, end: 3.2, t: 5}]`
prepares a source excerpt and overlays it inside the band at assembled second 5.
It is always muted; the original speaker's audio continues beneath it. The builder
normalises cutaway FPS to the main source. Record a reuse basis for each posting
deliverable. Keep drafts in `Working` and label completed private deliveries in
`Exports/02 Private Reviews`.
No anime or stock assets are automatically obtained. Existing styles remain available
when `referenceEdit` is omitted.
For paired exports, per-clip `sourceAudioDb` can attenuate the speech/effects master before
adding the bed (between -30 and 0 dB, default 0). Use measured audio peaks to choose it.
Packet hashes, packet counts and FPS must match; container start/duration rounding up to
1 ms is allowed and reported. One missing picture packet or changed content still fails QA.

Each candidate entry needs source URL, source start/end, surrounding context, matching reference/timestamps,
reason, source-verification status, visual inspection coverage and reuse basis. Unresolved
leads belong in a separate section and do not count as verified render-ready candidates.
If fewer than the current brief requests satisfy the evidence requirements, report the
real count and limiting cause. Do not fill a quota with weaker passages.

Keep the two target editing profiles distinct until inspection establishes common rules.
Choose exact cuts, shot framing, captions, pauses and beat cues from the actual source.
Avoid changing sentence meaning by joining unrelated statements. Avoid baking uncertainty
into executable clips.json: produce that file only with validated source timecodes/assets.

When requested, deliver mixed and music-free companions for Reels and YouTube Shorts.
The current owner default is music-free only. The music-free file
retains dialogue/effects and identical picture/timing. Keep production music separately
licensed and stored in `music`; reference audio is never the music asset. Identify desired
posting-app tracks and cue timing separately, subject to availability in the owner's account.
Check both platform overlays, source-embedded music, audio intelligibility, complete sentences,
captions/crops at all cuts, absence of foreign overlaid watermarks/symbols/handles/end cards,
and paired-export picture-hash/timing receipts when pairs are requested.
