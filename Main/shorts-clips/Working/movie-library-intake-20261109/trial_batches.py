"""Guarded sample of the exact batching/verification path for this intake."""
import time

from export_batches import encode, verify_and_save
from pack_intake import MOVIES, PACKS, WORK, cool, load, require_guard

require_guard(gpu=True)
for pack in ("tommy-s04", "steve", "walter"):
    packet = load(WORK / pack / "candidates.json")
    source = MOVIES / PACKS[pack][0]
    options = [row for row in packet["candidates"] if 35 < row["start"] < 65 and row["end"] - row["start"] > 2.5]
    if len(options) < 2:
        options = packet["candidates"][:3]
    out = WORK / "export-trial" / f"{pack}-{time.time_ns()}"
    saved = out / "verified"
    saved.mkdir(parents=True)
    cool(74)
    begun = time.monotonic()
    wanted, files = encode(source, packet["source"], options[:3], out / "staged")
    entries = verify_and_save(wanted, files, packet["source"], saved)
    print("BATCH_TRIAL", pack, len(entries), sum(row["frames"] for row in entries),
          "work_seconds", round(time.monotonic() - begun, 1), flush=True)
