from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ContentBlueprint:
    title: str
    hook: str
    angle: str
    format: str
    target: str
    status: str = "ready_for_review"


def _clean(value: Any) -> str:
    return str(value or "").strip()


def build_blueprint(story: dict[str, Any], target: str = "arabic-short-form") -> dict[str, Any]:
    """Prepare a reviewable content blueprint from a discovered story.

    This is the CaseHunter/GenLab-style preparation stage only: it does not
    publish automatically or copy copyrighted source material.
    """
    title = _clean(story.get("title"))
    summary = _clean(story.get("summary"))
    if not title:
        raise ValueError("story.title is required")

    hook = f"شنو القصة؟ {title}"
    angle = summary[:280] if summary else "شرح مختصر للخبر مع التركيز على أهم معلومة قابلة للتحقق."

    blueprint = ContentBlueprint(
        title=title,
        hook=hook,
        angle=angle,
        format="short",
        target=target,
    )

    return {
        "blueprint": blueprint.__dict__,
        "source_url": _clean(story.get("source_url")),
        "score": story.get("score"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
