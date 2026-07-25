# SPDX-License-Identifier: Apache-2.0
"""FIX 315 — launch decision package intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
    LAUNCH_DECISION_PACKAGE_RECORD_KINDS,
)
from aethos_core.mission_control.launch_decision_package.launch_decision_package_store import (
    append_launch_decision_package_record,
)

_VIEW_PACKAGE_RX = re.compile(r"^\s*show\s+launch\s+decision\s+package\s*$", re.IGNORECASE)
_VIEW_EXECUTIVE_RX = re.compile(r"^\s*show\s+executive\s+summary\s*$", re.IGNORECASE)
_VIEW_RECOMMENDATION_RX = re.compile(r"^\s*show\s+launch\s+recommendation\s+package\s*$", re.IGNORECASE)
_VIEW_DASHBOARD_RX = re.compile(r"^\s*show\s+launch\s+decision\s+dashboard\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*launch\s+decision\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*launch\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_launch_decision_package_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_EXECUTIVE_RX.match(text):
        return {"action": "view", "focus": "launch_executive_summary"}
    if _VIEW_RECOMMENDATION_RX.match(text):
        return {"action": "view", "focus": "launch_recommendation_package"}
    if _VIEW_DASHBOARD_RX.match(text):
        return {"action": "view", "focus": "launch_decision_dashboard"}
    if _VIEW_PACKAGE_RX.match(text):
        return {"action": "view", "focus": "launch_decision_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"launch_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "launch_decision_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("launch decision:") or lowered.startswith("launch package:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "launch_decision_package_record",
            "content": body,
        }

    return None


def handle_launch_decision_package_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "launch_decision_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in LAUNCH_DECISION_PACKAGE_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_launch_decision_package_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            domain=str(intent.get("domain") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
