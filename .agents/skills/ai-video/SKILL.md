---
name: ai-video
description: Create new narrated AI reels, illustrated explainers and cinematic videos from a brief or storyboard, using local media tools or verified free online generation. Route visual design, narration, captions and rendering by capability and measured hardware limits. Use for creating new videos; use viral-shorts for extracting moments from existing source footage.
---

# AI Video

For enhancing supplied footage while retaining its speaker/dialogue, use
[motion-edit](../motion-edit/SKILL.md). This workflow creates new narrated films.

Create a coherent finished film, usually a 30–60 second vertical reel. Plan the idea,
script and visual continuity first. The owner permits local processing and genuinely free
online AI tools; there is no permission to buy credits, enable billing or use paid cloud
fallbacks. Do not promise virality or photorealistic local generation that has not been tested.

The owner's supplied October 2026 references establish a cinematic technical-explainer
direction: large product/mechanism close-ups, detailed cutaways, material lighting,
camera moves, and animated physical behaviour. Captions support the demonstration.
The earlier paper-background touchscreen diagram is not an accepted match to that style.
Study the actual references before a new production; do not substitute a generic diagram
template or a text-card sequence for this visual direction. A stylised or 2.5D alternative
must be described accurately, not passed off as an equivalent 3D result.
The owner wants an original visual identity, not exact reference copies. Use references
to judge craft and explanatory clarity; author our own geometry, shot progression,
camera choreography, palette and motion language. Do not trace their sequences,
reuse their presenter/branding or reconstruct their distinctive graphics shot for shot.
Reference narration is not automatically a factual source. Verify the new script's
scientific explanation with primary technical sources rather than copying claims,
numeric readouts or simplified field visualisations literally.
Read the [recorded four-reference study](../../../Main/AI-videos/Working/reference-analysis/style-findings.json)
for timestamped examples, tool decisions and explicit inspection coverage. Recheck its
file inventory against Reference before reusing those findings.

## Owner's project folders and references

Use `D:\J.A.R.V.I.S\Clipping\Main\AI-videos` for this skill:

