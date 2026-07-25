# SPDX-License-Identifier: Apache-2.0
"""Prompt inference — detect lightweight continuity prompts."""

from __future__ import annotations

import re
from typing import Any

_CONTINUITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("situation_improved", re.compile(r"\b(has|did)\b.{0,40}\b(situation|things?)\b.{0,20}\b(improv\w*|better|stabil\w*)\b", re.I)),
    ("deployment_stabilized", re.compile(r"\b(deployment|deploy\w*)\b.{0,30}\b(stabil\w*|recover\w*|hold|settl\w*)\b", re.I)),
    ("recovery_status", re.compile(r"\b(has|did)\b.{0,30}\b(recovery|recover\w*)\b.{0,20}\b(stabil\w*|hold|complet\w*|finish\w*)\b", re.I)),
    ("what_changed", re.compile(r"\b(what changed|what.?s changed|any change|update on)\b", re.I)),
    ("did_it_hold", re.compile(r"\b(did it hold|still holding|holding up|still stable)\b", re.I)),
    ("monitoring_advice", re.compile(r"\b(monitoring|what should (we|i) monitor|monitoring additions?)\b", re.I)),
    ("operational_status", re.compile(r"\b(operational state|runtime status|how.?s it going|status update)\b", re.I)),
]


def infer_continuity_intent(user_text: str) -> dict[str, Any]:
    text = (user_text or "").strip()
    lower = text.lower()
    for intent, pattern in _CONTINUITY_PATTERNS:
        if pattern.search(lower):
            return {"continuity_prompt": True, "intent": intent, "confidence": 0.82}
    if len(text.split()) <= 8 and any(w in lower for w in ("improv", "stable", "stabilized", "better", "hold")):
        return {"continuity_prompt": True, "intent": "implicit_followup", "confidence": 0.68}
    return {"continuity_prompt": False, "intent": None, "confidence": 0.0}
