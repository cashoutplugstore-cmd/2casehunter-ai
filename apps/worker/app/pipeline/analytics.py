from __future__ import annotations

from typing import Any


PLATFORMS = {"tiktok", "youtube_shorts", "instagram_reels"}


def build_analytics_event(
    video_id: str,
    platform: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    if not str(video_id).strip():
        raise ValueError("video_id is required")
    if platform not in PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    views = max(0, int(metrics.get("views", 0)))
    likes = max(0, int(metrics.get("likes", 0)))
    comments = max(0, int(metrics.get("comments", 0)))
    shares = max(0, int(metrics.get("shares", 0)))
    return {
        "video_id": video_id,
        "platform": platform,
        "metrics": {
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
        },
        "engagement_rate": round((likes + comments + shares) / views, 4) if views else 0.0,
        "status": "captured",
    }
