# Editorial captions: reference-led default

Owner-approved on 3 November 2026. Reference: [The Nicks Edit tutorial](https://www.youtube.com/watch?v=uAga_kBywLM).
This guide governs caption treatment, not content selection or permission to reuse assets.

For thought.palace, captioning is the final editing step: begin caption design,
placement, timing and rendering only after the source speech, B-roll, any
chosen song timing, picture cuts, transitions and SFX are locked.
Use the existing beat map when composing captions. Follow the
[owner-led workflow](owner-led-edit.md).
Use vertical stacks beside a subject when the clear space is tall and narrow,
ordinary horizontal phrases when the frame gives them width, and centred
compositions when the picture allows. Check the full stack as words reveal.

**Owner update, 8 November 2026:** Difference blending is required on every caption
word in every future video, including supporting text and italic accents. This replaces
the earlier selective-use/solid-fallback advice. Only an explicit owner exception changes
that requirement; existing approved exports are not retrofitted without a request.

**Placement clarification, 8 November 2026:** default to centring the whole caption
composition in the picture (logical 540,960 in the current rounded-square layout).
Other genuinely empty areas are allowed when they improve the visual composition
and readability. Decide per shot/phrase, check movement, faces and meaningful
gestures, and keep word positions stable while the phrase builds. Centre placement
does not override face clearance; this changes position, not the all-word Difference
treatment. Opening treatments and final covers follow [hooks and thumbnails](hooks-and-thumbnails.md).

## Evidence and intended appearance

| Reference time | Demonstrated technique | Apply to our edits |
|---|---|---|
| 0:00–0:22; 21:07–21:28 | Final-result previews: bracketed key words, stacked phrases, changing hierarchy and spatial placement | Match the typography and motion language, without the creator's watermark, film clips or music |
| 1:52–2:17 | SF Pro Display Bold, tracking around -50 in Premiere | Use bundled upright Inter Bold, an explicitly agreed visual substitute; start at -0.05 em tracking and tune by eye |
| 2:34–3:31 | Small setup, medium supporting words, largest bracketed emphasis | Author balanced phrase compositions; reserve the largest type for the actual payoff |
| 3:54–4:13; 10:49–11:23 | Individual text layers timed to the speaker | Check every word onset against dialogue; preserve the full spoken wording |
| 9:24–10:00; 10:41 | Gradients with Screen and Color Dodge; Difference shown at 4:59 | Historical blending reference; the 8 November owner instruction now requires white-fill Difference on all caption words |
| 12:05–12:58 | Basic 3D tilt, swivel, rotation and placement | Selective perspective on emphasis, not constant movement on every word |
| 13:21–14:00 | Duplicate foreground video masked over text | Put selected text behind the speaker using a synchronized, muted foreground duplicate and checked masks |
| 19:15–20:21 | Creator's private motion presets | Recreate observable motion independently; never claim possession of the presets or an exact proprietary curve |

Coverage: full transcript inspected, plus sampled opening/final-preview frames. This is
not a claim of continuous audiovisual inspection of the entire 21-minute tutorial.
The font and independent easing are known differences from the example.

### Two short owner references, supplied later on 3 November

Preserved originals and inspection evidence live under
`Main/shorts-clips/Reference/captions-20261103` and
`Working/reference-analysis/captions-20261103`. The inventory records file hashes.
The first supplied file is the one with `(1)` in its name; the second has no suffix.

- **First, 14.14s:** font labels appear at about 5s (Sequel Sans Heavy), 6s
  (Roundhand), 7s (Deutschlander), 8s (Outerion), and 9s (Sinethar). The intro and
  ending also demonstrate bold sans text layered with a larger script accent.
- **Second, 21.38s, especially 10–13s:** letters crossing green leaves turn
  pink/purple while other portions remain gray or dark. At 11.1s, `get a`
  demonstrates different colours within a single word; at 12.4s `shot` retains
  texture through its letterforms. Other bright-background shots also show dark text.
  This is consistent with Difference blending, rather than simply translucent white.
  The project settings were not supplied: the exact blend/opacity is an inference.
- Coverage: full-duration 0.5-second sheets visually inspected for both files;
  the requested 10–13.2s interval additionally sampled at 0.1s and inspected at key
  colour changes. Audio was not needed for identifying these visual treatments and
  was not independently reviewed. Do not label this a complete audiovisual study.

### Colour-reactive text preset

Set `surface: "difference"` explicitly on every spoken-caption layer unless
the owner has requested a specific exception. It defaults to a white
solid fill, `blend: "difference"`, full `fillOpacity: 1`, and `shadow: "none"`.
The actual footage supplies the colour and texture: white-minus-green produces
pink/purple, while white-minus-pale backgrounds produces dark letters. This is a
blend response, not blur or physical glass refraction. There is no fixed pink tint.

```json
{"t": 10, "dur": 0.8, "text": "grow", "x": 100, "y": 900,
 "width": 880, "size": 104, "font": "inter", "surface": "difference",
 "fillOpacity": 1, "motion": {"inSec": 0.12, "blur": 4}}
```

The owner's proof is `Working/reference-analysis/captions-20261103/surface-proof-phone.png`:
the middle panel shows full Difference; the lower panel shows a softer 65% mix.
Start at full strength; `fillOpacity: 0.65` is the pictured softer alternative.
Tune a positive effect strength for the footage without leaving any words untreated.
`fillOpacity` mixes the effect with the original picture. The renderer supports
`color`, `gradient`, `blend` and `shadow` overrides. For the Difference preset use
white `color: "#ffffff"`, no inherited silver gradient, and Difference blending.
Omit `blend` or set it to `"difference"`; do not inherit `"normal"` from an old layer.
Inspect the whole word
across the actual moving background. Do not isolate the caption on an opaque card:
it must blend against the source picture, not a black intermediate backdrop.
The owner prefers the clean Difference finish. Keep the approved shadow-free
Difference layers and check skin, white clothing and moving highlights at phone
size. Normal shadows on the legacy solid treatment remain strong by default.
If the result loses readability, adjust placement, size, weight, hold or positive mix
strength while retaining Difference on every word. Do not silently fall back to solid
text. Check the actual shot, keeping faces clear and respecting phone-interface bounds.

### Selective weight, size and typeface

The 1 November `11.58.27 AM` reference uses a flowing italic accent on "high"
around 16–17s, contrasted with upright, heavier emphasis elsewhere. The exact
reference font remains unidentified. Keep the bold Inter base and selectively accent
meaningful words or short phrases; do not italicize every caption or duplicate branding.
Mark the words that carry a hook, turn or payoff. Make selected words clearly
larger or heavier than their neighbors, or use an occasional contrasting licensed
font. Measure the changed word widths and reserve their places before they appear.
Supporting words keep the established Inter hierarchy. Keep timing and Difference
consistent across styles.
For a similar serif contrast, use bundled `font: "cormorant", italic: true`, weight
300–700 (start at 700). Cormorant Garamond Italic is an explicitly documented visual
substitute, not an exact font identification. `font: "inter", italic: true` uses
Inter's real italic face when a sans italic fits better. Both are OFL-licensed assets;
retain the bundled licences and source/hash receipts. Never activate the personal-use
reference downloads for production. Recheck the actual italic glyph bounds, word timing,
and phone-size readability, especially thin serif strokes and overshoots.

Verify the chosen surface on the actual footage, including supporting words and
italic layers. The synthetic leaf chart shows the preset, not its appearance in
an edit. A designed transition card is a separate graphic. A requested solid
white payoff applies only to the named phrase, as with Cavill's “to be Fair.”

### Other reference fonts and exact availability

| Label in the first file | Verified source / present status |
|---|---|
| Sequel Sans Heavy | [OGJ Type](https://ogjtype.com/font/sequel-sans/) sells Sequel Sans. No licensed local file was supplied; not downloaded from unofficial font mirrors. Historical Heavy naming must be matched to the purchased version. |
| Roundhand | The reel does not identify the foundry/version. [Roundhand BT](https://www.myfonts.com/collections/roundhand-font-bitstream) is one commercial candidate; exact identity remains unresolved. No file downloaded as an assumed exact match. |
| Deutschlander | [Sharkshock's author listing](https://www.dafont.com/deutschlander.font). Personal-use download saved with its readme; no channel-production licence recorded. |
| Outerion | [Rantautype's author listing](https://www.1001fonts.com/outerion-font.html). Personal-use download saved with its readme/EULA; no channel-production licence recorded. |
| Sinethar | [Hanzel Space's author listing](https://www.dafont.com/sinethar.font). Personal-use download saved with its readme; no channel-production licence recorded. |

The three downloaded packages are in the study's `font-downloads` directory, with
SHA-256/source receipts in `downloads.json`. They are reference downloads, not installed
Windows fonts, not bundled in the production public directory, and not activated in
the renderer. Use the cleared bundled Inter and Cormorant faces until appropriate
licensed originals are provided. Download availability does not make a personal-use font production-ready.
Do not substitute another font silently or copy the reel's third-party media assets.

## Authoring and rendering

Use `referenceEdit.profile: "editorial"`, `layeredOnly: true`, and manually authored
`layers`. Author `referenceEdit.frame` per [framing and source quality](framing-and-source-quality.md)
and set the `shots` crop for the actual speaker and source cuts.
Keep old authored layouts intact. Other layouts remain
available when a brief needs them. Never force text across faces to preserve a template.

Each layer keeps the existing `t`, `dur`, `text`, `x`, `y`, `width`, `size`, `align`,
`weight` and optional `wordTimes`. Coordinates are output pixels on 1080x1920;
times are seconds in the assembled clip. New editorial controls:

- `font: "inter"`, weight 100–900 (default 700); optional `italic: true` loads
  `InterVariable-Italic.woff2`, not browser-synthesized slant. `font: "cormorant"`
  requires `italic: true`, weight 300–700, and loads `CormorantGaramond-Italic.ttf`.
  Asset source and SHA-256 live
  in `assets/fonts/provenance.json`; retain `LICENSE.txt`. Stage the exact bundled font
  at `public/fonts/InterVariable.woff2`, with any requested italic assets alongside it.
  Retain `Inter-LICENSE.txt` and `Cormorant-OFL.txt` when staging their respective faces.
  Font loading blocks frame capture until every requested face is ready.
- `tracking` in em (default -0.05), `lineHeight` (default 0.94), `color` for a solid
  fill or `gradient` for CSS gradient stops. The legacy solid preset defaults to a
  white-to-silver gradient; new channel captions explicitly use white Difference.
- `blend`: `normal`, `screen`, `difference`, `color-dodge`; `glow` in pixels.
- `surface`: `solid` (existing silver treatment) or `difference` (the owner’s new
  colour-reactive reference); `fillOpacity` is a finite number from 0 to 1.
- `shadow`: `strong` (legacy solid default), `soft`, or `none` (Difference default). Strong combines a
  tight dark edge shadow with a softer cast shadow, so white text remains readable
  on white clothes or bright backgrounds. Inspect at phone size. Do not substitute
  a white glow for contrast; reduce glow when it weakens the dark separation.
- `motion`: `inSec`, `outSec`, `rise` in pixels, `scaleFrom`, `blur` in pixels,
  `easing` (`cubic`, `expo`, `linear`). Defaults: 0.20s in, 0.08s out, 28px rise,
  0.92 scale, 10px blur, cubic ease-out. These are our starting settings, not measured
  values from the private preset. Adjust by comparison with the visible example.
- `perspective: {distance, rotateX, rotateY}` and existing `rotate` for Z rotation.
- `depth: "front" | "behind"` and `z` within that plane. Keep z between 0 and 999.

With `wordTimes`, the complete text reserves its final layout while individual spans
animate at their own timestamps; previously visible words must not recenter or jump.
For mixed font sizes or unusual compositions, author one word/phrase per layer with
explicit positions. Phrase composition is an editorial task, not automatic random sizing.

A progressive top-to-bottom build is a sequence of fixed rows. Reveal the first
line at the top on its words, hold it while the next lines appear below, and
clear the group together at the next thought or incompatible picture cut.
Use independent layer positions and a shared end time. Vertical entrance
animation is a separate choice. Fit the widest completed group and its motion
inside the picture. Start large enough to read on a phone and use a larger
key word where the shot has room. Tighten spacing so a payoff such as
“to be” and “Fair” reads as a single phrase.

For [movie cutaways](movie-cutaways.md), keep Inter Bold for supporting words and
reserve visible size or weight changes for spoken hooks, turns and payoffs. Use
bundled Cormorant Italic selectively. Plan the entire phrase for the moving shot,
then lock its word positions. Reposition at a shot or phrase boundary when the
picture changes. End outgoing caption fades at picture cuts when the old placement
would overlap the incoming subject. For low contrast, try clean negative space or
a subtle darkening of the picture under the text while retaining white Difference.

Behind-subject layers require `foregroundMasks` covering their complete intervals:

```json
{"t": 0, "dur": 1.2, "keyframes": [
  {"t": 0, "points": [[400,300],[680,300],[740,1000],[320,1000]]},
  {"t": 1.2, "points": [[410,300],[690,300],[750,1000],[330,1000]]}
]}
```

These are illustrative vertices, not a usable person mask. Points use output canvas
coordinates in clockwise order; keep identical vertex correspondence and count across
strictly ordered keyframes. Interpolate only inside a shot. Use separate mask intervals
across source cuts. The foreground uses the same video frame, framing, grade and motion
as the base, with audio muted. Inspect all overlap frames, including hair, shoulders and
hands; add keyframes when the outline changes. Do not use a large rectangular cutout.

## Acceptance and reuse

Before the full render, inspect stills at phrase starts, settled emphasis and every
mask transition. Check each fully revealed group and the frames before and
after every caption or picture change. Check the word's final glyph, group
overlaps, mask coverage through motion, and outgoing fades over cards or new
shots. If a mask clips a word, move the group into clear space or refine the
mask. Do not leave partly obscured letters. Then review the complete output
with sound when available. Check word onsets against actual dialogue within
one source frame where verified, stable typography, readable emphasis, crop changes, and
safe placement against Reels/Shorts UI overlays. Check light clothing and bright areas
specifically: the owner previously flagged the Ronaldo “life” payoff over a white shirt.
Under the current all-word Difference rule, solve separation with framing, typography
and mix strength while preserving the effect. Check every non-exempt caption layer for
`surface: "difference"`, a white fill without an inherited gradient/normal blend, and
a positive effect mix; sample every phrase and source cut for the visible response.
Selective occlusion may establish depth,
but must not hide enough of a key word to prevent reading it.

Rebuild from clean footage and the transcript, never a captioned export. Preserve the
approved source range and audio unless the brief changes them. For caption-only revisions,
stream-copy the approved dialogue when timing is identical and compare audio packet
hashes/timestamps. Preserve earlier exports and save a versioned revision with QA evidence.

All existing resource guards, reuse-basis records, music-free delivery and own-channel
branding rules apply. This style does not require Premiere, FilmCraft, paid presets,
new services, provider uploads or model installations.
