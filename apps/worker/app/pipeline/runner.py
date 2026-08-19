from __future__ import annotations

from typing import Any

from ..db import get_supabase
from ..radar.service import scan_feed
from .service import build_blueprint


def run_feed_pipeline(
    feed_url: str,
    source_name: str = "RSS",
    target: str = "arabic-short-form",
    persist: bool = True,
) -> dict[str, Any]:
    """Run RSS discovery -> scoring -> blueprint and optionally persist the run."""
    stories = scan_feed(feed_url, source_name)
    if not stories:
        return {
            "status": "no_story",
            "source_name": source_name,
            "stories_found": 0,
            "story": None,
            "blueprint": None,
            "saved": False,
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

    saved = False
    save_error: str | None = None
    if persist:
        try:
            supabase = get_supabase()
            response = (
                supabase.table("content_runs")
                .insert(
                    {
                        "source_name": source_name,
                        "source_url": story.get("url", ""),
                        "story_title": story["title"],
                        "story_summary": story.get("summary", ""),
                        "score": story.get("score"),
                        "target": target,
                        "status": "ready_for_review",
                        "blueprint": result["blueprint"],
                    }
                )
                .execute()
            )
            saved = bool(response.data)
        except Exception as exc:
            save_error = str(exc)

    payload: dict[str, Any] = {
        "status": "ready_for_review",
        "source_name": source_name,
        "stories_found": len(stories),
        "story": story,
        **result,
        "saved": saved,
    }
    if save_error:
        payload["save_error"] = save_error
    return payload
