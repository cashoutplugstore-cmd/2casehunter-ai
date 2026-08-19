from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import re

import feedparser


@dataclass(slots=True)
class RadarItem:
    title: str
    url: str
    summary: str | None
    published_at: datetime | None
    source_name: str


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _clean_summary(value: str | None, max_chars: int = 1600) -> str | None:
    if not value:
        return None

    # RSS feeds commonly put HTML markup and image tags in summary/description.
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    return text[:max_chars].rstrip() + ("…" if len(text) > max_chars else "")


def fetch_rss(url: str, source_name: str = "RSS") -> list[RadarItem]:
    feed = feedparser.parse(url)
    items: list[RadarItem] = []

    for entry in feed.entries:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue

        published = entry.get("published") or entry.get("updated")
        items.append(
            RadarItem(
                title=html.unescape(re.sub(r"\s+", " ", title)).strip(),
                url=link,
                summary=_clean_summary(entry.get("summary") or entry.get("description")),
                published_at=_parse_date(published),
                source_name=source_name,
            )
        )

    return items
