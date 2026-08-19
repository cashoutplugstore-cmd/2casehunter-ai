from __future__ import annotations

from typing import Any


BLOCKED_CATEGORIES = {"graphic_violence", "sexual_content", "illegal_drugs", "extremism"}


def review_policy(item: dict[str, Any]) -> dict[str, Any]:
    category = str(item.get("category") or "").strip().lower()
    risk = float(item.get("risk_score", 0) or 0)
    reasons: list[str] = []

    if category in BLOCKED_CATEGORIES:
        reasons.append(f"blocked_category:{category}")
    if risk >= 0.8:
        reasons.append("high_risk_score")

    return {
        "status": "blocked" if reasons else "approved_for_generation",
        "requires_human_review": bool(reasons),
        "reasons": reasons,
    }
