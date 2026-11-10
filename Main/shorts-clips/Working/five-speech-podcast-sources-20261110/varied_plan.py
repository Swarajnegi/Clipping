"""Frame-reviewed replacements keyed by their existing cutaway slots."""
from varied_candidates import K, LUKE, MATT, STEVE, TYLER, WALTER

CHANGES = {
    "01": {
        2: (LUKE, "luke-beside-the-red-workbench", .26, .35,
            "The mechanic at his tool chest makes the planning line feel practical."),
        6: (STEVE, "wide-view-of-the-team-workspace", 2.71, .58,
            "The team discussion bridges from a single work station to leading a group."),
    },
    "02": {
        3: (MATT, "two-figures-facing-off-in-rain", .26, .51,
            "A single exchange makes his question about individual points concrete."),
        4: (TYLER, "tyler-spars-in-parking-lot", .36, .56,
            "The back-and-forth of the sparring sells the idea that skill does not mean winning every exchange."),
        5: (LUKE, "luke-catches-his-breath-on-the-floor", .20, .45,
            "Taking a breath after a setback illustrates losing a point without carrying it forward."),
    },
    "03": {
        2: (K, "lone-figure-crosses-the-orange-desert", .40, .50,
            "The walk across open terrain visualizes purpose reaching beyond one role."),
        4: (MATT, "matt-by-a-daylight-window", 1.04, .31,
            "The quiet look across the room gives the line about a particular moment a human face."),
    },
    "04": {
        2: (K, "equipment-on-a-lit-work-table", 1.69, .48,
            "The hand brings a physical piece into the frame as Rubin describes something missing."),
        4: (WALTER, "hands-at-work-in-low-light", 1.08, .50,
            "A practical task underlines the line about someone having to do the work."),
        5: (STEVE, "figure-crosses-a-shadowed-workspace", 1.61, .50,
            "The walk between the benches puts motion under Rubin's decision to make it himself."),
        6: (K, "hands-hold-a-small-object-in-amber-light", 3.06, .52,
            "A person handling the tiny carved figures illustrates care for the finished object."),
    },
    "05": {
        1: (K, "joi-reaches-toward-officer-k", .06, .51,
            "The early reach makes the risk of asking for help visible."),
        3: (LUKE, "woods-conversation-reverse-angle", .34, .66,
            "The private conversation matches a friend finally admitting that he has struggled."),
        4: (MATT, "matt-in-a-low-lit-close-up", 3.19, .45,
            "Matt's lowered gaze illustrates the hesitation in I didn't want to bother you."),
    },
}

PLACEMENT = {
    ("02", 5): (540, 1250),
    ("03", 4): (540, 1210),
    ("05", 3): (310, 1010),
}

WRAPS = {("05", 3): {"I've been struggling": 2, "why didn't you call me": 3}}
