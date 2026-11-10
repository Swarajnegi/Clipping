"""Scout exact library files for the five private-review cutaway revisions."""
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
WORK = P / "movie-cutaways-varied"
LUKE = "Luke Glanton - The Place Beyond the Pines"
K = "Blade Runner 2049 - Officer K"
MATT = "Daredevil - Matt Murdock S02"
STEVE = "Avengers Endgame - Steve Rogers"
WALTER = "Breaking Bad - Walter White S05A"
TYLER = "Fight Club"

OPTIONS = {
    "01": [(K, "hands-work-at-the-kitchen-sink"), (LUKE, "luke-beside-the-red-workbench"),
           (LUKE, "figures-at-a-service-counter"), (K, "figure-walks-among-work-tables"),
           (STEVE, "wide-view-of-the-team-workspace")],
    "02": [(MATT, "two-figures-facing-off-in-rain"), (TYLER, "tyler-spars-in-parking-lot"),
           (LUKE, "luke-catches-his-breath-on-the-floor"), (MATT, "figures-grapple-in-a-blue-corridor")],
    "03": [(K, "lone-figure-crosses-the-orange-desert"), (LUKE, "luke-works-at-a-motorcycle"),
           (MATT, "matt-by-a-daylight-window"), (MATT, "figure-running-across-a-rooftop"),
           (K, "figure-walks-toward-an-orange-light")],
    "04": [(K, "hands-operate-an-amber-console"), (K, "equipment-on-a-lit-work-table"),
           (WALTER, "hands-at-work-in-low-light"), (STEVE, "figure-crosses-a-shadowed-workspace"),
           (TYLER, "working-at-a-crowded-table"), (K, "hands-hold-a-small-object-in-amber-light")],
    "05": [(K, "joi-reaches-toward-officer-k"), (LUKE, "woods-conversation-reverse-angle"),
           (MATT, "matt-in-a-low-lit-close-up"), (LUKE, "coworker-listens-in-close-up"),
           (K, "hands-meet-in-the-apartment")],
}

if __name__ == "__main__":
    sys.path.insert(0, str(P.parent / "complete-thoughts-movie-cutaways-20261110"))
    import study_candidates as study

    study.require_guard(gpu=True)
    WORK.mkdir(exist_ok=True)
    study.WORK = WORK
    study.OPTIONS = OPTIONS
    study.study()
