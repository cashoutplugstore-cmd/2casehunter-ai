from __future__ import annotations

from .rss import RadarItem, fetch_rss
from .scoring import score_story


def scan_feed(url: str, source_name: str = "RSS") -> list[dict]:
    results: list[dict] = []
    for item in fetch_rss(url, source_name):
        results.append(
            {
                "title": item.title,
                "url": item.url,
                "summary": item.summary,
                "published_at": item.published_at.isoformat() if item.published_at else None,
                "source_name": item.source_name,
                "score": score_story(item.title, item.summary),
            }
        )

    return sorted(results, key=lambda item: item["score"], reverse=True)
