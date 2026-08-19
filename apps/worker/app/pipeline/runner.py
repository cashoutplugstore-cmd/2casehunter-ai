from __future__ import annotations

from typing import Any

from ..radar.service import scan_feed
from .service import build_blueprint


def run_feed_pipeline(
    feed_url: str,
    source_name: str = "RSS",
    target: str = "arabic-short-form",
) -> dict[str, Any]:
    """Run the first CaseHunter pipeline stage for one RSS feed.

    Flow: RSS discovery -> scoring -> select highest-scoring story -> blueprint.
    It intentionally stops before media generation or publishing.
    """
    stories = scan_feed(feed_url, source_name)
    if not stories:
        return {
            "status": "no_story",
            "source_name": source_name,
            "stories_found": 0,
            "story": None,
            "blueprint": None,
        }

    story = stories[0]
    result = build_blueprint(
        {
            "title": story["title"],
            "summary": story.get("summary", ""),
            "source_url": story.get("url", ""),
            "score": story.get("score"),
        },
        target=target,
    )

    return {
        "status": "ready_for_review",
        "source_name": source_name,
        "stories_found": len(stories),
        "story": story,
        **result,
    }
