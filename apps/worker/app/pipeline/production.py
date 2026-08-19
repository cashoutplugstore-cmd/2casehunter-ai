from __future__ import annotations

from typing import Any


def build_production_plan(script: dict[str, Any]) -> dict[str, Any]:
    """Turn a short-form script into a deterministic video production plan."""
    title = str(script.get("title") or "").strip()
    text = str(script.get("script") or "").strip()

    if not title:
        raise ValueError("script.title is required")
    if not text:
        raise ValueError("script.script is required")

    parts = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not parts:
        parts = [text]

    durations = [5, 12, 5]
    scenes: list[dict[str, Any]] = []
    for index, part in enumerate(parts[:3]):
        duration = durations[index] if index < len(durations) else 5
        scenes.append(
            {
                "scene": index + 1,
                "duration_seconds": duration,
                "voiceover": part,
                "on_screen_text": part[:90],
                "visual_direction": "B-roll or generated visual matching the narration; keep the subject clear and vertical 9:16.",
                "transition": "cut" if index else "fade_in",
            }
        )

    total = sum(scene["duration_seconds"] for scene in scenes)
    return {
        "title": title,
        "format": "short",
        "aspect_ratio": "9:16",
        "language": "ar",
        "duration_seconds": total,
        "scenes": scenes,
        "captions": True,
        "voiceover": {"enabled": True, "language": "ar"},
        "status": "ready_for_render",
    }
