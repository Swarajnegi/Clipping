# Rounded-square framing and native 4K acquisition

Owner instruction, 8 November 2026: future vertical edits should use the supplied
squarish frame; horizontal framing remains appropriate when it better serves a shot.
This changes framing, not the approved caption animation, all-word Difference,
italic accents, clean dialogue or no-foreign-branding requirements.

## Reference evidence

Supplied file: `chriswillx2026_11_08_16_54_187e9fb175-56bf-4d3c-b649-b70f90d123ce.mp4`
under the project's `.codex-attachments`. It is a 720×1280 H.264 file, 30 FPS,
1993 video frames; container duration approximately 66.57s. This compressed style
reference is not a 4K production original.

Frames inspected: 1, 10, 20, 30, 40, 50, 60 and 65 seconds. The seven content
samples show a consistently centred, approximately 654×654 picture, left near
33px and top near 313px, with rounded corners around 30–32px and black surround.
The 65s sample is black; do not copy this tail into our edits. Both talking-head
and illustrative passages retain this square window. These are sampled visual
observations, not continuous playback/audio inspection. Evidence, individual PNGs,
and measurement receipts: `Main/shorts-clips/Working/reference-analysis/squarish-20261108`.
Guard: `9b3d04038bbb452bb63a945d7c46caa5`, worker succeeded, cleanup confirmed.

## New vertical project setup

Use a 1080×1920 logical design canvas and 2160×3840 delivery:

```json
{"referenceEdit": {
  "profile": "editorial", "layeredOnly": true,
  "frame": {"x": 50, "y": 470, "width": 980, "height": 980, "radius": 48},
  "layers": []
}}
```

This is geometry only. Add real timed caption layers before validation; empty
editorial layers are rejected. Apply the white Difference preset as specified
in the [caption guide](editorial-captions.md).
Keep visible words within the picture's rounded bounds, with comfortable inset;
the frame is x=50–1030 and y=470–1450 at logical resolution. Follow actual empty
space and movement. The owner's later 8 November correction centres the complete
caption block near logical (540,960), the shared centre of this square and canvas.
The subsequent owner clarification allows placement in other genuinely empty areas
for visual appeal and readability. Centre is the default, not a compulsory anchor
in every shot. Adjust framing/shot choice and whole-phrase placement to keep faces
and meaningful gestures clear. Check the crop before and after each source angle
change. An interview two-shot may need a speaker-focused crop when the line
belongs to one person. This supersedes the older
bottom-centre starting placement for new channel edits. Existing mask points and captions use the
same global logical coordinates, not coordinates relative to this inset box.

The renderer uses the same frame for speaker footage, synchronized foreground
duplicates and cutaways. Landscape sources are cropped to fill the square; portrait
sources are cropped vertically. Inspect face, hands, source branding and scene
changes throughout; tune shot centres rather than accepting an automatic centre
crop. Avoid excessive zoom. All source cuts still preserve timing and dialogue.

For a passage that benefits from horizontal picture space, author an explicit
wider frame and crop plan. Black 9:16 surround may remain for Shorts/Reels. A native
horizontal deliverable can be chosen by the brief, but the current ViralShort
composition itself is 9:16; do not claim that changing the inset makes its output
16:9. Retain that distinction in delivery notes.

The new `referenceEdit.frame` takes precedence over `bandHeight`. Omitting it
preserves legacy band behavior; full-height and previously approved projects keep
their authored geometry. New specs must explicitly author the square or their
justified horizontal alternative rather than relying on an old band default.

## Source and output resolution

- Production download target: supported native UHD/DCI 4K, including portrait 4K,
  preserving source FPS. Resolution outranks MP4/H.264 preference: supported VP9
  4K beats H.264 1080p. Do not request 8K unnecessarily.
  Wider originals such as 3840×1920 are valid 4K-width sources at their native
  aspect ratio, not 1080p. Record `native_4k_wide_aspect` and actual dimensions;
  do not describe them as 3840×2160 UHD. A square crop retains at most their
  shorter side before further zoom (1920×1920 in this example).
- This RTX 2060 host cannot hardware-decode AV1. Select a compatible original
  format first. If only AV1 offers 4K, report that limitation and the supported
  lower resolution; do not silently use a CPU decoding fallback.
- Preserve the original dialogue track. Keep `lang` ahead of bitrate in forced
  yt-dlp sorting; a higher-bitrate automatic dub is not the speaker's original
  audio. Retain selected audio language/format-note evidence. For these English
  interviews, verify the original English track and compare its wording with the
  source transcript before cutting. The Jimmy Carr batch exposed this issue;
  its dubbed download was preserved UNUSED and original English restored.
- `prep.py` records actual decoded dimensions and `source_quality`; it rejects a
  known cached sub-4K master when compatible 4K is available. Preserve the old
  work directory and use a new `--work-id`. A source listing is not proof the
  downloaded media is 4K: probe the actual file before expensive work.
- Metadata and cheap context windows/proofs can remain lower resolution for
  discovery. Label them as research/proof assets. Acquire the selected original
  4K passage before final rendering; preserve canonical URL, format identity,
  source range, actual dimensions, native FPS and reuse basis in project records.
- For sources whose highest accessible compatible original is lower resolution,
  report the limitation before finishing. Never describe an upscale as recovered
  native detail. The owner's request does not make unavailable source detail exist.
- `build.py` defaults to `--output-scale 2` (2160×3840). Use scale 1 for a cheap
  proof or an explicit lower-resolution request. The design canvas remains
  1080×1920, so fonts, masks and frame coordinates are scaled together.

A square crop from a 3840×2160 landscape master retains up to roughly 2160×2160
source detail before further zoom. In the default 4K canvas its picture window is
1960×1960. State source resolution, retained crop and export resolution separately;
black canvas pixels and 4K typography do not add camera detail.

No automatic retroactive downloads or rebuilds of older approved exports. All
download/processing stages retain the existing guards, permissions and provenance.
