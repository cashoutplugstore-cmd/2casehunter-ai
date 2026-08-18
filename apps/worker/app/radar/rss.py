from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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
                title=title.strip(),
                url=link,
                summary=(entry.get("summary") or None),
                published_at=_parse_date(published),
                source_name=source_name,
            )
        )

    return items
