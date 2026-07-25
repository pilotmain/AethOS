# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    IDENTITY_ACCESS_HARDENING_RECORD_KINDS,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
    append_identity_access_hardening_record,
)

_VIEW_AUTHORIZATION_RX = re.compile(
    r"^\s*show\s+(?:authorization\s+report|identity\s+(?:and\s+)?access\s+hardening)\s*$",
    re.IGNORECASE,
)
_VIEW_PERMISSION_RX = re.compile(r"^\s*show\s+permission\s+evaluation\s*$", re.IGNORECASE)
_VIEW_BOUNDARY_RX = re.compile(r"^\s*show\s+tenant\s+boundary\s+audit\s*$", re.IGNORECASE)
_VIEW_LEAST_PRIV_RX = re.compile(r"^\s*show\s+least\s+privilege\s+report\s*$", re.IGNORECASE)

_NOTE_RX = re.compile(r"^\s*authorization\s+note\s*:\s*(.+)$", re.IGNORECASE)
_DECISION_RX = re.compile(
    r"^\s*authorization\s+review\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)


def parse_identity_access_hardening_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_PERMISSION_RX.match(text):
        return {"action": "view", "focus": "permission_evaluation"}
    if _VIEW_BOUNDARY_RX.match(text):
        return {"action": "view", "focus": "tenant_boundary_audit"}
    if _VIEW_LEAST_PRIV_RX.match(text):
        return {"action": "view", "focus": "least_privilege_report"}
    if _VIEW_AUTHORIZATION_RX.match(text):
        return {"action": "view", "focus": "authorization_dashboard"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"authorization_decision_{decision}",
            "content": body,
        }

    note_match = _NOTE_RX.match(text)
    if note_match:
        return {
            "action": "record",
            "kind": "authorization_note",
            "content": note_match.group(1).strip(),
        }

    lowered = text.lower()
    if lowered.startswith("identity access:") or lowered.startswith("authorization:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "identity_access_hardening_record",
            "content": body,
        }

    return None


def handle_identity_access_hardening_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view", "focus": intent.get("focus") or "authorization_dashboard"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in IDENTITY_ACCESS_HARDENING_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        record = append_identity_access_hardening_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            organization_id=str(intent.get("organization_id") or "") or None,
            user_id=str(intent.get("user_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
