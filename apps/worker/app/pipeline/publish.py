from __future__ import annotations

from typing import Any


class PublishProvider:
    name = "manual-review"

    def submit(self, video: dict[str, Any], platform: str) -> dict[str, Any]:
        return {
            "provider": self.name,
            "platform": platform,
            "status": "ready_for_publish",
            "video": video,
        }


def build_publish_job(video: dict[str, Any], platform: str = "tiktok") -> dict[str, Any]:
    if not isinstance(video, dict):
        raise ValueError("video must be an object")
    if not str(video.get("title") or "").strip():
        raise ValueError("video.title is required")
    allowed = {"tiktok", "youtube_shorts", "instagram_reels"}
    if platform not in allowed:
        raise ValueError(f"unsupported platform: {platform}")
    return PublishProvider().submit(video, platform)
