# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management intent."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_KINDS,
    LIFECYCLE_STAGES,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_store import (
    append_autonomous_application_lifecycle_management_record,
)

_VIEW_RX = re.compile(
    r"^\s*(?:show\s+)?(?:(?:autonomous\s+)?application\s+lifecycle\s+(?:management|dashboard|timeline)|"
    r"lifecycle\s+management(?:\s+dashboard)?|"
    r"application\s+lifecycle\s+dashboard)\s*$",
    re.IGNORECASE,
)

_STAGE_NOTE_RX = {
    "concept": re.compile(r"^\s*concept\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "product_design": re.compile(r"^\s*design\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "delivery": re.compile(r"^\s*delivery\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "deployment": re.compile(r"^\s*deployment\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "operations": re.compile(r"^\s*operations\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "recovery": re.compile(r"^\s*recovery\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
    "evolution": re.compile(r"^\s*evolution\s+lifecycle\s+note\s*:\s*(.+)$", re.IGNORECASE),
}

_KIND_BY_STAGE = {
    "concept": "concept_lifecycle_note",
    "product_design": "design_lifecycle_note",
    "delivery": "delivery_lifecycle_note",
    "deployment": "deployment_lifecycle_note",
    "operations": "operations_lifecycle_note",
    "recovery": "recovery_lifecycle_note",
    "evolution": "evolution_lifecycle_note",
}

_TRANSITION_RX = re.compile(r"^\s*lifecycle\s+transition\s+note\s*:\s*(.+)$", re.IGNORECASE)

_DECISION_RX = re.compile(
    r"^\s*lifecycle\s+decision\s+(?P<decision>approve|hold|reject|defer)\s*:\s*(?P<body>.+)$",
    re.IGNORECASE | re.S,
)

_KV_RX = re.compile(r"(\w+)\s*=\s*([^,\s]+(?:\s+[^,\s=]+)*)")


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in _KV_RX.finditer(blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def parse_autonomous_application_lifecycle_management_intent(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None

    if _VIEW_RX.match(text):
        return {"action": "view"}

    decision_match = _DECISION_RX.match(text)
    if decision_match:
        decision = decision_match.group("decision").lower()
        body = (decision_match.group("body") or "").strip()
        if not body:
            return None
        return {
            "action": "record",
            "kind": f"human_lifecycle_decision_{decision}",
            "content": body,
        }

    for stage, rx in _STAGE_NOTE_RX.items():
        match = rx.match(text)
        if match:
            kv = _parse_kv_blob(match.group(1))
            return {
                "action": "record",
                "kind": _KIND_BY_STAGE[stage],
                "content": match.group(1).strip(),
                "lifecycle_stage": stage,
                "opportunity_id": kv.get("opportunity") or kv.get("opportunity_id"),
            }

    transition_match = _TRANSITION_RX.match(text)
    if transition_match:
        kv = _parse_kv_blob(transition_match.group(1))
        stage = kv.get("stage") or kv.get("lifecycle_stage")
        return {
            "action": "record",
            "kind": "lifecycle_transition_note",
            "content": transition_match.group(1).strip(),
            "lifecycle_stage": stage,
        }

    lowered = text.lower()
    if lowered.startswith("application lifecycle:") or lowered.startswith("lifecycle:"):
        body = text.split(":", 1)[1].strip()
        return {
            "action": "record",
            "kind": "autonomous_application_lifecycle_management_record",
            "content": body,
        }

    return None


def handle_autonomous_application_lifecycle_management_intent(
    intent: dict[str, Any],
    *,
    session_id: str | None = None,
) -> dict[str, Any]:
    action = intent.get("action")
    if action == "view":
        return {"action": "view"}

    if action == "record":
        kind = str(intent.get("kind") or "")
        if kind not in AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_KINDS:
            raise ValueError(f"unsupported record kind: {kind!r}")
        stage = intent.get("lifecycle_stage")
        if stage and str(stage) not in LIFECYCLE_STAGES:
            raise ValueError(f"unsupported lifecycle stage: {stage!r}")
        record = append_autonomous_application_lifecycle_management_record(
            kind=kind,
            content=str(intent.get("content") or ""),
            session_id=session_id,
            lifecycle_stage=str(stage) if stage else None,
            opportunity_id=str(intent.get("opportunity_id") or "") or None,
        )
        return {"action": "record", "record": record}

    raise ValueError(f"unsupported intent action: {action!r}")
