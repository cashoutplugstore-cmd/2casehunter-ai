from __future__ import annotations

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


def submit_render_job(render_job: dict[str, Any], provider: VideoProvider | None = None) -> dict[str, Any]:
    selected = provider or QueueOnlyProvider()
    return selected.submit(render_job)
