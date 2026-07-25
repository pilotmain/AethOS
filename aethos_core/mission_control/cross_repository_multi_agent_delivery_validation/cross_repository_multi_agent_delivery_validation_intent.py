# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — chat intent for cross-repository multi-agent delivery validation."""

from __future__ import annotations

import re

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+cross.repo\s+(?:multi.agent\s+)?delivery\s+validation"
    r"|cross.repository\s+validation\s+matrix"
    r"|cross.repo\s+evidence\s+registry"
    r"|delivery\s+generalization\s+validation"
    r")\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*cross.repo\s+validation\s+(?P<kind>observation|evidence|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "observation": "validation_observation",
    "evidence": "cross_repo_evidence_note",
    "note": "validation_annotation",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"validation\s+grant\s+trust"
    r"|auto\s+trust"
    r"|rerun\s+pilot"
    r")\b",
    re.I,
)


def is_cross_repository_multi_agent_delivery_validation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_VIEW_RX.search(raw) or _RECORD_RX.match(raw))


def parse_cross_repository_multi_agent_delivery_validation_record_intent(
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
