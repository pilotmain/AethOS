# SPDX-License-Identifier: Apache-2.0
"""User intent contracts — enforce counts, ranking, filters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_COUNT_RX = re.compile(
    r"\b(top|best|first|leading)\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.I,
)
_WORD_TO_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


@dataclass
class IntentContract:
    query: str
    result_count: int | None = None
    ranked: bool = False
    deduplicate: bool = True
    geographic_filter: str | None = None
    audience: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "result_count": self.result_count,
            "ranked": self.ranked,
            "deduplicate": self.deduplicate,
            "geographic_filter": self.geographic_filter,
            "audience": self.audience,
        }


def parse_intent_contract(query: str) -> IntentContract:
    q = (query or "").strip()
    count: int | None = None
    ranked = bool(re.search(r"\b(top|best|leading|highest rated|most popular)\b", q, re.I))
    m = _COUNT_RX.search(q)
    if m:
        raw = m.group(2).lower()
        count = int(raw) if raw.isdigit() else _WORD_TO_NUM.get(raw)
    geo = None
    geo_m = re.search(r"\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)\b", q)
    if geo_m:
        geo = geo_m.group(1).strip()
    elif re.search(r"\bvirginia\b", q, re.I):
        geo = "Virginia"
    audience = None
    if re.search(r"\b(toddler|kids?|children|family|playground)\b", q, re.I):
        audience = "family"
    return IntentContract(
        query=q,
        result_count=count,
        ranked=ranked or count is not None,
        geographic_filter=geo,
        audience=audience,
    )
