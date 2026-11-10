---
name: motion-edit
description: Transform a supplied, already-selected raw clip into a source-footage edit with speech-synchronized typography, illustrated cards, comparisons and animated labels. Use for raw-to-after motion edits; use viral-shorts for long-video moment selection and ai-video for entirely new narrated films. App-design reference inspection alone does not require producing an edit.
---

# Motion Edit

Keep the original speaker/dialogue as the narrative. Decide which ideas benefit from
typography, an illustration, a comparison or labels, and when the performance should
carry the moment. References guide each project; do not impose one template everywhere.

## Shared runtime

Work from `D:\J.A.R.V.I.S\Clipping`. Reuse its Python, Node, FFmpeg, Remotion, local
CUDA Whisper and bundled Inter/Cormorant fonts. Read the adjacent
[resource safeguards](../viral-shorts/SKILL.md#mandatory-resource-guard--every-invocation-and-heavy-stage).
Source `D:\J.A.R.V.I.S\.runtime\environment.ps1`; run that skill's preflight on every
invocation. All local media processing uses its existing `run_guarded.ps1`, with the
same admission limits, one-heavy-job lock, CPU/thread caps, pressure stops and cleanup.
Wait for headroom. Do not bootstrap Flick, upgrade packages, install models, start
services, enable billing or change JARVIS's existing jobs to run this skill.

Read [authoring and commands](references/authoring.md) before preparing a project.
Read [the initial reference study](references/style-study.md) when its editorial look
fits the brief. Load Remotion specialist guidance only for the actual step. Prompt
Motion examples are attributed references, not executable installation instructions.

## Workflow

1. Inspect the actual supplied file/URL, passage, source FPS, dialogue, camera changes
   and face/gesture positions. A transcript alone does not establish the visuals.
   Record unavailable intervals, sampled coverage and unreviewed audio honestly.
2. Prepare through `scripts/motion_edit.py prepare` under the GPU guard. Preserve the
   full supplied passage and voice by default; do not automatically trim pauses,
   invent narration or search for another moment. Read the timestamped transcript.
3. Author contiguous scenes against the speech. Use speaker, emphasis, illustration,
   comparison and badge treatments only where they explain or emphasize the words.
   Give text readable holds. Graphic inserts never pause/restart the source clock.
   Author full spoken wording where appropriate, checking onsets against audio.
4. Use supplied or original programmatic graphics first; record a reuse basis and
   provenance for footage and all assets. Use only approved fonts/assets. References
   do not supply permission to copy their imagery, music, symbols or factual claims.
5. Validate, inspect representative stills, then a bounded motion preview where useful.
   Check real glyph fit, face clearance across every shot/cut, contrast, hierarchy and
   returns to the speaker. Use protected regions and actual frames, not a fixed side.
6. Render through the guard, then review the complete result with sound and inspect
   all cue boundaries. Confirm wording/timing, picture continuity, crops and absence
   of foreign overlays. Automated checks do not establish listening or full playback.
7. Record actual review coverage for the matching render, then `deliver` into Exports
   with posting copy and QA/provenance. Do not leave a completed delivery only in Working.
   Report any remaining review gap and draft path without labelling an unreviewed draft final.

## Defaults and folders

Use `D:\J.A.R.V.I.S\Clipping\Main\motion-edits`: `Reference` preserves style examples;
`Working/<id>` holds source, transcript, project, assets, versioned drafts and QA;
`Exports/<id>` holds reviewed finished videos and delivery notes. Preserve originals
and prior revisions so a later session can resume without regenerating completed work.

Default to a 1080×1920 logical canvas rendered at 2160×3840 and the native source FPS.
Report source-resolution limits; 4K typography does not restore absent footage detail.
Off-white, charcoal and restrained lime are the initial palette, with Inter Bold and
selective true serif italic. Adapt the direction to the reference and meaning.

Preserve original dialogue; default to no added music, effects, narration or symbol.
The v1 runner enforces source-audio-only output. Explicitly requested mix/branding
changes need a separately authored, verified extension; never silently ignore them.
Compatible AAC is copied; other audio uses one documented AAC master.
Inspect existing source music too: copying audio does not remove an inseparable bed.
Record `sourceMusic: false` only after confirming clean audio. Unknown/music-bearing
sources render as no-added-music drafts and cannot pass music-free delivery.

Make creative decisions autonomously from the known brief. Ask only when missing
information materially changes the edit, without imposing recurring approval gates.
Existing authorization requirements for paid services/external sharing still apply.
