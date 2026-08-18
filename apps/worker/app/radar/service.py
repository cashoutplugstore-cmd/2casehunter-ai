from __future__ import annotations

from .rss import fetch_rss
from .scoring import score_story
from .sources import get_active_sources


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


def scan_active_sources() -> list[dict]:
    results: list[dict] = []
    for source in get_active_sources():
        try:
            results.extend(scan_feed(source["url"], source["name"]))
        except Exception as exc:
            results.append(
                {
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "url": source["url"],
                    "error": str(exc),
                }
            )

    return sorted(results, key=lambda item: item.get("score", -1), reverse=True)
