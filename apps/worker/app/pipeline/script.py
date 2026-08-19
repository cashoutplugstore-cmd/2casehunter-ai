from __future__ import annotations

from typing import Any


def build_short_script(blueprint: dict[str, Any]) -> dict[str, Any]:
    """Turn a reviewed blueprint into an original short-form script draft."""
    title = str(blueprint.get("title") or "").strip()
    hook = str(blueprint.get("hook") or "").strip()
    angle = str(blueprint.get("angle") or "").strip()

    if not title:
        raise ValueError("blueprint.title is required")

    script = "\n\n".join(
        part
        for part in (
            hook or f"خلينا نفهم شنو صار بـ{title}.",
            angle or "نشرح الفكرة باختصار ونفصل بين المعلومة المؤكدة وأي تفاصيل غير مؤكدة.",
            "شنو رأيك؟ تابعنا للمزيد من القصص والتحليلات.",
        )
        if part
    )

    return {
        "title": title,
        "format": "short",
        "language": "ar",
        "script": script,
        "status": "ready_for_review",
    }
