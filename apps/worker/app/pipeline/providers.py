from __future__ import annotations

import os
from typing import Any, Protocol


class VideoProvider(Protocol):
    name: str

    def submit(self, render_job: dict[str, Any]) -> dict[str, Any]: ...


class QueueOnlyProvider:
    """Safe default adapter: validates and queues work without external API calls."""

    name = "queue-only"

    def submit(self, render_job: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.name,
            "status": "queued",
            "job": render_job,
        }


def _configured_provider() -> VideoProvider:
    provider_name = os.getenv("VIDEO_PROVIDER", "queue-only").strip().lower()
    if provider_name == "ffmpeg-local":
        from .ffmpeg_provider import FFmpegProvider

        return FFmpegProvider()
    return QueueOnlyProvider()


def submit_render_job(render_job: dict[str, Any], provider: VideoProvider | None = None) -> dict[str, Any]:
    selected = provider or _configured_provider()
    return selected.submit(render_job)
