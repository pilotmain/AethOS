# SPDX-License-Identifier: Apache-2.0
"""FIX 309 — SaaS launch readiness assessment intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
    SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_KINDS,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
    append_saas_launch_readiness_assessment_record,
)

_VIEW_READINESS_RX = re.compile(r"^\s*show\s+launch\s+readiness\s*$", re.IGNORECASE)
_VIEW_BLOCKERS_RX = re.compile(r"^\s*show\s+launch\s+blockers\s*$", re.IGNORECASE)
_VIEW_RISKS_RX = re.compile(r"^\s*show\s+launch\s+risks\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+launch\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*launch\s+readiness\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*launch\s+readiness\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_saas_launch_readiness_assessment_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_BLOCKERS_RX.match(text):
        return {"action": "view", "focus": "launch_risk_registry"}
    if _VIEW_RISKS_RX.match(text):
        return {"action": "view", "focus": "launch_risk_registry"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "launch_readiness_dashboard"}
    if _VIEW_READINESS_RX.match(text):
        return {"action": "view", "focus": "launch_readiness_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"launch_readiness_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "launch_readiness_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("launch readiness:") or lowered.startswith("launch:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "saas_launch_readiness_assessment_record",
            "content": body,
        }

    return None


def handle_saas_launch_readiness_assessment_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "launch_readiness_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_saas_launch_readiness_assessment_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
