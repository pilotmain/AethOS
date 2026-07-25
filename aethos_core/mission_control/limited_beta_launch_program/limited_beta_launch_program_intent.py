# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
    LIMITED_BETA_LAUNCH_PROGRAM_RECORD_KINDS,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
    append_limited_beta_launch_program_record,
)

_VIEW_PROGRAM_RX = re.compile(r"^\s*show\s+beta\s+launch\s+program\s*$", re.IGNORECASE)
_VIEW_READINESS_RX = re.compile(r"^\s*show\s+beta\s+readiness\s*$", re.IGNORECASE)
_VIEW_COHORTS_RX = re.compile(r"^\s*show\s+beta\s+cohorts\s*$", re.IGNORECASE)
_VIEW_FEEDBACK_RX = re.compile(r"^\s*show\s+beta\s+feedback\s*$", re.IGNORECASE)
_VIEW_METRICS_RX = re.compile(r"^\s*show\s+beta\s+success\s+metrics\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+beta\s+dashboard\s*$", re.IGNORECASE)

_CANDIDATE_NOTE_RX = re.compile(r"^\s*beta\s+candidate\s+note\s*:\s*(.+)$", re.IGNORECASE)
_ADMISSION_DECISION_RX = re.compile(
    r"^\s*beta\s+admission\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)
_LAUNCH_DECISION_RX = re.compile(
    r"^\s*beta\s+launch\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_limited_beta_launch_program_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_READINESS_RX.match(text):
        return {"action": "view", "focus": "beta_readiness_report"}
    if _VIEW_COHORTS_RX.match(text):
        return {"action": "view", "focus": "beta_cohort_registry"}
    if _VIEW_FEEDBACK_RX.match(text):
        return {"action": "view", "focus": "beta_feedback_registry"}
    if _VIEW_METRICS_RX.match(text):
        return {"action": "view", "focus": "beta_success_metrics"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "beta_operations_dashboard"}
    if _VIEW_PROGRAM_RX.match(text):
        return {"action": "view", "focus": "beta_operations_dashboard"}

    admission_match = _ADMISSION_DECISION_RX.match(text)
    if admission_match:
        decision = admission_match.group("decision").lower()
        body = (admission_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"beta_admission_review_decision_{decision}",
            "content": body,
        }

    launch_match = _LAUNCH_DECISION_RX.match(text)
    if launch_match:
        decision = launch_match.group("decision").lower()
        body = (launch_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"beta_launch_review_decision_{decision}",
            "content": body,
        }

    note_match = _CANDIDATE_NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "beta_candidate_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("beta program:") or lowered.startswith("beta launch:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "limited_beta_launch_program_record",
            "content": body,
        }

    return None


def handle_limited_beta_launch_program_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "beta_operations_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in LIMITED_BETA_LAUNCH_PROGRAM_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_limited_beta_launch_program_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
            cohort_id=str(intent.get("cohort_id") or "") or None,
            candidate_id=str(intent.get("candidate_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
