# Local capability and generation routes

## Observed host, 25 October 2026

Native Windows 11, i7-10750H (6 cores/12 threads), about 16 GiB RAM, NVIDIA RTX 2060
(6 GiB VRAM), driver 592.82, roughly 64 GiB free on D at inspection. Around 5 GiB RAM
and 5.1 GiB video memory were free; these are snapshots, never admission guarantees.
JARVIS's 18 paused jobs and disabled watchdog must stay unchanged.

| Capability | Evidence and route |
|---|---|
| Existing-video clipping, captions, voice and NVENC | Existing guarded pipeline; rerun current preflight |
| AI-authored graphics/illustrated films | Remotion + SVG/Anatomy + Kokoro; use the illustrated benchmark receipt |
| Local photorealistic diffusion | **Uncertified**; no diffusion runtime/model was installed by the skill creation |
| Free online assets | Allowed when actual account access, free quota and asset sharing are verified |

NVENC is a video encoder. Its success does not prove a generative model fits. Model
weights, text encoders, decoder and activations count against both RAM and VRAM. Shorter
segments can reduce activations but cannot fix an oversized base model. Offloading can
increase system-RAM needs and processing time; it is never an unannounced CPU fallback.

## Procedural 3D pilot, 28 October 2026

Portable Blender 4.5.15 LTS is installed under `.runtime/blender/4.5.15`, with an
official-checksum receipt. The original touchscreen pilot completed an eight-second,
1080×1920, 30 fps sample using EEVEE on the RTX 2060, with 32 samples, two CPU threads
and no CPU rendering. All 240 images passed integrity/source checks; Remotion composed
the labels and NVENC encoded the video, followed by stream-copy finalization and full decode.
Working sources, both editable Blender scenes, QA and guard diagnostics are under
`Main/AI-videos/Working/touchscreen-3d-test`; validated output, receipt and forecast are
under `Main/AI-videos/Exports/touchscreen-3d-test`.

Cycles OptiX rendered a native frame in about 9.9 seconds, but continuous rendering
triggered the conservative thermal stop and, on the owner's monitored retry, a software
thermal-throttling flag at a sampled 86 C. Its sustained profile remains uncertified.
The 100 completed Cycles frames are retained separately; do not mix them with EEVEE frames.

EEVEE needed material-level raytraced transmission, slab thickness and disabling the
glass's opaque shadow to retain the sensor grid. These are approximate glass-lighting
settings; inspect representative stills for each new scene. The corrected later frames
rendered in roughly 3.5–4 seconds, but pacing each frame until core temperature was below
80 C dominated elapsed time: about two hours for this sample. The final long pass peaked
at a sampled 86 C with no observed thermal-throttling flags. Visible grain remains at
32 samples; this is a procedural 3D visual pilot, not photorealistic diffusion certification.

The same-complexity extrapolation, including a 50% retry margin, is roughly 11 hours for
30 seconds and 22 hours for 60 seconds of rendering. It excludes new assets, animation
authoring, narration, sound and editorial work. Do not treat it as a complete production
forecast or certification of a day-long load; benchmark and budget the actual storyboard.

## Local diffusion feasibility gate

Keep a separate environment under `.runtime/ai-video/`, never modify the existing clipping
or parent JARVIS environments to install Torch/Diffusers. Setup must be explicit, pinned,
guarded and disk-budgeted including downloads, extraction, cache duplication and outputs.
Retain at least 20 GiB disk reserve; do not automatically download several model families.

The first candidate for a bounded evaluation is **CogVideoX-2B in FP16**, using the official
Diffusers sequential CPU offload, VAE slicing and tiling path. Its upstream 4 GiB minimum
was measured on different GPU architectures, so it is not a promise for Turing/Windows
or this PC's available RAM. This 2B profile is text-to-video; do not promise image-conditioned
identity continuation from it. A richer image-to-video candidate needs its own explicit
memory/precision/continuity assessment before any download.

