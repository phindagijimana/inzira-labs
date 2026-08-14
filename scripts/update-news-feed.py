#!/usr/bin/env python3
"""Fetch RSS and PubMed headlines into content/news-feed.json."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "license-service"))

from news_feed import build_feed, config_path, output_path, write_feed  # noqa: E402


def main() -> int:
    payload = build_feed(config_path())
    write_feed(payload, output_path())
    author_count = len(payload.get("authorItems", []))
    print(f"Wrote {payload.get('itemCount', 0)} feed items and {author_count} author items to {output_path()}")
    for err in payload.get("errors", []):
        print(f"  - {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
