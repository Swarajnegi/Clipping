# Whole-clip pacing and transition pairs

## The two 11 November edits

- **19.25s horizontal:** The first movie shot lands at 1.97s. Eight hard-cut
  inserts through 8.80s develop the cost of overwork. The wide speaker beat
  “so for me” separates that warning from a four-shot recovery sequence. The
  9.70–11.67s rest shot and 13.17–15.00s straightening action take longer to
  read. A stable frontal close-up carries the ending from 15.90s. The first
  film entry shows a direct picture cut. Inversion Flicker and a separate sound
  at that entry remain unverified.
- **34.99s square:** A guest-to-host cut at 0.43s uses different source coverage.
  Film takes over at 1.70s on the work lead-in. Hard-cut phone, paperwork and
  office shots make an idea concrete. The drummer sequence at 16.77–19.40s
  briefly accelerates on the repeated action. Flash/attack pairs in that run
  sit near 17.77, 18.10, 18.50 and 18.83s. A repeated accent links two flashes
  in that run to the white “against” card at 27.97s. Another short accent is
  repeated on both “relentless obsession” panel entries. The host's profile
  then holds about 3.1s before the frontal “Do the work.” The cut to black
  aligns with an attack recurring on the music grid. Exact effect names and
  stems are unresolved. These findings come from frame-level evidence, word
  timing and waveform comparisons.

Full cut and sound maps are in
`Main/shorts-clips/Working/reference-analysis/dialogue-cuts-20261111/REVIEW.md`.
The references demonstrate dialogue-led shot runs, meaningful speaker returns
and contrast between busy passages and quiet holds. Keep source framing stable
through those holds. Match their editorial purpose and follow the flash limits
below when adapting the technique.

The 10.05s tutorial labels four pairs. Frames and waveform were inspected, and
the exact recordings and dialogue mix were not independently heard. Presets are
original recreations with separately sourced substitute sounds.

| Tutorial time | Labelled effect and sound | Preset | Sound ID |
| --- | --- | --- | --- |
| 2.23–2.43s | Inversion Flicker / Data analysis (Killy) | `inversion-flicker` | `small-electric-glitch` |
| 4.70–5.03s | BW Inverted Shock / Glitch sound logo (YBMD) | `bw-inverted-shock` | `glitch-static` |
| 7.23–7.50s | Blu-ray Scanning / Unpleasant whoosh (new_field) | `blu-ray-scanning` | `digital-sweep-effect` |
| Around 9.90s | Retro Exposure / Single-lens reflex shutter (Satoru Saito) | `retro-exposure` | `camera-shutter-click` |

## Author and review

Use hard cuts for routine shot changes. Choose the sound for the thing the
viewer sees or the phrase that changes the meaning. A visible hit can earn an
action-synchronous accent, a reveal can earn a short anticipatory lead-in, and
a deliberate text card can earn one accent on entry. Leave room for speech and
for the strongest music hit when it already does the job. Record the spoken cue,
the outgoing and incoming shot, cut frame, sound accent time, effect, sound and
reason in the project's beat map. Review sound effects, dialogue and music
together on the intended playback mix. Use the four presets as options.

For a spoken pivot that deserves a graphic, use the Cavill “and lastly”
sequence as a model. A single camera-capture flash and synced shutter mark
the turn from the dark embrace. A clean white card with a short black phrase
holds long enough to read. The next shot carries the concluding thought.
Separate the flash frame from the readable hold, and end the outgoing speech
caption and fade before the flash. Check the frame before the flash, the
flash itself, the first legible card frame and the first frame after the card.
Keep the shutter audible without masking the pivot. Use this treatment where
the dialogue earns a break in the picture, and use straight cuts for ordinary
beats.

Add the optional `transitionCues` array to an individual clip in `clips.json`:

```json
[
  {"frame": 45, "preset": "inversion-flicker", "soundId": "small-electric-glitch"}
]
```

Frames are zero-based on the assembled **clip body** at native FPS, after speech
cuts and excluding any intro. Use an explicit `referenceEdit.frame`. Put the cue
on the first frame of the incoming shot. Keep cues ordered and at least one
second apart. Picture filters stay inside the picture area and underneath captions.
Omit `soundId` for a silent visual cue. Keep the two inversion presets to a
single decaying pulse. Check the actual moving edit for stacked or repeated
bright flashes and check that words remain readable over the changing footage.

The builder mixes SFX against the assembled dialogue after rendering and before
adding any music bed. Music-free versions retain the effects. If using a direct-props montage
workflow, render `transitionCues` with the picture, mux the approved dialogue,
then call `resolve_cues` and `mix_transition_sounds` in
`scripts/transition_sounds.py` under the resource guard before adding music.
Pass the rendered frame count and native FPS to bound the mix. Use the staged
audio at its existing level unless a documented gain is needed.

The [sound manifest](../assets/transition-sounds.json) records each official
download, licence, hash, trim and acoustic accent. Save the WAVs locally as
`Main/shorts-clips/SFX/<soundId>.wav`. If a file is absent, restore it from the
manifest and verify the hash. Keep stock WAVs out of Git and use them only in
finished edits under their licence. Before substituting an exact tutorial asset,
verify official access and permission for YouTube and Instagram and update the
manifest. The tutorial's combined audio is reference material.

Inspect the first three seconds, each accented cut and the final beat at phone
size. Listen through the whole edit for masked consonants, intrusive peaks,
and cut-to-sound alignment. Record actual review coverage and confirm source
frame cadence and dialogue sync through the guard.

## Choose and time the music

When planning music with the owner, give two or three ranked song suggestions in
the review or upload notes. Give the track, artist, exact recording or version, a reference
link when available, and the **start and end timestamps on that recording** for
the proposed excerpt. Specify where that excerpt starts in the edit when it
starts after frame zero. Derive the endpoint from the final edit duration and
the intended music placement. Label estimates and record whether the actual
recording or only its metadata was checked.

For thought.palace, ask the owner to confirm the exact YouTube Sound recording
and excerpt after the [B-roll decision](owner-led-edit.md#2-send-the-b-roll-brief-and-wait-for-shot-choices).
Map the beats that affect the edit, including relevant downbeats, pauses and
melodic changes. Record the intended visible changes in the edit timeline, or mark them for a visual
change to be determined during the final caption stage. A new shot, caption
reveal, genuine angle change or small visual accent can carry a beat. Design and
time caption reveals only after the picture and transitions are locked. Log the
chosen effect and sound where used. Check that the shot remains readable and
the dialogue remains intelligible. Bring changed shot requirements to the owner.
Mix sound accents around the primary track's hits so they reinforce the cut and
leave room for dialogue. Give each alternate its own excerpt and identify any
important cuts that would need retiming.

For thought.palace, deliver the music-free dialogue-and-effects master and
include the cue sheet when music timing was agreed. When the owner handles music
independently, follow the dialogue timing and skip the song stage. A cleared timing audition stays in `Working`. A
version with embedded music requires an explicit delivery request.