Do not use standard Wan2.1 1.3B as a known 6 GiB fit: its official baseline is 8.19 GB VRAM.
Do not choose FramePack just because it advertises 6 GB: its documented target is RTX
30/40/50 with FP16 and BF16, and 20-series hardware is untested. Avoid FP8/BF16-dependent
optimizations on the RTX 2060. Do not install unsupported custom CUDA kernels or a system
driver update to force a model through this gate.

Before production, demonstrate loading, a small short sample, a representative sample
and acceptable quality under the guard. Record the exact model/revision, dtype, dimensions,
frames, steps, GPU device/actual compute, peak RAM/VRAM, timing and startup overhead.
Use at most 30 minutes for an initial inference probe; stop on OOM, unsafe pressure, no
progress, or a clearly excessive forecast. No unattended retry/model-download ladder.

Start with the requested batch only if it is inside the certified envelope. Otherwise
propose smaller supported shots if the model itself fits. Shared reference assets and
editorial cuts are the default continuity technique; a seed is not an identity guarantee.
Do not queue a full film until a conservative measured estimate, including retries and
final assembly, is <=24 hours. Reforecast after each completed shot and stop for an owner
decision if the remaining project exceeds that limit. Keep completed assets for resumption.

The guard's default 85 C sustained stop remains mandatory unless the owner explicitly
authorizes the opt-in `MonitoredRender` profile for a particular run. On 28 October the
owner authorized it for the touchscreen pilot after inspecting device-reported limits:
87 C target, 93 C hardware slowdown, 98 C shutdown. The profile warns at 85 C, stops at
90 C for ten seconds and aborts on observed thermal throttling; those readings are not
a guarantee of safe operation for every workload. Other runs retain the default.
Between heavy stages use fresh
admission; if still hot, wait rather than immediately starting the next shot. Do not
declare a day-long load safe from a short benchmark or change thermal limits automatically.

## Free online generation

The owner allows verified free online tools. Local is preferred when it meets quality
and time requirements. A genuinely free tool may be chosen for better quality or to
avoid an infeasible local load; it need not wait for an OOM. No paid provider, subscription,
credit purchase, billing enablement or quota bypass is authorized.

- **Pomelli** is Google's marketing-creative web application. Its official help currently
  describes no-charge image/video generations. Verify region, sign-in and the account's
  current free allowance in the real UI before submitting; do not invent a Pomelli API.
  Use the browser tools for an available signed-in session, or report the exact login/
  account blocker. Do not publish or post the resulting reel automatically.
- **Gemini** is configured for review with the owner's key in ignored `.runtime/watch/.env`.
  It is not permission to call paid Gemini image/video models. Check model availability
  and the confirmed free-tier flag. On quota/auth/network failure, fall back visibly to
  local frame/transcript preparation plus assistant review, with no claim Gemini reviewed it.
- **Open Higgsfield** is a Next.js client for external model APIs and public asset uploads;
  self-hosting its interface does not run those models locally or make generation free.
  Do not install it as a local diffusion engine or upload assets without the required permission.
- **HyperFrames** is an alternative HTML renderer. Consider it when its authoring model
  materially improves a brief; benchmark a representative scene under the same guard
  before changing the primary renderer. Do not run both renderers for every scene.
- **VoiceStudio** is optional for cloning/dubbing beyond Kokoro. Validate one needed engine
  in a separate guarded process before adopting it. OpenWhispr is unnecessary for the
  automated pipeline's existing timestamped transcription step.

Record provider, model, prompt, input references, output resolution/duration and any
watermark/use restrictions for each imported asset. Free access is account-dependent and
time-dependent; verify it when used. A provider failure returns to local options or an
owner decision, never silently to a paid service.

Primary references:
- https://github.com/zai-org/CogVideo#model-introduction
- https://github.com/Wan-Video/Wan2.1
- https://github.com/lllyasviel/FramePack#requirements
- https://support.google.com/labs/answer/16715058
- https://github.com/wide-trace/open-higgsfield
- https://github.com/heygen-com/hyperframes
