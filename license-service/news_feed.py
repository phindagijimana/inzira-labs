"""Build and cache the Inzira Labs news feed for API and static export."""

from __future__ import annotations

import asyncio
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER_AGENT = "InziraLabsNewsFeed/1.0 (+https://github.com/phindagijimana/inzira-labs)"
CACHE_TTL = timedelta(hours=int(os.getenv("NEWS_FEED_CACHE_HOURS", "6")))

_cache: dict[str, Any] | None = None
_cache_at: datetime | None = None
_cache_lock = asyncio.Lock()


def resolve_site_dir() -> Path:
    here = Path(__file__).resolve()
    for cand in (here.parent.parent, Path.cwd(), here.parent):
        if (cand / "content" / "news-feed-config.json").is_file():
            return cand
    return here.parent.parent


def config_path() -> Path:
    return resolve_site_dir() / "content" / "news-feed-config.json"


def output_path() -> Path:
    return resolve_site_dir() / "content" / "news-feed.json"


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
    for fmt in ("%Y %b", "%Y %b %d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            sample = value.strip()
            if fmt == "%Y %b":
                sample = " ".join(sample.split()[:2])
            elif fmt == "%Y %b %d":
                sample = " ".join(sample.split()[:3])
            elif "T" in fmt:
                sample = value[:19]
            else:
                sample = value[:10]
            dt = datetime.strptime(sample, fmt.replace("%z", "") if "%z" in fmt else fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    match = re.match(r"^(\d{4})", value)
    if match:
        return datetime(int(match.group(1)), 1, 1, tzinfo=timezone.utc)
    return None


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def keyword_score(title: str, keywords: list[str]) -> int:
    haystack = title.lower()
    return sum(1 for kw in keywords if kw.lower() in haystack)


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


def pubmed_summaries(ids: list[str]) -> dict:
    if not ids:
        return {}
    summary_params = urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json"})
    summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{summary_params}"
    try:
        return json.loads(fetch_text(summary_url)).get("result", {})
    except Exception:
        return {}


def pubmed_search_ids(term: str, retmax: int) -> list[str]:
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
        return payload.get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


def pubmed_recent(term: str, source: str, filter_id: str, retmax: int = 4) -> list[dict]:
    ids = pubmed_search_ids(term, retmax)
    summary = pubmed_summaries(ids)
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


def pubmed_author_items(term: str, retmax: int, cutoff: datetime) -> list[dict]:
    ids = pubmed_search_ids(term, retmax)
    summary = pubmed_summaries(ids)
    items: list[dict] = []
    for pmid in ids:
        record = summary.get(pmid, {})
        title = record.get("title")
        if not title:
            continue
        pubdate = record.get("pubdate") or record.get("sortpubdate")
        dt = parse_date(pubdate)
        if dt and dt < cutoff:
            continue
        journal = record.get("fulljournalname") or record.get("source") or "PubMed"
        iso_date = dt.date().isoformat() if dt else None
        items.append(
            {
                "title": re.sub(r"\s+", " ", title.strip()),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "date": iso_date,
                "journal": journal,
                "source": "PubMed",
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
    item = {
        "title": title,
        "url": url,
        "date": iso_date,
        "source": raw.get("source", ""),
        "filter": raw.get("filter", "all"),
    }
    if "score" in raw:
        item["score"] = raw["score"]
    return item


def dedupe_key(item: dict) -> str:
    return item["url"].lower().rstrip("/")


def build_feed(cfg_path: Path | None = None) -> dict[str, Any]:
    path = cfg_path or config_path()
    config = json.loads(path.read_text(encoding="utf-8"))
    max_age = int(config.get("maxAgeDays", 14))
    max_items = int(config.get("maxItems", 36))
    keywords = [kw for kw in config.get("keywords", []) if isinstance(kw, str) and kw.strip()]
    broad_sources = set(config.get("broadFeedsRequireKeyword", []))
    min_broad_score = int(config.get("minKeywordScoreForBroadFeeds", 1))
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
            collected.extend(pubmed_recent(query["term"], query["source"], query["filter"]))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PubMed {query.get('source')}: {exc}")

    normalized: list[dict] = []
    seen: set[str] = set()
    for raw in collected:
        score = keyword_score(raw.get("title", ""), keywords)
        if raw.get("source") in broad_sources and score < min_broad_score:
            continue
        raw["score"] = score
        item = normalize_item(raw, cutoff)
        if not item:
            continue
        key = dedupe_key(item)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)

    normalized.sort(key=lambda x: x.get("date") or "", reverse=True)
    normalized.sort(key=lambda x: x.get("score", 0), reverse=True)
    normalized = normalized[:max_items]
    for item in normalized:
        item.pop("score", None)

    author_items: list[dict] = []
    author_cfg = config.get("authorWatch") or {}
    author_term = author_cfg.get("term")
    if author_term:
        author_cutoff = datetime.now(timezone.utc) - timedelta(days=int(author_cfg.get("maxAgeDays", 730)))
        try:
            author_items = pubmed_author_items(
                author_term,
                int(author_cfg.get("retmax", 10)),
                author_cutoff,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"PubMed author watch: {exc}")

    output: dict[str, Any] = {
        "fetchedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "itemCount": len(normalized),
        "items": normalized,
        "authorItems": author_items,
        "live": True,
    }
    if errors:
        output["errors"] = errors
    return output


def write_feed(payload: dict[str, Any], out_path: Path | None = None) -> None:
    target = out_path or output_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_static_feed() -> dict[str, Any]:
    path = output_path()
    if not path.is_file():
        return {"items": [], "authorItems": [], "itemCount": 0, "fetchedAt": None, "live": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.setdefault("live", False)
        return payload
    except json.JSONDecodeError:
        return {"items": [], "authorItems": [], "itemCount": 0, "fetchedAt": None, "live": False}


def _refresh_sync() -> dict[str, Any]:
    try:
        payload = build_feed()
        write_feed(payload)
        return payload
    except Exception as exc:  # noqa: BLE001
        fallback = read_static_feed()
        fallback["refreshError"] = str(exc)
        fallback["live"] = False
        return fallback


async def get_news_feed(force_refresh: bool = False) -> dict[str, Any]:
    global _cache, _cache_at
    now = datetime.now(timezone.utc)
    async with _cache_lock:
        if (
            not force_refresh
            and _cache is not None
            and _cache_at is not None
            and now - _cache_at < CACHE_TTL
        ):
            return _cache

        payload = await asyncio.to_thread(_refresh_sync)
        _cache = payload
        _cache_at = now
        return payload