- `Reference`: owner's style examples. Study the available videos in depth before
  designing a film; follow [reference study](../viral-shorts/references/stage-routing.md#reference-study).
  Preserve originals and report when the folder has no videos to inspect.
- `Working/<project-id>`: brief, storyboard, prompts, generated/imported assets,
  narration, project records, drafts, continuity checks and QA evidence.
- `Exports/<project-id>`: finished, validated videos and delivery/provenance notes.

Save timestamped reference findings in `Working/reference-analysis`; record which files
were inspected and recheck new/changed examples on later invocations. Match the relevant
visual language, pacing and sound design to the brief. References do not automatically
become assets for reuse, and different example styles need not be blended together.

The runner currently stages under `work/ai-video`, `out/ai-video` and `public/ai-video`.
Keep required staging in place, copy working records/drafts/QA to this skill's `Working`
folder, and copy only reviewed final deliverables to `Exports`. Do not invent an output
flag or move existing projects/shared runtimes to make these folders appear integrated.

## Runtime and admission

Work in `D:\J.A.R.V.I.S\Clipping`. Source
`D:\J.A.R.V.I.S\.runtime\environment.ps1`. Python is `.venv\Scripts\python.exe`.
Run `.agents\skills\viral-shorts\scripts\check_environment.ps1` on every invocation.
Run `scripts/ai_video.py check` to distinguish available composition from certified diffusion.
Keep every dependency, cache, credential, model and output under `D:\J.A.R.V.I.S`.

All heavy local work uses the existing `viral-shorts/scripts/run_guarded.ps1` with the
canonical Clipping root. Both skills therefore share **one lock and one CPU-capped process
tree**. Preserve its mains/CPU/RAM/GPU admission, 25% tree CPU cap, two-thread limits,
one rendering worker, pressure aborts and confirmed cleanup. Do not copy the guard into
an independent folder, start JARVIS, or change the owner's jobs/watchdog hold.

The orchestrating assistant can plan and review; local media generation does not imply
that the assistant itself runs offline. For confidential assets use only explicitly allowed
destinations; no online upload is required to make an illustrated film.

## Choose the specialist for the actual step

Read [the stage routing guide](../viral-shorts/references/stage-routing.md), then load
only relevant specialist instructions. Remotion is the working default, Anatomy is for
technical isometric assets, and free image/video generators are optional asset sources.
Do not add HyperFrames, VoiceStudio or OpenWhispr merely to increase the tool count.

Flick (`../flick/SKILL.md`, when installed) can improve concrete scene planning and
action-matched motion/sound; its templates are not a 3D model generator. Reuse the
existing runtime and resource guard rather than its alternate bootstrap. See the
shared routing guide for FilmCraft and EffectCraft use.

For local capacity, model candidates, free-provider checks and long-run limits, read
[hardware and generation](references/hardware-and-generation.md). For the executable
storyboard format and continuity rules read [production](references/production.md).

## Production loop

1. Establish the audience, message, length, visual style and narration. Default to a
   coherent film with intentional cuts; an unbroken generated take requires a separate
   tested continuation capability. Write a consistent palette, character/prop references,
   camera rules and voice before making individual assets.
2. Choose illustrated, cinematic, or a mixture per scene. Use SVG/Anatomy and frame-driven
   motion for explanations. For original 3D product/mechanism cutaways, use the portable
   Blender route and measured profile in [hardware and generation](references/hardware-and-generation.md);
   retain Remotion for labels and final encoding. Procedural 3D does not require a diffusion model.
   Use a certified local diffusion profile or a verified free
   provider for new realistic footage. An installed UI or an advertised VRAM minimum is
   not a certified model. Open Higgsfield is an API frontend, not a local model.
3. Prefer a **single batch** when the requested duration, resolution and model fit a
   measured profile. Only segment for a real model-duration/memory/time limit, or when
   the story itself calls for separate shots. Splitting does not shrink model weights.
4. Before a full generation batch, benchmark the intended profile. Record actual GPU use,
   peak RAM/VRAM, elapsed time, resolution, frame count, dtype and quality. Forecast the
   whole project including retries and composition. If unknown, benchmark first; if the
   conservative forecast exceeds **24 hours**, stop and present simplification/free-online/
   cloud choices. Paid cloud always waits for a new explicit owner decision.
5. Produce assets sequentially and save completed shots/checkpoints. Release each model
   process before narration/transcription or rendering. Stop on out-of-memory; report
   the limit instead of automatically retrying on CPU or buying a different service.
6. Write `Main/AI-videos/Working/<id>/storyboard.json`, run `scripts/ai_video.py plan <file>`, then
   render through the shared guard. Local illustrated benchmark/render commands are below.
7. Inspect `qa.jpg`, boundary frames and the video/audio. Check identity, wardrobe, lighting,
   text, framing, pacing, caption timing and joins. A matching seed alone does not establish
   continuity. Never deliver a scene with visible drift as a seamless film.
8. Copy validated `out/ai-video/<id>/video.mp4` and its receipt to
   `Main/AI-videos/Exports/<id>/`; retain QA and working records in
   `Main/AI-videos/Working/<id>/`. State which assets were locally
   generated, assistant-authored graphics, imported, or generated by a named free service.
   Keep free-service failures, untested local models and any manual steps visible.

```powershell
$ClipRoot = 'D:\J.A.R.V.I.S\Clipping'
$ClipPython = Join-Path $ClipRoot '.venv\Scripts\python.exe'
$Guard = Join-Path $ClipRoot '.agents\skills\viral-shorts\scripts\run_guarded.ps1'
& $ClipPython scripts/ai_video.py check
# First measured illustrated sample; this is not a diffusion benchmark.
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/ai_video.py', 'benchmark') -TimeoutSeconds 900
# After writing an actual storyboard and checking its forecast:
& $ClipPython scripts/ai_video.py plan $StoryboardJson
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/ai_video.py', 'render', $StoryboardJson)
```

Check each exit code before the next step. A benchmark is a technical acceptance sample,
not permission to replace requested content with a generic demo. The built-in diagram is
only a simple sample; real Anatomy work follows that specialist's craft and geometry checks.
