"""LAYER: Engineer. Metadata-only original-footage discovery.

THE BIG PICTURE: catalogue original episodes before spending bandwidth or GPU time.
THE FLOW: bounded listing -> hydrate individual metadata -> deduplicate -> atomic catalogue.
No media, subtitle bodies, thumbnails or credentials are downloaded or stored.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from common import ROOT, slug


def source_key(info: dict) -> str:
    platform = (info.get("extractor_key") or info.get("extractor") or "unknown").lower()
    if platform.startswith("youtube"):
        platform = "youtube"
    elif platform.startswith("rumble"):
        platform = "rumble"
    return f"{platform}:{info['id']}"


def error_status(message: str) -> str:
    text = message.lower()
    if any(s in text for s in ("403", "429", "captcha", "sign in", "login", "cloudflare", "bot", "forbidden", "members-only", "channel's members", "premium-only")):
        return "blocked"
    if any(s in text for s in ("404", "removed", "private video", "unavailable", "not found")):
        return "unavailable"
    return "failed"


def safe_error(error: Exception) -> str:
    # Provider diagnostics may contain signed URLs. Keep the reason, omit URL tokens.
    return re.sub(r"https?://\S+", "[url]", str(error)).replace("\x1b", "")[:1500]


def episode(info: dict, seed: str) -> dict:
    key = source_key(info)
    url = info.get("webpage_url") or info.get("original_url") or seed
    subtitles = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    return {
        "key": key, "platform": key.split(":", 1)[0], "video_id": str(info["id"]),
        "canonical_url": url, "title": info.get("title"),
        "uploader": info.get("uploader"), "channel_id": info.get("channel_id"),
        "channel_url": info.get("channel_url") or info.get("uploader_url"),
        "upload_date": info.get("upload_date"), "duration": info.get("duration"),
        "description": info.get("description"), "chapters": info.get("chapters") or [],
        "view_count": info.get("view_count"), "live_status": info.get("live_status"),
        "captions": {"status": "available" if subtitles or automatic else "none_reported",
                     "manual_languages": sorted(subtitles), "automatic_languages": sorted(automatic)},
        "access_status": "metadata_available", "reuse_permission": "unknown",
        "found_via": [seed],
        "prep": {"input": url, "expected_legacy_id": slug(str(info["id"])),
                 "work_id": slug(key.replace(":", "_")),
                 "catalogue_key": key, "note": "Verify source URL in staging before reusing a cached ID."},
    }


def collect(sources: list[str], limit: int, ydl_factory: Any = None) -> dict:
    if ydl_factory is None:
        from yt_dlp import YoutubeDL
        ydl_factory = YoutubeDL
    options = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "cachedir": False, "socket_timeout": 20, "retries": 0, "extractor_retries": 0,
        "js_runtimes": {"node": {"path": str(ROOT / ".runtime/node/node.exe")}},
        "playlistend": limit + 1, "lazy_playlist": True,
    }
    rows: dict[str, dict] = {}
    listings = []
    for seed in dict.fromkeys(sources):
        parsed = urlsplit(seed)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Sources must be HTTP(S) URLs without embedded credentials")
        listing = {"url": seed, "status": "complete", "limit": limit, "seen": 0, "errors": []}
        try:
            with ydl_factory({**options, "extract_flat": "in_playlist"}) as ydl:
                info = ydl.extract_info(seed, download=False)
                if not info:
                    raise ValueError("Extractor returned no metadata")
                entries = iter(info.get("entries") or []) if "entries" in info else iter([info])
                for index, item in enumerate(islice(entries, limit + 1)):
                    if index == limit:
                        listing["status"] = "limited"
                        break
                    listing["seen"] += 1
                    if not item:
                        listing["errors"].append({"status": "unavailable", "reason": "Empty listing entry"})
                        continue
                    target = item.get("webpage_url") or item.get("url") or seed
                    try:
                        if item.get("_type") in ("url", "url_transparent"):
                            with ydl_factory({**options, "noplaylist": True}) as detail:
                                item = detail.extract_info(target, download=False)
                        if not item or not item.get("id") or "entries" in item:
                            raise ValueError("Individual episode metadata was not returned")
                        row = episode(item, seed)
                        if row["key"] in rows:
                            rows[row["key"]]["found_via"] = list(dict.fromkeys([*rows[row["key"]]["found_via"], seed]))
                        else:
                            rows[row["key"]] = row
                    except Exception as exc:
                        reason = safe_error(exc)
                        listing["errors"].append({"url": target, "status": error_status(reason), "reason": reason,
                                                  "captions_status": "not_checked"})
            if listing["errors"]:
                listing["status"] = "partial"
        except Exception as exc:
            reason = safe_error(exc)
            listing["status"] = "partial" if listing["seen"] else error_status(reason)
            listing["errors"].append({"status": error_status(reason), "reason": reason, "captions_status": "not_checked"})
        listings.append(listing)
        print(f"{seed}: {listing['status']}, {listing['seen']} entries", flush=True)
    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "media_downloaded": False, "listings": listings, "episodes": list(rows.values())}


def write_catalogue(path: Path, catalogue: dict) -> None:
    path = path.resolve()
    path.relative_to(ROOT.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", help="Original episode or channel URLs")
    parser.add_argument("--limit", type=int, default=25, help="Maximum episodes per source (1–150)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 150:
        parser.error("--limit must be between 1 and 150")
    args.output.resolve().relative_to(ROOT.resolve())
    result = collect(args.sources, args.limit)
    write_catalogue(args.output, result)
    print(f"Saved {len(result['episodes'])} unique episodes to {args.output}")
    return 0 if all(row["status"] == "complete" for row in result["listings"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
