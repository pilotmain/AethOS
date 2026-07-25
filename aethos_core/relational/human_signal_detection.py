# SPDX-License-Identifier: Apache-2.0
"""Human signal detection — frustration, confusion, urgency."""

from __future__ import annotations

import re
from typing import Any

_FRUSTRATION = re.compile(r"\b(frustrated|annoyed|again\?|still broken|why won't|fed up|ugh)\b", re.I)
_CONFUSION = re.compile(r"\b(confused|don't understand|what does|unclear|lost|help me understand)\b", re.I)
_URGENCY = re.compile(r"\b(urgent|asap|immediately|production down|outage|critical|emergency)\b", re.I)
_CRISIS = re.compile(r"\b(outage|production down|customers affected|sev-?1|incident)\b", re.I)


def detect_human_signals(text: str | None = None) -> dict[str, Any]:
    """Detect emotional/operational human signals from operator text."""
    t = text or ""
    signals: list[str] = []
    if _CRISIS.search(t):
        signals.append("crisis")
    if _URGENCY.search(t):
        signals.append("urgency")
    if _FRUSTRATION.search(t):
        signals.append("frustration")
    if _CONFUSION.search(t):
        signals.append("confusion")
    intensity = min(1.0, len(signals) * 0.25 + (0.2 if "crisis" in signals else 0))
    return {
        "signals": signals,
        "intensity": round(intensity, 2),
        "frustrated": "frustration" in signals,
        "confused": "confusion" in signals,
        "urgent": "urgency" in signals or "crisis" in signals,
        "crisis": "crisis" in signals,
    }
