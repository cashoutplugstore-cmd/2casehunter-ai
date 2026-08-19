from __future__ import annotations

from typing import Any


def build_render_job(plan: dict[str, Any]) -> dict[str, Any]:
    """Create a provider-neutral render job from a production plan.

    This intentionally prepares the render specification without calling an
    external video provider. A provider adapter can consume this job later.
    """
    title = str(plan.get("title") or "").strip()
    scenes = plan.get("scenes")
    if not title:
        raise ValueError("plan.title is required")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("plan.scenes must be a non-empty list")

    return {
        "job_type": "short_video_render",
        "title": title,
        "format": plan.get("format", "short"),
        "aspect_ratio": plan.get("aspect_ratio", "9:16"),
        "language": plan.get("language", "ar"),
        "duration_seconds": int(plan.get("duration_seconds", 0)),
        "captions": bool(plan.get("captions", True)),
        "voiceover": plan.get("voiceover", {"enabled": True, "language": "ar"}),
        "scenes": scenes,
        "status": "queued_for_render",
    }
