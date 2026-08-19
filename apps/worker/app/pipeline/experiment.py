from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Variant:
    id: str
    hook: str
    angle: str
    cta: str


DEFAULT_VARIANTS = (
    Variant("A", "question", "straight_news", "تابع للمزيد"),
    Variant("B", "surprise", "explainer", "شوف شنو صار"),
    Variant("C", "controversy", "context", "شنو رأيك؟"),
)


def build_experiment(blueprint: dict[str, Any], variants: tuple[Variant, ...] = DEFAULT_VARIANTS) -> dict[str, Any]:
    if not str(blueprint.get("title") or "").strip():
        raise ValueError("blueprint.title is required")
    return {
        "status": "ready_for_test",
        "title": blueprint["title"],
        "variants": [
            {"id": v.id, "hook": v.hook, "angle": v.angle, "cta": v.cta}
            for v in variants
        ],
        "selection_policy": "collect_metrics_then_rank",
    }
