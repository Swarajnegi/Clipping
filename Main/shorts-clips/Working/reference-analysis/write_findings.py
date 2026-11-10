"""Materialise the assistant's inspected reference findings alongside raw evidence."""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
NOTES = {
"bd696e66727f": ("Andrew Tate; duty to family and legacy", [
 [0,2,"Anime boxer opens while original-speaker speech starts immediately; wide horizontal band on black."],
 [2,7,"Cut to Tate in sunglasses; small white uppercase phrase captions sit inside the picture, across torso."],
 [7,8,"Anime bed cutaway illustrates inactivity; speech continues across the visual cut."],
 [12,14,"Anime victory cutaway illustrates achievement; return to a wider interview shot around 14s."],
 [17.7,24.68,"Final challenge about parents resolves into being remembered; anime inserts near 20s, then speaker close-up to end."]],
 "Use illustrative cutaways at semantic beats, retain original voice, avoid a narrated preamble. Sampled caption size is restrained; exact font/grade remain unmeasured."),
"8e0acc5fd0ac": ("Andrew Tate; focus on worthwhile work", [
 [0,5.1,"Direct admonition, close portrait framing, small sentence-case white captions near upper torso."],
 [6.64,10.88,"Repetition culminates in work works; no sampled visual cutaway."],
 [11.22,12.77,"Rhetorical question closes; last sample dims."]], "Short direct-address material can work without extra context or montage."),
"80786a7729fb": ("Tristan Tate; age as achievement rather than years", [
 [0,11,"Voice-led montage: purple suit, selfie, jet/KFC and car; visuals illustrate the nouns in the story."],
 [12,27.72,"University/job/property comparison; house footage then return to selfie."],
 [27.72,35.86,"Past-versus-present reversal; switch into warm stairway/suit footage."],
 [35.86,48.60,"Return to selfie for concluding definition; small uppercase captions remain central."]], "Seek a personal reversal with a concrete low point and a changed interpretation; montage supports the story."),
"d5ee97392fa9": ("Tristan Tate; self-reliance and a small trusted team", [
 [0,13.02,"Repeated nobody-cares claims; single seated interview shot with small English captions and oversized clipped Italian subtitles."],
 [14.64,21.78,"One or two close people form the team; holds the seated speaker."],
 [22.1,27.14,"Ending imagines the viewer returning to tell the success story."]], "Keep the rhetorical progression and supportive ending; use a clean original rather than this already-captioned copy."),
"c73aba692323": ("Andrew Tate; decisions versus feelings", [
 [0,4.44,"Wide horizontal talking-head band on black; Real. title types on above picture."],
 [4.44,12.12,"Concrete examples: gym, food, drink; white uppercase sentence captions near chest."],
 [12.34,23.40,"Rebuttal and return to action regardless of mood; same sampled angle."]], "Prefer concrete behavioural examples over vague motivation; the Real. heading is a reference detail, not a required brand element."),
"9988184cc3c2": ("Tristan Tate; trust revealed by difficult times", [
 [0,2.86,"Question hook over suit/hat imagery."],
 [2.96,10.54,"Answer carries across suit, event, interview and jet imagery; small white phrase captions."],
 [10.88,15.63,"Turns from disappointment into identifying real trust; ends on Andrew smiling."]], "Question-to-answer-to-reframe is a useful compact story shape."),
"42ba7e114875": ("Andrew Tate; effort and an exaggerated bag-of-blessings metaphor", [
 [0,10.08,"Direct address in purple-lit jet cabin; bold italic uppercase phrase captions."],
 [10.08,23.84,"Metaphor accompanies expressive hands and delivery; continuous speaker image."],
 [23.84,28.10,"Concluding explanation delivers the punchline to the metaphor."]], "Retain a colourful metaphor and expressive delivery; no need to cut away from a good performance."),
"144791ab5d56": ("Cristiano Ronaldo; discipline and consistency", [
 [0,13.46,"WHOOP-style interview framing alternates close and wide; small sentence captions inside picture."],
 [13.46,31.7,"Challenge to consistency and the gym example resolve the spoken argument."],
 [32,61.21,"Long football celebration/performance montage follows speech; captions mostly disappear."]], "Athlete discipline fits the content taste. The long sports montage is a taste example, not the default 25-second target structure."),
"f59b86fe347f": ("Chris Bumstead on Modern Wisdom; children see who their parents really are", [
 [0,21.5,"Seated dark-toned podcast shot, moderate black bars, small white phrases; starts without a host question."],
 [21.5,36.6,"Punch-in to face during personal accountability point; no sampled unrelated b-roll."],
 [36.6,42.81,"Contrast public image with home behaviour; ends in an abstract blurred graphic."]], "A thoughtful, complete argument belongs beside harder delivery; preserve the change from observation to accountability."),
"8cade4740882": ("Andrew Tate; incentives behind rules", [
 [0,8.9,"Warm interview with microphone; medium picture band on black and white uppercase captions; BASEDTATES watermark."],
 [9.76,17.58,"Enumerates education and instructions under a steady shot."],
 [17.9,23.22,"Conclusion identifies rules with the people who make them."]], "If selecting this theme, preserve it as the speaker's opinion and include enough antecedent context to explain them."),
"4ae595218838": ("Andrew Tate; fully attending to emotions instead of half-distraction", [
 [0,10.72,"Full portrait lifestyle montage: meal, car, training and phone; small uppercase captions below centre."],
 [10.72,23.8,"Friends, walking and woman cutaways illustrate the examples; sampled dissolves overlap several changes."],
 [23.8,35.46,"Car monologue becomes visual anchor for the conclusion; final caption/speech may be cut mid-thought."]], "Do not imitate a truncated ending; seek the complete final sentence in the original."),
"ec82ce1649ad": ("Andrew Tate; no shortcuts, illustrated through sparring", [
 [0,9.94,"Seated laptop monologue in a horizontal band; persistent title above it, italic small captions inside."],
 [9.94,30.46,"Sparring anecdote establishes why advice cannot replace training; uninterrupted sampled shot."],
 [35.68,52.7,"Generalises daily work to gym, fighting, guitar and business."],
 [54.9,67.13,"Rhetorical challenge extends the point; source is much longer than the two style targets."]], "Use the sparring analogy as one focused short rather than carrying the entire monologue."),
"7cd84cd7251d": ("Tristan Tate; nostalgia and a changing world", [
 [0,12.44,"Portrait montage of architecture, cars and brothers; bold white uppercase phrases near upper torso."],
 [12.44,22.96,"Watch and lifestyle details alternate with seated speaker; voices include a reply."],
 [22.96,33.90,"Money-versus-memory contrast resolves into Luton being gone; ends on walking/tunnel montage."]], "Two-speaker exchanges can supply a counterpoint; preserve who says what and keep the nostalgia payoff."),
"e70b09933e41": ("Andrew Tate; ten ambitious actions and commitment", [
 [0,2,"Thin horizontal strip expands into a steady wide speaker band on black; original speech starts immediately."],
 [2,10,"Mostly small central phrases; guaranteed and 100% expand into large mixed-weight typography at the right."],
 [12.9,19.12,"Keep, high and yourself receive typographic emphasis while the picture stays on the speaker."],
 [23.58,26.68,"Large turquoise 2026/end-card wording enters behind/right of speaker; finishes with future-year promise."]], "Use semantic typography and selective word emphasis, not constant word-pop. Adapt dated year promises to the actual source; do not fabricate new speech."),
}

