"""Sample the exact local excerpt candidates through the clipping guard."""
import sys
from pathlib import Path

from cutaway_plan import CUTS

work = Path(__file__).resolve().parent / "movie-cutaways"
work.mkdir(exist_ok=True)
sys.path.insert(0, str(work.parent.parent / "complete-thoughts-movie-cutaways-20261110"))
import study_candidates as study

study.WORK = work
study.OPTIONS = {number: [(cut[2],cut[3]) for cut in cuts] for number,cuts in CUTS.items()}
study.require_guard(gpu=True)
study.study()
