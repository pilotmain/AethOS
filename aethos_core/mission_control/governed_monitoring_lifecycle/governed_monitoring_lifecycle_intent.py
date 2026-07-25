# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — chat intent for governed monitoring lifecycle."""

from __future__ import annotations

import re
from typing import Any

_VIEW_RX = re.compile(
    r"\b("
    r"show\s+(?:governed\s+)?monitoring\s+(?:lifecycle|health|review)"
    r"|monitoring\s+health\s+report"
    r"|monitoring\s+review\s+packet"
    r"|governed\s+monitoring\s+lifecycle"
    r")\b",
    re.I,
)

_ESCALATE_RX = re.compile(
    r"\b(prepare\s+incident\s+escalation|generate\s+incident\s+escalation)\b",
    re.I,
)

_DECISION_RX = re.compile(
    r"^\s*operational\s+decision\s+(?P<decision>continue|investigate|escalate|ignore)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_NOTE_RX = re.compile(
    r"^\s*monitoring\s+(?P<kind>observation|note)\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_WORKFLOW_RX = re.compile(
    r"^\s*workflow\s+result\s*:\s*(?P<body>.+)$",
    re.I | re.S,
)

_DECISION_KIND_MAP = {
    "continue": "operational_decision_continue",
    "investigate": "operational_decision_investigate",
    "escalate": "operational_decision_escalate",
    "ignore": "operational_decision_ignore",
}

_NOTE_KIND_MAP = {
    "observation": "monitoring_observation",
    "note": "operator_review_note",
}

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"autonomous\s+remediation"
    r"|auto\s+rollback"
    r"|redeploy\s+now"
    r"|mutate\s+infrastructure"
    r")\b",
    re.I,
)

_STATUS_RX = re.compile(r"\bstatus\s*=\s*(success|failure|failed|degraded|cancelled)\b", re.I)


def _parse_workflow_metadata(text: str) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    match = _STATUS_RX.search(text or "")
    if match:
        status = match.group(1).lower()
        meta["workflow_status"] = "success" if status == "success" else status
    lowered = (text or "").lower()
    if "success" in lowered and "workflow_status" not in meta:
        meta["workflow_status"] = "success"
    if "failure" in lowered or "failed" in lowered:
        meta["workflow_status"] = "failure"
    return meta


def is_governed_monitoring_lifecycle_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(
        _VIEW_RX.search(raw)
        or _ESCALATE_RX.search(raw)
        or _DECISION_RX.match(raw)
        or _NOTE_RX.match(raw)
        or _WORKFLOW_RX.match(raw)
    )


def is_governed_monitoring_escalation_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or _FORBIDDEN_RX.search(raw):
        return False
    return bool(_ESCALATE_RX.search(raw))


def parse_governed_monitoring_lifecycle_record_intent(
    text: str,
) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()
    workflow_match = _WORKFLOW_RX.match(raw)
    if workflow_match:
        body = (workflow_match.group("body") or "").strip()
        if body:
            return "workflow_result_note", body, _parse_workflow_metadata(body)

    decision_match = _DECISION_RX.match(raw)
    if decision_match:
        kind = _DECISION_KIND_MAP.get(decision_match.group("decision").lower())
        body = (decision_match.group("body") or "").strip()
        if kind and body:
            return kind, body, {}

    note_match = _NOTE_RX.match(raw)
    if note_match:
        kind = _NOTE_KIND_MAP.get(note_match.group("kind").lower())
        body = (note_match.group("body") or "").strip()
        if kind and body:
            return kind, body, {}

    return None
