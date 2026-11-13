# Dialogue-led movie cutaways

For thought.palace, begin scouting only after the owner approves the source
passage. Follow the [B-roll brief and shot-choice step](owner-led-edit.md#2-send-the-b-roll-brief-and-wait-for-shot-choices).
Give a placement count, library coverage and the number of distinct new
excerpts to source. Wait for the owner's choices before confirming music.

Scout film or TV cutaways for each edit and let the full beat map determine the
count. For a 19–35s edit, try connected runs of 0.5–1.5s shots
where the speech and action move quickly. A 10–15s edit can work with around
three strong inserts. Give any action that needs more screen time room to read.
Keep the speaker visible where their delivery or reaction carries more meaning.
Keep the approved passage and speech timing intact for a picture-only revision.

Scout a visual match for each substantial spoken beat, including later turns
that could otherwise stay on the same speaker shot for several seconds. Give
recognizable film and TV moments more screen time where their action clarifies
the speaker's point. A reaction, attempt, setback and recovery can each warrant
a different shot. Retain the speaker's personal delivery and conclusion where
they carry more weight. Count useful visual beats and keep the soundtrack
continuous across the cuts.

## New pack intake and handoff

On an applicable request, check for newly added full-length videos directly under
`Main/shorts-clips/Movie Clips`, on `E:\Clipping\Movie Clips` when mounted, or at
the path supplied in the brief. Wait for downloads to complete and skip partial
files. Identify each pack independently from its filename and media metadata.
Check the existing catalogues for the same pack before extracting again. An absent
original for an already catalogued title is expected after owner cleanup.

Study the new pack across its timeline and choose a varied set of usable cinematic
and everyday moments. Save **5–10 seconds of usable source footage per library
excerpt**, with a complete action or reaction and trim room before and after it
where the source allows. A coherent sequence can include adjacent angles if
they build the same action. Keep an especially useful detail shorter only if
the surrounding scene offers no suitable trim room. Label it as a short detail
and record the reason. Keep any 1–2 second project trims in `Working/<project-id>`.

Save independent, silent video files in `Movie Clips/<title>` at the source
aspect ratio, dimensions and frame rate. The files must remain usable after the
full-length pack is removed. Keep pack identity, the original filename and size,
source-relative start and end, actual duration, review coverage and reuse status
in the title's catalogue. When the action is inside a longer excerpt, note the
key action's offset so the editor can find it quickly. Use distinct source
records if a title has multiple packs. Add an
`editorial` entry to each excerpt during intake. Describe visible action, assign
supported dialogue cues from `scripts/movie_library.py`, and record mood,
framing, possible use and the evidence actually inspected. Use
`evidence.status: "unresolved"` when the picture is unclear.

Before handing off, fully decode each saved excerpt and verify its actual
duration, dimensions, frame rate and silence. Check the start and end in the
saved picture for trim room and the intended action. Reconcile the catalogue
and library index with the files on disk. Report the number of 5–10 second
excerpts, any short details with their reasons, the location and review
coverage. Flag unfinished or unexpectedly short extracts while the source is
available. The owner removes the original when satisfied.

For older short excerpts, first check for an existing longer file that
contains the same source range. If the original is available, save a longer
version with a separate catalogue ID and record the match. Keep the existing
asset and offsets usable for past edits. If the surrounding frames are
missing, keep the short excerpt and mark the longer version as needing a
source. Preserve real frame order and timing.

## Choose from the library

- Start at `Main/shorts-clips/Movie Clips/README.md`. Each title has a
  `CATALOGUE.md` for browsing and a `catalogue.json` with source offsets and review
  coverage. Search by what the picture should communicate and start with
  enough source duration to trim. For example, run
  `& $ClipPython scripts/movie_library.py search "trying again after failure" --min-duration 5 --limit 12`.
  This reads only catalogue metadata. Use `--cue` for a specific cue and
  `--json` for the asset ID, source offsets and detailed review record.
- Compare the strongest cue matches across film and series families before
  returning to a familiar title. Both Peaky Blinders packs are one family. Pass
  `--shot-map` for recent approved or reviewed versions, latest first, and
  `--used-title` for each insert already selected in the current batch.
  Usage breaks ties after cue and wording fit. The action, mood and framing
  must suit the exact line at the cut. A single title can carry a deliberate
  sequence when its shots build on one another. Use the separate anime library
  when the brief calls for it.
- Check motion and surrounding context before locking the excerpt. A representative
  frame suggests a candidate. The full intended interval establishes whether the
  action, framing and emotion fit the line. Check the final crop at phone size
  and normal speed. Describe the visible action or readable reaction in one
  sentence and name the exact words it serves. If the crop hides the subject or
  the intended action, reframe or reject it. Keep object details, backs and
  establishing shots only when the action or story beat reads without knowing the
  movie. Hold on the speaker when a proposed insert fails either check.
  Record what was actually reviewed.
- Test the sequence's implied story before rendering and after final framing.
  Summarize the clip's human point in one sentence. For each insert, name what
  the viewer sees, the spoken phrase it serves, and the emotion or motive it
  implies. Follow the sequence at normal speed with the audio off, then
  compare it with the dialogue and the promised payoff. A courtroom may show
  judgment, but several polished workplace shots can make a self-worth clip
  feel like a story about professional approval. A held expression, personal
  action or ordinary relationship may carry the actual idea. When the speaker
  sets up a belief and then challenges it, confine the illustrative shot to the
  side it depicts and check that it ends at the turn. Do this check before asking
  the owner to review. State the coverage if playback is unavailable.
- Reuse an existing excerpt when it covers the action. When a new excerpt is useful,
  keep it under `Movie Clips/<title>` at its original aspect ratio, resolution and FPS
  with audio removed. Follow the intake checks and avoid overlapping duplicates.
  If the pack is gone, an unextracted moment requires the original again.
- Verify a recorded reuse basis for each film/TV source before including it in a
  posting deliverable. Locally supplied packs with unresolved reuse may be used for
  owner-authorized private tests in `Working`. Record their status there.

## Edit and review

1. Open on the speaker when their delivery establishes the hook. Bring in a
   cutaway on the spoken cue it illustrates. Hold the speaker when their
   delivery carries the line, and reframe on actual camera changes.
   A source reaction/angle or caption reveal can supply the first change.
   Return to the speaker on a personal pivot, reaction or conclusion.
2. Map each distinct spoken beat through the example, reversal and payoff.
   Frame-step reference cuts so short inserts do not go missing between
   samples. Give each beat a shot, hold or graphic, and note deliberate
   departures. Group cutaways into short runs
   that develop one idea, such as effort → strain → reset. Enter on the phrase
   that makes the sequence legible. Use detail, action, consequence and reaction
   shots as the line develops. Hold a reaction or action until it reads.
   Compare the [two owner references](transitions.md#the-two-11-november-edits).
   Prefer hard cuts and reserve [transition pairs](transitions.md)
   for accents. Record the exact spoken cue, assembled frame range, source in/out
   or offset and duration, intended visible action, crop and
   `library_asset_id` from search for each insert. Keep `title` on the shot-map
   entry so the next edit can count title use. Preserve important faces, reactions and action in the rounded-square
   crop, or use horizontal framing when the brief and passage suit it. Keep inserts
   silent beneath continuous original dialogue.
3. After the source speech, B-roll, any chosen song timing, cuts, transitions and SFX
   are decided and picture is locked, follow [editorial captions](editorial-captions.md)
   as the final editing step. Compose for the shot or
   phrase using centre or open space, keep words stable during their reveal, and
   emphasize a few meaningful words through larger type, weight or occasional
   italic. Follow the caption guide for white Difference and explicit exceptions.
   Check bright and moving areas and
   clean up any caption fade that lingers across a picture cut.
4. Use the existing [cutaway builder interface](source-discovery.md#reference-composition-data)
   for simple inserts. For a shot-specific crop, stage a silent, pre-framed derivative
   under the project and use the existing Remotion cutaway layer. Keep the library
   master in its original framing and conform only the staged insert to the edit FPS.
   Use the mandatory resource guard for media processing and rendering.
5. Check the opening three seconds, frames on both sides of every insert boundary,
   the actual action at the chosen source offset, caption onsets and
   emphasized beats at phone size. Review the full edit with sound and record
   the actual coverage. For a picture-only revision, stream-copy the approved
   audio and compare packet payloads and timestamps. When adding SFX, verify
   speech timing and clarity in the new mix. Complete the decode and check
   the intended frame count and native edit clock before delivery.

The Goggins test under `Working/movie-cutaway-test-20261109` is a worked example.
Its `SHOT-MAP.md` pairs Tyler's pause after a fight with learning failure, Jon's
training counter with the turn toward victory, and Tony's unstable flight test with
trial and adjustment. The two WhatsApp style references from 9 November are documented
there with sampled timestamps and inspection limits.
