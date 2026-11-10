---
name: viral-shorts
description: Discover original footage from reference edits, study the owner's editing and content taste, and turn long videos into vertical Shorts/Reels with framing, captions and optional narration. Use for clipping footage, finding suitable podcast moments, reference-led source discovery, or producing edited shorts and paired mixed/music-free exports.
---

# /viral-shorts

## Default framing and production source quality — 8 November 2026

For future vertical edits, use the owner's **centred rounded-square picture on a
black 9:16 canvas**, based on the supplied Chris Williamson reference. Author the
explicit `referenceEdit.frame` geometry and keep captions inside the picture,
shot-aware and off faces. Horizontal picture framing is allowed when it suits the
passage; do not force every source into a square. Read
[framing and source quality](references/framing-and-source-quality.md) before
new project setup. Existing approved edits are not automatically rebuilt.

Download native 4K production originals wherever available, preserving source FPS.
The prep downloader now prefers supported 4K over 1080p; cheaper research proxies
must remain labelled and cannot silently become finishing masters. If compatible
4K is unavailable, report the actual source limitation. A 2160×3840 export is not
proof of native 4K detail. Keep old lower-resolution revisions intact and acquire
a new master/revision when upgrading. Builder delivery defaults to scale 2; use
`--output-scale 1` explicitly for inexpensive editorial proofs. Resource safeguards
and one-heavy-stage-at-a-time admission remain mandatory.

For already-selected raw footage requiring illustrated cards, comparisons and
speech-led motion graphics, use [motion-edit](../motion-edit/SKILL.md). Keep this
workflow for discovery, moment selection and ordinary captioned clip production.

## Dialogue-led movie cutaways — 9 November 2026

**Permanent owner direction:** Include silent, dialogue-matched film or TV
cutaways in every new edit. Aim for around six or seven inserts per clip,
adjusting for the spoken beats and runtime. Follow
[movie cutaways](references/movie-cutaways.md) and search the local Movie Clips
catalogue first. Map the hook, development and payoff to recognizable scenes.
Use as much variety from the extracted film and TV library as the dialogue
supports, both within an edit and across a batch. Choose every insert for the
exact spoken cue and keep connected sequences coherent.
Start on the speaker, keep dialogue continuous and return to them where their
delivery carries the moment. Recompose captions around faces and action.
Verify a posting reuse basis for the inserts before promoting a clip for
publication. Keep versions with unresolved reuse labeled as private review.

