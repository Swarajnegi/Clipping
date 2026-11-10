"""
outliers.py -- find bounded public-view research leads relative to a channel's median.

Public views identify research leads, not retention or a copying formula. This bounded
listing has no age adjustment; compare similar-age examples before drawing conclusions.

Usage: python scripts/outliers.py <channel-url-or-@handle> [--limit 150] [--top 15]
"""

from __future__ import annotations

import argparse
import statistics
from common import ROOT


def shorts_url(target: str) -> str:
    if target.startswith("@"):
        return f"https://www.youtube.com/{target}/shorts"
    return target.rstrip("/") + ("" if target.rstrip("/").endswith("/shorts") else "/shorts")


def main() -> int:
    import yt_dlp

    ap = argparse.ArgumentParser()
    ap.add_argument("channel")
    ap.add_argument("--limit", type=int, default=150)
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    if not 1 <= args.limit <= 150 or not 1 <= args.top <= 150:
        ap.error('Limits must be between 1 and 150')
    opts = {"quiet": True, "extract_flat": True, "playlistend": args.limit,
            "cachedir": False, "socket_timeout": 20, "retries": 0, "extractor_retries": 0,
            "js_runtimes": {"node": {"path": str(ROOT / ".runtime/node/node.exe")}}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(shorts_url(args.channel), download=False)
    entries = [e for e in info.get("entries") or [] if e]
    missing = sum(e.get('view_count') is None for e in entries)
    rows = [(e['view_count'], e.get("title") or "", e.get("url") or e.get("id"))
            for e in entries if e.get('view_count') is not None]
    if not rows:
        print("no Shorts with view counts found")
        return 1
    med = statistics.median(r[0] for r in rows)
    print(f"{info.get('channel') or info.get('title')}: {len(rows)} Shorts, median {med:,.0f} views")
    print(f'{missing} counts unknown. Bounded listing; ages unadjusted; ratios are discovery leads only.')
    print(f"{'ratio':>6}  {'views':>12}  title / url")
    for views, title, url in sorted(rows, reverse=True)[: args.top]:
        ratio = f'{views / med:6.1f}x' if med else '   N/A '
        print(f"{ratio}  {views:12,}  {title[:70]}\n{'':22}{url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
