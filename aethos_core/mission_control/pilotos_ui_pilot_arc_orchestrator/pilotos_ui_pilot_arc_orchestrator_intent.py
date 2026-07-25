# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — chat intent for PilotOS UI pilot arc orchestrator."""

from __future__ import annotations

import re

_PILOT_ARC_RX = re.compile(
    r"\b("
    r"pilotos\s+(?:ui\s+)?pilot\s+arc"
    r"|show\s+pilotos\s+pilot"
    r"|pilotos\s+pilot\s+status"
    r"|pilotos\s+trust\s+report"
    r")\b",
    re.I,
)

_RUN_PILOT_RX = re.compile(
    r"\brun\s+pilotos\s+pilot\s+(?P<num>[123])\b",
    re.I,
)

_RECORD_RX = re.compile(
    r"^\s*pilot\s+arc\s+(?P<kind>trust|issue|register|evidence)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_KIND_MAP = {
    "trust": "pilot_arc_trust_decision",
    "issue": "repo_issue_binding",
    "register": "repository_registration",
    "evidence": "pilot_evidence_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"auto\s+trust"
    r"|inherit\s+trust"
    r"|bypass\s+gate"
    r"|hidden\s+run"
    r")\b",
    re.I,
)


def is_pilotos_ui_pilot_arc_orchestrator_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_PILOT_ARC_RX.search(raw))


def parse_run_pilotos_pilot_intent(text: str) -> int | None:
    raw = (text or "").strip()
    match = _RUN_PILOT_RX.search(raw)
    if not match:
        return None
    return int(match.group("num"))


def parse_pilotos_ui_pilot_arc_orchestrator_record_intent(text: str) -> tuple[str, str] | None:
    raw = (text or "").strip()
    if not raw:
        return None
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