inventory = json.loads((BASE / "inventory.json").read_text(encoding="utf-8"))
report = ["# Reference study — 1 November 2026", "",
"All 14 originals were inventoried and processed through the guard. Full files were passed to CUDA speech transcription, and all generated one-second frame sheets were inspected by the assistant. This is a transcript-and-sampled-visual study, not continuous audiovisual playback. Exact cut frames, animation curves, music, sound effects, beat alignment and mix levels remain unverified. Gemini's first request returned HTTP 500; no provider assessment was obtained. Song titles and slowed/sped-up variants are unidentified. FFprobe found no title, artist or album tags in any of the fourteen WhatsApp files. See cloud-receipt.json for upload cleanup status.", "",
"The reference folder remains unchanged. Transcript recognition contains errors; findings below use visible captions where they clarify the words. ASR errors include 'saying a humbling video game' in target A and a disputed year in the nostalgia reference. These require original-source checks before final captions.", "",
"## Editing profiles", "",
"**Target A — restrained illustrated monologue (11.54.55).** Wide band on a black 9:16 canvas, original speaker first, tiny white uppercase phrase captions inside the picture, purposeful anime cutaways, direct challenge and a resolved final line. Keep the serious delivery and use cutaways to represent the spoken idea. Anime/other b-roll needs its own reuse basis. The optional referenceEdit layout now supports a wide band, restrained captions and muted multi-source cutaways. Default dimensions/fonts remain an approximation requiring acceptance against this reference.", "",
"**Target B — speaker plus kinetic typography (11.58.27).** Wide band on black with an opening expansion, direct speech throughout, restrained base captions and larger mixed-weight key phrases. The emphasis follows ideas (certainty, effort, commitment, year), rather than animating every word identically. The optional kinetic referenceEdit layout now supports timed emphasis with independent position, size and italic styling. The precise font, opening expansion and choreography still require motion acceptance before claiming an exact visual match.", "",
"**Content priorities observed:** practical discipline, meaningful work, parents/legacy, trust, self-reliance, uncomfortable personal stories and reflective contrasts. The Cristiano and Williamson examples demonstrate that creator matching alone is insufficient. No reference proves virality or audience demographics.", "",
"## Per-reference findings", ""]
for row in inventory["files"]:
    folder = BASE / row["evidence_dir"]
    theme, events, rule = NOTES[row["evidence_dir"]]
    sheets = sorted(p.name for p in folder.glob("sheet-*.jpg"))
    transcript = json.loads((folder / "transcript.json").read_text(encoding="utf-8"))
    findings = {"inspected_at": datetime.now(timezone.utc).isoformat(), "identity": row,
                "theme": theme, "observations": [{"start":a,"end":b,"finding":t} for a,b,t in events],
                "editing_rule": rule, "coverage": {"transcript_read": True, "sheets_inspected": sheets,
                "visual_cadence_seconds": 1, "continuous_playback": False, "direct_audio_listening": False},
                "music": {"song": None, "variant": None, "status": "unidentified", "mix_level_measured": False},
                "uncertainty": ["ASR wording requires verification", "Subsecond motion/cuts and audio/music not directly inspected"]}
    (folder / "findings.json").write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding="utf-8")
    report.extend([f"### {row['file']}", "", f"{row['duration']:.2f}s · {row['width']}×{row['height']} · {row['rate']} · {row['role']}", "", f"**Content:** {theme}", ""])
    report.extend(f"- {a:.2f}–{b:.2f}s: {t}" for a,b,t in events)
    report.extend(["",f"**Editing lesson:** {rule}","",f"Evidence: [{row['evidence_dir']}]({row['evidence_dir']}/findings.json); all {len(sheets)} sheet(s) inspected; full ASR transcript in transcript.json. Audio/music limitations above apply.",""])
(BASE / "REFERENCE_STUDY.md").write_text("\n".join(report),encoding="utf-8")
