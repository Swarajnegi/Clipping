# Source-led motion authoring

`MotionEdit` keeps the clean source video mounted on the global timeline under graphics.
The runner remuxes dialogue after picture rendering. It reuses ViralShort's framing and
EditorialCaptions, rather than AIReel's narration model.

## Commands

After sourcing the D-drive environment and passing the existing preflight, run from Clipping:

```powershell
$ClipPython = 'D:\J.A.R.V.I.S\Clipping\.venv\Scripts\python.exe'
$Guard = 'D:\J.A.R.V.I.S\Clipping\.agents\skills\viral-shorts\scripts\run_guarded.ps1'
$Project = 'D:\J.A.R.V.I.S\Clipping\Main\motion-edits\Working\my-edit\project.json'
# Bind $InputClip to the actual absolute file path or original URL.
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/motion_edit.py','prepare',$InputClip,'--id','my-edit')
# Author project.json against the prepared source/transcript before rendering.
& $ClipPython scripts/motion_edit.py validate $Project
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/motion_edit.py','render',$Project,'--still','2.4','--scale','2')
& $Guard -Mode Run -Workload Gpu -FilePath $ClipPython -ArgumentList @('scripts/motion_edit.py','render',$Project,'--preview','0:5')
& $Guard -Mode Run -Workload Gpu -TimeoutSeconds 7200 -FilePath $ClipPython -ArgumentList @('scripts/motion_edit.py','render',$Project)
# After actual review of the matching completed render:
& $ClipPython scripts/motion_edit.py deliver $Project
```

Choose timeouts from a measured preview. Do not repeatedly restart deferred/failed work.
`prepare --no-transcribe` is for silent/visual-only references or tests. Local inputs are
preserved in Working; URL acquisition reuses the downloader. Variable/nonzero-origin
presentation timestamps are normalized to the reported native rate, with the original
clock/file retained. Whisper reads extracted PCM to avoid the known PyAV interface issue;
its process exits before rendering. `--still` writes PNG; bounded previews default to scale 1.

## Project contract

Keep measured `source` fields intact: original/staged identities, rate, frame count,
duration, dimensions, audio presence and any normalization. Author:

- `reuseBasis`: recorded footage permission, licence or own-footage declaration.
- `transcript`: editable language/status/segments with word timestamps; the initial
  extraction is also retained in `transcript.json`. Check speech before finalizing cues.
- `sourceMusic`: null until inspected, then true/false. Music-free delivery requires
  false; copying source audio does not remove an existing music bed.
- `assets`: IDs mapped to `{path,reuseBasis}`, plus source/attribution if relevant.
  Files must exist under D:\J.A.R.V.I.S and be SVG/PNG/JPEG/WebP. Rendering snapshots
  them and records hashes; remote URLs are not loaded as live render assets.
- `shots`: increasing `{t,x,w}` entries: seconds, horizontal centre and visible-width
  fractions. The initial centre crop is a starting point, not a reviewed face crop.
- `captionLayers`: existing editorial layers (`t,dur,text,wordTimes,x,y,width,size`,
  font/style/motion). Use Inter or true Cormorant italic, with front depth. Subject-depth
  masks require an explicitly authored extension. Coordinates use the 1080×1920 canvas.
- `scenes`: contiguous coverage from zero to source end, with start/end seconds rounded
  to native frames. No gaps, overlaps or zero-frame cues are accepted.
- `protectedRegions`: optional `{start,end,x,y,width,height}` face/UI rectangles;
  intersecting active caption/badge boxes are rejected.
- `outputScale`: 1 or 2 (default 2); `palette`: six-digit `light/dark/accent` hex colours;
  `posting`: `{title,description}`.

| kind | Fields | Treatment |
| --- | --- | --- |
| `speaker` | Optional scene `captionLayers` | Source plus global captions |
| `emphasis` | `title`, optional `eyebrow`, `subtitle` | Accent headline/serif continuation over source |
| `illustration` | `title`, `asset` ID, optional `eyebrow`, `subtitle` | Light illustrated card |
| `comparison` | `title`, `left/right: {title,detail?,asset?}`, optional subtitle | Dark two-sided layout, one highlighted side |
| `badges` | `badges: [{text,at,x,y,width}]` | Labels entering individually over the source |

All times are clip-global. Global captions appear on speaker/badge scenes; graphic scenes
use their authored text and optional scene captionLayers. An explicit empty scene list
suppresses global captions. Keep complete speech readable without redundant emphasis.
Caption boxes must fit x=72–1008 and y=220–1500. The coarse bounds check does not measure
every glyph or detect moving faces; inspect actual wrapping and motion before delivery.

## Render and delivery evidence

Every render gets a unique draft/QA identifier. The runner requires actual NVENC,
checks dimensions/native FPS, completely decodes picture on CUDA and checks frame count.
Audio muxing must preserve picture packets. Unchanged AAC dialogue must retain every
audio packet and timestamp; non-AAC conversion is explicitly labelled as a one-time
master. Preview audio is an encoded excerpt, not a packet-identical final master.

Every render retains its project/props and a content-addressed immutable asset/font
snapshot. `last-preview.json` and `last-render.json` stay separate so a later excerpt
does not displace the completed full render awaiting review.

After review, fill `review.json` with the matching `render_sha256`, reviewer/time,
honest `coverage`, resolved empty `issues`, and true `visual_complete`,
`caption_timing_checked`, `branding_checked`, `continuous_playback_with_sound`.
Do not tick unperformed checks. Delivery rejects stale specs, modified renders,
previews, synthetic fixtures and incomplete reviews. It preserves the draft and verifies
the export copy hash. Report any remaining review gap rather than claiming upload QA.

Author a brief `posting.title` and `posting.description` before delivery. Technical
setup evidence and its limits are in the [setup record](../../../../Main/motion-edits/Working/setup-validation/README.md).
