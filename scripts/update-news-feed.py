#!/usr/bin/env python3
"""Fetch RSS and PubMed headlines into content/news-feed.json."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "content" / "news-feed-config.json"
OUTPUT_PATH = ROOT / "content" / "news-feed.json"
USER_AGENT = "InziraLabsNewsFeed/1.0 (+https://github.com/phindagijimana/inzira-labs)"


def fetch_text(url: str, timeout: int = 25) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value[: len(fmt.replace("%z", "+0000"))], fmt.replace("%z", "+0000") if "%z" in fmt else fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_rss(xml_text: str, source: str, filter_id: str) -> list[dict]:
    items: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items

    for node in root.iter():
        name = local(node.tag)
        if name not in {"item", "entry"}:
            continue
        title = link = date_raw = None
        for child in node:
            child_name = local(child.tag)
            if child_name == "title" and child.text:
                title = re.sub(r"\s+", " ", child.text.strip())
            elif child_name == "link":
                link = child.text or child.attrib.get("href")
            elif child_name in {"pubDate", "published", "updated"} and child.text:
                date_raw = child.text.strip()
        if title and link:
            items.append(
                {
                    "title": title,
                    "url": link,
                    "date": date_raw,
                    "source": source,
                    "filter": filter_id,
                }
            )
    return items


def pubmed_recent(term: str, source: str, filter_id: str, retmax: int = 4) -> list[dict]:
    params = urlencode(
        {
            "db": "pubmed",
            "term": term,
            "sort": "pub date",
            "retmax": retmax,
            "retmode": "json",
        }
    )
    search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
    try:
        payload = json.loads(fetch_text(search_url))
        ids = payload.get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []
    if not ids:
        return []

    summary_params = urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{summary_params}"
    try:
        summary = json.loads(fetch_text(summary_url)).get("result", {})
    except Exception:
        return []

    items: list[dict] = []
    for pmid in ids:
        record = summary.get(pmid, {})
        title = record.get("title")
        if not title:
            continue
        pubdate = record.get("pubdate") or record.get("sortpubdate")
        items.append(
            {
                "title": re.sub(r"\s+", " ", title.strip()),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "date": pubdate,
                "source": source,
                "filter": filter_id,
            }
        )
    return items


def normalize_item(raw: dict, cutoff: datetime) -> dict | None:
    dt = parse_date(raw.get("date"))
    if dt and dt < cutoff:
        return None
    iso_date = dt.date().isoformat() if dt else None
    title = raw.get("title", "").strip()
    url = raw.get("url", "").strip()
    if not title or not url:
        return None
    return {
        "title": title,
        "url": url,
        "date": iso_date,
        "source": raw.get("source", ""),
        "filter": raw.get("filter", "all"),
    }


def dedupe_key(item: dict) -> str:
    return item["url"].lower().rstrip("/")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    max_age = int(config.get("maxAgeDays", 14))
    max_items = int(config.get("maxItems", 36))
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age)

    collected: list[dict] = []
    errors: list[str] = []

    for feed in config.get("rss", []):
        try:
            xml_text = fetch_text(feed["url"])
            collected.extend(parse_rss(xml_text, feed["source"], feed["filter"]))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"RSS {feed.get('source', feed.get('url'))}: {exc}")

    for query in config.get("pubmed", []):
        try:
            collected.extend(
                pubmed_recent(query["term"], query["source"], query["filter"])
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PubMed {query.get('source')}: {exc}")

    normalized: list[dict] = []
    seen: set[str] = set()
    for raw in collected:
        item = normalize_item(raw, cutoff)
        if not item:
            continue
        key = dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)

    normalized.sort(key=lambda x: x.get("date") or "", reverse=True)
    normalized = normalized[:max_items]

    output = {
        "fetchedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "itemCount": len(normalized),
        "items": normalized,
    }
    if errors:
        output["errors"] = errors
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(normalized)} items to {OUTPUT_PATH}")
    if errors:
        print("Warnings:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
