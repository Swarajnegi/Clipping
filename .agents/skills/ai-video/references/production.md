# Storyboard and continuity

The local compositor accepts JSON through `scripts/ai_video.py plan|render <file>`:

```json
{
  "id": "cache-explainer",
  "backend": "illustrated",
  "title": "How a cache saves work",
  "fps": 30,
  "narration": "Optional narration synthesized locally with timestamped captions.",
  "voice": "am_michael",
  "scenes": [
    {"duration": 6, "heading": "Remember the result", "body": "Reuse it until the input changes.", "accent": "#82e6cb"},
    {"duration": 6, "heading": "Skip the repeated work", "asset": "D:/J.A.R.V.I.S/Clipping/work/ai-video/cache-explainer/cache.svg", "kind": "image"}
  ]
}
```

`backend: illustrated` is the compositor, including films assembled from generated video
assets. Each asset must exist on D under JARVIS. `kind` is image or video; video audio is
muted, with one continuous narration track. Add source sound/music explicitly in the
composition when the brief calls for it, then validate the mix. Do not silently discard
requested source audio. Narration must fit the total scene duration; the renderer fails
instead of cutting speech off. Generated-shot FPS and resolution are recorded separately
from the final delivery profile (default 1080×1920/30 FPS); upscaling does not create native detail.

`backend: local-diffusion` is a feasibility request, not an installed generator. The planner
returns `needs_benchmark` until a real local profile exists. Never hand-edit a profile to
mark a model certified. Generated footage is imported into the illustrated compositor
after its separate inference worker and quality checks pass.

## Asset and scene design

- Write one style/continuity brief for the whole film. Keep character reference images,
  wardrobe, scale, palette, lighting, environment, voice and camera direction consistent.
- Use Anatomy for technical mechanisms, not for drawing people or every diagram. Read
  its craft, motion and verification references. Import a properly exported SVG or port
  its geometry to a deterministic React scene; pointer-driven wall-clock animation is
  not automatically a video timeline.
- Drive all video motion from frame time. Avoid CSS animations, unsynchronised browser
  physics, random values per render and unseeded noise. Inspect identical frames twice
  for more complex SVG/WebGL or third-party assets.
- The same narrator, music bed, grade, typography and caption placement bridge scenes.
  Use intentional cuts and matched action/composition. Use end/start frame conditioning
  only when the actual model supports it; do not invent flags.
- For resource splitting, retain a shared brief and timebase, overlap handles when useful,
  and inspect both sides of every join. Do not hide an identity or geometry change with
  a crossfade and call it continuous. If acceptable continuity cannot be achieved within
  the budget, explain the limitation and offer illustrated or editorial alternatives.

## Output acceptance

Keep partial outputs separate and only publish the final MP4 after stream/duration/FPS
validation and actual encoder verification. Review QA frames and listen to speech/music,
including every join. Keep the input storyboard, generated asset provenance, render log,
resource log and receipt so another session can resume completed work without regenerating it.
