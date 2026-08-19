from __future__ import annotations

from typing import Any


def engagement_rate(metrics: dict[str, Any]) -> float:
    views = max(int(metrics.get("views", 0)), 0)
    if views == 0:
        return 0.0
    interactions = sum(max(int(metrics.get(k, 0)), 0) for k in ("likes", "comments", "shares", "saves"))
    return round((interactions / views) * 100, 2)


def rank_content(metrics: dict[str, Any]) -> dict[str, Any]:
    rate = engagement_rate(metrics)
    views = max(int(metrics.get("views", 0)), 0)
    # Simple transparent baseline; replace with learned ranking after enough data.
    score = round(min(100.0, rate * 8 + min(views / 1000, 20)), 2)
    return {"engagement_rate": rate, "performance_score": score}


def feedback_signal(metrics: dict[str, Any]) -> dict[str, Any]:
    ranked = rank_content(metrics)
    if ranked["performance_score"] >= 70:
        label = "strong"
    elif ranked["performance_score"] >= 40:
        label = "promising"
    else:
        label = "weak"
    return {**ranked, "label": label, "next_action": "reuse_pattern" if label == "strong" else "test_variant"}
