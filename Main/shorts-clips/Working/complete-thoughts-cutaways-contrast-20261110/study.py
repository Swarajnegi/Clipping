"""Sample the reusable source excerpts around prospective dialogue beats."""
import sys
from pathlib import Path

work = Path(__file__).resolve().parent
sys.path.insert(0, str(work.parent / "complete-thoughts-movie-cutaways-20261110"))
import study_candidates as study

study.WORK = work
study.OPTIONS = {
    "hollis": [
        ("Fight Club", "empty-office-corridor"),
        ("Peaky Blinders - Tommy Shelby S04", "figure-walking-through-sparks"),
        ("Peaky Blinders - Tommy Shelby S06", "figures-enter-through-a-bright-doorway"),
    ],
    "goggins": [
        ("Daredevil - Matt Murdock S02", "matt-in-a-low-lit-close-up"),
        ("Jon Snow", "jon-gets-back-up-in-training"),
        ("Iron Man", "tony-reclines-with-the-reactor"),
    ],
    "clear": [
        ("Iron Man", "two-figures-in-the-workshop"),
        ("Iron Man", "prototype-suit-stands-in-the-workshop"),
        ("Peaky Blinders - Tommy Shelby S04", "figures-at-a-dim-workbench"),
    ],
    "robbins": [
        ("Breaking Bad - Walter White S05A", "skyler-in-the-doorway"),
        ("Iron Man", "pepper-and-tony-in-quiet-conversation"),
        ("Iron Man", "tony-alone-in-a-wide-workshop"),
    ],
    "carr": [
        ("Peaky Blinders - Tommy Shelby S04", "tommy-alone-in-the-office"),
        ("Peaky Blinders - Tommy Shelby S06", "light-over-a-crowd"),
        ("Fight Club", "working-at-a-crowded-table"),
    ],
}

if __name__ == "__main__":
    study.require_guard(gpu=True)
    study.study()
