# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — chat intent for agent execution quality and throughput metrics."""

from __future__ import annotations

import re

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+agent\s+execution\s+(?:quality|metrics|throughput)"
    r"|agent\s+execution\s+throughput"
    r"|agent\s+execution\s+quality\s+metrics"
    r"|agent\s+throughput\s+score"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*agent\s+metrics\s+(?P<kind>observation|note|intervention)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "observation": "metrics_observation",
    "note": "throughput_note",
    "intervention": "human_intervention_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"metrics\s+grant\s+authority"
    r"|auto\s+approve"
    r"|bypass\s+gate"
    r")\b",
    re.I,
)


def is_agent_execution_quality_throughput_metrics_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_VIEW_RX.search(raw) or _RECORD_RX.match(raw))


def parse_agent_execution_quality_throughput_metrics_record_intent(
    text: str,
) -> tuple[str, str] | None:
    raw = (text or "").strip()
    match = _RECORD_RX.match(raw)
    if not match:
        return None
    kind = _KIND_MAP.get(match.group("kind").lower())
    if not kind:
        return None
    body = (match.group("body") or "").strip()
    if not body:
        return None
    return kind, body