When the owner adds a full-length pack, follow the guide's
[pack intake](references/movie-cutaways.md#new-pack-intake-and-handoff) on the next
applicable clipping request. Save and verify standalone excerpts before the owner
removes the full-length file.

## Default caption treatment — owner decisions, 3–8 November 2026

Latest owner correction, 8 November: for new thought.palace edits, centre the
**whole caption composition** in the middle of the picture, rather than anchoring
it at the bottom. On the current centred square/9:16 canvas both centres are
logical (540, 960). The owner's later clarification allows other genuinely empty
areas when they improve visual appeal and readability. Choose placement per shot
or phrase, keep faces/meaningful gestures clear, and avoid words jumping arbitrarily.
Keep the established type, timing and Difference treatment. Preserve older saved project geometry.
Read `EDITORIAL_TASTE.md` for the current duration, source-variety and owner-review
brief; these are not universal duration/source-count rules for other projects.

For new edits, use the [reference-style editorial captions](references/editorial-captions.md):
locally bundled Inter Bold, tight typography, word-synchronous stacked phrases,
large emphasis words, selective perspective and clean subject-depth compositing.
**Permanent owner instruction, 8 November 2026: apply colour-reactive Difference
blending to every word of every caption in every future video.** This includes
supporting words, emphasis, italic accents and every caption layer, not selected phrases
or foliage shots only. Author `surface: "difference"` explicitly on every layer and
follow the guide's white-fill preset. The supplied `surface-proof-phone.png` is the
visual reference: letters respond to the actual picture beneath them; simple translucent
white text does not reproduce it. Tune effect strength and placement for readability,
but do not silently switch words back to solid silver/normal blending. Change this rule
only when the owner explicitly requests an exception. Inspect the effect on the actual
moving footage, including bright clothing, dark areas and camera cuts, at phone size.
**Permanent owner direction, 10 November 2026:** Give selected hook, pivot and
payoff words visibly heavier weight or a larger size than their supporting text.
Use occasional true italics or a contrasting licensed typeface where the phrase
benefits from it, as in the 1 November 11:58 reference ("high" around 16s).
Reserve those word positions before their reveal. Inspect the hierarchy and
spacing at phone size. Keep the approved clean Difference finish. Solve
readability over skin or bright clothing through placement and typography.
Read that guide before authoring captions. This supersedes the older italic/picture-band
caption defaults, unless the current brief explicitly chooses another treatment.
Author `referenceEdit.profile: "editorial"` and its layers; selecting `brand.style: "bold"`
alone does not generate this treatment. Older styles remain explicit alternatives and
existing approved exports/specifications keep their behavior. Do not retrofit them unasked.

## Hook treatments and thumbnails — owner instruction, 8 November 2026

Before designing an opening or final cover, read
[hook treatments and thumbnails](references/hooks-and-thumbnails.md). The preserved
`luka.visual` reference demonstrates a progressively edited opening: colour,
reframing/zoom, captions, illustrative animation and an audio stage. Adapt techniques
to the actual speech and channel tone; a visual effect cannot supply a missing
spoken hook or complete payoff. Record the chosen treatment and why it fits.
**Permanent owner direction, 10 November 2026:** Start with the spoken hook and
make the first meaningful visual change on the earliest natural beat in the
opening one to three seconds. Prefer a dialogue-matched film or TV cutaway where
the line earns it. Use a reframing, caption emphasis or purposeful graphic when
the speaker should stay on screen. Check timing, readability and speech clarity
through all three seconds. Record the actual first line, the first transition's
timestamp and the spoken beat it serves. Check the opening at phone size before
delivering the finished cut.
An inexpensive opening preview may be shown on a specific clip before final finishing;
this is optional, not a new mandatory approval gate. Existing owner review gates apply.

Every finished clip must include a high-quality matching thumbnail/cover image,
reviewed at phone size and delivered beside its video in `Exports`. Keep exploratory
opening/thumbnail drafts in `Working`; finish only the owner's approved selections
when the brief calls for rough-cut review. Do not insert a static thumbnail intro
or copy the reference creator's footage, graphics, notifications, branding or sound.

## Standing owner rule — our channel, reference inspiration only

We are making edits for the owner's own channel. Use only the owner's supplied and
approved channel symbol, or **no symbol** when none is supplied. Never carry another
channel's overlaid watermark, logo, handle, signature or branded end card into a delivered
clip. This applies both to reference edits and to branding baked into original source footage.
Do not replace another publisher's mark with an invented owner mark.

References are taste and discovery guidance: people, subjects, delivery, humour, music
styles and potential source leads. Take inspiration from their cuts, fonts, layering,
framing and pacing; do not copy the reference edit, its branding or its media assets into
production by default. A reference is not proof of current popularity; verify trend or
outlier claims with current evidence. Identifying a reference song does not authorize copying it.

Acquire an authorized original, prefer a clean source, or reframe cleanly to exclude
baked-in channel branding while preserving faces, meaning and visual quality. Check the
whole selected passage because watermarks can animate or change position. If clean
framing is not viable, find another suitable source or report the specific limitation.
Keep original-source provenance and the reuse basis in project records and posting notes.

Before delivery, inspect final frames for foreign overlaid symbols, watermarks, handles
and end cards as well as caption readability and timing. A successful render is not a
branding check. The default for the current project is unbranded, music-free exports.

## Owner's project folders and references

Use `D:\J.A.R.V.I.S\Clipping\Main\shorts-clips` for this skill:

- `Reference`: owner's style examples. Study the available videos in depth before
  choosing an edit style; follow [reference study](references/stage-routing.md#reference-study).
  Preserve originals and report an empty folder rather than assuming a reference style.
- `Working/<project-id>`: source copies/downloads, transcripts, contact sheets, edit
  decisions, reference analysis, clips JSON, drafts and QA evidence.
- `Movie Clips/<title>`: reusable source-native, silent film/TV excerpts with source
  times, editorial tags and review status. Start at `Movie Clips/README.md`.
- `Exports/<project-id>`: finished, validated videos and their delivery notes.

Keep reference analysis in `Working/reference-analysis`, with timestamped observations
and a record of which files were actually inspected. Recheck for new/changed examples
on later invocations. References guide style; they are not automatically source footage.
The owner's brief decides which examples apply to a particular project.

For discovery from references rather than a supplied source, read
[source discovery](references/source-discovery.md). Use `scripts/discover.py` for bounded,
metadata-only catalogues; it does not choose moments or prove download access.
`scripts/study_references.py --mode inventory` records identities; `--mode cloud` submits
full files through the verified free-tier helper without local video processing. It records
provider review and upload-deletion results. `--mode local` requires the GPU guard and
prepares full transcripts and one-second frame sheets for assistant inspection. Prepared
evidence and provider descriptions are not a claim of direct full audiovisual playback.

Owner's 1 November 2026 brief: `WhatsApp Video 2026-11-01 at 11.54.55 AM.mp4` and
`WhatsApp Video 2026-11-01 at 11.58.27 AM.mp4` are editing targets. Other examples guide
content, delivery, humour and music taste. Discover by taste across creators; begin with
Tate's Emergency Meeting/Tate Confidential, Rogan and Williamson. Follow the target's
opening, including direct speaker openings; do not force a narrated intro. Keep separate
profiles if these two edits differ. Findings live in `Working/reference-analysis`.
Read its `REFERENCE_STUDY.md` and the current project's source shortlist before selecting
a style. The inspected November targets use (A) restrained captions with illustrative
cutaways and (B) selective kinetic typography over the speaker. Both use a wide picture
band on black. Per-clip `referenceEdit` supports these layouts; read the source-discovery
reference for its schema. Exact visual matching still requires font/position tuning and motion QA. Audio/music study
coverage is recorded separately in the report; it is not inferred from the frame sheets.

The commands below still use the renderer's existing `work`, `out` and `public` staging
paths. Retain necessary staging files for those commands; copy project records/drafts/QA
into `Working/<project-id>` and promote only reviewed deliverables into
`Exports/<project-id>`. Do not claim these scripts already support output-directory flags,
move/delete existing projects, or relocate shared dependencies/caches for this layout.

## Native Windows location and runtime

Pipeline root: `D:\J.A.R.V.I.S\Clipping` directly; do not add an `autoclipper` subfolder.
Python: `D:\J.A.R.V.I.S\Clipping\.venv\Scripts\python.exe`.
Music: `D:\J.A.R.V.I.S\Clipping\music`; campaign material: `D:\J.A.R.V.I.S\Clipping\Campaigns`.
Keep the clipping environment separate from JARVIS's parent `.venv`; an old machine's
virtual environment is not portable. Restore dependencies from the clipping project's actual
manifests rather than modifying JARVIS's working environment or copying old binaries.

Use native PowerShell and explicit executables. Begin each clipping session with:

```powershell
. 'D:\J.A.R.V.I.S\.runtime\environment.ps1'
$ClipRoot = 'D:\J.A.R.V.I.S\Clipping'
$ClipPython = Join-Path $ClipRoot '.venv\Scripts\python.exe'
$Guard = Join-Path $ClipRoot '.agents\skills\viral-shorts\scripts\run_guarded.ps1'
Set-Location -LiteralPath $ClipRoot
& 'D:\J.A.R.V.I.S\Clipping\.agents\skills\viral-shorts\scripts\check_environment.ps1'
if ($LASTEXITCODE -ne 0) { throw 'Clipping is blocked or deferred; read the environment and resource report before proceeding.' }
```

The check inspects files, executable locations, installed package metadata against the lock,
and 30 seconds of CPU/RAM/power/GPU telemetry; it does not import ML libraries,
load weights, contact providers, install packages or start services. Structural checks do not
prove dependencies or rendering work. Stop at missing components and identify them accurately.
Restore/setup when requested; do not substitute JARVIS's model stack or Codex's private runtime.

Source `D:\J.A.R.V.I.S\.runtime\environment.ps1` before any installation, model loading or rendering so
TEMP/TMP, pip/npm/uv caches, Hugging Face, Torch and other library caches remain under
`D:\J.A.R.V.I.S`. Keep Node, npm packages, browsers, FFmpeg, model weights, watch configuration,
local credentials and generated audio/video on D too. Preflight must not install CUDA or
download GPU components/models. Inspect this laptop and the recovered scripts' supported settings before
choosing CPU/GPU execution or concurrency; start expensive work sequentially with bounded
concurrency. Never inherit the dead laptop's throughput, GPU availability or credentials.

## Mandatory resource guard — every invocation and heavy stage

The owner's choice is **wait for headroom; preserve JARVIS's existing state**. Never stop,
suspend or reprioritize JARVIS, edit its pause registry, or change its watchdog or schedules
for clipping. Respect an owner hold: jobs that are paused/off stay paused/off, and no
bootstrap repair may start services or re-enable the watchdog to satisfy preflight.
Every invocation must run the preflight above. `-SkipResourceCheck` is an internal layout-only
check used by the launcher; it is not a successful invocation preflight.

Run all local transcription, voice generation, frame extraction/analysis and rendering through
`scripts/run_guarded.ps1 -Mode Run`. Commands below that load models or process video show
the required wrapper. A wrapper run rechecks the layout and waits for fresh capacity before
starting; a check earlier in the conversation is never a substitute. Lightweight metadata,
file inspection and the remote Gemini analysis itself do not need a GPU workload slot.

| Safeguard | Enforced default |
|---|---|
| Admission | Mains power, CPU average <=40% over 30s, available RAM >=4 GiB |
| GPU admission (default workload) | Utilization <=30%, free VRAM >=3 GiB, temperature <80 C |
| Busy machine | Sample every 5s; explain every 60s; defer after 10 minutes |
| Clipping concurrency | One heavy stage at a time, including across skill callers |
| CPU containment | Whole process tree capped at 25%, below-normal priority, numerical-library threads <=2 |
| Runtime pressure | Abort at CPU >85% for 15s, RAM <2 GiB for 10s, GPU >=85 C for 10s |
| Unknown telemetry / disconnected mains | Defer before launch; stop the clipping tree if lost during execution |

High GPU utilization during the stage is expected; it is not an abort condition. The guard
does not cap unrelated applications and cannot guarantee total machine load. These are
conservative defaults; adjust only after a measured sample and an explicit owner decision.

An explicitly owner-authorized render may opt into `-ThermalProfile MonitoredRender`.
This warns at 85 C and stops at 90 C for ten seconds, or on observed hardware/software
thermal throttling at the next five-second sample. Throttle telemetry is mandatory for
this profile; missing measurements defer/abort. Admission remains below 80 C and all
CPU/RAM/power/VRAM, containment and cleanup rules remain intact. The default is still
`Conservative` (85 C). Never select the alternate profile merely to complete a hot job.

Pass an executable path and a PowerShell string array, never a composed shell command:

```powershell
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('.\scripts\build.py', $ClipsJson)
if ($LASTEXITCODE -ne 0) { throw 'Stage did not complete; inspect the guard diagnostic and worker logs.' }
```

The launcher waits up to 600s for admission and supervises a stage for 1800s by default.
Use `-TimeoutSeconds` for a measured longer stage (maximum 86400s); do not increase the
waiting period by repeatedly starting the same deferred operation unattended.
Exit codes: 1 missing layout; 75 deferred/busy; 76 resource abort; 124 execution timeout;
130 cancellation; 70 launcher/cleanup failure. Worker errors are preserved. No automatic
retry or CPU fallback is permitted after a GPU error or out-of-memory failure.

GPU settings must be verified on this host: transcription uses the
available CUDA backend with a model that fits the 6 GiB GPU; hardware video encoding uses
NVENC where supported. Observe actual GPU execution on a sample; merely detecting the GPU
is not proof. Run transcription and rendering as separate guarded processes so model memory
is released between stages. Voice may use a documented lightweight CPU backend explicitly
with `-Workload Cpu`; do not silently move GPU transcription/rendering to CPU.

The restored builder uses NVENC for snippets/backgrounds and requires Remotion hardware
encoding with bitrate control (CRF is incompatible with NVENC). The builder explicitly sets
rendering concurrency to **1** and video decoding workers to **2**; `remotion.config.ts` bounds every Remotion
FFmpeg command with `-threads 2`, `-filter_threads 2` and `-filter_complex_threads 2`.
Python helpers apply the same FFmpeg bounds. Voice synthesis runs on CPU with two ONNX
threads; word alignment runs on CUDA in that separate voice process, which exits before
rendering. Invoke `voice.py` with `-Workload Gpu` because alignment needs the GPU too.
Direct model/video script execution outside the guard is rejected by Windows job membership.
Nested voice/model and render stages use the launcher's internal `-Mode Wait` to obtain fresh
capacity measurements while retaining the outer job and lock. This mode checks resources
only; it never launches work or replaces the mandatory invocation preflight.

### Explicit restoration/setup only

Routine preflight never installs anything. When the owner asks for setup/restoration,
`-Setup` permits guarded installers to run with an incomplete layout; all resource admission,
CPU limits, monitoring, single-instance locking and cleanup remain active. Do not use it to
bypass a blocked production video stage. Keep the existing base Python and create only
`Clipping/.venv`; dependencies come from `requirements.txt` / `requirements.lock.txt`,
and the renderer from `package.json` / `package-lock.json`.

After creating that venv on D, the guarded setup stages are:

```powershell
& $Guard -Mode Run -Setup -Workload Cpu -FilePath $ClipPython -ArgumentList @('-m', 'pip', 'install', '--only-binary=:all:', '-r', 'requirements.lock.txt')
& $Guard -Mode Run -Setup -Workload Cpu -FilePath $ClipPython -ArgumentList @('scripts/restore_assets.py')
& $Guard -Mode Run -Setup -Workload Cpu -FilePath $ClipPython -ArgumentList @('scripts/restore_whisper.py')
& $Guard -Mode Run -Setup -Workload Cpu -FilePath $ClipPython -ArgumentList @('scripts/install_renderer.py')
```

Stop after a nonzero stage result. `restore_assets.py` downloads portable Node/FFmpeg,
Kokoro/YuNet models and the upstream video-review helper on D; it validates published
checksums where available and records provenance under `.runtime/pipeline-restore/`.
`install_renderer.py` installs npm-lockfile packages sequentially with verified integrity and
paced file extraction, without package lifecycle scripts. It obtains
its local browser, and typechecks it. Test the restored runtime with:

```powershell
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/verify_runtime.py', '--smoke')
```

This creates synthetic speech/video only, checks actual CUDA transcription and NVENC
rendering at 30000/1001 FPS, and writes a receipt under `.runtime/pipeline-restore/`.
Inspect its QA strip before declaring restoration verified. No private footage or provider
upload is needed. A model or render error stops that stage without automatic retry/fallback.

Diagnostics live under `.runtime/guard/<run-id>/`: resource samples, stdout/stderr and
`result.json`. The last result must show `worker_succeeded` and `cleanup_confirmed=true`;
then validate video/audio streams, duration, captions and visual QA before delivery.
`worker_succeeded` alone is not editorial acceptance. Preserve completed outputs; never
deliver interrupted or partial outputs without revalidation. Cancellation stops only the
guard-owned Windows Job Object. A pending cleanup record blocks new work until that job
is confirmed empty; the next invocation checks this without terminating other processes.

Usage: `/viral-shorts <url-or-file> [n=2-10] [campaign brief path]` in Claude;
use `$viral-shorts` or select the skill in Codex. Read the source video's actual frame rate;
preserve it through selection, timing and rendering instead of assuming 30 FPS.

You are the editor. Scripts perceive and render; **you judge**. Never skip the looking steps —
on the MW4 run, half of the audio-top candidates were killcam replays, pre-round screens and
a firing range, and on the TED test a fixed centre crop would have cut the speaker in half.

## Selection before production

Before choosing podcast moments, read [moment selection](references/moment-selection.md).
Require a compelling spoken opening, progression, fluent delivery, a complete payoff and
channel fit before expensive captioning. A useful lesson, high replay peak or famous guest
cannot override a failed check. Search across sources rather than filling a clip quota.

Study successful and weaker comparable Shorts; treat public views as reach evidence,
not proof of retention or a causal editing formula. `scripts/outliers.py` supplies leads,
not an approval score. Check sample age, format and missing counts before comparisons.
Recreate useful storytelling principles, not another editor's assets or a copying percentage.

Tighten and, when authorized, restructure genuine source speech without changing meaning,
attribution or context. Preserve emotional pauses and natural breaths; do not automatically
enable silence trimming on all speech. End when the strongest thought lands. Runtime and
count follow the current brief; there is no universal duration floor or posting quota.
Narration, music and channel branding remain governed by the owner's brief and rules above.

Prepare an inexpensive full-length editorial proof before 4K finishing. Review its complete
flow with sound and record the actual reviewer/method/coverage. Transcript and frame checks
alone cannot establish spoken fluency. Pending audiovisual review is not editorial approval.
Keep this coverage distinct from technical render QA and the owner's decision to publish.

Use actual audience metrics at comparable publication ages. `results.py` preserves legacy
`--avd` as percentage viewed; duration in seconds is a separate field. Unknown metrics stay
unknown. There is no universal 85/85 pass rule. Log owner selection independently and judge
workflow improvement by accepted clips and production minutes per accepted clip.

## Styles (`brand.style`, per-clip override `style`)

| Style | Look | Use for |
|---|---|---|
| `bold` | full-bleed, big word-pop captions, accent highlight | legacy alternative; editorial layers are the new caption default |
| `clean` | small one-line captions below the chin, plain hook | TikTok podcast/motivation pages |
| `frame` | rounded-corner card on black, captions under it | "cinematic"/quote pages (Alex's frame) |
| `letterbox` | 16:9 band scaled ~2× on black, one-line captions | podcast compilations (Joe's 198%) |

## Steps

Before choosing tools, read [stage routing](references/stage-routing.md). Load only the
specialist guidance for the step being performed: Remotion composition, captions and export,
Anatomy only for requested technical illustrations. Keep the current verified runtime and
editorial refinements; another app is adopted only for a specific measured benefit.

In the commands below, bind `$VideoInput` to the owner's URL/file and derive `$VideoId`,
`$CandidateRanges`, `$ShotRange`, `$ClipsJson` and metrics from actual pipeline outputs or
owner-provided values. Replace the literal `'@channel'` with the selected real channel.
Check restored scripts' help/schema before using optional flags; examples are not receipts.

0. **Reference (new channel or new niche).** Use `scripts/outliers.py` as a bounded discovery
   lead on relevant channels. Compare strong and weaker examples of similar age and format;
   record source, hook, progression, ending, observed metrics and actual inspection coverage.

1. **Prep** — `& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('.\scripts\prep.py', $VideoInput)`
   Outputs `work/<id>/`: `source.json` (title, chapters, **heatmap**), `transcript.txt`,
   `timeline.txt` (per-5s loud/onsets/var/cuts/wps/heat), `signals.json`.
   If `heatmap=no`, YouTube is not serving replay data for that video — use chapters.

2. **Shortlist selectively.** Use chapters, transcript search, replay peaks and delivery signals
   as leads, with no automatic heatmap precedence. Apply the five editorial checks in the
   linked guide. Record exact opening, source ranges, context, payoff, cut proposal,
   benchmark match and rejection risks. Use `segments` for justified tightening/restructuring;
   keep meaning and attribution intact. Reject weak passages even when the brief permits more.

2b. **Gemini second opinion (restored claude-video `watch` helper).**
   The helper is restored under `.runtime/claude-video`. Use `scripts/watch_review.py`,
   which imports the helper's real config module and binds its config paths to
   `.runtime/watch/.env` before delegating. This is a local adapter for upstream's hardcoded
   home-directory config, not an invented upstream flag. Never invoke the raw setup helper
   against the Windows home directory, and never put keys in this skill.
   `& $ClipPython .\scripts\watch_review.py --check` reports key/model/free-tier readiness
   without exposing the key or uploading video. Credentials live in ignored `.runtime/watch/.env`.
   The owner permits **automatic local fallback** if Gemini is missing, rate-limited or fails.
   Use `--help` for actual window/question flags. `--engine auto` chooses Gemini only with
   a configured key and a confirmed free-tier project; `--engine local` forbids cloud review.
   There is no paid fallback, billing enablement or automatic API retry.
   Use the configured model confirmed available to the key; historical model names and the
   upstream default are not provider-verified settings. Model listing is not proof of a review.
   Actual helper analysis includes local frame extraction: invoke it through `$Guard -Mode Run
   -Workload Cpu -FilePath $ClipPython` with an argument array beginning
   `'scripts/watch_review.py'`. The adapter requires job membership, bounds FFmpeg threads,
   and disables the helper's separate Whisper backends; local transcription stays in prep.py.
   For each shortlisted window, ask: "Rate 1-10 how gripping this is for a YouTube Short.
   What happens second by second (visual + audio)? Where exactly is the peak reaction or
   payoff? Is there dead air?" Use peak timestamps to tighten boundaries and choose the
   intro still; treat ratings as supporting judgment, not measured virality.
   Verify the provider's actual upload/deletion behavior; do not promise automatic deletion.
   Skip cloud analysis for private/campaign footage the user must not share, as in the original
   workflow, using `--engine local`. If Gemini is unavailable, prepare local contact sheets
   and use the existing CUDA transcript; inspect them and continue with assistant review.
   Label the result accurately: local preparation does not mean a local vision model made
   an assessment, and a fallback must never be reported as Gemini review. The adapter records
   the selected route and fallback in `.runtime/watch/last-review.json`.

3. **Look.** `& $Guard -Mode Run -Workload Cpu -FilePath $ClipPython -ArgumentList @('.\scripts\sheet.py', $VideoId, $CandidateRanges, '--frames', '8', '--name', 'round1')`, then Read the jpg.
   Reject: replays/killcams, menus, loading, pre-round, practice ranges, dead air, non-English UI
   when the brief says English only, and moments that need context the clip does not contain.

4. **Frame.** Fast-cut sources (a cut every ~1–2s in `timeline.txt`): omit `shots` on talk
   clips — build.py makes one shot per detected cut and face-tracks each (YuNet; b-roll with
   no face falls back to centre). Slower multi-cam (TED, podcasts): run sheet.py through
   `$Guard -Mode Run -Workload Cpu` with arguments `@('.\scripts\sheet.py', $VideoId, '--shots', $ShotRange, '--name', 'cN_shots')` → set per-shot `x` (gridlines 0.25/0.5/0.75) and `w`
   (omit = full-bleed + tracking; 0.6–0.7 for slides/on-screen text; 1.0 whole frame;
   `"lock": true` to stop tracking, e.g. audience shots). Gaming: type `gaming`, x 0.5.
   Blue sub-samples (S3b…) expose missed cuts — add a shot there.
   Two-person conversations (interview, car ride, podcast two-shot): set `"trackMode": "group"`
   and `"widthFrac": 0.5` so tracking centres BOTH faces — default tracking follows the
   largest face and cropped Jay Leno out while he delivered the punchline.
   Vehicle/action/wide-shot clips: `"widthFrac": 0.42` so explosions and water shots keep context.
   Intro stills: avoid frames with the source's own burned-in labels/arrows.

5. **Choose the opening.** Follow the project brief/reference before defaulting to narration.
   Omit `intro` for a direct source-speaker opening. If narration fits, write 1–2 sentences, 5–12s,
   stakes + curiosity, present tense, no spoiler ("He survived six levels without flinching.
   Then Nick offered him something to cool down."). Pick `introFrameAt` = the most striking
   frame of the clip (not the payoff frame).

6. **Write `work/<id>/clips.json`** (schema in `scripts\build.py` docstring): `brand` (style,
   accent, grade, music, voice), per clip start/end or `segments`, type, `intro`, hook, shots,
   punchIns (≤1.1×, 1–2 biggest beats), title, description, why. Campaign brief? Required
   caption/#Ad/tags → `footer`, logo → `watermark`, mandatory on-screen text → hook.

7. **Render** — `& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('.\scripts\build.py', $ClipsJson)` (append `'--only', '2'` for an actual selected clip).
   For the owner's paired delivery use `"pairedExports": true` at the top level of clips.json
   or append `--paired-exports`. Configure a cleared music file. The builder renders one
   speech/effects master with the added bed disabled, then stream-copies its picture while
   mixing the bed into the companion. Outputs: `clip_NN.mp4`, `clip_NN_music-free.mp4`,
   and a packet-hash/timing receipt. Source-embedded music remains in both: choose clean
   dialogue sources or explicitly mark that limitation. Never mute speech to make this version.
   The old laptop measured ~10–13 min per minute of output; that is historical only.
   Measure one small render here before estimating a batch. Keep one heavy render at a time,
   with cancellation and observable progress; do not launch parallel background batches.

8. **QA.** Read every `out/<id>/qa/clip_NN.jpg` (start, 35%, 70%, end; frame 1 is the intro
   when present). Check: intro still is striking, captions readable/synced/one line in clean,
   hook in the safe zone and off faces, no half-cropped subject, and no foreign overlaid
   watermarks/symbols/handles/end cards. Include frames across source cuts and any animated
   branding. Use the owner's approved mark or none. Fix, re-render with `--only`.

9. **Hand over** validated `clip_NN.mp4`, its matching reviewed thumbnail/cover image,
   and `UPLOAD.md` from
   `Main/shorts-clips/Exports/<project-id>/` after copying from renderer staging;
   keep QA evidence under the project's `Working` folder. Remind the user to check 1–2 on the phone
   with sound before posting if that coverage remains outstanding. Do not prescribe a posting quota.

10. **Close the loop.** Log real Studio metrics using `scripts/results.py add`; legacy
    `--avd` means percentage viewed, not seconds. Use `selection` for owner choices and
    production time. Review comparable-age results before the next batch; missing metrics
    are not zeros, and one viral outlier is not a universal benchmark. Suggest a complementary
    next upload on our channel in posting notes; do not withhold this clip's payoff for part two.

## Rules

- Rights: catalogue discovery leads with unknown permission, but record a reuse basis before
  production/delivery (own footage, permission, applicable licence or authorized campaign).
  Public availability and creator identity do not establish permission. Third-party footage
  can receive claims or strikes; flag an unresolved reuse basis once, without inventing a legal determination.
- Music: only license-clean tracks the user placed in `D:\J.A.R.V.I.S\Clipping\music\`; never rip songs.
- Don't reuse the MW4/Valorant clips in `D:\J.A.R.V.I.S\Clipping\Campaigns` as references — they failed.
