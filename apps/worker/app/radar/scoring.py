from __future__ import annotations

import re


KEYWORDS = {
    "prison": 12,
    "prisoner": 12,
    "inmate": 12,
    "jail": 10,
    "sentenced": 8,
    "convicted": 8,
    "escape": 14,
    "escaped": 14,
    "custody": 8,
    "court": 5,
    "arrest": 6,
    "murder": 8,
    "case": 3,
}


def score_story(title: str, summary: str | None = None) -> int:
    text = f"{title} {summary or ''}".lower()
    score = sum(weight for keyword, weight in KEYWORDS.items() if re.search(rf"\b{re.escape(keyword)}\b", text))
    return min(score, 100)
