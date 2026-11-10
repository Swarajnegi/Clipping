# Dialogue-led movie cutaways

Include film or TV cutaways in every new edit and aim for around six or seven
inserts per clip. Use the spoken beats and runtime to choose the final count.
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
`Main/shorts-clips/Movie Clips`. Wait for downloads to complete and skip partial
files. Identify each pack independently from its filename and media metadata.
Check the existing catalogues for the same pack before extracting again. An absent
original for an already catalogued title is expected after owner cleanup.

Study the new pack across its timeline and choose a varied set of usable cinematic
and everyday moments. Cut around complete actions, reactions or short visual
beats. Save independent, silent video files in `Movie Clips/<title>` at the source
aspect ratio, dimensions and frame rate. The files must remain usable after the
full-length pack is removed. Keep pack identity, the original filename and size,
source-relative timecodes, review coverage and reuse status in the title's
catalogue. Use distinct source records if a title has multiple packs. Add an
`editorial` entry to each excerpt during intake. Describe visible action, assign
supported dialogue cues from `scripts/movie_library.py`, and record mood,
framing, possible use and the evidence actually inspected. Use
`evidence.status: "unresolved"` when the picture is unclear.

Before handing off, fully decode each saved excerpt, verify its dimensions,
frame rate and silence, and reconcile both catalogue entries and the library index
with the files on disk. Report the count, location and inspection coverage.
Flag any failed or unfinished ranges while their source is still available.
The owner removes the original when satisfied. Preserve the excerpts and
catalogues, and use them directly once the full-length file is gone.

## Choose from the library

- Start at `Main/shorts-clips/Movie Clips/README.md`. Each title has a
  `CATALOGUE.md` for browsing and a `catalogue.json` with source offsets and review
  coverage. Search by what the picture should communicate. For example, run
  `& $ClipPython scripts/movie_library.py search "trying again after failure" --min-duration 2 --limit 12`.
  This reads only catalogue metadata. Use `--cue` for a specific cue and
  `--json` for the asset ID, source offsets and detailed review record.
- Compare the strongest cue matches across film and series families before
  returning to a familiar title. Both Peaky Blinders packs are one family. Pass
  `--shot-map` for recent approved or reviewed versions, latest first, and
  `--used-title` for each insert already selected in the current batch.
  Usage breaks ties after cue and wording fit. The action, mood and framing
  must suit the exact line at the cut. A single title can carry a deliberate
  sequence when its shots build on one another. For the current owner brief, skip anime.
- Check motion and surrounding context before locking the excerpt. A representative
  frame suggests a candidate. The full intended interval establishes whether the
  action, framing and emotion fit the line. Record what was actually reviewed.
- Reuse an existing excerpt when it covers the action. When a new excerpt is useful,
  keep it under `Movie Clips/<title>` at its original aspect ratio, resolution and FPS
  with audio removed. Follow the intake checks and avoid overlapping duplicates.
  If the pack is gone, an unextracted moment requires the original again.
- Verify a recorded reuse basis for each film/TV source before including it in a
  posting deliverable. Locally supplied packs with unresolved reuse may be used for
  owner-authorized private tests in `Working`. Record their status there.

## Edit and review

1. Open on the speaker and let their actual first line establish the hook. Bring
   in a cutaway on the earliest natural spoken cue, ideally within the first
   three seconds. Use a small reframe or typographic emphasis for the opening
   change when the speaker should stay visible. Return to the speaker for personal
   testimony or the closing thought when their performance serves the payoff.
2. Record the exact spoken cue, assembled frame range, source offset, crop and
   `library_asset_id` from search for each insert. Keep `title` on the shot-map
   entry so the next edit can count title use. Preserve important faces, reactions and action in the rounded-square
   crop, or use horizontal framing when the brief and passage suit it. Keep inserts
   silent beneath continuous original dialogue.
3. Follow [editorial captions](editorial-captions.md). Compose for the shot or
   phrase using centre or open space, keep words stable during their reveal, and
   emphasize a few meaningful words through larger type, weight or occasional
   italic. Keep white Difference on every word. Check bright and moving areas and
   clean up any caption fade that lingers across a picture cut.
4. Use the existing [cutaway builder interface](source-discovery.md#reference-composition-data)
   for simple inserts. For a shot-specific crop, stage a silent, pre-framed derivative
   under the project and use the existing Remotion cutaway layer. Keep the library
   master in its original framing and conform only the staged insert to the edit FPS.
   Use the mandatory resource guard for media processing and rendering.
5. Check the opening three seconds, insert entries and exits, caption onsets and
   emphasized beats at phone size. Review the full edit with sound and record
   the actual coverage. For an unchanged dialogue timeline, stream-copy the approved
   audio and compare packet payloads and timestamps. Complete the decode and check
   the intended frame count and native edit clock before delivery.

The Goggins test under `Working/movie-cutaway-test-20261109` is a worked example.
Its `SHOT-MAP.md` pairs Tyler's pause after a fight with learning failure, Jon's
training counter with the turn toward victory, and Tony's unstable flight test with
trial and adjustment. The two WhatsApp style references from 9 November are documented
there with sampled timestamps and inspection limits.
